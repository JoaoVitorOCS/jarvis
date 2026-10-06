# Tendências do Instagram (opcional, API da Meta)

Permite ao `/jarvis-pesquisa` ler os posts com mais engajamento por hashtag (30 hashtags diferentes por semana) e,
com a permissão de insights, os posts recentes de perfis do nicho. Grátis.

1. A conta do Instagram precisa ser profissional **e ligada a uma Página do Facebook** (no app: Editar perfil → Página).
2. Crie um app em https://developers.facebook.com (tipo Empresa) e abra o **Graph API Explorer**.
3. Gere um **token de usuário** com: `instagram_basic`, `pages_show_list`, `pages_read_engagement`, `business_management`
   e, para ler perfis, `instagram_manage_insights`. Troque por um token de longa duração (60 dias) em
   **Ferramentas → Depurador de token de acesso → Estender**.
4. Descubra o id: no Explorer, `me/accounts?fields=instagram_business_account` → o número dentro de
   `instagram_business_account` vai em `META_IG_ID`. O token vai em `META_TOKEN`.
5. Teste: `python3 scripts/tendencias.py tags <uma hashtag do seu nicho> --days 30`.
Renove o token a cada ~60 dias.
