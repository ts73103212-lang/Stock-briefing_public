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


# 2026-11-22: 5点未満の候補を外す
from note_pipeline.highlights import merge_work, prune  # noqa: E402


def _h2(head, type_, lens):
    return {"headline": head, "evidence": "根拠 出典あり", "source": "https://example.com", "type": type_, "lens": lens}


def _items(n, prefix):
    types = ["数字", "歴史の事例", "意外な事実", "用語のたとえ", "図にできるネタ", "技術の強み", "他社比較", "統計"]
    lenses = ["数字・需給", "歴史・アノマリー", "海外・マクロ", "統計", "技術"]
    return [_h2(f"{prefix}の見どころ{i}", types[i % len(types)], lenses[i % len(lenses)]) for i in range(n)]


def test_prune_drops_below_min_by_rank_but_keeps_min():
    cands = [{"id": f"c{i}", "rank": i, "title": f"t{i}"} for i in range(1, 8)]
    counts = {"c1": 6, "c2": 5, "c3": 1, "c4": 4, "c5": 3, "c6": 0, "c7": 2}
    kept, dropped = prune(cands, counts, min_points=5, min_keep=5)
    # 5点以上は c1,c2 だけ → 2点以上の c4,c5,c7 を順位順に戻して5本
    assert [c["id"] for c in kept] == ["c1", "c2", "c4", "c5", "c7"]
    assert {d["id"] for d in dropped} == {"c3", "c6"}


def test_prune_keeps_all_qualifying_even_above_min_keep():
    cands = [{"id": f"c{i}", "rank": i} for i in range(1, 8)]
    counts = {f"c{i}": 6 for i in range(1, 7)} | {"c7": 4}
    kept, dropped = prune(cands, counts, min_points=5, min_keep=5)
    assert len(kept) == 6 and dropped[0]["id"] == "c7"


def test_prune_disabled_by_default():
    cands = [{"id": "c1"}, {"id": "c2"}]
    assert prune(cands, {}, 0, 5) == (cands, [])


def test_merge_work_prunes_below_min(tmp_path):
    (tmp_path / "highlights").mkdir()
    cands = [{"id": f"c{i}", "rank": i, "title": f"t{i}"} for i in range(1, 8)]
    (tmp_path / "day_doc.json").write_text(json.dumps({"candidates": cands}, ensure_ascii=False))
    data = {f"c{i}": _items(6 if i <= 5 else 1, f"c{i}") for i in range(1, 8)}
    (tmp_path / "highlights" / "numbers.json").write_text(json.dumps(data, ensure_ascii=False))
    doc, report = merge_work(tmp_path, cap=8, min_points=5, min_keep=5)
    assert [c["id"] for c in doc["candidates"]] == ["c1", "c2", "c3", "c4", "c5"]
    assert {d["id"] for d in report["dropped"]} == {"c6", "c7"}
    assert report["status"] == "done" and report["kept_below_min"] == []
