#!/usr/bin/env python3
"""Publicação no Instagram (Composio) e no YouTube Shorts (API do YouTube, seu projeto no Google Cloud): prepara,
hospeda, publica (reel, carrossel ou foto), manda o mesmo conteúdo para o story e sobe o reel como Short.
Também agenda na agenda da ponte (dados/agenda.json).

Cada post é uma pasta em projetos/<slug>/ com um publicacao.json:
  {"tipo": "reel" | "carrossel" | "foto",
   "midia": ["renders/master.mp4"]          (reel: 1 vídeo; carrossel: 2 a 10 imagens; foto: 1 imagem),
   "capa": "renders/capa.jpg"               (opcional, só reel),
   "legenda_arquivo": "legenda.txt",
   "story": true,                           (padrão: o reel/foto/1º slide também vai para o story)
   "instagram": false,                      (opcional: Short sem post no Instagram)
   "youtube": {"titulo": "...",             (opcional, só reel: liga o Short; até 100 caracteres)
               "descricao_arquivo": "descricao-youtube.txt",
               "tags": ["..."],
               "midia": "renders/master-yt.mp4"}}   (opcional: render próprio, ex. com o CTA "inscreva-se";
                                                     sem ele, o Short sobe o mesmo vídeo do Instagram)

Uso (da raiz da pasta do Jarvis):
  python3 scripts/publicar.py preparar projetos/<slug>                 # converte e hospeda → projetos/<slug>/.hospedado.json
  python3 scripts/publicar.py ensaio   projetos/<slug>                 # cria os containers SEM publicar (expiram em 24 h)
  python3 scripts/publicar.py publicar projetos/<slug> --confirmo      # publica UMA vez por rede (só com aprovação do dono)
      [--so instagram|youtube]                                          # só uma das redes
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
import youtube as Y  # noqa: E402

ROOT = C.ROOT
LOG = ROOT / "dados" / "publicados.jsonl"
AGENDA = ROOT / "dados" / "agenda.json"


def load(proj):
    d = Path(proj).resolve()
    cfg = json.loads((d / "publicacao.json").read_text())
    cfg["_dir"] = d
    cfg["_legenda"] = (d / cfg.get("legenda_arquivo", "legenda.txt")).read_text().rstrip("\n")
    return cfg


def ffprobe(p):
    return json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(p)],
                                     capture_output=True, text=True, check=True).stdout)


def probe(p):
    d = ffprobe(p)
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
    if not cfg.get("instagram", True):
        sys.exit("Só YouTube: não precisa preparar nem hospedar (o Short sobe direto do arquivo).")
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


def registrar(rec):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def publicar_instagram(cfg):
    marker = cfg["_dir"] / ".publicado.json"
    if marker.exists():
        print(f"Instagram: já publicado ({marker.read_text()})")  # nunca publica duas vezes
        return
    C.me()
    ig = "me"  # a ferramenta do Composio aceita "me" (testado: vale para qualquer conta conectada)
    cid, h = containers(cfg, ig)
    r = C.execute("INSTAGRAM_CREATE_POST", {"ig_user_id": ig, "creation_id": cid})
    if not r.get("successful"):
        sys.exit(f"FALHOU: {r.get('error')}")
    mid = (r.get("data") or {}).get("id")
    last = (C.ok(C.execute("INSTAGRAM_GET_USER_MEDIA", {"limit": 1})).get("data") or [{}])[0]
    rec = {"data": time.strftime("%Y-%m-%dT%H:%M:%S"), "rede": "instagram", "media_id": mid, "permalink": last.get("permalink"),
           "tipo": cfg["tipo"], "projeto": cfg["_dir"].name, "tags": cfg.get("tags", {})}
    marker.write_text(json.dumps(rec, ensure_ascii=False))
    registrar(rec)
    print("PUBLICADO", rec.get("permalink") or mid)
    if cfg.get("story", True):
        story(cfg, ig, h)


def checar_youtube(cfg):
    """Confere o Short antes de subir: reel, título, descrição, vídeo vertical de até 3 min. Devolve (vídeo, título, descrição)."""
    yt, d = cfg["youtube"], cfg["_dir"]
    if cfg["tipo"] != "reel":
        sys.exit("YouTube Shorts só para reel (vídeo).")
    titulo = (yt.get("titulo") or "").strip()
    if not titulo or len(titulo) > 100:
        sys.exit(f"youtube.titulo vazio ou com mais de 100 caracteres ({len(titulo)}).")
    desc = (d / yt.get("descricao_arquivo", "descricao-youtube.txt")).read_text().strip()
    video = d / (yt.get("midia") or cfg["midia"][0])
    info = ffprobe(video)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    dur = float(info["format"]["duration"])
    if dur > Y.MAX_SHORT:
        sys.exit(f"Vídeo com {dur:.0f} s: acima de {Y.MAX_SHORT} s o YouTube não trata como Short.")
    if int(v["height"]) < int(v["width"]):
        sys.exit("Vídeo não é vertical: o YouTube só trata como Short vídeo vertical (ou quadrado) de até 3 min.")
    return video, titulo, desc


def publicar_youtube(cfg):
    marker = cfg["_dir"] / ".publicado-youtube.json"
    if marker.exists():
        print(f"YouTube: já publicado ({marker.read_text()})")
        return
    video, titulo, desc = checar_youtube(cfg)
    Y.eu()  # confirma o token e o canal antes de enviar
    vid = Y.achar_por_titulo(titulo)  # já está no canal (ex.: execução repetida)? não sobe de novo
    if vid:
        print(f"YouTube: Short já no ar (https://youtube.com/shorts/{vid})")
    else:
        vid = Y.upload(video, titulo, desc, tags=cfg["youtube"].get("tags", []))
        if cfg.get("capa"):
            try:
                Y.capa(vid, cfg["_dir"] / cfg["capa"])
            except SystemExit as e:
                print(f"Capa do Short não enviada: {e}")
    rec = {"data": time.strftime("%Y-%m-%dT%H:%M:%S"), "rede": "youtube", "video_id": vid,
           "permalink": f"https://youtube.com/shorts/{vid}", "tipo": "short", "projeto": cfg["_dir"].name, "tags": cfg.get("tags", {})}
    marker.write_text(json.dumps(rec, ensure_ascii=False))
    registrar(rec)
    print("SHORT PUBLICADO", rec["permalink"], "(confira em alguns minutos: python3 scripts/youtube.py status", vid + ")")


def publicar(proj, confirmo, so=None):
    if not confirmo:
        sys.exit("Publicar exige --confirmo (e a aprovação do dono na conversa).")
    cfg = load(proj)
    redes = []
    if cfg.get("instagram", True) and so in (None, "instagram"):
        redes.append(("Instagram", publicar_instagram))
    if cfg.get("youtube") and so in (None, "youtube"):
        redes.append(("YouTube", publicar_youtube))
    if not redes:
        sys.exit("Nada a publicar: confira \"instagram\", \"youtube\" no publicacao.json e o --so.")
    falhas = []
    for nome, fn in redes:  # uma rede falhar não impede a outra
        try:
            fn(cfg)
        except SystemExit as e:
            falhas.append(f"{nome}: {e}")
            print(f"{nome} FALHOU: {e}")
    if falhas:
        sys.exit("\n".join(falhas))


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
        if cfg.get("instagram", True):
            C.me()
            cid, _ = containers(cfg, "me")
            print(f"ENSAIO OK no Instagram: container {cid} pronto, nada publicado (expira em 24 h).")
        if cfg.get("youtube"):
            video, titulo, _ = checar_youtube(cfg)
            Y.eu()
            print(f"ENSAIO OK no YouTube: {video.name} cabe num Short, título \"{titulo}\" (a API não tem rascunho; nada foi enviado).")
    elif cmd == "publicar":
        publicar(proj, "--confirmo" in a, a[a.index("--so") + 1] if "--so" in a else None)
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
