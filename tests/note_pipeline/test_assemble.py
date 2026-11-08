import json
from pathlib import Path

from PIL import Image

from note_pipeline import assemble, figs

FIX = Path(__file__).parent / "fixtures"


def _work(tmp_path, drop=None, missing=None, no_figs=None):
    day = json.loads((FIX / "daily_sample.json").read_text(encoding="utf-8"))
    w = tmp_path / "work"
    (w / "drafts").mkdir(parents=True)
    (w / "figs").mkdir()
    plan = {"date": day["date"], "mode": "daily", "notes": ["計画の注記"], "candidates": day["candidates"],
            "articles": [{"id": a["id"], "kind": a["kind"], "topic": a["titles"][0]} for a in day["articles"]]}
    (w / "plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    for a in day["articles"]:
        if a["id"] == missing:
            continue
        figures = a.pop("figures")
        a["figure_requests"] = [{"n": 1, "type": "D"}]
        (w / "drafts" / f"a{a['id']}.json").write_text(json.dumps(a, ensure_ascii=False), encoding="utf-8")
        if a["id"] != no_figs:
            (w / "figs" / f"a{a['id']}.json").write_text(json.dumps(figures, ensure_ascii=False), encoding="utf-8")
    if drop:
        (w / "review").mkdir()
        (w / "review" / "verdict.json").write_text(json.dumps({f"a{drop}": "drop"}), encoding="utf-8")
    return w


def test_assemble_all_three(tmp_path):
    day = assemble.assemble(_work(tmp_path))
    assert [a["id"] for a in day["articles"]] == ["1", "2", "3"]
    assert len(day["articles"][0]["figures"]) == 2
    assert all("figure_requests" not in a for a in day["articles"])
    assert day["candidates"] and day["notes"] == ["計画の注記"]
    assert day["date"] == "2026-11-04" and day["mode"] == "daily"


def test_missing_draft_is_skipped_with_note(tmp_path):
    day = assemble.assemble(_work(tmp_path, missing="2"))
    assert [a["id"] for a in day["articles"]] == ["1", "3"]
    assert any("記事2" in n and "見送り" in n for n in day["notes"])


def test_dropped_by_pm(tmp_path):
    day = assemble.assemble(_work(tmp_path, drop="3"))
    assert [a["id"] for a in day["articles"]] == ["1", "2"]
    assert any("記事3" in n for n in day["notes"])


def test_no_figs_file_means_no_figures(tmp_path):
    day = assemble.assemble(_work(tmp_path, no_figs="1"))
    assert day["articles"][0]["figures"] == []


def test_cli_zero_articles_exit_1(tmp_path):
    w = _work(tmp_path)
    for p in (w / "drafts").iterdir():
        p.unlink()
    assert assemble.main(["--work", str(w), "--out", str(w / "day.json")]) == 1


def test_cli_writes_day_json(tmp_path):
    w = _work(tmp_path)
    assert assemble.main(["--work", str(w), "--out", str(w / "day.json")]) == 0
    assert len(json.loads((w / "day.json").read_text(encoding="utf-8"))["articles"]) == 3


def test_figs_cli_renders_each_spec(tmp_path):
    day = json.loads((FIX / "daily_sample.json").read_text(encoding="utf-8"))
    spec = tmp_path / "a1.json"
    spec.write_text(json.dumps(day["articles"][0]["figures"], ensure_ascii=False), encoding="utf-8")
    assert figs.main(["--spec", str(spec), "--out", str(tmp_path / "out")]) == 0
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == ["fig1.jpg", "fig2.jpg"]
    assert Image.open(tmp_path / "out" / "fig1.jpg").size == (1920, 1080)


def test_header_proposal_merged(tmp_path):
    w = _work(tmp_path)
    (w / "figs" / "a1_header.json").write_text(json.dumps(
        {"concept": "構図案", "prompt": "a corgi ...", "callouts": ["−3,643円"]}, ensure_ascii=False), encoding="utf-8")
    day = assemble.assemble(w)
    a1 = day["articles"][0]
    assert a1["header_proposal"]["prompt"] == "a corgi ..."
    assert a1["header"]["callouts"] == ["−3,643円"]
    assert "header_proposal" not in day["articles"][1]
