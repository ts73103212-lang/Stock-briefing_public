# note 記事制作のサブエージェント体制 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 日次（平日16:15）と週末の有料記事を、役割を分けたサブエージェントのチームで作る。証券アナリストが各専門エージェントの調査をまとめて記事を書き、PM がレビュー・差戻し・最終精査する。

**Architecture:** 定期タスクのメインセッションは「進行役」に徹し（前処理・エージェント起動・ファイル受け渡し・ビルド・公開・通知）、判断と執筆はすべてサブエージェントが行う。エージェント同士はスクラッチパッドの作業ディレクトリ `WORK/` のファイルで情報を受け渡し、進行役に返すのは数行の要約だけにする（進行役のコンテキストを小さく保つ）。役割定義は `.claude/agents/note-*.md` に置き、共通の編集ルールは `docs/note-pipeline/editorial-rules.md` に一本化する。

**Tech Stack:** Claude Code サブエージェント（Agent ツール）、既存の `note_pipeline`（Python）、Artifact、Gmail コネクタ、定期タスク

**Spec:** `docs/superpowers/specs/2026-11-04-note-content-pipeline-design.md`（前計画 `2026-11-04-note-content-pipeline.md` の成果物の上に作る）

## 組織

| エージェント | ファイル | モデル | 役割 | 主な出力 |
|---|---|---|---|---|
| 進行役（メインセッション） | 定期タスクのプロンプト | — | 休場日判定・材料準備・起動順の管理・時間管理・ビルド・公開・通知。**記事の中身は判断しない** | `WORK/inputs/*`、最終ページ |
| PM | `note-pm` | opus | ①ネタ決定（調査報告から3本と選外候補を決める）②レビュー（チェックリストで承認／差戻し／見送り）③最終精査（軽微な語句は自分で直す） | `plan.json`、`review/r{n}.md`、`review/verdict.json` |
| 相場分析 | `note-market-analyst` | sonnet | 指数・為替・セクター・メルマガ/振り返りメールのシグナルから「今日のテーマ候補」を出す。テーマ記事の深掘り調査も担当 | `research/market.md`、`deep/a1.md` |
| 日本株 | `note-jp-equity` | sonnet | スクリーニング結果・ストップ高・出来高急増・ニュースから注目銘柄候補（5〜8件、業種分散、直近14日除外）を出す | `research/jp.md` |
| 米国株 | `note-us-equity` | sonnet | 前夜〜当日の米国市場・SOX・米国発の材料と日本株への波及 | `research/us.md` |
| 個別株分析 | `note-stock-analyst` | sonnet | 選ばれた1銘柄の材料・IR・株価/出来高・業績・バリュエーション・強気/弱気論点（銘柄ごとに並列起動） | `deep/a{id}.md`（図用データ付き） |
| 証券アナリスト | `note-securities-analyst` | opus | 調査報告をまとめ、テンプレートどおりに記事を書く（タイトル3案・本文・X投稿2案・出典・図の依頼）。差戻しの修正 | `drafts/a{id}.json` |
| 視覚化スペシャリスト | `note-viz` | sonnet | 図の依頼を図 spec（型A〜F）にし、描画して目視確認・修正 | `figs/a{id}.json`、`figs/a{id}/*.jpg` |

相場分析と日本株・米国株を分けるのは、テーマ（全体相場）と銘柄選び（個別）と海外要因を並列に調べて時間内に収めるため。個別株分析は「選ばれた1銘柄を深く」、日本株は「候補を広く」で重ならない。

## 日次の流れ（16:15 起動、17:30 通知が保証ライン）

| 目安 | フェーズ | 実行 | 並列 |
|---|---|---|---|
| 16:15 | 0 準備 | 進行役: 休場日判定、引けJSONの鮮度、前回ページ取得（銘柄履歴）、メールから**シグナルだけ**抽出 → `WORK/inputs/` | — |
| 16:20 | 1 調査 | 相場分析・日本株・米国株 | 3 |
| 16:35 | 2 ネタ決定 | PM → `plan.json` | 1 |
| 16:40 | 3 深掘り | 相場分析（テーマ）＋個別株分析×2 | 3 |
| 16:55 | 4 執筆 | 証券アナリスト×3（記事ごと） | 3 |
| 17:07 | 5 図 | 視覚化×3（記事ごと） | 3 |
| 17:15 | 6 レビュー | PM（3本まとめて） | 1 |
| 17:18 | 7 差戻し | 該当の証券アナリスト／視覚化のみ。**1回まで**。17:20 を過ぎていたら差戻しせず、PM が軽微修正で承認するか見送る | ≤3 |
| 17:23 | 8 最終精査 | PM（差戻し分のみ） | 1 |
| 17:25 | 9 納品 | 進行役: assemble → build → Artifact 上書き → 通知 | — |

- どのフェーズでも 1 本が失敗したら、その記事だけ見送って残りを進める（設計書 §8）。
- 進行役は各フェーズの開始時刻を `WORK/timeline.txt` に記録し、手動テストで所要時間を測る。

## 週末（有料記事、土曜午前）

日次の流れと同じチームで、時間制約の代わりに品質を優先する。
1. 進行役: 納品ページの埋め込み「今週の記事一覧」（`note-pipeline:digest`）を読む。
2. PM: 今週の記事から最も深掘りしがいのあるテーマを1つ決め、調査の観点を割り振る（`plan.json`、mode=paid）。
3. 相場分析・日本株・米国株（必要なら個別株分析）が並列で深掘り（長期データ・歴史の比較を含む）。
4. 証券アナリスト: 7,000字級、無料／有料の境界つき。視覚化: 図5〜6枚。
5. PM レビュー（差戻し**2回まで**）→ 最終精査 → 納品（見出しはゴールド）。

> 設計書 §9 は「日次が1〜2週間安定してから自動化」としているが、ユーザー指示（2026-11-08）により日次と同時に週末も定期運用を始める。

## Global Constraints

- 設計書 §2 の法令・著作権・保存先の制約はすべてのエージェントに適用（`editorial-rules.md` に集約）。
- メルマガの本文は進行役もエージェントも転載・要約しない。`inputs/mail.md` には「話題の語句・銘柄名・強調箇所の語句」だけを書く。
- 記事本文・調査メモは `WORK/`（スクラッチパッド）にだけ置き、リポジトリにコミットしない。
- エージェントが進行役に返す要約は 10 行以内。詳細はファイルに書く。

## Review Focus

1. 記事の下書きが欠けている／PM が見送った記事 → `assemble` が残りの記事だけで day.json を作り、注記を入れる（Task 1 のテスト）。
2. 図の spec が無い記事 → 図なしで組み立てられる（Task 1）。
3. 週末タスクが今週の記事一覧を読めない（ダイジェスト未埋め込み）→ 空として扱い、PM が市況から選ぶ（Task 1）。
4. 7日より古いダイジェストが残り続ける → 更新時に消える（Task 1）。
5. サブエージェント定義が読み込まれない環境 → 進行役が general-purpose に役割ファイルを読ませて代替する（Task 2 のプロンプトに明記）。

---

### Task 1: 受け渡し用の小さなツール（assemble / figs / digest）

**Files:**
- Create: `note_pipeline/assemble.py`, `note_pipeline/figs.py`
- Modify: `note_pipeline/history.py`（名前つき meta に一般化し、ダイジェストを追加）、`note_pipeline/build.py`（ダイジェストを埋め込む）
- Test: `tests/note_pipeline/test_assemble.py`, `tests/note_pipeline/test_history.py`, `tests/note_pipeline/test_build.py`

**Interfaces:**
- `assemble.assemble(work: Path) -> dict` … `plan.json`（date, mode, price, meta, articles[{id, kind, …}], candidates, notes）と `drafts/a{id}.json`、`figs/a{id}.json`、任意の `review/verdict.json`（{"a1": "approve"|"drop"}）から day.json を作る。下書きが無い記事・drop の記事は除き `notes` に「記事{id}（{kind名}）は見送り」を足す。`figure_requests` キーは除く。
- CLI: `python -m note_pipeline.assemble --work WORK --out WORK/day.json`（記事が0本なら終了コード1）
- `figs.main(argv)`: `python -m note_pipeline.figs --spec figs/a1.json --out figs/a1/` → `fig{n}.jpg` を書いてパスを表示（視覚化エージェントの確認用）
- `history.DIGEST_META = "note-pipeline:digest"`、`history.parse_meta(html, name) -> dict`、`history.meta_tag(hist, name=HISTORY_META)`、`history.update_digest(dig, today, items: list[dict], keep_days=7)`（items は {kind, title, summary}）
- build は `--prev-page` のダイジェストを引き継ぎ、今日の全記事を足して埋め込む

- [ ] テストを書く（assemble: 3本正常／1本下書き欠落→2本＋注記／verdict drop／figs 無し→figures 空／figure_requests 除去／0本で CLI 終了コード1。figs CLI: 2 spec → 2枚。digest: 往復・8日前削除・build で埋め込み）
- [ ] FAIL を確認 → 実装 → PASS を確認 → commit

### Task 2: エージェント定義・編集ルール・進行役プロンプト

**Files:**
- Create: `.claude/agents/note-pm.md`, `note-market-analyst.md`, `note-jp-equity.md`, `note-us-equity.md`, `note-stock-analyst.md`, `note-securities-analyst.md`, `note-viz.md`
- Create: `docs/note-pipeline/editorial-rules.md`（文体・禁止表現・テンプレート・X投稿・出典ルール。全エージェントが最初に読む）
- Modify: `docs/note-pipeline/daily-task-prompt.md`, `weekly-paid-prompt.md`, `README.md`

- [ ] 各エージェント定義に「入力ファイル・出力ファイル（書式）・やらないこと・返す要約の形」を書く
- [ ] 進行役プロンプトにフェーズ表、時間管理、失敗時の扱い、エージェント定義が読めないときの代替（general-purpose ＋「`.claude/agents/note-xx.md` を読んでその役割として動く」）を書く
- [ ] commit

### Task 3: 手動テスト（日次・直近営業日 11/6 分）

- [ ] 進行役プロンプトどおりにこのセッションで実行（休場日判定は「テスト実行・対象日 2026-11-06」として上書き）
- [ ] 各フェーズの所要時間を記録し、75分に収まるか確認。収まらなければフェーズ配分を直す
- [ ] 納品ページを公開してユーザーが確認（見た目・コピー・note 貼り付け）

### Task 4: 定期運用の開始

- [ ] 日次: 平日 16:15 JST、毎回新しいセッション、Gmail コネクタ、プッシュ通知
- [ ] 週末: 土曜午前、同上
- [ ] 実行コードの取得方法（main へのマージ、または起動時にこのブランチから取り込む）をプロンプトに明記

## 手動テストの結果（2026-11-08、対象日 11/6）

- 3本とも PM 承認で納品（差戻し2本・1回）。所要約26分。
- 判明した問題と対応:
  - サブエージェントの WebFetch はプロキシを通らず名前解決に失敗 → `curl` で取得するよう editorial-rules に明記。
  - 報道・TDnet・Yahoo!ファイナンス時系列がネットワーク設定で拒否 → 環境の許可リストに追加（ユーザー承認済み）。株探・IR BANK・stooq・Yahoo Finance API はサイト側が拒否するため使わない。
  - 個別株の日足は Yahoo!ファイナンスの時系列ページで取得できる → 型Aは日足で描く。引けJSONの vol_ratio は算出期間不明のため記事に使わない。
  - 図: 型Bのラベル重なり、型Aの出来高欠損・日付目盛り重複・出来高目盛りなし、型Eの長いラベル、見出しの禁則 → コード修正済み。
  - ストップ高JSONにトヨタ（7203）の異常値（出来高400株・時価総額358兆円）→ fetch 側の調査が必要（未対応）。
