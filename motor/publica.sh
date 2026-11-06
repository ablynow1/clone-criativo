#!/bin/bash
# Sobe a página de aprovação (pub/) pra SUA hospedagem por FTP. Opcional: sem hospedagem, use o servidor.py.
#   cd projetos/<produto> && bash ../../motor/publica.sh
# Precisa no .env da raiz: SITE_BASE, FTP_HOST, FTP_USER, FTP_PASS (e FTP_PASTA, a pasta pública no servidor; padrão /public_html)
# A hospedagem precisa ter PHP (o voto.php grava os votos). Não apaga nada lá e não sobe os votos (*.jsonl).
set -e
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
[ -f config.json ] || { echo "✗ rode dentro da pasta do projeto (projetos/<produto>)"; exit 1; }
[ -f pub/index.html ] || { echo "✗ falta pub/index.html — rode: python3 $RAIZ/motor/pagina.py"; exit 1; }
[ -f "$RAIZ/.env" ] || { echo "✗ falta $RAIZ/.env (copie o .env.exemplo)"; exit 1; }
set -a; source "$RAIZ/.env"; set +a
for v in SITE_BASE FTP_HOST FTP_USER FTP_PASS; do [ -n "${!v}" ] || { echo "✗ falta $v no .env"; exit 1; }; done
command -v lftp >/dev/null || { echo "✗ falta o lftp (Mac: brew install lftp · Linux: sudo apt install lftp)"; exit 1; }
PRODUTO="$(python3 -c 'import json;print(json.load(open("config.json"))["produto"])')"
REMOTO="${FTP_PASTA:-/public_html}/$PRODUTO"
LFTP_PASSWORD="$FTP_PASS" lftp --env-password -u "$FTP_USER" "$FTP_HOST" <<FTPEOF
set ssl:verify-certificate no
set net:timeout 60
set net:max-retries 4
set mirror:parallel-transfer-count 4
mkdir -p -f $REMOTO
mirror -R --only-newer --verbose=1 --exclude-glob .DS_Store --exclude-glob '*.jsonl' pub "$REMOTO"
quit
FTPEOF
echo "✔ ${SITE_BASE%/}/$PRODUTO/"
