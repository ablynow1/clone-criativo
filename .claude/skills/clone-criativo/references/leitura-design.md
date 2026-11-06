# Leitura de design (por referência) e padrões (síntese)

Objetivo: entender POR QUE cada imagem validada para o dedo e vende, num formato que vira brief. Descrever o que
está lá, sem inventar. Ler a prancha (`analise/pranchas/r###.jpg`); se o texto do anúncio estiver pequeno demais,
abrir `refs/<id>.jpg` direto. O `refs.json` tem headline/copy/CTA/link do anúncio — usar junto com a imagem.

## `analise/leitura/<id>.json`
```json
{
  "id": "1234567890",
  "tipo": "lista de benefícios",
  "formato": "4:5",
  "gancho_visual": "o que para o dedo, em 1 frase (ex.: a mochila gigante cortada pela borda, em diagonal)",
  "headline_imagem": "texto principal ESCRITO na imagem; se for gringo, em PT e o original entre colchetes",
  "textos_secundarios": ["selo 'frete grátis'", "3 bullets: …"],
  "hierarquia": ["1º produto", "2º título", "3º estrelas", "4º botão"],
  "produto": {"aparece": true, "tamanho": "60% da área", "posicao": "centro-baixo", "contexto": "flutuando em fundo bege"},
  "pessoa": {"aparece": false, "o_que": ""},
  "texto_na_imagem": "pouco | médio | muito",
  "paleta": ["#f3eadf", "#1a1a1a", "#c0392b"],
  "tipografia": "sans pesada caixa alta no título, fina no resto",
  "estilo": "estúdio limpo | foto de celular | design chapado | colagem | 3D | print de tela",
  "prova": ["4,9★ 2.300 avaliações"],
  "oferta_na_imagem": "preço/desconto/frete/garantia que aparecem (vazio se nada)",
  "angulo": "dor | desejo | prova social | oferta | curiosidade | autoridade | comparação | identidade | novidade",
  "por_que_funciona": "1–2 frases: o mecanismo de atenção + o de convencimento",
  "transplante": "como isso vira criativo do produto do cliente, concreto (qual foto, qual promessa, qual prova da oferta.json)",
  "encaixe": 8
}
```
**Tipos** (use exatamente um destes): produto em destaque · produto em uso · foto de celular (UGC) · antes e depois ·
comparação nós × eles · depoimento/avaliação · lista de benefícios · ingredientes/composição · oferta/promoção ·
kit/bundle · problema → solução · texto nativo (nota, tweet, print de chat) · notícia/advertorial · meme/humor ·
detalhe/textura · flat lay · autoridade/especialista · pergunta/quiz · fundador/bastidor · outro.

`encaixe` (0–10) = o quanto ESTA referência dá um bom criativo pro produto do cliente:
+3 o produto tem o que ela precisa (tipo de foto, prova, mecanismo, oferta) · +3 carrega a promessa principal do
cliente · +2 dá pra gerar com fidelidade (produto não deforma, texto curto) · +2 combina com a marca do cliente ·
− risco de compliance ou de parecer cópia.

## Síntese: `padroes.json`
Agrupe as leituras por estrutura (tipo + como o layout é montado + ângulo). Um padrão precisa de 2+ referências OU
1 referência muito validada (nota 75+). 5–10 padrões costuma ser o certo.
```json
[{
  "id": "p1",
  "nome": "Produto gigante + 3 benefícios em selos",
  "descricao": "como a peça é montada (fundo, posição do produto, onde fica o texto, quantos elementos)",
  "refs": ["id1", "id2", "id3"],
  "peso": 212.4,
  "porque_funciona": "…",
  "como_aplicar": "no produto do cliente: foto 01 de frente, título com a promessa X, selos com 3 diferenciais da LP",
  "precisa": ["foto de frente com fundo limpo", "3 diferenciais curtos"],
  "risco": "",
  "encaixe": 9,
  "usado_em": []
}]
```
- `peso` = soma das notas de validação das refs (o script não calcula; somar do `refs.json`).
- Ordenar pelo que mais vale a pena testar: `encaixe` alto E `peso` alto primeiro.
- `usado_em` é preenchido quando o padrão vira criativo num lote (ids `l1c1`…).

## O que observar (o que costuma separar validado de não validado em imagem estática)
- Uma ideia por peça; leitura em 1 segundo. O título raramente passa de 8 palavras.
- O produto é grande e reconhecível, ou a peça é deliberadamente "nativa" (parece post, nota, print, foto de amigo).
- Prova concreta e específica (número, estrelas, nome de mídia) perto do título.
- Contraste alto entre título e fundo; uma cor de destaque só.
- Oferta só quando é forte (desconto grande, kit, frete grátis); senão o anúncio vende benefício.
- Formato vertical 4:5 domina no feed; 1:1 aparece em marca antiga; 9:16 é story.

## Muitas referências (> ~45): subagentes em paralelo
`python3 $M/pranchas.py --por-lote 12` gera `analise/lotes_leitura/<n>.json`. Um subagente por lote, 3–4 de cada vez,
descrição em português. Prompt:
```
Você vai fazer a leitura de design de anúncios de imagem validados (que estão vendendo) para servir de base a novos
criativos do produto do cliente. Só leitura de imagens + gravar JSON.
1. Leia o esquema e as regras: <raiz do repositório>/.claude/skills/clone-criativo/references/leitura-design.md
2. Leia a oferta do cliente: <projeto>/oferta.json (pra preencher "transplante" e "encaixe").
3. Abra seu lote: <projeto>/analise/lotes_leitura/<n>.json — tem "pranchas", "ids" e "saida_dir".
4. Em cada prancha (4 anúncios, rótulo "#n · id · marca · nota"), leia cada anúncio. Se o texto estiver pequeno,
   abra <projeto>/refs/<id>.jpg. Os dados do anúncio (headline, copy, link) estão em <projeto>/refs.json.
5. Grave um JSON por id em <saida_dir>/<id>.json, no esquema exato. Não pule id.
Responda no fim só: quantos leu e os 3 tipos que mais apareceram.
```
Depois, eu sintetizo os padrões (não delegar a síntese: ela decide o lote).
