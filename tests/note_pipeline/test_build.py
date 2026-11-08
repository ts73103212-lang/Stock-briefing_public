import json
from pathlib import Path

from PIL import Image

from note_pipeline import build, history

FIX = Path(__file__).parent / "fixtures"


def test_build_writes_index_and_images(tmp_path):
    rc = build.main(["--input", str(FIX / "daily_sample.json"), "--out", str(tmp_path)])
    assert rc == 0
    assert (tmp_path / "index.html").exists()
    imgs = sorted(p.name for p in (tmp_path / "img").iterdir())
    assert imgs == sorted([f"a{i}_{n}.jpg" for i in (1, 2, 3) for n in ("header", "fig1", "fig2")])
    for p in (tmp_path / "img").iterdir():
        assert p.stat().st_size <= 250_000, p
        assert Image.open(p).format == "JPEG"


def test_build_paid_mode(tmp_path):
    rc = build.main(["--input", str(FIX / "paid_sample.json"), "--out", str(tmp_path), "--mode", "paid"])
    assert rc == 0
    assert sorted(p.name for p in (tmp_path / "img").iterdir()) == ["fig1.jpg", "fig2.jpg", "header.jpg"]


def test_build_lint_exit_code(tmp_path, capsys):
    day = json.loads((FIX / "daily_sample.json").read_text(encoding="utf-8"))
    day["articles"][0]["body_html"] += "<p>今が買い場です。</p>"
    inp = tmp_path / "day.json"
    inp.write_text(json.dumps(day, ensure_ascii=False), encoding="utf-8")
    rc = build.main(["--input", str(inp), "--out", str(tmp_path / "out")])
    assert rc == 2
    assert "買い場" in capsys.readouterr().err
    assert (tmp_path / "out" / "index.html").exists()


def test_build_missing_disclaimer_warns(tmp_path, capsys):
    day = json.loads((FIX / "daily_sample.json").read_text(encoding="utf-8"))
    day["articles"][1]["body_html"] = "<p>免責なし</p>"
    day["articles"][1]["figures"] = []
    inp = tmp_path / "day.json"
    inp.write_text(json.dumps(day, ensure_ascii=False), encoding="utf-8")
    assert build.main(["--input", str(inp), "--out", str(tmp_path / "out")]) == 2
    assert "免責文" in capsys.readouterr().err


def test_history_carried(tmp_path):
    prev = tmp_path / "prev.html"
    prev.write_text(f"<html><head>{history.meta_tag({'2026-11-02': ['9999'], '2026-10-01': ['0000']})}</head></html>",
                    encoding="utf-8")
    out = tmp_path / "out"
    assert build.main(["--input", str(FIX / "daily_sample.json"), "--out", str(out), "--prev-page", str(prev)]) == 0
    h = history.parse_history((out / "index.html").read_text(encoding="utf-8"))
    assert h == {"2026-11-02": ["9999"], "2026-11-04": ["1111", "2222"]}


def test_digest_embedded_and_carried(tmp_path):
    prev = tmp_path / "prev.html"
    prev.write_text("<html><head>" + history.meta_tag(
        {"2026-11-03": [{"kind": "theme", "title": "前日", "summary": ""}]}, name=history.DIGEST_META)
        + "</head></html>", encoding="utf-8")
    out = tmp_path / "out"
    build.main(["--input", str(FIX / "daily_sample.json"), "--out", str(out), "--prev-page", str(prev)])
    dig = history.parse_meta((out / "index.html").read_text(encoding="utf-8"), history.DIGEST_META)
    assert dig["2026-11-03"][0]["title"] == "前日"
    assert [d["title"] for d in dig["2026-11-04"]] == ["ダミータイトル1-案1", "ダミータイトル2-案1", "ダミータイトル3-案1"]
