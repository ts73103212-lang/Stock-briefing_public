import json

from note_pipeline.highlights import merge_work, prune, select


def _h(head, type_, lens):
    return {"headline": head, "evidence": "根拠 出典あり", "source": "https://example.com", "type": type_, "lens": lens}


def _items(n, prefix):
    types = ["数字", "歴史の事例", "意外な事実", "用語のたとえ", "図にできるネタ", "技術の強み", "他社比較", "統計"]
    lenses = ["数字・需給", "歴史・アノマリー", "海外・マクロ", "統計", "技術"]
    return [_h(f"{prefix}の見どころ{i}", types[i % len(types)], lenses[i % len(lenses)]) for i in range(n)]


def test_select_required_groups_first():
    got = select(_items(8, "a"), cap=8)
    assert [h["type"] for h in got[:3]] == ["数字", "歴史の事例", "意外な事実"]
    assert [h["id"] for h in got] == [f"h{i}" for i in range(1, 9)]


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


def test_merge_work_prunes(tmp_path):
    (tmp_path / "highlights").mkdir()
    cands = [{"id": f"c{i}", "rank": i, "title": f"t{i}"} for i in range(1, 8)]
    (tmp_path / "day_doc.json").write_text(json.dumps({"candidates": cands}, ensure_ascii=False))
    data = {f"c{i}": _items(6 if i <= 5 else 1, f"c{i}") for i in range(1, 8)}
    (tmp_path / "highlights" / "numbers.json").write_text(json.dumps(data, ensure_ascii=False))
    doc, report = merge_work(tmp_path, cap=8, min_points=5, min_keep=5)
    assert [c["id"] for c in doc["candidates"]] == ["c1", "c2", "c3", "c4", "c5"]
    assert {d["id"] for d in report["dropped"]} == {"c6", "c7"}
    assert report["status"] == "done" and report["kept_below_min"] == []
