#!/usr/bin/env python3
"""Instagram pelo Composio (plano gratuito): conectar a conta e executar ferramentas.

.env: COMPOSIO_API_KEY (chave do projeto no dashboard do Composio) e, opcional, COMPOSIO_USER_ID (padrão "jarvis").

Uso:
  python3 scripts/composio_ig.py conectar              # devolve o link para autorizar o seu Instagram
  python3 scripts/composio_ig.py contas                # contas conectadas
  python3 scripts/composio_ig.py eu                    # @ e id da conta (confere se está tudo certo)
  python3 scripts/composio_ig.py ferramentas           # lista as ferramentas do Instagram
  python3 scripts/composio_ig.py schema INSTAGRAM_GET_USER_INFO
  python3 scripts/composio_ig.py exec INSTAGRAM_GET_USER_MEDIA '{"limit": 5}'
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://backend.composio.dev/api"


def env(name, default=""):
    if os.environ.get(name):
        return os.environ[name]
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip().strip('"')
    return default


USER = env("COMPOSIO_USER_ID", "jarvis")


def call(method, path, body=None, query=None):
    url = BASE + path + ("?" + urllib.parse.urlencode(query, doseq=True) if query else "")
    headers = {"Content-Type": "application/json"}
    if env("COMPOSIO_API_KEY"):  # no servidor sem chave no disco, um proxy pode injetar a autenticação
        headers["x-api-key"] = env("COMPOSIO_API_KEY")
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read() or "{}")
    except urllib.error.HTTPError as e:
        sys.exit(f"Composio HTTP {e.code} {method} {path}: {e.read().decode()[:600]}")


def execute(slug, arguments=None):
    return call("POST", f"/v3.1/tools/execute/{slug}", {"user_id": USER, "arguments": arguments or {}})


def ok(r):
    return (r.get("data") or {}) if r.get("successful") else {}


def me():
    u = ok(execute("INSTAGRAM_GET_USER_INFO"))
    if not u.get("id"):
        sys.exit("Instagram não conectado no Composio. Rode: python3 scripts/composio_ig.py conectar")
    return u


def auth_config(toolkit="instagram"):
    items = call("GET", "/v3/auth_configs", query={"toolkit_slug": toolkit}).get("items", [])
    if items:
        return items[0]["id"]
    made = call("POST", "/v3/auth_configs", {"toolkit": {"slug": toolkit}, "auth_config": {"type": "use_composio_managed_auth"}})
    return made.get("auth_config", made).get("id")


def main(argv):
    if not argv:
        sys.exit(__doc__)
    cmd, rest = argv[0], argv[1:]
    if cmd == "conectar":
        out = call("POST", "/v3.1/connected_accounts/link", {"auth_config_id": auth_config(), "user_id": USER})
        print("Abra este link no navegador e autorize a sua conta profissional do Instagram:\n" + str(out.get("redirect_url")))
    elif cmd == "contas":
        items = call("GET", "/v3/connected_accounts", query={"user_ids": USER}).get("items", [])
        print(json.dumps([{"id": a.get("id"), "toolkit": (a.get("toolkit") or {}).get("slug"), "status": a.get("status")} for a in items], indent=1))
    elif cmd == "eu":
        u = me()
        print(json.dumps({"username": u.get("username"), "id": u.get("id"), "seguidores": u.get("followers_count")}, ensure_ascii=False))
    elif cmd == "ferramentas":
        for t in call("GET", "/v3/tools", query={"toolkit_slug": "instagram", "limit": 200}).get("items", []):
            print(t.get("slug"), "·", (t.get("description") or "")[:110].replace("\n", " "))
    elif cmd == "schema":
        t = call("GET", f"/v3/tools/{rest[0]}")
        print(json.dumps({"slug": t.get("slug"), "input": t.get("input_parameters")}, indent=1, ensure_ascii=False))
    elif cmd == "exec":
        print(json.dumps(execute(rest[0], json.loads(rest[1]) if len(rest) > 1 else {}), indent=1, ensure_ascii=False))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
