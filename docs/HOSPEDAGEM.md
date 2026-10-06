# Hospedagem da mídia

A API do Instagram não recebe arquivo: ela baixa o vídeo/imagem de um **link público**. O `publicar.py preparar`
sobe a mídia e o `limpar` apaga depois de publicado.

## Vercel Blob (versão grátis)
1. Conta grátis em https://vercel.com → **Storage → Create → Blob** → dê um nome → crie.
2. Na aba do Blob, em **.env.local** (ou Settings → tokens), copie o `BLOB_READ_WRITE_TOKEN` → cole no `.env`.
3. Instale o CLI: `npm i -g vercel`. No `.env`: `HOSPEDAGEM=vercel`.
4. Teste: `python3 scripts/publicar.py preparar projetos/exemplo-carrossel` deve devolver URLs `...blob.vercel-storage.com/...`.
O plano Hobby tem cota mensal de armazenamento e tráfego que sobra para posts (a mídia fica lá só até publicar).

## Próprio servidor (versão paga)
`HOSPEDAGEM=servidor` e `PUBLIC_URL=https://seu-dominio`. O `instalar.sh` já configura o Caddy para servir
`dados/publico/` em `https://seu-dominio/publico/...`.
