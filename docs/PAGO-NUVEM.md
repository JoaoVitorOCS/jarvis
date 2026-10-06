# Versão paga: Jarvis 24 h num servidor, pelo WhatsApp

## Custos (referência)
| Item | Opção | Custo aproximado |
|---|---|---|
| Servidor | VPS Ubuntu 24.04, 2 vCPU, 4 GB (Hetzner, DigitalOcean, Contabo, Hostinger...) | US$ 5–7/mês |
| Domínio | um subdomínio de um domínio que você já tem, ou um novo | R$ 0–60/ano |
| Claude | sua assinatura (token de `claude setup-token`) ou API por uso | assinatura atual / por uso |
| WhatsApp | Meta direto: 1.000 conversas de serviço/mês grátis + um chip só para isso | R$ 0 + chip |
|  | Twilio: número na hora, paga por mensagem | centavos por mensagem |

## Passo a passo
1. **Servidor:** crie a VPS com Ubuntu 24.04 e sua chave SSH. Anote o IP.
2. **Domínio:** crie um registro **A** `jarvis.seudominio.com` → IP do servidor (espere propagar: `ping jarvis.seudominio.com`).
3. **Pasta do Jarvis no servidor:** suba a sua pasta (ela já tem marca, cadernos e scripts):
   `rsync -av --exclude dados/publico ~/jarvis/ usuario@IP:~/jarvis/` (ou um repo **privado** no GitHub e `git clone`).
   Copie o `.env` à parte (`scp ~/jarvis/.env usuario@IP:~/jarvis/.env`); ele não vai no git.
4. **Instalar:** `ssh usuario@IP`, `cd ~/jarvis && bash deploy/servidor/instalar.sh jarvis.seudominio.com`.
5. **Claude no servidor:** no seu computador, `claude setup-token` → copie o token → no `.env` do servidor
   `CLAUDE_CODE_OAUTH_TOKEN=...` (ou use `ANTHROPIC_API_KEY` para pagar por uso). Teste no servidor: `claude -p "oi"`.
6. **WhatsApp:** siga `WHATSAPP-META.md` ou `WHATSAPP-TWILIO.md`; webhook = `https://jarvis.seudominio.com/webhook`.
7. `sudo systemctl restart jarvis` → mande "oi" no WhatsApp → mande a senha → `/status`.

## Manutenção
- Log: `journalctl -u jarvis -f`. Atualizar scripts: `git pull` (ou rsync) e `sudo systemctl restart jarvis`.
- Backup: a pasta `~/jarvis` (sem `.env` no git). As regras aprendidas ficam em `cadernos/`: não perca.
- Segurança: só o seu número é atendido, as mensagens da Meta/Twilio têm assinatura conferida, e a senha protege o resto.
