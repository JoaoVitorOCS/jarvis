---
name: jarvis-publicar
description: Publicação do Jarvis no Instagram (Composio) — prepara e hospeda a mídia, faz um ensaio sem publicar, publica ou agenda o reel/carrossel/foto e manda o mesmo conteúdo para o story, sempre com aprovação explícita. Use quando pedirem "publica", "posta", "agenda para amanhã às 12h", "sobe o reel".
---

# Publicar ou agendar

**Nunca publique sem um "aprovo" (ou equivalente explícito) da pessoa para o conteúdo exato**: arquivo, capa, legenda e horário.

1. Confira `projetos/<slug>/publicacao.json` (tipo, mídia, legenda, `story: true`, `tags`) e a legenda final.
2. `python3 scripts/publicar.py preparar projetos/<slug>` → converte para o padrão da API e hospeda (URLs em `.hospedado.json`).
3. `python3 scripts/publicar.py ensaio projetos/<slug>` → cria o post SEM publicar. Se falhar, corrija antes de seguir.
4. Mostre o resumo (arquivo, capa, legenda inteira, horário) e peça a aprovação.
5. Com o ok:
   - agora: `python3 scripts/publicar.py publicar projetos/<slug> --confirmo`
   - agendado: `python3 scripts/publicar.py agendar projetos/<slug> 2026-10-07T12:07:00-03:00` (a ponte precisa estar
     rodando nesse horário; na versão grátis o computador precisa estar ligado e acordado).
   O script publica uma única vez (marca `.publicado.json`) e em seguida manda o story com a mesma mídia.
6. Depois de publicado: `python3 scripts/publicar.py limpar projetos/<slug>` (apaga a mídia pública) e lembre a pessoa
   de ficar online na 1ª hora para responder comentários. Respostas a comentários também só com texto aprovado.
7. Marque no plano da semana o que saiu e quando; daqui a 24 h e a 7 dias o `/jarvis-insights` lê o resultado.

Problemas comuns: "processamento falhou" = vídeo fora do padrão (rode `preparar` de novo); URL inacessível = hospedagem
expirou ou é privada; legenda com mais de 2.200 caracteres é recusada.
