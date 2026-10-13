---
name: jarvis-publicar
description: Publicação do Jarvis no Instagram (Composio) e no YouTube Shorts (API do YouTube): prepara e hospeda a mídia, faz um ensaio sem publicar, publica ou agenda o reel/carrossel/foto, manda o mesmo conteúdo para o story e sobe o reel como Short, sempre com aprovação explícita. Use quando pedirem "publica", "posta", "agenda para amanhã às 12h", "sobe o reel", "manda pro YouTube", "sobe como Short".
---

# Publicar ou agendar

**Nunca publique sem um "aprovo" (ou equivalente explícito) da pessoa para o conteúdo exato**: arquivo, capa, legenda,
título e descrição do Short e horário.

1. Confira `projetos/<slug>/publicacao.json` (tipo, mídia, legenda, `story: true`, `tags`) e a legenda final.
   **Short (só reel, se o YouTube estiver conectado: `python3 scripts/youtube.py eu`):** inclua o bloco `youtube`
   (`titulo` até 100 caracteres, escrito para busca; `descricao_arquivo`; `tags`; `midia` só se houver um render
   próprio para o YouTube, ex. com fecho "inscreva-se"). Título e descrição são texto novo, não a legenda do Instagram.
   Só Short, sem Instagram: `"instagram": false`. Detalhes em `docs/YOUTUBE.md` do plugin.
2. `python3 scripts/publicar.py preparar projetos/<slug>` → converte para o padrão da API e hospeda (URLs em `.hospedado.json`).
   Só Short não precisa: o YouTube recebe o arquivo direto.
3. `python3 scripts/publicar.py ensaio projetos/<slug>` → cria o post do Instagram SEM publicar e confere o Short
   (vertical, até 3 min, título, canal). Se falhar, corrija antes de seguir.
4. Mostre o resumo (arquivo, capa, legenda inteira, título e descrição do Short, horário) e peça a aprovação.
5. Com o ok:
   - agora: `python3 scripts/publicar.py publicar projetos/<slug> --confirmo` (as duas redes; `--so instagram|youtube` para uma só)
   - agendado: `python3 scripts/publicar.py agendar projetos/<slug> 2026-10-07T12:07:00-03:00` (a ponte precisa estar
     rodando nesse horário; na versão grátis o computador precisa estar ligado e acordado).
   Cada rede sai uma única vez (`.publicado.json` e `.publicado-youtube.json`); uma falhar não impede a outra, e repetir
   o comando só tenta a que faltou. No Instagram, em seguida vai o story com a mesma mídia.
6. Depois de publicado: `python3 scripts/publicar.py limpar projetos/<slug>` (apaga a mídia pública) e lembre a pessoa
   de ficar online na 1ª hora para responder comentários. Respostas a comentários também só com texto aprovado.
   Short: em alguns minutos, `python3 scripts/youtube.py status <id>` confere se caiu na aba Shorts e se ficou público.
7. Marque no plano da semana o que saiu e quando; daqui a 24 h e a 7 dias o `/jarvis-insights` lê o resultado.

Problemas comuns: "processamento falhou" = vídeo fora do padrão (rode `preparar` de novo); URL inacessível = hospedagem
expirou ou é privada; legenda com mais de 2.200 caracteres é recusada. **YouTube:** Short "privado" mesmo pedindo público =
projeto do Google Cloud ainda sem auditoria da API (ver `docs/YOUTUBE.md`, passo 3); `invalid_grant` = login vencido ou
app no modo "Teste" (publique o app e rode `youtube.py login`); `quotaExceeded` = cota do dia acabou (volta à meia-noite do Pacífico);
foi para a aba Vídeos = vídeo com mais de 3 min ou horizontal.
