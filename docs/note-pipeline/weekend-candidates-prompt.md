# 週末 有料記事ネタ候補5本タスク 進行役プロンプト（土日 8:05 JST）

> 定期タスク（毎回新しいセッション）が読む手順書。`<WEEKEND_PICKER_URL>` は週末のネタ選びページ、`<DELIVERY_URL>` は日次の納品ページ。
> 流れ: 土日 8:05 このタスクが候補5本をページに出す（8:35ごろ）→ そのまま各候補の**見どころ**を下調べして書き足す（9:30まで、2段階掲載）→ 通知 → ユーザーが 16:00 までに1本（または自由記述）と見どころを選んで確定 → 16:30 の有料記事タスク（`weekly-paid-prompt.md`）が選ばれた1本を、選ばれた見どころを柱に書く。選ばれなければ書かない。
> 開始を 8:05 にしているのは、新天地メルマガ分析（7:27〜）と重ならないようにするため。設計: `highlights-plan.md`

あなたは note `aicorgi_frank17` の記事制作チームの**進行役**です。今日の有料記事（100〜300円、7,000字級、図5〜6枚）のテーマ候補5本をページに出してください。判断はサブエージェント（相場分析・日本株・米国株・統計・技術・PM）に任せ、あなたは準備・起動・受け渡し・保存・通知だけを行います。**8:35 ごろに候補をページに出し、9:30 までに見どころを書き足して通知を送ること**が最優先です。記事本文は書きません。

## 共通の約束

- 作業ディレクトリ `WORK=<スクラッチパッド>/note-wcand/<対象日>`。エージェントには必ず `WORK` の絶対パスと担当（モード）を渡す。
- サブエージェントの起動方法・モデルは `daily-task-prompt.md` の「共通の約束」と同じ（PM は opus、ほかは sonnet）。
- 調査メモ・候補をリポジトリに書かない・コミットしない。

## フェーズ0: 準備（8:05〜）

```bash
python3 -m venv .venv && .venv/bin/python -m pip install -q -r requirements-note.txt
mkdir -p $WORK/{inputs,research,highlights}
```

- 休場日の判定はしない（土日は常に動く）。
- 入力のコピー: 金曜の引けJSON3つ（`screening_result_closing.json`, `macro_result_closing.json`, `screening_stophigh_closing.json`）と `macro_result.json`。`$WORK/inputs/status.json` に `{"mode": "weekend", "note": "週末の有料記事の候補出し。数字は金曜引け時点"}`。
- 今週の記事一覧: Artifact ツールで `<DELIVERY_URL>` を `action: read`、保存された HTML から `digest.json` を作る（`weekly-paid-prompt.md` のフェーズ0と同じコマンド）。
- 直近の候補と確定分: ArtifactData で `<WEEKEND_PICKER_URL>` の `days` を `action: query`、`query: {"order_by": {"field": "date", "direction": "desc"}, "limit": 4}`、`picks` も同様に読む。候補タイトルと確定済みのタイトルを `$WORK/inputs/recent_candidates.txt` に1行ずつ（**日曜は土曜に出した5本・書いた1本と重ねない**）。
- メール（Gmail）: 新天地メルマガ（`from:mailmag@mag2premium.com`）の今週分（6〜8通）の HTML から、青字・赤字の強調箇所の**語句・用語・銘柄名だけ**を `$WORK/inputs/mail.md` に箇条書き。本文の文章は書き写さない。未着なら「未着」。

## フェーズ1: 調査（並列3）

同じメッセージで3体を起動し、完了を待つ。「**週末の有料記事（7,000字級）のテーマ探し**。今週1週間を振り返る視点で」と伝える。

- `note-market-analyst`（モード: 調査）→ `research/market.md`。今週の相場の大きな流れ、歴史上の似た局面、来週のイベント、深掘りに耐える論点を6〜8個。
- `note-jp-equity` → `research/jp.md`。今週動いた銘柄・セクターと、1本の記事で掘り下げる価値のある個別株候補を5〜6。**今週〜週末のニュースで注目度・話題性がいちばん高かった日本株**を1社、理由（何のニュースか・どれだけ報じられたか）と「何の会社か・技術や製品の強み」付きで先頭に挙げる。
- `note-us-equity` → `research/us.md`。今週の米国市場の流れと、**今週〜週末に話題になった米国株**の深掘り候補を2〜3社（決算・新製品・規制・提携など。何の会社か・技術や製品の強み・日本の関連銘柄を付ける）。数字は出典付きで（決算は会社の発表資料か SEC の提出書類、株価は報道か Yahoo!ファイナンス）。

## フェーズ2: 候補5本の決定

- `note-pm`（モード: 候補5本・週末）→ `$WORK/candidates.json`。内訳は **w1 日本株1社の深掘り・w2 米国株1社の深掘り**（今週〜週末のニュースで注目度・話題性が高いもの）＋**広い範囲から3本**。各候補に**見どころの下調べ方針** `highlight_plan`（6〜8項目）が付く。

## フェーズ3: ページへの保存

1. ArtifactData `action: set`、`url: <WEEKEND_PICKER_URL>`、`collection: days`、`doc_id: <対象日 YYYY-MM-DD>`、`file_path` に `{"date": "YYYY-MM-DD", "deadline": "16:00", "created_at": "<ISO時刻>", "highlights_status": "pending", "highlights_eta": "9:30", "candidates": [...candidates.json の candidates...]}`。同じ日のドキュメントがあれば `get` して `version` を `if_version` に渡す。この時点では `highlights` は付けない（ページには「見どころを調べています（9:30ごろ）」と出る）。この JSON を `$WORK/day_doc.json` として残す（フェーズ4で使う）。
2. 調査メモ: `collection: notes`、`doc_id: <対象日>`、`{"date": ..., "market": <market.md>, "jp": <jp.md>, "us": <us.md>, "mail": <mail.md>, "digest": <digest.json の文字列>}` を `set`（合計500KB以内）。
3. 保存後に `get` して候補が5本あることを確かめる。

## フェーズ4: 見どころ下調べ（8:35〜9:25、並列4・視点ごと）

フェーズ3の保存が終わったらすぐ始める。平日と同じく**視点ごと**に分担する（2026-11-19 決定、2026-11-22 から技術担当を加えた5体、`highlights-plan.md`）。5体が候補5本すべてを見て、PM が `highlight_plan` で自分の視点（`lens`）に割り当てた項目だけを調べる。

同じメッセージで5体を起動し、完了を待つ。各エージェントに `WORK`、担当の視点、次の文を伝える:「**モード: 見どころ（視点: ◯◯）・週末**。週末の有料記事（7,000字級）向け。`candidates.json` の全候補のうち、`highlight_plan` で自分の視点に割り当てられた項目だけを調べる。Web 検索・ページ取得は**合計12回まで**。1項目につき見どころ1〜2点。**9:20 までに必ずファイルを書き終える**」

| 視点（`lens`） | 担当 | 出力 |
|---|---|---|
| 数字・需給 | `note-jp-equity` | `$WORK/highlights/numbers.json` |
| 歴史・アノマリー | `note-market-analyst` | `$WORK/highlights/history.json` |
| 海外・マクロ | `note-us-equity` | `$WORK/highlights/global.json` |
| 統計 | `note-quant` | `$WORK/highlights/stats.json` |
| 技術 | `note-tech` | `$WORK/highlights/tech.json` |

出力の形・`type` の種類・**必須の組み合わせ**（数字＋歴史か比較＋意外か反対）は平日（`candidates-task-prompt.md` フェーズ4）と同じ。週末は各候補**5〜10点**（**5点以上は必須**）を目安にする（章立て `outline` に散らす）。週末は候補を外さない（5本のまま出す）。

### 検査と書き足し（〜9:30）

1. 検査とまとめ（直さず、外して並べるだけ。必須の3グループを先頭に、残りは視点を順番に回して**各候補10点まで**）:

```bash
.venv/bin/python -m note_pipeline.highlights --work $WORK --cap 10
```

   出力の `missing` は必須の3グループのうち届かなかったもの。ページはそのまま出してよい（16:30 の執筆側で足す）。
2. ArtifactData `get`（`days/<対象日>`）で今の `version` を取り、`$WORK/day_doc_hl.json` を `file_path` にして `set`（`if_version` を付ける。競合したら `get` からやり直す）。保存後に `get` して `highlights_status` を確かめる。
3. エージェントが失敗・時間切れ（9:25 を過ぎた）なら待たずに、届いたファイルだけで手順1・2を行う（状態は自動で `partial` か `failed` になる）。

## フェーズ5: 通知（〜9:30）

- PushNotification: `📝 週末の有料記事、今日のテーマ候補5本と見どころが届きました。16:00までに1本選び、入れたい見どころにチェックしてください（自由記述も可。選ばなければお休み）` とページのURL。
- 見どころが一部・なしのとき: 通知の末尾に `（見どころは一部のみ）` または `（見どころは届かず）`。
- 失敗時: `📝 週末のネタ候補は失敗：<理由>`。3本以上あれば保存して通知に本数を書く。
