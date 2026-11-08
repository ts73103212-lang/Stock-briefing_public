import json
from datetime import date

import pytest

from note_pipeline import market


@pytest.mark.parametrize("d,closed", [
    (date(2026, 11, 3), True),   # 文化の日
    (date(2026, 11, 4), False),
    (date(2026, 11, 7), True),   # 土曜
    (date(2026, 11, 8), True),   # 日曜
    (date(2027, 1, 2), True),
    (date(2026, 12, 31), True),
    (date(2026, 11, 23), True),  # 勤労感謝の日
    (date(2027, 1, 4), False),   # 大発会
])
def test_is_tse_closed(d, closed):
    assert market.is_tse_closed(d) is closed


def _write(tmp_path, fetched_at="2026-11-04 15:35 JST", status="OK", skip=()):
    for name in market.CLOSING_FILES:
        if name in skip:
            continue
        (tmp_path / name).write_text(json.dumps({"fetched_at": fetched_at, "status": status}), encoding="utf-8")


def test_freshness_all_ok(tmp_path):
    _write(tmp_path)
    assert set(market.check_closing_freshness(tmp_path, date(2026, 11, 4)).values()) == {"ok"}


def test_freshness_stale(tmp_path):
    _write(tmp_path, fetched_at="2026-11-02 15:35 JST")
    assert set(market.check_closing_freshness(tmp_path, date(2026, 11, 4)).values()) == {"stale"}


def test_freshness_missing_and_error(tmp_path):
    _write(tmp_path, status="NG", skip=("macro_result_closing.json",))
    r = market.check_closing_freshness(tmp_path, date(2026, 11, 4))
    assert r["macro_result_closing.json"] == "missing"
    assert r["screening_result_closing.json"] == "error"


def test_freshness_broken_json(tmp_path):
    _write(tmp_path)
    (tmp_path / "screening_result_closing.json").write_text("{broken", encoding="utf-8")
    assert market.check_closing_freshness(tmp_path, date(2026, 11, 4))["screening_result_closing.json"] == "error"
