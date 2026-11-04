"""注目銘柄の執筆履歴（直近14日の除外判定、設計書 §4.1-3）。

履歴は納品ページの <meta name="note-pipeline:history"> に JSON で埋め込み、
翌日のタスクが前回のページを読んで引き継ぐ。リポジトリには保存しない。
"""
from __future__ import annotations

import html
import json
import re
from datetime import date, timedelta

HISTORY_META = "note-pipeline:history"
_META_RE = re.compile(r'<meta\s+name="' + re.escape(HISTORY_META) + r'"\s+content="([^"]*)"\s*/?>')


def parse_history(page_html: str) -> dict[str, list[str]]:
    m = _META_RE.search(page_html or "")
    if not m:
        return {}
    try:
        data = json.loads(html.unescape(m.group(1)))
    except ValueError:
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): [str(c) for c in v] for k, v in data.items() if isinstance(v, list)}


def update_history(hist: dict[str, list[str]], today: date, codes: list[str],
                   keep_days: int = 14) -> dict[str, list[str]]:
    cutoff = today - timedelta(days=keep_days)
    out = {k: list(v) for k, v in hist.items() if date.fromisoformat(k) >= cutoff}
    if codes:
        merged = out.get(today.isoformat(), []) + [c for c in codes if c not in out.get(today.isoformat(), [])]
        out[today.isoformat()] = merged
    return dict(sorted(out.items()))


def recent_codes(hist: dict[str, list[str]], today: date, days: int = 14) -> set[str]:
    cutoff = today - timedelta(days=days)
    return {c for k, v in hist.items() if cutoff <= date.fromisoformat(k) <= today for c in v}


def meta_tag(hist: dict[str, list[str]]) -> str:
    payload = json.dumps(hist, ensure_ascii=False, sort_keys=True)
    return f'<meta name="{HISTORY_META}" content="{html.escape(payload, quote=True)}">'
