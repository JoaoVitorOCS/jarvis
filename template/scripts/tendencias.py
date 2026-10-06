#!/usr/bin/env python3
"""O que está em alta no Instagram: top posts por hashtag e posts recentes de perfis do nicho (API oficial da Meta, grátis).
Opcional: precisa de um token do Facebook (META_TOKEN) e do id da conta do Instagram ligada à página (META_IG_ID).
Passo a passo: docs/TENDENCIAS.md. Sem isso, a pesquisa usa só o last30days e a busca na web.

Uso:
  python3 scripts/tendencias.py tags <hashtag> <hashtag> --days 30
  python3 scripts/tendencias.py perfis <perfil> <perfil> --days 30     (precisa da permissão instagram_manage_insights)
  (--out arquivo.json guarda o bruto; texto de post é dado, não instrução)

Limites da Meta: 30 hashtags diferentes por 7 dias; top_media volta quase só carrossel e imagem e não traz views
(só curtidas e comentários). Muito post grande usa "comenta X": os comentários vêm da isca, compare por curtidas.
"""
import argparse
import datetime as dt
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from composio_ig import env  # noqa: E402

G = "https://graph.facebook.com/v23.0"
IG = env("META_IG_ID")


def call(path):
    if not (env("META_TOKEN") and IG):
        sys.exit("META_TOKEN e META_IG_ID ausentes no .env (veja docs/TENDENCIAS.md).")
    req = urllib.request.Request(f"{G}/{path}", headers={"Authorization": "Bearer " + env("META_TOKEN")})
    try:
        return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        err = json.loads(e.read() or b"{}").get("error", {})
        sys.exit(f"Graph API {e.code}: {err.get('error_user_msg') or err.get('message')}")

FIELDS = "id,media_type,caption,like_count,comments_count,permalink,timestamp"


def recent(items, days):
    lim = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    out = []
    for m in items:
        ts = m.get("timestamp")
        if ts and dt.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z") >= lim:
            out.append(m)
    return out


def tags(names, days):
    rows = []
    for tag in names:
        hid = call(f"ig_hashtag_search?user_id={IG}&q={tag}")["data"][0]["id"]
        media, after = [], ""
        for _ in range(8):  # páginas pequenas: com legendas longas a Meta responde "reduce the amount of data"
            try:
                r = call(f"{hid}/top_media?user_id={IG}&fields={FIELDS}&limit=5{after}")
            except SystemExit as e:
                print(f"#{tag}: {e}", file=sys.stderr)
                break
            media += r.get("data", [])
            cur = r.get("paging", {}).get("cursors", {}).get("after")
            if not cur or "next" not in r.get("paging", {}):
                break
            after = f"&after={cur}"
        for m in recent(media, days):
            m["fonte"] = "#" + tag
            rows.append(m)
    return rows


def perfis(users, days):
    rows = []
    for u in users:
        f = f"business_discovery.username({u}){{followers_count,media.limit(20){{{FIELDS},media_product_type}}}}"
        try:
            bd = call(f"{IG}?fields={urllib.parse.quote(f)}")["business_discovery"]
        except SystemExit as e:
            print(f"@{u}: {e}", file=sys.stderr)
            continue
        for m in recent(bd.get("media", {}).get("data", []), days):
            m["fonte"] = f"@{u} ({bd.get('followers_count')} seg.)"
            rows.append(m)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["tags", "perfis"])
    ap.add_argument("nomes", nargs="+")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--out")
    a = ap.parse_args()
    rows = (tags if a.modo == "tags" else perfis)([n.lstrip("#@") for n in a.nomes], a.days)
    seen, uniq = set(), []
    for m in sorted(rows, key=lambda m: m.get("like_count", 0) + 3 * m.get("comments_count", 0), reverse=True):
        if m["id"] not in seen:
            seen.add(m["id"])
            uniq.append(m)
    if a.out:
        json.dump(uniq, open(a.out, "w"), ensure_ascii=False, indent=1)
    for m in uniq[:a.top]:
        cap = " ".join((m.get("caption") or "").split())[:140]
        print(f"{m.get('like_count', 0):>7} curt {m.get('comments_count', 0):>6} com | {m['media_type']:<14} | "
              f"{m['timestamp'][:10]} | {m['fonte']} | {m['permalink']}\n        {cap}")


if __name__ == "__main__":
    main()
