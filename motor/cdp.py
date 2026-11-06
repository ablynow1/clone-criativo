#!/usr/bin/env python3
"""Chrome headless via CDP: base dos coletores do Clone Criativo (LP e Biblioteca).

- Um Chrome só (porta CDP_PORTA, perfil CDP_PERFIL). O caminho do Chrome sai de CHROME (variável de ambiente) ou é
  procurado nos lugares de sempre (Mac, Linux, Windows/WSL).
- Trava global da Biblioteca (/tmp/clone-criativo.lockdir): dois coletores ao mesmo tempo = a Biblioteca bloqueia.
- Captura as respostas GraphQL (scroll infinito, detalhe do anúncio) e os POSTs do GraphQL
  (modelo pra repetir a consulta do detalhe com fetch dentro da página).
"""
import asyncio, atexit, json, os, re, signal, socket, subprocess, sys, time, urllib.request

import websockets

import shutil


def acha_chrome():
    """Caminho do Chrome/Chromium: variável CHROME ou os lugares de sempre. None se não achar."""
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for c in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium",
              "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
              "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe"):
        if os.path.exists(c):
            return c
    for n in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        w = shutil.which(n)
        if w:
            return w
    return None


CHROME = acha_chrome()
UA_MAC = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
UA_IPHONE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 "
             "(KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1")
PORTA = int(os.environ.get("CDP_PORTA", "9381"))
PERFIL = os.environ.get("CDP_PERFIL", "/tmp/clone-criativo-cdp")
TRAVA = "/tmp/clone-criativo.lockdir"


# ---------------------------------------------------------------- trava global
def _ancestrais():
    """pids deste processo e de todos os pais (o shell que me chamou também tem 'biblioteca.py' na linha)."""
    out, p = set(), os.getpid()
    for _ in range(30):
        out.add(p)
        r = subprocess.run(["ps", "-o", "ppid=", "-p", str(p)], capture_output=True, text=True)
        try:
            p = int(r.stdout.strip())
        except ValueError:
            break
        if p <= 1:
            break
    return out


def _outro_coletor_vivo():
    """True se outro coletor da Biblioteca estiver rodando (fora eu e quem me chamou)."""
    r = subprocess.run(["pgrep", "-f", r"motor/biblioteca\.py (busca|paginas|pageid|alcance|executa)"],
                       capture_output=True, text=True)
    meus = _ancestrais()
    for p in r.stdout.split():
        p = int(p)
        if p in meus:
            continue
        a = subprocess.run(["ps", "-o", "args=", "-p", str(p)], capture_output=True, text=True).stdout
        if re.search(r"(^|/)(ba|z)?sh\s+(-\w+\s+)*-c\s", a):   # embrulho "zsh -c ..." de algum comando, não é coletor
            continue
        if a.strip():
            return True
    return False


def trava(espera_max=3 * 3600):
    """Pega a trava da Biblioteca. Espera a vez se outro coletor estiver rodando; limpa trava órfã."""
    t0, avisou = time.time(), False
    while True:
        try:
            os.mkdir(TRAVA)
            break
        except FileExistsError:
            if not _outro_coletor_vivo():
                idade = time.time() - os.stat(TRAVA).st_mtime
                if idade > 90:   # ninguém rodando e trava velha = sobrou de processo morto
                    print("… trava órfã (ninguém coletando) — limpando", flush=True)
                    try:
                        os.rmdir(TRAVA)
                    except OSError:
                        pass
                    continue
            if not avisou:
                print("… outro coletor da Biblioteca está rodando — esperando a vez", flush=True)
                avisou = True
            if time.time() - t0 > espera_max:
                raise SystemExit("✗ trava ocupada há muito tempo — conferir " + TRAVA)
            time.sleep(20)

    def solta(*_):
        try:
            os.rmdir(TRAVA)
        except OSError:
            pass
    atexit.register(solta)

    def sai(*_):
        solta()
        sys.exit(1)
    for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(s, sai)


# ---------------------------------------------------------------- Chrome
def _porta_livre(p):
    s = socket.socket()
    try:
        s.connect(("127.0.0.1", p))
        s.close()
        return False
    except Exception:
        return True


def sobe_chrome(ua=UA_MAC):
    if not _porta_livre(PORTA):
        return None   # já tem Chrome nessa porta (reaproveita)
    if not CHROME:
        raise SystemExit("✗ não achei o Google Chrome. Instale o Chrome ou aponte o caminho: export CHROME=/caminho/do/chrome")
    os.makedirs(PERFIL, exist_ok=True)
    p = subprocess.Popen(
        [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
         f"--remote-debugging-port={PORTA}", f"--user-data-dir={PERFIL}",
         f"--user-agent={ua}", "--window-size=1440,3000", "--lang=pt-BR",
         "--no-first-run", "--no-default-browser-check",
         "--disable-blink-features=AutomationControlled",
         "--disable-background-timer-throttling", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        if not _porta_livre(PORTA):
            return p
        time.sleep(0.5)
    raise RuntimeError("Chrome não subiu na porta CDP")


def _ws_url():
    for _ in range(30):
        try:
            d = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORTA}/json/list", timeout=5))
            pags = [t for t in d if t.get("type") == "page"]
            if pags:
                return pags[0]["webSocketDebuggerUrl"]
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError("sem aba CDP")


class Aba:
    def __init__(self, ws):
        self.ws = ws
        self.i = 0
        self.gql = []      # requestId das respostas GraphQL
        self.posts = []    # postData dos POSTs ao GraphQL (modelo de consulta)

    def zera(self):
        self.gql, self.posts = [], []

    async def cmd(self, metodo, **params):
        self.i += 1
        meu = self.i
        await self.ws.send(json.dumps({"id": meu, "method": metodo, "params": params}))
        while True:
            msg = json.loads(await self.ws.recv())
            m = msg.get("method")
            if m == "Network.responseReceived":
                if "graphql" in msg["params"]["response"].get("url", ""):
                    self.gql.append(msg["params"]["requestId"])
            elif m == "Network.requestWillBeSent":
                rq = msg["params"].get("request") or {}
                if "graphql" in rq.get("url", "") and rq.get("postData"):
                    self.posts.append(rq["postData"])
            if msg.get("id") == meu:
                if "error" in msg:
                    raise RuntimeError(f"{metodo}: {msg['error']}")
                return msg.get("result", {})

    async def js(self, expr):
        r = await self.cmd("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
        if r.get("exceptionDetails"):
            raise RuntimeError("JS: " + json.dumps(r["exceptionDetails"])[:400])
        return (r.get("result") or {}).get("value")

    async def corpos_gql(self, contem):
        """Corpos das respostas GraphQL capturadas que contêm a string."""
        out = []
        for rid in self.gql:
            try:
                b = (await self.cmd("Network.getResponseBody", requestId=rid)).get("body") or ""
            except Exception:
                continue
            if contem in b:
                out.append(b)
        return out

    async def vai(self, url, espera=8.0):
        self.zera()
        await self.cmd("Page.navigate", url=url)
        await asyncio.sleep(espera)

    async def rola(self, vezes=6, pausa=2.4):
        for _ in range(vezes):
            await self.js("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(pausa)


class Sessao:
    """async with Sessao() as aba: ...   (sobe o Chrome, liga Page/Runtime/Network, fecha no fim)"""

    def __init__(self, ua=UA_MAC):
        self.ua = ua
        self.proc = None
        self.ws = None

    async def __aenter__(self):
        self.proc = sobe_chrome(self.ua)
        self.ws = await websockets.connect(_ws_url(), max_size=300 * 1024 * 1024, ping_interval=None)
        aba = Aba(self.ws)
        await aba.cmd("Page.enable")
        await aba.cmd("Runtime.enable")
        await aba.cmd("Network.enable", maxResourceBufferSize=60_000_000, maxTotalBufferSize=250_000_000)
        return aba

    async def __aexit__(self, *exc):
        try:
            await self.ws.close()
        except Exception:
            pass
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except Exception:
                self.proc.kill()
