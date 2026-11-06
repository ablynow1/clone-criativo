#!/usr/bin/env python3
"""Nota de validação de cada anúncio de IMAGEM das marcas escolhidas -> refs.json + refs/ + marcas_stats.json.

  python3 ranking.py [--por-marca 5] [--total 45] [--min-dias 14] [--carrossel] [--todos-destinos]

Entrada: ads.json (parse.py), marcas.json (as 10–15 escolhidas), alcance.json (opcional, biblioteca.py alcance).

NOTA (0–100) = o quanto o anúncio está provado, com os sinais que a Meta deixa ver:
  posição por impressões na listagem da própria marca  35   (1º lugar = 35; a Meta ordena por impressão)
  dias no ar (ainda ativo)                           25   (180+ dias = 25)
  variações (anúncios usando o mesmo criativo)       20   (32+ = 20)
  alcance real na UE (só anúncio veiculado na UE)    20   (2 mi+ = 20; sem dado, os outros 3 viram 100%)
  × peso da marca: 0,75 a 1,0 pelo nº de anúncios validados da marca (200+ = 1,0)
Faixas: 70+ "muito validado", 50–69 "validado", <50 "em teste". Fica fora: "<100" impressões, clique que não vai
pra loja (Instagram, WhatsApp, Facebook, vazio), catálogo (DPA) e vídeo (foco atual = imagem).
"""
import argparse, concurrent.futures as cf, json, math, os, sys, urllib.request
from collections import Counter, defaultdict

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adlib import url_marca   # noqa: E402

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/137 Safari/537.36"}


def baixa(url, dst):
    if os.path.exists(dst) and os.path.getsize(dst) > 3000:
        return True
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
            b = r.read()
        if len(b) < 3000:
            return False
        open(dst, "wb").write(b)
        Image.open(dst).verify()
        return True
    except Exception:
        try:
            os.remove(dst)
        except OSError:
            pass
        return False


def ahash(p):
    try:
        im = Image.open(p).convert("L").resize((9, 8))
        px = list(im.getdata())
        return sum(1 << i for i in range(64) if px[(i // 8) * 9 + i % 8] > px[(i // 8) * 9 + i % 8 + 1])
    except Exception:
        return None


def dist(a, b):
    return bin(a ^ b).count("1")


def proporcao(w, h):
    r = w / float(h or 1)
    if r >= 1.6:
        return "1.91:1"
    if r >= 1.15:
        return "horizontal"
    if r >= 0.92:
        return "1:1"
    if r >= 0.76:
        return "4:5"
    if r >= 0.62:
        return "2:3"
    return "9:16"


def nota(x, alc, total_marca):
    p_imp = 1 - (x["ordem_marca"] - 1) / float(max(x["n_marca"] or 1, 1))
    s_imp = 35 * max(0.0, p_imp)
    s_dias = 25 * min(x["dias"], 180) / 180.0
    s_var = 20 * min(math.log2(max(x["variacoes"], 1)) / 5.0, 1.0)
    if alc and alc.get("alcance"):
        s_ue = 20 * min(math.log10(alc["alcance"]) / 6.3, 1.0)
        base = s_imp + s_dias + s_var + s_ue
    else:
        s_ue = None
        base = (s_imp + s_dias + s_var) * 100 / 80.0
    f = 0.75 + 0.25 * min(math.log10(max(total_marca or 1, 1)) / 2.3, 1.0)
    return round(base * f, 1), dict(imp=round(s_imp, 1), dias=round(s_dias, 1), var=round(s_var, 1),
                                    ue=(round(s_ue, 1) if s_ue is not None else None), peso_marca=round(f, 2))


def nivel(n):
    return "muito validado" if n >= 70 else "validado" if n >= 50 else "em teste"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--por-marca", type=int, default=5)
    ap.add_argument("--total", type=int, default=45)
    ap.add_argument("--min-dias", type=int, default=14)
    ap.add_argument("--carrossel", action="store_true", help="carrossel entra (1º card)")
    ap.add_argument("--todos-destinos", action="store_true", help="não corta clique fora da loja")
    a = ap.parse_args()

    marcas = json.load(open("marcas.json"))
    sel = {m["page_id"]: m for m in marcas}
    alc = json.load(open("alcance.json")) if os.path.exists("alcance.json") else {}
    A = [x for x in json.load(open("ads.json")) if x["page_id"] in sel and x["ordem_marca"]]

    por = defaultdict(list)
    for x in A:
        por[x["page_id"]].append(x)

    stats, cands, fora = [], [], Counter()
    for pid, m in sel.items():
        L = por.get(pid, [])
        tot = max([x["total_marca"] or 0 for x in L] + [0]) or len(L)
        st = dict(page_id=pid, nome=m.get("nome") or (L[0]["marca"] if L else "?"), motivo=m.get("motivo", ""),
                  site=m.get("site", ""), validados=tot, coletados=len(L),
                  formatos=dict(Counter(x["fmt"] for x in L)),
                  dias_max=max([x["dias"] for x in L] + [0]),
                  alcance_max=max([(alc.get(x["id"]) or {}).get("alcance") or 0 for x in L] + [0]) or None,
                  dominio=(Counter(x["dominio"] for x in L if x["destino"] == "loja").most_common(1) or [("", 0)])[0][0],
                  pct_loja=round(100 * sum(1 for x in L if x["destino"] == "loja") / max(len(L), 1)),
                  biblioteca=url_marca(pid))
        stats.append(st)
        for x in L:
            ok_fmt = x["fmt"] == "imagem" or (a.carrossel and x["fmt"] == "carrossel")
            if not ok_fmt:
                fora[x["fmt"]] += 1
                continue
            if not x["imagens"]:
                fora["sem imagem"] += 1
                continue
            if not x["ativo"] or x["dias"] < a.min_dias:
                fora["menos de %d dias" % a.min_dias] += 1
                continue
            if x["imp_txt"] == "<100":
                fora["<100 impressões"] += 1
                continue
            if x["destino"] != "loja" and not a.todos_destinos:
                fora["clique pra " + x["destino"]] += 1
                continue
            n, partes = nota(x, alc.get(x["id"]), tot)
            y = dict(x)
            y.update(score=n, partes=partes, nivel=nivel(n), total_marca=tot,
                     alcance=(alc.get(x["id"]) or {}).get("alcance"),
                     pct_fem=(alc.get(x["id"]) or {}).get("pct_fem"),
                     idade_top=(alc.get(x["id"]) or {}).get("idade_top"))
            cands.append(y)

    # fila pro alcance real na UE (anúncios veiculados na UE ainda sem número)
    sem_alc = sorted([c for c in cands if c["ue"] and c["id"] not in alc], key=lambda c: -c["score"])
    json.dump([{k: c[k] for k in ("id", "page_id", "ue", "score")} for c in sem_alc], open("cands_ue.json", "w"), indent=1)

    # baixa a imagem principal (só dos que têm chance de entrar) e tira repetido visual
    cands.sort(key=lambda c: -c["score"])
    por_m = defaultdict(list)
    for c in cands:
        if len(por_m[c["page_id"]]) < a.por_marca * 3:
            por_m[c["page_id"]].append(c)
    pre = [c for L in por_m.values() for c in L]
    os.makedirs("refs/orig", exist_ok=True)
    with cf.ThreadPoolExecutor(12) as ex:
        list(ex.map(lambda c: baixa(c["imagens"][0], f"refs/orig/{c['id']}.jpg"), pre))

    vistos, escolhidos, cont = [], [], Counter()
    for c in sorted(pre, key=lambda c: -c["score"]):
        p = f"refs/orig/{c['id']}.jpg"
        if not os.path.exists(p):
            fora["imagem não baixou"] += 1
            continue
        h = ahash(p)
        if h is not None and any(dist(h, v) <= 5 for v in vistos):
            fora["repetida (mesma imagem)"] += 1
            continue
        if cont[c["page_id"]] >= a.por_marca:
            continue
        vistos.append(h)
        cont[c["page_id"]] += 1
        escolhidos.append(c)
    escolhidos = sorted(escolhidos, key=lambda c: -c["score"])[:a.total]

    refs = []
    for c in escolhidos:
        p = f"refs/orig/{c['id']}.jpg"
        im = Image.open(p).convert("RGB")
        w, h = im.size
        im.thumbnail((1080, 1920))
        im.save(f"refs/{c['id']}.jpg", quality=90)
        c.update(w=w, h=h, proporcao=proporcao(w, h), arquivo=f"refs/{c['id']}.jpg", url_imagem=c["imagens"][0])
        for k in ("fontes", "videos", "thumb", "collation_id", "inicio", "n_cards", "categorias_pagina"):
            c.pop(k, None)
        refs.append(c)
    json.dump(refs, open("refs.json", "w"), ensure_ascii=False, indent=1)

    tops = defaultdict(list)
    for r in refs:
        tops[r["page_id"]].append(r["id"])
    for st in stats:
        st["refs"] = tops.get(st["page_id"], [])
        st["imagens_validas"] = sum(1 for c in cands if c["page_id"] == st["page_id"])
    stats.sort(key=lambda s: -s["validados"])
    json.dump(stats, open("marcas_stats.json", "w"), ensure_ascii=False, indent=1)

    print(f"{len(cands)} imagens validadas nas {len(sel)} marcas → {len(refs)} referências em refs.json")
    print("faixas:", dict(Counter(r["nivel"] for r in refs)))
    print("ficaram fora:", dict(fora))
    for s in stats:
        print(f"  {s['nome'][:26]:<26} {s['validados']:>4} validados · {s['imagens_validas']:>3} imagens ok · "
              f"{len(s['refs'])} refs · até {s['dias_max']} dias" + (f" · alcance UE até {s['alcance_max']:,}".replace(",", ".") if s['alcance_max'] else ""))
    if sem_alc:
        print(f"→ {len(sem_alc)} imagens rodam na UE e ainda não têm alcance: "
              f"python3 biblioteca.py alcance --ads cands_ue.json  e depois rode ranking.py de novo")


if __name__ == "__main__":
    main()
