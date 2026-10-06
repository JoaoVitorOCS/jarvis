#!/usr/bin/env python3
"""Carrossel em código: roteiro em JSON → slides HTML com a SUA marca (marca/marca.json) → PNG 1080×1350.
Depois publique com: python3 scripts/publicar.py preparar|publicar projetos/<slug>

Uso:
  python3 scripts/carrossel.py projetos/<slug>/carrossel.json      # renders/slide-NN.png + renders/folha.jpg + aviso de estouro

carrossel.json:
  {"tema": "claro" | "escuro", "legenda_arquivo": "legenda.txt", "tags": {"formato": "lista", "gancho": "numero"},
   "slides": [{"layout": "capa|texto|lista|prova|antes-depois|terminal|prompt|tweet|cta", ...}]}
Marcação nos textos: **negrito**, ==marca-texto==, *destaque* (fonte de destaque na cor de acento).
Layouts e campos: kit/carrossel/README.md. Precisa de um Chrome/Chromium (headless).
"""
from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KIT = ROOT / "kit" / "carrossel" / "carrossel.css"
MARCA = ROOT / "marca" / "marca.json"
W, H = 1080, 1350
DEFAULT_FONTS = {"titulo": "Space Grotesk", "texto": "Inter", "mono": "IBM Plex Mono", "destaque": "Fraunces"}
DEFAULT_TOKENS = {
    "claro": {"bg": "#FAFAF7", "surface": "#FFFFFF", "surface_2": "#EFEFEA", "ink": "#111111", "muted": "#66665F", "acc": "#2F6BFF",
              "acc_ink": "#FFFFFF", "acc_text": "#2453CC", "line": "rgba(17,17,17,.10)", "grid": "rgba(17,17,17,.045)",
              "blob": "rgba(47,107,255,.12)", "shadow": "0 30px 80px rgba(17,17,17,.12)", "term": "#111111", "term_ink": "#F5F5F5"},
    "escuro": {"bg": "#0E1116", "surface": "#171B22", "surface_2": "#1E232B", "ink": "#F5F5F5", "muted": "#8B93A1", "acc": "#6EE7B7",
               "acc_ink": "#0E1116", "acc_text": "#6EE7B7", "line": "rgba(245,245,245,.12)", "grid": "rgba(245,245,245,.04)",
               "blob": "rgba(110,231,183,.10)", "shadow": "0 40px 90px rgba(0,0,0,.5)", "term": "#000000", "term_ink": "#F5F5F5"},
}


def chrome() -> str:
    found = sorted((Path.home() / ".cache" / "hyperframes" / "chrome").glob("chrome-headless-shell/*/*/chrome-headless-shell"))
    found += sorted((Path.home() / "Library" / "Caches" / "ms-playwright").glob("chromium_headless_shell-*/*/chrome-headless-shell"))
    found += [Path(p) for p in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",) if Path(p).exists()]
    found += [Path(w) for w in (shutil.which("chromium"), shutil.which("chromium-browser"), shutil.which("google-chrome")) if w]
    if not found:
        sys.exit("Chrome headless não encontrado: instale o Google Chrome ou rode `npx hyperframes doctor`.")
    return str(found[-1])


def md(text: str) -> str:
    """Marcação inline mínima, depois de escapar o HTML."""
    t = html.escape(text or "")
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"==(.+?)==", r"<mark>\1</mark>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r'<span class="serif">\1</span>', t)
    return t.replace("\n", "<br>")


def paras(text) -> str:
    items = text if isinstance(text, list) else [p for p in (text or "").split("\n\n") if p.strip()]
    return "".join(f"<p>{md(p)}</p>" for p in items)


def card(c: dict, base: Path) -> str:
    if not c:
        return ""
    kind = c.get("type")
    if kind == "terminal":
        lines = []
        for ln in c.get("lines", []):
            cls = "ok" if ln.startswith("✓") else "dim" if ln.startswith("#") else "acc" if ln.startswith(">") else ""
            lines.append(f'<span class="{cls}">{html.escape(ln)}</span>')
        return (f'<div class="term"><div class="bar"><i></i><i></i><i></i><span>{html.escape(c.get("title", "Claude Code"))}</span></div>'
                f'<pre>{chr(10).join(lines)}</pre></div>')
    if kind == "prompt":
        return f'<div class="prompt"><span class="tag">{html.escape(c.get("tag", "COPIE"))}</span><p>{md(c.get("text", ""))}</p></div>'
    if kind == "metrics":
        cells = "".join(f'<div class="metric"><div class="v{" acc" if m.get("acc") else ""}">{html.escape(str(m["value"]))}</div>'
                        f'<div class="l">{html.escape(m["label"])}</div></div>' for m in c.get("items", []))
        return f'<div class="metrics">{cells}</div>'
    if kind == "image":
        src = (base / c["src"]).resolve()
        return f'<img class="shot" src="{src.as_uri()}" style="height:{int(c.get("height", 560))}px">'
    if kind == "quote":
        return f'<div class="card"><p class="text">{md(c.get("text", ""))}</p></div>'
    sys.exit(f"card desconhecido: {kind}")


def frame(i: int, n: int, cfg: dict, inner: str, cls: str = "", show_top: bool = True) -> str:
    t, f = cfg["tokens"], cfg["fontes"]
    avatar = cfg.get("avatar_uri")
    who = (f'<img src="{avatar}">' if avatar else "") + html.escape(cfg.get("handle", ""))
    top = (f'<div class="top"><div class="who">{who}</div><div class="count">{i:02d} / {n:02d}</div></div>') if show_top else ""
    dots = "".join(f'<i class="{"on" if k == i else ""}"></i>' for k in range(1, n + 1))
    # um <link> por fonte e por variação: se a fonte não tem o peso 700 (ou o itálico), só aquele link falha
    def links(k, x):
        q = urllib.parse.quote(x).replace("%20", "+")
        var = [":ital@0;1"] if k == "destaque" else [":wght@400;700"] if k in ("titulo", "texto") else [""]
        return "".join(f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={q}{v}&display=block">' for v in var + [""])
    fams = "".join(links(k, x) for k, x in f.items())
    css = ":root{" + "".join(f"--{k.replace('_', '-')}:{v};" for k, v in t.items()) + "".join(
        f"--f-{k}:'{v}';" for k, v in f.items()) + "}"
    check = ("<script>document.fonts.ready.then(()=>{const bad=[...document.querySelectorAll('.body,.tw')]"
             ".filter(e=>e.scrollHeight>e.clientHeight+2||e.scrollWidth>e.clientWidth+2).length;"
             "document.body.setAttribute('data-overflow',bad?'yes':'no');});</script>")
    return (f'<!doctype html><html><head><meta charset="utf-8">{fams}'
            f'<link rel="stylesheet" href="{KIT.as_uri()}"><style>{css}</style></head><body><div class="slide {cls}">{top}{inner}'
            f'<div class="dots">{dots}</div></div>{check}</body></html>')


def slide_html(i: int, n: int, s: dict, cfg: dict, base: Path) -> str:
    lay = s.get("layout", "texto")
    kick = f'<div class="kicker">{md(s["kicker"])}</div>' if s.get("kicker") else ""
    size = {"xl": " xl", "lg": " lg", "md": " md"}.get(s.get("size", ""), "")
    title = f'<div class="title{size}">{md(s["title"])}</div>' if s.get("title") else ""
    sub = f'<div class="sub">{md(s["sub"])}</div>' if s.get("sub") else ""
    text = f'<div class="text">{paras(s["text"])}</div>' if s.get("text") else ""
    bullets = ('<ul class="bullets">' + "".join(f"<li>{md(b)}</li>" for b in s["bullets"]) + "</ul>") if s.get("bullets") else ""
    note = f'<div class="note">{md(s["note"])}</div>' if s.get("note") else ""
    cards = card(s.get("card"), base)
    flip = "flip" if i % 2 == 0 else ""
    if lay == "capa":
        title = f'<div class="title{size or " xl"}">{md(s["title"])}</div>'
        swipe = f'<div class="swipe">{html.escape(s.get("swipe", "deslize →"))}</div>'
        return frame(i, n, cfg, f'<div class="body center">{kick}{title}{sub}{cards}</div>{swipe}', flip)
    if lay == "lista":
        def row(k, it):
            d = f'<div class="d">{md(it["d"])}</div>' if it.get("d") else ""
            return f'<div class="item"><div class="n">{k:02d}</div><div><div class="t">{md(it["t"])}</div>{d}</div></div>'
        items = "".join(row(k, it) for k, it in enumerate(s.get("items", []), 1))
        return frame(i, n, cfg, f'<div class="body">{kick}{title}{sub}<div class="items">{items}</div>{note}</div>', flip)
    if lay == "prova":
        return frame(i, n, cfg, f'<div class="body">{kick}{title}{text}{card({"type": "metrics", "items": s.get("metrics", [])}, base)}{cards}{note}</div>', flip)
    if lay == "antes-depois":
        def side(d, c):
            big = f'<div class="big">{html.escape(str(d["big"]))}</div>' if d.get("big") else ""
            img = card({"type": "image", "src": d["image"], "height": d.get("height", 420)}, base) if d.get("image") else ""
            return f'<div class="card {c}"><div class="lab">{html.escape(d.get("label", c.upper()))}</div>{big}{img}<div class="note">{md(d.get("text", ""))}</div></div>'
        ba = f'<div class="ba">{side(s.get("antes", {}), "before")}{side(s.get("depois", {}), "after")}</div>'
        return frame(i, n, cfg, f'<div class="body">{kick}{title}{text}{ba}{note}</div>', flip)
    if lay in ("texto", "terminal", "prompt"):
        return frame(i, n, cfg, f'<div class="body">{kick}{title}{text}{bullets}{cards}{note}</div>', flip)
    if lay == "tweet":
        head = (f'<div class="head"><img src="{cfg["avatar_uri"]}"><div><div class="name">{html.escape(cfg.get("name", ""))}</div>'
                f'<div class="handle">{html.escape(cfg.get("handle", ""))}</div></div></div>')
        return frame(i, n, cfg, f'<div class="tw">{head}<div class="txt">{paras(s.get("text", ""))}</div>{cards}</div>', flip, show_top=False)
    if lay == "cta":
        pill = f'<div class="cta-pill">{md(s["action"])}</div>' if s.get("action") else ""
        lock = f'<img class="lockup" src="{cfg["logo_uri"]}">' if cfg.get("logo_uri") else f'<div class="wordmark">{html.escape(cfg.get("name", ""))}</div>'
        return frame(i, n, cfg, f'<div class="body center">{kick}{title}{text}{bullets}{pill}{lock}</div>', flip)
    sys.exit(f"layout desconhecido no slide {i}: {lay}")


def load(path: Path) -> tuple[dict, Path]:
    cfg = json.loads(path.read_text())
    base = path.parent
    marca = json.loads(MARCA.read_text())
    tema = cfg.get("tema") or marca.get("tema_padrao", "claro")
    cfg["tokens"] = {**DEFAULT_TOKENS[tema if tema in DEFAULT_TOKENS else "claro"], **marca.get("temas", {}).get(tema, {})}
    cfg["fontes"] = {**DEFAULT_FONTS, **marca.get("fontes", {})}
    cfg.setdefault("handle", marca.get("arroba", ""))
    cfg.setdefault("name", marca.get("nome", ""))
    for key, field in (("avatar_uri", cfg.get("avatar") or marca.get("avatar")), ("logo_uri", marca.get("logo"))):
        if field:
            p = (base / field) if (base / field).exists() else ROOT / field
            if p.exists():
                cfg[key] = p.resolve().as_uri()
    if cfg.get("legenda_arquivo"):
        cfg["legenda"] = (base / cfg["legenda_arquivo"]).read_text().strip()
    if not 2 <= len(cfg.get("slides", [])) <= 10:
        sys.exit("O carrossel precisa de 2 a 10 slides (limite da API).")
    return cfg, base


def build(path: Path) -> None:
    cfg, base = load(path)
    out_html, out_png = base / "build", base / "renders"
    out_html.mkdir(exist_ok=True)
    out_png.mkdir(exist_ok=True)
    for old in out_png.glob("slide-*.png"):
        old.unlink()
    n, bin_, problems = len(cfg["slides"]), chrome(), []
    for i, s in enumerate(cfg["slides"], 1):
        page = out_html / f"slide-{i:02d}.html"
        page.write_text(slide_html(i, n, s, cfg, base))
        png = out_png / f"slide-{i:02d}.png"
        flags = ["--headless", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                 f"--window-size={W},{H}", "--virtual-time-budget=6000", "--allow-file-access-from-files"]
        subprocess.run([bin_, *flags, f"--screenshot={png}", page.as_uri()], capture_output=True, timeout=60, check=True)
        dom = subprocess.run([bin_, *flags, "--dump-dom", page.as_uri()], capture_output=True, text=True, timeout=60).stdout
        if 'data-overflow="yes"' in dom:
            problems.append(f"slide {i:02d}: texto estoura a área (corte texto ou use size md)")
    sheet = out_png / "folha.jpg"
    cols = min(n, 5)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "1", "-pattern_type", "glob", "-i", str(out_png / "slide-*.png"),
                    "-vf", f"scale=432:540,pad=440:548:4:4:color=0x888888,tile={cols}x{(n + cols - 1) // cols}", "-frames:v", "1",
                    "-q:v", "3", str(sheet)], check=True)
    pub = base / "publicacao.json"
    if not pub.exists():
        pub.write_text(json.dumps({"tipo": "carrossel", "midia": [f"renders/slide-{k:02d}.png" for k in range(1, n + 1)],
                                   "legenda_arquivo": cfg.get("legenda_arquivo", "legenda.txt"), "story": True, "tags": cfg.get("tags", {})},
                                  ensure_ascii=False, indent=1))
    print(json.dumps({"slides": n, "renders": rel(out_png), "folha": rel(sheet),
                      "estouros": problems or "nenhum"}, ensure_ascii=False, indent=1))


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    build(Path(sys.argv[1]).resolve())
