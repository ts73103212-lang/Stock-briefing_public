"""売買推奨表現・文体・X投稿文の形式チェック（設計書 §2・§4.5、編集ルール 3）。

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


# 編集ルール 3（2026-11-22）: 一人称は記事全体で1回まで、AIっぽい言い回しは使わない
FIRST_PERSON = re.compile(r"私(?:は|なら|が|の|も|として|自身|たち)")
FIRST_PERSON_MAX = 1
AI_PHRASES = [
    r"と言えるでしょう", r"と言えます", r"重要なのは", r"注目すべきは", r"いかがでしょうか",
    r"まとめると", r"ではないでしょうか", r"まさに", r"という点です", r"[—―]",
]


def check_style(text: str) -> list[str]:
    """本文（タグを除いた文字）の文体の警告。"""
    text = text or ""
    problems = []
    n = len(FIRST_PERSON.findall(text))
    if n > FIRST_PERSON_MAX:
        problems.append(f"一人称「私」が{n}回（記事全体で{FIRST_PERSON_MAX}回まで。普通の解説調に言い換える）")
    for pat in AI_PHRASES:
        for m in re.finditer(pat, text):
            s = max(0, m.start() - 12)
            problems.append(f"AIっぽい言い回し「{m.group(0)}」: …{text[s:m.end() + 12]}…")
    return problems
