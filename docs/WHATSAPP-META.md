# WhatsApp pela Meta (Cloud API direto)

Grátis nas respostas (1.000 conversas de serviço por mês por número), mas exige um número só para o bot
(um chip pré-pago serve; o número **não** pode estar em uso no app do WhatsApp).

1. https://developers.facebook.com → **Meus apps → Criar app** → tipo **Empresa** → adicione o produto **WhatsApp**.
2. Em **WhatsApp → Configuração da API**, adicione o **seu número do bot** (verificação por SMS/ligação). O número de teste
   da Meta é dos EUA e pode não entregar mensagens no Brasil: use um número próprio.
3. Anote: **Phone number ID** → `WHATSAPP_PHONE_ID`; **WhatsApp Business Account ID** → `WHATSAPP_WABA_ID`;
   **App ID** e **App Secret** (Configurações do app → Básico) → `WHATSAPP_APP_ID`, `WHATSAPP_APP_SECRET`.
4. **Token permanente:** Configurações do negócio → Usuários do sistema → crie um usuário Admin → Gerar token com
   `whatsapp_business_messaging` e `whatsapp_business_management`, validade "nunca" → `WHATSAPP_TOKEN`.
5. No `.env`: `CANAL=whatsapp-meta`, `WHATSAPP_DONO=<seu celular com 55 + DDD, só números>`,
   `WHATSAPP_VERIFY_TOKEN=<uma palavra aleatória>`.
6. Webhook: no servidor (`PUBLIC_URL` definido), a ponte registra sozinha `https://seu-dominio/webhook` ao subir.
   No computador, ela usa um túnel grátis da Cloudflare (`brew install cloudflared`) e reaponta a cada início.
7. Mande "oi" do seu celular para o número do bot. A janela de 24 h começa aí: o bot só responde dentro dela
   (fora dela a Meta cobra por template; a ponte não manda nada).
Cota: a ponte conta cada envio e para em `WHATSAPP_COTA` (padrão 900/mês) para nunca passar do grátis.
Não cadastre forma de pagamento na Meta se quiser garantia de custo zero.
