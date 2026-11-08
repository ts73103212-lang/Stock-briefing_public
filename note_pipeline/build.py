"""day.json から図・見出し画像・納品ページを作る CLI。

  python -m note_pipeline.build --input day.json --out OUTDIR [--mode daily|paid] [--prev-page prev.html]

OUTDIR に index.html と img/*.jpg を出力する。推奨表現・X投稿文の形式・免責文の
欠落を検出したら stderr に出して終了コード 2（出力はそのまま行う）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

from . import charts, header, history, lint, page

DISCLAIMER = "投資判断はご自身で"
_TAG_RE = re.compile(r"<[^>]+>")


def _check_article(a: dict) -> list[str]:
    where = f"記事{a['id']}"
    problems = []
    texts = list(a.get("titles", [])) + [a.get("summary", ""), _TAG_RE.sub("", a.get("body_html", ""))]
    for t in texts:
        problems += [f"{where}: {p}" for p in lint.check_text(t)]
    for i, x in enumerate(a.get("xposts", []), 1):
        problems += [f"{where} X案{i}: {p}" for p in lint.check_xpost(x)]
    if DISCLAIMER not in a.get("body_html", ""):
        problems.append(f"{where}: 末尾の免責文「🐾投資判断はご自身で🐾」がありません")
    return problems


def build(day: dict, out: Path, mode: str, prev_page: Path | None = None) -> list[str]:
    out = Path(out)
    img_dir = out / "img"
    img_dir.mkdir(parents=True, exist_ok=True)
    names = page.image_names(day, mode)
    problems: list[str] = []
    for a in day["articles"]:
        n = names[str(a["id"])]
        h = a.get("header", {})
        header.render_header(a["kind"], a.get("label", ""), h.get("title") or a["titles"][0], h.get("lead", ""),
                             img_dir / n["header"], callouts=h.get("callouts"))
        for k, spec in enumerate(a.get("figures", []), 1):
            charts.render(spec, img_dir / n["figs"][k - 1], number=k)
        problems += _check_article(a)
    prev_html = prev_page.read_text(encoding="utf-8") if prev_page else ""
    today = date.fromisoformat(day["date"])
    codes = [c for a in day["articles"] if a["kind"] == "stock" for c in a.get("codes", [])]
    hist = history.update_history(history.parse_history(prev_html), today, codes)
    items = [{"kind": a["kind"], "title": a["titles"][0], "summary": a.get("summary", "")} for a in day["articles"]]
    dig = history.update_digest(history.parse_meta(prev_html, history.DIGEST_META), today, items)
    meta = "\n".join(t for t in (history.meta_tag(hist) if hist else "",
                                  history.meta_tag(dig, name=history.DIGEST_META) if dig else "") if t)
    (out / "index.html").write_text(page.render(day, mode, names, meta), encoding="utf-8")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m note_pipeline.build")
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--mode", choices=("daily", "paid"))
    ap.add_argument("--prev-page", type=Path)
    args = ap.parse_args(argv)
    day = json.loads(args.input.read_text(encoding="utf-8"))
    mode = args.mode or day.get("mode", "daily")
    if not day.get("articles"):
        print("articles が空です", file=sys.stderr)
        return 1
    problems = build(day, args.out, mode, args.prev_page)
    for p in problems:
        print(f"警告: {p}", file=sys.stderr)
    print(f"出力: {args.out / 'index.html'}（{len(day['articles'])}本）")
    return 2 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
