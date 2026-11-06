#!/usr/bin/env python3
"""Gera um criativo por API de imagem (alternativa ao Magnific pelo conector). Rode na pasta do projeto.

  python3 gera.py --prompt lotes/lote1/prompts/l1c1.txt --ref lp/img/01.jpg --ref refs/123.jpg \
                  --saida lotes/lote1/gerados/l1c1 [--n 2] [--provedor gemini|openai] [--proporcao 4:5] [--simular]

--ref: na ORDEM do prompt (Imagem 1 = produto, Imagem 2 = outra foto do produto, última = anúncio modelo).
--saida: sem extensão; grava <saida>_a.png, <saida>_b.png...
--simular: monta o pedido e mostra o que iria, sem chamar a API (não gasta nada).

Provedor e chaves vêm do .env da raiz do repositório:
  GERADOR=gemini  + GEMINI_API_KEY=...   (Google AI Studio · "Nano Banana")   modelo: GEMINI_IMAGE_MODEL
  GERADOR=openai  + OPENAI_API_KEY=...   (OpenAI · gpt-image)                 modelo: OPENAI_IMAGE_MODEL
Os nomes de modelo mudam com o tempo: se a API disser que o modelo não existe, troque no .env (ver INSTALACAO.md).
"""
import argparse, base64, io, json, os, sys, time, urllib.error, urllib.request, uuid

from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
PADRAO = {"gemini": "gemini-3-pro-image-preview", "openai": "gpt-image-1"}
TAMANHO_OPENAI = {"4:5": "1024x1536", "9:16": "1024x1536", "2:3": "1024x1536", "1:1": "1024x1024",
                  "16:9": "1536x1024", "3:2": "1536x1024"}


def env():
    d = {}
    p = os.path.join(RAIZ, ".env")
    if os.path.exists(p):
        for l in open(p, encoding="utf-8"):
            l = l.strip()
            if l and not l.startswith("#") and "=" in l:
                k, v = l.split("=", 1)
                d[k.strip()] = v.strip().strip('"').strip("'")
    d.update({k: v for k, v in os.environ.items() if k in ("GERADOR", "GEMINI_API_KEY", "OPENAI_API_KEY",
                                                         "GEMINI_IMAGE_MODEL", "OPENAI_IMAGE_MODEL")})
    return d


def imagem_bytes(arq, lado=1536):
    """JPEG reduzido (lado maior ≤ 1536) pra mandar como referência."""
    im = Image.open(arq)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        f = Image.new("RGB", im.size, (255, 255, 255))
        f.paste(im, mask=im.split()[-1])
        im = f
    im = im.convert("RGB")
    if max(im.size) > lado:
        im.thumbnail((lado, lado), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "JPEG", quality=92)
    return b.getvalue()


def post(url, corpo, cab, tempo=300):
    rq = urllib.request.Request(url, data=corpo, headers=cab, method="POST")
    try:
        with urllib.request.urlopen(rq, timeout=tempo) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode(errors='ignore')[:600]}")


# ---------------------------------------------------------------- Google Gemini (Nano Banana)
def gemini(prompt, refs, proporcao, chave, modelo, simular):
    partes = [{"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(imagem_bytes(r)).decode()}} for r in refs]
    partes.append({"text": prompt})
    cfg = {"responseModalities": ["TEXT", "IMAGE"], "imageConfig": {"aspectRatio": proporcao, "imageSize": "2K"}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
    if simular:
        print(f"  [simulação] POST {url} · {len(refs)} imagens · proporção {proporcao} · prompt {len(prompt)} caracteres")
        return None
    cab = {"Content-Type": "application/json", "x-goog-api-key": chave}
    corpo = {"contents": [{"role": "user", "parts": partes}], "generationConfig": cfg}
    try:
        j = post(url, json.dumps(corpo).encode(), cab)
    except RuntimeError as e:
        if "imageSize" in str(e) or "image_size" in str(e):   # modelo sem 2K: tenta no tamanho padrão
            cfg["imageConfig"].pop("imageSize")
            j = post(url, json.dumps(corpo).encode(), cab)
        else:
            raise
    for c in j.get("candidates") or []:
        for p in (c.get("content") or {}).get("parts") or []:
            d = p.get("inlineData") or p.get("inline_data")
            if d and d.get("data"):
                return base64.b64decode(d["data"])
    motivo = json.dumps(j.get("promptFeedback") or (j.get("candidates") or [{}])[0].get("finishReason") or j)[:400]
    raise RuntimeError("a API não devolveu imagem: " + motivo)


# ---------------------------------------------------------------- OpenAI (gpt-image)
def openai(prompt, refs, proporcao, chave, modelo, simular):
    tam = TAMANHO_OPENAI.get(proporcao, "1024x1536")
    if simular:
        print(f"  [simulação] POST https://api.openai.com/v1/images/edits · {modelo} · {len(refs)} imagens · {tam}")
        return None
    fr = uuid.uuid4().hex
    corpo = io.BytesIO()

    def campo(nome, valor):
        corpo.write(f"--{fr}\r\nContent-Disposition: form-data; name=\"{nome}\"\r\n\r\n{valor}\r\n".encode())
    campo("model", modelo)
    campo("prompt", prompt)
    campo("size", tam)
    campo("quality", "high")
    campo("n", "1")
    for k, r in enumerate(refs):
        corpo.write(f"--{fr}\r\nContent-Disposition: form-data; name=\"image[]\"; filename=\"ref{k}.jpg\"\r\n"
                    f"Content-Type: image/jpeg\r\n\r\n".encode())
        corpo.write(imagem_bytes(r))
        corpo.write(b"\r\n")
    corpo.write(f"--{fr}--\r\n".encode())
    j = post("https://api.openai.com/v1/images/edits", corpo.getvalue(),
             {"Authorization": f"Bearer {chave}", "Content-Type": f"multipart/form-data; boundary={fr}"})
    d = (j.get("data") or [{}])[0]
    if d.get("b64_json"):
        return base64.b64decode(d["b64_json"])
    if d.get("url"):
        return urllib.request.urlopen(d["url"], timeout=120).read()
    raise RuntimeError("a API não devolveu imagem: " + json.dumps(j)[:400])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True, help="arquivo .txt com o prompt (ou o próprio texto)")
    ap.add_argument("--ref", action="append", default=[], help="imagem de referência, na ordem do prompt")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--n", type=int, default=2)
    ap.add_argument("--provedor", default=None)
    ap.add_argument("--proporcao", default="4:5")
    ap.add_argument("--simular", action="store_true")
    a = ap.parse_args()

    e = env()
    prov = (a.provedor or e.get("GERADOR") or "").lower()
    if prov not in ("gemini", "openai"):
        sys.exit("✗ defina GERADOR=gemini ou GERADOR=openai no .env (ou use --provedor). "
                 "Magnific é pelo conector do Claude Code, não por este script.")
    chave = e.get("GEMINI_API_KEY" if prov == "gemini" else "OPENAI_API_KEY", "")
    if not chave and not a.simular:
        sys.exit(f"✗ falta {'GEMINI_API_KEY' if prov == 'gemini' else 'OPENAI_API_KEY'} no .env")
    modelo = e.get("GEMINI_IMAGE_MODEL" if prov == "gemini" else "OPENAI_IMAGE_MODEL") or PADRAO[prov]
    prompt = open(a.prompt, encoding="utf-8").read() if os.path.exists(a.prompt) else a.prompt
    for r in a.ref:
        if not os.path.exists(r):
            sys.exit(f"✗ referência não existe: {r}")

    fn = gemini if prov == "gemini" else openai
    erros = 0
    for k in range(a.n):
        dst = f"{a.saida}_{'abcdefgh'[k]}.png"
        t0 = time.time()
        try:
            b = fn(prompt, a.ref, a.proporcao, chave, modelo, a.simular)
            if b is None:
                continue
            im = Image.open(io.BytesIO(b))
            os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
            im.save(dst)
            print(f"✔ {dst} · {im.size[0]}x{im.size[1]} · {prov}/{modelo} · {time.time() - t0:.0f}s", flush=True)
        except Exception as x:
            erros += 1
            print(f"✗ {dst}: {str(x)[:500]}", flush=True)
    sys.exit(1 if erros else 0)


if __name__ == "__main__":
    main()
