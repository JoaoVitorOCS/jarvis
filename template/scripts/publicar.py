#!/usr/bin/env python3
"""Publicação no Instagram (Composio): prepara, hospeda, publica (reel, carrossel ou foto) e manda o mesmo conteúdo
para o story. Também agenda na agenda da ponte (dados/agenda.json).

Cada post é uma pasta em projetos/<slug>/ com um publicacao.json:
  {"tipo": "reel" | "carrossel" | "foto",
   "midia": ["renders/master.mp4"]          (reel: 1 vídeo; carrossel: 2 a 10 imagens; foto: 1 imagem),
   "capa": "renders/capa.jpg"               (opcional, só reel),
   "legenda_arquivo": "legenda.txt",
   "story": true}                           (padrão: o reel/foto/1º slide também vai para o story)

Uso (da raiz da pasta do Jarvis):
  python3 scripts/publicar.py preparar projetos/<slug>                 # converte e hospeda → projetos/<slug>/.hospedado.json
  python3 scripts/publicar.py ensaio   projetos/<slug>                 # cria os containers SEM publicar (expiram em 24 h)
  python3 scripts/publicar.py publicar projetos/<slug> --confirmo      # publica UMA vez (só com aprovação do dono)
  python3 scripts/publicar.py agendar  projetos/<slug> 2026-10-07T12:07:00-03:00
  python3 scripts/publicar.py limpar   projetos/<slug>                 # apaga a mídia hospedada depois de publicado

Hospedagem (HOSPEDAGEM no .env; a API do Instagram só aceita URL pública):
  vercel    Vercel Blob grátis (BLOB_READ_WRITE_TOKEN; precisa do CLI: npm i -g vercel)
  servidor  a pasta dados/publico servida pelo Caddy em PUBLIC_URL/publico (versão paga, no servidor)
"""
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import composio_ig as C  # noqa: E402

ROOT = C.ROOT
LOG = ROOT / "dados" / "publicados.jsonl"
AGENDA = ROOT / "dados" / "agenda.json"


def load(proj):
    d = Path(proj).resolve()
    cfg = json.loads((d / "publicacao.json").read_text())
    cfg["_dir"] = d
    cfg["_legenda"] = (d / cfg.get("legenda_arquivo", "legenda.txt")).read_text().rstrip("\n")
    return cfg


def probe(p):
    d = json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(p)],
                                  capture_output=True, text=True, check=True).stdout)
    return float(d["format"]["duration"]), any(s["codec_type"] == "audio" for s in d["streams"])


def prep_video(src):
    dur, has_audio = probe(src)
    if not 3 <= dur <= 900:
        sys.exit(f"Duração {dur:.1f}s fora do limite de reels (3 s a 15 min).")
    out = src.with_name(src.stem + ".ig.mp4")
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-i", str(src)]
    if not has_audio:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest"]
    cmd += ["-map", "0:v:0", "-map", "0:a:0" if has_audio else "1:a:0", "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-r", "30", "-crf", "18", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    return out


def prep_image(src):
    out = src.with_name(src.stem + ".ig.jpg")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-q:v", "2", str(out)], check=True)
    return out


def host(p):
    mode = C.env("HOSPEDAGEM", "vercel")
    if mode == "servidor":
        pub = ROOT / "dados" / "publico"
        pub.mkdir(parents=True, exist_ok=True)
        name = f"{secrets.token_hex(8)}-{p.name}"
        shutil.copy(p, pub / name)
        return f"{C.env('PUBLIC_URL').rstrip('/')}/publico/{name}"
    tok = C.env("BLOB_READ_WRITE_TOKEN") or sys.exit("BLOB_READ_WRITE_TOKEN ausente no .env (veja docs/HOSPEDAGEM.md).")
    # o token vai pelo ambiente: algumas versões do CLI ignoram --rw-token e só leem BLOB_READ_WRITE_TOKEN
    r = subprocess.run(["vercel", "blob", "put", str(p), "--access", "public", "--pathname", f"jarvis/{p.name}",
                        "--add-random-suffix", "true", "--non-interactive"], capture_output=True, text=True, timeout=600, cwd="/tmp",
                       env={**os.environ, "BLOB_READ_WRITE_TOKEN": tok})
    m = re.search(r"https://\S+\.blob\.vercel-storage\.com/\S+", r.stdout + r.stderr)
    if r.returncode or not m:
        sys.exit(f"Falha no upload de {p.name}:\n{(r.stdout + r.stderr)[-800:]}")
    return m.group(0).rstrip(").,")


def unhost(urls):
    if C.env("HOSPEDAGEM", "vercel") == "servidor":
        for u in urls:
            (ROOT / "dados" / "publico" / u.rsplit("/", 1)[-1]).unlink(missing_ok=True)
        return
    subprocess.run(["vercel", "blob", "del", *urls, "--non-interactive"], check=True, timeout=120, cwd="/tmp",
                   env={**os.environ, "BLOB_READ_WRITE_TOKEN": C.env("BLOB_READ_WRITE_TOKEN")})


def preparar(proj):
    cfg = load(proj)
    d = cfg["_dir"]
    midia = [d / m for m in cfg["midia"]]
    if cfg["tipo"] == "reel":
        v = prep_video(midia[0])
        capa = d / cfg["capa"] if cfg.get("capa") else None
        if not capa:
            capa = v.with_name(v.stem + ".capa.jpg")
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "1", "-i", str(v), "-frames:v", "1", "-q:v", "2", str(capa)], check=True)
        out = {"midia": [host(v)], "capa": host(prep_image(capa))}
    else:
        if cfg["tipo"] == "carrossel" and not 2 <= len(midia) <= 10:
            sys.exit("Carrossel precisa de 2 a 10 imagens.")
        out = {"midia": [host(prep_image(m)) for m in midia]}
    (d / ".hospedado.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


def wait(cid):
    for _ in range(40):
        s = C.ok(C.execute("INSTAGRAM_GET_POST_STATUS", {"creation_id": cid}))
        st = s.get("status_code") or s.get("status")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            sys.exit(f"processamento falhou: {s}")
        time.sleep(15)
    sys.exit("processamento não terminou em 10 min")


def container(args):
    r = C.execute("INSTAGRAM_CREATE_MEDIA_CONTAINER", args)
    if not r.get("successful"):
        sys.exit(f"container falhou: {r.get('error')}")
    return r["data"].get("id") or r["data"].get("creation_id")


def containers(cfg, ig):
    h = json.loads((cfg["_dir"] / ".hospedado.json").read_text())
    cap = cfg["_legenda"]
    if cfg["tipo"] == "reel":
        cid = container({"ig_user_id": ig, "content_type": "reel", "video_url": h["midia"][0], "cover_url": h.get("capa"), "caption": cap})
    elif cfg["tipo"] == "foto":
        cid = container({"ig_user_id": ig, "content_type": "photo", "image_url": h["midia"][0], "caption": cap})
    else:
        kids = [container({"ig_user_id": ig, "content_type": "carousel_item", "image_url": u}) for u in h["midia"]]
        for k in kids:
            wait(k)
        r = C.execute("INSTAGRAM_CREATE_CAROUSEL_CONTAINER", {"ig_user_id": ig, "children": kids, "caption": cap})
        if not r.get("successful"):
            sys.exit(f"carrossel falhou: {r.get('error')}")
        cid = r["data"].get("id") or r["data"].get("creation_id")
    wait(cid)
    return cid, h


def story(cfg, ig, h):
    url = h["midia"][0]
    args = {"ig_user_id": ig, "media_type": "STORIES", **({"video_url": url} if cfg["tipo"] == "reel" else {"image_url": url})}
    cid = container(args)
    wait(cid)
    r = C.execute("INSTAGRAM_CREATE_POST", {"ig_user_id": ig, "creation_id": cid})
    print("STORY PUBLICADO" if r.get("successful") else f"STORY FALHOU: {r.get('error')}")


def publicar(proj, confirmo):
    if not confirmo:
        sys.exit("Publicar exige --confirmo (e a aprovação do dono na conversa).")
    cfg = load(proj)
    marker = cfg["_dir"] / ".publicado.json"
    if marker.exists():
        sys.exit(f"Já publicado: {marker.read_text()}")  # nunca publica duas vezes
    C.me()
    ig = "me"  # a ferramenta do Composio aceita "me" (testado: vale para qualquer conta conectada)
    cid, h = containers(cfg, ig)
    r = C.execute("INSTAGRAM_CREATE_POST", {"ig_user_id": ig, "creation_id": cid})
    if not r.get("successful"):
        sys.exit(f"FALHOU: {r.get('error')}")
    mid = (r.get("data") or {}).get("id")
    last = (C.ok(C.execute("INSTAGRAM_GET_USER_MEDIA", {"limit": 1})).get("data") or [{}])[0]
    rec = {"data": time.strftime("%Y-%m-%dT%H:%M:%S"), "media_id": mid, "permalink": last.get("permalink"), "tipo": cfg["tipo"],
           "projeto": cfg["_dir"].name, "tags": cfg.get("tags", {})}
    marker.write_text(json.dumps(rec, ensure_ascii=False))
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("PUBLICADO", rec.get("permalink") or mid)
    if cfg.get("story", True):
        story(cfg, ig, h)


def agendar(proj, quando):
    from datetime import datetime
    datetime.fromisoformat(quando)  # valida
    items = json.loads(AGENDA.read_text()) if AGENDA.exists() else []
    rel = str(Path(proj).resolve().relative_to(ROOT))
    items.append({"at": quando, "nome": f"publicar {rel}", "run": ["python3", "scripts/publicar.py", "publicar", rel, "--confirmo"]})
    AGENDA.parent.mkdir(parents=True, exist_ok=True)
    AGENDA.write_text(json.dumps(items, ensure_ascii=False, indent=1))
    print(f"Agendado para {quando}. A ponte do Jarvis precisa estar rodando nesse horário.")


def main(a):
    if len(a) < 2:
        sys.exit(__doc__)
    cmd, proj = a[0], a[1]
    if cmd == "preparar":
        preparar(proj)
    elif cmd == "ensaio":
        cfg = load(proj)
        C.me()
        cid, _ = containers(cfg, "me")
        print(f"ENSAIO OK: container {cid} pronto, nada publicado (expira em 24 h).")
    elif cmd == "publicar":
        publicar(proj, "--confirmo" in a)
    elif cmd == "agendar":
        agendar(proj, a[2])
    elif cmd == "limpar":
        d = Path(proj).resolve()
        h = json.loads((d / ".hospedado.json").read_text())
        unhost(h["midia"] + ([h["capa"]] if h.get("capa") else []))
        print("mídia hospedada apagada")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
