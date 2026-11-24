"""render.sh を偽の codex（PATH 先頭に置いたスタブ）で動かして、status.json と出力を確かめる。"""
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RENDER = REPO / "manga_pipeline" / "render.sh"

STUB_OK = r"""#!/usr/bin/env bash
# 偽 codex: 引数を記録し、CODEX_HOME/generated_images に PNG を1枚置く
echo "$@" >> "$CODEX_HOME/calls.txt"
cat > /dev/null   # プロンプト（stdin）を読み捨てる
d="$CODEX_HOME/generated_images/thread-$RANDOM$RANDOM"
mkdir -p "$d"
"$PYTHON" -c "from PIL import Image; Image.new('RGB',(1536,1024),'white').save('$d/ig_1.png')"
echo "done"
"""

STUB_FAIL_ON_2 = r"""#!/usr/bin/env bash
cat > /dev/null
n=$(( $(cat "$CODEX_HOME/count" 2>/dev/null || echo 0) + 1 )); echo $n > "$CODEX_HOME/count"
if [ "$n" = 2 ]; then echo "model error: something broke" >&2; exit 1; fi
d="$CODEX_HOME/generated_images/t$n"; mkdir -p "$d"
"$PYTHON" -c "from PIL import Image; Image.new('RGB',(1024,1024),'white').save('$d/a.png')"
"""

STUB_401 = r"""#!/usr/bin/env bash
cat > /dev/null
echo "ERROR: unexpected status 401 Unauthorized: Your access token could not be refreshed. Please log in again." >&2
exit 1
"""


def _run(tmp_path, stub, n_panels=2):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    codex = bindir / "codex"
    codex.write_text(stub)
    codex.chmod(codex.stat().st_mode | stat.S_IEXEC)
    home = tmp_path / "codex_home"
    home.mkdir()
    ref = REPO / "assets/manga/corgi_sensei_sheet.png"
    jobs = [{"n": i, "prompt": f"scene {i}", "refs": [str(ref)], "out": f"p{i}.png"}
            for i in range(1, n_panels + 1)]
    jf = tmp_path / "jobs.json"
    jf.write_text(json.dumps(jobs))
    out = tmp_path / "out"
    env = dict(os.environ, PATH=f"{bindir}:{os.environ['PATH']}", CODEX_HOME=str(home),
               PYTHON=sys.executable, MANGA_DATE="2026-11-24", MANGA_RUN_ID="r1")
    r = subprocess.run(["bash", str(RENDER), str(jf), str(out)], env=env,
                       capture_output=True, text=True)
    status = json.loads((out / "status.json").read_text())
    return r, status, out, home


def test_render_ok_writes_panels_and_status(tmp_path):
    from PIL import Image
    r, st, out, home = _run(tmp_path, STUB_OK)
    assert r.returncode == 0, r.stderr
    assert st["date"] == "2026-11-24" and st["run_id"] == "r1" and st["auth"] == "ok"
    assert st["panels"] == {"1": "ok", "2": "ok"}
    assert "finished_at" in st
    for i in (1, 2):
        with Image.open(out / f"p{i}.png") as im:
            assert im.size == (1024, 1024)
    calls = (home / "calls.txt").read_text()
    assert "--image=" in calls and "corgi_sensei_sheet.png" in calls


def test_render_panel_failure_continues(tmp_path):
    r, st, out, _ = _run(tmp_path, STUB_FAIL_ON_2, n_panels=3)
    assert st["panels"] == {"1": "ok", "2": "failed", "3": "ok"}
    assert st["auth"] == "ok"
    assert not (out / "p2.png").exists()
    assert r.returncode != 0   # 失敗コマがあればジョブを失敗扱いにする


def test_render_auth_expired_stops(tmp_path):
    r, st, out, home = _run(tmp_path, STUB_401, n_panels=3)
    assert st["auth"] == "expired"
    assert st["panels"] == {"1": "failed", "2": "failed", "3": "failed"}
    assert r.returncode != 0


def test_render_sh_has_no_xtrace():
    text = RENDER.read_text()
    assert "set -euo pipefail" in text
    assert "set -x" not in text
