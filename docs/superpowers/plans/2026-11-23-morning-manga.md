# 朝ブリーフィング 8コマ漫画 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 平日の夕方に Claude が台本を作り、GitHub Actions 上の Codex がコマを描き、Claude が確認・組版して非公開 Artifact に納品する。翌朝のブリーフィングが、それをメール下部に貼る。

**Architecture:** 描画は `manga_render.yml`（workflow_dispatch）が担当する。ChatGPT のログイン情報（auth.json）を Secrets から復元し、使用後に書き戻す。プロンプトの組み立て、組版、manifest の作成は、Python の小さなモジュール `manga_pipeline/` にまとめる。夕方の進行と朝の貼り付けは、リポジトリ内の手順書（`docs/manga/*.md`）を定期タスクのプロンプトから参照させる。

**Tech Stack:** Python 3.11、Pillow、jpholiday（既存 `note_pipeline.market`）、Noto Sans JP（既存 `note_pipeline.fonts`）、pytest、GitHub Actions、Codex CLI（ChatGPT ログイン）、Claude の定期タスク／Artifact／Gmail。

**Spec:** `docs/superpowers/specs/2026-11-23-morning-manga-design.md`

## Global Constraints

- 公開リポジトリ。**セリフ・解説・完成画像はリポジトリに書かない、コミットしない。** 置いてよいのは、文字なしのコマ画像（ブランチ `manga`）と英語の場面プロンプトだけ。
- コマ画像：1024×1024。完成画像：`row1.jpg`〜`row4.jpg`、各 1360×684、JPEG 品質85、各200KB以内。
- 吹き出し：1つあたり3行まで、1行12字まで。
- 描き直し：最大2回、1回あたり最大8コマ（ChatGPT Plus）。
- 夕方の漫画タスクは 17:45 JST に開始し、19:30 JST が締切。過ぎたら漫画なしとする。
- 通知文：見送りは「🐾 漫画は本日見送り：<理由>」。
- 投資助言に当たる表現を使わない（`docs/note-pipeline/editorial-rules.md` §1）。ゴンダ先輩の失敗談では、銘柄名を出さない。
- Python は `.venv/bin/python` を使う（OS の Pillow と衝突するため。`requirements-note.txt` を流用）。
- 秘密情報 `CODEX_AUTH_JSON`、`SECRETS_PAT` の中身を、ログ・コミット・チャットに出さない。

## Review Focus

1. **auth.json の書き戻し漏れ。** Codex がトークンを更新したのに Secrets を書き戻せないと、翌日からログインできなくなる。`if: always()` で書き戻し、失敗したら `status.json` に `"auth":"persist_failed"` を書く（Task 3）。
2. **吹き出しの溢れ。** 長いセリフや、半角英数字が混ざったセリフでも、制限内なら枠の中に収まる。超えた場合は組版前にエラーにする（Task 4 `test_wrap_*`）。
3. **for_date の連休またぎ。** 金曜や祝日前日に作った漫画は、次の営業日の朝に出る。年末年始（12/31〜1/3 は東証休場）もまたぐ（Task 5 `test_next_business_day_*`）。
4. **前日分の誤掲載。** 朝の時点で manifest が古ければ（for_date ≠ 今日）、漫画欄を省く（Task 7）。
5. **Actions が途中で止まる。** 夕方タスクが `status.json` を待ち続けないよう、19:30 の締切で打ち切って見送りを通知する（Task 6）。

---

## File Structure

| ファイル | 役割 |
|---|---|
| `assets/manga/*.png` | 設定画（配置済み） |
| `docs/manga/README.md` | ユーザー向けの手順：auth.json と PAT の登録、ログイン切れの直し方 |
| `docs/manga/prompt-common.md` | 場面プロンプトの共通文（設計書 §7.3 の原文） |
| `manga_pipeline/__init__.py` | 空 |
| `manga_pipeline/request.py` | render 依頼 JSON の検証、コマごとの完全プロンプトと参考画像パスの組み立て（CLI あり） |
| `manga_pipeline/render.sh` | Actions 内で `codex exec` を1コマずつ呼び、`status.json` を書く |
| `.github/workflows/manga_render.yml` | 描画ワークフロー |
| `manga_pipeline/compose.py` | 吹き出しの組版、横2コマの段画像4枚の出力（CLI あり） |
| `manga_pipeline/manifest.py` | for_date の算出、manifest.json、納品ページ index.html の出力（CLI あり） |
| `docs/manga/evening-task-prompt.md` | 夕方の漫画タスクの進行手順 |
| `docs/manga/briefing-manga.md` | 朝ブリーフィングが漫画を貼る手順 |
| `tests/manga_pipeline/test_*.py` | テスト |

---

### Task 1: ユーザー向け手順書と Secrets の登録（ゲート）

**Files:**
- Create: `docs/manga/README.md`

**Interfaces:**
- Produces: リポジトリの Secrets `CODEX_AUTH_JSON`（`base64 -w0 ~/.codex/auth.json` の値）、`SECRETS_PAT`（fine-grained PAT）

- [ ] **Step 1: README を書く**
  - ユーザーは PAT の作り方を知らない。GitHub の画面で押す場所を1手ずつ書く。
  - **PAT を作る：** Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token と進み、次のとおり設定する。
    - Repository access：`Stock-briefing_public` のみ
    - Repository permissions：**Secrets: Read and write** のみ
    - 有効期限：1年
  - **Secrets に登録する：** リポジトリの Settings → Secrets and variables → Actions → New repository secret で、2つを登録する。
  - **auth.json を用意する：**
    - Windows の場合（PowerShell）：`[Convert]::ToBase64String([IO.File]::ReadAllBytes("$HOME\.codex\auth.json"))`
    - Mac／Linux の場合：`base64 -w0 ~/.codex/auth.json`（Mac は `base64 -i ~/.codex/auth.json`）
  - **登録後：** PC で `codex logout` → `codex login` を実行し、Actions とは別のログイン状態にする。同じ auth.json を2か所で使うと、更新が衝突するため。
  - **「Codex の再ログインが必要」と通知が来たとき：** 上の「auth.json を用意する」と「Secrets に登録する」をやり直す。
- [ ] **Step 2: コミットしてユーザーに依頼する**
  ```bash
  git add docs/manga/README.md && git commit -m "docs(manga): Secrets 登録手順"
  ```
  ユーザーに README の手順を依頼する。2つの Secrets の登録が済むまで、Task 3 の Step 4 には進まない（Task 2 は並行してよい）。

---

### Task 2: 依頼 JSON とプロンプトの組み立て（`request.py`）

**Files:**
- Create: `manga_pipeline/__init__.py`, `manga_pipeline/request.py`, `docs/manga/prompt-common.md`, `tests/manga_pipeline/__init__.py`, `tests/manga_pipeline/test_request.py`

**Interfaces:**
- Produces:
  - `REF_FILES: dict[str, str]` = `{"corgi": "assets/manga/corgi_sensei_sheet.png", "mirai": "assets/manga/mirai_sheet.png", "gonda": "assets/manga/gonda_sheet.png"}`
  - `load_request(text: str) -> dict`：検証済みの依頼を返す。不正なら `ValueError`
  - `build_jobs(req: dict, repo: Path) -> list[dict]`：`[{"n": int, "prompt": str, "refs": [str(絶対パス)], "out": "p{n}.png"}]`
  - CLI：`python -m manga_pipeline.request --request-file R.json --repo . --out jobs.json`

依頼の書式（設計書 §7.2）：`{"date":"YYYY-MM-DD","run_id":"r1","panels":[{"n":1,"prompt":"...","refs":["mirai"]}]}`

- [ ] **Step 1: 失敗するテストを書く**
  - `test_load_request_ok`：コマ1つの正しい依頼が通る。
  - `test_load_request_rejects`：パラメータ化で、次をそれぞれ `ValueError` にする。
    - `n` が0、または9
    - `n` の重複
    - `panels` が空、または9件
    - `refs` が空、または未知のキー `"bob"`
    - `prompt` が空、または1,500字超
    - `date` が `2026/11/24` の形
    - `run_id` が `r1`〜`r3` 以外
  - `test_build_jobs_prefixes_common`：`prompt` が `prompt-common.md` の本文で始まり、場面文で終わる。
  - `test_build_jobs_ref_paths`：`refs: ["corgi","gonda"]` が、存在する絶対パス2つになる。
- [ ] **Step 2: 失敗を確認する**
  Run: `.venv/bin/python -m pytest tests/manga_pipeline/test_request.py -q` → FAIL（ModuleNotFoundError）
- [ ] **Step 3: 実装する**
  - `prompt-common.md` には、設計書 §7.3 の共通文をコードブロックの外にそのまま置く。
  - `build_jobs` は、共通文の末尾の `Scene:` の後に半角スペースを1つ入れ、場面文をつなぐ。
- [ ] **Step 4: テストが通ることを確認する**
  Run: 同上 → PASS
- [ ] **Step 5: コミットする**
  `git commit -m "feat(manga): render 依頼の検証とプロンプト組み立て"`

---

### Task 3: 描画ワークフロー（`manga_render.yml`）と無人描画の確認（ゲート）

**Files:**
- Create: `manga_pipeline/render.sh`, `.github/workflows/manga_render.yml`

**Interfaces:**
- Consumes: Task 2 の CLI（`jobs.json`）、Task 1 の Secrets
- Produces:
  - ブランチ `manga` の `manga/<date>/p{n}.png`
  - ブランチ `manga` の `manga/<date>/status.json`
    ```json
    {"date":"…","run_id":"r1","finished_at":"ISO8601","auth":"ok|expired|persist_failed",
     "panels":{"1":"ok|failed", …}}
    ```

- [ ] **Step 1: Codex CLI の画像生成の呼び方を確かめる**
  - Codex CLI 0.171.0 を一時的に入れて、次を記録する。
    - `codex exec --help`
    - `codex features list`（無ければ `codex --help`）
  - 確かめる項目は3つ：画像を渡すオプション（`-i` など）、画像生成機能を有効にする方法、生成画像の保存先。
  - 結果は `render.sh` の冒頭コメントに書く。
- [ ] **Step 2: `render.sh <jobs.json> <outdir>` を書く**
  - `set -euo pipefail` を使い、`set -x` は禁止。
  - 1コマごとに `codex exec` を呼び、保存先から `outdir/p{n}.png` にコピーする。
  - コマ単位の失敗は `failed` と記録して、次のコマへ進む。
  - ログインエラー（401／`login` を含む）を検知したら、`auth=expired` で中断する。
  - 最後に `status.json` を書く。
- [ ] **Step 3: `manga_render.yml` を書く**
  - トリガーは `workflow_dispatch` のみ。入力は `request`（string, required）。
  - `concurrency: {group: manga-render, cancel-in-progress: false}`
  - `timeout-minutes: 40`
  - 権限：`contents: write`
  - 手順：
    1. checkout
    2. setup-node 22
    3. `npm i -g @openai/codex@0.171.0`
    4. setup-python 3.11 と `pip install -r requirements-note.txt`
    5. `echo "$CODEX_AUTH_JSON" | base64 -d > ~/.codex/auth.json`（実行前に `::add-mask::`）
    6. 依頼を `request.json` に書き、`python -m manga_pipeline.request` で `jobs.json` を作る
    7. `render.sh`
    8. **`if: always()`**：auth.json の sha256 が実行前と違えば、`GH_TOKEN=${{ secrets.SECRETS_PAT }} gh secret set CODEX_AUTH_JSON --body "$(base64 -w0 ~/.codex/auth.json)"` で書き戻す。失敗したら `status.json` の `auth` を `persist_failed` にする。
    9. **`if: always()`**：charts と同じ方式で、ブランチ `manga` を更新する（`docs/briefing-charts.md` 参照）。前回の内容を `git fetch origin manga` で取り込み、`manga/<date>/` を追加・上書きする。直近7日分だけを残し、1コミットに squash して force push する。
- [ ] **Step 4: 無人描画を確認する（ゲート）**
  - `actions_run_trigger` で、コマ1つ（refs `["corgi"]`、場面は試し描きの p2）の依頼を送る。
  - 完了後、ブランチ `manga` の `status.json` が `panels.1 == "ok"` かつ `auth == "ok"` であること、`p1.png` に設定画どおりのコーギーが描かれていることを確かめる。
  - 同じ依頼をもう1回送り、2回目も `auth == "ok"` であることを確かめる（書き戻しが1往復できた証拠）。
  - **どちらかが駄目なら、ここで作業を止めてユーザーに相談する**（案B／案C）。
- [ ] **Step 5: コミットする**
  `git commit -m "feat(manga): Codex 描画ワークフロー"`

---

### Task 4: 組版（`compose.py`）

**Files:**
- Create: `manga_pipeline/compose.py`, `tests/manga_pipeline/test_compose.py`

**Interfaces:**
- Consumes: コマ画像 `p1.png`〜`p8.png`、`note_pipeline.fonts.ensure_fonts()`（Bold を使う）
- Produces:
  - `wrap_lines(text: str) -> list[str]`：`\n` で分けた行を返す。4行以上、または13字以上の行があれば `ValueError`（全角も半角も1字と数える）
  - `compose_rows(script: dict, panel_dir: Path, out_dir: Path) -> list[Path]`：row1〜4.jpg のパスを返す
  - CLI：`python -m manga_pipeline.compose --script script.json --panels DIR --out DIR`
  - `script.json`：
    ```json
    {"title":"…","panels":[{"n":1,"bubbles":[{"speaker":"mirai","text":"先生！日経平均が\n5％も下がってます…！","x":0.38}]}]}
    ```
    `bubbles` は1〜2個、`x` は0〜1（話者の横位置）。

- [ ] **Step 1: 失敗するテストを書く**
  - `test_wrap_ok`：12字×3行が通る。
  - `test_wrap_too_long`：13字の行で `ValueError`。
  - `test_wrap_too_many_lines`：4行で `ValueError`。
  - `test_wrap_mixed_width`：`"SOX指数-10.7%で\n連れ安"` は1行目が12字なので通る。
  - `test_compose_rows_size`：テスト内で作った無地の1024px画像8枚から4枚が出る。各 `(1360, 684)`、各 200KB 以内。
  - `test_bubble_inside_panel`：`x=0.0` と `x=1.0` でも、吹き出しの外枠がコマから14px以上内側にある。吹き出しの矩形を返す内部関数 `bubble_box(text_w, text_h, x) -> tuple[int,int,int,int]` で検証する。
  - `test_rejects_missing_panel`：`p5.png` が無いと `FileNotFoundError`。
- [ ] **Step 2: 失敗を確認する**
  Run: `.venv/bin/python -m pytest tests/manga_pipeline/test_compose.py -q` → FAIL
- [ ] **Step 3: 実装する**
  - 寸法と色は、設計書 §7.5 の「見本の数値」をそのまま定数にする。
    - コマ 660px、段の余白 12px、コマ間 16px
    - 文字 34px、行間 8px
    - 吹き出し：上端から 14px、角丸 28px、枠 3px
    - 尻尾：吹き出しの下端から 34px
    - コマの枠 4px、番号の丸 34px（#1E3A5F）、番号の文字 22px
  - 吹き出しが2つのコマは、2つ目を1つ目の下に 10px 空けて置く。
- [ ] **Step 4: テストが通ることを確認する**
  Run: 同上 → PASS
- [ ] **Step 5: 目で確認する**
  - 試し描きの台本（設計書の題材、セリフは `docs` に置かず、テストの一時ディレクトリで使う）と、Task 3 で得たコマ、または無地画像で組む。
  - スマホ幅 390px の HTML に貼って Playwright でスクリーンショットを撮り、文字が読めることを確かめる。
- [ ] **Step 6: コミットする**
  `git commit -m "feat(manga): 吹き出し組版と段画像の出力"`

---

### Task 5: manifest と納品ページ（`manifest.py`）

**Files:**
- Create: `manga_pipeline/manifest.py`, `tests/manga_pipeline/test_manifest.py`

**Interfaces:**
- Consumes: `note_pipeline.market.is_tse_closed(d: date) -> bool`、Task 4 の row 画像
- Produces:
  - `next_business_day(d: date) -> date`
  - `build_manifest(made_at: datetime, title: str, kind: str, explanation_html: str, rows: list[Path], prev: dict | None) -> dict`：設計書 §7.6 のキーに `kind`（theme/term/stock/caution）と `history`（前回 manifest の history に今回の `{for_date, kind}` を足し、直近5件）を加える。`for_date` は `next_business_day(made_at.date())`、各 row に sha256 を付ける。
  - `render_index(manifest: dict) -> str`：漫画4枚と解説を表示する HTML（画像は `manga/rowN.jpg` を相対参照）
  - CLI：`python -m manga_pipeline.manifest --title T --explanation E.html --rows DIR --out DIR`。`DIR/index.html` と `DIR/manga/manifest.json` を書き、row を `DIR/manga/` にコピーする。

- [ ] **Step 1: 失敗するテストを書く**
  - `test_next_business_day_weekday`：2026-11-24（火）→ 11-25
  - `test_next_business_day_friday`：2026-11-27（金）→ 11-30（月）
  - `test_next_business_day_new_year`：2026-12-30（水）→ 2027-01-04（月）
  - `test_manifest_sha256`：row の sha256 が `hashlib.sha256` と一致する。
  - `test_explanation_needs_disclaimer`：`explanation_html` に「※投資判断はご自身で。」が無ければ `ValueError`。
  - `test_history_keeps_last5`：前回の history 5件＋今回で、最古の1件が落ちて5件になる。
  - `test_index_contains_rows`：index.html に `manga/row1.jpg`〜`row4.jpg` と title がある。
- [ ] **Step 2〜4: 失敗を確認 → 実装 → テストが通ることを確認する**
  Run: `.venv/bin/python -m pytest tests/manga_pipeline/test_manifest.py -q`
  - index.html は白背景、`'Meiryo UI','Noto Sans JP',sans-serif`、最大幅 680px。
- [ ] **Step 5: コミットする**
  `git commit -m "feat(manga): manifest と納品ページ"`

---

### Task 6: 夕方の漫画タスク（手順書・Artifact・定期タスク）

**Files:**
- Create: `docs/manga/evening-task-prompt.md`

**Interfaces:**
- Consumes: Task 2〜5 の CLI、ワークフロー `manga_render.yml`
- Produces:
  - 非公開 Artifact「朝マンガ納品」の固定 URL（以下 `<MANGA_URL>`）
  - 定期タスク「朝マンガ 夕方制作（平日17:45）」（cron `CRON_TZ=Asia/Tokyo 45 17 * * 1-5`）

- [ ] **Step 1: 手順書を書く**
  - 作業はすべて `WORK/`（gitignore 済みか確認。無ければ `.gitignore` に追加）で行う。
  - 東証が休場の日は、何もせず終了する。
  - フェーズは次のとおり。各フェーズに締切を書く。
    1. **題材を決める**（〜18:00）：材料は次の3つ。回の種類と注意喚起の週2回上限を守る（設計書 §4.1）。今週の回の種類は、`<MANGA_URL>` の前回 manifest の `history`（直近5件）で数える。前回 manifest は `--prev` に渡す。
       - 引けの JSON
       - note の納品ページ `https://claude.ai/artifact/Pp1EquXnURMFDYTiLemq9q`
       - Web 検索
    2. **台本・場面プロンプト・解説を作る**（〜18:10）：`WORK/script.json`、`WORK/request.json`、`WORK/explanation.html` に書く。設計書 §4.2、§4.3、§7.3 のルールを転記する。
    3. **描画を依頼する**：GitHub MCP の `actions_run_trigger`（workflow `manga_render.yml`、ref `main`、inputs `request`）を使う。
    4. **完了を待つ**：Monitor の until ループで、1分おきに `git fetch origin manga` して `status.json` の `run_id` を見る。19:15 を過ぎたら見送る。
    5. **確認する**：設計書 §7.4 の5項目で確認する。描き直しは、直す点を足した場面プロンプトで `run_id` r2、r3 として依頼する。
    6. **組版する**：組んで、目で確認する。顔に重なる吹き出しは `x` を直す。
    7. **納品する**：`manifest` CLI → Artifact に publish（初回は新規作成。URL は手順書に書く）。
    8. **通知する**：PushNotification で次のどれかを送る。
       - 成功：「🐾 明日の漫画ができました：<title>」
       - 見送り：「🐾 漫画は本日見送り：<理由>」
       - ログイン切れ：`auth` が `expired` または `persist_failed` なら、見送りの理由を「Codex の再ログインが必要（docs/manga/README.md）」にする。
- [ ] **Step 2: Artifact を作る**
  - 試し描きのコマ（Task 4 Step 5 の出力）で、一度手動で通しで納品する。
  - `<MANGA_URL>` を手順書に書き込む。
- [ ] **Step 3: 定期タスクを作る**
  - `create_trigger` で作る（ユーザーの承認を得て、Gmail は不要）。
  - モデルは opus（台本の質と画像の確認のため）。
  - プロンプトは、既存の note 日次タスクと同じ形にする：リポジトリの取得 → `docs/manga/evening-task-prompt.md` を読んで実行 → 台本・解説はリポジトリに書かない。
- [ ] **Step 4: 手動で1回動かす**
  - `fire_trigger` で1回動かす。
  - 19:30 までに通知が来ること、`<MANGA_URL>` に4枚と解説が出ることを確かめる。
- [ ] **Step 5: コミットする**
  `git commit -m "feat(manga): 夕方の漫画タスク手順"`

---

### Task 7: 朝ブリーフィングへの組み込み

**Files:**
- Create: `docs/manga/briefing-manga.md`
- Modify: 朝ブリーフィングの定期タスクのプロンプト（リポジトリ外。`list_triggers` の2ページ目以降で、件名【デイトレブリーフィング】／【株-朝ブリーフィング】を送っているものを探す）

**Interfaces:**
- Consumes: `<MANGA_URL>` の `manga/manifest.json` と `manga/row1〜4.jpg`

- [ ] **Step 1: `briefing-manga.md` を書く**
  - 設計書 §7.7 の手順1〜5を、`docs/briefing-charts.md` と同じ書き方にする。
  - Artifact の読み方：`action: read, url: <MANGA_URL>, path: "manga/manifest.json"` → `paths` で row 4枚を読む。保存先の絶対パスと `sha256sum` を、添付の `content` に使う。
  - `for_date` が今日でなければ、漫画欄を丸ごと省き、注記もしない。
- [ ] **Step 2: 朝のプロンプトを更新する**
  - `get_trigger` で現在のプロンプトを読む。
  - チャートの手順の後に、1行足す：「最後に `docs/manga/briefing-manga.md` の手順で、漫画欄をフッターの前に入れる」。
  - `update_trigger` で更新する（ユーザーの承認を得て）。
- [ ] **Step 3: 確認する**
  - 翌朝の配信後、Gmail でメールの最下部に4枚と解説があることを確かめる。
  - スマホの Gmail でセリフが読めることを、ユーザーに確かめてもらう。
- [ ] **Step 4: コミットする**
  `git commit -m "feat(manga): 朝ブリーフィングに漫画欄を追加"`

---

## 実行の順番

Task 1 → (Task 2 ∥ ユーザーの Secrets 登録) → **Task 3（ゲート）** → Task 4 → Task 5 → Task 6 → Task 7。
Task 3 の Step 4 が駄目なら、Task 4 以降に進まずにユーザーへ相談する。
