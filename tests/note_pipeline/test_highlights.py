import json

from note_pipeline import highlights as hl


def item(headline, type_, lens="数字・需給", evidence="根拠 +12%（日経 11/18）", source="https://example.com"):
    return {"headline": headline, "evidence": evidence, "source": source, "type": type_, "lens": lens}


def test_group_of_types():
    assert hl.group_of("数字") == "数字"
    assert hl.group_of("統計") == "数字"
    assert hl.group_of("歴史の事例") == "歴史か比較"
    assert hl.group_of("他社比較") == "歴史か比較"
    assert hl.group_of("意外な事実") == "意外か反対"
    assert hl.group_of("反対の見方") == "意外か反対"
    assert hl.group_of("用語のたとえ") is None


def test_drops_empty_and_banned_items():
    items = [item("", "数字"), item("今が買い場です", "数字"), item("受注残は過去最高", "数字")]
    assert [h["headline"] for h in hl.clean(items)] == ["受注残は過去最高"]


def test_drops_duplicate_headlines():
    items = [item("受注残は過去最高", "数字"), item("受注残は 過去最高", "数字", lens="統計")]
    assert len(hl.clean(items)) == 1


def test_required_groups_come_first_and_ids_are_renumbered():
    items = [item("たとえ", "用語のたとえ", "歴史・アノマリー"), item("たとえ2", "図にできるネタ", "歴史・アノマリー"),
             item("意外", "意外な事実", "海外・マクロ"), item("過去3回", "歴史の事例", "歴史・アノマリー"),
             item("伸び率", "数字", "数字・需給")]
    out = hl.select(items, cap=4)
    assert [h["type"] for h in out[:3]] == ["数字", "歴史の事例", "意外な事実"]
    assert [h["id"] for h in out] == ["h1", "h2", "h3", "h4"]
    assert len(out) == 4


def test_fill_spreads_over_lenses():
    items = [item("a", "数字", "数字・需給"), item("b", "図にできるネタ", "数字・需給"),
             item("c", "図にできるネタ", "数字・需給"), item("d", "用語のたとえ", "統計")]
    out = hl.select(items, cap=3)
    assert [h["headline"] for h in out] == ["a", "b", "d"]


def test_missing_groups():
    out = hl.select([item("伸び率", "数字")], cap=6)
    assert hl.missing_groups(out) == ["歴史か比較", "意外か反対"]


def test_merge_work(tmp_path):
    (tmp_path / "highlights").mkdir()
    (tmp_path / "highlights" / "numbers.json").write_text(json.dumps(
        {"c1": [item("伸び率", "数字")], "c2": [item("出来高3倍", "数字")]}, ensure_ascii=False))
    (tmp_path / "highlights" / "history.json").write_text(json.dumps(
        {"c1": [item("過去3回", "歴史の事例", "歴史・アノマリー"), item("逆に下落", "反対の見方", "歴史・アノマリー")]},
        ensure_ascii=False))
    (tmp_path / "highlights" / "broken.json").write_text("{")
    (tmp_path / "day_doc.json").write_text(json.dumps(
        {"date": "2026-11-19", "candidates": [{"id": "c1"}, {"id": "c2"}, {"id": "c3"}]}))
    doc, report = hl.merge_work(tmp_path, cap=6)
    c1, c2, c3 = doc["candidates"]
    assert len(c1["highlights"]) == 3 and c1["highlights"][0]["lens"] == "数字・需給"
    assert len(c2["highlights"]) == 1 and "highlights" not in c3
    assert doc["highlights_status"] == "partial"
    assert report["counts"] == {"c1": 3, "c2": 1, "c3": 0}
    assert report["missing"]["c2"] == ["歴史か比較", "意外か反対"]
    assert "c1" not in report["missing"]
    assert report["unreadable"] == ["broken.json"]
