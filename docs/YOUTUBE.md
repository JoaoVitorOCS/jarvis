# YouTube Shorts

O Jarvis sobe o mesmo reel como Short no seu canal, com título e descrição próprios, pela **API do YouTube num
projeto seu no Google Cloud** (grátis, sem cartão). Short não tem endpoint próprio: é o upload normal de um vídeo
**vertical de até 3 min**, e o próprio YouTube decide se ele vai para a aba Shorts.

> Por que não pelo Composio? A conexão gerenciada divide a cota da API entre todos os usuários e costuma chegar
> esgotada (`quotaExceeded`). No seu projeto a cota (10.000 unidades/dia, ~6 uploads) é só sua.

## 1. Projeto e API (uma vez)
1. https://console.cloud.google.com → **Novo projeto** (ex.: `jarvis-youtube`). Não precisa ativar faturamento.
2. **APIs e serviços → Biblioteca** → "YouTube Data API v3" → **Ativar**.
3. **APIs e serviços → Tela de consentimento OAuth** (ou "Google Auth Platform"): tipo **Externo**, nome do app,
   seu e-mail de suporte e de contato. Em **Público-alvo**, clique em **Publicar app** para ficar **"Em produção"**.
   No modo "Teste" o Google derruba o login a cada 7 dias. Não precisa pedir verificação: no login vai aparecer
   "o Google não verificou este app"; clique em **Avançado → Acessar** (o app é seu).
4. **Credenciais → Criar credenciais → ID do cliente OAuth → App para computador**. Copie o ID e a chave secreta para o `.env`:
   ```
   YOUTUBE_CLIENT_ID=...
   YOUTUBE_CLIENT_SECRET=...
   ```

## 2. Login e conferência
```
python3 scripts/youtube.py login     # abre o navegador: escolha a conta E o canal certo (contas de marca aparecem à parte)
python3 scripts/youtube.py eu        # precisa mostrar o nome do seu canal
```
O token fica em `dados/.youtube-token.json` (fora do git) e se renova sozinho. Num servidor sem navegador, faça o
login no seu computador e copie o `refresh_token` desse arquivo para `YOUTUBE_REFRESH_TOKEN=` no `.env` do servidor.

## 3. Auditoria (para os Shorts ficarem públicos)
Projeto novo, ainda não auditado, tem **todo upload travado como privado** (o vídeo sobe e só você vê). Para liberar,
preencha o formulário de auditoria da API: https://support.google.com/youtube/contact/yt_api_form. Diga que é um app
de uso próprio que publica os vídeos do seu canal. Até a aprovação, publique os privados à mão no Studio (Visibilidade → Público).

## 4. No post
No `projetos/<slug>/publicacao.json` do reel:
```json
"youtube": {"titulo": "Até 100 caracteres, com a palavra que as pessoas buscam",
            "descricao_arquivo": "descricao-youtube.txt",
            "tags": ["tema", "nicho"],
            "midia": "renders/master-yt.mp4"}
```
- `midia` é opcional: use quando o Short tiver um render próprio (ex.: fecho com "inscreva-se" no lugar de "siga").
  Sem ela, sobe o mesmo vídeo do Instagram.
- `"instagram": false` publica só o Short.
- `publicar` e `agendar` mandam para as duas redes; `--so youtube` só para o YouTube. Cada rede sai **uma vez só**
  (`.publicado-youtube.json` + busca do título no canal), então repetir o comando não duplica.

Opcionais no `.env`: `YOUTUBE_IDIOMA` (padrão `pt-BR`), `YOUTUBE_CATEGORIA` (padrão `22`, Pessoas e blogs; `28` =
Ciência e tecnologia, `27` = Educação, `26` = Como fazer e estilo) e `YOUTUBE_PRIVACIDADE` (padrão `public`).

## Bom saber
- Até 3 min e vertical: o `ensaio` confere antes. Se mesmo assim o vídeo for para a aba Vídeos, `youtube.py status <id>` avisa.
- **Capa:** o Jarvis envia a capa do reel, mas o YouTube só usa capa personalizada em Short de canal do Programa de
  Parcerias. Até lá fica a automática (mandar não faz mal; passa a valer sozinho quando o canal entrar).
- **Música:** trilha comercial mixada no vídeo pode receber reivindicação do Content ID (anúncios do vídeo vão para
  o dono da música) ou até bloqueio. Para monetizar, prefira trilha própria ou com licença comercial.
- Título e descrição do Short são texto à parte: escreva para busca (o YouTube vive de busca e sugestão), não copie a legenda do Instagram.
