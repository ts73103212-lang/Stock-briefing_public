import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from manga_pipeline.compose import (BUBBLE_MARGIN, PANEL, bubble_box, compose_rows, wrap_lines)

REPO = Path(__file__).resolve().parents[2]


def test_wrap_ok():
    t = "一二三四五六七八九十一二\n一二三四五六七八九十一二\n一二三四五六七八九十一二"
    assert wrap_lines(t) == ["一二三四五六七八九十一二"] * 3


def test_wrap_too_long():
    with pytest.raises(ValueError):
        wrap_lines("一二三四五六七八九十一二三")


def test_wrap_too_many_lines():
    with pytest.raises(ValueError):
        wrap_lines("あ\nい\nう\nえ")


def test_wrap_mixed_width():
    assert wrap_lines("SOX指数-10.7%で\n連れ安") == ["SOX指数-10.7%で", "連れ安"]


def test_wrap_rejects_empty():
    with pytest.raises(ValueError):
        wrap_lines("")


@pytest.mark.parametrize("x", [0.0, 0.5, 1.0])
def test_bubble_inside_panel(x):
    l, t, r, b = bubble_box(408, 118, x)
    assert l >= BUBBLE_MARGIN and t >= BUBBLE_MARGIN
    assert r <= PANEL - BUBBLE_MARGIN and b <= PANEL
    assert r - l == 408 + 48


def test_bubble_centered_on_speaker():
    l, _, r, _ = bubble_box(200, 34, 0.5)
    assert abs((l + r) / 2 - PANEL / 2) <= 1


def _script(text="先生！日経平均が\n5％も下がってます…！"):
    panels = []
    for n in range(1, 9):
        bubbles = [{"speaker": "mirai", "text": text, "x": 0.3}]
        if n == 2:
            bubbles.append({"speaker": "corgi", "text": "落ち着くワン", "x": 0.8})
        panels.append({"n": n, "bubbles": bubbles})
    return {"title": "テスト", "panels": panels}


def _panels(d: Path, skip=None):
    d.mkdir(parents=True, exist_ok=True)
    for n in range(1, 9):
        if n != skip:
            Image.new("RGB", (1024, 1024), (200 + n * 5, 220, 240)).save(d / f"p{n}.png")
    return d


def test_compose_rows_size(tmp_path):
    rows = compose_rows(_script(), _panels(tmp_path / "panels"), tmp_path / "out")
    assert [p.name for p in rows] == ["row1.jpg", "row2.jpg", "row3.jpg", "row4.jpg"]
    for p in rows:
        with Image.open(p) as im:
            assert im.size == (1360, 684) and im.format == "JPEG"
        assert p.stat().st_size <= 200 * 1024


def test_compose_draws_bubble(tmp_path):
    rows = compose_rows(_script(), _panels(tmp_path / "panels"), tmp_path / "out")
    with Image.open(rows[0]) as im:
        px = im.convert("RGB").getpixel((12 + int(0.3 * PANEL), 12 + 14 + 8))
    assert min(px) > 240   # 吹き出しの中は白


def test_rejects_missing_panel(tmp_path):
    with pytest.raises(FileNotFoundError):
        compose_rows(_script(), _panels(tmp_path / "panels", skip=5), tmp_path / "out")


def test_rejects_overlong_text_before_composing(tmp_path):
    out = tmp_path / "out"
    with pytest.raises(ValueError):
        compose_rows(_script("一二三四五六七八九十一二三"), _panels(tmp_path / "panels"), out)
    assert not list(out.glob("*.jpg")) if out.exists() else True


@pytest.mark.parametrize("mutate", [
    lambda s: s["panels"].pop(),                                   # 7コマ
    lambda s: s["panels"][0].update(bubbles=[]),                   # 吹き出し0
    lambda s: s["panels"][0]["bubbles"].extend([{"speaker": "mirai", "text": "a", "x": 0.1}] * 2),
    lambda s: s["panels"][0]["bubbles"][0].update(x=1.5),          # x 範囲外
    lambda s: s["panels"][0]["bubbles"][0].update(speaker="bob"),
], ids=["seven", "no_bubble", "three_bubbles", "x_out", "speaker"])
def test_rejects_bad_script(tmp_path, mutate):
    s = _script()
    mutate(s)
    with pytest.raises(ValueError):
        compose_rows(s, _panels(tmp_path / "panels"), tmp_path / "out")


def test_cli(tmp_path):
    sf = tmp_path / "script.json"
    sf.write_text(json.dumps(_script(), ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([sys.executable, "-m", "manga_pipeline.compose", "--script", str(sf),
                        "--panels", str(_panels(tmp_path / "p")), "--out", str(tmp_path / "o")],
                       cwd=REPO, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert len(list((tmp_path / "o").glob("row*.jpg"))) == 4
