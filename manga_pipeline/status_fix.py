"""manga_render.yml の後段で status.json を補正する。

  --persist-failed : auth.json の書き戻しに失敗した。auth が ok なら persist_failed にする。
  --ensure         : render.sh が status.json を書けなかった（ログイン復元失敗・途中停止）ときに、
                     jobs.json のコマを全部 failed にした status.json を作る。
                     auth は、ログインを復元できていれば ok、できていなければ expired。
date / run_id は環境変数 MANGA_DATE / MANGA_RUN_ID から取る。
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _base(auth: str, panels: dict) -> dict:
    return {"date": os.environ.get("MANGA_DATE", ""), "run_id": os.environ.get("MANGA_RUN_ID", ""),
            "finished_at": _now(), "auth": auth, "panels": panels}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("status", type=Path)
    ap.add_argument("--persist-failed", action="store_true")
    ap.add_argument("--ensure", action="store_true")
    ap.add_argument("--jobs", type=Path)
    ap.add_argument("--auth-restored", default="false")
    a = ap.parse_args(argv)
    a.status.parent.mkdir(parents=True, exist_ok=True)

    if a.ensure and not a.status.exists():
        panels = {}
        if a.jobs and a.jobs.exists():
            panels = {str(j["n"]): "failed" for j in json.loads(a.jobs.read_text(encoding="utf-8"))}
        auth = "ok" if a.auth_restored == "true" else "expired"
        a.status.write_text(json.dumps(_base(auth, panels), ensure_ascii=False, indent=1), encoding="utf-8")

    if a.persist_failed:
        st = json.loads(a.status.read_text(encoding="utf-8")) if a.status.exists() else _base("ok", {})
        if st.get("auth") == "ok":
            st["auth"] = "persist_failed"
        a.status.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
