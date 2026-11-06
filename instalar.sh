#!/bin/bash
# Instala o que o Clone Criativo precisa e confere a máquina.  Uso: bash instalar.sh
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo "✗ falta o Python 3 — veja INSTALACAO.md"; exit 1; }
echo "→ instalando Pillow e websockets"
python3 -m pip install --user -q -r requirements.txt 2>/dev/null \
  || python3 -m pip install -q -r requirements.txt 2>/dev/null \
  || python3 -m pip install --user --break-system-packages -q -r requirements.txt \
  || { echo "✗ não consegui instalar — rode: python3 -m pip install -r requirements.txt"; exit 1; }
[ -f .env ] || { cp .env.exemplo .env && echo "→ criei o .env (padrão: Magnific pelo conector, página local)"; }
chmod +x motor/publica.sh
echo
python3 motor/verifica.py
echo
echo "Próximo passo: abra o Claude Code aqui dentro (claude) — ele explica o projeto e te ajuda com o que faltar."
