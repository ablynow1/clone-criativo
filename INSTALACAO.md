# Instalação

Leva uns 15 minutos. No fim, `python3 motor/verifica.py` tem que dizer **== TUDO PRONTO**.

## 1. O que precisa ter

| O quê | Pra quê | Como conferir |
|---|---|---|
| **Claude Code** | é quem roda tudo | `claude --version` · instalar: https://claude.com/claude-code |
| **Python 3.9+** | os scripts do motor | `python3 --version` · Mac: vem com as ferramentas do Xcode (`xcode-select --install`) ou https://www.python.org |
| **Google Chrome** | lê a página do produto e a Biblioteca de Anúncios (roda invisível) | o `verifica.py` acha sozinho; se estiver em outro lugar: `export CHROME=/caminho/do/chrome` |
| **git** | baixar o repositório | `git --version` |
| **Um gerador de imagem** | criar os criativos | ver o passo 3 |

Sistema: **Mac** ou **Linux**. No **Windows**, use o WSL (Ubuntu) e instale o Chrome dentro dele
(`sudo apt install -y wget && wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && sudo apt install -y ./google-chrome-stable_current_amd64.deb`).

## 2. Baixar e instalar

```bash
git clone https://github.com/ablynow1/clone-criativo.git
cd clone-criativo
bash instalar.sh
```

O `instalar.sh` instala as duas bibliotecas Python (Pillow e websockets), cria o `.env` a partir do `.env.exemplo` e
roda o `verifica.py`. Se preferir na mão: `pip3 install -r requirements.txt` e `cp .env.exemplo .env`.

## 3. Conectar o gerador de imagem (escolha UM)

Defina no `.env` a linha `GERADOR=` com a opção escolhida.

### Opção A — Magnific pelo conector do Claude Code (recomendado)
É o que gerou o exemplo original: modelo **Nano Banana** em 2K, com o produto e o anúncio de referência como imagens
de entrada. O Claude chama o Magnific direto, sem chave no `.env`.

1. Tenha uma conta no **Magnific** (https://www.magnific.com) com plano que dê créditos de geração de imagem.
   Referência: ~65 créditos por imagem em 2K → ~650 créditos por lote de 5 (2 variações cada).
2. Adicione o conector (uma vez, vale pra todos os projetos):
   ```bash
   claude mcp add --transport http -s user magnific https://mcp.magnific.com
   ```
3. Abra o Claude Code (`claude`), digite `/mcp`, escolha **magnific** → **Authenticate**. O navegador abre: entre na
   sua conta do Magnific e autorize.
4. No `.env`: `GERADOR=magnific-mcp`.
5. Teste: peça ao Claude "mostra minha conta e o saldo do Magnific". Ele deve mostrar seu nome/e-mail e os créditos.

> Tem mais de uma conta no Magnific? Antes de cada lote o Claude mostra qual conta está conectada e espera o seu ok.
> Pra trocar: `/mcp` → magnific → limpar autenticação → Authenticate de novo, logado na conta certa.

### Opção B — Google Gemini ("Nano Banana") por chave de API
1. Crie a chave em https://aistudio.google.com/apikey (os modelos de imagem podem exigir faturamento ativado no
   projeto do Google Cloud ligado à chave).
2. No `.env`:
   ```
   GERADOR=gemini
   GEMINI_API_KEY=sua-chave
   GEMINI_IMAGE_MODEL=gemini-3-pro-image-preview
   ```
   `gemini-3-pro-image-preview` (Nano Banana Pro) gera em 2K e escreve texto melhor. Mais barato:
   `gemini-2.5-flash-image`. Se o Google renomear os modelos, troque essa linha pelo nome atual
   (lista em https://ai.google.dev/gemini-api/docs/models).
3. Teste sem gastar: `python3 motor/gera.py --prompt "teste" --ref <qualquer .jpg> --saida /tmp/x --simular`.

### Opção C — OpenAI (gpt-image) por chave de API
1. Crie a chave em https://platform.openai.com/api-keys (a OpenAI pode pedir a verificação da organização antes de
   liberar os modelos de imagem).
2. No `.env`:
   ```
   GERADOR=openai
   OPENAI_API_KEY=sua-chave
   OPENAI_IMAGE_MODEL=gpt-image-1
   ```
   O formato vertical sai em 1024×1536 (2:3); dá pra recortar pra 4:5 depois. Se a OpenAI lançar um modelo de imagem
   mais novo, troque o `OPENAI_IMAGE_MODEL`.

### Outro gerador?
Qualquer API que aceite **várias imagens de referência + texto** e devolva uma imagem serve (Flux Kontext, Ideogram,
Seedream…). Peça ao Claude: "adiciona o provedor X no gera.py" e passe a documentação da API. O formato do prompt
está em `.claude/skills/clone-criativo/references/geracao.md`.

## 4. Onde a página de aprovação abre

### Padrão: no seu computador (não precisa de nada)
O Claude roda `python3 motor/servidor.py` e te passa `http://localhost:8765/`. Os votos funcionam e ficam em
`projetos/<produto>/pub/dados/votos.jsonl`. Pra abrir no celular (mesma rede Wi-Fi): o Claude roda com `--rede` e te
passa o endereço com o IP do computador.

### Opcional: na sua hospedagem (pra mandar o link pra outra pessoa)
Precisa de hospedagem com **PHP** e acesso **FTP** (HostGator, Hostinger, Locaweb…). No `.env`:
```
SITE_BASE=https://seusite.com.br/criativos
FTP_HOST=ftp.seusite.com.br
FTP_USER=usuario
FTP_PASS=senha
FTP_PASTA=/public_html/criativos
```
E instale o `lftp` (Mac: `brew install lftp` · Linux: `sudo apt install lftp`). A página de cada produto fica em
`SITE_BASE/<produto>/`. O `SITE_BASE` vale pros projetos criados **depois** de preenchido.
Hospedagem só estática (GitHub Pages, Netlify, Vercel) abre a página, mas os votos não gravam; aí você vota pelo chat.

## 5. Conferir

```bash
python3 motor/verifica.py
```

```
✔ Python 3.11.6
✔ Pillow 11.3.0
✔ websockets 15.0.1
✔ Chrome: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome
✔ curl
✔ .env encontrado

Gerador de imagem: magnific-mcp
✔ conector do Magnific no Claude Code

Página de aprovação:
· sem hospedagem: a página abre no seu computador com  python3 motor/servidor.py  (votos funcionam)

== TUDO PRONTO
```

Pronto: abra o Claude Code na pasta (`claude`) e mande o link do produto.

## Problemas comuns
| Sintoma | O que fazer |
|---|---|
| `✗ não achei o Google Chrome` | instale o Chrome ou `export CHROME="/caminho/do/chrome"` (pode pôr no `~/.zshrc`) |
| A coleta termina com **código 3** | a Meta bloqueou por excesso de busca: espere ~40 min e peça pro Claude continuar (o que veio fica em cache) |
| Magnific: "Server not found" | rode de novo o `claude mcp add ...` do passo 3A e abra uma conversa nova |
| Gemini/OpenAI: "model not found" | troque o nome do modelo no `.env` pelo atual |
| A página não abre no celular | o computador e o celular precisam estar na mesma Wi-Fi; peça pro Claude subir o servidor com `--rede` |
| `pip3: command not found` | `python3 -m pip install -r requirements.txt` |
