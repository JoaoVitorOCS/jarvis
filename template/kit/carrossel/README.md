# Carrossel em código

O roteiro vira um JSON, o JSON vira HTML com as cores e fontes de `marca/marca.json`, e um Chrome headless tira um PNG
de 1080×1350 de cada slide. Custo zero e o estilo fica igual em todo post.

```bash
python3 scripts/carrossel.py projetos/<slug>/carrossel.json   # renders/slide-NN.png + renders/folha.jpg + aviso de estouro
python3 scripts/publicar.py preparar projetos/<slug>           # depois: ensaio → publicar/agendar (com aprovação)
```

## carrossel.json
```json
{"tema": "claro", "legenda_arquivo": "legenda.txt", "tags": {"formato": "lista", "gancho": "numero"},
 "slides": [{"layout": "capa", "kicker": "…", "title": "…", "sub": "…"}]}
```
- `tema`: `claro` ou `escuro` (os dois definidos em `marca/marca.json`).
- Marcação nos textos: `**negrito**`, `==marca-texto==` (bloco da cor de acento atrás) e `*destaque*` (palavra-chave na fonte de destaque).
- Todo slide aceita `kicker` (rótulo em caixa alta acima do título) e `note` (linha menor no fim).
- `size` muda o título: `md` diminui; `lg` e `xl` aumentam (caixa alta).
- O avatar do cabeçalho vem de `marca.avatar`; o fecho usa `marca.logo` (ou o nome, se não houver logo).

## Layouts
| Layout | Para quê | Campos |
|---|---|---|
| `capa` | slide 1: promessa e "deslize →" | `kicker`, `title`, `sub`, `swipe`, `card` |
| `antes-depois` | prova lado a lado (bom para o slide 2) | `title`, `antes`/`depois` `{label, big, text, image}`, `note` |
| `prova` | números em cards | `title`, `text`, `metrics: [{value, label, acc}]`, `note` |
| `texto` | um ponto com bullets e card | `title`, `text`, `bullets: []`, `card`, `note` |
| `lista` | passos ou itens numerados | `title`, `sub`, `items: [{t, d}]`, `note` |
| `terminal` | um agente fazendo algo | `title`, `card: {type: terminal, title, lines: [">", "#", "✓"]}` |
| `prompt` | prompt copiável | `title`, `card: {type: prompt, tag, text}` |
| `tweet` | texto puro, cara de post | `text`, `card` |
| `cta` | fecho | `title`, `text`, `bullets`, `action` (pílula) |

Cards (`card`): `terminal`, `prompt`, `metrics`, `image` (`src` relativo à pasta do projeto) e `quote`.

## Regras que funcionam
- 6 a 10 slides; o slide 2 precisa funcionar sozinho (o Instagram reexibe o carrossel a partir dele).
- Um objetivo por carrossel (salvar ou mandar para alguém); o último slide pede exatamente isso.
- Prova em todo slide do meio: print, número ou exemplo real.
