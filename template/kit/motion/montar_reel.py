#!/usr/bin/env python3
"""Reel editorial (só texto + efeitos + música) a partir de um reel.json e da SUA marca (marca/marca.json).

Estrutura: gancho (frame 0 já legível) → trilho: a câmera corre de lado por 2 a 6 cards, trocando de tema a cada par
com uma transição de pinceladas → fecho com botão clicado (Seguir/Salvar/Comentar) → nome/logo → volta ao gancho (loop).

Uso (da raiz da pasta do Jarvis):
  python3 kit/motion/montar_reel.py projetos/<slug>                   # gera projetos/<slug>/reel/index.html
  cd projetos/<slug>/reel && npx --yes hyperframes check && npx --yes hyperframes render . -o ../renders/reel.mp4
  python3 kit/motion/montar_reel.py projetos/<slug> --mixar           # junta a música (−6 dB) e fecha o master em LUFS_ALVO

projetos/<slug>/reel.json:
  {"gancho": ["Linha 1 do gancho", "linha 2 com *destaque*"], "subgancho": "frase curta abaixo (opcional)",
   "cards": [{"rotulo": "1/3", "titulo": "nome", "texto": "o que é", "nota": "→ quando usar", "numero": 1234}],
   "fecho": ["Salva pra usar", "no *próximo post.*"], "botao": "Salvar", "botao_feito": "Salvo ✓",
   "musica": "kit/musica/minha-faixa.wav", "musica_inicio": 0, "lufs": -16}
Marcação: *palavra* = destaque (fonte de destaque com o marca-texto da cor de acento).
"""
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
KIT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
from carrossel import DEFAULT_FONTS, DEFAULT_TOKENS  # noqa: E402

STEP = 2.8


def words(line):
    out = []
    for p in re.split(r"(\*[^*]+\*)", line):
        if p.startswith("*"):
            ws = " ".join(f'<span class="wm"><span class="wi">{html.escape(w)}</span></span>' for w in p[1:-1].split())
            out.append(f'<span class="acc"><i class="mk"></i>{ws}</span>')
        elif p.strip():
            out.append(" ".join(f'<span class="wm"><span class="wi">{html.escape(w)}</span></span>' for w in p.split()))
    return " ".join(out)


def title(lines):
    return "".join(f'<div class="ln">{words(l)}</div>' for l in lines)


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    proj = Path(a[0]).resolve()
    cfg = json.loads((proj / "reel.json").read_text())
    marca = json.loads((ROOT / "marca" / "marca.json").read_text())
    if "--mixar" in a:
        return mix(proj, cfg)
    cards = cfg["cards"]
    if not 2 <= len(cards) <= 6:
        sys.exit("Use de 2 a 6 cards.")
    claro = {**DEFAULT_TOKENS["claro"], **marca.get("temas", {}).get("claro", {})}
    escuro = {**DEFAULT_TOKENS["escuro"], **marca.get("temas", {}).get("escuro", {})}
    fontes = {**DEFAULT_FONTS, **marca.get("fontes", {})}
    # 3 temas que se alternam a cada par de cards: escuro, claro e um com o fundo na cor de acento
    temas = [("escuro", escuro["bg"], escuro["ink"], escuro["surface"], escuro["acc"], escuro["acc_ink"]),
             ("claro", claro["bg"], claro["ink"], claro["surface"], claro["acc"], claro["acc_ink"]),
             ("acento", claro["acc"], claro["acc_ink"], escuro["bg"], escuro["acc"], escuro["acc_ink"])]

    T = {"trilho": 5.8}
    t, sw, ca = T["trilho"] + 1.3, [], []
    for i in range(len(cards)):
        if i and i % 2 == 0:
            sw.append(round(t, 3))
            t += 0.6
        ca.append(round(t, 3))
        t += STEP
    T.update(sw=sw, ca=ca, cta=round(t + 0.4, 3))
    T["total"] = round(T["cta"] + 5.6, 2)

    cells, cardhtml = [], []
    for i, c in enumerate(cards):
        nome, bg, ink, surf, acc, acc_ink = temas[(i // 2) % 3]
        cells.append(f'<div class="tc" style="left:{i * 1080}px;background:{bg}"></div>')
        num = f'<div class="rs">{c["numero"]:,}</div>'.replace(",", ".") if isinstance(c.get("numero"), int) else ""
        cardhtml.append(
            f'<div class="repo" id="rp{i}" style="left:{i * 1080 + 80}px;background:{surf};color:{ink if nome != "acento" else "#F5F5F5"};'
            f'box-shadow:12px 12px 0 {acc if nome != "acento" else ink}">'
            f'<div class="rk">{html.escape(c.get("rotulo", f"{i + 1}/{len(cards)}"))}</div>'
            f'<div class="rn" style="color:{acc if nome != "claro" else claro["acc_text"]}">{html.escape(c["titulo"])}</div>'
            f'<div class="rd">{html.escape(c.get("texto", ""))}</div>{num}'
            + (f'<div class="ru">{html.escape(c["nota"])}</div>' if c.get("nota") else "") + "</div>")

    DUR = {"impact": 1.6, "riser-1.5s": 1.5, "whoosh": 0.55, "pop": 0.17, "tick": 0.09, "chime": 0.95, "snap": 0.16, "counter": 0.6}
    fx = [(0.03, "impact", .25), (1.2, "pop", .12), (T["trilho"] - 0.6, "whoosh", .15)]
    for i, x in enumerate(ca):
        fx += [(x - 0.45, "whoosh", .1)] + [(x + 0.1 + k * 0.07, "tick", .04) for k in range(5)] + [(x + 0.9, "counter", .1)]
    fx += [(s - 0.6, "riser-1.5s", .12) for s in sw]
    A = T["cta"]
    fx += [(A - 0.6, "whoosh", .15), (A + 1.2, "snap", .1), (A + 1.6, "pop", .13), (A + 2.55, "pop", .16), (A + 2.6, "chime", .13),
           (A + 3.0, "snap", .12), (T["total"] - 0.9, "whoosh", .13)]
    fx = sorted((round(t, 3), n, v) for t, n, v in fx if 0 <= t < T["total"] - 0.1)
    audio = "\n".join(f'<audio id="sfx{i}" data-start="{t}" data-duration="{DUR[n]}" data-track-index="{2 + i % 9}" '
                      f'data-volume="{v}" src="sfx/{n}.wav"></audio>' for i, (t, n, v) in enumerate(fx))

    gf = "".join(f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={f.replace(" ", "+")}{v}&display=block">'
                 for k, f in fontes.items() for v in ([":wght@400;700"] if k in ("titulo", "texto") else [":ital@0;1"] if k == "destaque" else []) + [""])
    rep = {
        "__FONTS__": gf, "__F_TITULO__": fontes["titulo"], "__F_TEXTO__": fontes["texto"], "__F_MONO__": fontes["mono"],
        "__F_DESTAQUE__": fontes["destaque"], "__BG__": escuro["bg"], "__INK__": escuro["ink"], "__ACC__": escuro["acc"],
        "__ACC_INK__": escuro["acc_ink"], "__CBG__": claro["bg"], "__CINK__": claro["ink"], "__CACC__": claro["acc"],
        "__H1__": title(cfg["gancho"]), "__SUB_JS__": json.dumps(cfg.get("subgancho", "")), "__CELLS__": "".join(cells),
        "__CARDS__": "\n".join(cardhtml), "__HA__": title(cfg.get("fecho", ["Segue pra ver o *próximo.*"])),
        "__BTN__": html.escape(cfg.get("botao", "Seguir")), "__BTN_OK__": json.dumps(cfg.get("botao_feito", "Seguindo ✓")),
        "__NOME__": json.dumps(marca.get("nome", "").upper()[:24]), "__N__": str(len(cards)), "__T__": json.dumps(T),
        "__TOTAL__": str(T["total"]), "__AUDIO__": audio,
        "__THEMES__": json.dumps([{"ink": (x[2] if x[0] != "acento" else x[2]), "mk": x[4] if x[0] != "acento" else x[2]} for x in temas]),
    }
    out = (KIT / "reel.html.tpl").read_text()
    for k, v in rep.items():
        out = out.replace(k, v)
    dst = proj / "reel"
    dst.mkdir(exist_ok=True)
    (dst / "index.html").write_text(out)
    shutil.copy(KIT / "ed.js", dst / "ed.js")
    shutil.copytree(KIT / "sfx", dst / "sfx", dirs_exist_ok=True)
    if not (dst / "hyperframes.json").exists():
        (dst / "hyperframes.json").write_text('{"paths": {"assets": "assets"}}\n')
    (proj / "renders").mkdir(exist_ok=True)
    print(json.dumps({"index": str((dst / "index.html").relative_to(ROOT)), "duracao": T["total"], "cards": len(cards)}))


def mix(proj, cfg):
    """Música −6 dB sob os efeitos, depois o master inteiro no LUFS alvo (ganho linear, sem compressão)."""
    src = proj / "renders" / "reel.mp4"
    dst = proj / "renders" / "master.mp4"
    music = ROOT / cfg["musica"] if cfg.get("musica") else None
    tmp = dst.with_suffix(".tmp.mov")
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)],
                                 capture_output=True, text=True).stdout)
    if music:
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(src), "-ss", str(cfg.get("musica_inicio", 0)), "-i", str(music),
                        "-filter_complex", f"[1:a]atrim=0:{total},afade=t=out:st={total - 1.2}:d=1.2,volume=0.5[m];[0:a][m]amix=inputs=2:duration=first:normalize=0[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "pcm_s16le", str(tmp)], check=True)
    else:
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(src), "-c:v", "copy", "-c:a", "pcm_s16le", str(tmp)], check=True)
    meas = subprocess.run(["ffmpeg", "-nostdin", "-i", str(tmp), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", meas)[-1])
    alvo = float(cfg.get("lufs", -16))
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(tmp), "-af", f"volume={alvo - I:.2f}dB", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(dst)], check=True)
    tmp.unlink()
    pub = proj / "publicacao.json"
    if not pub.exists():
        pub.write_text(json.dumps({"tipo": "reel", "midia": ["renders/master.mp4"], "legenda_arquivo": "legenda.txt", "story": True,
                                   "tags": cfg.get("tags", {})}, ensure_ascii=False, indent=1))
    print(json.dumps({"master": str(dst.relative_to(ROOT)), "lufs": alvo}))


if __name__ == "__main__":
    main()
