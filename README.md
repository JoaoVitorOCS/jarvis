# Jarvis · agente de conteúdo pessoal para Claude Code

Um agente que trabalha no seu Instagram com você: **pesquisa** o que está em alta no seu nicho, **planeja** a semana,
**cria** reels e carrosséis na sua marca (em código, sem editor), **publica** só com a sua aprovação e **aprende** com
as métricas de cada post, guardando o que funciona num caderno de regras por rede.

Você fala com ele pelo celular, por texto ou áudio.

```
Pesquisa ─▶ Estratégia ─▶ Criação ─▶ Aprovação ─▶ Publicação ─▶ Insights ─▶ Aprendizado ─┐
   ▲                                                                                       │
   └─────────────────────── o próximo post já sai ajustado ◀───────────────────────────────┘
```

## Duas versões
| | Grátis | Paga |
|---|---|---|
| Roda | no seu computador | num servidor na nuvem, 24 h |
| Você fala pelo | Telegram | WhatsApp (Meta direto ou Twilio) |
| Custo | R$ 0 além da assinatura do Claude | ~US$ 5–7/mês de servidor + WhatsApp |

## Instalar
Precisa do [Claude Code](https://claude.com/claude-code) e de uma assinatura do Claude. No Claude Code:
```
/plugin marketplace add JoaoVitorOCS/jarvis
/plugin install jarvis@jarvis
```
Depois, numa conversa nova: **`/jarvis-setup`**. O onboarding pergunta sobre você e a sua marca, monta a sua pasta
do Jarvis e guia cada conexão (Instagram, hospedagem, Telegram ou WhatsApp, servidor), conferindo cada passo.

## O que vem no pacote
| Skill | Faz |
|---|---|
| `/jarvis-setup` | onboarding: entrevista de marca, pasta do Jarvis, contas, canal, serviço, primeiro teste |
| `/jarvis-pesquisa` | o que está em alta no nicho (Instagram, last30days, web) → pautas com prova |
| `/jarvis-plano` | grade da semana, uma variável testada por post |
| `/jarvis-criar` | roteiro aprovado → reel editorial (Hyperframes) ou carrossel (HTML → PNG) na sua marca |
| `/jarvis-publicar` | prepara, ensaia, publica ou agenda + story automático |
| `/jarvis-insights` | métricas → caderno de regras por rede → próximos testes |

`template/` vira a sua pasta: ponte do celular (`jarvis_bridge.py`), scripts de publicação e métricas, kits de reel e
carrossel que leem as suas cores e fontes, e os serviços do Mac e do servidor. `docs/` tem o passo a passo de cada serviço.

## Princípios
- Nada sai sem a sua aprovação do conteúdo exato.
- Números só reais. O que deu errado também entra.
- Suas chaves ficam no `.env` da sua pasta (fora do git). Sua marca, seus dados e suas regras são só seus.

Licença MIT.
