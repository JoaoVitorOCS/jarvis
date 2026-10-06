# Instagram pelo Composio (grátis)

O Composio guarda a autorização do seu Instagram e expõe as ferramentas de publicação e métricas por API.
O plano gratuito sobra para uso pessoal.

1. A conta do Instagram precisa ser **profissional**: no app, Configurações → Tipo de conta e ferramentas → Criador
   (ou Empresa). Não precisa de página do Facebook.
2. Crie a conta em https://composio.dev → no painel, **Settings → API Keys** → crie uma chave → no `.env`:
   `COMPOSIO_API_KEY=...`
3. Na pasta do Jarvis: `python3 scripts/composio_ig.py conectar` → abra o link, entre no Instagram e autorize.
4. Confira: `python3 scripts/composio_ig.py eu` deve mostrar o seu @.

Problemas: "Instagram não conectado" = refaça o passo 3; erro 401 = chave errada no `.env`.
A conta conectada fica no usuário `COMPOSIO_USER_ID` (padrão `jarvis`): se mudar, conecte de novo.
