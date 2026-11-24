"""朝マンガの manifest.json と、納品ページ index.html の出力（設計書 §7.6）。

CLI:
  python -m manga_pipeline.manifest --title T --kind term --explanation E.html --rows DIR --out DIR \
      [--prev 前回の manifest.json] [--made-at 2026-11-24T18:40:00+09:00]
  → DIR/index.html と DIR/manga/manifest.json を書き、row1〜4.jpg を DIR/manga/ にコピーする。
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from note_pipeline.market import is_tse_closed

JST = timezone(timedelta(hours=9))
KINDS = {"theme", "term", "stock", "caution"}   # 相場の振り返り・用語・話題の銘柄/テーマ・注意喚起
DISCLAIMER = "※投資判断はご自身で。"
HISTORY_LEN = 5
ROW_FILES = [f"row{k}.jpg" for k in range(1, 5)]


def next_business_day(d: date) -> date:
    """d の翌日以降で、最初の東証の営業日。"""
    d += timedelta(days=1)
    while is_tse_closed(d):
        d += timedelta(days=1)
    return d


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_manifest(made_at: datetime, title: str, kind: str, explanation_html: str,
                   rows: list[Path], prev: dict | None) -> dict:
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {sorted(KINDS)}: {kind!r}")
    if not title or not title.strip():
        raise ValueError("title is empty")
    if DISCLAIMER not in explanation_html:
        raise ValueError(f"explanation_html must contain {DISCLAIMER}")
    if [Path(r).name for r in rows] != ROW_FILES:
        raise ValueError(f"rows must be {ROW_FILES}")
    if made_at.tzinfo is None:
        made_at = made_at.replace(tzinfo=JST)
    for_date = next_business_day(made_at.astimezone(JST).date()).isoformat()
    history = [h for h in (prev or {}).get("history", []) if h.get("for_date") != for_date]
    history = (history + [{"for_date": for_date, "kind": kind}])[-HISTORY_LEN:]
    return {
        "for_date": for_date,
        "made_at": made_at.astimezone(JST).isoformat(timespec="minutes"),
        "title": title.strip(),
        "kind": kind,
        "rows": [{"file": Path(r).name, "sha256": _sha256(r)} for r in rows],
        "explanation_html": explanation_html,
        "history": history,
    }


def render_index(manifest: dict) -> str:
    """納品ページ（ユーザーの確認用）。画像は manga/rowN.jpg を相対参照する。"""
    title = html.escape(manifest["title"])
    imgs = "\n".join(
        f'    <img src="manga/{html.escape(r["file"])}" alt="{title} {i}段目" width="1360" height="684">'
        for i, r in enumerate(manifest["rows"], 1))
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>朝マンガ納品</title>
<style>
  :root {{ --bg: #ffffff; --fg: #1a1a1a; --muted: #5f6b7a; --rule: #e3e7ec; --accent: #1e3a5f; }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{ --bg: #15181c; --fg: #ececec; --muted: #a3adb8; --rule: #2c3238; --accent: #8fb3e0; }}
  }}
  :root[data-theme="dark"] {{ --bg: #15181c; --fg: #ececec; --muted: #a3adb8; --rule: #2c3238; --accent: #8fb3e0; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--fg);
         font-family: 'Meiryo UI', 'Noto Sans JP', sans-serif; line-height: 1.7; }}
  main {{ max-width: 680px; margin: 0 auto; padding: 20px 16px 40px; }}
  .meta {{ color: var(--muted); font-size: 13px; margin: 0 0 4px; }}
  h1 {{ font-size: 20px; margin: 0 0 14px; color: var(--accent); }}
  img {{ width: 100%; height: auto; display: block; margin: 4px 0; }}
  h2 {{ font-size: 16px; margin: 22px 0 6px; padding-top: 14px; border-top: 1px solid var(--rule); }}
  .expl p {{ margin: 0 0 10px; }}
</style>
</head>
<body>
<main>
  <p class="meta">{html.escape(manifest["for_date"])} の朝に掲載 ・ 作成 {html.escape(manifest["made_at"])} ・ {html.escape(manifest["kind"])}</p>
  <h1>🐾 コーギー先生の8コマ相場教室「{title}」</h1>
  <div class="rows">
{imgs}
  </div>
  <h2>📝 解説</h2>
  <div class="expl">{manifest["explanation_html"]}</div>
</main>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--title", required=True)
    ap.add_argument("--kind", required=True, choices=sorted(KINDS))
    ap.add_argument("--explanation", required=True, type=Path)
    ap.add_argument("--rows", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--prev", type=Path, help="前回の manifest.json（無ければ履歴なしで作る）")
    ap.add_argument("--made-at", help="ISO8601（既定は現在時刻 JST）")
    a = ap.parse_args(argv)

    made_at = datetime.fromisoformat(a.made_at) if a.made_at else datetime.now(JST)
    prev = json.loads(a.prev.read_text(encoding="utf-8")) if a.prev and a.prev.exists() else None
    rows = [a.rows / name for name in ROW_FILES]
    for r in rows:
        if not r.exists():
            raise FileNotFoundError(r)
    manifest = build_manifest(made_at, a.title, a.kind, a.explanation.read_text(encoding="utf-8"), rows, prev)
    manga_dir = a.out / "manga"
    manga_dir.mkdir(parents=True, exist_ok=True)
    for r in rows:
        if r.resolve() != (manga_dir / r.name).resolve():
            shutil.copyfile(r, manga_dir / r.name)
    (manga_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    (a.out / "index.html").write_text(render_index(manifest), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("for_date", "title", "kind")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
