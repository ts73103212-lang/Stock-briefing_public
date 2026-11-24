import copy
import json
from pathlib import Path

import pytest

from manga_pipeline.request import REF_FILES, build_jobs, load_request

REPO = Path(__file__).resolve().parents[2]

OK = {"date": "2026-11-24", "run_id": "r1",
      "panels": [{"n": 1, "prompt": "Corgi sensei stands on the right, pointing at a falling chart.",
                  "refs": ["corgi"]}]}


def _req(mutate):
    r = copy.deepcopy(OK)
    mutate(r)
    return json.dumps(r)


def _panels(k):
    return [{"n": i, "prompt": "x", "refs": ["mirai"]} for i in range(1, k + 1)]


def test_load_request_ok():
    req = load_request(json.dumps(OK))
    assert req["date"] == "2026-11-24"
    assert req["panels"][0]["n"] == 1


@pytest.mark.parametrize("mutate", [
    lambda r: r["panels"][0].update(n=0),
    lambda r: r["panels"][0].update(n=9),
    lambda r: r.update(panels=[{"n": 2, "prompt": "a", "refs": ["corgi"]},
                               {"n": 2, "prompt": "b", "refs": ["corgi"]}]),
    lambda r: r.update(panels=[]),
    lambda r: r.update(panels=_panels(8) + [{"n": 1, "prompt": "x", "refs": ["mirai"]}]),
    lambda r: r["panels"][0].update(refs=[]),
    lambda r: r["panels"][0].update(refs=["bob"]),
    lambda r: r["panels"][0].update(prompt=""),
    lambda r: r["panels"][0].update(prompt="a" * 1501),
    lambda r: r.update(date="2026/11/24"),
    lambda r: r.update(run_id="r4"),
    lambda r: r.update(run_id="r0"),
], ids=["n0", "n9", "dup", "empty", "nine", "refs_empty", "refs_unknown",
        "prompt_empty", "prompt_long", "date_slash", "run_r4", "run_r0"])
def test_load_request_rejects(mutate):
    with pytest.raises(ValueError):
        load_request(_req(mutate))


def test_load_request_rejects_invalid_json():
    with pytest.raises(ValueError):
        load_request("{not json")


def test_build_jobs_prefixes_common():
    common = (REPO / "docs/manga/prompt-common.md").read_text(encoding="utf-8").strip()
    jobs = build_jobs(load_request(json.dumps(OK)), REPO)
    assert jobs[0]["prompt"].startswith(common)
    assert jobs[0]["prompt"].endswith("Scene: " + OK["panels"][0]["prompt"])
    assert jobs[0]["n"] == 1 and jobs[0]["out"] == "p1.png"


def test_build_jobs_ref_paths():
    req = _req(lambda r: r["panels"][0].update(refs=["corgi", "gonda"]))
    refs = build_jobs(load_request(req), REPO)[0]["refs"]
    assert len(refs) == 2
    for p in refs:
        assert Path(p).is_absolute() and Path(p).exists()
    assert refs[0].endswith(REF_FILES["corgi"])


def test_cli_writes_jobs(tmp_path):
    import subprocess, sys
    rf = tmp_path / "request.json"
    rf.write_text(json.dumps(OK), encoding="utf-8")
    out = tmp_path / "jobs.json"
    subprocess.run([sys.executable, "-m", "manga_pipeline.request", "--request-file", str(rf),
                    "--repo", str(REPO), "--out", str(out)], check=True, cwd=REPO)
    jobs = json.loads(out.read_text(encoding="utf-8"))
    assert jobs[0]["out"] == "p1.png"
