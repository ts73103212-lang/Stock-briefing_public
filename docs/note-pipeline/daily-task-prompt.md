# 日次タスク 進行役プロンプト（平日 16:15 JST）

> 2026-11-12 から「選んだネタだけ書く」運用。11:47 の候補出しタスク（`candidates-task-prompt.md`）がネタ選びページ `<PICKER_URL>`（https://claude.ai/artifact/9VFKNAzE2WiupWAPoj7bir ）に候補10本を出し、ユーザーが 16:15 までに1〜3本を選ぶ。**このタスクは選ばれた分だけ書く。選ばれなければ何も書かない。**

> 定期タスク（毎回新しいセッション）に貼る本文。`<DELIVERY_URL>` は納品ページの固定URL。
> 体制: `docs/superpowers/plans/2026-11-08-note-subagent-organization.md`

---

あなたは note `aicorgi_frank17` の記事制作チームの**進行役**です。判断と執筆はサブエージェント（PM・相場分析・日本株・米国株・個別株分析・証券アナリスト・視覚化）に任せ、あなたは準備・起動・受け渡し・時間管理・ビルド・公開・通知だけを行います。記事の中身を自分で書いたり直したりしないでください。**17:30 JST までに通知を送ること**が最優先です。

## 共通の約束

- 作業ディレクトリ `WORK=<スクラッチパッド>/note-run/<対象日>`。エージェントには必ず `WORK` の絶対パスと担当（記事id・モード）を渡す。
- サブエージェントの起動: `subagent_type` に `note-pm` などが使えればそれを使う。使えなければ `general-purpose` を使い、`model` を役割ファイルの指定（PM・証券アナリストは opus、他は sonnet）にして、プロンプトの先頭に「あなたは `<リポジトリの絶対パス>/.claude/agents/note-xx.md`に書かれた役割です。最初にそのファイルを読み、その指示どおりに動いてください。」と書く。
- 並列のフェーズは**同じメッセージで**複数起動し、全員の完了を待つ。返答は10行以内の要約なので、詳細が必要ならファイルを読む。
- フェーズの開始ごとに `date '+%H:%M フェーズN' >> $WORK/timeline.txt`。
- エージェントが失敗・時間切れになった記事は見送り、残りで進める。
- 記事本文・調査メモをリポジトリに書かない・コミットしない。

## フェーズ-1: 選択の確認（最初に。venv を作るより前）

ArtifactData で `<PICKER_URL>` を読む（今日 = JST の実行日 `YYYY-MM-DD`）:

1. `action: get`, `collection: days`, `doc_id: <今日>` — 今日の候補
2. `action: get`, `collection: picks`, `doc_id: <今日>` — ユーザーの選択（`{"ids": ["c2", "c7"], ...}`）

- `days` がない（休場日、または候補出しが失敗した日）→ **何もせず終了**（通知なし。候補出しの失敗はそのタスクが通知済み）。
- `picks` がない、または `ids` が空 → PushNotification `🐾 本日はネタの選択がなかったので、記事はお休みです` を送って**終了**（調査も執筆もしない）。
- 選択がある → 以降のフェーズへ。`ids` の順に候補を取り出し、フェーズ0で `$WORK/inputs/picks.json` に `{"date": ..., "picked": [選ばれた候補...], "others": [選ばれなかった候補...]}` として保存する。`ids` は最大3本。

## フェーズ0: 準備（16:15〜）

```bash
# 定期タスクに付けたリポジトリ（Stock-briefing_public）の中で作業する。自分で clone はしない
[ -d note_pipeline ] || { git fetch -q origin claude/sweet-brown-hyew3j && git checkout -q origin/claude/sweet-brown-hyew3j -- note_pipeline .claude docs/note-pipeline docs/superpowers assets requirements-note.txt; }
python3 -m venv .venv && .venv/bin/python -m pip install -q -r requirements-note.txt
.venv/bin/python -c "from datetime import date; from note_pipeline.market import is_tse_closed; print(is_tse_closed(date.today()))"
```

- `True` なら何もせず終了（通知もしない）。
- `mkdir -p $WORK/{inputs,research,deep,drafts,figs,review,out}`、引けJSON3つを `$WORK/inputs/` にコピー。
- 鮮度: `.venv/bin/python -c "import json,sys; from datetime import date; from pathlib import Path; from note_pipeline.market import check_closing_freshness as c; json.dump(c(Path('.'), date.today()), sys.stdout)" > $WORK/inputs/status.json`
- 前回ページ: Artifact ツールで `<DELIVERY_URL>` を `action: read`。保存された HTML を `$WORK/inputs/prev.html` にコピー。
  - `.venv/bin/python -c "import sys; from datetime import date; from note_pipeline.history import parse_history, recent_codes; print('\n'.join(sorted(recent_codes(parse_history(open(sys.argv[1]).read()), date.today()))))" $WORK/inputs/prev.html > $WORK/inputs/recent_codes.txt`
- メール（Gmail）:
  - 新天地メルマガ（`from:mailmag@mag2premium.com`）直近3〜4通（当日の東京版は夜の配信なので、16:15 時点で届いているのは前日の東京版と前夜のNY版まで）。HTML の青字・赤字の強調箇所から**話題の語句・銘柄名だけ**を `$WORK/inputs/mail.md` に箇条書き（本文の文章は書き写さない）。未着なら「未着」と書く。
  - 当日の「【今日の相場振り返り】」メールの要点を `$WORK/inputs/review_mail.md` に。
- 12時の調査メモ: ArtifactData `get` で `<PICKER_URL>` の `notes/<今日>` を読み、`market`, `jp`, `us`, `mail` を `$WORK/research/market.md`, `jp.md`, `us.md`, `$WORK/inputs/mail_midday.md` に書き出す（前場時点のメモ。数字は深掘りで引け値に更新する）。
- ここで1回目の時刻を記録。

## 所要時間の目安（2026-11-08 手動テストの実測）

フェーズ0〜公開まで約26分（調査 2分、ネタ決定 1分、深掘り 2〜5分、執筆 2分、図 1分、レビュー 4分、差戻し対応 5分、最終精査 1分）。75分の枠には余裕があるが、差戻しは1回までを守る。

## フェーズ1: 調査（原則スキップ）

- 12時の調査メモ（`research/*.md`）がそろっていれば**スキップ**する（トークン節約）。
- メモが取れなかったときだけ、従来どおり `note-market-analyst`（モード: 調査）、`note-jp-equity`、`note-us-equity` を並列で起動する。

## フェーズ2: ネタ確定（選択から plan.json を組み立てる）

PM は呼ばない。`picks.json` から機械的に `$WORK/plan.json` を作る（内容は書き換えない）:

- `articles`: 選ばれた順に `id` を `"1"`, `"2"`, `"3"`。
  - `kind: "topic"` の候補 → `{"id", "kind": "theme", "topic": title, "angle", "facts_needed", "assignee": "note-market-analyst"}`
  - `kind: "stock"` の候補 → `{"id", "kind": "stock", "code", "name", "angle", "facts_needed", "assignee": "note-stock-analyst"}`
- `candidates`（選外）: 選ばれなかった候補を `{"title": title, "reason": "今回は選ばれず"}` で並べる。
- `notes`: メルマガ未着などの注記があれば入れる。
- `{"date": "<今日>", "mode": "daily", ...}` の形は従来の `plan.json` と同じ。

深掘りの担当には「**12時の候補出しは前場時点。株価・騰落率は引けの数字で確かめ直すこと**」と必ず伝える。

## フェーズ3: 深掘り（並列、記事ごと）

- テーマ記事 → `note-market-analyst`（モード: 深掘り、記事id）
- 注目銘柄記事 → `note-stock-analyst`（記事idと銘柄）を記事ごとに1体ずつ

## フェーズ4: 執筆（並列、記事ごと）

- `note-securities-analyst`（記事id）を記事の数だけ

## フェーズ5: 図（並列、記事ごと）

- `note-viz`（記事id）を記事の数だけ。図に加えて見出し画像の提案（`figs/a{id}_header.json`）も作る。続けて仮ビルド:

```bash
.venv/bin/python -m note_pipeline.assemble --work $WORK --out $WORK/day.json
.venv/bin/python -m note_pipeline.build --input $WORK/day.json --out $WORK/out --prev-page $WORK/inputs/prev.html 2> $WORK/build_warnings.txt
```

## フェーズ6: レビュー

- `note-pm`（モード: レビュー、n=1）。17:20 を過ぎていたら「差戻し不可（時間切れ）」と伝える。

## フェーズ7: 差戻し（1回まで、並列）

- `verdict.json` が `revise` の記事について、`r1.md` で指名された担当（証券アナリスト／視覚化）を記事ごとに起動。図の差戻しは視覚化の後に `figs` で描き直し済みであること。
- 続けて `note-pm`（モード: 最終精査）。

## フェーズ8: 納品（〜17:28）

```bash
.venv/bin/python -m note_pipeline.assemble --work $WORK --out $WORK/day.json
.venv/bin/python -m note_pipeline.build --input $WORK/day.json --out $WORK/out --prev-page $WORK/inputs/prev.html
```

- 終了コード 2 の警告が残っていても、PM が承認済みなら納品してよい（警告は通知に書かない）。
- Artifact ツールで `$WORK/out/index.html` を `url: <DELIVERY_URL>` に publish。`files` に `img/*.jpg` をすべて（例 `{"img/a1_fig1.jpg": "$WORK/out/img/a1_fig1.jpg"}`）。`action: list, scope: files` で見た前回の画像のうち今日使わないものは `null` で消す。
- PushNotification:
  - 成功: `🐾 今日のnote <選ばれた本数>本ができました：①<タイトル> ②<タイトル> …`（選ばれた本数だけ）
  - 本数不足: `🐾 今日のnote 2本ができました（1本は見送り）：①… ②…`
  - 全体失敗: `🐾 本日は失敗：<理由>`

## 失敗時の動き（設計書 §8）

| 状況 | 動き |
|---|---|
| 東証休場日 | 実行せず終了（通知なし） |
| 引けJSONが古い・取得失敗 | status.json に出る。エージェントが Web 検索で補完し、図に「Web検索値」 |
| メルマガ未着 | mail.md に「未着」。PM がページに注記 |
| 銘柄材料が裏付けできない | PM が次の候補に差し替え（時間がなければ見送り） |
| 3本そろわない | できた本数だけ納品し、通知に本数を明記 |
| 全体失敗 | 「本日は失敗：理由」を通知 |
