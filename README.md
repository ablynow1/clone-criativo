# Clone Criativo

**Você manda o link da página do seu produto. O Claude acha os anúncios de imagem que estão vendendo de verdade na
Biblioteca de Anúncios da Meta, entende por que eles funcionam e gera criativos novos do SEU produto, no mesmo modelo,
em lotes de 5 pra você aprovar.**

Funciona dentro do [Claude Code](https://claude.com/claude-code). Não é um app com botão: é um método + um motor de
scripts que o Claude roda por você, conversando em português.

> Instalação, conexão do gerador de imagem (Magnific, Gemini ou OpenAI) e hospedagem: **[INSTALACAO.md](INSTALACAO.md)**.

---

## O que você recebe no fim

Uma **página de aprovação** (abre no seu navegador, e no celular se quiser) com 4 abas:

| Aba | O que tem |
|---|---|
| **Lotes** | Os criativos gerados, 5 por lote. Cada um mostra o anúncio validado que o originou, por que deve vender, o texto do anúncio pronto pra colar no Gerenciador, botões ✓ Aprovar / ✕ Reprovar, caixa de ajuste ("troca o fundo", "título maior") e "Baixar em alta". |
| **Validados** | As 10–15 marcas escolhidas (quantos anúncios validados cada uma tem, por que entrou) e os ~45 anúncios de imagem mais validados, com nota de 0 a 100 e a leitura de design de cada um. |
| **Padrões** | O que se repete entre os que vendem (ex.: "produto gigante + 3 selos de benefício", "print de avaliação", "comparação nós × eles") e como cada padrão encaixa no seu produto. |
| **Sua oferta** | Como o Claude leu a sua página (promessa, provas, preço, público, cores) + uma caixa pra corrigir a leitura. |

Os seus votos voltam pro Claude e **ensinam o lote seguinte**: variações do que você aprovou, nada parecido com o que
você reprovou, e os padrões que ainda não foram testados.

---

## Como funciona (as 8 etapas)

| # | Etapa | Tempo | O que acontece |
|---|---|---|---|
| 1 | **Projeto** | segundos | Cria `projetos/<produto>/`. |
| 2 | **Ler a página** | ~5 min | Um Chrome invisível abre a página no computador e no celular: tira prints, textos, preços, cores, fontes e fotos do produto. O Claude escreve a **oferta** (promessa, mecanismo, provas, preço, frete, garantia, público, o que NÃO pode prometer) e os **termos de busca**. |
| 3 | **Achar marcas validadas** | 25–40 min | Busca na Biblioteca de Anúncios da Meta em português (Brasil) e em inglês (mundo), mais os concorrentes que você ou o Claude conhecem. Escolhe 12–18 marcas que vendem a mesma coisa ou a mesma promessa e coleta os anúncios ativos de cada uma. |
| 4 | **Ranking** | ~2 min | Dá uma nota de validação (0–100) a cada anúncio de **imagem** e fica com os ~45 melhores (até 5 por marca). |
| 5 | **Leitura de design** | ~15 min | O Claude olha cada anúncio: o que para o dedo, a hierarquia, a prova, o ângulo, a paleta, por que funciona e como vira criativo do seu produto. Agrupa em **padrões**. |
| 6 | **1ª leva da página** | ~1 min | Você já vê as marcas, os validados e os padrões antes de gastar qualquer crédito. |
| 7 | **Lote de 5** | ~10 min | 5 briefs de padrões diferentes → o Claude mostra o custo e **espera o seu ok** → gera 2 variações de cada → confere uma por uma (texto letra por letra, produto fiel, nada da marca do concorrente) → refaz o que falhar → publica. |
| 8 | **Votos → próximo lote** | — | Você aprova/reprova/pede ajuste na página; o Claude lê os votos e monta o lote seguinte. |

### O que é "validado" (e o limite honesto disso)
Um anúncio é validado quando **continua no ar há 14+ dias** — ninguém mantém anúncio que não vende. A nota soma:

- **posição na ordem por impressões** dentro da marca (a Meta ordena; 1º = o que mais aparece) — 35 pontos;
- **dias no ar** — 25 pontos;
- **variações** (o mesmo criativo duplicado em vários conjuntos = escala) — 20 pontos;
- **alcance real** na Europa — 20 pontos;
- tudo × o peso da marca (quantos anúncios validados ela tem).

A Meta **não mostra impressão nem alcance** de anúncio comercial que roda só no Brasil. Quando o anúncio também roda na
União Europeia, ela mostra quantas pessoas ele alcançou de verdade — esse é o único número real, e aparece em azul na
página. Marcas gringas entram justamente por isso: trazem padrão testado em escala e alcance real.

### Regras que o Claude segue sempre
- **Modelar, não copiar.** Do anúncio validado vem a estrutura (layout, hierarquia, tipo de prova, ângulo). Produto,
  fotos, textos e marca são seus. Nunca o logo, nome, foto ou frase do concorrente.
- **Só o que está na sua página.** Preço, desconto, frete, número de avaliações e garantia exatamente como estão lá.
- **Compliance da Meta.** Sem atributo pessoal ("você está acima do peso?"), sem antes/depois de corpo, sem cura ou
  resultado garantido.
- **Só anúncio que leva pra loja.** Anúncio que manda pro Instagram, WhatsApp ou marketplace fica de fora.
- **Nunca gasta crédito sem o seu ok.** Antes de cada lote ele mostra o gerador, a conta, o saldo e o custo.

---

## Começo rápido

```bash
git clone https://github.com/ablynow1/clone-criativo.git
cd clone-criativo
bash instalar.sh          # instala o que falta e confere a máquina
claude                    # abre o Claude Code dentro da pasta
```

Na primeira conversa o Claude explica o projeto, confere a instalação e te ajuda a conectar o gerador de imagem.
Depois é só mandar:

> Gera criativos pra esse produto: https://sualoja.com.br/products/seu-produto

Outros pedidos que ele entende: "próximo lote", "faz variações dos aprovados", "traz mais referências",
"procura só marcas gringas", "quero formato story 9:16".

---

## Quanto custa
- **Coleta na Biblioteca e leitura**: nada além do seu plano do Claude Code.
- **Imagens**: cada lote = 5 criativos × 2 variações = ~10 imagens (+1 por correção). No Magnific (Nano Banana 2K) deu
  ~65 créditos por imagem em nov/2026 (~650 por lote). No Gemini e na OpenAI, veja o preço por imagem na página do
  provedor. O Claude sempre mostra o custo antes.

## Estrutura do repositório

```
clone-criativo/
├── README.md                 ← você está aqui
├── INSTALACAO.md             ← instalar, conectar gerador, publicar a página
├── CLAUDE.md                 ← o que o Claude faz ao abrir o projeto
├── instalar.sh               ← instala dependências e roda o verifica.py
├── .env.exemplo              ← copie pra .env (gerador, chaves, hospedagem)
├── .claude/skills/clone-criativo/
│   ├── SKILL.md              ← o método, passo a passo (o Claude segue isso)
│   └── references/           ← regras de cada etapa (oferta, biblioteca, leitura, geração, página)
├── motor/                    ← scripts Python que o Claude roda
│   ├── lp.py                 ← lê a página do produto
│   ├── biblioteca.py         ← coleta da Biblioteca de Anúncios (Chrome invisível)
│   ├── parse.py · anunciantes.py · ranking.py · pranchas.py
│   ├── gera.py               ← gera imagem por API (Gemini / OpenAI)
│   ├── pagina.py · servidor.py · publica.sh · testa.py · votos.py
│   └── assets/               ← modelo da página + voto.php
└── projetos/                 ← um projeto por produto (fica só no seu computador)
```

## Perguntas comuns
**Preciso de login no Facebook?** Não. A Biblioteca de Anúncios é pública; o Chrome invisível abre sem login.

**A Meta pode bloquear?** Se fizer muita busca seguida, ela devolve página vazia por um tempo. O motor faz uma coleta
por vez, com pausa entre páginas; se bloquear, espera ~40 min e continua de onde parou (o que já veio fica guardado).

**Funciona com qualquer loja?** Qualquer página pública de produto (Shopify, Nuvemshop, Yampi, WooCommerce, página
própria). Página com senha não dá: mande prints.

**E infoproduto (curso, ebook)?** Funciona. Sem foto de produto, o Claude recorta os mockups da própria página.

**Funciona no Windows?** Use o WSL (Ubuntu dentro do Windows) com o Chrome instalado. No Mac e no Linux, direto.
