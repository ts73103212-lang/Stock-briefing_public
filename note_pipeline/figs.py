"""図 spec の配列を描画して確認する（視覚化スペシャリスト用）。

  python -m note_pipeline.figs --spec WORK/figs/a1.json --out WORK/figs/a1/
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import charts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m note_pipeline.figs")
    ap.add_argument("--spec", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)
    specs = json.loads(args.spec.read_text(encoding="utf-8"))
    for n, spec in enumerate(specs, 1):
        print(charts.render(spec, args.out / f"fig{n}.jpg", number=n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
