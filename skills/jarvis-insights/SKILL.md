---
name: jarvis-insights
description: Motor de aprendizado do Jarvis — lê as métricas de cada post (alcance, skip rate, retenção, envios, salvamentos, seguidores), compara por variável testada e atualiza o caderno de regras de cada rede social, que passa a guiar os próximos posts. Use quando pedirem "como foram os posts", "métricas", "relatório da semana", "o que funcionou", ou toda semana.
---

# Insights e aprendizado

O Jarvis aprende assim: **cada post testa uma variável** (anotada em `tags`), as métricas voltam como dado e as
conclusões viram regras no caderno da rede (`cadernos/<rede>.md`). O `/jarvis-plano` e o `/jarvis-criar` leem o caderno
antes de tudo. Cada rede tem o seu caderno porque o comportamento muda de uma para outra.

## 1. Dados
`python3 scripts/metricas.py snapshot` e depois `python3 scripts/metricas.py resumo --json`.

## 2. Leitura (honesta)
- Compare **por etiqueta** (`por_etiqueta`) e só tire conclusão com pelo menos 3 posts de cada lado; antes disso é
  **hipótese**. Escreva a força da evidência junto de cada achado.
- Métricas que mais pesam: alcance de quem não segue, **skip rate** (reel), retenção média, **envios por mil** e
  **salvos por mil**. Curtida pesa pouco.
- Procure o que mudou de um post para o outro além da variável testada (horário, tema): se mudou mais de uma coisa, diga.

## 3. Atualizar o caderno da rede
Em `cadernos/instagram.md`, para cada achado: a regra em uma linha, a evidência (posts, números), o status
(`hipótese` → `confirmada` com 3+ posts concordando → `descartada` se os dados virarem) e a data.
Ex.: `- [confirmada · 4 posts] gancho com número no frame 0: skip 41% vs 63% sem número (07/10–14/10)`.
Copie as 5 regras mais fortes para a seção "Regras que o Jarvis aprendeu" do `CLAUDE.md`.

## 4. Relatório para a pessoa
Curto: 3 linhas de resumo · o que funcionou · o que não funcionou · **próximos 3 testes** (uma variável cada).
Grave em `relatorios/<AAAA-MM-DD>.md`. Sem número inventado; amostra pequena = diga que é pequena.
