"""見どころの検査とまとめ（候補出しタスクのフェーズ4）。

視点ごとの担当（数字・需給／歴史・アノマリー／海外・マクロ／統計）が書いた
`WORK/highlights/*.json` を候補ごとに集め、空の項目・売買推奨の表現・重複を外し、
「数字＋歴史か比較＋意外か反対」の3グループが先頭に来るよう並べて上限で切る。
直さず、外して並べるだけ。

    python -m note_pipeline.highlights --work WORK [--cap 6]

`WORK/day_doc.json` に見どころを足して `WORK/day_doc_hl.json` に書き、
状態と候補ごとの点数・足りないグループを JSON で標準出力に出す。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from note_pipeline.lint import check_text

FIELDS = ("headline", "evidence", "source", "type", "lens")

# 必須の3グループ（各候補に1点ずつ入れたい）。順番が表示順。
REQUIRED = {
    "数字": ("数字", "統計"),
    "歴史か比較": ("歴史の事例", "他社比較"),
    "意外か反対": ("意外な事実", "反対の見方"),
}


def group_of(type_: str) -> str | None:
    for group, types in REQUIRED.items():
        if type_ in types:
            return group
    return None


def _key(headline: str) -> str:
    return re.sub(r"[\s　、。・,.!?！？「」『』（）()]", "", headline)


def clean(items) -> list[dict]:
    """空の項目・推奨表現・見出しの重複を外す（順番は保つ）。"""
    out, seen = [], set()
    for h in items if isinstance(items, list) else []:
        if not isinstance(h, dict):
            continue
        if not all(str(h.get(k, "")).strip() for k in ("headline", "evidence", "source")):
            continue
        if check_text(f"{h['headline']} {h['evidence']}"):
            continue
        k = _key(str(h["headline"]))
        if k in seen:
            continue
        seen.add(k)
        out.append({f: str(h.get(f, "")).strip() for f in FIELDS})
    return out


def select(items: list[dict], cap: int) -> list[dict]:
    """必須3グループを1点ずつ先に取り（視点が重ならないように）、残りは視点を順番に回して埋める。"""
    pool = clean(items)
    chosen: list[dict] = []
    for group in REQUIRED:
        used = {h["lens"] for h in chosen}
        hits = [h for h in pool if group_of(h["type"]) == group]
        if hits:
            pick = next((h for h in hits if h["lens"] not in used), hits[0])
            chosen.append(pick)
            pool.remove(pick)
    lenses: dict[str, list[dict]] = {}
    for h in pool:
        lenses.setdefault(h["lens"], []).append(h)
    while len(chosen) < cap and any(lenses.values()):
        for queue in lenses.values():
            if queue and len(chosen) < cap:
                chosen.append(queue.pop(0))
    return [dict(h, id=f"h{i + 1}") for i, h in enumerate(chosen[:cap])]


def missing_groups(highlights: list[dict]) -> list[str]:
    have = {group_of(h.get("type", "")) for h in highlights}
    return [g for g in REQUIRED if g not in have]


def merge_work(work: Path, cap: int = 6) -> tuple[dict, dict]:
    raw: dict[str, list] = {}
    unreadable = []
    for f in sorted((work / "highlights").glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except Exception:
            unreadable.append(f.name)
            continue
        for cid, items in (d.items() if isinstance(d, dict) else []):
            if isinstance(items, list):
                raw.setdefault(cid, []).extend(items)
    doc = json.loads((work / "day_doc.json").read_text())
    counts, missing, n = {}, {}, 0
    for c in doc["candidates"]:
        got = select(raw.get(c["id"], []), cap)
        counts[c["id"]] = len(got)
        if got:
            c["highlights"] = got
            n += 1
            lack = missing_groups(got)
            if lack:
                missing[c["id"]] = lack
    doc["highlights_status"] = "done" if n == len(doc["candidates"]) else ("partial" if n else "failed")
    doc["highlights_at"] = datetime.now(timezone.utc).isoformat()
    return doc, {"status": doc["highlights_status"], "counts": counts, "missing": missing, "unreadable": unreadable}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--cap", type=int, default=6)
    a = ap.parse_args(argv)
    doc, report = merge_work(a.work, a.cap)
    (a.work / "day_doc_hl.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))
    json.dump(report, sys.stdout, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
