# WhatsApp pela Twilio

Mais rápido de montar (número na hora), mas cobra por mensagem (Twilio + tarifa da Meta).

1. Conta em https://twilio.com → console → anote **Account SID** e **Auth Token** → `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`.
2. Para testar: **Messaging → Try it out → Send a WhatsApp message** (sandbox): mande o código `join ...` do seu
   celular para o número da sandbox. Para produção: **Messaging → Senders → WhatsApp senders** (registro do seu número).
3. `TWILIO_WHATSAPP_FROM=whatsapp:+<número da Twilio>`, `WHATSAPP_DONO=<seu celular, só números>`, `CANAL=whatsapp-twilio`.
4. Webhook de entrada: no sender (ou na sandbox), em **When a message comes in**: `https://seu-dominio/webhook` (POST).
   Precisa de URL fixa: use no servidor (`PUBLIC_URL`). O túnel grátis muda de endereço a cada início.
5. `sudo systemctl restart jarvis` → mande "oi" → senha → `/status`.
A ponte confere a assinatura `X-Twilio-Signature` de cada mensagem; o `PUBLIC_URL` precisa ser exatamente a URL configurada.
