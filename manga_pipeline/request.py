"""render 依頼 JSON の検証と、コマごとの完全プロンプト・参考画像パスの組み立て（設計書 §7.2・§7.3）。

CLI: python -m manga_pipeline.request --request-file R.json --repo . --out jobs.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REF_FILES: dict[str, str] = {
    "corgi": "assets/manga/corgi_sensei_sheet.png",
    "mirai": "assets/manga/mirai_sheet.png",
    "gonda": "assets/manga/gonda_sheet.png",
}
COMMON_FILE = "docs/manga/prompt-common.md"
MAX_PROMPT = 1500
RUN_IDS = {"r1", "r2", "r3"}  # 初回＋描き直し最大2回
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def load_request(text: str) -> dict:
    """依頼 JSON を検証して返す。不正なら ValueError。"""
    try:
        req = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"request is not valid JSON: {e}") from e
    if not isinstance(req, dict):
        raise ValueError("request must be an object")
    if not isinstance(req.get("date"), str) or not _DATE.fullmatch(req["date"]):
        raise ValueError("date must be YYYY-MM-DD")
    if req.get("run_id") not in RUN_IDS:
        raise ValueError(f"run_id must be one of {sorted(RUN_IDS)}")
    panels = req.get("panels")
    if not isinstance(panels, list) or not 1 <= len(panels) <= 8:
        raise ValueError("panels must have 1..8 items")
    seen: set[int] = set()
    for p in panels:
        n = p.get("n") if isinstance(p, dict) else None
        if not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= 8:
            raise ValueError(f"panel n must be 1..8: {n!r}")
        if n in seen:
            raise ValueError(f"duplicate panel n: {n}")
        seen.add(n)
        prompt = p.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > MAX_PROMPT:
            raise ValueError(f"panel {n}: prompt must be 1..{MAX_PROMPT} chars")
        refs = p.get("refs")
        if not isinstance(refs, list) or not refs or any(r not in REF_FILES for r in refs):
            raise ValueError(f"panel {n}: refs must be a non-empty subset of {sorted(REF_FILES)}")
    return req


def build_jobs(req: dict, repo: Path) -> list[dict]:
    """コマごとに共通文＋場面文のプロンプトと、参考画像の絶対パスを返す。"""
    repo = Path(repo).resolve()
    common = (repo / COMMON_FILE).read_text(encoding="utf-8").strip()
    jobs = []
    for p in sorted(req["panels"], key=lambda p: p["n"]):
        refs = []
        for key in p["refs"]:
            path = repo / REF_FILES[key]
            if not path.exists():
                raise FileNotFoundError(path)
            refs.append(str(path))
        jobs.append({"n": p["n"], "prompt": f"{common} {p['prompt'].strip()}",
                     "refs": refs, "out": f"p{p['n']}.png"})
    return jobs


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--request-file", required=True, type=Path)
    ap.add_argument("--repo", default=".", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    req = load_request(a.request_file.read_text(encoding="utf-8"))
    jobs = build_jobs(req, a.repo)
    a.out.write_text(json.dumps(jobs, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
