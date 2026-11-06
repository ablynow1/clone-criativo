#!/usr/bin/env python3
"""Confere se a máquina está pronta pro Clone Criativo. Rode da raiz do repositório:  python3 motor/verifica.py"""
import json, os, shutil, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
ok_geral = True


def linha(ok, txt, dica=""):
    global ok_geral
    print(("✔ " if ok else "✗ ") + txt + ("" if ok or not dica else f"\n    → {dica}"))
    if not ok:
        ok_geral = False


def aviso(txt):
    print("· " + txt)


linha(sys.version_info >= (3, 9), f"Python {sys.version.split()[0]}", "instale o Python 3.9 ou mais novo")
try:
    import PIL
    linha(True, f"Pillow {PIL.__version__}")
except ImportError:
    linha(False, "Pillow (imagens)", "pip3 install -r requirements.txt")
try:
    import websockets
    linha(True, f"websockets {websockets.__version__}")
except ImportError:
    linha(False, "websockets (controle do Chrome)", "pip3 install -r requirements.txt")
try:
    from cdp import CHROME
except SystemExit:
    CHROME = None
linha(bool(CHROME), f"Chrome: {CHROME or 'não achei'}", "instale o Google Chrome ou ponha CHROME=/caminho/do/chrome no ambiente")
linha(bool(shutil.which("curl")), "curl", "instale o curl")

env = {}
p = os.path.join(RAIZ, ".env")
if os.path.exists(p):
    for l in open(p, encoding="utf-8"):
        l = l.strip()
        if l and not l.startswith("#") and "=" in l:
            k, v = l.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    linha(True, ".env encontrado")
else:
    aviso(".env não existe ainda (cp .env.exemplo .env) — sem ele o padrão é Magnific pelo conector e página local")

g = (env.get("GERADOR") or "magnific-mcp").lower()
print(f"\nGerador de imagem: {g}")
if g == "magnific-mcp":
    r = subprocess.run(["claude", "mcp", "list"], capture_output=True, text=True) if shutil.which("claude") else None
    tem = bool(r and "magnific" in (r.stdout + r.stderr).lower())
    linha(tem, "conector do Magnific no Claude Code",
          "claude mcp add --transport http -s user magnific https://mcp.magnific.com  → depois /mcp → magnific → Authenticate")
elif g == "gemini":
    linha(bool(env.get("GEMINI_API_KEY")), "GEMINI_API_KEY no .env", "crie a chave em https://aistudio.google.com/apikey")
elif g == "openai":
    linha(bool(env.get("OPENAI_API_KEY")), "OPENAI_API_KEY no .env", "crie a chave em https://platform.openai.com/api-keys")
else:
    linha(False, f"GERADOR={g} desconhecido", "use magnific-mcp, gemini ou openai")

print("\nPágina de aprovação:")
if env.get("SITE_BASE"):
    falta = [k for k in ("FTP_HOST", "FTP_USER", "FTP_PASS") if not env.get(k)]
    linha(not falta, f"publicar em {env['SITE_BASE']}", "faltam no .env: " + ", ".join(falta))
    linha(bool(shutil.which("lftp")), "lftp (envio por FTP)", "Mac: brew install lftp · Linux: sudo apt install lftp")
else:
    aviso("sem hospedagem: a página abre no seu computador com  python3 motor/servidor.py  (votos funcionam)")

print("\n" + ("== TUDO PRONTO" if ok_geral else "== FALTA ARRUMAR o que está com ✗ (ver INSTALACAO.md)"))
sys.exit(0 if ok_geral else 1)
