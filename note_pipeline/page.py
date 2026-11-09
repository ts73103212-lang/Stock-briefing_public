"""納品ページ（非公開アーティファクト）の HTML を作る（設計書 §6）。

雛形は初回有料記事（中間選挙）の納品ページ。日次ページはその記事ブロックを
1〜3本並べ、冒頭に一覧、末尾に選外のネタ候補を置く。

記事 dict のキー:
  id, kind("theme"|"stock"|"paid"), label, titles[3], summary, header{title, lead},
  body_html（<!--fig:N--> で図の位置、<!--paywall--> で有料エリア境界）,
  figures[chart spec], xposts[2], sources[{label,url}], notes[str], codes[str]（注目銘柄のみ）
"""
from __future__ import annotations

import re
from datetime import date
from html import escape
from pathlib import Path

from .style import circled

TEMPLATES = Path(__file__).parent / "templates"
FONTS_LINK = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
              'family=Noto+Sans+JP:wght@400;700&family=Noto+Serif+JP:wght@700&display=swap">')
KIND_LABEL = {"theme": "テーマ", "stock": "注目銘柄", "paid": "有料"}
_FIG_RE = re.compile(r"<!--\s*fig:(\d+)\s*-->")
_PAYWALL_RE = re.compile(r"<!--\s*paywall\s*-->")
PAYWALL_HTML = '<div class="paywall">― ここから有料（noteの「有料エリア指定」をこの位置に）―</div>'


def _e(s) -> str:
    return escape(str(s), quote=True)


def jp_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.year}年{d.month}月{d.day}日"


def image_names(day: dict, mode: str) -> dict[str, dict]:
    """記事 id → {"header": ファイル名, "figs": [ファイル名…]}。有料は試作と同じ header.jpg / fig{n}.jpg。"""
    out = {}
    for a in day["articles"]:
        prefix = "" if mode == "paid" else f"a{a['id']}_"
        out[str(a["id"])] = {
            "header": f"{prefix}header.jpg",
            "figs": [f"{prefix}fig{n}.jpg" for n in range(1, len(a.get("figures", [])) + 1)],
        }
    return out


def body_with_figures(a: dict, names: dict) -> str:
    figs = a.get("figures", [])

    def fig(m: re.Match) -> str:
        n = int(m.group(1))
        if n < 1 or n > len(figs):
            return f"<p>［図{circled(n)}］</p>"
        f = figs[n - 1]
        alt = f"図{circled(n)}：{f.get('title', '')}"
        if f.get("alt"):
            alt += f"。{f['alt']}"
        return (f"<p>［図{circled(n)}：{_e(f.get('title', ''))}］</p>\n"
                f'<figure><img src="img/{names["figs"][n - 1]}" alt="{_e(alt)}" loading="lazy">'
                f"<figcaption>図{circled(n)}</figcaption></figure>")

    body = _PAYWALL_RE.sub(PAYWALL_HTML, _FIG_RE.sub(fig, a["body_html"]))
    return add_section_dividers(body)


_H2_RE = re.compile(r"(?=<h2[\s>])")


def add_section_dividers(body: str) -> str:
    """節（h2）の前に区切り線を入れる（2026-11-09 ユーザー指示）。本文の先頭が h2 のときは入れない。"""
    parts = _H2_RE.split(body)
    out = parts[0]
    for part in parts[1:]:
        out += ("<hr>\n" if out.strip() else "") + part
    return out


def _article_block(a: dict, names: dict, heading_tag: str = "h2") -> str:
    aid = _e(a["id"])
    titles = "\n".join(
        f'<div class="row"><p id="t{aid}-{i}">{_e(t)}</p><button data-copy="t{aid}-{i}">コピー</button></div>'
        for i, t in enumerate(a.get("titles", []), 1))
    xposts = "\n".join(
        f'<div class="row"><pre class="xpost" id="x{aid}-{i}">{_e(x)}</pre>'
        f'<button data-copy="x{aid}-{i}">コピー</button></div>'
        for i, x in enumerate(a.get("xposts", []), 1))
    sources = "\n".join(
        f'<li><a href="{_e(s["url"])}" target="_blank" rel="noopener">{_e(s["label"])}</a></li>' if s.get("url")
        else f"<li>{_e(s['label'])}</li>" for s in a.get("sources", []))
    notes = "\n".join(f"<li>{_e(n)}</li>" for n in a.get("notes", []))
    hdr_alt = _e(f"見出し画像：{a.get('header', {}).get('title', '')}")
    prop = a.get("header_proposal") or {}
    proposal = ""
    if prop.get("prompt"):
        proposal = f"""
  <section class="panel">
    <{heading_tag} class="ph">見出し画像の提案（画像生成AI用）</{heading_tag}>
    <p class="note">{_e(prop.get('concept', ''))}</p>
    <div class="row"><pre class="xpost" id="hp{aid}">{_e(prop['prompt'])}</pre><button data-copy="hp{aid}">コピー</button></div>
  </section>"""
    return f"""
  <section class="panel">
    <{heading_tag} class="ph">タイトル案</{heading_tag}>
    {titles}
  </section>
  <section class="panel">
    <{heading_tag} class="ph">見出し画像（note推奨 1280×670）</{heading_tag}>
    <img src="img/{names['header']}" alt="{hdr_alt}">
    <p class="hint">仮の見出し画像です。長押し（PCは右クリック）で保存できます。</p>
  </section>{proposal}
  <div class="bar">
    <button class="primary" data-copy-body="body{aid}" data-status="st{aid}">本文をコピー（見出し・太字つき）</button>
    <button data-copy-plain="body{aid}" data-status="st{aid}">プレーンテキストでコピー</button>
    <span class="status" id="st{aid}" role="status"></span>
  </div>
  <article id="body{aid}">
{body_with_figures(a, names)}
  </article>
  <section class="panel">
    <{heading_tag} class="ph">X投稿文（noteのURLを末尾に足してください）</{heading_tag}>
    {xposts}
  </section>
  <details class="panel">
    <summary>使った材料と出典（事実確認用）</summary>
    <ul>
{sources}
{notes}
    </ul>
  </details>"""


def _document(title: str, history_meta: str, content: str) -> str:
    css = (TEMPLATES / "page.css").read_text(encoding="utf-8")
    js = (TEMPLATES / "page.js").read_text(encoding="utf-8")
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{_e(title)}</title>
{history_meta}
{FONTS_LINK}
<style>
{css}
</style>
</head>
<body>
<div class="wrap">
{content}
</div>
<script>
{js}
</script>
</body>
</html>
"""


def render_paid(day: dict, img_names: dict, history_meta: str = "") -> str:
    a = day["articles"][0]
    names = img_names[str(a["id"])]
    eyebrow = f"有料記事 ・ {_e(day.get('price', '100〜300円'))} ・ {jp_date(day['date'])}作成"
    meta = f'<p class="meta">{_e(day["meta"])}図はタップ（スマホは長押し）で保存し、本文の［図○］の位置に貼ってください。</p>' \
        if day.get("meta") else ""
    content = f"""<div class="eyebrow">{eyebrow}</div>
<h1>{_e(a['header'].get('title') or a['titles'][0])}</h1>
{meta}
{_article_block(a, names)}"""
    return _document(a["header"].get("title") or a["titles"][0], history_meta, content)


def render_daily(day: dict, img_names: dict, history_meta: str) -> str:
    arts = day["articles"]
    toc = "\n".join(
        f'<li class="toc-item"><a href="#a{_e(a["id"])}"><img src="img/{img_names[str(a["id"])]["header"]}" alt="">'
        f'<div><span class="kind kind-{_e(a["kind"])}">{_e(KIND_LABEL.get(a["kind"], a["kind"]))}</span>'
        f'<b>{_e(a["titles"][0])}</b><span>{_e(a.get("summary", ""))}</span></div></a></li>'
        for a in arts)
    notices = "\n".join(f'<p class="notice">{_e(n)}</p>' for n in day.get("notes", []))
    cards = "\n".join(
        f"""<section class="card" id="a{_e(a['id'])}" aria-labelledby="h{_e(a['id'])}">
  <span class="kind kind-{_e(a['kind'])}">{_e(a.get('label') or KIND_LABEL.get(a['kind'], ''))}</span>
  <h2 id="h{_e(a['id'])}">{i}. {_e(a['titles'][0])}</h2>
  {_article_block(a, img_names[str(a['id'])], heading_tag='h3')}
</section>""" for i, a in enumerate(arts, 1))
    cands = day.get("candidates", [])
    cand_html = ""
    if cands:
        items = "\n".join(f"<li>{_e(c['title'])}<br><span>{_e(c.get('reason', ''))}</span></li>" for c in cands)
        cand_html = f'<section class="panel"><h2>選外のネタ候補</h2><ol class="cands">{items}</ol></section>'
    jd = jp_date(day["date"])
    content = f"""<div class="eyebrow">今日のnote ・ {jd}</div>
<h1>今日のnote {len(arts)}本</h1>
<p class="meta">各記事の「本文をコピー」で note に貼り付け、図は［図○］の位置に差し込んでください。画像は長押し（PCは右クリック）で保存できます。</p>
{notices}
<ul class="toc">
{toc}
</ul>
{cards}
{cand_html}"""
    return _document(f"今日のnote {jd}", history_meta, content)


def render(day: dict, mode: str, img_names: dict, history_meta: str = "") -> str:
    if mode == "paid":
        return render_paid(day, img_names, history_meta)
    return render_daily(day, img_names, history_meta)
