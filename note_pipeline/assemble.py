"""サブエージェントの成果物（WORK/ 配下）を day.json にまとめる。

  python -m note_pipeline.assemble --work WORK --out WORK/day.json

WORK/plan.json            PM のネタ決定（date, mode, price, meta, articles[{id, kind, …}], candidates, notes）
WORK/drafts/a{id}.json    証券アナリストの記事（page.py の記事 dict。figure_requests は除去する）
WORK/figs/a{id}.json      視覚化スペシャリストの図 spec の配列
WORK/review/verdict.json  PM の最終判定 {"a1": "approve" | "drop"}（任意）
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

KIND_NAME = {"theme": "テーマ", "stock": "注目銘柄", "paid": "有料"}
PLAN_KEYS = ("date", "mode", "price", "meta")


def _load(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def assemble(work: Path) -> dict:
    work = Path(work)
    plan = _load(work / "plan.json")
    if plan is None:
        raise FileNotFoundError(work / "plan.json")
    verdict = _load(work / "review" / "verdict.json", {}) or {}
    day = {k: plan[k] for k in PLAN_KEYS if k in plan}
    day.setdefault("mode", "daily")
    notes = list(plan.get("notes", []))
    articles = []
    for p in plan.get("articles", []):
        aid = str(p["id"])
        label = f"記事{aid}（{KIND_NAME.get(p.get('kind'), p.get('kind', ''))}）"
        draft = _load(work / "drafts" / f"a{aid}.json")
        if verdict.get(f"a{aid}") == "drop":
            notes.append(f"{label}はレビューで見送り")
            continue
        if draft is None:
            notes.append(f"{label}は未完成のため見送り")
            continue
        draft.pop("figure_requests", None)
        draft["id"] = aid
        draft.setdefault("kind", p.get("kind"))
        draft["figures"] = _load(work / "figs" / f"a{aid}.json", []) or []
        articles.append(draft)
    day["articles"] = articles
    day["candidates"] = plan.get("candidates", [])
    day["notes"] = notes
    return day


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m note_pipeline.assemble")
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)
    day = assemble(args.work)
    args.out.write_text(json.dumps(day, ensure_ascii=False, indent=1), encoding="utf-8")
    for n in day["notes"]:
        print(f"注記: {n}")
    print(f"記事 {len(day['articles'])} 本 → {args.out}")
    return 0 if day["articles"] else 1


if __name__ == "__main__":
    sys.exit(main())
