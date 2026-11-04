from pathlib import Path

import pytest
from fontTools.ttLib import TTFont
from PIL import Image

from note_pipeline import charts, fonts, header, style

COMMON = {"title": "出来高は平常時の9倍", "subtitle": "2026年11月4日", "source": "出典：テスト"}

SPECS = {
    "A": {"dates": [f"2026-{m:02d}-01" for m in range(5, 11)] + ["2026-11-04"],
          "close": [100, 110, 105, 120, 118, 130, 150], "volume": [1, 2, 1, 3, 2, 4, 9],
          "annotations": [{"date": "2026-11-04", "text": "決算"}]},
    "B": {"periods": ["23/3", "24/3", "25/3", "26/3予"], "sales": [100, 120, 140, 160],
          "op_income": [10, 12, 15, 20], "forecast_from": 3},
    "C": {"columns": ["PER", "時価総額(億円)", "騰落率"],
          "rows": [{"name": "A社", "values": [12.3, 1500, 5.2]}, {"name": "B社", "values": [30.1, 800, -3.1]}],
          "shade_cols": [0, 2]},
    "D": {"cards": [{"label": "日経平均", "value": "62,188円", "sub": "−893円", "tone": "down"},
                    {"label": "ドル円", "value": "152.3円", "sub": "+0.4円", "tone": "up"},
                    {"label": "SOX", "value": "7,010", "sub": "+1.2%", "tone": "up"},
                    {"label": "米上院", "value": "54:44", "sub": "民主党", "tone": "navy"}]},
    "E": {"labels": ["電気機器", "銀行", "不動産"], "values": [-2.1, 1.3, 0.4], "highlight": "電気機器"},
    "F": {"table": {"header": ["論点", "過去", "今回", "私の見方"],
                    "rows": [["①", "a", "b", "c"], ["②", "d", "e", "f"]], "emphasis_col": 3}},
}


@pytest.mark.parametrize("kind", list(SPECS))
def test_each_chart_type_renders_1920x1080_jpeg(kind, tmp_path):
    spec = {"type": kind, **COMMON, **SPECS[kind]}
    out = charts.render(spec, tmp_path / f"fig_{kind}.jpg", number=1)
    im = Image.open(out)
    assert im.format == "JPEG"
    assert im.size == (1920, 1080)


def test_diagram_boxes_variant_renders(tmp_path):
    spec = {"type": "F", **COMMON, "boxes": [{"text": "利上げ"}, {"text": "円高"}, {"text": "輸出株安"}],
            "arrows": [[0, 1], [1, 2]]}
    assert Image.open(charts.render(spec, tmp_path / "f.jpg", number=2)).size == (1920, 1080)


def test_unknown_type_raises(tmp_path):
    with pytest.raises(ValueError):
        charts.render({"type": "Z", **COMMON}, tmp_path / "x.jpg", number=1)


def test_web_search_note_in_source():
    assert "Web検索値" in style.source_text("出典：株探", web_search=True)
    assert "Web検索値" not in style.source_text("出典：株探", web_search=False)


@pytest.mark.parametrize("kind,rgb", [("theme", (0x1E, 0x3A, 0x5F)), ("stock", (0x2E, 0x8B, 0x57)),
                                      ("paid", (0xE6, 0xC4, 0x6E))])
def test_header_sizes_and_bg(kind, rgb, tmp_path):
    out = header.render_header(kind, "テーマ", "見出しのテスト", "リード文", tmp_path / f"h_{kind}.jpg")
    im = Image.open(out).convert("RGB")
    assert im.size == (1920, 1005)
    px = im.getpixel((5, 5))
    assert all(abs(a - b) < 40 for a, b in zip(px, rgb)), px


def test_fonts_are_static_400_700():
    paths = fonts.ensure_fonts()
    for key, weight in (("regular", 400), ("bold", 700)):
        f = TTFont(paths[key])
        assert "fvar" not in f
        assert f["OS/2"].usWeightClass == weight
