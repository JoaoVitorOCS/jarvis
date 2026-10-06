# Telegram (versão grátis)

1. No Telegram, abra **@BotFather** → `/newbot` → escolha um nome e um usuário terminado em `bot`.
2. Copie o **token** que ele devolve e cole no `.env`: `TELEGRAM_BOT_TOKEN=...` e `CANAL=telegram`.
3. No terminal, dentro da pasta do Jarvis: `python3 scripts/jarvis_bridge.py --definir-senha` (mínimo 8 caracteres;
   só o hash fica salvo).
4. Suba a ponte: `python3 scripts/jarvis_bridge.py`. No celular, mande "oi" para o seu bot: ele responde com o seu
   **chat id**. Cole no `.env` (`TELEGRAM_CHAT_ID=...`), pare a ponte (Ctrl+C) e suba de novo.
5. Mande a senha: o bot apaga a mensagem e desbloqueia. Teste `/status` e "o que você consegue fazer?".

Só o seu chat é atendido; qualquer outra pessoa que achar o bot é ignorada. O bot bloqueia sozinho depois de
6 h sem uso (mude com `JARVIS_LOCK_HOURS`). Áudio: instale o whisper (`pip3 install openai-whisper`).
Para deixar rodando sempre: `GRATIS-MAC.md`.
