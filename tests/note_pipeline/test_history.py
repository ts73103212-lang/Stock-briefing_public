from datetime import date

from note_pipeline import history


def test_roundtrip_through_meta_tag():
    h = {"2026-11-04": ["6857", "8035"], "2026-11-03": ["593A"]}
    html = f"<html><head>{history.meta_tag(h)}</head><body></body></html>"
    assert history.parse_history(html) == h


def test_no_meta_returns_empty():
    assert history.parse_history("<html><body>なし</body></html>") == {}


def test_update_drops_old_entries():
    h = {"2026-10-15": ["1111"], "2026-10-25": ["2222"]}
    out = history.update_history(h, date(2026, 11, 4), ["3333"])
    assert "2026-10-15" not in out          # 20日前
    assert out["2026-10-25"] == ["2222"]
    assert out["2026-11-04"] == ["3333"]


def test_recent_codes_window():
    h = {"2026-10-20": ["1111"], "2026-10-21": ["2222"], "2026-11-04": ["3333"]}
    assert history.recent_codes(h, date(2026, 11, 4)) == {"2222", "3333"}


def test_meta_tag_escapes_quotes():
    tag = history.meta_tag({"2026-11-04": ['"><script>']})
    assert "<script>" not in tag
    assert history.parse_history(tag) == {"2026-11-04": ['"><script>']}
