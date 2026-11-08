# note / X 発信パイプライン Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 日次タスク（平日16:15）と週1有料記事の Claude 定期タスクが使う「図表・見出し画像・納品ページ」の生成ツールと、タスク用プロンプトをリポジトリに用意する。

**Architecture:** Python パッケージ `note_pipeline/` を追加する。記事本文は定期タスク（Claude）が書き、スクラッチパッドに置いた JSON（記事・図の定義）を `python -m note_pipeline.build` に渡すと、図（JPEG）・見出し画像・納品ページ HTML が出力ディレクトリにそろう。それを Artifact ツールで固定URLに上書き公開する。リポジトリには生成コード・ブランド素材・プロンプトのみを置き、記事本文は置かない。納品ページと図のデザインは、初回有料記事（中間選挙、https://claude.ai/artifact/JB4vSK8bM71sDAjsM4K6he ）を雛形にする。

**Tech Stack:** Python 3.11+, matplotlib, fontTools, Pillow, jpholiday, pytest

**Spec:** `docs/superpowers/specs/2026-11-04-note-content-pipeline-design.md`（ブランチ `claude/gallant-noether-lb8jru` から取り込む）

## Global Constraints

- 図: 1280×720px を 1.5 倍（1920×1080）で書き出し、JPEG 品質 90。ファイル名は `fig{n}.jpg`（日次は `a{記事番号}_fig{n}.jpg`）。右上に通し番号（①②…）。
- 見出し画像: 1280×670px を 1.5 倍（1920×1005）。背景 テーマ＝ネイビー、注目銘柄＝グリーン、有料＝ゴールド。
- 配色: ネイビー `#1E3A5F`、ゴールド `#C9A227`（強調1点のみ）、上昇 `#2E8B57`、下落 `#C0392B`、背景 `#FAF8F3`。
- 左上=結論タイトル、左下=出典と日付、右下=コーギーロゴ（小さく半透明）。
- フォント: Noto Sans JP の可変フォントから fontTools で Regular(400)/Bold(700) の静的フォントを作って使う（Thin 描画の回避）。
- 売買推奨表現（「買い」「目標株価」「損切り」「推奨」「今がチャンス」等）を使わない。全記事の末尾に「🐾投資判断はご自身で🐾」。
- X投稿文: 140字以内、ハッシュタグ2個まで。
- 記事本文・有料記事をリポジトリにコミットしない。テストのフィクスチャもダミー文のみ。
- 納品ページに「一括ダウンロード」ボタンを作らない。

## Review Focus

1. 東証休場日（土日・祝日・振替休日・12/31〜1/3）に日次タスクが走ったとき → 何もせず終了する。`market.is_tse_closed` のテスト（Task 2）。
2. 引けJSONが当日分でない／status が OK 以外 → 「Web検索で補完」が必要と判定される。`market.check_closing_freshness` のテスト（Task 2）。
3. 記事が3本そろわない（1〜2本）→ 納品ページは本数分だけ表示し、一覧も崩れない。`page.render_daily` のテスト（Task 3）。
4. 本文・タイトル・X投稿文に `<`・`&`・引用符が入る → HTML が壊れない（タイトルとX文はエスケープ、本文 HTML はそのまま）。`page` のテスト（Task 3）。
5. 直近14日に書いた銘柄の除外 → 前回の納品ページに埋め込んだ履歴から読み戻せ、15日以上前は消える。`history` のテスト（Task 2）。

---

### Task 1: フォント・スタイル・図の型（A〜F）・見出し画像

**Files:**
- Create: `note_pipeline/__init__.py`, `note_pipeline/fonts.py`, `note_pipeline/style.py`, `note_pipeline/charts.py`, `note_pipeline/header.py`
- Create: `assets/brand/README.md`, `assets/brand/logo_navy.png`, `assets/brand/corgi_tophat.png`（試作画像から切り出した暫定素材）
- Create: `requirements-note.txt`
- Test: `tests/note_pipeline/test_charts.py`

**Interfaces:**
- Produces:
  - `fonts.ensure_fonts(cache_dir: Path | None = None) -> dict[str, Path]` キー `"regular"`/`"bold"`。キャッシュ既定 `~/.cache/note_pipeline/fonts`。matplotlib に登録し `rcParams["font.family"]` を設定。
  - `style.PALETTE: dict[str,str]`（navy, gold, up, down, bg, muted, grid）
  - `style.new_canvas(title: str, subtitle: str, source: str, number: int) -> tuple[Figure, Axes]` … 1280×720 キャンバスと本体領域の Axes
  - `style.save_jpeg(fig, path: Path, logo: bool = True) -> Path` … 品質90、右下ロゴ合成
  - `charts.render(spec: dict, out_path: Path, number: int) -> Path` … `spec["type"]` が `"A"`〜`"F"` で分岐。不明な型は `ValueError`。
  - 各型の spec キー: A `{dates, close, volume, annotations:[{date,text}]}` / B `{periods, sales, op_income, forecast_from}` / C `{columns, rows:[{name, values}], shade_cols}` / D `{cards:[{label, value, sub, tone}]}`（tone は up/down/navy） / E `{labels, values, highlight}` / F `{boxes:[{text}], arrows:[[i,j]]}` もしくは `{table:{header, rows, emphasis_col}}`（試作の図⑦型）
  - 全型共通キー: `title, subtitle, source`、任意 `web_search: bool`（真なら出典に「Web検索値」を付ける）
  - `header.render_header(kind: Literal["theme","stock","paid"], label: str, title: str, lead: str, out_path: Path) -> Path`

- [ ] **Step 1: テストを書く** — `test_each_chart_type_renders_1920x1080_jpeg`（A〜F 全型を最小 spec で描き、Pillow で開いて `size == (1920,1080)`、format JPEG）、`test_unknown_type_raises`、`test_web_search_note_in_source`（`style.source_text(source, web_search=True)` が「Web検索値」を含む）、`test_header_sizes_and_bg`（3種とも `(1920,1005)`、左端ピクセルの色がそれぞれネイビー/グリーン/ゴールド系）、`test_fonts_are_static_400_700`（生成フォントに `fvar` テーブルが無く、`OS/2.usWeightClass` が 400/700）。
- [ ] **Step 2:** `pytest tests/note_pipeline/test_charts.py -q` → import エラーで FAIL
- [ ] **Step 3:** 実装。フォントは `https://raw.githubusercontent.com/google/fonts/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf` を取得し `fontTools.varLib.instancer.instantiateVariableFont(font, {"wght": 400|700})`。ロゴは `assets/brand/logo_navy.png` を円形マスク・不透明度0.85で右下に。デザインは試作 fig1/fig2/fig7/header に合わせる。
- [ ] **Step 4:** テスト PASS
- [ ] **Step 5:** commit `feat(note): chart types A-F, header image, font setup`

### Task 2: 材料チェック・休場日・銘柄履歴・表現チェック

**Files:**
- Create: `note_pipeline/market.py`, `note_pipeline/history.py`, `note_pipeline/lint.py`
- Test: `tests/note_pipeline/test_market.py`, `tests/note_pipeline/test_history.py`, `tests/note_pipeline/test_lint.py`

**Interfaces:**
- Produces:
  - `market.is_tse_closed(d: date) -> bool`（土日、jpholiday の祝日、12/31、1/1〜1/3）
  - `market.check_closing_freshness(repo_dir: Path, today: date) -> dict[str, str]` ファイル名→ `"ok" | "stale" | "missing" | "error"`。対象 `screening_result_closing.json` / `screening_stophigh_closing.json` / `macro_result_closing.json`。`fetched_at` の日付が today と違えば stale、`status != "OK"` は error。
  - `history.HISTORY_META = "note-pipeline:history"`
  - `history.parse_history(html: str) -> dict[str, list[str]]`（日付ISO→銘柄コード）。meta が無ければ `{}`
  - `history.update_history(hist, today: date, codes: list[str], keep_days: int = 14) -> dict` … today 追加、14日より古い日を削除
  - `history.recent_codes(hist, today, days=14) -> set[str]`
  - `history.meta_tag(hist) -> str` … `<meta name="note-pipeline:history" content="…JSON…">`（属性エスケープ済み）
  - `lint.check_text(text: str) -> list[str]` … 推奨表現の検出。`買い推奨|買い場|買い時|今が買い|目標株価|損切|推奨|今がチャンス|売り推奨|利確` を検出し、否定の免責文「推奨するものではありません」は除外。
  - `lint.check_xpost(text: str) -> list[str]` … `len(text) > 140` と `#` タグ数 > 2、および `check_text` の結果

- [ ] **Step 1: テストを書く** — `is_tse_closed`: 2026-11-03（文化の日）True、2026-11-04 False、2026-11-07（土）True、2027-01-02 True、2026-12-31 True。`check_closing_freshness`: tmp に fetched_at "2026-11-04 15:35 JST" の3ファイル→全 ok／前日付→stale／欠落→missing／status "NG"→error。`history`: parse(meta_tag(h)) == h、20日前の項目が update で消える、meta 無し HTML→{}、recent_codes が14日以内のみ。`lint`: 「今が買い場です」「目標株価は3000円」で検出、「特定の銘柄の売買を推奨するものではありません」「その後買い戻し」で検出なし、141字の X 文と3タグで2件。
- [ ] **Step 2:** FAIL を確認
- [ ] **Step 3:** 実装
- [ ] **Step 4:** PASS を確認
- [ ] **Step 5:** commit `feat(note): holiday/freshness checks, ticker history, wording lint`

### Task 3: 納品ページ生成（日次・有料）と build CLI

**Files:**
- Create: `note_pipeline/page.py`, `note_pipeline/templates/page.css`, `note_pipeline/templates/page.js`, `note_pipeline/build.py`, 起動は `python -m note_pipeline.build`
- Create: `tests/note_pipeline/fixtures/daily_sample.json`, `tests/note_pipeline/fixtures/paid_sample.json`（ダミー文）
- Test: `tests/note_pipeline/test_page.py`, `tests/note_pipeline/test_build.py`

**Interfaces:**
- Consumes: Task 1 `charts.render`, `header.render_header`; Task 2 `history.meta_tag`, `lint.check_text`, `lint.check_xpost`
- Produces:
  - 記事 dict: `{id, kind: "theme"|"stock"|"paid", label, titles: [3], summary, header: {title, lead}, body_html, figures: [chart spec], xposts: [2], sources: [{label, url}], notes: [str]}`。`body_html` 内の `<!--fig:N-->` を `<p>［図N］</p><figure><img src=…></figure>` に置換する（試作と同じく［図○］のマーカーと画像を並べる）。有料記事は `<!--paywall-->` を試作の `.paywall` に置換。
  - `page.render_daily(day: dict, img_names: dict[str, list[str]], history_meta: str) -> str` … day = `{date, articles: [1..3], candidates: [{title, reason}], notes: [str]}`。冒頭一覧（見出し縮小・タイトル・一行要約・`#a{id}` リンク）→記事カード×n→選外候補。
  - `page.render_paid(day: dict, img_names, history_meta="") -> str` … 試作ページと同じ構成（タイトル案3・見出し画像・本文コピーバー・本文・X投稿2案・出典）。`day = {date, price, articles: [1 paid]}`
  - 本文コピー: 記事ごとに「本文をコピー（見出し・太字つき）」「プレーンテキストでコピー」。コピー時は figure を除き paywall を「――――（ここから有料）――――」に置換（試作のJS）。
  - `build.main(argv) -> int` … `python -m note_pipeline.build --input day.json --out OUTDIR [--mode daily|paid]`。OUTDIR に `index.html` と `img/*.jpg` を出力。lint の警告を stderr に出し、警告があれば終了コード 2（出力は行う）。`--prev-page prev.html` で履歴を引き継ぎ、注目銘柄記事の `codes` を追記。

- [ ] **Step 1: テストを書く** — `test_daily_renders_three_cards_and_index`（`id="a1"`〜`a3`、一覧リンク3つ、`img/a1_fig1.jpg`、選外候補が表示）、`test_daily_with_one_article`（カード1つ、一覧1行）、`test_titles_escaped`（タイトル `A<b>&"` が `A&lt;b&gt;&amp;` で出る）、`test_fig_marker_replaced`、`test_paid_has_paywall_and_disclaimer_kept`、`test_no_bulk_download`（"一括ダウンロード" を含まない）、`test_build_writes_index_and_images`（fixture で `index.html` と全画像が出来、JPEG が各 250KB 以下）、`test_build_lint_exit_code`（「今が買い場」を含めると 2）、`test_history_carried`（`--prev-page` の履歴＋今日の codes が meta に入る）。
- [ ] **Step 2:** FAIL を確認
- [ ] **Step 3:** 実装。CSS/JS は試作ページから移植（ダーク対応トークン・sticky バー・clipboard フォールバック）。日次の記事カードはコピーバーをカードごとに持つ。
- [ ] **Step 4:** PASS を確認、`--mode paid` で中間選挙ページ相当が出ることをスクラッチパッドで目視（本文は試作から一時的に読み込むだけでコミットしない）
- [ ] **Step 5:** commit `feat(note): delivery page renderer and build CLI`

### Task 4: 定期タスク用プロンプトと運用手順

**Files:**
- Create: `docs/note-pipeline/daily-task-prompt.md`（§4 の流れ、§4.2〜4.5 テンプレート、§8 失敗時、§7 通知文、固定URL・Artifact 上書き・ピン、17:30 保証）
- Create: `docs/note-pipeline/weekly-paid-prompt.md`（§9、土曜午前、`--mode paid`）
- Create: `docs/note-pipeline/README.md`（セットアップ、day.json の書式、§10 の動作確認手順、§11 の注意）

- [ ] **Step 1:** プロンプトを書く。入力 JSON の例は Task 3 の記事 dict と同じキーを使う。
- [ ] **Step 2:** `python -m note_pipeline.build --input tests/note_pipeline/fixtures/daily_sample.json --out <scratch>` が通ることを README の手順どおりに確認
- [ ] **Step 3:** commit `docs(note): scheduled-task prompts and runbook`

定期実行の有効化（§10-3）は、ユーザーが手動実行の結果を確認した後に行う。本計画には含めない。
