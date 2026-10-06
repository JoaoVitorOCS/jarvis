#!/usr/bin/env bash
# Instala o Jarvis num servidor Ubuntu 24.04 (versão paga). Rode como um usuário comum com sudo, DENTRO da pasta do Jarvis:
#   bash deploy/servidor/instalar.sh jarvis.seudominio.com
set -euo pipefail
DOMINIO="${1:?uso: bash deploy/servidor/instalar.sh <dominio>}"
PASTA="$(cd "$(dirname "$0")/../.." && pwd)"

echo "== pacotes"
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-venv ffmpeg git curl debian-keyring debian-archive-keyring apt-transport-https chromium-browser || \
  sudo apt-get install -y python3 python3-pip python3-venv ffmpeg git curl chromium
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
pip3 install --break-system-packages requests
# áudio por voz (opcional, ~1 GB de RAM): pip3 install --break-system-packages openai-whisper

echo "== Claude Code"
sudo npm install -g @anthropic-ai/claude-code
command -v vercel >/dev/null || sudo npm install -g vercel

echo "== Caddy (HTTPS)"
if ! command -v caddy >/dev/null; then
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
  sudo apt-get update -y && sudo apt-get install -y caddy
fi
sed "s#jarvis.seudominio.com#$DOMINIO#; s#PASTA_DO_JARVIS#$PASTA#g" "$PASTA/deploy/servidor/Caddyfile" | sudo tee /etc/caddy/Caddyfile >/dev/null
mkdir -p "$PASTA/dados/publico"
chmod o+x "$HOME" "$PASTA" "$PASTA/dados" && chmod o+rx "$PASTA/dados/publico"   # o Caddy precisa ler a mídia pública
sudo systemctl reload caddy || sudo systemctl restart caddy

echo "== serviço do Jarvis"
sed "s#USUARIO#$USER#; s#PASTA_DO_JARVIS#$PASTA#g" "$PASTA/deploy/servidor/jarvis.service" | sudo tee /etc/systemd/system/jarvis.service >/dev/null
grep -q '^PUBLIC_URL=' "$PASTA/.env" && sed -i "s#^PUBLIC_URL=.*#PUBLIC_URL=https://$DOMINIO#" "$PASTA/.env" || echo "PUBLIC_URL=https://$DOMINIO" >> "$PASTA/.env"
grep -q '^HOSPEDAGEM=' "$PASTA/.env" && sed -i "s#^HOSPEDAGEM=.*#HOSPEDAGEM=servidor#" "$PASTA/.env" || echo "HOSPEDAGEM=servidor" >> "$PASTA/.env"
sudo systemctl daemon-reload
sudo systemctl enable --now jarvis

echo
echo "Pronto. Confira:"
echo "  sudo systemctl status jarvis      (deve estar active/running)"
echo "  journalctl -u jarvis -f           (log ao vivo)"
echo "  curl -I https://$DOMINIO/publico/  (HTTPS respondendo)"
echo "Falta: CLAUDE_CODE_OAUTH_TOKEN (ou ANTHROPIC_API_KEY) no .env e o webhook do WhatsApp apontando para https://$DOMINIO/webhook"
