import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PAGE = REPO / "docs" / "manga" / "picker.html"
SCENARIOS = [
    "render", "pick-request", "free-exclusive", "blank-free", "auto",
    "reload", "deadline", "cross-deadline", "no-today", "no-db", "switch-day", "live-update",
]


def _have_playwright() -> bool:
    if not shutil.which("node"):
        return False
    r = subprocess.run(["node", "-e", "require('playwright')"],
                       cwd=REPO, capture_output=True)
    return r.returncode == 0


def test_picker_follows_artifact_page_contract():
    html = PAGE.read_text(encoding="utf-8")
    low = html.lower()
    assert html.lstrip().startswith("<title>朝マンガ ネタ選び</title>")
    assert "<!doctype" not in low and "<html" not in low and "<body" not in low and "<head" not in low
    assert "Meiryo UI" in html
    assert "prefers-color-scheme: dark" in html
    assert 'name="claude:viewport-fit-sides"' in html


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_picker_scenario(scenario):
    if not _have_playwright():
        pytest.skip("node または playwright が無い")
    r = subprocess.run(["node", "tests/manga_pipeline/picker_check.mjs", scenario],
                       cwd=REPO, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
