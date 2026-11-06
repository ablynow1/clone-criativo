#!/usr/bin/env python3
"""refs.json -> analise/pranchas/r###.jpg (4 referências por prancha, 2x2, ~700 px cada, dá pra ler o texto do anúncio)
+ analise/lotes_leitura/<n>.json (lote pra quem for fazer a leitura de design: pranchas + ids + onde gravar).

  python3 pranchas.py [--por-lote 12]
Rótulo de cada quadro: #n · id · marca · nota.  A leitura de cada id vai em analise/leitura/<id>.json
(esquema em references/leitura-design.md).
"""
import argparse, json, os

from PIL import Image, ImageDraw, ImageFont


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
    ap.add_argument("--por-lote", type=int, default=12, help="referências por leitor (subagente)")
    a = ap.parse_args()
    R = json.load(open("refs.json"))
    B = os.getcwd()
    for d in ("analise/pranchas", "analise/lotes_leitura", "analise/leitura"):
        os.makedirs(d, exist_ok=True)
    F = fonte(24)
    CW, CH, POR = 700, 820, 4
    pr = []
    for k in range(0, len(R), POR):
        g = R[k:k + POR]
        img = Image.new("RGB", (2 * CW + 12, 2 * (CH + 40)), (255, 255, 255))
        d = ImageDraw.Draw(img)
        for j, r in enumerate(g):
            x, y = (j % 2) * (CW + 12), (j // 2) * (CH + 40)
            t = f"#{k + j + 1} · {r['id']} · {r['marca'][:22]} · nota {r['score']:.0f}"
            d.rectangle([x, y, x + CW, y + 36], fill=(0, 0, 0))
            d.text((x + 8, y + 5), t, fill=(255, 80, 80), font=F)
            im = Image.open(r["arquivo"]).convert("RGB")
            im.thumbnail((CW, CH))
            img.paste(im, (x + (CW - im.width) // 2, y + 40))
        p = f"analise/pranchas/r{k // POR + 1:03d}.jpg"
        img.save(p, quality=85)
        pr.append((p, [r["id"] for r in g]))
    n = 0
    por_pr = max(1, a.por_lote // POR)
    for k in range(0, len(pr), por_pr):
        n += 1
        parte = pr[k:k + por_pr]
        json.dump(dict(pranchas=[f"{B}/{p}" for p, _ in parte], ids=[i for _, ids in parte for i in ids],
                       saida_dir=f"{B}/analise/leitura"), open(f"analise/lotes_leitura/{n}.json", "w"), indent=1)
    print(f"{len(R)} referências · {len(pr)} pranchas em analise/pranchas · {n} lotes de leitura")


if __name__ == "__main__":
    main()
