#!/usr/bin/env python3
"""Cria a pasta de um produto novo em projetos/<produto>/ (rode de qualquer lugar).

  python3 motor/novo.py <produto> "<link da página do produto>" ["<Marca · Produto>"]
  Ex.: python3 motor/novo.py bolsa-couro "https://minhaloja.com.br/products/bolsa" "Minha Loja · Bolsa de Couro"

<produto> = só letra minúscula, número e hífen (vira o nome da pasta e o final do endereço da página).
Se o .env tiver SITE_BASE (sua hospedagem), a página publicada fica em $SITE_BASE/<produto>/.
"""
import json, os, re, sys, time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)


def env():
    d = {}
    p = os.path.join(RAIZ, ".env")
    if os.path.exists(p):
        for l in open(p, encoding="utf-8"):
            l = l.strip()
            if l and not l.startswith("#") and "=" in l:
                k, v = l.split("=", 1)
                d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        sys.exit(__doc__)
    produto, lp = a[0], a[1]
    titulo = a[2] if len(a) > 2 else produto.replace("-", " ").title()
    if not re.fullmatch(r"[a-z0-9-]+", produto):
        sys.exit(f"✗ '{produto}': use só letra minúscula, número e hífen (ex.: bolsa-couro)")
    if not lp.startswith("http"):
        sys.exit("✗ o link da página tem que começar com http")
    pasta = os.path.join(RAIZ, "projetos", produto)
    if os.path.exists(os.path.join(pasta, "config.json")):
        sys.exit(f"✗ {pasta} já existe — use outro nome (ex.: {produto}-2)")
    for d in ("lp", "busca", "dumps", "refs", "analise/leitura", "lotes", "pub"):
        os.makedirs(os.path.join(pasta, d), exist_ok=True)
    e = env()
    base = e.get("SITE_BASE", "").rstrip("/")
    url = f"{base}/{produto}/" if base else ""
    json.dump(dict(produto=produto, lp=lp, titulo=titulo, url=url, criado=time.strftime("%Y-%m-%d"),
                   gerador=e.get("GERADOR", "magnific-mcp"), proporcao="4:5", dias_validado=14),
              open(os.path.join(pasta, "config.json"), "w"), ensure_ascii=False, indent=2)
    print(f"✔ projeto: {pasta}")
    print(f"  entrar:  cd {pasta}")
    print(f"  página:  {url or 'local (python3 ' + AQUI + '/servidor.py)'}")


if __name__ == "__main__":
    main()
