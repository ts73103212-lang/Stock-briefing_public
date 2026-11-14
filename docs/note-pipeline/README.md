# note / X 発信パイプライン

設計書: `docs/superpowers/specs/2026-11-04-note-content-pipeline-design.md`
実装計画: `docs/superpowers/plans/2026-11-04-note-content-pipeline.md`

体制（サブエージェント）: `docs/superpowers/plans/2026-11-08-note-subagent-organization.md`
- 進行役プロンプト: `candidates-task-prompt.md`（平日11:47、ネタ候補10本）、`daily-task-prompt.md`（平日16:15、選ばれた分だけ執筆）、`weekend-candidates-prompt.md`（土日8:05（9:00までに掲載）、有料記事のテーマ候補5本）、`weekly-paid-prompt.md`（土日16:30、選ばれた1本を執筆）
- ネタ選びページ: `picker.html`（公開先 https://claude.ai/artifact/9VFKNAzE2WiupWAPoj7bir 。データベース `days/<日付>`＝候補、`picks/<日付>`＝選択、`notes/<日付>`＝12時の調査メモ。本人だけが読み書きできる）
- 週末のネタ選びページ: `weekend-picker.html`（公開先 https://claude.ai/artifact/CFwy1xxH6MQMp5V64fHHP1 。`days`・`picks`・`notes` の構造は平日と同じ。土日とも 16:00 締切、1日1本）
- 平日の流れ: 11:47 候補10本（話題・用語・トリッキー4＋個別銘柄6）→ 16:15 までにユーザーが「通常1〜3本・長文（有料）1本まで・自由記述1枠」を選ぶ → 16:15 選ばれた分だけ書く（通常は17:30まで、長文は19:30までに通知。選ばれなければお休み）
- 役割定義: `.claude/agents/note-*.md`（PM・相場分析・日本株・米国株・個別株分析・証券アナリスト・視覚化）
- 全員が読む編集ルール: `editorial-rules.md`

このリポジトリは公開のため、**記事本文は置きません**。ここにあるのは図表・見出し画像・納品ページの生成コード（`note_pipeline/`）、ブランド素材（`assets/brand/`）、定期タスク用プロンプトだけです。

## セットアップ

```bash
python3 -m venv .venv && .venv/bin/python -m pip install -r requirements-note.txt  # OS の Pillow との衝突を避けるため venv を使う
.venv/bin/python -m pip install pytest && .venv/bin/python -m pytest tests/note_pipeline -q
```

初回実行時に Noto Sans JP の可変フォントを GitHub（google/fonts）から取得し、Regular(400)/Bold(700) の静的フォントを `~/.cache/note_pipeline/fonts` に作ります（matplotlib が可変フォントを細字で描くため）。

## 使い方

```bash
.venv/bin/python -m note_pipeline.build --input day.json --out out/ [--mode daily|paid] [--prev-page prev.html]
```

- `out/index.html` と `out/img/*.jpg`（JPEG 品質90）ができる。日次は `a{記事id}_header.jpg` / `a{記事id}_fig{n}.jpg`、有料は `header.jpg` / `fig{n}.jpg`。
- 終了コード: 0＝OK、2＝警告あり（推奨表現・X投稿文の字数/タグ数・免責文の欠落。出力は作られる）、1＝入力エラー。
- `--prev-page`: 前回の納品ページ HTML。埋め込まれた銘柄履歴（`<meta name="note-pipeline:history">`）を引き継ぎ、14日より古い分を消して今日の `codes` を足す。

### サブエージェントの成果物をまとめる

```bash
.venv/bin/python -m note_pipeline.figs --spec WORK/figs/a1.json --out WORK/figs/a1/     # 視覚化担当の確認用
.venv/bin/python -m note_pipeline.assemble --work WORK --out WORK/day.json             # plan.json + drafts + figs + verdict → day.json
```

納品ページには銘柄履歴（14日）と今週の記事一覧（`note-pipeline:digest`、7日）が埋め込まれ、翌日・週末のタスクが読み戻します。

## day.json の書式

```json
{
  "date": "2026-11-05",
  "mode": "daily",
  "notes": ["メルマガ未着のため、ニュースとデータだけでテーマを選びました"],
  "candidates": [{"title": "候補の銘柄・テーマ", "reason": "選外の理由"}],
  "articles": [
    {
      "id": "1",
      "kind": "theme",
      "label": "テーマ",
      "titles": ["タイトル案1", "タイトル案2", "タイトル案3"],
      "summary": "一行要約",
      "header": {"title": "見出し画像の大きな文字", "lead": "見出し画像の小さな文字"},
      "body_html": "<p>はじめに…</p><h2>1. 数字で見る現状</h2><!--fig:1--> … <p><b>🐾投資判断はご自身で🐾</b></p>",
      "figures": [{"type": "D", "title": "結論を一言で", "subtitle": "2026年11月5日", "source": "出典：…", "cards": []}],
      "xposts": ["案1", "案2"],
      "sources": [{"label": "株探 …", "url": "https://…"}],
      "notes": ["日経平均終値は報道の大引け値を採用（JSONは…）"],
      "codes": ["6857"]
    }
  ]
}
```

- `kind`: `theme`（見出し画像ネイビー）/ `stock`（グリーン、`codes` 必須）/ `paid`（ゴールド）
- `body_html`: `<h2>` `<h3>` `<p>` `<b>` `<ul>` `<blockquote>` 程度。`<!--fig:N-->` が［図N：タイトル］と画像に置き換わる。有料記事は `<!--paywall-->` が有料エリア境界。
- 有料モードは `price`（例 "300円（案）"）と `meta`（字数・無料/有料の範囲の説明）を追加。

### 図の型（`figures[].type`）

共通キー: `title`（結論を一言で）, `subtitle`, `source`, 任意 `web_search: true`（出典に「Web検索値」）, 任意 `alt`

| 型 | 用途 | キー |
|---|---|---|
| A | 株価（終値線）＋出来高、重要日に注釈 | `dates`(ISO), `close`, `volume`（欠損は null）, `annotations: [{date, text, pos?, y?, style?, highlight?}]`, `hlines: [{y, label?, color?, style?}]`, `ylim: [lo, hi]` |
| B | 売上・営業利益（予想は斜線） | `periods`, `sales`, `op_income`, `forecast_from`(予想が始まる添字), 任意 `unit`, `series_labels`（例 ["売上収益","営業利益"]） |
| C | 同業比較表（大小を色の濃さで） | `columns`, `rows: [{name, values}]`, `shade_cols`(濃淡を付ける列の添字) |
| D | 指標カード（最大6枚） | `cards: [{label, value, sub, tone: up/down/navy}]` |
| E | 横棒の順位（騰落率） | `labels`, `values`, `highlight`(ゴールドにする1本), 任意 `unit` |
| F | 図解（フロー）または表 | `boxes: [{text, note?, emphasis?}]` + `arrows: [[i, j]]`、または `table: {header, rows, emphasis_col}` |

### 型A の追加オプション

- `hlines`: 水平線。`color` は gold（既定）/ up / down / navy / muted、`style` は dashed（既定）/ dotted / solid。例: `{"y": 1851.5, "label": "自社株買い価格 1,851.5円"}`
- 注釈の `pos`: 吹き出しの位置。above / below / left / right / above-left / above-right / below-left / below-right。省略時は自動。
- 注釈の `y`: 終値以外の点を指す（場中高値、ストップ高の値など）。
- 注釈の `style: "note"`: 枠なしの小さな注記（点と出来高の色付けもしない）。`highlight: false` で金の点・出来高の色付けだけを止める。
- `ylim`: 縦軸の範囲。

## 動作確認（設計書 §10）

1. 定期実行を有効にする前に、対話チャットで `daily-task-prompt.md` の手順を1回手動で実行し、納品ページを作る（このとき固定URLができる。サイドバーにピン留め）。
2. ページの見た目・各コピー・画像の長押し保存を確認する。
3. 「本文をコピー → note に貼り付け」で見出し・太字が崩れないことを実機で確認する。
4. 問題なければ、`<DELIVERY_URL>` を埋めたプロンプトで平日 16:15 JST の定期タスクを作る（Gmail コネクタを付ける）。

## 実装時の注意（設計書 §11）

- Yahoo Finance（`query1/query2.finance.yahoo.com`, `fc.yahoo.com`）は環境のネットワーク設定で拒否・制限されることがある。型A・B の個別株データに必要。
- 長期の米国株は `raw.githubusercontent.com/datasets/s-and-p-500`（Shiller 月次）で取得できる。
- `macro_result_closing.json` の日経平均終値（15:35取得）は報道の大引け値と一致しない日がある。記事では報道値を優先し、差異を出典欄に記す。
- ブランド素材のうち `corgi_hunting.png`（注目銘柄の見出し）と `thank_you.png` は未配置。`assets/brand/README.md` 参照。
