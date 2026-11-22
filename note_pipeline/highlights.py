"""見どころの検査とまとめ（候補出しタスクのフェーズ4）。

視点ごとの担当（数字・需給／歴史・アノマリー／海外・マクロ／統計／技術）が書いた
`WORK/highlights/*.json` を候補ごとに集め、空の項目・売買推奨の表現・重複を外し、
「数字＋歴史か比較＋意外か反対」の3グループが先頭に来るよう並べて上限で切る。
直さず、外して並べるだけ。

    python -m note_pipeline.highlights --work WORK [--cap 8] [--min-points 5 --min-keep 5]

`WORK/day_doc.json` に見どころを足して `WORK/day_doc_hl.json` に書き、
状態と候補ごとの点数・足りないグループを JSON で標準出力に出す。

`--min-points` を付けると、見どころがその点数に満たない候補を PM の順位（`rank`、
小さいほど上位）の低いものから外す。ただし `--min-keep` 本は必ず残す（足りなければ、
外した候補のうち見どころが2点以上のものを優先し、順位の高い順に戻す）。
外した候補は `dropped` に残す（2026-11-22 ユーザー指示: 平日は7本から5点未満を削る）。
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


def _rank(c: dict, i: int) -> tuple[int, int]:
    r = c.get("rank")
    return (r if isinstance(r, int) else 999, i)


def prune(candidates: list[dict], counts: dict[str, int], min_points: int, min_keep: int) -> tuple[list[dict], list[dict]]:
    """見どころが min_points 点未満の候補を外す。min_keep 本は必ず残す。並び順は元のまま。"""
    if min_points <= 0:
        return candidates, []
    order = sorted(range(len(candidates)), key=lambda i: _rank(candidates[i], i))
    keep = {i for i in order if counts.get(candidates[i]["id"], 0) >= min_points}
    if len(keep) < min_keep:
        rest = [i for i in order if i not in keep]
        rest.sort(key=lambda i: (counts.get(candidates[i]["id"], 0) <= 1, _rank(candidates[i], i)))
        keep |= set(rest[: min_keep - len(keep)])
    kept = [c for i, c in enumerate(candidates) if i in keep]
    dropped = [{"id": c["id"], "title": c.get("title", ""), "count": counts.get(c["id"], 0)}
               for i, c in enumerate(candidates) if i not in keep]
    return kept, dropped


def merge_work(work: Path, cap: int = 6, min_points: int = 0, min_keep: int = 5) -> tuple[dict, dict]:
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
    doc["candidates"], dropped = prune(doc["candidates"], counts, min_points, min_keep)
    if dropped:
        doc["dropped"] = dropped
    kept_ids = {c["id"] for c in doc["candidates"]}
    n = sum(1 for c in doc["candidates"] if c.get("highlights"))
    missing = {k: v for k, v in missing.items() if k in kept_ids}
    doc["highlights_status"] = "done" if n == len(doc["candidates"]) else ("partial" if n else "failed")
    doc["highlights_at"] = datetime.now(timezone.utc).isoformat()
    short = [c["id"] for c in doc["candidates"] if min_points > 0 and counts.get(c["id"], 0) < min_points]
    return doc, {"status": doc["highlights_status"], "counts": counts, "missing": missing,
                 "dropped": dropped, "kept_below_min": short, "unreadable": unreadable}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--cap", type=int, default=6)
    ap.add_argument("--min-points", type=int, default=0, help="これ未満の候補を外す（0=外さない）")
    ap.add_argument("--min-keep", type=int, default=5, help="外しても必ず残す本数")
    a = ap.parse_args(argv)
    doc, report = merge_work(a.work, a.cap, a.min_points, a.min_keep)
    (a.work / "day_doc_hl.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))
    json.dump(report, sys.stdout, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
