#!/usr/bin/env python3
"""Puxa os votos e ajustes da página -> votos.json e mostra por lote (rode na pasta do projeto).

  python3 votos.py           # página publicada (config.json → url) ou, sem url, os votos locais (pub/dados/votos.jsonl)
  python3 votos.py --local   # força ler os votos locais

Algumas hospedagens (HostGator e parecidas) recusam pedido sem cara de navegador (406): por isso vai pelo curl com
User-Agent de navegador.
"""
import glob, json, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from servidor import estado   # noqa: E402

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137 Safari/537.36"
cfg = json.load(open("config.json"))
if cfg.get("url") and "--local" not in sys.argv:
    url = cfg["url"].rstrip("/") + "/voto.php?estado=1"
    r = subprocess.run(["curl", "-s", "-A", UA, "--max-time", "30", url], capture_output=True, text=True)
    try:
        V = json.loads(r.stdout)["votos"]
    except Exception:
        sys.exit("✗ não consegui ler os votos: " + (r.stdout or r.stderr)[:200])
else:
    V = estado("pub/dados/votos.jsonl")
json.dump(V, open("votos.json", "w"), ensure_ascii=False, indent=1)

marca = {1: "✓", -1: "✕", 0: "·"}
tot = {1: 0, -1: 0, 0: 0}
for p in sorted(glob.glob("lotes/lote*/lote.json"), key=lambda s: int("".join(ch for ch in s.split("/")[1] if ch.isdigit()) or 0)):
    l = json.load(open(p))
    print(f"Lote {l.get('n')}:")
    for c in l.get("criativos", []):
        v, _, com = (V.get(c["id"]) or [0, 0, ""])
        tot[v] = tot.get(v, 0) + 1
        print(f"  {marca.get(v, '?')} {c['id']} · {c.get('padrao', '')[:38]} · {c.get('headline', '')[:48]}")
        if com:
            print(f"      ajuste: {com}")
of = (V.get("oferta") or [0, 0, ""])[2]
if of:
    print("Correção da oferta:", of)
print(f"total: {tot[1]} aprovados · {tot[-1]} reprovados · {tot[0]} sem voto")
