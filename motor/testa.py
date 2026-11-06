#!/usr/bin/env python3
"""Testa a página como o usuário usa (celular, Chrome headless). Rode na pasta do projeto.

  python3 testa.py            # testa a página publicada (config.json → url); sem url publicada, testa local
  python3 testa.py --local    # sobe pub/ no servidor.py (127.0.0.1:8799) e testa ali (votos de teste somem no fim)
  python3 testa.py --sem-voto # não testa o voto (o teste de voto aprova e desfaz o 1º criativo)

Confere: erro de JavaScript, nº de cards = nº de criativos, imagens carregando, as 4 abas com conteúdo, voto indo e
voltando no voto.php. Grava prints em analise/teste_<aba>.png pra eu olhar.
"""
import asyncio, base64, json, os, subprocess, sys, time

os.environ.setdefault("CDP_PORTA", "9384")
os.environ.setdefault("CDP_PERFIL", "/tmp/clone-criativo-teste-cdp")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp   # noqa: E402

LOCAL = "--local" in sys.argv
AQUI = os.path.dirname(os.path.abspath(__file__))
SEM_VOTO = "--sem-voto" in sys.argv


class AbaTeste(cdp.Aba):
    def __init__(self, ws):
        super().__init__(ws)
        self.erros = []

    async def cmd(self, metodo, **params):
        self.i += 1
        meu = self.i
        await self.ws.send(json.dumps({"id": meu, "method": metodo, "params": params}))
        while True:
            msg = json.loads(await self.ws.recv())
            m = msg.get("method")
            if m == "Runtime.exceptionThrown":
                d = msg["params"]["exceptionDetails"]
                self.erros.append((d.get("exception") or {}).get("description") or d.get("text"))
            elif m == "Runtime.consoleAPICalled" and msg["params"].get("type") == "error":
                self.erros.append(" ".join(str(a.get("value", a.get("description", ""))) for a in msg["params"].get("args", [])))
            if msg.get("id") == meu:
                if "error" in msg:
                    raise RuntimeError(f"{metodo}: {msg['error']}")
                return msg.get("result", {})


async def main():
    cfg = json.load(open("config.json"))
    ids = json.load(open("pub/ids.json"))
    n_cri = len([i for i in ids if i != "oferta"])
    srv = None
    local = LOCAL or not cfg.get("url")
    if local:
        if os.path.exists("pub/dados/votos.jsonl"):
            os.rename("pub/dados/votos.jsonl", "pub/dados/votos.jsonl.antes")
        srv = subprocess.Popen([sys.executable, os.path.join(AQUI, "servidor.py"), "--porta", "8799"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.5)
        url = "http://127.0.0.1:8799/"
    else:
        url = cfg["url"]
    ok = True

    def res(cond, txt):
        nonlocal ok
        ok = ok and cond
        print(("✔ " if cond else "✗ ") + txt, flush=True)

    proc = cdp.sobe_chrome(cdp.UA_IPHONE)
    try:
        import websockets
        async with websockets.connect(cdp._ws_url(), max_size=100 * 1024 * 1024, ping_interval=None) as ws:
            aba = AbaTeste(ws)
            for d in ("Page", "Runtime", "Network"):
                await aba.cmd(d + ".enable")
            await aba.cmd("Network.setCacheDisabled", cacheDisabled=True)
            await aba.cmd("Emulation.setDeviceMetricsOverride", width=390, height=844, deviceScaleFactor=2, mobile=True)
            await aba.vai(url + "#lotes", 4)
            t = await aba.js("document.title")
            res(bool(t), f"abriu: {t}")
            n = await aba.js("document.querySelectorAll('#lotes .cri').length")
            res(n == n_cri, f"cards de criativo: {n} (esperado {n_cri})")
            # rola a página pra carregar as imagens preguiçosas e confere
            await aba.js("(async()=>{for(let y=0;y<document.body.scrollHeight;y+=700){scrollTo(0,y);await new Promise(r=>setTimeout(r,120))}scrollTo(0,0)})()")
            await asyncio.sleep(1.5)
            ruins = await aba.js("[...document.querySelectorAll('#lotes img')].filter(i=>i.complete&&!i.naturalWidth).map(i=>i.src)")
            res(not ruins, f"imagens dos lotes carregando ({len(ruins or [])} quebradas)" + (f": {ruins[:3]}" if ruins else ""))
            shot = await aba.cmd("Page.captureScreenshot", format="png")
            os.makedirs("analise", exist_ok=True)
            open("analise/teste_lotes.png", "wb").write(base64.b64decode(shot["data"]))
            for a in ("validados", "padroes", "oferta"):
                await aba.js(f"document.querySelector('nav.abas button[data-aba={a}]').click()")
                await asyncio.sleep(0.8)
                tam = await aba.js(f"document.getElementById('{a}').innerText.length")
                res(tam > 40, f"aba {a}: {tam} caracteres")
                shot = await aba.cmd("Page.captureScreenshot", format="png")
                open(f"analise/teste_{a}.png", "wb").write(base64.b64decode(shot["data"]))
            if not SEM_VOTO and n:
                await aba.js("document.querySelector('nav.abas button[data-aba=lotes]').click()")
                await asyncio.sleep(0.5)
                cid = await aba.js("document.querySelector('#lotes button.sim').getAttribute('data-id')")
                antes = await aba.js("fetch('voto.php?estado=1',{cache:'no-store'}).then(r=>r.json()).then(j=>(j.votos['%s']||[0])[0])" % cid)
                if antes not in (0, None):
                    res(True, f"voto: {cid} já tem voto seu ({antes}) — não mexi")
                else:
                    await aba.js("document.querySelector('#lotes button.sim').click()")
                    await asyncio.sleep(2)
                    v1 = await aba.js("fetch('voto.php?estado=1',{cache:'no-store'}).then(r=>r.json()).then(j=>(j.votos['%s']||[0])[0])" % cid)
                    await aba.js("document.querySelector('#lotes button.sim').click()")
                    await asyncio.sleep(2)
                    v2 = await aba.js("fetch('voto.php?estado=1',{cache:'no-store'}).then(r=>r.json()).then(j=>(j.votos['%s']||[0])[0])" % cid)
                    res(v1 == 1 and v2 == 0, f"voto: aprovar gravou ({v1}) e desfazer voltou ({v2}) em {cid}")
            res(not aba.erros, "sem erro de JavaScript" + (f": {aba.erros[:3]}" if aba.erros else ""))
    finally:
        if proc:
            proc.terminate()
        if srv:
            srv.terminate()
            if os.path.exists("pub/dados/votos.jsonl"):
                os.remove("pub/dados/votos.jsonl")
            if os.path.exists("pub/dados/votos.jsonl.antes"):
                os.rename("pub/dados/votos.jsonl.antes", "pub/dados/votos.jsonl")
    print("== TUDO CERTO" if ok else "== TEM FALHA (ver ✗ acima)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
