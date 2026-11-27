"""朝マンガのネタ候補（その日の4候補）の文書づくりと検証。

CLI:
  python -m manga_pipeline.topics build-day --candidates C.json --memos M.json --prev 前回の manifest.json \
      --day-out DAY.json --notes-out NOTES.json [--made-at 2026-11-27T14:05:00+09:00]
  → C.json は {"candidates": [...4件]}、M.json は {"c1": "<下調べメモ>", ...}。
    DAY.json（候補の日の文書）と NOTES.json（下調べメモ）を書き、概要を標準出力に出す。
    問題があれば1行1件で標準エラーに出し、終了コード 1。
  python -m manga_pipeline.topics resolve --day DAY.json --pick PICK.json --notes NOTES.json \
      --prev 前回の manifest.json --out RESOLVED.json [--today 2026-11-27]
  → ユーザーの選択を読み分けて RESOLVED.json に書き、{"mode","for_date","id","notices"} を標準出力に出す。
    どのファイルも無ければ None 扱い（--prev は履歴なし）。--today の既定は JST の今日。
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


def _clean(v) -> str | None:
    if not isinstance(v, str):
        return None
    v = v.strip()
    return v or None


def _is_stale(picked_at, created_at) -> bool:
    try:
        return datetime.fromisoformat(picked_at) < datetime.fromisoformat(created_at)
    except (TypeError, ValueError):
        return False   # 読めなければこの判定は飛ばす（naive と aware の比較も TypeError）


def resolve_pick(today: date, day: dict | None, pick: dict | None, notes: dict | None,
                 history: list[dict]) -> dict:
    """ユーザーの選択を user / free / auto に読み分ける。"""
    for_date = next_business_day(today)
    if not day or day.get("date") != today.isoformat():
        day = None
    pick = pick or {}
    request = _clean(pick.get("request"))
    free = _clean(pick.get("free"))
    pid = pick.get("id")
    notices: list[str] = []
    mode = "auto"
    candidate = None

    if pid:
        candidate = next((c for c in (day or {}).get("candidates", []) if c.get("id") == pid), None)
        if candidate is None:
            notices.append(f"選択した候補 {pid} が見つからないため、おまかせで描きます")
        elif _is_stale(pick.get("picked_at"), day.get("created_at")):
            candidate = None
            notices.append("候補が選択の後に作り直されたため、おまかせで描きます")
        else:
            mode = "user"
            if free:
                free = None
                notices.append("自由記述は、候補を選んだので使いません")
    elif free:
        mode = "free"
        request = None

    if mode != "user":
        request = None
    if mode != "free":
        free = None
    memo = None
    if mode == "user":
        m = (notes or {}).get("memos", {}).get(pid)
        memo = m if isinstance(m, str) else None
    warnings = []
    for text in (request, free):
        if text:
            warnings += check_text(text)
    return {
        "mode": mode,
        "for_date": for_date.isoformat(),
        "candidate": candidate if mode == "user" else None,
        "memo": memo,
        "request": request,
        "free": free,
        "caution_cap_applies": mode == "auto",
        "caution_count": caution_count(history, for_date),
        "notices": notices,
        "warnings": warnings,
    }


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _cmd_resolve(a: argparse.Namespace) -> int:
    today = date.fromisoformat(a.today) if a.today else datetime.now(JST).date()
    prev = _load(a.prev) or {}
    r = resolve_pick(today, _load(a.day), _load(a.pick), _load(a.notes), prev.get("history", []))
    a.out.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"mode": r["mode"], "for_date": r["for_date"],
                      "id": r["candidate"]["id"] if r["candidate"] else None,
                      "notices": r["notices"]}, ensure_ascii=False))
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
    r = sub.add_parser("resolve", help="ユーザーの選択を読み分ける")
    r.add_argument("--day", required=True, type=Path)
    r.add_argument("--pick", required=True, type=Path)
    r.add_argument("--notes", required=True, type=Path)
    r.add_argument("--prev", required=True, type=Path, help="前回の manifest.json（無ければ履歴なし）")
    r.add_argument("--out", required=True, type=Path)
    r.add_argument("--today", help="YYYY-MM-DD（既定は JST の今日）")
    r.set_defaults(func=_cmd_resolve)
    a = ap.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
