"""朝マンガのネタ候補（その日の4候補）の文書づくりと検証。

CLI:
  python -m manga_pipeline.topics build-day --candidates C.json --memos M.json --prev 前回の manifest.json \
      --day-out DAY.json --notes-out NOTES.json [--made-at 2026-11-27T14:05:00+09:00]
  → C.json は {"candidates": [...4件]}、M.json は {"c1": "<下調べメモ>", ...}。
    DAY.json（候補の日の文書）と NOTES.json（下調べメモ）を書き、概要を標準出力に出す。
    問題があれば1行1件で標準エラーに出し、終了コード 1。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from manga_pipeline.manifest import JST, KINDS, next_business_day
from note_pipeline.lint import check_text

DEADLINE = "20:00"
CANDIDATE_IDS = ["c1", "c2", "c3", "c4"]
CHARACTERS = {"corgi", "mirai", "gonda"}
CAUTION_CAP = 2          # 同じ週に注意喚起を出す回数の目安（これ以上は「今週N回目」と添える）
TITLE_MAX = 40
SUMMARY_MAX = 120
HOOK_MAX = 80


def _monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def caution_count(history: list[dict], for_date: date) -> int:
    """for_date と同じ週（月曜始まり）に出した注意喚起の数。for_date 当日の分は数えない。"""
    n = 0
    for h in history:
        if h.get("kind") != "caution" or not h.get("for_date"):
            continue
        d = date.fromisoformat(h["for_date"])
        if d != for_date and _monday(d) == _monday(for_date):
            n += 1
    return n


def caution_note(history: list[dict], for_date: date) -> str | None:
    count = caution_count(history, for_date)
    return f"今週{count + 1}回目" if count >= CAUTION_CAP else None


def _check_candidate(c: dict, expected_id: str) -> list[str]:
    p: list[str] = []
    if c.get("id") != expected_id:
        p.append(f"{expected_id}: id が {c.get('id')!r}（{expected_id} の順に並べる）")
    if c.get("kind") not in KINDS:
        p.append(f"{expected_id}.kind: {sorted(KINDS)} のどれか（{c.get('kind')!r}）")
    d = c.get("difficulty")
    if isinstance(d, bool) or d not in (1, 2, 3):
        p.append(f"{expected_id}.difficulty: 1〜3 の整数（{d!r}）")
    for field, limit in (("title", TITLE_MAX), ("summary", SUMMARY_MAX), ("hook", HOOK_MAX)):
        v = c.get(field)
        if not isinstance(v, str) or not v.strip():
            p.append(f"{expected_id}.{field}: 空")
            continue
        if len(v) > limit:
            p.append(f"{expected_id}.{field}: {len(v)}字（{limit}字以内）")
        p += [f"{expected_id}.{field}: {s}" for s in check_text(v)]
    ch = c.get("characters")
    if (not isinstance(ch, list) or not ch
            or not all(isinstance(x, str) and x in CHARACTERS for x in ch)):
        p.append(f"{expected_id}.characters: {sorted(CHARACTERS)} から1つ以上（{ch!r}）")
    return p


def build_day(made_at: datetime, candidates: list[dict], memos: dict[str, str],
              history: list[dict]) -> tuple[dict, dict]:
    """(候補の日の文書, 下調べメモの文書) を返す。問題は全部まとめて ValueError（1行1件）。"""
    if made_at.tzinfo is None:
        made_at = made_at.replace(tzinfo=JST)
    made_at = made_at.astimezone(JST)
    today = made_at.date()
    for_date = next_business_day(today)

    problems: list[str] = []
    if len(candidates) != len(CANDIDATE_IDS):
        problems.append(f"候補は{len(CANDIDATE_IDS)}件必要（{len(candidates)}件）")
    for cid, c in zip(CANDIDATE_IDS, candidates):
        problems += _check_candidate(c, cid)
    if len(candidates) == len(CANDIDATE_IDS) and len({c.get("kind") for c in candidates}) == 1:
        problems.append(f"kind: {len(candidates)}件すべて同じ（{candidates[0].get('kind')!r}）、混ぜる")
    for cid in CANDIDATE_IDS:
        m = memos.get(cid)
        if not isinstance(m, str) or not m.strip():
            problems.append(f"{cid}: 下調べメモが空")
    if problems:
        raise ValueError("\n".join(problems))

    note = caution_note(history, for_date)
    out = []
    for c in candidates:
        c = {k: v for k, v in c.items() if k != "caution_count_note"}
        if c["kind"] == "caution" and note is not None:
            c["caution_count_note"] = note
        out.append(c)
    day = {
        "date": today.isoformat(),
        "for_date": for_date.isoformat(),
        "deadline": DEADLINE,
        "created_at": made_at.isoformat(timespec="minutes"),
        "candidates": out,
    }
    notes = {"date": today.isoformat(), "memos": {cid: memos[cid] for cid in CANDIDATE_IDS}}
    return day, notes


def _cmd_build_day(a: argparse.Namespace) -> int:
    made_at = datetime.fromisoformat(a.made_at) if a.made_at else datetime.now(JST)
    candidates = json.loads(a.candidates.read_text(encoding="utf-8"))["candidates"]
    memos = json.loads(a.memos.read_text(encoding="utf-8"))
    prev = json.loads(a.prev.read_text(encoding="utf-8")) if a.prev.exists() else {}
    try:
        day, notes = build_day(made_at, candidates, memos, prev.get("history", []))
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    a.day_out.write_text(json.dumps(day, ensure_ascii=False, indent=1), encoding="utf-8")
    a.notes_out.write_text(json.dumps(notes, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({
        "date": day["date"], "for_date": day["for_date"],
        "kinds": [c["kind"] for c in day["candidates"]],
        "caution_notes": {c["id"]: c["caution_count_note"] for c in day["candidates"] if "caution_count_note" in c},
    }, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build-day", help="候補の日の文書と下調べメモを書く")
    b.add_argument("--candidates", required=True, type=Path)
    b.add_argument("--memos", required=True, type=Path)
    b.add_argument("--prev", required=True, type=Path, help="前回の manifest.json（無ければ履歴なし）")
    b.add_argument("--day-out", required=True, type=Path)
    b.add_argument("--notes-out", required=True, type=Path)
    b.add_argument("--made-at", help="ISO8601（既定は現在時刻 JST）")
    b.set_defaults(func=_cmd_build_day)
    a = ap.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
