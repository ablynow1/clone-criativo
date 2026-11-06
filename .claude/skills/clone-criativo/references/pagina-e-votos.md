# Página de aprovação, votos e aprendizado

## A página (`pub/`, montada pelo `pagina.py`)
Abas:
- **Lotes**: cada criativo com a referência que o originou (marca, nota, sinais, link da Biblioteca), por que deve
  vender, texto do anúncio (com botão copiar), ✓ Aprovar / ✕ Reprovar (tocar de novo desfaz), caixa de ajuste e
  "Baixar em alta".
- **Validados**: as marcas (validados, dias, alcance UE, motivo) e os criativos ranqueados com a leitura de design.
- **Padrões**: o que se repete, com encaixe no produto.
- **Sua oferta**: como eu li a LP + caixa "corrigir a leitura" (vira o id `oferta` nos votos).

## Abrir / publicar (sempre nesta ordem)
```bash
python3 $M/pagina.py
python3 $M/testa.py --local                 # testa no celular simulado (Chrome headless); votos de teste somem no fim
```
Depois, um dos dois:
- **Local (padrão, sem hospedagem)**: `python3 $M/servidor.py` em segundo plano → `http://localhost:8765/`.
  `--rede` deixa abrir no celular na mesma Wi-Fi. Votos ficam em `pub/dados/votos.jsonl`. O servidor precisa estar
  rodando enquanto o usuário vota; se ele fechou, subir de novo (os votos já gravados continuam lá).
- **Hospedagem com PHP** (se `config.json → url` existe, vindo do `SITE_BASE` do `.env`): `bash $M/publica.sh`
  (sobe `pub/` por FTP sem apagar nada e sem os `*.jsonl`) → `python3 $M/testa.py` (testa a página no ar).
- Olhe os prints `analise/teste_*.png` antes de mandar o link.
- `testa.py` aprova e desfaz o 1º criativo pra testar o voto (se o usuário já votou nele, não mexe).
- Algumas hospedagens (HostGator e parecidas): `curl` sem User-Agent leva 406 — `votos.py` já manda.
- Hospedagem só estática (GitHub Pages, Netlify, Vercel): a página abre, mas o voto não grava (não tem PHP). Nesse caso
  os votos vêm pelo chat: o usuário diz "aprovo l1c2, reprovo o resto, no l1c4 troca o fundo".

## Votos
`voto.php` (hospedagem) ou `servidor.py` (local) gravam em `pub/dados/votos.jsonl`.
`GET voto.php?estado=1` → `{"votos": {"<id>": [v, t, "ajuste"]}}` (v: 1 aprovado, -1 reprovado, 0 sem voto).
`python3 $M/votos.py` lê (da hospedagem se tem `url`, senão o arquivo local), grava `votos.json` e mostra por lote.
Se o usuário votar pelo chat, gravar o `votos.json` à mão no mesmo formato.

## Aprender com os votos → `gosto.md`
Depois de cada lote votado, reescrever `gosto.md` (curto, em bullets):
- **Aprova**: padrões/ângulos/estilos dos ✓ (com o id do criativo).
- **Reprova**: o que os ✕ têm em comum (mesmo parecendo certo).
- **Ajustes pedidos**: os comentários, literalmente, e como vou aplicar.
- **Correção da oferta** (id `oferta`): atualizar `oferta.json` e dizer o que mudou.

## Próximo lote
1. Pra cada ✓: 1–2 **variações** (mesma estrutura, outro gancho/título, outro fundo ou outra foto do produto, ou o
   formato 9:16 pro story). Variação de aprovado é o que mais rende em DR.
2. Ajuste pedido = refazer aquele criativo com o ajuste (conta como 1 do lote).
3. Completar até 5 com padrões ainda não testados, na ordem de `encaixe × peso`.
4. Nada que repita o motivo de um ✕.
5. `nota` do lote diz o que mudou ("variações do l1c2 e l1c4 + 1 padrão novo").
Se ele pedir "mais referências" ou outro mercado: nova busca → `marcas.json` maior → `paginas` → `ranking.py` →
leitura só das refs novas (as antigas já têm `analise/leitura/<id>.json`).
