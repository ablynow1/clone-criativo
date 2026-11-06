#!/usr/bin/env python3
"""Biblioteca de Anúncios da Meta: URLs, extração dos anúncios do HTML/GraphQL e normalização.

O que a Meta expõe (conferido em 04/11/2026):
- Anúncio comercial veiculado no Brasil: NÃO tem número de impressão nem alcance (impressions_index = -1).
  Os sinais de validação são indiretos: posição na listagem ordenada por impressões, dias no ar e
  collation_count (quantos anúncios usam o mesmo criativo).
- Anúncio veiculado na União Europeia (is_aaa_eligible = true): o detalhe traz eu_total_reach, o alcance
  REAL na UE (ex.: uma marca de vitaminas alemã: 1.959.789). É o único número de verdade; ver biblioteca.py alcance.
- impressions_text "<100" aparece em anúncio que quase não rodou: sinal negativo.
"""
import datetime, json, re, urllib.parse

# ---------------------------------------------------------------- URLs
def url_base(pais="ALL", dias=14):
    u = (f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country={pais}&media_type=all"
         "&sort_data[direction]=desc&sort_data[mode]=total_impressions")
    if dias:
        lim = (datetime.date.today() - datetime.timedelta(days=dias)).isoformat()
        u += f"&start_date%5Bmax%5D={lim}"   # ÚNICO corte de data que a Biblioteca respeita
    return u


def url_pagina(page_id, pais="ALL", dias=14):
    return url_base(pais, dias) + f"&view_all_page_id={page_id}&search_type=page"


def url_busca(termo, pais="BR", dias=14, exata=False):
    q = urllib.parse.quote(f'"{termo}"' if exata else termo)
    return url_base(pais, dias) + f"&q={q}&search_type=" + ("keyword_exact_phrase" if exata else "keyword_unordered")


def url_marca(page_id):
    """Link pro humano: todos os anúncios ativos da marca, mundo todo."""
    return ("https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=ALL"
            f"&view_all_page_id={page_id}&search_type=page&media_type=all")


def url_anuncio(aid):
    return f"https://www.facebook.com/ads/library/?id={aid}"


def slug(s, n=40):
    s = (s or "").lower()
    for a, b in (("áàâãä", "a"), ("éèêë", "e"), ("íìîï", "i"), ("óòôõö", "o"), ("úùûü", "u"), ("ç", "c"), ("ñ", "n")):
        for c in a:
            s = s.replace(c, b)
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")[:n] or "x"


# ---------------------------------------------------------------- extração
def sem_resultado(html):
    return ("Nenhum anúncio corresponde" in html or "No ads match" in html
            or re.search(r'"search_results_connection":\{"count":0[,}]', html) is not None)


def total(html):
    """Contador da listagem (quantos anúncios o filtro tem no total)."""
    m = re.search(r'"search_results_connection":\{"count":(\d+)', html)
    return int(m.group(1)) if m else None


def extrai_ads(html):
    """Ancora em ad_archive_id e recupera o objeto JSON inteiro por casamento de chaves. Mantém a ordem da página."""
    if not html or "Nenhum anúncio corresponde" in html or "No ads match" in html:
        return []
    ads, vistos = [], set()
    for m in re.finditer(r'"ad_archive_id"', html):
        o = _objeto(html, m.start())
        if not o:
            continue
        aid = o.get("ad_archive_id")
        if not aid or aid in vistos or "snapshot" not in o:
            continue
        vistos.add(aid)
        ads.append(o)
    return ads


def _objeto(s, i, janela=120000):
    d = 0
    for j in range(i, max(0, i - janela), -1):
        c = s[j]
        if c == '}':
            d += 1
        elif c == '{':
            if d == 0:
                d2 = 0
                for k in range(j, min(len(s), j + janela)):
                    if s[k] == '{':
                        d2 += 1
                    elif s[k] == '}':
                        d2 -= 1
                        if d2 == 0:
                            try:
                                return json.loads(s[j:k + 1])
                            except Exception:
                                return None
                return None
            d -= 1
    return None


# ---------------------------------------------------------------- destino do clique
_RUINS = [("app", r"itunes\.apple\.com|apps\.apple\.com|play\.google\.com|onelink\.me|app\.adjust\.com"),
          ("marketplace", r"shopee\.|shein\.|(^|[./])amazon\.|amzn\.|mercadoli[vb]re|magazineluiza|magalu\.|aliexpress|"
                          r"temu\.com|americanas\.com|casasbahia|submarino\.com|kwai\.com"),
          ("instagram", r"instagram\.com|instagr\.am"), ("whatsapp", r"wa\.me|whatsapp"),
          ("messenger", r"m\.me/|messenger\.com"), ("facebook", r"(^|//|\.)facebook\.com|fb\.com|fb\.me"),
          ("tiktok", r"tiktok\.com"), ("linktree", r"linktr\.ee|linkin\.bio"), ("telegram", r"t\.me/")]


def destino(link):
    """'loja' quando o clique vai pro site da marca; senão o tipo: app, marketplace, instagram, whatsapp... (regra: só loja)."""
    l = (link or "").strip().lower()
    if not l:
        return "vazio"
    for nome, rx in _RUINS:
        if re.search(rx, l):
            return nome
    return "loja"


def dominio(link):
    try:
        h = urllib.parse.urlparse(link if "//" in (link or "") else "https://" + (link or "")).hostname or ""
    except Exception:
        return ""
    return h[4:] if h.startswith("www.") else h


# ---------------------------------------------------------------- normalização
FMT = {"IMAGE": "imagem", "DCO": "imagem", "MULTI_IMAGES": "imagem", "CAROUSEL": "carrossel",
       "DPA": "catalogo", "VIDEO": "video"}


def _txt(x):
    if isinstance(x, dict):
        return x.get("text") or ""
    return x or ""


def normaliza(ad, agora):
    sn = ad.get("snapshot") or {}
    cards = sn.get("cards") or []
    c0 = cards[0] if cards else {}
    fmt_meta = sn.get("display_format") or ""

    titulo = sn.get("title") or c0.get("title") or ""
    corpo = _txt(sn.get("body")) or c0.get("body") or ""
    if "{{" in titulo:
        titulo = c0.get("title") or ""
    if "{{" in corpo:
        corpo = c0.get("body") or ""

    imagens = []
    for im in sn.get("images") or []:
        u = im.get("original_image_url") or im.get("resized_image_url")
        if u:
            imagens.append(u)
    for c in cards:
        if c.get("video_sd_url") or c.get("video_hd_url"):
            continue
        u = c.get("original_image_url") or c.get("resized_image_url")
        if u and u not in imagens:
            imagens.append(u)
    videos = [v.get("video_hd_url") or v.get("video_sd_url") for v in (sn.get("videos") or [])
              if v.get("video_hd_url") or v.get("video_sd_url")]
    videos += [c.get("video_hd_url") or c.get("video_sd_url") for c in cards
               if c.get("video_hd_url") or c.get("video_sd_url")]
    preview = ((sn.get("videos") or [{}])[0].get("video_preview_image_url") if sn.get("videos") else None) \
        or c0.get("video_preview_image_url")

    fmt = FMT.get(fmt_meta, "outro")
    if fmt == "imagem" and not imagens and videos:
        fmt = "video"
    ini = ad.get("start_date") or 0
    dias = max(0, int((agora - ini) / 86400)) if ini else 0
    imp = (ad.get("impressions_with_index") or {}).get("impressions_text")
    link = sn.get("link_url") or c0.get("link_url") or ""

    return {
        "id": str(ad.get("ad_archive_id")),
        "page_id": str(ad.get("page_id") or sn.get("page_id") or ""),
        "marca": (sn.get("page_name") or ad.get("page_name") or "?").strip(),
        "ativo": bool(ad.get("is_active")),
        "formato_meta": fmt_meta, "fmt": fmt,
        "imagens": imagens[:8], "videos": videos[:3],
        "thumb": (imagens[0] if imagens else preview) or "",
        "headline": titulo.strip()[:200],
        "copy": corpo.strip()[:1200],
        "descricao": (sn.get("link_description") or c0.get("link_description") or "").strip()[:200],
        "cta": sn.get("cta_text") or c0.get("cta_text") or "",
        "link": link, "dominio": dominio(link), "destino": destino(link),
        "dias": dias, "inicio": ini,
        "variacoes": ad.get("collation_count") or 1,
        "collation_id": str(ad.get("collation_id") or ""),
        "ue": bool(ad.get("is_aaa_eligible")),
        "imp_txt": imp,
        "ia": bool(ad.get("contains_digital_created_media")),
        "plataformas": ad.get("publisher_platform") or [],
        "seguidores": sn.get("page_like_count") or 0,
        "categorias_pagina": sn.get("page_categories") or [],
        "n_cards": len(cards),
        "biblioteca": url_anuncio(ad.get("ad_archive_id")),
    }
