#!/usr/bin/env python3
"""Lê a LP do cliente (rode na pasta do projeto) -> lp/lp.json + prints + fotos do produto.

  python3 lp.py "<url da LP>"

Abre no Chrome headless (desktop 1440 e iPhone 390), rola a página toda pra carregar as imagens, e guarda:
  lp/desktop_NN.jpg, lp/mobile_NN.jpg   prints da página inteira em fatias (pra eu ler a oferta)
  lp/dobra_desktop.jpg, lp/dobra_mobile.jpg   primeira tela
  lp/img/NN.jpg + lp/imagens.jpg        fotos grandes da página (maior versão do CDN) + prancha numerada
  lp/lp.json                            título, textos, preços, JSON-LD, produto Shopify (.js), cores, fontes, logo
Não usa a trava da Biblioteca (é o site do cliente, não a Meta).
"""
import asyncio, base64, concurrent.futures as cf, io, json, os, re, sys, urllib.parse, urllib.request

os.environ.setdefault("CDP_PORTA", "9383")
os.environ.setdefault("CDP_PERFIL", "/tmp/validados-lp-cdp")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Sessao, UA_IPHONE   # noqa: E402
from PIL import Image, ImageDraw, ImageFont   # noqa: E402

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/137 Safari/537.36"}

JS_FECHA_POPUP = r"""(() => {
  let n = 0;
  document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}));
  const rx = /^(×|x|✕|fechar|close|não,? obrigad|nao,? obrigad|no,? thanks|aceitar|aceito|accept|ok|entendi|continuar)/i;
  for (const e of document.querySelectorAll('button,[role=button],a,[class*=close],[aria-label*=close i],[aria-label*=fechar i]')) {
    const t = (e.innerText || e.getAttribute('aria-label') || '').trim();
    const r = e.getBoundingClientRect();
    if (r.width && r.height && (rx.test(t) || /close|fechar/i.test(e.className || '')) && t.length < 40) {
      const z = getComputedStyle(e.closest('[role=dialog],[class*=modal],[class*=popup],[class*=cookie],[id*=cookie]') || e).position;
      if (e.closest('[role=dialog],[class*=modal],[class*=popup],[class*=cookie],[id*=cookie],[class*=newsletter]')) { try { e.click(); n++; } catch (x) {} }
    }
  }
  return n;
})()"""

JS_ROLA = r"""(async () => {
  // rolagem instantânea: com scroll-behavior:smooth a página não chega nas seções e as animações de entrada não disparam
  document.documentElement.style.setProperty('scroll-behavior', 'auto', 'important');
  const vai = y => window.scrollTo({top: y, left: 0, behavior: 'instant'});
  const h = () => Math.min(document.documentElement.scrollHeight, 30000);
  for (let y = 0; y < h(); y += 500) { vai(y); await new Promise(r => setTimeout(r, 220)); }
  vai(h()); await new Promise(r => setTimeout(r, 1200));
  vai(0); await new Promise(r => setTimeout(r, 800));
  return document.documentElement.scrollHeight;
})()"""

JS_EXTRAI = r"""(async () => {
  const vis = e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity !== 0; };
  const meta = n => (document.querySelector(`meta[name="${n}"],meta[property="${n}"]`) || {}).content || '';
  const out = {url: location.href, titulo: document.title, lang: document.documentElement.lang,
    descricao: meta('description'), og_titulo: meta('og:title'), og_imagem: meta('og:image'),
    canonical: (document.querySelector('link[rel=canonical]') || {}).href || ''};
  out.senha = /\/password/.test(location.pathname) || !!document.querySelector('form[action*=password]');
  out.jsonld = [];
  for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
    try { const j = JSON.parse(s.textContent); (Array.isArray(j) ? j : (j['@graph'] || [j])).forEach(x => out.jsonld.push(x)); } catch (e) {}
  }
  out.jsonld = out.jsonld.filter(x => /product|offer|aggregaterating|organization|brand/i.test(JSON.stringify(x['@type'] || ''))).slice(0, 6);
  out.plataforma = window.Shopify ? 'shopify' : (window.LS && window.LS.store ? 'nuvemshop' : (document.querySelector('[data-yampi],script[src*=yampi]') ? 'yampi' : (/vtex/i.test(document.documentElement.innerHTML.slice(0, 200000)) ? 'vtex' : '')));
  out.shopify_produto = null;
  if (window.Shopify && /\/products\//.test(location.pathname)) {
    try { const r = await fetch(location.pathname.replace(/\/$/, '') + '.js'); if (r.ok) { const p = await r.json();
      out.shopify_produto = {titulo: p.title, marca: p.vendor, tipo: p.type, tags: p.tags, preco: p.price / 100,
        preco_de: p.compare_at_price ? p.compare_at_price / 100 : null,
        variantes: (p.variants || []).slice(0, 30).map(v => ({nome: v.title, preco: v.price / 100, de: v.compare_at_price ? v.compare_at_price / 100 : null, disponivel: v.available})),
        imagens: (p.images || []).map(u => (u.startsWith('//') ? 'https:' + u : u)),
        descricao: (p.description || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 5000)}; } } catch (e) {}
  }
  out.titulos = [...document.querySelectorAll('h1,h2,h3')].filter(vis).map(e => e.tagName + ': ' + e.innerText.trim().replace(/\s+/g, ' ')).filter(t => t.length > 4).slice(0, 80);
  const bt = new Set();
  for (const e of document.querySelectorAll('button,a[class*=btn],a[class*=button],[class*=button],input[type=submit]')) {
    if (!vis(e)) continue; const t = (e.innerText || e.value || '').trim().replace(/\s+/g, ' ');
    if (t && t.length < 60) bt.add(t); if (bt.size > 50) break; }
  out.botoes = [...bt];
  const txt = (document.body.innerText || '').replace(/\n{3,}/g, '\n\n');
  out.texto = txt.slice(0, 45000);
  const pr = new Set(); const rx = /R\$\s?\d{1,3}(\.\d{3})*(,\d{2})?/g; let m;
  while ((m = rx.exec(txt)) && pr.size < 40) pr.add(txt.slice(Math.max(0, m.index - 50), m.index + 40).replace(/\s+/g, ' '));
  out.precos = [...pr];
  const imgs = []; const seen = new Set();
  for (const e of document.querySelectorAll('img')) {
    let u = e.currentSrc || e.src || ''; if (!u || u.startsWith('data:')) continue;
    if (e.srcset) { let best = 0; for (const p of e.srcset.split(',')) { const [uu, w] = p.trim().split(/\s+/); const n = parseInt(w) || 0; if (n > best) { best = n; u = new URL(uu, location.href).href; } } }
    const base = u.split('?')[0].replace(/_(\d+x\d*|\d*x\d+)(?=\.)/, '').replace(/-\d+-\d+(?=\.(jpe?g|png|webp))/, '');
    if (seen.has(base)) continue; seen.add(base);
    const r = e.getBoundingClientRect();
    const nw = e.naturalWidth, nh = e.naturalHeight;
    if (Math.max(nw, r.width) < 280 || Math.max(nh, r.height) < 200) continue;
    imgs.push({url: u, alt: (e.alt || '').slice(0, 120), nw, nh, w: Math.round(r.width), h: Math.round(r.height),
      top: Math.round(r.top + scrollY), no_header: !!e.closest('header,nav'), logo: /logo/i.test(u + ' ' + e.alt + ' ' + e.className)});
  }
  out.imagens = imgs.slice(0, 80);
  const lg = imgs.find(i => i.logo) || [...document.querySelectorAll('header img,a[href="/"] img')].map(e => ({url: e.currentSrc || e.src}))[0];
  out.logo = lg ? lg.url : '';
  const cor = s => { const m = s.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/); if (!m || (m[4] !== undefined && +m[4] < 0.5)) return null;
    return '#' + [m[1], m[2], m[3]].map(x => (+x).toString(16).padStart(2, '0')).join(''); };
  const areas = {};
  for (const e of document.querySelectorAll('body *')) { const r = e.getBoundingClientRect(); const a = r.width * r.height;
    if (a < 15000) continue; const c = cor(getComputedStyle(e).backgroundColor); if (c) areas[c] = (areas[c] || 0) + a; }
  out.cores_fundo = Object.entries(areas).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([c, a]) => ({cor: c, area: Math.round(a)}));
  const est = e => e ? {cor: cor(getComputedStyle(e).color), fundo: cor(getComputedStyle(e).backgroundColor), fonte: getComputedStyle(e).fontFamily, peso: getComputedStyle(e).fontWeight, tam: getComputedStyle(e).fontSize, texto: (e.innerText || e.value || '').trim().slice(0, 60)} : null;
  const cta = [...document.querySelectorAll('button,a,input[type=submit]')].filter(vis).filter(e => /comprar|adicionar|carrinho|buy|add to cart|garant|quero/i.test(e.innerText || e.value || ''))
    .sort((a, b) => b.getBoundingClientRect().width * b.getBoundingClientRect().height - a.getBoundingClientRect().width * a.getBoundingClientRect().height)[0];
  out.estilos = {body: est(document.body), h1: est(document.querySelector('h1')), h2: est(document.querySelector('h2')), cta: est(cta)};
  return out;
})()"""


JS_ALTURA = r"""(() => {
  // destrava página que prende a rolagem no html/body (altura fixa + overflow) — senão o print para na 1ª tela
  for (const e of [document.documentElement, document.body]) {
    e.style.setProperty('overflow', 'visible', 'important'); e.style.setProperty('height', 'auto', 'important');
    e.style.setProperty('max-height', 'none', 'important');
  }
  let fundo = Math.max(document.documentElement.scrollHeight, document.body.scrollHeight);
  for (const e of document.querySelectorAll('body > *, main, footer')) {
    const r = e.getBoundingClientRect(); if (r.height) fundo = Math.max(fundo, r.bottom + scrollY);
  }
  return Math.min(Math.round(fundo), %d);
})()"""


async def print_inteiro(aba, largura, prefixo, fatia, max_h, dpr):
    h = int(await aba.js(JS_ALTURA % max_h) or 2000)
    r = await aba.cmd("Page.captureScreenshot", format="jpeg", quality=82, captureBeyondViewport=True,
                      clip={"x": 0, "y": 0, "width": largura, "height": h, "scale": 1})
    im = Image.open(io.BytesIO(base64.b64decode(r["data"]))).convert("RGB")
    arqs = []
    passo = int(fatia * dpr)
    for k, y in enumerate(range(0, im.height, passo), 1):
        p = f"lp/{prefixo}_{k:02d}.jpg"
        im.crop((0, y, im.width, min(im.height, y + passo))).save(p, quality=80)
        arqs.append(p)
    dobra = im.crop((0, 0, im.width, min(im.height, int((900 if prefixo == "desktop" else 844) * dpr))))
    dobra.save(f"lp/dobra_{prefixo}.jpg", quality=85)
    return arqs, h


def maior_versao(u):
    """Pede a maior versão da foto no CDN (Shopify, Nuvemshop)."""
    if "cdn.shopify.com" in u or "/cdn/shop/" in u:
        u = re.sub(r"_(\d+x\d*|\d*x\d+)(?=\.(jpe?g|png|webp))", "", u.split("?")[0], flags=re.I)
        return u + "?width=2048"
    if "mitiendanube.com" in u or "nuvemshop" in u or "cloudfront.net/stores" in u:
        return re.sub(r"-\d+-\d+(?=\.(jpe?g|png|webp))", "-1024-1024", u, flags=re.I)
    return u


def baixa(u, dst):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
            b = r.read()
        im = Image.open(io.BytesIO(b))
        im.load()
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            fundo = Image.new("RGB", im.size, (255, 255, 255))
            fundo.paste(im, mask=im.split()[-1])
            im = fundo
        im.convert("RGB").save(dst, quality=92)
        return im.size
    except Exception:
        return None


async def main(url):
    os.makedirs("lp/img", exist_ok=True)
    async with Sessao() as aba:
        # desktop
        await aba.cmd("Emulation.setDeviceMetricsOverride", width=1440, height=900, deviceScaleFactor=1, mobile=False)
        await aba.vai(url, 8)
        await aba.js(JS_FECHA_POPUP)
        await aba.js(JS_ROLA)
        await aba.js(JS_FECHA_POPUP)
        await asyncio.sleep(1)
        dados = await aba.js(JS_EXTRAI)
        desk, hd = await print_inteiro(aba, 1440, "desktop", 1800, 16000, 1)
        # celular
        await aba.cmd("Network.setUserAgentOverride", userAgent=UA_IPHONE)
        await aba.cmd("Emulation.setDeviceMetricsOverride", width=390, height=844, deviceScaleFactor=2, mobile=True)
        await aba.cmd("Emulation.setTouchEmulationEnabled", enabled=True)
        await aba.vai(url, 8)
        await aba.js(JS_FECHA_POPUP)
        await aba.js(JS_ROLA)
        await aba.js(JS_FECHA_POPUP)
        await asyncio.sleep(1)
        mob, hm = await print_inteiro(aba, 390, "mobile", 1500, 12000, 2)
    dados["prints"] = {"desktop": desk, "mobile": mob, "altura_desktop": hd, "altura_mobile": hm}

    # fotos: produto Shopify primeiro, depois as maiores da página (sem logo/ícone)
    urls = []
    if dados.get("shopify_produto"):
        urls += dados["shopify_produto"]["imagens"]
    cand = sorted([i for i in dados.get("imagens", []) if not i["logo"] and not i["no_header"]],
                  key=lambda i: (i["top"] > 2500, -(max(i["nw"], i["w"]) * max(i["nh"], i["h"]))))
    urls += [i["url"] for i in cand]
    vistos, finais = set(), []
    for u in urls:
        u = urllib.parse.urljoin(dados["url"], u)
        b = re.sub(r"\?.*$", "", maior_versao(u))
        if b in vistos:
            continue
        vistos.add(b)
        finais.append(maior_versao(u))
    finais = finais[:24]
    with cf.ThreadPoolExecutor(8) as ex:
        tams = list(ex.map(lambda t: baixa(t[1], f"lp/img/{t[0] + 1:02d}.jpg"), enumerate(finais)))
    dados["fotos"] = [dict(arquivo=f"lp/img/{k + 1:02d}.jpg", url=u, w=t[0], h=t[1])
                      for k, (u, t) in enumerate(zip(finais, tams)) if t]
    if dados.get("logo"):
        if baixa(urllib.parse.urljoin(dados["url"], dados["logo"]), "lp/logo.png.jpg"):
            dados["logo_arquivo"] = "lp/logo.png.jpg"
    json.dump(dados, open("lp/lp.json", "w"), ensure_ascii=False, indent=1)

    # prancha numerada das fotos (pra eu escolher quais são do produto)
    F = None
    for p in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
              "C:/Windows/Fonts/arialbd.ttf", "DejaVuSans-Bold.ttf", "Arial Bold.ttf"):
        try:
            F = ImageFont.truetype(p, 26)
            break
        except Exception:
            pass
    if F is None:
        try:
            F = ImageFont.load_default(size=26)
        except TypeError:
            F = ImageFont.load_default()
    fs = dados["fotos"]
    if fs:
        C, L = 4, 330
        img = Image.new("RGB", (C * (L + 10), ((len(fs) + C - 1) // C) * (L + 10)), (255, 255, 255))
        d = ImageDraw.Draw(img)
        for k, f in enumerate(fs):
            im = Image.open(f["arquivo"]).convert("RGB")
            im.thumbnail((L, L))
            x, y = (k % C) * (L + 10), (k // C) * (L + 10)
            img.paste(im, (x, y))
            d.rectangle([x, y, x + 64, y + 34], fill=(0, 0, 0))
            d.text((x + 6, y + 3), f"{k + 1:02d}", fill=(255, 80, 80), font=F)
        img.save("lp/imagens.jpg", quality=82)

    sp = dados.get("shopify_produto") or {}
    print("LP:", dados.get("titulo", "")[:90])
    print("plataforma:", dados.get("plataforma") or "?", "· senha!" if dados.get("senha") else "")
    if sp:
        print(f"produto: {sp.get('titulo')} · R$ {sp.get('preco')} (de {sp.get('preco_de')}) · {len(sp.get('variantes', []))} variantes")
    print(f"preços no texto: {len(dados.get('precos', []))} · títulos: {len(dados.get('titulos', []))} · fotos: {len(fs)}")
    print(f"prints: {len(desk)} desktop + {len(mob)} celular · prancha das fotos: lp/imagens.jpg")
    print("cores de fundo:", ", ".join(c["cor"] for c in dados.get("cores_fundo", [])[:6]))
    e = dados.get("estilos") or {}
    print("fontes: h1", ((e.get("h1") or {}).get("fonte") or "")[:40], "· corpo", ((e.get("body") or {}).get("fonte") or "")[:40])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("uso: python3 lp.py <url>")
    asyncio.run(main(sys.argv[1]))
