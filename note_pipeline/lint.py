"""売買推奨表現とX投稿文の形式チェック（設計書 §2・§4.5）。

検出は「警告」。最終判断は書き手（定期タスクの Claude）が文脈で行う。
"""
from __future__ import annotations

import re

BANNED = [
    r"買い推奨", r"売り推奨", r"買い場", r"買い時", r"今が買い", r"買いです", r"買うべき", r"売るべき",
    r"目標株価", r"損切", r"利確", r"推奨", r"今がチャンス", r"必ず上がる", r"確実に上がる",
]
# 免責文など、否定・説明として使う定型句は除外する
ALLOWED = [r"推奨するものではありません", r"推奨するものではない", r"推奨はしません"]
X_MAX_CHARS = 140
X_MAX_TAGS = 2
_TAG_RE = re.compile(r"[#＃][^\s#＃]+")


def check_text(text: str) -> list[str]:
    cleaned = text or ""
    for pat in ALLOWED:
        cleaned = re.sub(pat, "", cleaned)
    problems = []
    for pat in BANNED:
        for m in re.finditer(pat, cleaned):
            s = max(0, m.start() - 12)
            problems.append(f"推奨表現「{m.group(0)}」: …{cleaned[s:m.end() + 12]}…")
    return problems


def check_xpost(text: str) -> list[str]:
    problems = []
    if len(text) > X_MAX_CHARS:
        problems.append(f"X投稿文が{len(text)}字（{X_MAX_CHARS}字以内）")
    tags = _TAG_RE.findall(text)
    if len(tags) > X_MAX_TAGS:
        problems.append(f"ハッシュタグが{len(tags)}個（{X_MAX_TAGS}個まで）")
    return problems + check_text(text)
