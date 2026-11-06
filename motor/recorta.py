#!/usr/bin/env python3
"""Recorta pedaços da LP em alta (mockups, telas de app, cartões de bônus, fotos do time) -> lp/img/<nome>.png

  python3 recorta.py "<url>" "nome1=texto que aparece no bloco;nome2=outro texto" [--celular] [--min 300x200]

Pra INFOPRODUTO: a "foto do produto" é o mockup desenhado na LP (tela da aula, app, capas). Cada alvo acha o MENOR
bloco da página que contém o texto e tem pelo menos --min (largura x altura em px CSS), e salva em 2x (3x no celular).
--celular: usa a versão de celular da página (bloco em coluna, bom pra colar na tela de um celular no criativo).
Ex.: python3 recorta.py "https://site/lp" "mock_curso=PROGRESSO;mock_fabrica=VOCÊ ESCOLHE" --min 380x260
"""
import argparse, asyncio, base64, json, os, sys

os.environ.setdefault("CDP_PORTA", "9385")
os.environ.setdefault("CDP_PERFIL", "/tmp/validados-recorte-cdp")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Sessao, UA_IPHONE, UA_MAC   # noqa: E402

JS = r"""((txt, mw, mh) => {
  const els = [...document.querySelectorAll('body *')].filter(e => e.children.length < 80 && (e.innerText || '').includes(txt));
  els.sort((a, b) => a.getBoundingClientRect().width * a.getBoundingClientRect().height - b.getBoundingClientRect().width * b.getBoundingClientRect().height);
  for (const e of els) { const r = e.getBoundingClientRect(); if (r.width >= mw && r.height >= mh) return {x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height}; }
  return null;
})(%s, %d, %d)"""


async def main(a):
    alvos = [p.split("=", 1) for p in a.alvos.split(";") if "=" in p]
    mw, mh = [int(v) for v in a.min.lower().split("x")]
    os.makedirs("lp/img", exist_ok=True)
    async with Sessao(UA_IPHONE if a.celular else UA_MAC) as aba:
        if a.celular:
            await aba.cmd("Emulation.setDeviceMetricsOverride", width=390, height=844, deviceScaleFactor=3, mobile=True)
        else:
            await aba.cmd("Emulation.setDeviceMetricsOverride", width=1440, height=900, deviceScaleFactor=2, mobile=False)
        await aba.vai(a.url, 6)
        await aba.js("document.documentElement.style.setProperty('scroll-behavior','auto','important')")
        await aba.js("(async()=>{for(let y=0;y<document.documentElement.scrollHeight;y+=400){scrollTo({top:y,behavior:'instant'});"
                     "await new Promise(r=>setTimeout(r,150))}scrollTo({top:0,behavior:'instant'})})()")
        await asyncio.sleep(1.5)
        for nome, txt in alvos:
            r = await aba.js(JS % (json.dumps(txt.strip()), mw, mh))
            if not r:
                print("✗", nome, "não achei bloco com", repr(txt))
                continue
            pad = 0 if a.celular else 16
            shot = await aba.cmd("Page.captureScreenshot", format="png", captureBeyondViewport=True,
                                 clip={"x": max(0, r["x"] - pad), "y": max(0, r["y"] - pad),
                                       "width": r["w"] + 2 * pad, "height": r["h"] + 2 * pad, "scale": 1})
            arq = f"lp/img/{nome.strip()}.png"
            open(arq, "wb").write(base64.b64decode(shot["data"]))
            print("✔", arq, f"{int(r['w'])}x{int(r['h'])} (CSS)")
    print("Atenção: barra fixa da página (topo/rodapé) pode aparecer no recorte do celular — conferir e cortar.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("alvos")
    ap.add_argument("--celular", action="store_true")
    ap.add_argument("--min", default="300x200")
    asyncio.run(main(ap.parse_args()))
