---
name: jarvis-setup
description: Onboarding do Jarvis — monta, do zero, um agente de conteúdo pessoal que pesquisa o que está em alta, planeja, cria (reels e carrosséis em código), publica no Instagram e aprende com as métricas de cada post. Duas versões — grátis (no seu computador, comandado pelo Telegram) ou paga (num servidor na nuvem, comandado pelo WhatsApp). Use quando a pessoa pedir para instalar, configurar ou começar o Jarvis, "montar meu agente", "onboarding", ou quando não existir uma pasta do Jarvis configurada.
---

# Onboarding do Jarvis

Você vai montar o Jarvis **da pessoa que está conversando com você**: com a marca, o nicho e as contas DELA.
Nada aqui pertence a outra pessoa; os exemplos do pacote são neutros e devem ser substituídos.

**Como conduzir:** um passo por vez, em português do Brasil, linguagem simples (a pessoa pode não ser técnica).
Use AskUserQuestion para decisões. Quando um passo depende de algo que só a pessoa pode fazer (criar conta, clicar
num link, pegar um token), explique em no máximo 5 passos numerados, espere ela voltar e **confira** antes de seguir.
Nunca peça senhas pessoais; chaves de API vão no arquivo `.env` da pasta do Jarvis (nunca no git, nunca no chat de
volta). Se a pessoa colar uma chave no chat, grave no `.env` e avise que ela pode revogar e gerar outra depois.

O pacote (este plugin) tem: `template/` (a pasta que vira o Jarvis da pessoa), `docs/` (passo a passo de cada serviço)
e as outras skills (`/jarvis-pesquisa`, `/jarvis-plano`, `/jarvis-criar`, `/jarvis-publicar`, `/jarvis-insights`).
O caminho do plugin é o diretório desta skill subindo dois níveis (`<base desta skill>/../..`); chame de PLUGIN.

## 0. Conferir o computador
Rode e interprete (não despeje a saída crua): `claude --version; python3 --version; ffmpeg -version | head -1; node --version; git --version`.
- Faltou algo: no Mac, `brew install python ffmpeg node git` (instale o Homebrew antes, se preciso: https://brew.sh).
  No Linux: `sudo apt install python3 python3-pip ffmpeg nodejs npm git`. No Windows: recomende o WSL (Ubuntu).
- `pip3 install requests` (a ponte usa). Áudio por voz é opcional: `pip3 install openai-whisper` (pesado; ~1 GB de RAM).

## 1. Escolher a versão (AskUserQuestion)
| | Grátis | Paga |
|---|---|---|
| Onde roda | no seu computador (precisa ficar ligado para responder e publicar no horário) | num servidor na nuvem, 24 h |
| Como você fala com ele | bot do **Telegram** (texto e áudio) | **WhatsApp** (texto e áudio) |
| Custo | R$ 0 além da sua assinatura do Claude | servidor (~US$ 5–7/mês) + WhatsApp: Meta (1.000 conversas grátis/mês, precisa de um número só para isso) ou Twilio (cobra por mensagem, número na hora) |
| Dá para migrar depois? | sim: a pasta é a mesma, muda só o canal e onde roda | — |

Recomende começar pela grátis se a pessoa ainda está testando. Registre a escolha em `dados/config.json` (`{"versao": "gratis"|"paga", "canal": ...}`).

## 2. Criar a pasta do Jarvis
Pergunte onde criar (padrão `~/jarvis`). Copie `PLUGIN/template/` para lá, rode `git init` e crie o `.env` a partir de
`.env.exemplo`. Confira que `.gitignore` cobre `.env`, `dados/.*`, `projetos/*/renders/` e `projetos/*/reel/sfx/`.
A partir daqui, **trabalhe sempre dentro dessa pasta** (ela é o "cérebro" do Jarvis: o `CLAUDE.md` dela é lido em toda conversa).

## 3. Entrevista de marca (o que deixa o Jarvis com a cara da pessoa)
Faça em 2 ou 3 rodadas de AskUserQuestion (até 4 perguntas por rodada), sempre com a opção "sugira para mim":
1. **Quem é você e o que faz** (uma frase), **@ do Instagram**, **nicho** e **para quem fala** (público).
2. **Objetivo agora** (crescer audiência · gerar clientes · vender um produto · autoridade) e **o que NÃO quer parecer**.
3. **3 a 4 pilares de conteúdo** (proponha com base no nicho; ex.: bastidores, ferramenta revelada, opinião, resultado).
4. **Tom de voz**: formal × próximo, gírias sim/não, palavrão sim/não, 1ª pessoa, exemplos de frases que a pessoa diria.
5. **Cores**: peça 2 cores (fundo e destaque) ou o site/logo de referência. Monte os temas `claro` e `escuro` com
   contraste AA (texto sobre o fundo ≥ 4,5:1; confira com uma conta, não no olho). Se a pessoa não souber, proponha
   2 paletas diferentes e mostre um carrossel de teste de cada uma (passo 9).
6. **Fontes**: 4 papéis do Google Fonts — `titulo`, `texto`, `mono`, `destaque` (itálica/serifada para a palavra-chave).
   Proponha combinações que combinem com o tom; nunca deixe as fontes padrão do pacote se a pessoa não aprovou.
7. **Cadência e horários**: quantos posts por semana, quais formatos (reel, carrossel), e se a pessoa consegue ficar online
   na 1ª hora depois de postar.

Grave:
- `marca/marca.json` (nome, arroba, frase, temas, fontes, avatar/logo se ela tiver o arquivo: peça para soltar em `marca/`);
- `marca/voz.md` (tom, use × evite, 5 frases de exemplo da própria pessoa);
- `CLAUDE.md` da pasta: preencha os campos `{{...}}` do template com as respostas (perfil, público, pilares, objetivo,
  cadência, regras de aprovação). Deixe a seção "Regras que o Jarvis aprendeu" vazia: ela cresce com o `/jarvis-insights`.
- `cadernos/instagram.md`: copie o modelo e preencha só o cabeçalho (conta, objetivo, data de início).

## 4. Instagram (Composio, grátis)
A conta precisa ser **profissional** (Criador ou Empresa; no app: Configurações → Tipo de conta). Siga `PLUGIN/docs/COMPOSIO.md`:
1. Criar conta em https://composio.dev (plano grátis) → copiar a **API key** → `COMPOSIO_API_KEY=` no `.env`.
2. `python3 scripts/composio_ig.py conectar` → a pessoa abre o link e autoriza o Instagram.
3. Conferir: `python3 scripts/composio_ig.py eu` precisa mostrar o @ certo. Não siga sem isso.

## 5. Hospedagem da mídia (a API do Instagram só aceita link público)
- **Grátis:** Vercel Blob (`PLUGIN/docs/HOSPEDAGEM.md`): conta na Vercel → Storage → Blob → criar → copiar o
  `BLOB_READ_WRITE_TOKEN` para o `.env` (`HOSPEDAGEM=vercel`) → `npm i -g vercel`.
- **Paga:** o próprio servidor serve `dados/publico/` (`HOSPEDAGEM=servidor`, configurado no passo 7).

## 6. Canal de conversa
- **Telegram (grátis):** `PLUGIN/docs/TELEGRAM.md`. Criar o bot no @BotFather → `TELEGRAM_BOT_TOKEN` no `.env` →
  `python3 scripts/jarvis_bridge.py --definir-senha` (a pessoa digita no terminal, nunca no chat) → subir a ponte uma vez,
  mandar "oi" para o bot: ele responde com o chat id → `TELEGRAM_CHAT_ID` no `.env` → reiniciar e testar com /status.
- **WhatsApp pela Meta (paga, mais barato):** `PLUGIN/docs/WHATSAPP-META.md` (app na Meta, número próprio, token permanente).
- **WhatsApp pela Twilio (paga, mais rápido de montar):** `PLUGIN/docs/WHATSAPP-TWILIO.md`.
Em `.env`: `CANAL=telegram|whatsapp-meta|whatsapp-twilio`, `WHATSAPP_DONO=<celular com DDI, só números>`.

## 7. Deixar rodando sozinho
- **Grátis (Mac):** `PLUGIN/docs/GRATIS-MAC.md` → instalar o serviço do macOS a partir de `deploy/mac/jarvis.plist`
  (troque o caminho da pasta) com `launchctl load`. Avise: Mac dormindo = Jarvis parado e posts agendados atrasam.
  Em Linux/Windows (WSL): use `deploy/servidor/jarvis.service` no próprio computador.
- **Paga (nuvem):** `PLUGIN/docs/PAGO-NUVEM.md` → criar a VPS (Ubuntu 24.04, 2 vCPU, 4 GB), apontar um domínio ou
  subdomínio (ou usar o túnel nomeado da Cloudflare), rodar `deploy/servidor/instalar.sh`, logar o Claude Code no servidor
  (`claude setup-token` no computador da pessoa → `CLAUDE_CODE_OAUTH_TOKEN` no `.env` do servidor; ou `ANTHROPIC_API_KEY`
  se ela preferir pagar por uso), copiar a pasta do Jarvis (git push para um repo PRIVADO ou `rsync`) e subir o serviço.
  `PUBLIC_URL=https://<domínio>` no `.env`.

## 8. Extras recomendados (todos grátis, como plugins do Claude Code)
Pergunte quais instalar (AskUserQuestion, multiSelect) e mostre os comandos `/plugin marketplace add` + `/plugin install`:
- **last30days** (`mvanhorn/last30days-skill`): o que o nicho está comentando nos últimos 30 dias (usado pela `/jarvis-pesquisa`);
- **no-ai-slop** (`petergyang/no-ai-slop`): tira a cara de IA dos textos (usado pela `/jarvis-criar`);
- **Hyperframes** (`heygen-com/hyperframes`): vídeo em HTML; o kit de reel do Jarvis renderiza com ele;
- **Instagram Skills** (`sergebulaev/instagram-skills`): planejamento, legendas e hashtags;
- Tendências direto do Instagram (opcional, API da Meta): `PLUGIN/docs/TENDENCIAS.md`.

## 9. Primeiro ciclo (prova de que funciona)
1. `python3 scripts/carrossel.py projetos/exemplo-carrossel/carrossel.json` → mostre `renders/folha.jpg` (Read): é a marca
   dela aplicada. Ajuste cores e fontes até ela gostar.
2. `python3 kit/motion/montar_reel.py projetos/exemplo-reel` → render com Hyperframes → mostre 3 quadros.
3. `python3 scripts/publicar.py preparar projetos/exemplo-carrossel` e depois `ensaio` (cria o post SEM publicar).
4. Pelo celular (Telegram/WhatsApp): mande "o que você consegue fazer?" e confira a resposta.
5. Apague os exemplos se ela quiser e sugira o próximo passo: `/jarvis-pesquisa` sobre o nicho dela.

## Checklist final (mostre marcado)
- [ ] `marca/marca.json`, `marca/voz.md` e `CLAUDE.md` preenchidos e aprovados
- [ ] `composio_ig.py eu` mostra o @ certo
- [ ] hospedagem testada (o `preparar` devolveu URLs)
- [ ] canal responde ao /status com a senha
- [ ] serviço sobe sozinho (reinicie o computador ou o servidor e confira)
- [ ] ensaio de publicação OK (nada foi publicado)

## Regras que valem sempre
- Publicar, responder comentário ou gastar crédito pago **só com aprovação explícita** do conteúdo exato.
- Números no conteúdo só reais e com fonte. Mostrar o que deu errado também (é o que dá credibilidade).
- `.env` nunca vai para o git nem aparece no chat. Repo da pasta do Jarvis no GitHub, se houver, sempre **privado**.
