"""材料の前提チェック: 東証休場日と、引けJSONの鮮度（設計書 §4.1・§8）。"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import jpholiday

CLOSING_FILES = (
    "screening_result_closing.json",
    "screening_stophigh_closing.json",
    "macro_result_closing.json",
)


def is_tse_closed(d: date) -> bool:
    """土日・祝日（振替休日含む）・年末年始（12/31〜1/3）なら True。"""
    if d.weekday() >= 5:
        return True
    if (d.month, d.day) in {(12, 31), (1, 1), (1, 2), (1, 3)}:
        return True
    return bool(jpholiday.is_holiday(d))


def check_closing_freshness(repo_dir: Path, today: date) -> dict[str, str]:
    """各引けJSONの状態を "ok" / "stale" / "missing" / "error" で返す。

    ok 以外のファイルは、Web検索で補完し図に「Web検索値」と明記する（§8）。
    """
    result: dict[str, str] = {}
    for name in CLOSING_FILES:
        path = Path(repo_dir) / name
        if not path.exists():
            result[name] = "missing"
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            result[name] = "error"
            continue
        if data.get("status") != "OK":
            result[name] = "error"
        elif not str(data.get("fetched_at", "")).startswith(today.isoformat()):
            result[name] = "stale"
        else:
            result[name] = "ok"
    return result
