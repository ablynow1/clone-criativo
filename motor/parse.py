#!/usr/bin/env python3
"""Dumps da Biblioteca -> ads.json (rode na pasta do projeto).

Lê busca/*.html (bu_ = busca por termo) e dumps/*.html (pg_ = página da marca). Cada anúncio guarda:
  ordem_marca  posição na listagem da PRÓPRIA marca, ordenada por impressões (1 = mais impressão)  ← sinal principal
  n_marca      quantos anúncios a listagem da marca trouxe (pra virar percentil)
  total_marca  contador da listagem da marca (anúncios ativos e no ar há N+ dias = validados)
  ordem_busca  melhor posição nas buscas por termo
  fontes       de quais dumps veio
"""
import json, os, sys, time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adlib import extrai_ads, normaliza, total   # noqa: E402

agora = int(time.time())
ads = {}
for pasta in ("busca", "dumps"):
    if not os.path.isdir(pasta):
        continue
    for f in sorted(os.listdir(pasta)):
        if not f.endswith(".html"):
            continue
        h = open(os.path.join(pasta, f), errors="ignore").read()
        lista = extrai_ads(h)
        tot = total(h)
        fonte = f[:-5]
        de_pagina = f.startswith("pg_")
        for i, b in enumerate(lista):
            a = normaliza(b, agora)
            x = ads.get(a["id"])
            if x is None:
                x = a
                x.update(fontes=[], ordem_marca=None, n_marca=None, total_marca=None, ordem_busca=None)
                ads[a["id"]] = x
            x["fontes"].append(fonte)
            if de_pagina:
                if x["ordem_marca"] is None or i + 1 < x["ordem_marca"]:
                    x.update(ordem_marca=i + 1, n_marca=len(lista), total_marca=tot)
            else:
                if x["ordem_busca"] is None or i + 1 < x["ordem_busca"]:
                    x["ordem_busca"] = i + 1

json.dump(list(ads.values()), open("ads.json", "w"), ensure_ascii=False, indent=1)
fm = Counter(a["fmt"] for a in ads.values())
mc = Counter(a["marca"] for a in ads.values())
print(f"{len(ads)} anúncios · {len(mc)} anunciantes · formatos {dict(fm)}")
print("mais anúncios:", ", ".join(f"{m} ({n})" for m, n in mc.most_common(15)))
