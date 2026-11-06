#!/usr/bin/env python3
"""Abre a página de aprovação no seu computador, com os votos funcionando (sem precisar de hospedagem).

  python3 servidor.py                 # rode na pasta do projeto: serve pub/ em http://localhost:8765
  python3 servidor.py --porta 9000
  python3 servidor.py --rede          # deixa abrir pelo celular na mesma rede Wi-Fi (http://<ip do computador>:8765)

Faz o mesmo que o voto.php faz numa hospedagem: POST voto.php grava em pub/dados/votos.jsonl e
GET voto.php?estado=1 devolve o último voto/comentário de cada criativo. Ctrl+C para.
"""
import argparse, functools, http.server, json, os, socket, sys, threading, time

TRAVA = threading.Lock()


def estado(log):
    voto, coment = {}, {}
    if os.path.exists(log):
        for l in open(log, encoding="utf-8"):
            try:
                x = json.loads(l)
            except Exception:
                continue
            if not isinstance(x, dict) or not {"id", "v", "t"} <= set(x):
                continue
            k = str(x["id"])
            if int(x["v"]) != 2 and (k not in voto or x["t"] >= voto[k][1]):
                voto[k] = (int(x["v"]), int(x["t"]))
            if x.get("c") and (k not in coment or x["t"] >= coment[k][1]):
                coment[k] = (x["c"], int(x["t"]))
    out = {}
    for k in set(voto) | set(coment):
        v = voto.get(k, (0, 0))
        c = coment.get(k, ("", 0))
        out[k] = [v[0], max(v[1], c[1]), c[0]]
    return out


class Pagina(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, cod, dados):
        b = json.dumps(dados, ensure_ascii=False).encode()
        self.send_response(cod)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _log(self):
        return os.path.join(self.directory, "dados", "votos.jsonl")

    def do_GET(self):
        if self.path.split("?")[0].endswith("/voto.php"):
            with TRAVA:
                return self._json(200, {"ok": True, "votos": estado(self._log())})
        if "/dados/" in self.path:
            return self._json(403, {"ok": False})
        return super().do_GET()

    def do_POST(self):
        if not self.path.split("?")[0].endswith("/voto.php"):
            return self._json(404, {"ok": False})
        n = min(int(self.headers.get("Content-Length") or 0), 200000)
        try:
            entra = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._json(400, {"ok": False, "erro": "json"})
        lote = entra.get("votos") if isinstance(entra, dict) and isinstance(entra.get("votos"), list) else [entra]
        try:
            validos = set(map(str, json.load(open(os.path.join(self.directory, "ids.json")))))
        except Exception:
            validos = set()
        agora = int(time.time() * 1000)
        linhas = []
        for x in lote[:200]:
            if not isinstance(x, dict):
                continue
            i, v = str(x.get("id", "")), x.get("v")
            if i not in validos or v not in (1, -1, 0, 2):
                continue
            t = x.get("t") if isinstance(x.get("t"), int) else agora
            c = str(x.get("c") or "").strip()[:800]
            linhas.append(json.dumps({"id": i, "v": v, "c": c, "t": t, "s": agora}, ensure_ascii=False))
        if linhas:
            os.makedirs(os.path.dirname(self._log()), exist_ok=True)
            with TRAVA, open(self._log(), "a", encoding="utf-8") as f:
                f.write("\n".join(linhas) + "\n")
        return self._json(200, {"ok": True})


def meu_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--porta", type=int, default=8765)
    ap.add_argument("--rede", action="store_true")
    ap.add_argument("--pasta", default="pub")
    a = ap.parse_args()
    if not os.path.exists(os.path.join(a.pasta, "index.html")):
        sys.exit(f"✗ falta {a.pasta}/index.html — rode antes: python3 <motor>/pagina.py (na pasta do projeto)")
    host = "0.0.0.0" if a.rede else "127.0.0.1"
    srv = http.server.ThreadingHTTPServer((host, a.porta), functools.partial(Pagina, directory=os.path.abspath(a.pasta)))
    print(f"✔ página no ar: http://localhost:{a.porta}/", flush=True)
    if a.rede:
        print(f"  no celular (mesma rede Wi-Fi): http://{meu_ip()}:{a.porta}/", flush=True)
    print("  votos em pub/dados/votos.jsonl · Ctrl+C para", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
