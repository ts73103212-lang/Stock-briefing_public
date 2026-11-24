from note_pipeline import archive


def test_roundtrip_and_hidden_attribute():
    html = archive.wrap("2026-11-24", "<p>a</p>", hidden=True) + archive.wrap("2026-11-25", "<p>b</p>", hidden=False)
    assert archive.parse_days(html) == {"2026-11-24": "<p>a</p>", "2026-11-25": "<p>b</p>"}


def test_merge_replaces_same_day_newest_first_and_drops_old():
    past = {"2026-11-24": "old", "2026-11-10": "x", "2026-11-11": "y"}
    out = archive.merge_days(past, "2026-11-25", "today", keep_days=14)
    assert out == {"2026-11-25": "today", "2026-11-24": "old"}
    out = archive.merge_days(past, "2026-11-24", "new", keep_days=14)
    assert out == {"2026-11-24": "new", "2026-11-11": "y"}


def test_legacy_page_imported_as_one_day():
    legacy = ('<html><body><div class="wrap">\n<div class="eyebrow">今日のnote ・ 2026年11月24日</div>\n'
              '<h1>今日のnote 1本</h1>\n<img src="img/a1_header.jpg">\n</div>\n<script>x</script></body></html>')
    days = archive.parse_days(legacy)
    assert list(days) == ["2026-11-24"]
    assert 'src="img/a1_header.jpg"' in days["2026-11-24"]


def test_no_days_in_unrelated_html():
    assert archive.parse_days("<html><head></head></html>") == {}


def test_tab_label():
    assert archive.tab_label("2026-11-24") == "11/24（火）"
