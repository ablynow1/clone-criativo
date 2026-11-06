#!/usr/bin/env python3
"""ads.json (buscas por termo) -> candidatos.json + pranchas analise/candidatos_N.jpg pra escolher as 10–15 marcas.

  python3 anunciantes.py [--top 40] [--min-dias 14] [--ruim "regex de anunciante fora do tema"]

Agrupa por anunciante (page_id) o que veio nas BUSCAS (bu_*): quantos anúncios validados apareceram, melhor posição
por impressão, maior tempo no ar, variações, domínio da loja e % de clique indo pra loja. A escolha final das marcas
é minha (relevância pro produto do cliente), olhando a prancha; esse script só ordena e mostra.
"""
import argparse, concurrent.futures as cf, json, os, re, sys, urllib.request
from collections import Counter, defaultdict

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adlib import url_marca   # noqa: E402

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/137 Safari/537.36"}


def baixa(url, dst):
    if os.path.exists(dst) and os.path.getsize(dst) > 1500:
        return True
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            b = r.read()
        if len(b) < 1500:
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


def fonte(t):
    for p in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
              "C:/Windows/Fonts/arialbd.ttf", "DejaVuSans-Bold.ttf", "Arial Bold.ttf"):
        try:
            return ImageFont.truetype(p, t)
        except Exception:
            pass
    try:
        return ImageFont.load_default(size=t)
    except TypeError:
        return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--min-dias", type=int, default=14)
    ap.add_argument("--ruim", default="")
    a = ap.parse_args()
    ruim = re.compile(a.ruim, re.I) if a.ruim else None

    A = [x for x in json.load(open("ads.json")) if any(f.startswith("bu_") for f in x["fontes"])]
    por = defaultdict(list)
    for x in A:
        if x["ativo"] and x["dias"] >= a.min_dias and x["page_id"]:
            por[x["page_id"]].append(x)

    cands = []
    for pid, L in por.items():
        marca = Counter(x["marca"] for x in L).most_common(1)[0][0]
        if ruim and ruim.search(marca):
            continue
        dest = Counter(x["destino"] for x in L)
        loja = dest.get("loja", 0) / len(L)
        doms = Counter(x["dominio"] for x in L if x["dominio"])
        ordem = min((x["ordem_busca"] or 999) for x in L)
        dias_max = max(x["dias"] for x in L)
        var = sum(x["variacoes"] for x in L)
        termos = sorted({re.sub(r"_\d+d(_ex)?$", "", f.split("_", 2)[2]).replace("_", " ")
                         for x in L for f in x["fontes"] if f.startswith("bu_")})
        score = (len(L) * 2 + min(var, 60) / 3 + min(dias_max, 365) / 30
                 + (10 if ordem <= 5 else 5 if ordem <= 15 else 0))
        score *= 0.15 if loja < 0.3 else (0.5 + 0.5 * loja)
        L.sort(key=lambda x: x["ordem_busca"] or 999)
        cands.append(dict(
            page_id=pid, marca=marca, score=round(score, 1), n=len(L), melhor_ordem=ordem, dias_max=dias_max,
            destino_principal=dest.most_common(1)[0][0],
            variacoes=var, pct_loja=round(100 * loja), dominio=(doms.most_common(1)[0][0] if doms else ""),
            formatos=dict(Counter(x["fmt"] for x in L)), termos=termos[:6],
            seguidores=max(x["seguidores"] for x in L),
            amostra=[(x["headline"] or x["copy"][:90]).replace("\n", " ")[:110] for x in L[:3]],
            thumbs=[[x["id"], x["thumb"]] for x in L if x["thumb"]][:3],
            biblioteca=url_marca(pid)))
    cands.sort(key=lambda c: -c["score"])
    json.dump(cands, open("candidatos.json", "w"), ensure_ascii=False, indent=1)

    top = cands[:a.top]
    os.makedirs("busca/thumbs", exist_ok=True)
    tarefas = [(u, f"busca/thumbs/{i}.jpg") for c in top for i, u in c["thumbs"]]
    with cf.ThreadPoolExecutor(12) as ex:
        list(ex.map(lambda t: baixa(*t), tarefas))

    # prancha: 8 marcas por imagem, 1 linha por marca (rótulo + até 3 miniaturas)
    os.makedirs("analise", exist_ok=True)
    F, F2 = fonte(22), fonte(17)
    H, W = 230, 1500
    for k in range(0, len(top), 8):
        grupo = top[k:k + 8]
        img = Image.new("RGB", (W, len(grupo) * (H + 12)), (255, 255, 255))
        d = ImageDraw.Draw(img)
        for j, c in enumerate(grupo):
            y = j * (H + 12)
            n = k + j + 1
            d.text((10, y + 8), f"#{n} {c['marca'][:30]}", fill=(200, 0, 0), font=F)
            d.text((10, y + 40), (f"[{c['destino_principal']}] " if c['destino_principal'] != 'loja' else '') + f"{c['dominio'][:34]}",
                   fill=(200, 0, 0) if c['destino_principal'] != 'loja' else (30, 30, 30), font=F2)
            d.text((10, y + 66), f"{c['n']} anúncios validados", fill=(30, 30, 30), font=F2)
            d.text((10, y + 90), f"até {c['dias_max']} dias · {c['variacoes']} var.", fill=(30, 30, 30), font=F2)
            d.text((10, y + 114), f"loja {c['pct_loja']}% · melhor #{c['melhor_ordem']}", fill=(30, 30, 30), font=F2)
            d.text((10, y + 138), ", ".join(f"{f} {q}" for f, q in c["formatos"].items())[:40], fill=(90, 90, 90), font=F2)
            x = 420
            for i, _ in c["thumbs"]:
                p = f"busca/thumbs/{i}.jpg"
                if not os.path.exists(p):
                    continue
                try:
                    im = Image.open(p).convert("RGB")
                except Exception:
                    continue
                im.thumbnail((340, H))
                img.paste(im, (x, y))
                x += im.width + 10
            d.line([(0, y + H + 6), (W, y + H + 6)], fill=(220, 220, 220), width=2)
        img.save(f"analise/candidatos_{k // 8 + 1}.jpg", quality=80)

    print(f"{len(cands)} anunciantes com anúncio validado nas buscas → candidatos.json")
    for n, c in enumerate(top, 1):
        tag = "" if c["destino_principal"] == "loja" else f" [{c['destino_principal']}]"
        print(f"{n:>2}. {(c['marca'][:26] + tag)[:28]:<28} {c['dominio'][:26]:<26} n={c['n']:<3} dias≤{c['dias_max']:<4} "
              f"var={c['variacoes']:<4} loja={c['pct_loja']}% #{c['melhor_ordem']} · {', '.join(c['termos'][:2])}")
    print(f"pranchas: analise/candidatos_1..{(len(top) + 7) // 8}.jpg")


if __name__ == "__main__":
    main()
