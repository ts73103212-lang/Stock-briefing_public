# 朝マンガ 夕方制作タスク（平日 17:45 JST）

> 定期タスク（毎回新しいセッション）が読む手順書。納品先 Artifact「朝マンガ納品」の固定URLは `https://claude.ai/artifact/9m4Jxvrm3aj12NaojgBiUW`。
> 設計書: `docs/superpowers/specs/2026-11-23-morning-manga-design.md`

---

あなたは朝ブリーフィングの**8コマ漫画の制作担当**です。題材決め・台本・場面プロンプト・解説・画像の確認・組版・納品を、あなた自身が行います（画像そのものは GitHub Actions 上の Codex が描く）。
**19:30 JST までに納品と通知を終えること**が最優先です。間に合わなければ、その日は漫画なしにします。

## 共通の約束

- 作業はすべてリポジトリ直下の `WORK/`（`.gitignore` 済み）で行う。**台本・セリフ・解説・完成画像はリポジトリに書かない・コミットしない・push しない**（公開リポジトリ）。
  リポジトリに置いてよいのは、文字なしのコマ画像（ブランチ `manga`。Actions が置く）と英語の場面プロンプトだけ。
- フェーズの開始ごとに `TZ=Asia/Tokyo date '+%H:%M フェーズN' >> WORK/timeline.txt`。
- 投資助言に当たる表現を使わない（`docs/note-pipeline/editorial-rules.md` §1）。
- 数字は引けJSONか、出典を確認できたものだけを使う（Web の取り方は `editorial-rules.md` §2a）。
- 日付と時刻はすべて日本時間で扱う（コンテナは UTC。`TZ=Asia/Tokyo` を付ける）。今日の日付は `TZ=Asia/Tokyo date +%F`。
- 締切: 題材 18:00 → 台本 18:10 → 描画の待ちは **19:15 で打ち切り** → 納品・通知 **19:30**。

## フェーズ0: 準備（17:45〜）

```bash
# 定期タスクに付けたリポジトリ（Stock-briefing_public）の中で作業する。自分で clone はしない
git pull -q origin main
python3 -m venv .venv && .venv/bin/python -m pip install -q -r requirements-note.txt
TZ=Asia/Tokyo .venv/bin/python -c "from datetime import date; from note_pipeline.market import is_tse_closed; print(is_tse_closed(date.today()))"
```

- `True`（今日が東証の休場日）なら、何もせず終了する（通知もしない）。
- `mkdir -p WORK/panels WORK/out`
- **GitHub を使えるようにする（描画の起動に必要）。** 定期タスクのセッションには、最初は GitHub のツールが付いていない。
  1. ToolSearch で `actions_run_trigger` を探す。見つかればそのまま進む。
  2. 見つからなければ、`mcp__claude-code-remote__add_repo` を `owner: "ts73103212-lang"`, `repo: "Stock-briefing_public"`, `access: "push"` で呼び、もう一度 ToolSearch で `actions_run_trigger` を探す。
  3. それでも使えなければ、ここで見送る（理由「GitHub の描画を起動できず」）。題材や台本を作る前に判断して、時間と生成枠を無駄にしない。
- 前回の manifest: Artifact ツールで `action: read, url: https://claude.ai/artifact/9m4Jxvrm3aj12NaojgBiUW, path: "manga/manifest.json"` を読み、保存先のファイルを `WORK/prev_manifest.json` にコピーする。読めなければ前回なしとして進める。
- 載せる日: 漫画は**次の営業日の朝**に載る（金曜・祝日前日は連休明け）。
  `TZ=Asia/Tokyo .venv/bin/python -c "from datetime import date; from manga_pipeline.manifest import next_business_day; print(next_business_day(date.today()))"` → `FOR_DATE`

## フェーズ1: 題材を決める（〜18:00）

材料は次の3つ。

1. 引けの JSON: `macro_result_closing.json`・`screening_result_closing.json`・`screening_stophigh_closing.json`（指数・為替・セクター・ストップ高）
2. note の納品ページ `https://claude.ai/artifact/Pp1EquXnURMFDYTiLemq9q`（今日の記事3本。Artifact ツールで `action: read`）
3. Web 検索（その日の経済ニュース・話題の銘柄やテーマ）

回の種類（`kind`）を1つ選ぶ（設計書 §4.1）。

| kind | 内容 | 主な登場人物 |
|---|---|---|
| `theme` | 相場の振り返り：前営業日の指数・為替・セクターの大きな動きを1つ取り上げ、理由の手がかりを教える | 先生＋ミライ |
| `term` | 用語：株用語（例：SOX指数、連れ安、PTS、信用買い残）を1〜2個 | 先生＋ミライ |
| `stock` | 話題の銘柄・テーマ：当日の note 記事や、その日に話題の銘柄・テーマ | 先生＋ミライ（＋ゴンダ） |
| `caution` | 注意喚起：高値掴み・イナゴ買い・ニュースへの飛びつきなどの失敗パターン | ゴンダ先輩が主役。先生が諭し、ミライが学ぶ |

- **`caution` は週2回まで。** `WORK/prev_manifest.json` の `history`（直近5件の `{for_date, kind}`）のうち、`FOR_DATE` と同じ週（月〜金）の `caution` を数え、2回なら選ばない。
- 同じ kind が3日続かないようにする（毎日同じだと飽きるため）。
- 題材は1つに絞る。決めたら `WORK/topic.md` に、題材・kind・使う数字と出典を書く。

## フェーズ2: 台本・場面プロンプト・解説を作る（〜18:10）

### 登場人物

| キー | 人物 | 口調 | 見た目（設定画 `assets/manga/` のとおり） |
|---|---|---|---|
| `corgi` | コーギー先生。落ち着いて、要点を短く教える | 語尾「〜ワン」 | 黒のシルクハット＋金帯、紺に金ストライプのネクタイ、指し棒。**目は「^ ^」の笑い目** |
| `mirai` | ミライ。新人トレーダー（女性）。素直に質問する。読者の代わり | です・ます | 栗色のボブ、黄色のヘアクリップ、紺ブレザー、白ブラウス、グレーのスカート、社員証、タブレット |
| `gonda` | ゴンダ先輩。株歴1年。モメンタム株やイナゴ買いばかり。ミライには先輩風、先生には頭が上がらない | くだけた口調（「〜っしょ！」） | 小太りで大柄、太い眉、もじゃもじゃの焦げ茶の髪、緑のTシャツ、カーキの短パン、スニーカー、スマホ。憎めないお調子者。体型をからかう描写はしない |

### 台本のルール（設計書 §4.2）

- 8コマ。起（1〜2）・承（3〜5）・転（6〜7）・結（8）を目安にする。
- 吹き出しは1コマに1つ（掛け合いのコマでも最大2つ）。**1つの吹き出しは3行・1行12字まで**（改行は `\n`）。2行以内が理想。
- **ゴンダ先輩の失敗には銘柄名を出さない。**「SNSで話題の生成AI関連の小型株」「決算翌日にストップ高した電線株」のように、状況から分かる程度にぼかす。
- ゴンダ先輩が「買いだ！」と言うのは失敗の描写としてよい。ただし、必ず同じ回の中で先生が考え方を正し、正しい形で終わらせる。
- 実在の銘柄を名指しで悪く描かない。
- 急落・急騰の原因は、裏付けがある場合だけ書く。
- note 記事を題材にする場合も、記事本文は書き写さない。要点を漫画用に言い直す。

`WORK/script.json`（`x` は話者の横位置 0〜1。場面プロンプトの左右と合わせる）:

```json
{"title":"<12字程度の題>","panels":[
 {"n":1,"bubbles":[{"speaker":"mirai","text":"先生！日経平均が\n大きく下がってます","x":0.3}]},
 …8コマ分…]}
```

### 場面プロンプト（設計書 §7.3）

- 英語で、1コマ2〜3文。**人物の位置（左／右）を必ず書く**（吹き出しの尻尾の向きに使う）。
- 共通文（`docs/manga/prompt-common.md`）は Actions が頭に付けるので、場面文だけを書く。
- 絵と内容を一致させる（下落の話ならグラフは下向き：「the chart line goes DOWN」）。
- 文字・数字・ロゴを描かせる指示は書かない。
- `refs` は、そのコマに出る人物のキーだけ（`corgi` / `mirai` / `gonda`）。

`WORK/request.json`:

```json
{"date":"<今日 YYYY-MM-DD>","run_id":"r1",
 "panels":[{"n":1,"prompt":"Mirai stands on the left ..., Corgi Sensei on the right ...","refs":["mirai","corgi"]}, …8コマ分…]}
```

作ったら検証する: `.venv/bin/python -m manga_pipeline.request --request-file WORK/request.json --repo . --out WORK/jobs.json`
（台本の文字数も先に確かめる: `.venv/bin/python -c "import json; from manga_pipeline.compose import _validate; _validate(json.load(open('WORK/script.json')))"`）

### 解説（設計書 §4.3）

- `WORK/explanation.html`。漫画の下に載せる 200〜350 字。`<p>` で段落に分ける。
- 構成：用語の定義 → その日の数字 → 読者が明日から見られるポイント。
- 末尾に `<p>※投資判断はご自身で。</p>`（無いと manifest の作成がエラーになる）。

## フェーズ3: 描画を依頼する

GitHub MCP の `actions_run_trigger` を使う。

- `method: run_workflow`、`owner: ts73103212-lang`、`repo: Stock-briefing_public`、`workflow_id: manga_render.yml`、`ref: main`
- `inputs: {"request": "<WORK/request.json の中身を1行の文字列にしたもの>"}`

- 依頼の**直前に**時刻を控える（待つときに、古い `status.json` と取り違えないため）:
  `TZ=Asia/Tokyo date +%FT%T+09:00 > WORK/t0_<run_id>`

1回の描画は 8コマで約10分。

## フェーズ4: 完了を待つ（19:15 で打ち切り）

Bash を `run_in_background` で実行し、終わりの通知を待つ（その間ほかの作業はしない）。`RUN_ID` は今回の `run_id`（r1 / r2 / r3）。

```bash
D=$(TZ=Asia/Tokyo date +%F); RUN_ID=r1; T0=$(cat WORK/t0_$RUN_ID)
# run_id が一致し、かつ finished_at が依頼した時刻より後のものだけを今回の結果とみなす
until git fetch -q origin manga 2>/dev/null && git show FETCH_HEAD:manga/$D/status.json 2>/dev/null \
  | .venv/bin/python -c "import json,sys; s=json.load(sys.stdin); sys.exit(0 if s.get('run_id')==sys.argv[1] and s.get('finished_at','')>sys.argv[2] else 1)" "$RUN_ID" "$T0"; do
  [ "$(TZ=Asia/Tokyo date +%H%M)" -ge 1915 ] && { echo TIMEOUT; exit 1; }
  sleep 60
done
rm -rf WORK/panels && mkdir -p WORK/panels && git archive FETCH_HEAD manga/$D | tar -x -C WORK/panels --strip-components=2
cat WORK/panels/status.json
```

- `TIMEOUT` → 見送り（理由「描画が 19:15 までに終わらなかった」）。
- `status.json` の `auth` が `expired` または `persist_failed` → 見送り（理由「Codex の再ログインが必要（docs/manga/README.md）」）。
- `panels` で `failed` のコマは、フェーズ5の描き直しに回す。
- `WORK/panels/p{n}.png` は、同じ日の前の run の分も残っている（描き直さなかったコマはそのまま使う）。

## フェーズ5: 確認する（設計書 §7.4）

8枚を Read で見て、次のどれかに当たるコマを描き直し対象にする。

1. 文字・数字・吹き出し・ロゴが描かれている
2. 人物の顔・服・色が設定画と明らかに違う（コーギー先生の目が笑い目でない、ミライのヘアクリップが無い、など）
3. 場面の内容と絵が合っていない（例：下落の話なのにグラフが上向き）
4. 上の3割に吹き出しを置く余白が無い、または人物が小さすぎる
5. 手指・体の破綻が目立つ

- 描き直しは**最大2回**（`run_id` r2、r3）。**描き直すコマは2回合わせて8コマまで**（1日の生成は初回8枚と合わせて最大16枚。Codex の利用枠を note のサムネイル用に残すため。ユーザー判断 2026-11-25）。
  8コマを超えて直したいときは、重い問題（1〜3）のコマを優先する。描き直すコマだけを `panels` に入れ、場面プロンプトに直す点を英語で足す（例：「the chart line goes DOWN」「no text anywhere」）。依頼したらフェーズ4に戻る。
- 2回目（r3）でもダメなコマ：軽い問題（5）は採用する。4 は、吹き出しの `x` を動かして顔に重ならずに置けるなら採用する。
  重い問題（1〜3）が残る場合は、その日は見送る（理由「コマの絵が規定を満たさなかった」）。
- 19:15 を過ぎたら描き直しはしない。重い問題が残っていれば見送る。

## フェーズ6: 組版する

```bash
.venv/bin/python -m manga_pipeline.compose --script WORK/script.json --panels WORK/panels --out WORK/rows
```

- `WORK/rows/row1.jpg`〜`row4.jpg` を Read で見る。吹き出しが顔に重なっていれば、そのコマの `x` を直して組み直す。
- セリフが読めること、尻尾が話者の方を向いていることを確かめる。

## フェーズ7: 納品する（〜19:25）

```bash
.venv/bin/python -m manga_pipeline.manifest --title "<script.json の title>" --kind <kind> \
  --explanation WORK/explanation.html --rows WORK/rows --out WORK/out --prev WORK/prev_manifest.json
```

- 出力の `for_date` が `FOR_DATE` と同じか確かめる。
- Artifact ツールで `WORK/out/index.html` を `url: https://claude.ai/artifact/9m4Jxvrm3aj12NaojgBiUW` に publish する。`files` は次の5つ:
  `{"manga/row1.jpg": "WORK/out/manga/row1.jpg", …row4…, "manga/manifest.json": "WORK/out/manga/manifest.json"}`
  （パスは絶対パスにする）

## フェーズ8: 通知する（〜19:30）

PushNotification で次のどれかを送る。

- 成功：`🐾 明日の漫画ができました：<title>`（連休をまたぐときは「明日」を「<FOR_DATE の M/D>の」にする）
- 見送り：`🐾 漫画は本日見送り：<理由>`
- ログイン切れ（`auth` が `expired` / `persist_failed`）：`🐾 漫画は本日見送り：Codex の再ログインが必要（docs/manga/README.md）`

見送りの日は納品先を更新しない（前回の manifest の `for_date` は過去の日なので、朝のブリーフィングは漫画欄を省く）。

## 失敗時の動き

| 状況 | 動き |
|---|---|
| 東証休場日 | 実行せず終了（通知なし） |
| 引けJSONが古い | Web 検索で補い、確認できた数字だけ使う。確かめられなければ数字を使わない題材（用語など）にする |
| 描画が 19:15 までに終わらない | 見送り通知 |
| Codex のログイン切れ・書き戻し失敗 | 見送り通知（再ログインの案内つき） |
| 2回描き直しても重い問題が残る | 見送り通知 |
| 組版・納品でエラー | 直せれば直す。19:30 に間に合わなければ見送り通知 |
