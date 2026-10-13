#!/usr/bin/env python3
"""YouTube Shorts pelo SEU projeto no Google Cloud: login, canal, upload, status, capa e apagar.

.env: YOUTUBE_CLIENT_ID e YOUTUBE_CLIENT_SECRET (cliente OAuth do tipo "App para computador"; passo a passo em
docs/YOUTUBE.md). Opcionais: YOUTUBE_IDIOMA (padrão pt-BR), YOUTUBE_CATEGORIA (padrão 22, "Pessoas e blogs"),
YOUTUBE_PRIVACIDADE (padrão public). O token fica em dados/.youtube-token.json (fora do git) e se renova sozinho;
num servidor sem navegador, YOUTUBE_REFRESH_TOKEN no .env substitui o arquivo.

Shorts não têm endpoint próprio: é o upload normal de um vídeo vertical de até 3 min, e o YouTube decide sozinho se
ele vai para a aba Shorts (`status` confere). Projeto que ainda não passou na auditoria da API do YouTube tem todo
upload travado como privado; a publicação funciona, mas só você vê o vídeo até a auditoria sair.

Uso (da raiz da pasta do Jarvis):
  python3 scripts/youtube.py login                     # abre o navegador; escolha a conta do canal
  python3 scripts/youtube.py eu                        # canal autorizado (confere se está tudo certo)
  python3 scripts/youtube.py upload <video.mp4> --titulo "..." --descricao-arquivo <arq.txt> \\
      [--privacidade private|unlisted|public] [--agendar-para 2026-10-20T12:07:00-03:00] [--tags a,b] --confirmo
  python3 scripts/youtube.py status <video_id>         # privacidade, processamento, travas e se caiu na aba Shorts
  python3 scripts/youtube.py capa <video_id> <capa.jpg|png>
  python3 scripts/youtube.py apagar <video_id> --confirmo
"""
import base64
import hashlib
import http.server
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOKENS = ROOT / "dados" / ".youtube-token.json"
AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN = "https://oauth2.googleapis.com/token"
API = "https://www.googleapis.com/youtube/v3"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3/videos"
SCOPES = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube"  # youtube: editar e apagar
MAX_SHORT = 180  # segundos


def env(name, default=None):
    if os.environ.get(name):
        return os.environ[name]
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            if line.startswith(name + "=") and line.split("=", 1)[1].strip():
                return line.split("=", 1)[1].strip().strip('"')
    if default is None:
        sys.exit(f"{name} ausente no .env (veja docs/YOUTUBE.md).")
    return default


def request(method, url, data=None, headers=None, form=False, raw=None):
    body = raw
    if data is not None:
        body = urllib.parse.urlencode(data).encode() if form else json.dumps(data).encode()
    h = dict(headers or {})
    if data is not None:
        h["Content-Type"] = "application/x-www-form-urlencoded" if form else "application/json; charset=UTF-8"
    req = urllib.request.Request(url, method=method, data=body, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return r.headers, json.loads(r.read() or "{}")
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} {method} {url.split('?')[0]}: {e.read().decode()[:800]}")


def save(tok, old=None):
    if old and "refresh_token" not in tok:
        tok["refresh_token"] = old["refresh_token"]
    tok["expires_at"] = int(time.time()) + int(tok.get("expires_in", 0)) - 120
    TOKENS.parent.mkdir(parents=True, exist_ok=True)
    TOKENS.write_text(json.dumps(tok, indent=2))
    TOKENS.chmod(0o600)


def refresh(refresh_token):
    _, new = request("POST", TOKEN, form=True, data={
        "client_id": env("YOUTUBE_CLIENT_ID"), "client_secret": env("YOUTUBE_CLIENT_SECRET"),
        "grant_type": "refresh_token", "refresh_token": refresh_token})
    return new


def token():
    rt = env("YOUTUBE_REFRESH_TOKEN", "")
    if rt:  # servidor sem arquivo de token: renova a cada execução
        return refresh(rt)["access_token"]
    if not TOKENS.exists():
        sys.exit("Sem login no YouTube. Rode: python3 scripts/youtube.py login")
    tok = json.loads(TOKENS.read_text())
    if time.time() < tok.get("expires_at", 0):
        return tok["access_token"]
    new = refresh(tok["refresh_token"])
    save(new, tok)
    return new["access_token"]


def api(method, path, query=None, data=None):
    url = f"{API}{path}?" + urllib.parse.urlencode(query or {})
    return request(method, url, data=data, headers={"Authorization": f"Bearer {token()}"})[1]


def login():
    """Fluxo de app instalado (PKCE): o Google devolve o código para um servidor local de uma requisição só."""
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    got = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            got.update(dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query)))
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h2>Pronto. Pode fechar esta aba e voltar ao terminal.</h2>".encode())

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    redirect = f"http://127.0.0.1:{srv.server_port}"
    url = AUTH + "?" + urllib.parse.urlencode({
        "client_id": env("YOUTUBE_CLIENT_ID"), "redirect_uri": redirect, "response_type": "code", "scope": SCOPES,
        "access_type": "offline", "prompt": "consent select_account", "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256"})
    print("Abrindo o login do Google (escolha a conta e o canal onde os Shorts vão sair):\n" + url)
    webbrowser.open(url)
    while "code" not in got and "error" not in got:
        srv.handle_request()
    if got.get("error") or got.get("state") != state:
        sys.exit(f"Login recusado: {got.get('error', 'state inválido')}")
    _, tok = request("POST", TOKEN, form=True, data={
        "client_id": env("YOUTUBE_CLIENT_ID"), "client_secret": env("YOUTUBE_CLIENT_SECRET"), "code": got["code"],
        "grant_type": "authorization_code", "redirect_uri": redirect, "code_verifier": verifier})
    if "refresh_token" not in tok:
        sys.exit("O Google não devolveu refresh_token: remova o acesso do app na sua conta Google e rode login de novo.")
    save(tok)
    eu()


def eu():
    items = api("GET", "/channels", {"part": "snippet,statistics", "mine": "true"}).get("items", [])
    if not items:
        sys.exit("A conta autorizada não tem canal. Rode login de novo e escolha a conta/canal certo.")
    c = items[0]
    print(f"Canal: {c['snippet']['title']} ({c['snippet'].get('customUrl', '')}) · id {c['id']} · "
          f"{c['statistics'].get('subscriberCount', '?')} inscritos · {c['statistics'].get('videoCount', '?')} vídeos")


def upload(video, titulo, descricao, privacidade=None, agendar_para=None, tags=()):
    if len(titulo) > 100:
        sys.exit(f"Título com {len(titulo)} caracteres; o máximo é 100.")
    if len(descricao.encode()) > 5000:
        sys.exit("Descrição acima de 5.000 bytes.")
    status = {"privacyStatus": privacidade or env("YOUTUBE_PRIVACIDADE", "public"),
              "selfDeclaredMadeForKids": False, "embeddable": True}
    if agendar_para:
        status.update(privacyStatus="private", publishAt=agendar_para)  # o YouTube só agenda vídeo privado
    idioma = env("YOUTUBE_IDIOMA", "pt-BR")
    meta = {"snippet": {"title": titulo, "description": descricao, "tags": list(tags),
                        "categoryId": env("YOUTUBE_CATEGORIA", "22"),
                        "defaultLanguage": idioma, "defaultAudioLanguage": idioma},
            "status": status}
    size = video.stat().st_size
    headers, _ = request("POST", UPLOAD + "?" + urllib.parse.urlencode({"uploadType": "resumable", "part": "snippet,status"}),
                         data=meta, headers={"Authorization": f"Bearer {token()}", "X-Upload-Content-Type": "video/mp4",
                                             "X-Upload-Content-Length": str(size)})
    print(f"Enviando {video.name} ({size / 1048576:.1f} MB)…")
    _, res = request("PUT", headers["Location"], raw=video.read_bytes(),
                     headers={"Authorization": f"Bearer {token()}", "Content-Type": "video/mp4"})
    vid = res["id"]
    print(f"Enviado: https://youtube.com/shorts/{vid}")
    mostrar(vid)
    return vid


def capa(vid, imagem):
    """Capa personalizada (JPG/PNG). Em Short o YouTube só usa para canais do Programa de Parcerias; antes disso
    responde 200 e ignora, então mandar não faz mal e passa a valer sozinho quando o canal entrar."""
    data = Path(imagem).read_bytes()
    ctype = "image/png" if str(imagem).lower().endswith(".png") else "image/jpeg"
    url = "https://www.googleapis.com/upload/youtube/v3/thumbnails/set?" + urllib.parse.urlencode({"videoId": vid, "uploadType": "media"})
    request("POST", url, raw=data, headers={"Authorization": f"Bearer {token()}", "Content-Type": ctype})


def e_short(vid):
    """/shorts/<id> responde 200 para Short e redireciona para /watch quando o vídeo foi para a aba de vídeos
    (pode levar alguns minutos depois do upload). None = não deu para conferir."""
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    try:
        r = urllib.request.build_opener(NoRedirect).open(urllib.request.Request(f"https://www.youtube.com/shorts/{vid}", method="HEAD"), timeout=30)
        return r.status == 200
    except urllib.error.HTTPError as e:
        return False if 300 <= e.code < 400 else None
    except urllib.error.URLError:
        return None


def achar_por_titulo(titulo, n=25):
    """Últimos uploads do canal com este título exato (para nunca publicar duas vezes)."""
    ch = api("GET", "/channels", {"part": "contentDetails", "mine": "true"})["items"][0]
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    items = api("GET", "/playlistItems", {"part": "snippet", "playlistId": uploads, "maxResults": n}).get("items", [])
    return next((i["snippet"]["resourceId"]["videoId"] for i in items if i["snippet"]["title"].strip() == titulo.strip()), None)


def mostrar(vid):
    items = api("GET", "/videos", {"part": "status,processingDetails,snippet", "id": vid}).get("items", [])
    if not items:
        sys.exit("Vídeo não encontrado.")
    s = items[0]["status"]
    print(json.dumps({"titulo": items[0]["snippet"]["title"], "privacidade": s.get("privacyStatus"),
                      "agendado_para": s.get("publishAt"), "upload": s.get("uploadStatus"),
                      "recusa": s.get("rejectionReason") or s.get("failureReason"),
                      "processamento": items[0].get("processingDetails", {}).get("processingStatus")},
                     indent=2, ensure_ascii=False))


def arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "login":
        login()
    elif cmd == "eu":
        eu()
    elif cmd == "upload" and len(sys.argv) > 2:
        if "--confirmo" not in sys.argv:
            sys.exit("Upload exige --confirmo (depois da aprovação do vídeo, título e descrição exatos).")
        if not arg("--titulo") or not arg("--descricao-arquivo"):
            sys.exit("Faltam --titulo e --descricao-arquivo.")
        tags = [t.strip() for t in arg("--tags", "").split(",") if t.strip()]
        upload(Path(sys.argv[2]), arg("--titulo"), Path(arg("--descricao-arquivo")).read_text().strip(),
               arg("--privacidade"), arg("--agendar-para"), tags)
    elif cmd == "status" and len(sys.argv) > 2:
        mostrar(sys.argv[2])
        print("Na aba Shorts:", {True: "sim", False: "NÃO, foi para Vídeos", None: "não deu para conferir"}[e_short(sys.argv[2])])
    elif cmd == "capa" and len(sys.argv) > 3:
        capa(sys.argv[2], sys.argv[3])
        print("Capa enviada.")
    elif cmd == "apagar" and len(sys.argv) > 2 and "--confirmo" in sys.argv:
        request("DELETE", f"{API}/videos?id={sys.argv[2]}", headers={"Authorization": f"Bearer {token()}"})
        print("Apagado.")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
