# 朝マンガ ネタ候補タスク（平日 13:55 JST）

> 定期タスク（毎回新しいセッション。リポジトリは付いていない）が読む手順書。
> ネタ選びページ「朝マンガ ネタ選び」の固定URLは `https://claude.ai/artifact/LVZ7n7pqEzAdpfNWqUxjXM`（候補の保存先）。
> 納品先 Artifact「朝マンガ納品」は `https://claude.ai/artifact/9m4Jxvrm3aj12NaojgBiUW`（前回の manifest を読む）。
> note のネタ選びは `https://claude.ai/artifact/9VFKNAzE2WiupWAPoj7bir`（今日の note 候補を読むだけ）。
> 設計書: `docs/superpowers/specs/2026-11-27-manga-topic-picker-design.md`（§6.1〜6.2）

---

あなたは朝ブリーフィングの**8コマ漫画のネタ候補を4件出す担当**です。ユーザーが夕方までに1つ選び、夜に別のタスクが漫画に描きます。
ここでは漫画そのもの（台本・絵・解説）は作りません。**14:30 JST までに、4件の候補と下調べメモを保存して通知を送る**ことが最優先です。間に合わなければ、その日は候補なしにします。

## 共通の約束

- 作業はすべてリポジトリ直下の `WORK/`（`.gitignore` 済み）で行う。**候補・下調べメモをリポジトリに書かない・コミットしない・push しない**（公開リポジトリ）。保存先はネタ選びページの保存領域だけ。
- 使うツール: `ArtifactData`（action は get / query / set / delete。引数は `url`・`collection`・`doc_id`・`file_path`・`if_version`）、`Artifact`（action: read）、`PushNotification`、`WebSearch`。
  手元のツール一覧に `ArtifactData` か `PushNotification` が無ければ、先に ToolSearch で `select:ArtifactData,PushNotification` を呼んで読み込む。
- フェーズの開始ごとに `TZ=Asia/Tokyo date '+%H:%M フェーズN' >> WORK/timeline.txt`。
- 投資助言に当たる表現を使わない（`docs/note-pipeline/editorial-rules.md` §1。「買い時」「狙い目」「おすすめ銘柄」など）。
- 数字・豆知識は、出典を確かめられたものだけを使う（Web の取り方は `editorial-rules.md` §2a）。確かめられないものは候補に入れない。
- 日付と時刻はすべて日本時間で扱う（コンテナは UTC。`TZ=Asia/Tokyo` を付ける）。今日の日付は `TZ=Asia/Tokyo date +%F`（以下 `<今日>`）。
- 締切: 材料 14:15 → 候補と下調べメモ 14:20 → 保存・確認 14:30 → 通知 **14:30**。

## フェーズ0: 準備（13:55〜）

```bash
git clone -q --depth 1 https://github.com/ts73103212-lang/Stock-briefing_public repo && cd repo
python3 -m venv .venv && .venv/bin/python -m pip install -q -r requirements-note.txt
TZ=Asia/Tokyo .venv/bin/python -c "from datetime import date; from note_pipeline.market import is_tse_closed; print(is_tse_closed(date.today()))"
mkdir -p WORK
```

- `True`（今日が東証の休場日）なら、何もせず終了する（通知もしない）。以降の作業は `repo/` の中で行う。
- **再実行のガード。** ArtifactData `get`（`url: https://claude.ai/artifact/LVZ7n7pqEzAdpfNWqUxjXM`, `collection: picks`, `doc_id: <今日>`）。
  - すでに選択がある → `days` を上書きしない。PushNotification で `🐾 漫画のネタ候補は作り直しませんでした（すでに選択があります）` を送って終了する。
  - 無い → 続ける。次に `collection: days`, `doc_id: <今日>` を `get` し、すでにあれば返ってきた `version` を控える（フェーズ3の `set` で `if_version` に渡して上書きする）。無ければ新規。
- 前回の manifest: Artifact ツールで `action: read, url: https://claude.ai/artifact/9m4Jxvrm3aj12NaojgBiUW, path: "manga/manifest.json"` を読み、保存先のファイルを `WORK/prev_manifest.json` にコピーする。読めなければ無し（ファイルを作らない）。
- 直近の候補（同じネタを繰り返さないため）: ArtifactData `query`（`url: https://claude.ai/artifact/LVZ7n7pqEzAdpfNWqUxjXM`, `collection: days`, `order_by: date desc`, `limit: 5`）。
  返ってきた各日の候補の `title` を1行ずつ `WORK/recent_titles.txt` に書く。読めなければ空のまま進める。
- note の今日の候補: ArtifactData `get`（`url: https://claude.ai/artifact/9VFKNAzE2WiupWAPoj7bir`, `collection: days`, `doc_id: <今日>`）。読めなければ飛ばす（これは読むだけ。書き込まない）。

## フェーズ1: 材料を集める（〜14:15）

1. リポジトリの JSON: `macro_result.json`（前日の引け）・`macro_result_midday.json`（今日の前場）・`screening_result_midday.json`（前場のスクリーニング）。
2. Web 検索（WebSearch）：その日の経済ニュース・話題の銘柄やテーマを **5〜8件**。
3. note の今日の候補（フェーズ0で読めた分）、`WORK/prev_manifest.json` の `history`、`WORK/recent_titles.txt`。

- **大引けの数字はまだ無い**（この時刻は前場が終わった頃）。候補の文に引けの数字を断定で書かない。今日の動きは「前場で」と書く。
- 直近の候補・前回の漫画と同じネタは避ける。

## フェーズ2: 候補4件と下調べメモを作る（〜14:20）

候補は `id` が `c1`〜`c4`。1件ごとに次を決める。

| フィールド | 内容 |
|---|---|
| `id` | `c1`〜`c4`（この順） |
| `title` | 題（40字まで）。例：「PTSって何？夜の株価の読み方」 |
| `kind` | `theme`（相場の振り返り）／`term`（用語）／`stock`（話題の銘柄・テーマ）／`caution`（注意喚起） |
| `difficulty` | 1〜3 の整数（下の基準表） |
| `summary` | あらすじ1〜2行（120字まで） |
| `hook` | 解説に入れる予定の「へえ」と思う豆知識1行（80字まで。出典を確かめたものだけ） |
| `characters` | 登場人物のキー（`corgi` / `mirai` / `gonda`）の配列。空にしない |

- **種類を散らす。** 4件すべてが同じ kind にならない。目安は theme・term・stock から少なくとも各1件（残る1件は何でもよい）。
- `caution`（ゴンダ先輩が主役の失敗パターン回）は、今週の上限（週2回）に達していても出してよい。`caution_count_note` は**書かない**（`build-day` が `prev_manifest.json` の履歴から付ける）。
- 登場人物の目安：`theme`・`term` は `corgi`＋`mirai`、`stock` は `corgi`＋`mirai`（＋`gonda`）、`caution` は `gonda` が主役で `corgi`・`mirai` も出す。
- ゴンダ先輩の失敗を扱う候補でも、`title` や `summary` に銘柄名を出さない。実在の銘柄を名指しで悪く書かない。
- **難易度の基準**（`difficulty`）:

  | 難易度 | 基準 | 例 |
  |---|---|---|
  | ☆1 | 用語の基本 | PTS とは、ストップ高とは |
  | ☆2 | 指標・値動きの読み方 | 日経平均と TOPIX の差、出来高の見方 |
  | ☆3 | 需給・制度の応用 | 信用買い残、SQ、指数の入れ替え |

  4件の難易度は散らす（全部同じにしない）。

`WORK/candidates.json`:

```json
{"candidates": [
 {"id":"c1","title":"<題>","kind":"term","difficulty":1,"summary":"<あらすじ1〜2行>","hook":"<豆知識1行>","characters":["corgi","mirai"]},
 {"id":"c2", …}, {"id":"c3", …}, {"id":"c4", …}
]}
```

`WORK/memos.json`（候補ごとの下調べメモ。夜の制作タスクが使い回すので、**そのまま台本を起こせる**ように書く。どれも空にしない）:

```json
{"c1":"<メモ>","c2":"<メモ>","c3":"<メモ>","c4":"<メモ>"}
```

メモに入れるもの：

- 使う数字と、その出典 URL
- 台本の骨子（起・承・転・結を各1行）
- 豆知識（`hook`）の出典 URL

確かめられない数字・豆知識は、候補ごと差し替える（ぼかして残さない）。

## フェーズ3: 検証して保存する（〜14:30）

```bash
.venv/bin/python -m manga_pipeline.topics build-day --candidates WORK/candidates.json --memos WORK/memos.json \
  --prev WORK/prev_manifest.json --day-out WORK/day_doc.json --notes-out WORK/notes_doc.json
```

- 終了コード 1 なら、標準エラーに1行1件で問題が出る。`candidates.json`・`memos.json` を直して再実行する（**3回まで**）。3回でも通らなければ、通知して終了する（失敗時の表）。
- 通ったら、ArtifactData `set` で2つ保存する（`url: https://claude.ai/artifact/LVZ7n7pqEzAdpfNWqUxjXM`）。
  1. `collection: days`, `doc_id: <今日>`, `file_path: WORK/day_doc.json`（フェーズ0で `days/<今日>` の `version` を控えていれば `if_version` に渡す）
  2. `collection: notes`, `doc_id: <今日>`, `file_path: WORK/notes_doc.json`
  - `file_path` は絶対パスにする。
- 保存後、`days/<今日>` を ArtifactData `get` して、`candidates` が4件あることを確かめる。無ければ `set` をやり直す。

## フェーズ4: 通知する（14:30 まで）

PushNotification で次を送る（題は `candidates.json` の `title`、リンクは1つ）。

```
🐾 漫画のネタ候補が出ました（締切 20:00）：①<c1の題> ②<c2の題> ③<c3の題> ④<c4の題>
https://claude.ai/artifact/LVZ7n7pqEzAdpfNWqUxjXM
```

## 失敗時の動き

14:30 までに保存できなければ、PushNotification で次を送る。

`🐾 漫画のネタ候補は本日なし：<理由>（今夜は Claude が選んで描きます）`

| 状況 | 動き |
|---|---|
| 東証休場日 | 実行せず終了（通知なし） |
| `picks/<今日>` がすでにある | `days` を上書きせず、`🐾 漫画のネタ候補は作り直しませんでした（すでに選択があります）` を送って終了 |
| `prev_manifest.json` が読めない | 履歴なしとして進める |
| 直近の `days`・note の候補が読めない | 無しとして進める |
| JSON・Web が古い／取れない | 確認できた数字だけ使う。確かめられなければ数字を使わない候補（用語など）にする |
| `build-day` が3回直しても通らない | 「本日なし」通知（理由：候補の検証が通らず） |
| ArtifactData に保存できない | 1回やり直す。だめなら「本日なし」通知（理由：保存できず） |
| 14:30 に間に合わない | 「本日なし」通知（理由：時間切れ） |

「本日なし」の日は何も保存しない（夜の制作タスクが、候補なしとして Claude の選んだネタを描く）。
