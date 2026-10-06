#!/usr/bin/env python3
"""Ponte do Jarvis: o seu celular → Claude Code rodando nesta pasta.

Canais (escolha um em CANAL no .env):
  telegram         grátis; o bot busca as mensagens (long polling), sem servidor nem túnel
  whatsapp-meta    WhatsApp Cloud API da Meta (1.000 conversas de serviço grátis por mês por número)
  whatsapp-twilio  WhatsApp pela Twilio (número na hora, cobra por mensagem)

Três vias, cada uma um Claude Code persistente (stream-json):
  triagem · Haiku, sem ferramentas: decide RAPIDO ou FLUXO
  rapido  · Sonnet, só leitura: consultas, status, mandar arquivos que já existem
  fluxo   · Opus, sessão contínua: pesquisar, planejar, criar, aprovar ("aprovo"), agendar

Uso:
  python3 scripts/jarvis_bridge.py                  # sobe a ponte (o serviço do Mac/servidor roda isso)
  python3 scripts/jarvis_bridge.py --definir-senha  # grava só o hash da senha no .env
Comandos no chat: /status · /novo · /cancelar · /bloquear · /rapido <pergunta> · /opus <pedido>

Agenda (dados/agenda.json): a ponte executa no horário cada item {"at": ISO, "run": [cmd...], "texto": "..."} e manda
o resultado no chat. É assim que as publicações agendadas saem sem depender de serviço pago.
"""
import base64
import getpass
import hashlib
import hmac
import html
import json
import os
import queue
import re
import secrets
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"
STATE = ROOT / "dados" / ".ponte-estado.json"
AGENDA = ROOT / "dados" / "agenda.json"


def env(name, default=""):
    if os.environ.get(name):
        return os.environ[name]
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip().strip('"')
    return default


CANAL = env("CANAL", "telegram")
LOCK_HOURS = float(env("JARVIS_LOCK_HOURS", "6"))
NOME = env("JARVIS_NOME", "Jarvis")
COMMON = ["--input-format", "stream-json", "--output-format", "stream-json", "--verbose", "--strict-mcp-config"]

FLUXO_TOOLS = ["Bash", "Read", "Edit", "Write", "Glob", "Grep", "Skill", "WebSearch", "WebFetch", "TodoWrite", "Agent", "ToolSearch"]
FLUXO_SYSTEM = f"""Você é o {NOME}, usado pelo celular do dono desta pasta. Regras deste canal:
- Português do Brasil, curto e direto (tela de celular). Sem tabelas largas; prefira listas.
- Não existe AskUserQuestion aqui: para decidir algo, pergunte em texto com opções numeradas e PARE.
- Publicar, agendar, gastar créditos pagos e qualquer ação irreversível só depois de o usuário responder "aprovo"
  (ou equivalente explícito) a uma proposta exata sua.
- Antes de cada etapa longa (render, pesquisa), escreva uma linha curta dizendo o que vai fazer: cada texto seu chega
  na hora ao usuário como aviso de progresso.
- Para mandar um arquivo, escreva numa linha própria: ARQUIVO: <caminho absoluto>"""
RAPIDO_TOOLS = ["Read", "Glob", "Grep", "Bash(ls:*)", "Bash(cat:*)", "Bash(date:*)", "Bash(python3 scripts/metricas.py:*)"]
RAPIDO_SYSTEM = f"""Você é a via rápida do {NOME}: responde consultas e manda arquivos que já existem.
- SÓ LEITURA: nunca crie, edite, publique ou agende. Se o pedido exigir isso, responda: "Isso é com o fluxo: mande /opus <pedido>".
- Português do Brasil, curto. Para mandar um arquivo, escreva numa linha própria: ARQUIVO: <caminho absoluto>"""
TRIAGEM_SYSTEM = """Classifique a mensagem para um assistente que cria e publica conteúdo.
Responda SÓ com uma palavra: RAPIDO ou FLUXO.
RAPIDO = consulta sem criar nada (o que está agendado, métricas, mandar arquivo que já existe, horário).
FLUXO = criar, escrever, mudar, gerar, publicar, agendar, opinar, responder a uma proposta ("aprovo", "a opção 2"),
ou qualquer dúvida. Na dúvida: FLUXO."""


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ---------- senha ----------
def hash_password(pw, salt=None, n=300_000):
    salt = salt or os.urandom(16).hex()
    return f"pbkdf2${n}${salt}${hashlib.pbkdf2_hmac('sha256', pw.encode(), bytes.fromhex(salt), n).hex()}"


def check_password(pw):
    try:
        _, n, salt, _ = env("JARVIS_SENHA_HASH").split("$")
    except ValueError:
        return False
    return hmac.compare_digest(hash_password(pw, salt, int(n)), env("JARVIS_SENHA_HASH"))


def set_password():
    pw = getpass.getpass("Nova senha do Jarvis: ")
    if len(pw) < 8 or pw != getpass.getpass("Repita: "):
        sys.exit("Senha curta (mínimo 8) ou diferente na repetição. Nada mudou.")
    lines = [l for l in (ENV_FILE.read_text().splitlines() if ENV_FILE.exists() else []) if not l.startswith("JARVIS_SENHA_HASH=")]
    ENV_FILE.write_text("\n".join(lines + [f'JARVIS_SENHA_HASH="{hash_password(pw)}"']) + "\n")
    print("Senha salva (só o hash) no .env. Reinicie a ponte para valer.")


# ---------- canais ----------
class Telegram:
    name = "telegram"
    API = "https://api.telegram.org/bot{token}/{method}"

    def __init__(self):
        self.token, self.chat = env("TELEGRAM_BOT_TOKEN"), env("TELEGRAM_CHAT_ID")
        if not self.token:
            sys.exit("TELEGRAM_BOT_TOKEN ausente no .env (crie o bot no @BotFather; veja docs/TELEGRAM.md).")

    def call(self, method, files=None, **params):
        try:
            return requests.post(self.API.format(token=self.token, method=method), data=params, files=files, timeout=(10, 180)).json()
        except requests.RequestException as e:
            return {"ok": False, "description": str(e)}

    def send(self, text):
        for i in range(0, len(text), 3500):
            part = text[i:i + 3500]
            h = html.escape(part)
            h = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", h)
            h = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", h)
            if not self.call("sendMessage", chat_id=self.chat, text=h, parse_mode="HTML").get("ok"):
                self.call("sendMessage", chat_id=self.chat, text=part)

    def send_file(self, p):
        ext = p.suffix.lower()
        kind, field = (("sendVideo", "video") if ext == ".mp4" else ("sendPhoto", "photo") if ext in (".jpg", ".jpeg", ".png")
                       else ("sendAudio", "audio") if ext in (".wav", ".mp3", ".m4a", ".ogg") else ("sendDocument", "document"))
        if p.stat().st_size > 49 * 2**20:
            return self.send(f"(maior que 50 MB, não dá pelo bot: {p.name})")
        with p.open("rb") as fh:
            r = self.call(kind, files={field: fh}, chat_id=self.chat, caption=p.name)
        if not r.get("ok"):
            self.send(f"(falha ao mandar {p.name}: {r.get('description')})")

    def forget(self, msg):
        self.call("deleteMessage", chat_id=self.chat, message_id=msg["id"])

    def typing(self, msg):
        self.call("sendChatAction", chat_id=self.chat, action="typing")

    def audio_bytes(self, msg):
        info = self.call("getFile", file_id=msg["audio"])["result"]
        return requests.get(f"https://api.telegram.org/file/bot{self.token}/{info['file_path']}", timeout=(10, 120)).content

    def start(self, on_message):
        menu = [("status", "Ocupado? Fila e sessão"), ("novo", "Começar uma conversa nova"), ("cancelar", "Interromper a tarefa"),
                ("bloquear", "Travar agora (pede a senha)"), ("rapido", "Pergunta rápida (só leitura)"), ("opus", "Pedido direto ao fluxo")]
        self.call("setMyCommands", commands=json.dumps([{"command": c, "description": d} for c, d in menu]))
        offset = state.get("offset", 0)
        while True:
            try:
                r = requests.get(self.API.format(token=self.token, method="getUpdates"),
                                 params={"offset": offset, "timeout": 50}, timeout=(10, 60)).json()
            except requests.RequestException:
                time.sleep(5)
                continue
            for up in r.get("result", []):
                offset = state["offset"] = up["update_id"] + 1
                save_state()
                m = up.get("message")
                if not m:
                    continue
                chat = str(m["chat"]["id"])
                if not self.chat:
                    self.call("sendMessage", chat_id=chat, text=f"Seu chat id é {chat}. Coloque TELEGRAM_CHAT_ID={chat} no .env e reinicie.")
                    continue
                if chat != self.chat:
                    continue
                v = m.get("voice") or m.get("audio")
                on_message({"id": m["message_id"], "text": m.get("text") or m.get("caption") or "",
                            "audio": v["file_id"] if v else None})


class WebhookChannel:
    """Base dos canais de WhatsApp: servidor HTTP local + URL pública (PUBLIC_URL fixa no servidor, ou túnel grátis
    da Cloudflare quando roda no computador). Também serve arquivos temporários (/f/<token>/<nome>) para quem precisa
    de URL pública, como a Twilio."""
    PORT = int(env("JARVIS_PORTA", "8787"))

    def __init__(self):
        self.url, self.on_message, self.files = env("PUBLIC_URL").rstrip("/"), None, {}
        self.last_inbound = 0.0

    def handle_get(self, path, query):
        return 404, b""

    def handle_post(self, path, headers, body):
        return 404, b""

    def serve(self):
        ch = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                path, _, qs = self.path.partition("?")
                m = re.match(r"^/f/([0-9a-f]{32})/", path)
                if m and m.group(1) in ch.files:
                    p = ch.files[m.group(1)]
                    self.send_response(200)
                    self.send_header("Content-Length", str(p.stat().st_size))
                    self.end_headers()
                    self.wfile.write(p.read_bytes())
                    return
                code, out = ch.handle_get(path, dict(urllib.parse.parse_qsl(qs)))
                self.send_response(code)
                self.end_headers()
                self.wfile.write(out)

            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                code, out = ch.handle_post(self.path, self.headers, body)
                self.send_response(code)
                self.end_headers()
                self.wfile.write(out)

        ThreadingHTTPServer(("127.0.0.1", self.PORT), H).serve_forever()

    def public_file(self, p):
        tok = secrets.token_hex(16)
        self.files[tok] = p
        return f"{self.url}/f/{tok}/{urllib.parse.quote(p.name)}"

    def tunnel(self):
        proc = subprocess.Popen(["cloudflared", "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{self.PORT}"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        for line in proc.stderr:
            m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
            if m:
                threading.Thread(target=lambda: [None for _ in proc.stderr], daemon=True).start()
                return proc, m.group(0)
        raise RuntimeError("cloudflared não devolveu URL (instale: brew install cloudflared)")

    def registered(self):
        """Chamado quando a URL pública muda (túnel). Canais que precisam reapontar o webhook sobrescrevem."""

    def start(self, on_message):
        self.on_message = on_message
        threading.Thread(target=self.serve, daemon=True).start()
        if self.url:  # servidor: URL fixa (Caddy/HTTPS na frente)
            log(f"{self.name}: webhook em {self.url}/webhook")
            self.registered()
            while True:
                time.sleep(3600)
        while True:  # computador: túnel grátis, URL nova a cada início
            try:
                proc, self.url = self.tunnel()
                time.sleep(4)
                self.registered()
                log(f"{self.name}: webhook em {self.url}/webhook")
                proc.wait()
                log(f"{self.name}: túnel caiu, subindo de novo")
            except Exception as e:
                log(f"{self.name}: erro no túnel: {e}")
            time.sleep(10)


def same_number(a, b):
    """Celular do Brasil chega com ou sem o 9 extra (55 DD 9XXXXXXXX × 55 DD XXXXXXXX)."""
    a, b = re.sub(r"\D", "", a or ""), re.sub(r"\D", "", b or "")
    strip9 = lambda n: n[:4] + n[5:] if n.startswith("55") and len(n) == 13 and n[4] == "9" else n
    return bool(a) and strip9(a) == strip9(b)


class WhatsAppMeta(WebhookChannel):
    """WhatsApp Cloud API (Meta direto). Trava de cota: conta cada envio e corta em WHATSAPP_COTA (padrão 900/mês;
    a Meta dá 1.000 conversas de serviço grátis). Fora da janela de 24 h só template pago: não mandamos nada."""
    name = "whatsapp-meta"
    GRAPH = "https://graph.facebook.com/v23.0"

    def __init__(self):
        super().__init__()
        self.token, self.phone, self.waba = env("WHATSAPP_TOKEN"), env("WHATSAPP_PHONE_ID"), env("WHATSAPP_WABA_ID")
        self.secret, self.to, self.app_id = env("WHATSAPP_APP_SECRET"), env("WHATSAPP_DONO"), env("WHATSAPP_APP_ID")
        self.verify = env("WHATSAPP_VERIFY_TOKEN") or secrets.token_hex(16)
        self.cap = int(env("WHATSAPP_COTA", "900"))
        self.usage_file = ROOT / "dados" / ".whatsapp-uso.json"
        self.seen = set()
        if not all([self.token, self.phone, self.secret, self.to, self.app_id]):
            sys.exit("Faltam variáveis do WhatsApp (Meta) no .env; veja docs/WHATSAPP-META.md.")

    def take(self):
        month = time.strftime("%Y-%m")
        u = json.loads(self.usage_file.read_text()) if self.usage_file.exists() else {}
        if u.get("mes") != month:
            u = {"mes": month, "enviados": 0}
        if u["enviados"] >= self.cap:
            log(f"whatsapp: cota de {self.cap} envios atingida em {month}; mudo até o dia 1")
            return False
        u["enviados"] += 1
        self.usage_file.write_text(json.dumps(u))
        return True

    def post(self, path, **kw):
        try:
            return requests.post(f"{self.GRAPH}/{path}", headers={"Authorization": f"Bearer {self.token}"}, timeout=(10, 120), **kw).json()
        except requests.RequestException as e:
            return {"error": {"message": str(e)}}

    def send(self, text):
        text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", text).strip()
        if not text or time.time() - self.last_inbound > 24 * 3600 or not self.take():
            return
        r = self.post(f"{self.phone}/messages", json={"messaging_product": "whatsapp", "to": re.sub(r"\D", "", self.to),
                                                      "type": "text", "text": {"body": text[:4000], "preview_url": False}})
        if "error" in r:
            log("whatsapp: falha no envio:", r["error"].get("message"))

    def send_file(self, p):
        ext = p.suffix.lower()
        kind, limit = (("image", 5) if ext in (".jpg", ".jpeg", ".png") else ("audio", 16) if ext in (".mp3", ".m4a", ".ogg")
                       else ("video", 16) if ext == ".mp4" else ("document", 100))
        if p.stat().st_size > limit * 2**20:
            return self.send(f"(maior que {limit} MB, não dá pelo WhatsApp: {p.name})")
        if time.time() - self.last_inbound > 24 * 3600 or not self.take():
            return
        mime = {"image": "image/png" if ext == ".png" else "image/jpeg", "audio": "audio/mpeg", "video": "video/mp4"}.get(kind, "application/octet-stream")
        with p.open("rb") as fh:
            up = self.post(f"{self.phone}/media", data={"messaging_product": "whatsapp", "type": mime}, files={"file": (p.name, fh, mime)})
        if "id" not in up:
            return log("whatsapp: upload falhou:", up.get("error", {}).get("message"))
        body = {"id": up["id"], **({"filename": p.name} if kind == "document" else {}), **({"caption": p.name} if kind != "audio" else {})}
        self.post(f"{self.phone}/messages", json={"messaging_product": "whatsapp", "to": re.sub(r"\D", "", self.to), "type": kind, kind: body})

    def forget(self, msg):
        """A API não apaga mensagens do usuário: apague a senha à mão no app."""

    def typing(self, msg):
        self.post(f"{self.phone}/messages", json={"messaging_product": "whatsapp", "status": "read", "message_id": msg["id"],
                                                 "typing_indicator": {"type": "text"}})

    def audio_bytes(self, msg):
        h = {"Authorization": f"Bearer {self.token}"}
        info = requests.get(f"{self.GRAPH}/{msg['audio']}", headers=h, timeout=(10, 60)).json()
        return requests.get(info["url"], headers=h, timeout=(10, 120)).content

    def handle_get(self, path, q):
        ok = q.get("hub.mode") == "subscribe" and q.get("hub.verify_token") == self.verify
        return (200, q.get("hub.challenge", "").encode()) if ok else (403, b"")

    def handle_post(self, path, headers, body):
        sig = "sha256=" + hmac.new(self.secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, headers.get("X-Hub-Signature-256", "")):
            log("whatsapp: POST com assinatura inválida (descartado)")
            return 403, b""
        payload = json.loads(body or b"{}")
        for entry in payload.get("entry", []):
            for ch in entry.get("changes", []):
                for m in ch.get("value", {}).get("messages", []) or []:
                    if not same_number(m.get("from"), self.to) or m.get("id") in self.seen:
                        continue
                    self.seen.add(m["id"])
                    self.last_inbound = time.time()
                    self.on_message({"id": m["id"], "text": (m.get("text") or {}).get("body", ""),
                                     "audio": (m.get("audio") or {}).get("id") if m.get("type") == "audio" else None})
        return 200, b""

    def registered(self):
        """Aponta o webhook do app para a URL atual e assina a conta do WhatsApp no app."""
        r = requests.post(f"{self.GRAPH}/{self.app_id}/subscriptions", timeout=60, data={
            "object": "whatsapp_business_account", "callback_url": self.url + "/webhook", "verify_token": self.verify,
            "fields": "messages", "access_token": f"{self.app_id}|{self.secret}"}).json()
        s = self.post(f"{self.waba}/subscribed_apps")
        log("whatsapp: webhook registrado", r, s)


class WhatsAppTwilio(WebhookChannel):
    """WhatsApp pela Twilio. O webhook de entrada é configurado uma vez no console da Twilio (URL fixa: use no servidor).
    Arquivos saem por URL pública temporária servida pela própria ponte."""
    name = "whatsapp-twilio"

    def __init__(self):
        super().__init__()
        self.sid, self.auth = env("TWILIO_ACCOUNT_SID"), env("TWILIO_AUTH_TOKEN")
        self.sender, self.to = env("TWILIO_WHATSAPP_FROM"), env("WHATSAPP_DONO")
        if not all([self.sid, self.auth, self.sender, self.to]):
            sys.exit("Faltam variáveis da Twilio no .env; veja docs/WHATSAPP-TWILIO.md.")

    def _msg(self, **data):
        to = "whatsapp:+" + re.sub(r"\D", "", self.to)
        r = requests.post(f"https://api.twilio.com/2010-04-01/Accounts/{self.sid}/Messages.json", auth=(self.sid, self.auth),
                          data={"From": self.sender, "To": to, **data}, timeout=(10, 60))
        if r.status_code >= 300:
            log("twilio: falha no envio:", r.text[:300])

    def send(self, text):
        text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", text).strip()
        for i in range(0, len(text), 1500):  # limite da Twilio por mensagem
            self._msg(Body=text[i:i + 1500])

    def send_file(self, p):
        if p.stat().st_size > 16 * 2**20:
            return self.send(f"(maior que 16 MB, não dá pelo WhatsApp: {p.name})")
        self._msg(Body=p.name, MediaUrl=self.public_file(p))

    def forget(self, msg):
        """A API não apaga mensagens do usuário: apague a senha à mão no app."""

    def typing(self, msg):
        pass

    def audio_bytes(self, msg):
        return requests.get(msg["audio"], auth=(self.sid, self.auth), timeout=(10, 120)).content

    def handle_post(self, path, headers, body):
        params = dict(urllib.parse.parse_qsl(body.decode()))
        url = self.url + path
        signed = url + "".join(k + params[k] for k in sorted(params))
        sig = base64.b64encode(hmac.new(self.auth.encode(), signed.encode(), hashlib.sha1).digest()).decode()
        if not hmac.compare_digest(sig, headers.get("X-Twilio-Signature", "")):
            log("twilio: POST com assinatura inválida (descartado)")
            return 403, b""
        if not same_number(params.get("From", "").replace("whatsapp:", ""), self.to):
            return 200, b""
        self.last_inbound = time.time()
        audio = params.get("MediaUrl0") if params.get("MediaContentType0", "").startswith("audio") else None
        self.on_message({"id": params.get("MessageSid"), "text": params.get("Body", ""), "audio": audio})
        return 200, b"<Response></Response>"


# ---------- estado ----------
STATE.parent.mkdir(parents=True, exist_ok=True)
state = json.loads(STATE.read_text()) if STATE.exists() else {}


def save_state():
    STATE.write_text(json.dumps(state))


# ---------- Claude Code persistente ----------
class Agent:
    def __init__(self, key, model, args, persist=True):
        self.key, self.model, self.args, self.persist = key, model, args, persist
        self.proc, self.events, self.lock = None, queue.Queue(), threading.Lock()

    def start(self):
        cmd = ["claude", "-p", "--model", self.model, *COMMON, *self.args]
        if not self.persist:
            cmd.append("--no-session-persistence")
        elif state.get(self.key):
            cmd += ["--resume", state[self.key]]
        self.proc = subprocess.Popen(cmd, cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, bufsize=1)
        threading.Thread(target=self._read, args=(self.proc,), daemon=True).start()

    def _read(self, proc):
        for line in proc.stdout:
            try:
                self.events.put(json.loads(line))
            except json.JSONDecodeError:
                pass
        self.events.put({"type": "_exit"})

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.kill()
        self.proc = None

    def reset(self):
        self.stop()
        state.pop(self.key, None)
        save_state()

    def ask(self, text, on_text=None):
        with self.lock:
            if not self.proc or self.proc.poll() is not None:
                self.start()
            while not self.events.empty():
                self.events.get_nowait()
            self.proc.stdin.write(json.dumps({"type": "user", "message": {"role": "user", "content": text}}) + "\n")
            self.proc.stdin.flush()
            said = []
            while True:
                ev = self.events.get()
                t = ev.get("type")
                if t == "assistant":
                    for c in ev["message"].get("content", []):
                        if c.get("type") == "text" and c.get("text", "").strip():
                            said.append(c["text"].strip())
                            if on_text:
                                on_text(c["text"].strip())
                elif t == "result":
                    if self.persist and ev.get("session_id"):
                        state[self.key] = ev["session_id"]
                        save_state()
                    res = (ev.get("result") or "").strip()
                    return "" if (on_text and res in said) else res
                elif t == "_exit":
                    self.proc = None
                    return "(o Claude Code parou; mande de novo)"


triagem = Agent("triagem", env("JARVIS_MODELO_TRIAGEM", "haiku"), ["--tools", "", "--system-prompt", TRIAGEM_SYSTEM], persist=False)
rapido = Agent("rapido", env("JARVIS_MODELO_RAPIDO", "sonnet"), ["--tools", "Read,Glob,Grep,Bash", "--allowedTools", *RAPIDO_TOOLS,
                                                                  "--append-system-prompt", RAPIDO_SYSTEM])
fluxo = Agent("fluxo", env("JARVIS_MODELO_FLUXO", "opus"), ["--permission-mode", "acceptEdits", "--allowedTools", *FLUXO_TOOLS,
                                                             "--append-system-prompt", FLUXO_SYSTEM])


# ---------- áudio (whisper local, opcional) ----------
_whisper = {}


def load_whisper():
    try:
        import whisper
        _whisper["m"] = whisper.load_model(env("WHISPER_MODELO", "base"))
    except Exception as e:  # sem whisper a ponte segue só com texto
        _whisper["erro"] = str(e)


def transcribe(data):
    while "m" not in _whisper and "erro" not in _whisper:
        time.sleep(0.3)
    if "erro" in _whisper:
        return None
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as fh:
        fh.write(data)
    return _whisper["m"].transcribe(fh.name, language="pt")["text"].strip()


# ---------- trabalho ----------
CH = None
jobs, busy = queue.Queue(), threading.Event()
lock = {"until": 0.0, "fails": 0, "blocked_until": 0.0}


def forward(text):
    files = re.findall(r"^ARQUIVO:\s*(\S+)\s*$", text, re.M)
    body = re.sub(r"^ARQUIVO:.*$\n?", "", text, flags=re.M).strip()
    if body:
        CH.send(body)
    for f in files:
        p = Path(f).expanduser()
        if p.is_file() and ROOT in p.resolve().parents:
            CH.send_file(p)
        else:
            CH.send(f"(arquivo não encontrado ou fora da pasta do Jarvis: {f})")


def gate(msg):
    if not env("JARVIS_SENHA_HASH"):
        CH.send("🔒 Nenhuma senha definida. No terminal: python3 scripts/jarvis_bridge.py --definir-senha")
        return False
    now = time.time()
    if now < lock["until"]:
        lock["until"] = now + LOCK_HOURS * 3600
        return True
    text = (msg.get("text") or "").strip()
    if now < lock["blocked_until"]:
        CH.send(f"🔒 Muitas tentativas. Tente de novo em {int((lock['blocked_until'] - now) / 60) + 1} min.")
        return False
    if text and not text.startswith("/"):
        CH.forget(msg)
        if check_password(text):
            lock["fails"], lock["until"] = 0, now + LOCK_HOURS * 3600
            CH.send(f"🔓 Desbloqueado. Bloqueia de novo após {LOCK_HOURS:g} h sem uso ou com /bloquear.")
            return False
        lock["fails"] += 1
        if lock["fails"] >= 5:
            lock["fails"], lock["blocked_until"] = 0, now + 15 * 60
            CH.send("🔒 Senha errada 5 vezes. Bloqueado por 15 min.")
        else:
            CH.send(f"🔒 Senha incorreta ({lock['fails']}/5).")
        return False
    CH.send("🔒 Bloqueado. Mande a senha para continuar.")
    return False


def route(text):
    if text.startswith("/rapido"):
        return rapido, text[len("/rapido"):].strip()
    if text.startswith("/opus"):
        return fluxo, text[len("/opus"):].strip()
    return (rapido if "RAPIDO" in triagem.ask(text).upper() else fluxo), text


def work(msg):
    text = msg.get("text") or ""
    if msg.get("audio"):
        heard = transcribe(CH.audio_bytes(msg))
        if heard is None:
            return CH.send("Áudio não está ativo (instale o whisper: pip install openai-whisper). Mande em texto.")
        text = heard
        CH.send(f"🎙️ entendi: {text}")
    if not text:
        return CH.send("Mande texto ou áudio.")
    agent, prompt = route(text)
    CH.typing(msg)
    final = agent.ask(prompt, on_text=forward if agent is fluxo else None)
    if final:
        forward(final)


def worker():
    while True:
        msg = jobs.get()
        busy.set()
        try:
            work(msg)
        except Exception as e:
            CH.send(f"(erro na ponte: {e})")
        finally:
            busy.clear()


def command(text):
    if text == "/bloquear":
        lock["until"] = 0
        CH.send("🔒 Bloqueado.")
    elif text == "/novo":
        fluxo.reset()
        rapido.reset()
        CH.send("Conversa nova iniciada.")
    elif text == "/cancelar":
        while not jobs.empty():
            jobs.get_nowait()
        fluxo.stop()
        rapido.stop()
        CH.send("Cancelado. A conversa continua de onde parou.")
    elif text == "/status":
        CH.send(f"{NOME} ativo ({CH.name}). Ocupado: {'sim' if busy.is_set() else 'não'} · na fila: {jobs.qsize()}")
    else:
        return False
    return True


def on_message(msg):
    if not gate(msg) or command((msg.get("text") or "").strip()):
        return
    if busy.is_set() or not jobs.empty():
        CH.send(f"⏳ na fila ({jobs.qsize() + 1}). /cancelar interrompe a tarefa atual.")
    jobs.put(msg)


def agenda_loop():
    """Executa os itens vencidos de dados/agenda.json (publicações agendadas, lembretes) e manda o resultado."""
    while True:
        try:
            items = json.loads(AGENDA.read_text()) if AGENDA.exists() else []
            changed = False
            for it in items:
                if it.get("feito") or datetime.fromisoformat(it["at"]).timestamp() > time.time():
                    continue
                it["feito"] = time.strftime("%Y-%m-%dT%H:%M:%S")  # marca antes de rodar: nunca executa duas vezes
                AGENDA.write_text(json.dumps(items, ensure_ascii=False, indent=1))
                changed = True
                if it.get("texto"):
                    CH.send(it["texto"])
                if it.get("run"):
                    out = subprocess.run(it["run"], cwd=ROOT, capture_output=True, text=True, timeout=1800)
                    it["saida"] = (out.stdout or "")[-2000:] + (out.stderr or "")[-1000:]
                    CH.send(f"📅 {it.get('nome', 'agenda')}:\n" + ((out.stdout or "").strip()[-1500:] or (out.stderr or "").strip()[-800:]))
                log("agenda:", it.get("nome"), it["at"])
            if changed:
                AGENDA.write_text(json.dumps(items, ensure_ascii=False, indent=1))
        except Exception as e:
            log("agenda:", e)
        time.sleep(20)


def main():
    global CH
    CH = {"telegram": Telegram, "whatsapp-meta": WhatsAppMeta, "whatsapp-twilio": WhatsAppTwilio}.get(CANAL, Telegram)()
    threading.Thread(target=load_whisper, daemon=True).start()
    threading.Thread(target=worker, daemon=True).start()
    threading.Thread(target=agenda_loop, daemon=True).start()
    log(f"{NOME} ativo no canal {CH.name}")
    CH.start(on_message)


if __name__ == "__main__":
    set_password() if "--definir-senha" in sys.argv else main()
