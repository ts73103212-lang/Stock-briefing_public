import json
from pathlib import Path

from note_pipeline import page

FIX = Path(__file__).parent / "fixtures"


def load(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def names(day, mode):
    return page.image_names(day, mode)


def test_daily_renders_three_cards_and_index():
    day = load("daily_sample.json")
    html = page.render_daily(day, names(day, "daily"), "")
    for i in (1, 2, 3):
        assert f'id="a{i}"' in html
        assert f'href="#a{i}"' in html
    assert 'src="img/a1_fig1.jpg"' in html
    assert 'src="img/a2_header.jpg"' in html
    assert "選外ダミーA" in html and "材料が裏付けできない" in html
    assert "ダミーの注記" in html


def test_daily_with_one_article():
    day = load("daily_sample.json")
    day["articles"] = day["articles"][:1]
    html = page.render_daily(day, names(day, "daily"), "")
    assert html.count('class="card"') == 1
    assert html.count('class="toc-item"') == 1
    assert "1本" in html


def test_titles_escaped():
    day = load("daily_sample.json")
    day["articles"][0]["titles"][0] = 'A<b>&"'
    day["articles"][0]["xposts"][0] = "<script>x</script>"
    html = page.render_daily(day, names(day, "daily"), "")
    assert "A&lt;b&gt;&amp;&quot;" in html
    assert "<script>x</script>" not in html
    assert "<b>ダミーの強調</b>" in html  # 本文 HTML はそのまま


def test_fig_marker_replaced():
    day = load("daily_sample.json")
    html = page.render_daily(day, names(day, "daily"), "")
    assert "<!--fig:" not in html
    assert "［図①：ダミー指標］" in html


def test_paid_has_paywall_and_disclaimer_kept():
    day = load("paid_sample.json")
    html = page.render_paid(day, names(day, "paid"))
    assert 'class="paywall"' in html
    assert "🐾投資判断はご自身で🐾" in html
    assert 'src="img/header.jpg"' in html and 'src="img/fig2.jpg"' in html
    assert "300円（案）" in html


def test_no_bulk_download():
    for f, mode in (("daily_sample.json", "daily"), ("paid_sample.json", "paid")):
        day = load(f)
        html = page.render(day, mode, names(day, mode), "")
        assert "一括ダウンロード" not in html
        assert "download" not in html.lower()


def test_history_meta_embedded():
    day = load("daily_sample.json")
    html = page.render_daily(day, names(day, "daily"), '<meta name="note-pipeline:history" content="{}">')
    assert 'name="note-pipeline:history"' in html.split("</head>")[0]
