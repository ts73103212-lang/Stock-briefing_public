"""A4縦・学会抄録風HTML資料の共通部品（CSS・ページ枠・SVG図）。"""
from __future__ import annotations

from html import escape

THEMES = {
    1: {"label": "世界経済の行方", "en": "Global Macro after the Midterms", "c": "#1D3557", "a": "#C1121F", "t": "#EEF2F8", "t2": "#FBEDEE"},
    2: {"label": "半導体の巻き返しとAI投資", "en": "Semiconductors & AI", "c": "#0B4F5C", "a": "#0E9C9C", "t": "#E8F4F4", "t2": "#FFF6E0"},
    3: {"label": "お年玉銘柄と暴騰候補20", "en": "New-Year Picks & Top 20 Movers", "c": "#7E1A2C", "a": "#B8860B", "t": "#FBF3E4", "t2": "#F8ECEE"},
}

CSS = r"""
:root{
  /* レイアウト：A4縦シート（210×297mm）を縦に並べ、各シートは学会抄録の2段組 */
  --paper:#FFFFFF; --desk:#E9EBEF; --ink:#1B1F27; --muted:#5A6170; --rule:#D5D9E1; --soft:#F4F5F8;
  --up:#13803B; --down:#C1121F; --warn:#B45309;
  --f-body:"Meiryo UI","メイリオ",Meiryo,"Noto Sans JP","Hiragino Sans",sans-serif;
  --f-num:"Meiryo UI","Noto Sans JP",sans-serif;
  color-scheme: light;
}
html{background:var(--desk)}
body{background:var(--desk);color:var(--ink);font-family:var(--f-body);margin:0;
  padding-block:24px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));}
.deck{display:flex;flex-direction:column;align-items:center;gap:28px}
.toc{width:210mm;max-width:100%;font-size:13px;color:var(--muted);display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center}
.toc b{color:var(--ink)}
.toc a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--rule)}
.sheet-wrap{width:210mm;max-width:100%}
.sheet{width:210mm;height:297mm;box-sizing:border-box;background:var(--paper);box-shadow:0 2px 14px rgba(20,30,50,.16);
  padding:11mm 12mm 9mm;display:flex;flex-direction:column;overflow:hidden;position:relative;font-size:11.4px;line-height:1.62;
  transform-origin:top left}
.sheet *{box-sizing:border-box}
/* ページ上部：会議名・セッション番号 */
.runhead{display:flex;justify-content:space-between;align-items:baseline;font-size:9.5px;color:var(--muted);letter-spacing:.04em;
  border-bottom:1.5px solid var(--c);padding-bottom:4px}
.runhead b{color:var(--c)}
.titleblock{margin-top:9px;display:grid;grid-template-columns:auto 1fr;gap:4px 12px;align-items:start}
.sesno{grid-row:span 2;background:var(--c);color:#fff;font-weight:700;font-size:13px;line-height:1;padding:9px 9px 8px;border-radius:3px;text-align:center;min-width:46px}
.sesno small{display:block;font-size:8.5px;font-weight:400;opacity:.85;margin-top:4px;letter-spacing:.06em}
h1{font-size:20.5px;line-height:1.32;margin:0;color:var(--c);text-wrap:balance;font-weight:700}
.sub{font-size:11.5px;color:var(--muted);margin:0}
.abstract{margin-top:9px;background:var(--t);border-radius:3px;padding:8px 11px;display:grid;grid-template-columns:auto 1fr;gap:4px 10px}
.abstract .lab{font-weight:700;color:var(--c);font-size:10.5px;letter-spacing:.08em;padding-top:1px}
.abstract p{margin:0}
.kw{font-size:10px;color:var(--muted)}
.body{flex:1;min-height:0;margin-top:10px;overflow:hidden}
.fit{display:flex;flex-direction:column;gap:9px;justify-content:space-between}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:9px 16px;min-height:0}
.cols3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:9px 12px}
.span2{grid-column:span 2}
h2{font-size:13px;margin:0 0 3px;color:var(--c);display:flex;gap:7px;align-items:baseline;line-height:1.35}
h2 .n{font-size:11px;color:#fff;background:var(--c);border-radius:2px;padding:1px 5px;font-weight:700}
h3{font-size:11.5px;margin:0 0 2px;color:var(--ink)}
p{margin:0 0 4px}
ul.b{margin:0;padding-left:1.15em}
ul.b li{margin:0 0 2.5px}
ul.b li::marker{color:var(--a)}
.em{color:var(--a);font-weight:700}
.dn{color:var(--down);font-weight:700}
.upc{color:var(--up);font-weight:700}
.fig{border:1px solid var(--rule);border-radius:3px;padding:7px 8px 5px;background:#fff}
.fig svg{display:block;width:100%;height:auto}
.cap{font-size:9.6px;color:var(--muted);margin-top:3px;line-height:1.45}
.cap b{color:var(--ink)}
table.t{width:100%;border-collapse:collapse;font-size:10.2px;line-height:1.4;font-variant-numeric:tabular-nums}
table.t th{background:var(--c);color:#fff;font-weight:700;padding:4px 5px;text-align:left;white-space:nowrap}
table.t td{padding:3.6px 5px;border-bottom:1px solid var(--rule);vertical-align:top}
table.t tr:nth-child(even) td{background:var(--soft)}
table.t td.r,table.t th.r{text-align:right;white-space:nowrap}
table.t.nw td{white-space:nowrap}
table.t td.c,table.t th.c{text-align:center}
.box{border-radius:3px;padding:8px 10px;background:var(--soft)}
.box.tint{background:var(--t)}
.box.tint2{background:var(--t2)}
.alert{border:2px solid var(--down);border-radius:4px;padding:8px 11px;background:#FFF5F5}
.alert .hd{color:var(--down);font-weight:700;font-size:12.5px;margin-bottom:3px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.kpi{border-top:3px solid var(--c);background:var(--soft);padding:6px 8px 6px}
.kpi .v{font-family:var(--f-num);font-size:19px;font-weight:700;line-height:1.15;color:var(--c);font-variant-numeric:tabular-nums}
.kpi .v small{font-size:11px;margin-left:1px}
.kpi .l{font-size:9.5px;color:var(--muted);line-height:1.35;margin-top:2px}
.tag{display:inline-block;font-size:9px;font-weight:700;border-radius:2px;padding:0 5px;line-height:1.6;color:#fff;background:var(--a);vertical-align:1px}
.tag.c{background:var(--c)} .tag.g{background:#6B7280} .tag.r{background:var(--down)} .tag.u{background:var(--up)}
.stars{color:var(--a);letter-spacing:-1px;white-space:nowrap}
.refs{margin-top:auto;border-top:1px solid var(--rule);padding-top:4px;font-size:8.4px;color:var(--muted);line-height:1.45}
.refs ol{margin:0;padding-left:1.6em;columns:2;column-gap:14px}
.foot{display:flex;justify-content:space-between;font-size:8.4px;color:var(--muted);margin-top:4px}
.small{font-size:9.8px}
.muted{color:var(--muted)}
.vote{display:grid;grid-template-columns:repeat(4,1fr);gap:0;border:1px solid var(--rule)}
.vote div{border-right:1px solid var(--rule);border-bottom:1px solid var(--rule);height:24px;padding:3px 5px;font-size:9.5px;color:var(--muted)}
@media screen and (max-width:830px){ .sheet-wrap{overflow:hidden} }
@media print{
  @page{size:A4 portrait;margin:0}
  html,body{background:#fff;padding:0}
  .deck{gap:0;display:block}
  .toc{display:none}
  .sheet-wrap{width:210mm;max-width:none;height:auto!important}
  .sheet{box-shadow:none;page-break-after:always;break-after:page;transform:none!important}
}
@media (prefers-reduced-motion: reduce){*{transition:none!important}}
"""

FIT_JS = r"""
<script>
(function(){
  // 各シートの本文を、枠に収まる最大の倍率（1.0〜1.3）に拡大し、残りの余白は段落間に均等配分する
  function grow(){
    document.querySelectorAll('.sheet').forEach(function(s){
      var b=s.querySelector('.body'), f=s.querySelector('.fit'); if(!b||!f) return;
      var lo=1, hi=1.3;
      f.style.minHeight=''; f.style.zoom=1;
      for(var i=0;i<14;i++){ var m=(lo+hi)/2; f.style.zoom=m; if(f.scrollHeight*m<=b.clientHeight-2) lo=m; else hi=m; }
      f.style.zoom=lo; s.dataset.zoom=lo.toFixed(3); var free=b.clientHeight/lo-f.scrollHeight; s.dataset.free=Math.round(free*lo);
      f.style.minHeight=Math.floor((b.clientHeight-2)/lo)+'px';
    });
  }
  function fit(){
    document.querySelectorAll('.sheet-wrap').forEach(function(w){
      var s=w.querySelector('.sheet'); s.style.transform=''; var k=Math.min(1,w.clientWidth/s.offsetWidth);
      s.style.transform=k<1?'scale('+k+')':''; w.style.height=k<1?(s.offsetHeight*k)+'px':'';
    });
  }
  function all(){ grow(); fit(); }
  window.addEventListener('resize',fit);
  if(document.fonts&&document.fonts.ready){ document.fonts.ready.then(all); }
  window.addEventListener('load',all); all();
})();
</script>
"""


def sheet(theme: int, page: int, title: str, sub: str, body: str, refs: list[str], abstract: str | None = None, kw: str | None = None, sid: str | None = None) -> str:
    t = THEMES[theme]
    style = f"--c:{t['c']};--a:{t['a']};--t:{t['t']};--t2:{t['t2']}"
    ab = ""
    if abstract:
        ab = f'<div class="abstract"><div class="lab">要旨</div><div><p>{abstract}</p>' + (f'<div class="kw">キーワード：{kw}</div>' if kw else "") + "</div></div>"
    refs_html = ""
    if refs:
        refs_html = '<div class="refs"><ol>' + "".join(f"<li>{r}</li>" for r in refs) + "</ol></div>"
    gpage = (theme - 1) * 4 + page
    return f"""
<section class="sheet-wrap" id="{sid or f't{theme}p{page}'}"><article class="sheet" style="{style}">
  <div class="runhead"><span><b>株クラ秋季研究会 2026</b>｜2026年11月13日（金）</span><span>Session {theme}　{escape(t['en'])}</span></div>
  <div class="titleblock"><div class="sesno">{theme}-{page}<small>{page}/4</small></div><h1>{title}</h1><p class="sub">{sub}</p></div>
  {ab}
  <div class="body"><div class="fit">{body}</div></div>
  {refs_html}
  <div class="foot"><span>話題提供用の資料です。投資勧誘ではありません。数値は記載日時点、※は概算・報道ベースの数値。投資判断はご自身で。</span><span>p.{gpage} / 12</span></div>
</article></section>"""


def document(title: str, sheets: list[str]) -> str:
    toc = '<nav class="toc"><b>株クラ秋季研究会 2026　抄録集</b>' + "".join(
        f'<a href="#t{i}p1">Session {i}：{THEMES[i]["label"]}</a>' for i in (1, 2, 3)) + "</nav>"
    return f"""<title>{escape(title)}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap">
<style>{CSS}</style>
<main class="deck">{toc}{''.join(sheets)}</main>
{FIT_JS}
"""


# ---------------- SVG 図 ----------------
FONT = "font-family=\"Meiryo UI,Noto Sans JP,sans-serif\""


def _t(x, y, s, size=10, fill="#1B1F27", anchor="start", weight="400", extra=""):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" {FONT} {extra}>{s}</text>'


def bar_chart(labels, values, *, w=340, h=170, colors=None, fmt="{:+.1f}%", zero_line=True, highlight=None, unit_note="", ymin=None, ymax=None, label_size=8.5):
    """縦棒（正負対応）。"""
    pl, pr, pt, pb = 30, 6, 14, 30
    vmin = min(0, min(values)) if ymin is None else ymin
    vmax = max(0, max(values)) if ymax is None else ymax
    span = vmax - vmin or 1
    iw, ih = w - pl - pr, h - pt - pb
    def y(v):
        return pt + (vmax - v) / span * ih
    n = len(values)
    bw = iw / n * 0.68
    out = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img">']
    # grid
    step = _nice_step(span)
    g = (vmin // step) * step
    while g <= vmax + 1e-9:
        if g >= vmin - 1e-9:
            out.append(f'<line x1="{pl}" x2="{w-pr}" y1="{y(g):.1f}" y2="{y(g):.1f}" stroke="#E3E6EC" stroke-width="0.8"/>')
            out.append(_t(pl - 4, y(g) + 3, f"{g:g}", 8, "#5A6170", "end"))
        g += step
    if zero_line:
        out.append(f'<line x1="{pl}" x2="{w-pr}" y1="{y(0):.1f}" y2="{y(0):.1f}" stroke="#5A6170" stroke-width="1"/>')
    for i, (lab, v) in enumerate(zip(labels, values)):
        cx = pl + iw / n * (i + 0.5)
        c = (colors[i] if isinstance(colors, list) else colors) if colors else ("#13803B" if v >= 0 else "#C1121F")
        top, bot = (y(v), y(0)) if v >= 0 else (y(0), y(v))
        out.append(f'<rect x="{cx-bw/2:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{max(bot-top,0.8):.1f}" fill="{c}" rx="1"/>')
        vy = top - 3 if v >= 0 else bot + 9
        out.append(_t(cx, vy, fmt.format(v), 7.6 if n > 12 else 8.4, "#1B1F27", "middle", "700"))
        out.append(_t(cx, h - pb + 11, lab, label_size, "#5A6170", "middle"))
    if unit_note:
        out.append(_t(w - pr, 9, unit_note, 8, "#5A6170", "end"))
    out.append("</svg>")
    return "".join(out)


def hbar_chart(labels, values, *, w=340, row=17, colors=None, fmt="{:.0f}", vmax=None, label_w=96, note=""):
    """横棒（ランキング用）。"""
    pt = 12 if note else 4
    h = pt + row * len(values) + 4
    vmax = vmax or max(values) * 1.12
    iw = w - label_w - 40
    out = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img">']
    if note:
        out.append(_t(w, 9, note, 8, "#5A6170", "end"))
    for i, (lab, v) in enumerate(zip(labels, values)):
        yy = pt + i * row
        c = (colors[i] if isinstance(colors, list) else colors) or "#1D3557"
        bw = max(v / vmax * iw, 1)
        out.append(_t(label_w - 6, yy + row * 0.68, lab, 8.8, "#1B1F27", "end"))
        out.append(f'<rect x="{label_w}" y="{yy+3:.1f}" width="{bw:.1f}" height="{row-6:.1f}" fill="{c}" rx="1.5"/>')
        out.append(_t(label_w + bw + 4, yy + row * 0.68, fmt.format(v), 8.6, "#1B1F27", "start", "700"))
    out.append("</svg>")
    return "".join(out)


def ladder(levels, *, w=340, h=250, lo=None, hi=None, title_unit="円"):
    """価格の“はしご”図。levels=[(value,label,color,bold)]。縦軸=価格。"""
    vals = [lv[0] for lv in levels]
    lo = lo or min(vals) * 0.97
    hi = hi or max(vals) * 1.02
    pt, pb = 10, 10
    def y(v):
        return pt + (hi - v) / (hi - lo) * (h - pt - pb)
    axis_x = 120
    out = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img">']
    out.append(f'<line x1="{axis_x}" x2="{axis_x}" y1="{pt}" y2="{h-pb}" stroke="#5A6170" stroke-width="1.2"/>')
    for v, lab, col, bold in levels:
        yy = y(v)
        out.append(f'<line x1="{axis_x-6}" x2="{w-4}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{col}" stroke-width="{2.2 if bold else 1}" stroke-dasharray="{"" if bold else "4 3"}"/>')
        out.append(f'<circle cx="{axis_x}" cy="{yy:.1f}" r="{4 if bold else 2.8}" fill="{col}"/>')
        out.append(_t(axis_x - 10, yy + 3.5, f"{v:,.0f}", 10 if bold else 9, col, "end", "700"))
        out.append(f'<rect x="{axis_x+10}" y="{yy-8.5:.1f}" width="{w-axis_x-14}" height="13" fill="#FFFFFF" opacity="0.9"/>')
        out.append(_t(axis_x + 12, yy + 2.5, lab, 9, col if bold else "#1B1F27", "start", "700" if bold else "400"))
    out.append("</svg>")
    return "".join(out)


def scenario_bar(parts, *, w=340, h=46):
    """確率の帯グラフ。parts=[(label,pct,color)]。"""
    out = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img">']
    x = 0
    tot = sum(p for _, p, _ in parts)
    for lab, p, c in parts:
        ww = p / tot * w
        out.append(f'<rect x="{x:.1f}" y="4" width="{ww-2:.1f}" height="24" fill="{c}" rx="2"/>')
        out.append(_t(x + ww / 2, 20.5, f"{p}%", 11, "#FFFFFF", "middle", "700"))
        out.append(_t(x + ww / 2, 41, lab, 9, "#1B1F27", "middle", "700"))
        x += ww
    out.append("</svg>")
    return "".join(out)


def timeline(events, *, w=700, h=150, months=("12月", "1月", "2月", "3月"), color="#1D3557", accent="#C1121F"):
    """12/1〜3/31 のイベントタイムライン。events=[(day_index 0-120, label, important)]。
    ラベルは上下交互、さらに2段の高さを交互に使い、近い日付が重ならないようにする。"""
    pl, pr = 14, 14
    iw = w - pl - pr
    days = 121
    def x(d):
        return pl + d / days * iw
    out = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img">']
    base = h / 2
    edges = [0, 31, 62, 90, 121]
    for i, m in enumerate(months):
        out.append(f'<rect x="{x(edges[i]):.1f}" y="{base-6:.1f}" width="{x(edges[i+1])-x(edges[i])-1:.1f}" height="12" fill="{color}" opacity="{0.85 - i*0.15:.2f}"/>')
        out.append(_t((x(edges[i]) + x(edges[i + 1])) / 2, base + 3.5, m, 8.5, "#FFFFFF", "middle", "700"))
    texts = []
    for k, (d, lab, imp) in enumerate(sorted(events, key=lambda e: e[0])):
        xx = x(d)
        up = k % 2 == 0
        tier = (k // 2) % 2
        reach = 14 + tier * 26
        y1 = base - 7 if up else base + 7
        y2 = y1 - reach if up else y1 + reach
        col = accent if imp else "#5A6170"
        out.append(f'<line x1="{xx:.1f}" x2="{xx:.1f}" y1="{y1:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="1"/>')
        out.append(f'<circle cx="{xx:.1f}" cy="{y2:.1f}" r="2.4" fill="{col}"/>')
        lines = lab.split("|")
        anchor = "start" if xx < 50 else ("end" if xx > w - 50 else "middle")
        tx = xx - 3 if anchor == "start" else (xx + 3 if anchor == "end" else xx)
        for j, ln in enumerate(lines):
            ty = (y2 - 5 - (len(lines) - 1 - j) * 10) if up else (y2 + 11 + j * 10)
            texts.append(_t(tx, ty, ln, 8.2, col if imp else "#1B1F27", anchor, "700" if imp else "400",
                            'paint-order="stroke" stroke="#FFFFFF" stroke-width="3.2" stroke-linejoin="round"'))
    out.extend(texts)  # 文字は線の上に白縁付きで重ね、引き出し線が文字を横切らないようにする
    out.append("</svg>")
    return "".join(out)


def line_chart(xlabels, series, *, w=700, h=210, lo, hi, step, hlines=(), xticks=None, bands=(), pr=120):
    """折れ線。series=[(values,color,width,dash,label)]、hlines=[(value,label,color)]、bands=[(lo,hi,color,label)]。"""
    pl, pt, pb = 44, 10, 20
    n = len(xlabels)
    iw, ih = w - pl - pr, h - pt - pb
    def x(i):
        return pl + i / (n - 1) * iw
    def y(v):
        return pt + (hi - v) / (hi - lo) * ih
    out = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img">']
    for b_lo, b_hi, col, lab in bands:
        out.append(f'<rect x="{pl}" y="{y(b_hi):.1f}" width="{iw}" height="{y(b_lo)-y(b_hi):.1f}" fill="{col}" opacity="0.13"/>')
    g = lo
    while g <= hi + 1e-9:
        out.append(f'<line x1="{pl}" x2="{pl+iw}" y1="{y(g):.1f}" y2="{y(g):.1f}" stroke="#E3E6EC" stroke-width="0.8"/>')
        out.append(_t(pl - 5, y(g) + 3, f"{g:,.0f}", 8, "#5A6170", "end"))
        g += step
    for i in (xticks or range(0, n, max(1, n // 6))):
        out.append(_t(x(i), h - 6, xlabels[i], 8, "#5A6170", "middle"))
    for v, lab, col in hlines:
        out.append(f'<line x1="{pl}" x2="{pl+iw}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{col}" stroke-width="1.4" stroke-dasharray="5 3"/>')
        out.append(_t(pl + iw + 6, y(v) + 3.5, lab, 8.6, col, "start", "700"))
    for vals, col, sw, dash, lab in series:
        pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(vals) if v is not None)
        out.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-dasharray="{dash}" stroke-linejoin="round"/>')
        last = [(i, v) for i, v in enumerate(vals) if v is not None][-1]
        if lab:
            out.append(f'<circle cx="{x(last[0]):.1f}" cy="{y(last[1]):.1f}" r="3" fill="{col}"/>')
            out.append(_t(pl + iw + 6, y(last[1]) + 3.5, lab, 8.6, col, "start", "700"))
    out.append("</svg>")
    return "".join(out)


def _nice_step(span):
    for s in (1, 2, 2.5, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 5000):
        if span / s <= 6:
            return s
    return span / 5
