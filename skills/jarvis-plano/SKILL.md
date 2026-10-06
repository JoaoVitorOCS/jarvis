---
name: jarvis-plano
description: Planejamento da semana do Jarvis — transforma as pautas pesquisadas numa grade de posts (formato, pilar, gancho, objetivo, dia e horário), respeitando o caderno de regras que o Jarvis aprendeu com as métricas. Use quando pedirem "planeja a semana", "grade de posts", "calendário", "o que postar em cada dia".
---

# Plano da semana

Leia: `CLAUDE.md` (cadência, objetivo), `marca/`, a pesquisa mais recente em `pesquisas/` e **`cadernos/instagram.md`**
(as regras aprendidas valem mais que qualquer heurística genérica; se uma regra do caderno contradiz o que você faria, siga o caderno).
Se o plugin Instagram Skills estiver instalado, use o `ig-content-planner` como base e ajuste às regras daqui.

## Regras padrão (até o caderno ter dados que digam outra coisa)
- **Reel** para alcance (chega em quem não segue), **carrossel** para salvamento, **story** para relacionamento.
- Um objetivo por post (alcance, salvamento, envio, seguidor, comentário). Na semana, espalhe os objetivos.
- Nenhum pilar acima de 50% da semana; nenhuma fórmula de gancho mais de 2 vezes.
- **Cada post testa UMA variável** (gancho, formato, horário, duração). Registre nas `tags` do post: é assim que o
  `/jarvis-insights` consegue comparar e aprender.
- Horários: comece pelos padrões do nicho (almoço 11h–13h e noite 19h–21h em dias úteis) e deixe o caderno corrigir.
- Nada de rajada: posts do mesmo dia com pelo menos 4 h de distância.

## Entrega
Tabela | Dia | Hora | Formato | Pilar | Gancho (1 linha) | Objetivo | Variável testada | e grave em
`planos/<AAAA-MM-DD>-semana.md`. Pergunte o que ajustar; com o ok, siga post a post no `/jarvis-criar`.
