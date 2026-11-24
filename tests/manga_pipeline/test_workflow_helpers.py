import json

import pytest
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _py(*args, env=None):
    import os
    return subprocess.run([sys.executable, *args], cwd=REPO, capture_output=True, text=True,
                          env=dict(os.environ, **(env or {})))


def test_mask_auth_masks_every_long_string(tmp_path):
    auth = {"OPENAI_API_KEY": None, "auth_mode": "chatgpt",
            "tokens": {"id_token": "eyJ" + "a" * 40, "access_token": "eyJ" + "b" * 40,
                       "refresh_token": "rt_" + "c" * 30, "account_id": "acc-1234567890abcdef"},
            "last_refresh": "2026-11-24T09:00:00Z"}
    f = tmp_path / "auth.json"
    f.write_text(json.dumps(auth))
    r = _py("manga_pipeline/mask_auth.py", str(f))
    assert r.returncode == 0
    lines = r.stdout.splitlines()
    for v in auth["tokens"].values():
        assert f"::add-mask::{v}" in lines
    assert "::add-mask::chatgpt" not in lines   # 短い値は対象外
    assert all(l.startswith("::add-mask::") for l in lines)


def test_status_persist_failed_overrides_ok(tmp_path):
    st = tmp_path / "status.json"
    st.write_text(json.dumps({"date": "2026-11-24", "run_id": "r1", "auth": "ok", "panels": {"1": "ok"}}))
    assert _py("manga_pipeline/status_fix.py", str(st), "--persist-failed").returncode == 0
    d = json.loads(st.read_text())
    assert d["auth"] == "persist_failed" and d["panels"] == {"1": "ok"}


def test_status_persist_failed_keeps_expired(tmp_path):
    st = tmp_path / "status.json"
    st.write_text(json.dumps({"date": "2026-11-24", "run_id": "r1", "auth": "expired", "panels": {}}))
    _py("manga_pipeline/status_fix.py", str(st), "--persist-failed")
    assert json.loads(st.read_text())["auth"] == "expired"


def test_status_ensure_writes_fallback_when_login_missing(tmp_path):
    jobs = tmp_path / "jobs.json"
    jobs.write_text(json.dumps([{"n": 1}, {"n": 3}]))
    st = tmp_path / "panels" / "status.json"
    r = _py("manga_pipeline/status_fix.py", str(st), "--ensure", "--jobs", str(jobs),
            "--auth-restored", "false", env={"MANGA_DATE": "2026-11-24", "MANGA_RUN_ID": "r2"})
    assert r.returncode == 0, r.stderr
    d = json.loads(st.read_text())
    assert d["auth"] == "expired" and d["run_id"] == "r2" and d["date"] == "2026-11-24"
    assert d["panels"] == {"1": "failed", "3": "failed"}
    assert "finished_at" in d


def test_status_ensure_keeps_existing(tmp_path):
    st = tmp_path / "status.json"
    st.write_text(json.dumps({"date": "2026-11-24", "run_id": "r1", "auth": "ok", "panels": {"1": "ok"}}))
    _py("manga_pipeline/status_fix.py", str(st), "--ensure", "--jobs", str(tmp_path / "none.json"),
        "--auth-restored", "true")
    assert json.loads(st.read_text())["panels"] == {"1": "ok"}


def test_workflow_is_dispatch_only_and_persists_always():
    yaml = pytest.importorskip("yaml")
    wf = yaml.safe_load((REPO / ".github/workflows/manga_render.yml").read_text())
    on = wf[True] if True in wf else wf["on"]   # PyYAML は on: を True と読む
    assert list(on) == ["workflow_dispatch"]
    assert wf["concurrency"] == {"group": "manga-render", "cancel-in-progress": False}
    steps = {s.get("name"): s for s in wf["jobs"]["render"]["steps"]}
    assert steps["Persist refreshed Codex login"]["if"].startswith("always()")
    assert steps["Publish panels to branch \"manga\""]["if"].startswith("always()")
    text = (REPO / ".github/workflows/manga_render.yml").read_text()
    assert "set -x" not in text and "${{ inputs.request }}" in wf["jobs"]["render"]["env"]["REQUEST"]
    assert "@openai/codex@0.171.0" in text


def test_workflow_has_persist_check_input():
    """SECRETS_PAT の書き戻しを、auth.json が変わっていなくても1回試せる（設計書 §8 の1往復確認）。"""
    yaml = pytest.importorskip("yaml")
    wf = yaml.safe_load((REPO / ".github/workflows/manga_render.yml").read_text())
    on = wf[True] if True in wf else wf["on"]
    inp = on["workflow_dispatch"]["inputs"]["persist_check"]
    assert inp["type"] == "boolean" and inp["default"] is False and inp["required"] is False
    persist = {s.get("name"): s for s in wf["jobs"]["render"]["steps"]}["Persist refreshed Codex login"]
    assert persist["env"]["PERSIST_CHECK"] == "${{ inputs.persist_check }}"
    assert '"$PERSIST_CHECK" != "true"' in persist["run"]
