# Gerar o lote (Magnific, Gemini ou OpenAI) e conferir

## 1. Briefs (`lotes/lote<N>/briefs.json`) — antes de gastar crédito
Lote 1 = 5 criativos, cada um de um padrão diferente:
- 3 dos padrões com maior `encaixe × peso`;
- 1 com a oferta (preço/kit/frete/garantia), se a oferta for forte; senão outro padrão de prova;
- 1 aposta (padrão validado menos óbvio, ou um ângulo que a LP tem e os concorrentes não usam).
Ângulos diferentes entre os 5 (dor, desejo, prova, oferta, curiosidade…). Lotes seguintes: ver `pagina-e-votos.md`.
```json
[{
  "id": "l1c1",
  "padrao": "p1",
  "padrao_nome": "Produto gigante + 3 benefícios em selos",
  "ref_id": "1234567890",
  "angulo": "desejo: aparência premium no trabalho",
  "proporcao": "4:5",
  "textos": {"titulo": "Couro legítimo que dura 10 anos", "apoio": "Cabe notebook 15,6\"", "selos": ["Garantia de 1 ano", "Frete grátis", "12x sem juros"], "rodape": ""},
  "fotos_produto": ["lp/img/01.jpg"],
  "composicao": "como montar a peça, baseado na leitura da ref (fundo, posição, tamanhos, cores da marca do cliente)",
  "porque": ["por que deve vender — 2 bullets curtos pro usuário"],
  "texto_anuncio": {"primario": "texto do anúncio pro Gerenciador (3–6 linhas)", "titulo": "até 40 caracteres", "descricao": ""},
  "cuidado": ""
}]
```
Regras do texto da imagem: título ≤ 8 palavras; total ≤ ~25 palavras; números e preços iguais aos da `oferta.json`;
PT-BR com acento; nada que a LP não sustente. `cuidado` = aviso de compliance pro usuário (ou vazio).

## 2. Qual gerador, conta e custo (sempre, a cada sessão) → esperar o ok
O gerador está em `config.json → gerador` (vem do `GERADOR` do `.env`; sem `.env` = `magnific-mcp`).

**magnific-mcp** (o conector do Magnific no Claude Code — é o que gerou o exemplo original):
- `mcp__magnific__account_profile` e `account_balance`: mostrar nome/e-mail e saldo e perguntar se é a conta certa
  (quem tem mais de uma conta pode estar logado na errada).
- `simulate_cost` com `{"mode":"imagen-nano-banana-2-1","resolution":"2k","aspectRatio":"4:5","count":2,"prompt":"x"}`.
  Referência (nov/2026): **~65 créditos por imagem** → lote (5 briefs × 2 variações) ≈ **650 créditos**. Correção = +1
  imagem. Se o modelo `imagen-nano-banana-2-1` não existir mais, `images_models_list` e escolher o Nano Banana mais novo.

**gemini** / **openai** (API com chave, `motor/gera.py`):
- Dizer qual provedor e modelo (`.env`) e o custo aproximado: 10 imagens por lote. Preço muda — mandar o usuário
  conferir na página de preços do provedor (Google AI Studio / OpenAI) se ele perguntar. Nunca inventar valor.
- `python3 $M/gera.py ... --simular` antes, pra conferir que o pedido está montado (não gasta nada).

Mensagem pro usuário (bullets): gerador, conta/saldo (se der), custo do lote, os 5 briefs em 1 linha cada.
**Gerar só depois do ok.**

## 3. Subir as imagens de referência
### magnific-mcp (uma vez por projeto; guardar ids em `magnific.json`)
- Pasta no Magnific pra não bagunçar a biblioteca do usuário: `folders_create` ("Clone Criativo · <Marca> · <Produto>")
  e passar o `folderReference` em TODA chamada de upload/geração desse projeto (ele não persiste sozinho).
- Foto do produto: `creations_upload_image(url=<oferta.json fotos_produto[].url>, fileName="produto-01.jpg")`.
- Anúncio de referência, nesta ordem:
  1. `refs.json → url_imagem` (fbcdn) se a coleta tem menos de ~24 h;
  2. a cópia publicada `<config.url>r/<id>.jpg` (só se a página estiver publicada numa hospedagem);
  3. arquivo local: `creations_request_upload(mimeType="image/jpeg")` → `curl -s -X PUT -H "Content-Type: image/jpeg"
     --data-binary @refs/<id>.jpg "<url assinada>"` → `creations_finalize_upload(path=…, fileName="ref-<id>.jpg", visible=false)`.
- `magnific.json`: `{"pasta": "<folderReference>", "produto": {"lp/img/01.jpg": "<identifier>"}, "refs": {"<ad id>": "<identifier>"}}`.
### gemini / openai
Nada a subir: o `gera.py` manda os arquivos locais (`lp/img/…`, `refs/<id>.jpg`) junto com o pedido.

## 4. Gerar
### magnific-mcp
`images_generate` por brief: `mode="imagen-nano-banana-2-1"`, `resolution="2k"`, `aspectRatio="4:5"`, `count=2`,
`references=[{"type":"image","identifier":<produto>}, (outra foto do produto se o brief pede), {"type":"image","identifier":<ref>}]`.
Disparar os 5 seguidos (não esperar um pra mandar o outro), depois `creations_wait` em grupos de até 8.
Assim que ficar pronto: `python3 $M/baixa.py <url> lotes/lote1/gerados/l1c1_a <url2> lotes/lote1/gerados/l1c1_b`
(o link expira).
### gemini / openai
Gravar o prompt em `lotes/lote1/prompts/l1c1.txt` e:
```bash
python3 $M/gera.py --prompt lotes/lote1/prompts/l1c1.txt --ref lp/img/01.jpg --ref refs/<ad id>.jpg \
                   --saida lotes/lote1/gerados/l1c1 --n 2
```
A ordem dos `--ref` é a ordem das "Image 1, Image 2…" do prompt. Os 5 briefs podem rodar em paralelo (5 comandos em
segundo plano). Erro de modelo inexistente → trocar `GEMINI_IMAGE_MODEL`/`OPENAI_IMAGE_MODEL` no `.env`.
Bloqueio de conteúdo (a API recusa) → suavizar o prompt (tirar pessoa, tirar promessa forte) e tentar 1 vez.

### Receita do prompt (instrução em inglês, texto da imagem em PT-BR entre aspas)
```
Create a high-converting static Meta feed ad, vertical 4:5.
REFERENCES: Image 1 = the product. Keep it EXACTLY as it is: shape, proportions, colors, materials, logo and label
text. Never redraw or invent packaging text. [Image 2 = the same product, <angle>.] Image <k> = a successful ad used
ONLY as a layout and style model.
LAYOUT (from the model ad): <composicao do brief, concreta: fundo, onde fica o produto e em que tamanho, onde fica cada
texto, selos, ícones, estrelas, botão>.
Do NOT copy anything that identifies the model ad's brand: no logo, brand name, product, photos, people or words.
TEXT ON THE IMAGE — Brazilian Portuguese, spelled exactly as written, accents included, and no other text anywhere:
- Headline: "<titulo>"
- Support line: "<apoio>"
- Badges: "<selo 1>", "<selo 2>", "<selo 3>"
STYLE: brand colors <hex principal> (main), <hex destaque> (accent), background <hex/descrição>; typography <ex.: heavy
geometric sans-serif headline, clean sans body>; <estilo de foto: ex. bright soft studio light / natural iPhone photo>.
Clean, legible at phone size, generous margins, product sharp and in focus. No watermark.
```
- Peça nativa (nota, print de review, tweet): descrever o "suporte" (fundo de papel, card de review com estrelas…) e
  manter o produto em foto real.
- Pessoa na peça: descrever perfil igual ao público da oferta; nunca rosto de pessoa real da referência.
- **Pessoa real do cliente (dono, sócio, especialista): perguntar antes** se pode gerar rosto com IA. Se for "só foto
  real": o prompt pede um cartão/moldura VAZIA no lugar ("an empty rounded photo frame,
  plain dark gray inside, where a portrait will be placed later") e a foto entra depois, por código:
  `python3 $M/compoe.py gerado.png final.png --foto lp/img/01.jpg --caixa x,y,l,a --raio 0.05 --ancora topo [--borda "#DDB45F" --borda-px 4]`
  (frações da imagem; conferir no Read se a caixa caiu em cima da moldura). Mesmo jeito pra logo exato (`--conter`).

### Tela de aparelho (notebook/celular mostrando o produto)
A IA redesenha o texto miúdo da tela e INVENTA palavra ("Quebre de pacho", "Poxefro de voz" — lote 1 do Creator que
Vende). Sempre trocar a tela por código depois:
1. recortar as telas reais da LP: `python3 $M/recorta.py "<lp>" "mock_curso=PROGRESSO;mock_fabrica=VOCÊ ESCOLHE" --min 380x260`
   e, pra tela de CELULAR, a versão de celular do mesmo bloco (`--celular`): ela vem em coluna e cabe em pé;
2. medir a tela do aparelho no gerado (recorte a região, Read, anotar os cantos);
3. colar: guardar o recorte do aparelho da frente → pintar a tela de trás de preto e colar a tela real (inteira, sem
   cortar) → devolver o aparelho da frente por cima com máscara arredondada → pintar a tela do celular e colar a versão
   de celular cortada pelo topo. Ficou nítido e certo (testado num infoproduto real).

### Infoproduto (sem foto de produto)
O "produto" é o mockup da LP (tela da aula, app, capas de bônus, mural de logos) — `recorta.py` tira em 2x. Foto de
pessoa real só colada (`compoe.py`), se o dono pediu assim.

## 5. Conferir cada imagem (Read em todas, sempre)
- [ ] Texto letra por letra (acento, cedilha, número, R$, vírgula). Uma letra errada = não serve.
- [ ] Produto fiel (formato, cor, logo, rótulo). Rótulo pode ficar ilegível pequeno, mas não pode ter palavra inventada.
- [ ] Nada da marca da referência (logo, nome, foto, frase).
- [ ] Sem mão/dedo deformado, objeto derretido, texto fantasma no fundo.
- [ ] Legível no celular (título grande, contraste).
- [ ] Bate com o brief e com a leitura da referência.
Escolha a melhor das 2 variações. Se as 2 falharem:
1. Texto errado e o resto bom → `images_generate` com a imagem gerada como 1ª referência e o prompt "Keep everything
   identical; only change the text to exactly: …" (ou `mode="ideogram-4-5"` + `preciseEdit=true`).
2. Produto deformado → refazer com o prompt mais restrito ("product must match Image 1 pixel-perfect in shape/label")
   e o produto maior/mais frontal.
Máximo 2 correções por criativo; se não sair, troca o brief e anota no `lote.json` (`nota`).

## 6. `lotes/lote<N>/lote.json` (o que a página mostra)
```json
{"n": 1, "data": "06/11", "nota": "1º lote: 5 padrões diferentes pra descobrir o que funciona",
 "criativos": [{"id": "l1c1", "arquivo": "lotes/lote1/gerados/l1c1_b.png", "padrao": "Produto gigante + 3 benefícios",
   "ref_id": "1234567890", "angulo": "…", "headline": "…", "porque": ["…", "…"],
   "texto_anuncio": {"primario": "…", "titulo": "…", "descricao": ""}, "cuidado": "",
   "prompt": "…", "modelo": "imagen-nano-banana-2-1", "creditos": 130}]}
```
Depois: preencher `usado_em` no `padroes.json`, `python3 $M/pagina.py`, servidor/publicação, `python3 $M/testa.py`, link pro usuário
com o resumo (5 bullets: padrão → título) e o gasto do lote.
