---
name: jarvis-criar
description: Criação de conteúdo do Jarvis na marca da pessoa — roteiro aprovado primeiro, depois reel editorial em motion (texto + efeitos + música, renderizado com Hyperframes) ou carrossel em código (HTML → PNG 1080×1350), com QA visual antes de entregar. Use quando pedirem "cria o reel", "faz um carrossel", "monta o post", "escreve o roteiro".
---

# Criar um post

Leia `CLAUDE.md`, `marca/marca.json`, `marca/voz.md` e `cadernos/instagram.md`. Crie a pasta `projetos/<AAAA-MM-DD>-<slug>/`.

## 1. Roteiro ✋ (sempre antes de qualquer render)
- Gancho legível no **primeiro quadro**, verdadeiro e sem contexto prévio; uma ideia por tela; números reais com fonte.
- Prova logo depois do gancho (print, número, resultado). O que deu errado também entra.
- Fecho com **um** CTA alinhado ao objetivo do post (seguir, salvar, mandar para alguém, comentar uma palavra).
- Passe o texto pelo `/no-ai-slop` (se instalado) e corte: "não é X, é Y", "o segredo que ninguém conta", travessão
  decorativo, adjetivo vazio. Siga `marca/voz.md`.
- Mostre o roteiro tela a tela + a legenda (gancho nos 125 primeiros caracteres, 3–5 hashtags específicas) e **pare até a aprovação**.

## 2a. Reel editorial (kit/motion)
1. Escreva `reel.json` (formato no topo de `kit/motion/montar_reel.py`): `gancho`, `subgancho`, 2 a 6 `cards`, `fecho`,
   `botao`, `musica` (arquivo seu em `kit/musica/`; instrumental, sem voz cantada) e `tags` (a variável que o post testa).
2. `python3 kit/motion/montar_reel.py projetos/<slug>` → `cd projetos/<slug>/reel && npx --yes hyperframes check`.
3. **QA antes do render:** `npx --yes hyperframes snapshot . --at <5 a 8 tempos>` e olhe a folha: texto cortado,
   sobreposição, contraste, gancho no frame 0. Corrija e repita.
4. `npx --yes hyperframes render . -o ../renders/reel.mp4` → `python3 kit/motion/montar_reel.py projetos/<slug> --mixar`
   (música −6 dB sob os efeitos; master em `lufs`, padrão −16). Mostre o `renders/master.mp4`.
5. Quer outra estrutura (antes/depois, diagrama, depoimento)? Use o plugin Hyperframes para compor uma cena nova,
   reaproveitando `kit/motion/ed.js` (texto que sobe, marca-texto, cards, pinceladas) e os tokens da marca. Varie a fórmula
   de um reel para o outro: mesma estética, estrutura diferente.

## 2b. Carrossel (kit/carrossel)
1. Escreva `carrossel.json` (layouts em `kit/carrossel/README.md`): 6 a 10 slides; o slide 2 precisa funcionar como capa
   (o Instagram reexibe o carrossel a partir dele); último slide = CTA.
2. `python3 scripts/carrossel.py projetos/<slug>/carrossel.json` → leia `renders/folha.jpg` e o campo `estouros`.
3. Corrija estouros (corte texto ou use `"size": "md"`) e mostre a folha.

## 3. Entrega
Mostre o arquivo final, a legenda e o `publicacao.json` (criado automaticamente). Com a aprovação, siga para o `/jarvis-publicar`.
