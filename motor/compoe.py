#!/usr/bin/env python3
"""Cola uma imagem REAL (foto de pessoa, logo, foto do produto) em cima do criativo gerado, sem passar por IA.

  python3 compoe.py <base> <saida> --foto <arquivo> --caixa x,y,l,a [--raio 0.04] [--borda "#DDB45F"] [--borda-px 6]
                    [--ancora topo|centro|base] [--conter] [--sombra]

--caixa em FRAÇÕES da base (0–1): x,y = canto de cima à esquerda, l,a = largura e altura. Ex.: 0.55,0.30,0.40,0.50
--ancora: onde cortar quando a foto não tem a proporção da caixa (retrato: "topo" pra não cortar o rosto).
--conter: encaixa a foto inteira (sem cortar) — use pra logo e PNG com transparência.
Uso típico: a IA gera a peça com um espaço reservado (cartão/moldura vazia) e aqui entra a foto real por cima.
Use sempre que o rosto de uma pessoa REAL (dono, sócio, especialista) entrar no criativo: IA pode desenhar o rosto diferente.
"""
import argparse

from PIL import Image, ImageDraw, ImageFilter


def cor(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("saida")
    ap.add_argument("--foto", required=True)
    ap.add_argument("--caixa", required=True)
    ap.add_argument("--raio", type=float, default=0.0, help="raio do canto, fração da largura da caixa")
    ap.add_argument("--borda", default="")
    ap.add_argument("--borda-px", type=int, default=0)
    ap.add_argument("--ancora", default="centro", choices=["topo", "centro", "base"])
    ap.add_argument("--conter", action="store_true")
    ap.add_argument("--sombra", action="store_true")
    a = ap.parse_args()

    base = Image.open(a.base).convert("RGBA")
    W, H = base.size
    x, y, l, h = [float(v) for v in a.caixa.split(",")]
    bx, by, bw, bh = round(x * W), round(y * H), round(l * W), round(h * H)
    foto = Image.open(a.foto).convert("RGBA")

    if a.conter:
        foto.thumbnail((bw, bh), Image.LANCZOS)
        cam = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        cam.paste(foto, ((bw - foto.width) // 2, (bh - foto.height) // 2), foto)
        foto = cam
    else:   # cobre a caixa (como object-fit: cover)
        esc = max(bw / foto.width, bh / foto.height)
        foto = foto.resize((max(bw, round(foto.width * esc)), max(bh, round(foto.height * esc))), Image.LANCZOS)
        ox = (foto.width - bw) // 2
        oy = {"topo": 0, "centro": (foto.height - bh) // 2, "base": foto.height - bh}[a.ancora]
        foto = foto.crop((ox, oy, ox + bw, oy + bh))

    mask = Image.new("L", (bw, bh), 0)
    r = round(a.raio * bw)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, bw - 1, bh - 1], radius=r, fill=255)
    if a.conter:
        mask = Image.composite(foto.split()[-1], Image.new("L", (bw, bh), 0), mask)

    if a.sombra:
        s = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(s).rounded_rectangle([bx + 8, by + 14, bx + bw + 8, by + bh + 14], radius=r, fill=(0, 0, 0, 140))
        base = Image.alpha_composite(base, s.filter(ImageFilter.GaussianBlur(18)))
    base.paste(foto, (bx, by), mask)
    if a.borda and a.borda_px:
        d = ImageDraw.Draw(base)
        d.rounded_rectangle([bx, by, bx + bw - 1, by + bh - 1], radius=r, outline=cor(a.borda), width=a.borda_px)
    out = base.convert("RGB") if a.saida.lower().endswith((".jpg", ".jpeg")) else base
    out.save(a.saida, quality=95)
    print(f"✔ {a.saida} · foto em {bx},{by} {bw}x{bh}")


if __name__ == "__main__":
    main()
