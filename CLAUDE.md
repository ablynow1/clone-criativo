# Clone Criativo — instruções pro Claude

Este repositório é o **Clone Criativo**: o usuário manda o link de uma página de produto e você gera criativos de
imagem modelados nos anúncios que já estão vendendo na Biblioteca de Anúncios da Meta, em lotes de 5, numa página de
aprovação. O método completo está na skill `.claude/skills/clone-criativo/SKILL.md` — siga ela sempre.

Fale sempre em **português do Brasil**, em bullets curtos, sem jargão técnico desnecessário.

## Primeira conversa (o usuário acabou de clonar/instalar)
Se a pasta `projetos/` não tem nenhum projeto (só o `.gitkeep`) **ou** o usuário perguntar "o que é isso" / "como
funciona" / "por onde começo", faça nesta ordem:

1. **Explique o projeto em detalhe**, com base no `README.md` (leia ele antes). Cubra, em seções curtas:
   - o que o Clone Criativo faz e o que ele entrega no fim (a página com 4 abas e os lotes de 5 criativos);
   - as 8 etapas do fluxo (link → oferta → marcas validadas → ranking → leitura de design → padrões → lote → votos),
     dizendo quanto tempo cada uma leva e o que ele vê em cada uma;
   - como a "validação" é medida e o limite honesto dela (a Meta não mostra impressão de anúncio que roda só no
     Brasil; o alcance real só aparece em anúncio que roda na Europa);
   - o que ele precisa ter (gerador de imagem conectado; o resto o `verifica.py` confere);
   - quanto custa (só o gerador de imagem gasta: ~10 imagens por lote) e que você **sempre** pede o ok antes de gastar;
   - as regras: modelar sem copiar, só preço/prova que estão na página dele, compliance da Meta.
2. **Rode `python3 motor/verifica.py`** e mostre o resultado. Se tiver ✗, guie a instalação pelo `INSTALACAO.md`,
   um passo por vez (comandos que ele precisa rodar no terminal: sugira digitar `! <comando>` aqui no Claude Code).
3. **Ajude a escolher o gerador de imagem** se ainda não tiver: Magnific pelo conector (recomendado, é o que gerou o
   exemplo original), Google Gemini por chave de API, ou OpenAI por chave de API. Crie o `.env` a partir do
   `.env.exemplo` com o que ele escolher. Nunca peça pra ele colar a chave no chat se ele puder colar direto no `.env`;
   se ele colar no chat, grave no `.env` e avise que a chave ficou no histórico da conversa.
4. Termine com: **"Me manda o link da página do produto que eu começo."**

## Quando o usuário mandar um link de produto
Use a skill `clone-criativo` (SKILL.md) do passo 0 ao 8. Antes de gerar imagem, mostre gerador/conta/custo e espere o ok.

## Regras do repositório
- Projetos de produto ficam em `projetos/<produto>/` e **nunca** vão pro git (estão no `.gitignore`), nem o `.env`.
- Não edite o `motor/` pra resolver um caso só; se precisar mudar o motor, explique o porquê ao usuário antes.
- Nenhum produto vem de exemplo no repositório: tudo começa do link que o usuário mandar.
