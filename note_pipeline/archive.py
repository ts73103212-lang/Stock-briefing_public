"""日次の納品ページを日付タブで残す（2026-11-24 ユーザー要望）。

1つの固定URLのページに、直近 KEEP_DAYS 日分の「その日の記事一式」を日付ごとのブロックで持つ。
翌日のタスクは前回のページ（prev.html）からブロックを取り出し、今日のブロックを足して作り直す。
記事本文はリポジトリに置かない約束なので、過去分の保管場所もページ自身にする（history と同じ方式）。

ブロックの目印は HTML コメントではなく要素にしている（読み戻しでコメントが落ちても壊れないように）:
  <div class="day" id="d-YYYY-MM-DD" data-day="YYYY-MM-DD"> … <i data-day-end="YYYY-MM-DD" hidden></i></div>
"""
from __future__ import annotations

import re
from datetime import date, timedelta

KEEP_DAYS = 14
WEEKDAYS = "月火水木金土日"

_BLOCK_RE = re.compile(
    r'<div class="day" id="d-(\d{4}-\d{2}-\d{2})" data-day="\1"[^>]*>\n?(.*?)\n?<i data-day-end="\1" hidden></i></div>',
    re.S)
_LEGACY_DATE_RE = re.compile(r'<div class="eyebrow">今日のnote ・ (\d{4})年(\d{1,2})月(\d{1,2})日</div>')
_LEGACY_BODY_RE = re.compile(r'<div class="wrap">\n(.*?)\n</div>\n<script>', re.S)


def parse_days(page_html: str) -> dict[str, str]:
    """前回ページから {日付: ブロックの中身} を取り出す。タブ化前の旧ページは1日分として取り込む。"""
    page_html = page_html or ""
    days = {m.group(1): m.group(2) for m in _BLOCK_RE.finditer(page_html)}
    if days:
        return days
    d, body = _LEGACY_DATE_RE.search(page_html), _LEGACY_BODY_RE.search(page_html)
    if d and body:
        return {date(int(d.group(1)), int(d.group(2)), int(d.group(3))).isoformat(): body.group(1)}
    return {}


def merge_days(past: dict[str, str], today: str, today_inner: str, keep_days: int = KEEP_DAYS) -> dict[str, str]:
    """今日のブロックで同じ日付を置き換え、古い日を落として新しい順に並べる。"""
    cutoff = date.fromisoformat(today) - timedelta(days=keep_days)
    out = {k: v for k, v in past.items() if date.fromisoformat(k) > cutoff}
    out[today] = today_inner
    return dict(sorted(out.items(), reverse=True))


def wrap(day_iso: str, inner: str, hidden: bool) -> str:
    h = " hidden" if hidden else ""
    return (f'<div class="day" id="d-{day_iso}" data-day="{day_iso}"{h}>\n{inner}\n'
            f'<i data-day-end="{day_iso}" hidden></i></div>')


def tab_label(day_iso: str) -> str:
    d = date.fromisoformat(day_iso)
    return f"{d.month}/{d.day}（{WEEKDAYS[d.weekday()]}）"
