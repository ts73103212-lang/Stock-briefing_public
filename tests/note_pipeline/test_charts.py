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


@pytest.mark.parametrize("kind", ["theme", "stock", "paid"])
def test_header_sizes_and_dark_bg(kind, tmp_path):
    out = header.render_header(kind, "テーマ", "見出しのテスト", "リード文", tmp_path / f"h_{kind}.jpg",
                               callouts=["+22%", "営業益 26億円"])
    im = Image.open(out).convert("RGB")
    assert im.size == (1920, 1005)
    r, g, b = im.getpixel((1900, 990))
    assert (r + g + b) / 3 < 110, (r, g, b)  # 暗い背景（インパクト重視）


def test_header_kinds_differ(tmp_path):
    px = {k: Image.open(header.render_header(k, "", "見出し", "", tmp_path / f"{k}.jpg")).convert("RGB").getpixel((1900, 20))
          for k in ("theme", "stock", "paid")}
    assert len(set(px.values())) == 3


def test_figures_have_no_logo(tmp_path):
    spec = {"type": "D", **COMMON, **SPECS["D"]}
    im = Image.open(charts.render(spec, tmp_path / "d.jpg", number=1)).convert("RGB")
    r, g, b = im.getpixel((1860, 1040))
    assert min(r, g, b) > 235, (r, g, b)  # 右下は背景のまま（ロゴを貼らない）


def test_title_is_large_for_phone():
    assert style.SIZES["title"] >= 34 and style.SIZES["tick"] >= 17 and style.SIZES["label"] >= 20


def test_fonts_are_static_400_700():
    paths = fonts.ensure_fonts()
    for key, weight in (("regular", 400), ("bold", 700)):
        f = TTFont(paths[key])
        assert "fvar" not in f
        assert f["OS/2"].usWeightClass == weight


def test_comparison_table_allows_missing_values(tmp_path):
    spec = {"type": "C", **COMMON, "columns": ["PER", "騰落率"],
            "rows": [{"name": "赤字社", "values": ["—", 3.0]}, {"name": "B社", "values": [20.0, None]},
                     {"name": "C社", "values": [10.0, -1.0]}], "shade_cols": [0, 1]}
    assert Image.open(charts.render(spec, tmp_path / "c.jpg", number=1)).size == (1920, 1080)


def test_price_chart_allows_missing_volume_and_sparse_dates(tmp_path):
    spec = {"type": "A", **COMMON, "dates": ["2026-07-17", "2026-08-06", "2026-09-02", "2026-11-05", "2026-11-06"],
            "close": [1500, 1800, 1850, 1919, 2076], "volume": [None, 120000, None, None, 457900],
            "annotations": [{"date": "2026-11-06", "text": "上方修正"}]}
    assert Image.open(charts.render(spec, tmp_path / "a.jpg", number=1)).size == (1920, 1080)


def test_month_labels_not_duplicated():
    import matplotlib.dates as mdates
    from datetime import datetime
    labels = charts.date_tick_labels([datetime(2026, 7, 17), datetime(2026, 11, 6)])
    assert len(labels) == len(set(labels))


def test_header_wrap_no_leading_punctuation():
    from PIL import ImageDraw, ImageFont
    f = ImageFont.truetype(str(fonts.ensure_fonts()["bold"]), 84)
    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    text = "全面安の日にストップ高、決算とガイダンスが示した次の論点は何か"
    for width in range(600, 1000, 13):
        lines = header._wrap(d, text, f, width)
        assert all(ln[:1] not in header.NO_LINE_START for ln in lines[1:]), lines


def test_header_wrap_prefers_break_after_punctuation():
    from PIL import ImageDraw, ImageFont
    f = ImageFont.truetype(str(fonts.ensure_fonts()["bold"]), 84)
    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    lines = header._balanced_wrap(d, "日経平均3,643円安の理由、中間選挙とデータセンター", f, 1002)
    assert lines[0].endswith("、")


def test_volume_tick_format():
    assert charts.fmt_volume(500000) == "50万"
    assert charts.fmt_volume(2_000_000) == "200万"
    assert charts.fmt_volume(1.2e8) == "1.2億"
    assert charts.fmt_volume(0) == "0"


def test_header_wrap_keeps_numbers_together():
    from PIL import ImageDraw, ImageFont
    f = ImageFont.truetype(str(fonts.ensure_fonts()["bold"]), 104)
    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    for width in range(500, 1100, 17):
        lines = header._wrap(d, "日経平均3,643円安の理由とSOX指数", f, width)
        assert not any(ln.endswith(("3", "3,", "3,6", "3,64")) and nxt[:1].isdigit()
                       for ln, nxt in zip(lines, lines[1:])), lines


def test_table_font_fits_cell():
    size = charts.fit_fontsize("終値前日比(%)", col_w=0.2, base=20)
    assert size < 20
    assert charts.fit_fontsize("A社", col_w=0.2, base=20) == 20


def test_header_wrap_keeps_unit_with_number():
    toks = header._TOKEN_RE.findall("日経平均3,643円安")
    assert "3,643円" in toks
