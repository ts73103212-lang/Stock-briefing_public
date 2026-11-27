import json
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

import pytest

from manga_pipeline.manifest import JST
from manga_pipeline.topics import build_day, caution_count, caution_note, resolve_pick

REPO = Path(__file__).resolve().parents[2]
TODAY = date(2026, 11, 27)


def _cands() -> list[dict]:
    spec = [("c1", "term", 1), ("c2", "theme", 2), ("c3", "stock", 2), ("c4", "caution", 3)]
    return [{"id": i, "title": f"題{i}", "kind": k, "difficulty": d, "summary": f"{i}の要約。",
             "hook": f"{i}の引き。", "characters": ["corgi", "mirai"]} for i, k, d in spec]


def _memos() -> dict[str, str]:
    return {f"c{n}": f"メモ{n}" for n in range(1, 5)}


def _day() -> dict:
    return build_day(datetime(2026, 11, 27, 14, 5, tzinfo=JST), _cands(), _memos(), [])[0]


def _notes() -> dict:
    return build_day(datetime(2026, 11, 27, 14, 5, tzinfo=JST), _cands(), _memos(), [])[1]


def test_caution_count_same_week_only():
    h = [{"for_date": "2026-11-24", "kind": "caution"}, {"for_date": "2026-11-26", "kind": "caution"},
         {"for_date": "2026-11-20", "kind": "caution"}, {"for_date": "2026-11-25", "kind": "term"}]
    assert caution_count(h, date(2026, 11, 27)) == 2


def test_caution_count_excludes_same_for_date():
    h = [{"for_date": "2026-11-27", "kind": "caution"}]
    assert caution_count(h, date(2026, 11, 27)) == 0


def test_caution_count_new_week_on_monday():
    h = [{"for_date": "2026-11-24", "kind": "caution"}, {"for_date": "2026-11-26", "kind": "caution"}]
    assert caution_count(h, date(2026, 11, 30)) == 0


def test_caution_note():
    h = [{"for_date": "2026-11-24", "kind": "caution"}, {"for_date": "2026-11-25", "kind": "caution"}]
    assert caution_note(h, date(2026, 11, 27)) == "今週3回目"
    assert caution_note(h[:1], date(2026, 11, 27)) is None


def test_build_day_shape():
    day, notes = build_day(datetime(2026, 11, 27, 14, 5, tzinfo=JST), _cands(), _memos(), [])
    assert day["date"] == "2026-11-27" and day["for_date"] == "2026-11-30" and day["deadline"] == "20:00"
    assert day["created_at"].startswith("2026-11-27T14:05")
    assert [c["id"] for c in day["candidates"]] == ["c1", "c2", "c3", "c4"]
    assert "caution_count_note" not in day["candidates"][3]
    assert notes == {"date": "2026-11-27", "memos": _memos()}


def test_build_day_sets_caution_note_from_history():
    h = [{"for_date": "2026-11-24", "kind": "caution"}, {"for_date": "2026-11-26", "kind": "caution"}]
    day, _ = build_day(datetime(2026, 11, 26, 14, 0, tzinfo=JST), _cands(), _memos(), h)
    assert day["candidates"][3]["caution_count_note"] == "今週3回目"   # for_date 11/27


def test_build_day_drops_note_on_non_caution():
    c = _cands(); c[0]["caution_count_note"] = "今週3回目"
    day, _ = build_day(datetime(2026, 11, 27, 14, 0, tzinfo=JST), c, _memos(), [])
    assert "caution_count_note" not in day["candidates"][0]


@pytest.mark.parametrize("mutate, word", [
    (lambda c: c.pop(), "4"),                                    # 3件
    (lambda c: c[1].update(id="c1"), "id"),                      # id の重複・順番違い
    (lambda c: c[0].update(kind="gossip"), "kind"),
    (lambda c: c[0].update(difficulty=4), "difficulty"),
    (lambda c: c[0].update(difficulty=True), "difficulty"),     # bool は数として扱わない
    (lambda c: c[0].update(title="  "), "title"),
    (lambda c: c[0].update(title="あ" * 41), "title"),
    (lambda c: c[0].update(summary="あ" * 121), "summary"),
    (lambda c: c[0].update(hook=""), "hook"),
    (lambda c: c[0].update(characters=["corgi", "tanaka"]), "characters"),
    (lambda c: c[0].update(characters=[]), "characters"),
    (lambda c: [x.update(kind="term") for x in c], "kind"),     # 4件すべて同じ kind
    (lambda c: c[2].update(summary="今が買い時の銘柄"), "推奨"),  # check_text に掛かる
])
def test_build_day_rejects(mutate, word):
    c = _cands(); mutate(c)
    with pytest.raises(ValueError, match=word):
        build_day(datetime(2026, 11, 27, 14, 0, tzinfo=JST), c, _memos(), [])


def test_build_day_needs_memo_for_each():
    m = _memos(); m["c3"] = " "
    with pytest.raises(ValueError, match="c3"):
        build_day(datetime(2026, 11, 27, 14, 0, tzinfo=JST), _cands(), m, [])


def _run(tmp_path: Path, cands: list[dict]):
    (tmp_path / "cands.json").write_text(json.dumps({"candidates": cands}, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "memos.json").write_text(json.dumps(_memos(), ensure_ascii=False), encoding="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "manga_pipeline.topics", "build-day",
         "--candidates", str(tmp_path / "cands.json"), "--memos", str(tmp_path / "memos.json"),
         "--prev", str(tmp_path / "no-such-prev.json"),
         "--day-out", str(tmp_path / "day.json"), "--notes-out", str(tmp_path / "notes.json"),
         "--made-at", "2026-11-27T14:05:00+09:00"],
        cwd=REPO, capture_output=True, text=True)


def test_cli_build_day(tmp_path):   # 書き出した2ファイルの date と、標準出力の for_date を確かめる
    r = _run(tmp_path, _cands())
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["for_date"] == "2026-11-30" and out["date"] == "2026-11-27"
    assert out["kinds"] == ["term", "theme", "stock", "caution"] and out["caution_notes"] == {}
    day = json.loads((tmp_path / "day.json").read_text(encoding="utf-8"))
    notes = json.loads((tmp_path / "notes.json").read_text(encoding="utf-8"))
    assert day["for_date"] == "2026-11-30" and day["date"] == "2026-11-27"
    assert notes["date"] == "2026-11-27" and notes["memos"] == _memos()


def test_cli_build_day_error_exit(tmp_path):   # 3件の候補で returncode 1、stderr に "4" を含む
    r = _run(tmp_path, _cands()[:3])
    assert r.returncode == 1
    assert "4" in r.stderr
    assert not (tmp_path / "day.json").exists()


def test_resolve_user_pick_with_request():
    r = resolve_pick(TODAY, _day(), {"id": "c2", "request": " PTSの時間帯も ", "free": None,
                     "picked_at": "2026-11-27T06:12:00Z"}, _notes(), [])
    assert r["mode"] == "user" and r["candidate"]["id"] == "c2" and r["memo"] == _memos()["c2"]
    assert r["request"] == "PTSの時間帯も" and r["free"] is None
    assert r["caution_cap_applies"] is False and r["notices"] == [] and r["for_date"] == "2026-11-30"


def test_resolve_free_only():
    r = resolve_pick(TODAY, _day(), {"id": None, "request": "x", "free": "ゴンダ先輩の失敗談", "picked_at": "2026-11-27T06:00:00Z"}, _notes(), [])
    assert r["mode"] == "free" and r["free"] == "ゴンダ先輩の失敗談" and r["request"] is None and r["candidate"] is None
    assert r["caution_cap_applies"] is False


def test_resolve_free_without_day():
    r = resolve_pick(TODAY, None, {"id": None, "free": "PTSの話", "picked_at": "2026-11-27T06:00:00Z"}, None, [])
    assert r["mode"] == "free"


def test_resolve_no_pick_is_auto():
    h = [{"for_date": "2026-11-24", "kind": "caution"}]
    r = resolve_pick(TODAY, _day(), None, _notes(), h)
    assert r["mode"] == "auto" and r["caution_cap_applies"] is True and r["notices"] == []
    assert r["caution_count"] == 0   # for_date 11/30 は翌週


def test_resolve_cleared_pick_is_auto():
    assert resolve_pick(TODAY, _day(), {"id": None, "request": None, "free": None}, _notes(), [])["mode"] == "auto"


def test_resolve_unknown_id_falls_back_with_notice():
    r = resolve_pick(TODAY, _day(), {"id": "c5", "picked_at": "2026-11-27T06:00:00Z"}, _notes(), [])
    assert r["mode"] == "auto" and "c5" in r["notices"][0]


def test_resolve_day_of_other_date_is_no_candidates():
    d = _day(); d["date"] = "2026-11-26"
    r = resolve_pick(TODAY, d, {"id": "c1", "picked_at": "2026-11-27T06:00:00Z"}, _notes(), [])
    assert r["mode"] == "auto" and r["notices"]


def test_resolve_pick_older_than_candidates():
    r = resolve_pick(TODAY, _day(), {"id": "c1", "picked_at": "2026-11-27T04:00:00Z"}, _notes(), [])  # 13:00 JST < 14:05
    assert r["mode"] == "auto" and "作り直" in r["notices"][0]


def test_resolve_id_wins_over_free():
    r = resolve_pick(TODAY, _day(), {"id": "c3", "free": "別の話", "picked_at": "2026-11-27T06:00:00Z"}, _notes(), [])
    assert r["mode"] == "user" and r["free"] is None and r["notices"]


def test_resolve_blank_strings_are_none():
    r = resolve_pick(TODAY, _day(), {"id": None, "request": "  ", "free": " \n", "picked_at": "2026-11-27T06:00:00Z"}, _notes(), [])
    assert r["mode"] == "auto"


def test_resolve_memo_missing_is_none():
    r = resolve_pick(TODAY, _day(), {"id": "c1", "picked_at": "2026-11-27T06:00:00Z"}, None, [])
    assert r["mode"] == "user" and r["memo"] is None


def test_resolve_warns_on_advice_words():
    r = resolve_pick(TODAY, _day(), {"id": None, "free": "今が買い時の株を教えて", "picked_at": "2026-11-27T06:00:00Z"}, _notes(), [])
    assert r["mode"] == "free" and r["warnings"]


def test_resolve_missing_picked_at_is_not_stale():
    r = resolve_pick(TODAY, _day(), {"id": "c1"}, _notes(), [])
    assert r["mode"] == "user"


def test_cli_resolve_missing_files(tmp_path):   # どのファイルも無い → returncode 0、out の mode == "auto"
    out = tmp_path / "resolved.json"
    r = subprocess.run(
        [sys.executable, "-m", "manga_pipeline.topics", "resolve",
         "--day", str(tmp_path / "no-day.json"), "--pick", str(tmp_path / "no-pick.json"),
         "--notes", str(tmp_path / "no-notes.json"), "--prev", str(tmp_path / "no-prev.json"),
         "--out", str(out), "--today", "2026-11-27"],
        cwd=REPO, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["mode"] == "auto" and doc["for_date"] == "2026-11-30"
    summary = json.loads(r.stdout)
    assert summary["mode"] == "auto" and summary["id"] is None and summary["notices"] == []
