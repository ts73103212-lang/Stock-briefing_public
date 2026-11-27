import hashlib
import json
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from manga_pipeline.manifest import build_manifest, next_business_day, render_index

REPO = Path(__file__).resolve().parents[2]
JST = timezone(timedelta(hours=9))
EXPL = "<p>SOX指数は米国の半導体株の指数。</p><p>※投資判断はご自身で。</p>"


def _rows(d: Path) -> list[Path]:
    d.mkdir(parents=True, exist_ok=True)
    out = []
    for k in range(1, 5):
        p = d / f"row{k}.jpg"
        p.write_bytes(f"jpeg-{k}".encode())
        out.append(p)
    return out


def test_next_business_day_weekday():
    assert next_business_day(date(2026, 11, 24)) == date(2026, 11, 25)


def test_next_business_day_friday():
    assert next_business_day(date(2026, 11, 27)) == date(2026, 11, 30)


def test_next_business_day_new_year():
    assert next_business_day(date(2026, 12, 30)) == date(2027, 1, 4)


def test_next_business_day_before_holiday():
    # 2027-02-11（木）建国記念の日 → 前日 2/10 に作った分は 2/12（金）
    assert next_business_day(date(2027, 2, 10)) == date(2027, 2, 12)


def test_manifest_sha256(tmp_path):
    rows = _rows(tmp_path)
    m = build_manifest(datetime(2026, 11, 24, 18, 40, tzinfo=JST), "SOX指数と連れ安", "term", EXPL, rows, None, picked="auto", difficulty=1)
    assert m["for_date"] == "2026-11-25"
    assert m["made_at"].startswith("2026-11-24T18:40")
    assert [r["file"] for r in m["rows"]] == ["row1.jpg", "row2.jpg", "row3.jpg", "row4.jpg"]
    for r, p in zip(m["rows"], rows):
        assert r["sha256"] == hashlib.sha256(p.read_bytes()).hexdigest()
    assert m["title"] == "SOX指数と連れ安" and m["kind"] == "term" and m["explanation_html"] == EXPL


def test_explanation_needs_disclaimer(tmp_path):
    with pytest.raises(ValueError):
        build_manifest(datetime(2026, 11, 24, 18, 0, tzinfo=JST), "t", "term", "<p>説明</p>", _rows(tmp_path), None, picked="auto", difficulty=1)


def test_rejects_unknown_kind(tmp_path):
    with pytest.raises(ValueError):
        build_manifest(datetime(2026, 11, 24, 18, 0, tzinfo=JST), "t", "gossip", EXPL, _rows(tmp_path), None, picked="auto", difficulty=1)


def test_rejects_wrong_row_count(tmp_path):
    with pytest.raises(ValueError):
        build_manifest(datetime(2026, 11, 24, 18, 0, tzinfo=JST), "t", "term", EXPL, _rows(tmp_path)[:3], None, picked="auto", difficulty=1)


def test_history_keeps_last5(tmp_path):
    prev = {"history": [{"for_date": f"2026-11-{d}", "kind": "term"} for d in (17, 18, 19, 20, 24)]}
    m = build_manifest(datetime(2026, 11, 24, 18, 0, tzinfo=JST), "t", "caution", EXPL, _rows(tmp_path), prev, picked="auto", difficulty=1)
    assert len(m["history"]) == 5
    assert m["history"][0]["for_date"] == "2026-11-18"
    assert m["history"][-1] == {"for_date": "2026-11-25", "kind": "caution", "picked": "auto", "difficulty": 1}


def test_history_replaces_same_for_date(tmp_path):
    """同じ for_date を作り直したら、履歴の同じ日を置き換える（二重に数えない）。"""
    prev = {"history": [{"for_date": "2026-11-25", "kind": "term"}]}
    m = build_manifest(datetime(2026, 11, 24, 19, 0, tzinfo=JST), "t", "theme", EXPL, _rows(tmp_path), prev, picked="auto", difficulty=1)
    assert m["history"] == [{"for_date": "2026-11-25", "kind": "theme", "picked": "auto", "difficulty": 1}]


def test_index_contains_rows(tmp_path):
    m = build_manifest(datetime(2026, 11, 24, 18, 0, tzinfo=JST), "SOX<指数>", "term", EXPL, _rows(tmp_path), None, picked="auto", difficulty=1)
    html = render_index(m)
    for k in range(1, 5):
        assert f'src="manga/row{k}.jpg"' in html
    assert "SOX&lt;指数&gt;" in html and EXPL in html and "2026-11-25" in html
    assert "Meiryo UI" in html


def test_cli(tmp_path):
    rows_dir = tmp_path / "rows"
    _rows(rows_dir)
    (tmp_path / "e.html").write_text(EXPL, encoding="utf-8")
    prev = tmp_path / "prev.json"
    prev.write_text(json.dumps({"history": [{"for_date": "2026-11-24", "kind": "caution"}]}))
    out = tmp_path / "site"
    r = subprocess.run([sys.executable, "-m", "manga_pipeline.manifest", "--title", "T", "--kind", "term",
                        "--explanation", str(tmp_path / "e.html"), "--rows", str(rows_dir), "--out", str(out),
                        "--prev", str(prev), "--made-at", "2026-11-27T18:30:00+09:00",
                        "--picked", "auto", "--difficulty", "1"],
                       cwd=REPO, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    m = json.loads((out / "manga/manifest.json").read_text(encoding="utf-8"))
    assert m["for_date"] == "2026-11-30" and len(m["history"]) == 2
    assert (out / "index.html").exists()
    assert sorted(p.name for p in (out / "manga").glob("row*.jpg")) == [f"row{k}.jpg" for k in range(1, 5)]


def test_cli_prev_missing_is_ok(tmp_path):
    rows_dir = tmp_path / "rows"
    _rows(rows_dir)
    (tmp_path / "e.html").write_text(EXPL, encoding="utf-8")
    r = subprocess.run([sys.executable, "-m", "manga_pipeline.manifest", "--title", "T", "--kind", "term",
                        "--explanation", str(tmp_path / "e.html"), "--rows", str(rows_dir),
                        "--out", str(tmp_path / "site"), "--prev", str(tmp_path / "nope.json"),
                        "--picked", "auto", "--difficulty", "1"],
                       cwd=REPO, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_index_follows_artifact_page_contract(tmp_path):
    """Artifact は公開時に doctype/html/head/body を付けるので、ページ本体だけを出す。"""
    m = build_manifest(datetime(2026, 11, 24, 18, 0, tzinfo=JST), "t", "term", EXPL, _rows(tmp_path), None, picked="auto", difficulty=1)
    html = render_index(m)
    low = html.lower()
    assert "<!doctype" not in low and "<html" not in low and "<body" not in low and "<head" not in low
    assert html.lstrip().startswith("<title>朝マンガ納品</title>")
    assert "max(16px, env(safe-area-inset-left, 0px))" in html
    assert 'name="claude:viewport-fit-sides"' in html


def test_history_records_picked_and_difficulty(tmp_path):
    m = build_manifest(datetime(2026, 11, 27, 21, 40, tzinfo=JST), "t", "term", EXPL, _rows(tmp_path), None,
                       picked="user", difficulty=2)
    assert m["history"] == [{"for_date": "2026-11-30", "kind": "term", "picked": "user", "difficulty": 2}]


def test_history_old_entries_without_picked(tmp_path):
    prev = {"history": [{"for_date": "2026-11-26", "kind": "caution"}]}
    m = build_manifest(datetime(2026, 11, 26, 21, 0, tzinfo=JST), "t", "theme", EXPL, _rows(tmp_path), prev,
                       picked="replaced", difficulty=3)
    assert m["history"][0] == {"for_date": "2026-11-26", "kind": "caution"}
    assert m["history"][1]["picked"] == "replaced"


@pytest.mark.parametrize("kw", [{"picked": "mine", "difficulty": 1}, {"picked": "auto", "difficulty": 0},
                                {"picked": "auto", "difficulty": True}])
def test_rejects_bad_picked_or_difficulty(tmp_path, kw):
    with pytest.raises(ValueError):
        build_manifest(datetime(2026, 11, 24, 18, 0, tzinfo=JST), "t", "term", EXPL, _rows(tmp_path), None, **kw)


def test_cli_requires_picked(tmp_path):
    rows_dir = tmp_path / "rows"
    _rows(rows_dir)
    (tmp_path / "e.html").write_text(EXPL, encoding="utf-8")
    r = subprocess.run([sys.executable, "-m", "manga_pipeline.manifest", "--title", "T", "--kind", "term",
                        "--explanation", str(tmp_path / "e.html"), "--rows", str(rows_dir),
                        "--out", str(tmp_path / "site"), "--difficulty", "1"],
                       cwd=REPO, capture_output=True, text=True)
    assert r.returncode != 0
    assert "--picked" in r.stderr
