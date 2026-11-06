# Ler a LP e escrever `oferta.json`

## O que olhar (nessa ordem)
1. `lp/dobra_mobile.jpg` e `lp/dobra_desktop.jpg` — promessa principal, prova na dobra, preço, botão.
2. `lp/mobile_*.jpg` (fatias da página inteira no celular) — mecanismo, benefícios, prova social, kits, garantia, FAQ.
3. `lp/imagens.jpg` (fotos numeradas) — quais são do PRODUTO (embalagem, frente/verso, em uso, detalhe). Anote os números.
4. `lp/lp.json` — `shopify_produto` (preço, de/por, variantes, descrição), `precos` (R$ com contexto), `titulos`,
   `botoes`, `jsonld` (nota/avaliações), `cores_fundo`, `estilos` (fonte e cor do h1/CTA). O `texto` inteiro só se faltar algo.

Se `senha: true` ou a página não tem produto: parar e pedir outra URL ou prints.

## Esquema (`oferta.json`)
```json
{
  "marca": "Minha Marca",
  "produto": "Mochila Executiva Couro Legítimo",
  "categoria": "mochila de couro masculina para trabalho",
  "url": "https://...",
  "promessa": "a frase de promessa principal, nas palavras da LP",
  "mecanismo": "o porquê funciona/é diferente (material, tecnologia, método) — vazio se a LP não tem",
  "publico": "quem compra (e quem usa, se diferente)",
  "dores": ["…"], "desejos": ["…"], "objecoes": ["…"],
  "provas": ["4,8★ em 1.200 avaliações", "+30 mil clientes", "selo X"],
  "diferenciais": ["…"],
  "preco": {"por": "R$ 389,90", "de": "R$ 549,90", "parcelado": "12x de R$ 37,99", "kits": ["2 por R$ 699"]},
  "oferta": {"frete": "frete grátis Sul/Sudeste", "garantia": "30 dias", "brinde": "", "urgencia": ""},
  "identidade": {"cores": ["#1b1b1b", "#c8a46a", "#f5f1ea"], "fontes": ["Playfair Display (títulos)", "Inter"],
                 "estilo_foto": "estúdio fundo claro + homem de terno na rua", "tom": "sóbrio, premium"},
  "fotos_produto": [
    {"arquivo": "lp/img/01.jpg", "url": "https://cdn.../foto.jpg?width=2048", "mostra": "frente, fundo branco", "uso": "referência principal"},
    {"arquivo": "lp/img/04.jpg", "url": "https://...", "mostra": "aberta, compartimentos", "uso": "detalhe"}
  ],
  "restricoes": ["não prometer resultado garantido", "não usar antes/depois de corpo", "não citar preço do concorrente"],
  "busca": {
    "pt_br": ["mochila executiva couro", "mochila couro masculina", "mochila para notebook couro"],
    "en_mundo": ["leather work backpack", "leather laptop backpack men"],
    "promessa_pt": ["mochila que cabe notebook e roupa"],
    "concorrentes": [{"nome": "Bellroy", "dominio": "bellroy.com"}, {"nome": "Couro & Co", "dominio": "..."}]
  }
}
```
- **Nada inventado.** Preço, número de avaliações, garantia e frete exatamente como estão na LP; o que não existe fica
  vazio. Os criativos só podem usar o que está aqui.
- `fotos_produto[].url` = a `url` da foto em `lp/lp.json → fotos` (é pública; o gerador sobe por ela). A 1ª é a mais
  fiel do produto inteiro (fundo limpo); ela vira a referência de produto em todo brief.
- `restricoes`: categoria sensível (suplemento, cosmético com promessa, emagrecimento, saúde, finanças) → listar o que
  a Meta barra. Na dúvida, rodar a skill `compliance-checker` na própria LP.

## Termos de busca (o que mais decide a qualidade das 10–15 marcas)
- **PT (país BR)**: 6–10 termos. Categoria do produto do jeito que o cliente final fala ("mala de bordo", não
  "bagagem de mão rígida em policarbonato"), variações com o material/benefício, e 1–2 com a promessa.
- **EN (país ALL)**: 4–8 termos. O mercado gringo tem mais marca escalada e mais anúncio na UE (alcance real).
- Frase exata (`--exata`) só pra termo de 2–4 palavras bem específico; termo amplo sem aspas.
- Evitar termo que puxa outro mercado ("bolsa" puxa bolsa de valores; "mala" puxa mala direta). Se uma busca trouxer
  muito anunciante fora do tema, passar `--ruim "regex"` no `anunciantes.py`.
- **Concorrentes**: os que eu já conheço do nicho + WebSearch ("melhores marcas de <categoria>", "<categoria> loja
  online", "<category> brand DTC") → domínio → `biblioteca.py pageid "dominio1;dominio2"`.
