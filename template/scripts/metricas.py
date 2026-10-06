#!/usr/bin/env python3
"""Métricas do Instagram (Composio) → snapshot do dia + resumo por post e por etiqueta. É a matéria-prima do
aprendizado: o /jarvis-insights lê o resumo e atualiza cadernos/instagram.md.

Uso:
  python3 scripts/metricas.py snapshot          # grava dados/instagram/snapshots/<hoje>/{conta,posts}.json
  python3 scripts/metricas.py resumo            # tabela dos posts + médias por etiqueta (do snapshot mais recente)
  python3 scripts/metricas.py resumo --json     # o mesmo em JSON (para o agente)

Etiquetas: cada post publicado pelo publicar.py leva as "tags" do publicacao.json (ex.: {"gancho": "numero",
"formato": "editorial", "horario": "12h"}). O resumo agrupa as métricas por etiqueta para mostrar o que funciona.
"""
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import composio_ig as C  # noqa: E402

ROOT = C.ROOT
SNAPS = ROOT / "dados" / "instagram" / "snapshots"
METRICS = ["views", "reach", "likes", "comments", "saved", "shares", "follows", "profile_visits"]
REEL_METRICS = ["ig_reels_avg_watch_time", "reels_skip_rate"]


def metric(mid, name):
    d = C.ok(C.execute("INSTAGRAM_GET_POST_INSIGHTS", {"ig_post_id": mid, "metric": [name]}))
    for x in d.get("data", []):
        if x.get("name") == name:
            return (x.get("values") or [{}])[0].get("value")
    return None


def snapshot():
    u = C.me()
    media, after = [], None
    while True:
        d = C.ok(C.execute("INSTAGRAM_GET_USER_MEDIA", {"limit": 50, **({"after": after} if after else {})}))
        media += d.get("data", [])
        pg = d.get("paging") or {}
        after = (pg.get("cursors") or {}).get("after") if pg.get("next") else None
        if not after or len(media) >= 100:
            break
    posts = []
    for m in media:
        row = {"id": m["id"], "data": m["timestamp"], "tipo": m.get("media_product_type") or m.get("media_type"),
               "permalink": m.get("permalink"), "legenda": (m.get("caption") or "")[:300]}
        # uma métrica por chamada: em lote a ferramenta descarta as que não valem para o tipo de mídia
        for k in METRICS + (REEL_METRICS if row["tipo"] == "REELS" else []):
            row[k] = metric(m["id"], k)
        posts.append(row)
    out = SNAPS / date.today().isoformat()
    out.mkdir(parents=True, exist_ok=True)
    (out / "conta.json").write_text(json.dumps({k: u.get(k) for k in ("username", "followers_count", "media_count")}, ensure_ascii=False, indent=1))
    (out / "posts.json").write_text(json.dumps(posts, ensure_ascii=False, indent=1))
    print(json.dumps({"snapshot": str(out.relative_to(ROOT)), "posts": len(posts), "seguidores": u.get("followers_count")}))


def resumo(as_json=False):
    snaps = sorted(p for p in SNAPS.glob("*") if (p / "posts.json").exists())
    if not snaps:
        sys.exit("Nenhum snapshot ainda. Rode: python3 scripts/metricas.py snapshot")
    posts = json.loads((snaps[-1] / "posts.json").read_text())
    conta = json.loads((snaps[-1] / "conta.json").read_text())
    tags = {}
    log = ROOT / "dados" / "publicados.jsonl"
    if log.exists():
        for line in log.read_text().splitlines():
            r = json.loads(line)
            tags[str(r.get("media_id"))] = r.get("tags") or {}
    groups = defaultdict(list)
    for p in posts:
        p["tags"] = tags.get(p["id"], {})
        reach = p.get("reach") or 0
        p["envios_por_mil"] = round(1000 * (p.get("shares") or 0) / reach, 1) if reach else None
        p["salvos_por_mil"] = round(1000 * (p.get("saved") or 0) / reach, 1) if reach else None
        for k, v in p["tags"].items():
            groups[f"{k}={v}"].append(p)

    def avg(ps, k):
        vals = [p[k] for p in ps if isinstance(p.get(k), (int, float))]
        return round(sum(vals) / len(vals), 1) if vals else None

    by_tag = {g: {"posts": len(ps), "alcance": avg(ps, "reach"), "skip_rate": avg(ps, "reels_skip_rate"),
                  "retencao_ms": avg(ps, "ig_reels_avg_watch_time"), "envios_por_mil": avg(ps, "envios_por_mil"),
                  "salvos_por_mil": avg(ps, "salvos_por_mil"), "seguiram": avg(ps, "follows")} for g, ps in sorted(groups.items())}
    if as_json:
        print(json.dumps({"snapshot": snaps[-1].name, "conta": conta, "posts": posts, "por_etiqueta": by_tag}, ensure_ascii=False, indent=1))
        return
    print(f"@{conta.get('username')} · {conta.get('followers_count')} seguidores · snapshot {snaps[-1].name}\n")
    print(f"{'data':10} {'tipo':9} {'alcance':>7} {'skip%':>6} {'ret.s':>6} {'envios':>6} {'salvos':>6} {'seg.':>4}  legenda")
    for p in posts[:30]:
        ret = (p.get("ig_reels_avg_watch_time") or 0) / 1000
        print(f"{p['data'][:10]:10} {p['tipo'][:9]:9} {p.get('reach') or 0:>7} {p.get('reels_skip_rate') or '':>6} "
              f"{ret or '':>6} {p.get('shares') or 0:>6} {p.get('saved') or 0:>6} {p.get('follows') or 0:>4}  {p['legenda'][:50]!r}")
    if by_tag:
        print("\nPor etiqueta (média):")
        for g, s in by_tag.items():
            print(f"  {g:30} n={s['posts']}  alcance={s['alcance']}  skip={s['skip_rate']}  envios/mil={s['envios_por_mil']}  salvos/mil={s['salvos_por_mil']}")
    print("\nAmostra pequena = hipótese, não conclusão. Mude uma variável por post para comparar.")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] not in ("snapshot", "resumo"):
        sys.exit(__doc__)
    snapshot() if a[0] == "snapshot" else resumo("--json" in a)
