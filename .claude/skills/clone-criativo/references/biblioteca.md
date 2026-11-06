# Biblioteca de Anúncios — coleta, sinais de validação e alcance real

## O que a Meta deixa ver (conferido em novembro/2026)
| sinal | de onde vem | vale pra |
|---|---|---|
| ordem por impressões | a listagem com `sort_data[mode]=total_impressions` vem ordenada pela Meta → posição 1 = mais impressão | todo anúncio (relativo à listagem) |
| dias no ar | `start_date` de anúncio ainda ativo; filtro `start_date[max]=hoje-14` = só quem passou de 14 dias | todo anúncio |
| variações | `collation_count`: quantos anúncios usam o mesmo criativo+texto (duplicado em conjuntos = escala) | todo anúncio |
| validados da marca | `search_results_connection.count` da listagem da marca com o filtro de 14 dias | marca |
| **alcance real** | detalhe do anúncio → `eu_total_reach` (pessoas alcançadas na UE) + idade/gênero | só anúncio veiculado na UE (`is_aaa_eligible`) |
| "<100" | `impressions_with_index.impressions_text` — anúncio que quase não rodou | sinal negativo |

Anúncio comercial que roda só no Brasil: **não tem** impressão nem alcance (`impressions_index = -1`; o detalhe não
traz `aaa_info`). Dizer isso ao usuário quando ele pedir "impressão".

## Nota de validação (ranking.py)
`posição na marca 35 + dias no ar 25 + variações 20 + alcance UE 20` (sem alcance, os 3 primeiros viram 100%)
× peso da marca 0,75–1,0 (nº de validados, 200+ = 1,0). Faixas: 70+ muito validado · 50–69 validado · <50 em teste.
A posição conta contra TODOS os anúncios da marca (vídeo inclusive): imagem em 3º numa marca de 300 anúncios é forte.

## Comandos (sempre na pasta do projeto)
```bash
python3 $M/biblioteca.py busca "a;b;c" --pais BR [--dias 14] [--exata]   # dumps/bu_br_<termo>_14d.html  (~1 min/termo)
python3 $M/biblioteca.py paginas marcas.json [--pais ALL] [--dias 14]    # dumps/pg_<marca>_<id>_14d.html (~1 min/marca)
                                                                          #   + alcance UE das 12 primeiras imagens de cada
python3 $M/biblioteca.py pageid "loja.com.br;brand.com"                  # pageids.json (~5 s/domínio)
python3 $M/biblioteca.py alcance --ads cands_ue.json [--max 150]         # alcance.json (~1,5 s/anúncio)
```
## Uma coleta por vez (trava)
- Cada comando pega a trava `/tmp/clone-criativo.lockdir` e roda ali mesmo. Se outra coleta estiver rodando, ele espera
  a vez (avisa "esperando a vez"). Nunca abrir dois coletores na Biblioteca ao mesmo tempo: a Meta bloqueia.
- Dá pra mandar `busca` BR, `busca` ALL e `pageid` em segundo plano ao mesmo tempo: eles entram um depois do outro.
- Rodar com `run_in_background` (coleta longa); mais de ~25 alvos: quebrar em dois comandos.
- Cache: dump que já existe não é recoletado. Pra forçar, apagar o arquivo.
- **Código 3 = bloqueio** (3 páginas seguidas vazias). Esperar ~40 min e rodar o mesmo comando. Se repetir: 2 h + perfil
  novo do Chrome (`rm -rf /tmp/clone-criativo-cdp`).
- Busca no país BR acha marca local; `ALL` acha as gringas grandes. Uma marca BR boa costuma ter 30–300 validados;
  gringa escalada, 200–2.000+.
- O jeito certo de esperar é o próprio comando em segundo plano: ele só termina quando a coleta acaba (vem 1 aviso no
  fim, com o resumo). Não fique consultando de minuto em minuto.

## Nicho que escala com vídeo (pouca imagem validada)
Infoproduto de creator/marketing: ~80% dos anúncios validados são vídeo (num teste real: 280 vídeos × 40 imagens nas
buscas; um dos maiores anunciantes tinha 222 validados e nenhuma imagem). Pra ter imagem suficiente:
- abrir uma 2ª leva de buscas no "produto digital barato do mesmo universo", que anuncia com imagem: "roteiros prontos",
  "ganchos prontos", "pack de…", "templates", "modelos de criativos";
- incluir SaaS/ferramenta pro mesmo público e marca gringa grande do tema — rodam na UE e
  trazem alcance real;
- deixar fora quem só tem vídeo (vale citar na resposta: "quem mais escala aqui é vídeo").

## Escolher as marcas (`marcas.json`)
Com `candidatos.json` + `analise/candidatos_*.jpg`:
- **Entra**: vende o mesmo tipo de produto, OU a mesma promessa pro mesmo público com preço/formato parecido; clique
  pra loja ≥ 50%; tem imagem validada (formato com "imagem").
- **Fica fora**: marketplace e varejão (Amazon, Shopee, Magalu, Mercado Livre — catálogo genérico), revenda/afiliado,
  anunciante só de vídeo (sem imagem nenhuma), outro nicho que caiu pela palavra, página de conteúdo/infoproduto (salvo
  se o cliente vende isso).
- Ordem de preferência: mesma categoria e escalada (muitos validados) > mesma promessa > mesma estética/público.
- Mistura boa: 5–8 BR + 5–8 gringas. Gringa traz padrão de design testado em escala e alcance real (UE).
- Escolha **12–18** pra coletar a página (algumas decepcionam) e corte pra **10–15** depois do `parse.py`.
- `marcas.json`: `[{"nome": "Bellroy", "page_id": "123", "site": "bellroy.com", "motivo": "mochila de couro premium, 420 validados"}]`
  O `motivo` aparece na página de aprovação — escrever curto e concreto.

## Alcance real (como funciona, se precisar mexer)
O `biblioteca.py alcance` abre a página de uma marca, clica em "Ver detalhes do anúncio" e captura o POST do GraphQL
(`AdLibraryV3AdDetailsQuery`, variáveis `adArchiveID` e `pageID`). Depois repete esse POST com `fetch` dentro da
página trocando os ids (0,2–0,6 s cada, pausa ~1,2 s). Se o Facebook mudar o nome do botão ou das variáveis, ajustar
`JS_CLICA`/`JS_REPETE`. Exemplos reais: de 87 mil a ~2 milhões de pessoas.
