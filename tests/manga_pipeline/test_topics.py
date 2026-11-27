import json
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

import pytest

from manga_pipeline.manifest import JST
from manga_pipeline.topics import build_day, caution_count, caution_note

REPO = Path(__file__).resolve().parents[2]


def _cands() -> list[dict]:
    spec = [("c1", "term", 1), ("c2", "theme", 2), ("c3", "stock", 2), ("c4", "caution", 3)]
    return [{"id": i, "title": f"題{i}", "kind": k, "difficulty": d, "summary": f"{i}の要約。",
             "hook": f"{i}の引き。", "characters": ["corgi", "mirai"]} for i, k, d in spec]


def _memos() -> dict[str, str]:
    return {f"c{n}": f"メモ{n}" for n in range(1, 5)}


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
