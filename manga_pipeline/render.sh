#!/usr/bin/env bash
# render.sh <jobs.json> <outdir>
#
# GitHub Actions（manga_render.yml）の中で、コマごとに `codex exec` を呼んで絵を描かせる。
# jobs.json は `python -m manga_pipeline.request` の出力（[{n, prompt, refs, out}]）。
# 出力: <outdir>/p{n}.png（1024x1024）と <outdir>/status.json
#   {"date","run_id","finished_at","auth":"ok|expired","panels":{"1":"ok|failed",...}}
#   （"persist_failed" は、後段のワークフローの書き戻しステップが上書きする）
#
# Codex CLI 0.171.0 で確かめたこと（2026-11-24, `codex exec --help` / `codex features list`）:
#   - 参考画像: `-i, --image <FILE>...`（複数可）。値を貪欲に取るので `--image=<path>` の形で1つずつ渡し、
#     プロンプトは位置引数ではなく stdin で渡す。
#   - 画像生成: 機能フラグ `image_generation` は stable / 既定で有効。念のため `--enable image_generation` を付ける。
#     ツール名は `image_gen`（imagegen）。保存先を指定する引数は無い。
#   - 保存先: 生成画像は `$CODEX_HOME/generated_images/...` に保存される（既定の CODEX_HOME は ~/.codex）。
#     そこで、呼ぶ直前に目印ファイルを作り、それより新しい PNG のうち最新の1枚をそのコマの画像とする。
#
# 秘密情報を出さないため、コマンドのトレース（xtrace）は使わない。ログイン情報（auth.json）の中身にも触れない。
set -euo pipefail

JOBS=${1:?usage: render.sh <jobs.json> <outdir>}
OUT=${2:?usage: render.sh <jobs.json> <outdir>}
PY=${PYTHON:-python3}
export CODEX_HOME=${CODEX_HOME:-$HOME/.codex}
GEN="$CODEX_HOME/generated_images"
PANEL_TIMEOUT=${PANEL_TIMEOUT:-900}

mkdir -p "$OUT" "$GEN"
WORK=$(mktemp -d)
RESULTS="$WORK/results.txt"
: > "$RESULTS"
auth=ok

count=$("$PY" -c 'import json,sys; print(len(json.load(open(sys.argv[1]))))' "$JOBS")

job_field() {  # job_field <index> <field>  -> 値（refs は1行に1つ）
  "$PY" - "$JOBS" "$1" "$2" <<'PY'
import json, sys
job = json.load(open(sys.argv[1]))[int(sys.argv[2])]
v = job[sys.argv[3]]
print("\n".join(v) if isinstance(v, list) else v)
PY
}

for ((i = 0; i < count; i++)); do
  n=$(job_field "$i" n)
  out_name=$(job_field "$i" out)
  if [ "$auth" != ok ]; then
    echo "$n failed" >> "$RESULTS"
    continue
  fi

  {
    echo "Generate exactly ONE image with the built-in image generation tool."
    echo "Use the attached images as character reference sheets for the characters in the scene."
    echo "Do not run shell commands and do not write any files; just generate the image."
    echo
    job_field "$i" prompt
  } > "$WORK/prompt_$n.txt"

  img_args=()
  while IFS= read -r ref; do
    [ -n "$ref" ] && img_args+=("--image=$ref")
  done < <(job_field "$i" refs)

  marker="$WORK/marker_$n"
  touch "$marker"
  log="$WORK/codex_$n.log"
  echo "::group::panel $n"
  set +e
  timeout "$PANEL_TIMEOUT" codex exec --skip-git-repo-check --enable image_generation \
    -s read-only -C "$WORK" --color never "${img_args[@]}" < "$WORK/prompt_$n.txt" > "$log" 2>&1
  rc=$?
  set -e
  tail -n 30 "$log" || true
  echo "::endgroup::"

  if [ "$rc" -ne 0 ]; then
    if grep -qiE '\b401\b|unauthori[sz]ed|log ?in|refresh[ _]token|token.{0,20}expired' "$log"; then
      echo "panel $n: login error -> auth=expired" >&2
      auth=expired
    else
      echo "panel $n: codex exited $rc" >&2
    fi
    echo "$n failed" >> "$RESULTS"
    continue
  fi

  newest=$(find "$GEN" -type f -name '*.png' -newer "$marker" -printf '%T@ %p\n' 2>/dev/null \
           | sort -n | tail -n 1 | cut -d' ' -f2-)
  if [ -z "$newest" ]; then
    echo "panel $n: no generated image found under $GEN" >&2
    echo "$n failed" >> "$RESULTS"
    continue
  fi

  # 1024x1024 にそろえる（正方形でなければ中央を切り抜く）
  if "$PY" - "$newest" "$OUT/$out_name" <<'PY'
import sys
from PIL import Image
with Image.open(sys.argv[1]) as im:
    im = im.convert("RGB")
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))
    im.resize((1024, 1024), Image.LANCZOS).save(sys.argv[2], "PNG")
PY
  then
    echo "$n ok" >> "$RESULTS"
  else
    echo "panel $n: could not convert $newest" >&2
    echo "$n failed" >> "$RESULTS"
  fi
done

"$PY" - "$RESULTS" "$OUT/status.json" "$auth" <<'PY'
import json, os, sys
from datetime import datetime, timedelta, timezone
panels = {}
for line in open(sys.argv[1]):
    n, res = line.split()
    panels[n] = res
status = {
    "date": os.environ.get("MANGA_DATE", ""),
    "run_id": os.environ.get("MANGA_RUN_ID", ""),
    "finished_at": datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds"),
    "auth": sys.argv[3],
    "panels": panels,
}
json.dump(status, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
print(json.dumps(status))
PY

rm -rf "$WORK"
[ "$auth" = ok ] || exit 1
# 失敗したコマが1つでもあれば終了コード1（ワークフローの後段は if: always() で動く）
"$PY" -c 'import json,sys; sys.exit(0 if all(v == "ok" for v in json.load(open(sys.argv[1]))["panels"].values()) else 1)' "$OUT/status.json"
