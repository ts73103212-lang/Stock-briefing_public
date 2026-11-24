"""auth.json の中の長い文字列（トークン類）を、GitHub Actions のログでマスクする。

使い方（Actions の run の中）: python manga_pipeline/mask_auth.py ~/.codex/auth.json
値は `::add-mask::<値>` の形でだけ出力する（このコマンド行自体はログに表示されない）。
"""
from __future__ import annotations

import json
import sys

MIN_LEN = 16


def _strings(v):
    if isinstance(v, dict):
        for x in v.values():
            yield from _strings(x)
    elif isinstance(v, list):
        for x in v:
            yield from _strings(x)
    elif isinstance(v, str) and len(v) >= MIN_LEN:
        yield v


def main(path: str) -> None:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for s in _strings(data):
        print(f"::add-mask::{s}")


if __name__ == "__main__":
    main(sys.argv[1])
