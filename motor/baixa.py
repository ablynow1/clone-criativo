#!/usr/bin/env python3
"""Baixa resultados do Magnific (os links expiram em ~30 min: baixar assim que ficarem prontos).

  python3 baixa.py <url> <destino_sem_extensao> [<url> <destino> ...]

A extensão sai do conteúdo (png/jpg/webp). Imprime o caminho final e o tamanho em pixels de cada um.
"""
import io, os, sys, urllib.request

from PIL import Image

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/137 Safari/537.36"}
a = sys.argv[1:]
if not a or len(a) % 2:
    sys.exit("uso: python3 baixa.py <url> <destino_sem_extensao> [...]")
erro = 0
for url, dst in zip(a[::2], a[1::2]):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
            b = r.read()
        im = Image.open(io.BytesIO(b))
        ext = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}.get(im.format, ".png")
        os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
        open(dst + ext, "wb").write(b)
        print(f"✔ {dst + ext} · {im.size[0]}x{im.size[1]}")
    except Exception as e:
        erro += 1
        print(f"✗ {dst}: {str(e)[:120]}")
sys.exit(1 if erro else 0)
