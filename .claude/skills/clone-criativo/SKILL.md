---
name: clone-criativo
description: >
  Sistema "página de produto → criativos validados → lotes de 5 criativos novos pra aprovar". O usuário manda o LINK da
  página de produto (LP); eu leio a oferta e a promessa, acho na Biblioteca de Anúncios da Meta 10–15 marcas validadas
  vendendo a mesma coisa (ou a mesma promessa), ranqueio os anúncios de IMAGEM que mais estão vendendo (ordem por
  impressões, dias no ar, variações e alcance real na Europa quando existe), faço a leitura de design de cada um, tiro
  os padrões que se repetem, cruzo com a oferta dele e gero lotes de 5 criativos (Magnific, Gemini ou OpenAI) numa
  página de aprovação (aprovar, reprovar, pedir ajuste). Os votos ensinam o lote seguinte. Use quando o usuário mandar
  um link de produto/LP, pedir "criativos", "lote de criativos", "criativos baseados nos que estão vendendo",
  "escaneia a biblioteca", "modela os validados pro meu produto", "leitura de design dos concorrentes", "próximo lote"
  ou "faz variações dos aprovados".
---

# Clone Criativo — do link do produto ao lote aprovado

Fluxo: **link → oferta → 10–15 marcas validadas → ranking dos anúncios de imagem → leitura de design → padrões →
lote de 5 → página de aprovação → votos ensinam o próximo lote.**

Caminhos (sempre a partir da raiz do repositório):
```bash
RAIZ="$(git rev-parse --show-toplevel)"; M="$RAIZ/motor"
```
Os scripts do `motor/` rodam **dentro da pasta do projeto** (`projetos/<produto>/`), salvo `novo.py` e `verifica.py`.

## Como falar com o usuário
- Português do Brasil, bullets curtos, a decisão dele no topo, números (créditos, R$, minutos) na própria linha.
- Descrição de comando e de agente também em português.
- **Entregar em levas**: abrir a página assim que a leitura dos validados estiver pronta (antes do lote) e dizer quanto
  tempo falta. Coleta longa roda em segundo plano; dar notícia a cada etapa.
- **Antes de gastar crédito de imagem**: mostrar gerador, conta/saldo e custo do lote e **esperar o ok**
  (`references/geracao.md` §2). Nunca gerar sem o ok.
- Tudo de navegador roda num Chrome headless próprio (não usa o Chrome dele, não precisa de login no Facebook).

## Passo 0 — conferir a máquina (1ª vez ou se algo falhar)
`python3 $M/verifica.py` (da raiz). Se tiver ✗, ajudar a resolver com o `INSTALACAO.md` antes de seguir.

## Passo a passo

### 0. Combinar (sem interrogatório)
Padrões quando ele não disser: mercado **BR + mundo**, imagem estática **4:5**, lote de **5**, validado = **14+ dias**.
Pergunte só o que muda o resultado (ex.: página com senha, produto com várias versões, rosto de pessoa real).

### 1. Projeto
```bash
python3 $M/novo.py <produto> "<link da página>" "<Marca · Produto>"     # produto = slug: bolsa-couro
cd "$RAIZ/projetos/<produto>"
```

### 2. Ler a página e escrever a oferta (~5 min)
```bash
python3 $M/lp.py "<link>"     # prints desktop/celular, textos, preços, cores, fontes, fotos (lp/img + lp/imagens.jpg)
```
Leia `lp/dobra_*.jpg`, as fatias `lp/mobile_*.jpg`, `lp/imagens.jpg` e o `lp/lp.json` (não leia o `texto` inteiro se
não precisar). **Infoproduto** (sem foto de produto): recorte os mockups da própria página em alta —
`python3 $M/recorta.py "<link>" "mock_curso=<texto do bloco>;mock_app=<texto>"` (e `--celular` pra tela de celular).
Escreva **`oferta.json`** — esquema e regras em `references/oferta.md` (promessa, mecanismo, provas, preço,
restrições de compliance, fotos boas do produto, **termos de busca** e concorrentes).

### 3. Achar as 10–15 marcas validadas (~25–40 min de Biblioteca, em segundo plano)
`references/biblioteca.md` tem o detalhe. Uma coleta por vez (o script espera a vez sozinho).
```bash
python3 $M/biblioteca.py busca "termo pt 1;termo pt 2;..." --pais BR      # 6–10 termos PT
python3 $M/biblioteca.py busca "en term 1;en term 2;..." --pais ALL       # 4–8 termos EN
python3 $M/biblioteca.py pageid "concorrente.com.br;brand.com"            # concorrentes que eu já conheço/achei na web
python3 $M/parse.py && python3 $M/anunciantes.py                          # candidatos.json + analise/candidatos_*.jpg
```
Olhe as pranchas e escolha **12–18** que vendem a mesma coisa ou a mesma promessa, com clique pra loja →
`marcas.json` (`[{"nome","page_id","site","motivo"}]`). Depois:
```bash
python3 $M/biblioteca.py paginas marcas.json && python3 $M/parse.py      # páginas + alcance real UE
```
Corte pra **10–15** (escala + relevância) e mande a lista pro usuário (marca · loja · nº validados · por que entrou).

### 4. Ranking dos anúncios de imagem (~2 min)
```bash
python3 $M/ranking.py      # nota 0–100 de validação, tira repetido, baixa refs/ → refs.json + marcas_stats.json
```
Se sobrou imagem da UE sem alcance: `biblioteca.py alcance --ads cands_ue.json` e `ranking.py` de novo.
Saída: top ~45, até 5 por marca.

### 5. Leitura de design + padrões (~15 min)
```bash
python3 $M/pranchas.py      # analise/pranchas/r###.jpg (4 por prancha) + lotes de leitura
```
Ler cada referência e gravar `analise/leitura/<id>.json`; depois sintetizar **`padroes.json`** com o encaixe de cada
padrão no produto. Rubrica, esquemas e como escolher: `references/leitura-design.md`. Até ~45 refs eu leio direto;
acima disso, subagentes em paralelo (prompt pronto lá). A síntese dos padrões é sempre minha.

### 6. Abrir a primeira leva (antes de gerar)
```bash
python3 $M/pagina.py && python3 $M/testa.py --local
python3 $M/servidor.py      # em segundo plano → http://localhost:8765/   (ou publica.sh, se ele tiver hospedagem)
```
Mande o link: abas **Validados** (marcas + criativos com nota e leitura), **Padrões** e **Sua oferta**.
Detalhe de abrir/publicar: `references/pagina-e-votos.md`.

### 7. Lote de 5 (~10 min)
`references/geracao.md`: briefs → gerador/conta/custo/**ok** → referências → gerar (2 variações por brief) → baixar →
**conferir cada imagem** (texto letra por letra, produto fiel, sem marca do concorrente) → corrigir/refazer o que
falhar → `lotes/lote<N>/lote.json` → `pagina.py` → `testa.py` → link.

### 8. Votos → próximo lote
```bash
python3 $M/votos.py         # ✓/✕/ajustes por criativo → votos.json
```
Atualize `gosto.md` (o que ele aprova/reprova e por quê, ajustes pedidos) e monte o próximo lote: variações dos
aprovados (outro gancho/fundo/formato) + padrões ainda não testados − o que ele reprovou.
Detalhe em `references/pagina-e-votos.md`.

## Regras que não mudam
- **Honestidade sobre "impressão"**: a Meta não mostra impressão de anúncio comercial no Brasil. A nota usa a ordem
  por impressões (a Meta ordena), dias no ar, variações e, quando o anúncio roda na UE, o **alcance real**. Dizer isso.
- **Só clique pra loja**: fora Instagram, WhatsApp, Facebook, link vazio, marketplace (Shopee, Amazon, Shein, Mercado
  Livre…) e loja de app — o `adlib.destino()` já classifica e o ranking já corta.
- **Modelar, não copiar**: do validado vem a estrutura (layout, hierarquia, tipo de prova, ângulo). Produto, fotos,
  textos e marca são do usuário. Nunca o logo, nome, foto ou frase do concorrente.
- **Compliance Meta** em todo brief: sem atributo pessoal ("você está acima do peso?"), sem antes/depois de corpo,
  sem cura/resultado garantido; números e selos só se estão na página.
- **Preço, desconto e frete exatamente como na página.** Texto da imagem em PT-BR conferido letra por letra.
- **Rosto de pessoa real** (dono, sócio, especialista): perguntar antes se pode gerar com IA. Se não, moldura vazia +
  foto real colada por código (`compoe.py`, ver `references/geracao.md`).
- **Uma coleta por vez** na Biblioteca. Código 3 = bloqueio: esperar ~40 min e rodar o mesmo comando (cache).
  Nunca martelar.
- URLs de imagem da Meta (`fbcdn`) e do Magnific expiram: baixar logo.
- Nunca subir `projetos/` nem `.env` pro GitHub (já estão no `.gitignore`).

## Arquivos do projeto (`projetos/<produto>/`)
`config.json` · `lp/` · `oferta.json` · `busca/` + `dumps/` · `ads.json` · `candidatos.json` · `marcas.json` ·
`alcance.json` · `refs.json` + `refs/` · `marcas_stats.json` · `analise/leitura/` · `padroes.json` ·
`lotes/lote<N>/{briefs.json,prompts/,gerados/,lote.json}` · `gosto.md` · `votos.json` · `pub/` (a página).
