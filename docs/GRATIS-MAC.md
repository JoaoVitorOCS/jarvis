# Versão grátis: deixar o Jarvis rodando no Mac

1. A pasta do Jarvis **não pode** estar em Mesa, Documentos ou Downloads (o macOS bloqueia serviços em segundo plano ali).
   Use, por exemplo, `~/jarvis`.
2. Edite `deploy/mac/jarvis.plist` trocando `PASTA_DO_JARVIS` pelo caminho absoluto (ex.: `/Users/voce/jarvis`).
3. `cp deploy/mac/jarvis.plist ~/Library/LaunchAgents/dev.jarvis.ponte.plist`
4. `launchctl load ~/Library/LaunchAgents/dev.jarvis.ponte.plist`
5. Confira o log: `tail -f dados/ponte.log` → deve aparecer "Jarvis ativo no canal telegram".

Limites da versão grátis: com o Mac dormindo ou desligado, o Jarvis não responde e as publicações agendadas saem
quando ele voltar (a agenda roda os itens atrasados e avisa). Em Ajustes → Bateria, evite o repouso automático
nos horários de post, ou migre para a versão paga.

Linux ou Windows (WSL): use `deploy/servidor/jarvis.service` (systemd) no próprio computador.
