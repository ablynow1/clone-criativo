#!/usr/bin/env python3
"""Monta a página de aprovação em pub/ (rode na pasta do projeto).
Depois: python3 <motor>/servidor.py (abre no seu computador) ou bash <motor>/publica.sh (sobe pra sua hospedagem).

  python3 pagina.py

Lê:  config.json · oferta.json · marcas_stats.json · refs.json · analise/leitura/<id>.json · padroes.json
     lotes/lote<N>/lote.json (criativos de cada lote) · lp/dobra_mobile.jpg
Grava: pub/index.html · pub/voto.php · pub/ids.json · pub/c/<id>.jpg (tela) · pub/full/<id>.* (alta, pra baixar)
       pub/r/<id>.jpg (referências — também servem de URL pública pro Magnific) · pub/lp/dobra.jpg
Arquivo faltando não derruba: avisa e segue.
"""
import glob, json, os, shutil, sys, time

from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(AQUI, "assets")


def le(p, padrao):
    try:
        return json.load(open(p))
    except Exception:
        return padrao


def reduz(src, dst, largura, q=86):
    im = Image.open(src)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        f = Image.new("RGB", im.size, (255, 255, 255))
        f.paste(im, mask=im.split()[-1])
        im = f
    im = im.convert("RGB")
    if im.width > largura:
        im = im.resize((largura, round(im.height * largura / im.width)), Image.LANCZOS)
    im.save(dst, quality=q, optimize=True)


def main():
    cfg = le("config.json", None)
    if not cfg:
        sys.exit("✗ falta config.json — rode na pasta do projeto (criada pelo novo.py)")
    for d in ("pub/c", "pub/full", "pub/r", "pub/lp", "pub/dados"):
        os.makedirs(d, exist_ok=True)
    avisos = []

    refs_in = le("refs.json", [])
    refs = []
    for r in refs_in:
        src = r.get("arquivo") or f"refs/{r['id']}.jpg"
        if not os.path.exists(src):
            avisos.append(f"referência sem imagem: {r['id']}")
            continue
        dst = f"pub/r/{r['id']}.jpg"
        if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
            reduz(src, dst, 1080, 88)
        x = {k: r.get(k) for k in ("id", "marca", "page_id", "score", "nivel", "dias", "variacoes", "ordem_marca",
                                    "n_marca", "alcance", "pct_fem", "idade_top", "biblioteca", "link", "proporcao", "headline")}
        x["img"] = f"r/{r['id']}.jpg"
        x["leitura"] = le(f"analise/leitura/{r['id']}.json", {})
        refs.append(x)
    sem_leitura = [r["id"] for r in refs if not r["leitura"]]

    lotes = []
    for p in sorted(glob.glob("lotes/lote*/lote.json"), key=lambda s: int("".join(ch for ch in s.split("/")[1] if ch.isdigit()) or 0)):
        l = le(p, None)
        if not l:
            avisos.append(f"{p} ilegível")
            continue
        cs = []
        for c in l.get("criativos", []):
            src = c.get("arquivo", "")
            if not src or not os.path.exists(src):
                avisos.append(f"criativo {c.get('id')} sem arquivo ({src})")
                continue
            ext = os.path.splitext(src)[1].lower() or ".png"
            tela, alta = f"pub/c/{c['id']}.jpg", f"pub/full/{c['id']}{ext}"
            reduz(src, tela, 1080, 88)       # sempre refaz: a variação escolhida pode ter mudado
            shutil.copyfile(src, alta)
            c2 = dict(c)
            v = int(time.time())   # quebra o cache do celular quando a imagem muda
            c2.update(img=f"c/{c['id']}.jpg?v={v}", full=f"full/{c['id']}{ext}?v={v}")
            for k in ("prompt", "magnific", "arquivo", "alternativas"):
                c2.pop(k, None)
            cs.append(c2)
        if cs:
            lotes.append(dict(n=l.get("n"), data=l.get("data", ""), nota=l.get("nota", ""), criativos=cs))

    lp = {}
    if os.path.exists("lp/dobra_mobile.jpg"):
        reduz("lp/dobra_mobile.jpg", "pub/lp/dobra.jpg", 600, 82)
        lp["dobra"] = "lp/dobra.jpg"

    dados = dict(
        config=dict(titulo=cfg.get("titulo", "Criativos validados"), cliente=cfg.get("cliente"), produto=cfg.get("produto"),
                    lp=cfg.get("lp"), gerado=time.strftime("%d/%m/%Y %H:%M"), dias=cfg.get("dias_validado", 14)),
        metodo=cfg.get("metodo") or [
            f"Validado = continua no ar há {cfg.get('dias_validado', 14)}+ dias e a Meta ainda entrega. Mais tempo, mais "
            "variações e mais alto na ordem por impressões = nota maior.",
            "A Meta não mostra impressão de anúncio que roda só no Brasil. Quando ele roda também na Europa, ela mostra o "
            "alcance real (em azul).",
            "Só entra imagem cujo clique vai pra loja (nada de Instagram ou WhatsApp).",
        ],
        oferta=le("oferta.json", {}), marcas=le("marcas_stats.json", []), refs=refs,
        padroes=le("padroes.json", []), lotes=lotes, lp=lp)

    html = open(os.path.join(ASSETS, "template.html"), encoding="utf-8").read()
    js = json.dumps(dados, ensure_ascii=False).replace("</", "<\\/")
    html = html.replace("__TITULO__", (cfg.get("titulo") or "Criativos validados").replace("<", "")).replace("__DADOS__", js)
    open("pub/index.html", "w", encoding="utf-8").write(html)
    shutil.copyfile(os.path.join(ASSETS, "voto.php"), "pub/voto.php")
    open("pub/dados/.htaccess", "w").write("<IfModule mod_authz_core.c>\nRequire all denied\n</IfModule>\n"
                                           "<IfModule !mod_authz_core.c>\nDeny from all\n</IfModule>\n")
    ids = [c["id"] for l in lotes for c in l["criativos"]] + ["oferta"]
    json.dump(ids, open("pub/ids.json", "w"))

    tam = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk("pub") for f in fs) / 1e6
    print(f"✔ pub/ montado · {len(refs)} referências ({len(refs) - len(sem_leitura)} com leitura) · "
          f"{len(dados['padroes'])} padrões · {len(lotes)} lotes / {len(ids) - 1} criativos · {tam:.1f} MB")
    if sem_leitura:
        print(f"  {len(sem_leitura)} referências ainda sem leitura de design")
    for a in avisos:
        print("  ⚠", a)
    print(f"  ver no computador: python3 {AQUI}/servidor.py   → http://localhost:8765/")
    if cfg.get("url"):
        print(f"  publicar: bash {AQUI}/publica.sh   → {cfg.get('url')}")


if __name__ == "__main__":
    main()
