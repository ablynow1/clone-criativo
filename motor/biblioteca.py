#!/usr/bin/env python3
"""Coletor da Biblioteca de Anúncios da Meta (Clone Criativo). Rode DENTRO da pasta do projeto.

  python3 biblioteca.py busca "termo 1;termo 2" --pais BR [--dias 14] [--exata]   -> dumps/bu_<pais>_<termo>_14d.html
  python3 biblioteca.py paginas marcas.json [--pais ALL] [--dias 14]              -> dumps/pg_<marca>_<id>_14d.html
  python3 biblioteca.py pageid "loja.com.br;outra.com"                            -> pageids.json
  python3 biblioteca.py alcance [--ads cands_ue.json] [--max 150]                 -> alcance.json (alcance real na UE)

Uma coleta por vez: o comando pega a trava (/tmp/clone-criativo.lockdir) e, se outra coleta estiver rodando, espera a
vez. Assim nunca há dois Chromes na Biblioteca ao mesmo tempo (a Meta bloqueia).

Regras: pausa de 9 s entre páginas, media_type=all, ordem por impressões, corte por start_date[max],
scroll infinito capturado pelo GraphQL. Bloqueio é silencioso: 3 páginas seguidas vazias = o trabalho para e este
comando sai com código 3. Esperar ~40 min e rodar o MESMO comando (o que já veio fica em cache em dumps/).
"""
import argparse, asyncio, json, os, re, subprocess, sys, time, urllib.parse

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from adlib import url_busca, url_pagina, extrai_ads, total, sem_resultado, slug   # noqa: E402
from cdp import Sessao, trava                          # noqa: E402

PAUSA = float(os.environ.get("CDP_PAUSA", "9"))


def _cache_ok(arq):
    return os.path.exists(arq) and os.path.getsize(arq) > 0


# ================================================================ execução
async def _coleta(alvos, rolagens, com_alcance=False, dias=14):
    os.makedirs("dumps", exist_ok=True)
    falta = [a for a in alvos if not _cache_ok(os.path.join("dumps", a["slug"] + ".html"))]
    print(f"{len(alvos)} alvos · {len(alvos) - len(falta)} em cache · {len(falta)} pra coletar", flush=True)
    if not falta and not com_alcance:
        return 0
    async with Sessao() as aba:
        rc = await _coleta_paginas(aba, falta, rolagens)
        if rc == 0 and com_alcance:
            # mesmo Chrome: alcance real das imagens que rodam na UE
            rc = await _alcance_lista(aba, _fila_alcance_dos_dumps(20, dias))
        return rc


async def _coleta_paginas(aba, falta, rolagens):
    vazios = 0
    for k, a in enumerate(falta, 1):
        arq = os.path.join("dumps", a["slug"] + ".html")
        t0 = time.time()
        try:
            await aba.vai(a["url"], a.get("espera", 12))
            await aba.rola(rolagens)
            await asyncio.sleep(1.5)
            h = await aba.js("document.documentElement.outerHTML") or ""
            extra = await aba.corpos_gql('"ad_archive_id"')
            if extra:
                h += "\n<!--GQL-->\n" + "\n".join(extra)
        except Exception as e:
            print(f"[{k}/{len(falta)}] {a['slug']}: ERRO {str(e)[:120]}", flush=True)
            continue
        n = len(extrai_ads(h))
        if n == 0 and not sem_resultado(h):
            vazios += 1
            print(f"[{k}/{len(falta)}] {a['slug']}: 0 ads | não renderizou (não guardei)", flush=True)
            if vazios >= 3:
                print("!! BLOQUEIO: 3 páginas seguidas vazias. Esperar ~40 min e rodar o mesmo comando.", flush=True)
                return 3
            await asyncio.sleep(PAUSA * 2)
            continue
        vazios = 0
        with open(arq, "w", errors="ignore") as f:
            f.write(h)
        print(f"[{k}/{len(falta)}] {a['slug']}: {n} ads | total do filtro {total(h)} | {time.time() - t0:.0f}s", flush=True)
        await asyncio.sleep(PAUSA)
    return 0


JS_PAGEID = r"""(async (d) => {
  const r = await fetch('/ads/library/?active_status=active&ad_type=all&country=ALL&q=' + encodeURIComponent(d) +
                        '&search_type=keyword_unordered&media_type=all', {credentials: 'include'});
  const html = await r.text();
  const stem = d.replace(/^www\./, '').split('.')[0].toLowerCase();
  const cnt = {};
  for (const p of html.split('"ad_archive_id"').slice(1)) {
    const s = p.slice(0, 9000);
    const pid = (s.match(/"page_id":"(\d+)"/) || [])[1];
    if (!pid) continue;
    let pn = (s.match(/"page_name":"((?:[^"\\]|\\.)*)"/) || [])[1] || '';
    try { pn = JSON.parse('"' + pn + '"'); } catch (e) {}
    cnt[pid] = cnt[pid] || {page_id: pid, page_name: pn, n: 0, n_dominio: 0};
    cnt[pid].n++;
    const links = s.match(/"link_url":"[^"]*"/g) || [];
    if (links.some(l => l.toLowerCase().includes(stem))) cnt[pid].n_dominio++;
  }
  return {status: r.status, paginas: Object.values(cnt).sort((a, b) => b.n_dominio - a.n_dominio || b.n - a.n).slice(0, 5)};
})(%s)"""


async def _pageids(dominios):
    out = json.load(open("pageids.json")) if os.path.exists("pageids.json") else {}
    falta = [d for d in dominios if d not in out]
    if not falta:
        print("todos em cache (pageids.json)")
        return 0
    async with Sessao() as aba:
        await aba.vai("https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=ALL&media_type=all", 10)
        for d in falta:
            try:
                r = await aba.js(JS_PAGEID % json.dumps(d))
            except Exception as e:
                print(d, "ERRO", str(e)[:100], flush=True)
                continue
            out[d] = r.get("paginas") or []
            json.dump(out, open("pageids.json", "w"), ensure_ascii=False, indent=1)
            top = out[d][0] if out[d] else None
            print(f"{d}: " + (f"{top['page_name']} ({top['page_id']}) · {top['n_dominio']}/{top['n']} ads com o domínio"
                              if top else "nenhum anunciante achado"), flush=True)
            await asyncio.sleep(5)
    return 0


JS_CLICA = r"""(() => {
  const b = [...document.querySelectorAll('div[role=button],a[role=button]')]
    .filter(e => /ver detalhes do an|see ad details|ver detalles del an/i.test(e.innerText || ''));
  if (b.length) { b[0].click(); return b.length; }
  return 0;
})()"""

# Repete a consulta AdLibraryV3AdDetailsQuery (modelo capturado do clique) trocando adArchiveID/pageID.
JS_REPETE = r"""(async (tpl, lista) => {
  const out = [];
  function anda(o, acc) {
    if (!o || typeof o !== 'object') return;
    if (Array.isArray(o)) { o.forEach(x => anda(x, acc)); return; }
    if (o.age_range && (typeof o.male === 'number' || typeof o.female === 'number')) {
      const m = o.male || 0, f = o.female || 0, u = o.unknown || 0;
      acc.masc += m; acc.fem += f; acc.idade[o.age_range] = (acc.idade[o.age_range] || 0) + m + f + u;
    }
    for (const k in o) anda(o[k], acc);
  }
  for (const [aid, pid] of lista) {
    const q = new URLSearchParams(tpl);
    const v = JSON.parse(q.get('variables'));
    for (const k of Object.keys(v)) { if (/adArchiveID/i.test(k)) v[k] = aid; if (/^pageID$/i.test(k)) v[k] = pid; }
    q.set('variables', JSON.stringify(v));
    let st = 0, alcance = null, acc = {masc: 0, fem: 0, idade: {}};
    try {
      const r = await fetch('/api/graphql/', {method: 'POST', body: q, credentials: 'include',
                            headers: {'content-type': 'application/x-www-form-urlencoded'}});
      st = r.status;
      const t = await r.text();
      const m = t.match(/"eu_total_reach":(\d+)/); if (m) alcance = parseInt(m[1]);
      for (const linha of t.split('\n')) { try { anda(JSON.parse(linha), acc); } catch (e) {} }
    } catch (e) { st = -1; }
    let idadeTop = null, maior = 0;
    for (const k in acc.idade) if (acc.idade[k] > maior) { maior = acc.idade[k]; idadeTop = k; }
    const tot = acc.masc + acc.fem;
    out.push({id: aid, st: st, alcance: alcance, pct_fem: tot ? Math.round(100 * acc.fem / tot) : null, idade_top: idadeTop});
    await new Promise(z => setTimeout(z, 900 + Math.random() * 600));
  }
  return out;
})(%s, %s)"""


async def _alcance_lista(aba, fila):
    """Alcance real na UE de cada anúncio da lista [{id, page_id}] (só os veiculados na UE têm). Grava alcance.json."""
    feito = json.load(open("alcance.json")) if os.path.exists("alcance.json") else {}
    fila = [a for a in fila if a["id"] not in feito]
    if not fila:
        return 0
    print(f"alcance real na UE: {len(fila)} anúncios pra consultar (~{max(1, round(len(fila) * 1.6 / 60))} min)", flush=True)
    tpl = None
    for pid in list(dict.fromkeys(a["page_id"] for a in fila))[:4]:
        # abre a página da marca e clica em "Ver detalhes" pra capturar o modelo da consulta
        await aba.vai(url_pagina(pid, "ALL", 0), 12)
        for _ in range(2):
            aba.posts = []
            n = await aba.js(JS_CLICA)
            await asyncio.sleep(6)
            tpl = next((p for p in aba.posts if "adArchiveID" in urllib.parse.unquote_plus(p)), None)
            if tpl or not n:
                break
        if tpl:
            break
    if not tpl:
        print("✗ não consegui capturar a consulta do detalhe (botão 'Ver detalhes' não respondeu)", flush=True)
        return 4
    for k in range(0, len(fila), 20):
        lote = [[a["id"], a["page_id"]] for a in fila[k:k + 20]]
        res = await aba.js(JS_REPETE % (json.dumps(tpl), json.dumps(lote))) or []
        for x in res:
            if x.get("st") == 200:
                feito[x["id"]] = {kk: x[kk] for kk in ("alcance", "pct_fem", "idade_top")}
        json.dump(feito, open("alcance.json", "w"), indent=1)
        ok = [x for x in res if x.get("alcance")]
        print(f"  alcance {min(k + 20, len(fila))}/{len(fila)} · {len(ok)} com número neste lote"
              + (f" (maior {max(x['alcance'] for x in ok):,})".replace(",", ".") if ok else ""), flush=True)
        if res and all(x.get("st") != 200 for x in res):
            print("!! BLOQUEIO: a consulta parou de responder — o que veio está em alcance.json", flush=True)
            return 3
        await asyncio.sleep(4)
    return 0


def _fila_alcance_dos_dumps(por_marca=12, min_dias=14):
    """Das páginas de marca já coletadas: as imagens veiculadas na UE mais altas na ordem por impressão (até N por dump)."""
    from adlib import normaliza
    agora, out = int(time.time()), []
    for f in sorted(os.listdir("dumps")) if os.path.isdir("dumps") else []:
        if not (f.startswith("pg_") and f.endswith(".html")):
            continue
        n = 0
        for b in extrai_ads(open(os.path.join("dumps", f), errors="ignore").read()):
            a = normaliza(b, agora)
            if a["ue"] and a["ativo"] and a["fmt"] in ("imagem", "carrossel") and a["dias"] >= min_dias and a["page_id"]:
                out.append({"id": a["id"], "page_id": a["page_id"]})
                n += 1
                if n >= por_marca:
                    break
    return out


async def _alcance(arq_ads, maximo):
    A = json.load(open(arq_ads))
    fila = [a for a in A if a.get("ue") and a.get("page_id")][:maximo]
    print(f"{len(fila)} anúncios veiculados na UE em {arq_ads}", flush=True)
    if not fila:
        return 0
    async with Sessao() as aba:
        return await _alcance_lista(aba, fila)


def executa(job):
    m = job["modo"]
    if m in ("busca", "paginas"):
        return asyncio.run(_coleta(job["alvos"], job.get("rolagens", 8),
                                   com_alcance=(m == "paginas" and job.get("alcance", True)), dias=job.get("dias", 14)))
    if m == "pageid":
        return asyncio.run(_pageids(job["dominios"]))
    if m == "alcance":
        return asyncio.run(_alcance(job["ads"], job.get("max", 150)))
    print("modo desconhecido", m)
    return 2


# ================================================================ linha de comando
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["busca", "paginas", "pageid", "alcance", "executa"])
    ap.add_argument("entrada", nargs="?")
    ap.add_argument("--pais", default=None)
    ap.add_argument("--dias", type=int, default=14)
    ap.add_argument("--exata", action="store_true")
    ap.add_argument("--rolagens", type=int, default=None)
    ap.add_argument("--ads", default="cands_ue.json")
    ap.add_argument("--max", type=int, default=150)
    a = ap.parse_args()

    if a.modo == "executa":
        job = json.load(open(a.entrada))
        trava()
        rc = executa(job)
        print("== trabalho terminou", time.strftime("%H:%M"), "código", rc, flush=True)
        sys.exit(rc or 0)

    if a.modo == "busca":
        pais = a.pais or "BR"
        termos = [t.strip() for t in (a.entrada or "").split(";") if t.strip()]
        job = dict(modo="busca", rolagens=a.rolagens or 6, alvos=[
            dict(slug=f"bu_{pais.lower()}_{slug(t)}_{a.dias}d" + ("_ex" if a.exata else ""),
                 url=url_busca(t, pais, a.dias, a.exata), espera=13) for t in termos])
    elif a.modo == "paginas":
        pais = a.pais or "ALL"
        marcas = json.load(open(a.entrada or "marcas.json"))
        job = dict(modo="paginas", rolagens=a.rolagens or 8, dias=a.dias, alvos=[
            dict(slug=f"pg_{slug(m['nome'], 28)}_{str(m['page_id'])[-6:]}_{a.dias}d",
                 url=url_pagina(m["page_id"], pais, a.dias), espera=13) for m in marcas])
    elif a.modo == "pageid":
        job = dict(modo="pageid", dominios=[d.strip().lower().replace("https://", "").replace("http://", "").split("/")[0]
                                            for d in (a.entrada or "").split(";") if d.strip()])
    else:
        job = dict(modo="alcance", ads=a.ads, max=a.max)

    if job["modo"] in ("busca", "paginas"):
        falta = [x for x in job["alvos"] if not _cache_ok(os.path.join("dumps", x["slug"] + ".html"))]
        if not falta:
            print(f"{len(job['alvos'])} alvos · todos em cache (dumps/)")
            sys.exit(0)
        job["alvos"] = falta
        print(f"{len(falta)} página(s) pra coletar (~{len(falta)} min de Biblioteca)", flush=True)

    trava()
    rc = executa(job)
    print("== FIM", time.strftime("%H:%M"), "código", rc, flush=True)
    sys.exit(rc or 0)


if __name__ == "__main__":
    main()
