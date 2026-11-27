# 朝マンガ 夕方制作タスク（平日 20:05 JST）

> 定期タスク（毎回新しいセッション）が読む手順書。納品先 Artifact「朝マンガ納品」の固定URLは `https://claude.ai/artifact/9m4Jxvrm3aj12NaojgBiUW`。
> 設計書: `docs/superpowers/specs/2026-11-23-morning-manga-design.md`、`docs/superpowers/specs/2026-11-27-manga-topic-picker-design.md`（ネタ選び）
> ネタ選びページ「朝マンガ ネタ選び」の固定URLは `https://claude.ai/artifact/LVZ7n7pqEzAdpfNWqUxjXM`（ユーザーの選択が入る。読むだけで、書き込まない）。

---

あなたは朝ブリーフィングの**8コマ漫画の制作担当**です。題材決め・台本・場面プロンプト・解説・画像の確認・組版・納品を、あなた自身が行います（画像そのものは GitHub Actions 上の Codex が描く）。
**22:00 JST までに納品と通知を終えること**が最優先です。間に合わなければ、その日は漫画なしにします。

## 共通の約束

- 作業はすべてリポジトリ直下の `WORK/`（`.gitignore` 済み）で行う。**台本・セリフ・解説・完成画像はリポジトリに書かない・コミットしない・push しない**（公開リポジトリ）。
  リポジトリに置いてよいのは、文字なしのコマ画像（ブランチ `manga`。Actions が置く）と英語の場面プロンプトだけ。
- フェーズの開始ごとに `TZ=Asia/Tokyo date '+%H:%M フェーズN' >> WORK/timeline.txt`。
- 投資助言に当たる表現を使わない（`docs/note-pipeline/editorial-rules.md` §1）。
- 数字は引けJSONか、出典を確認できたものだけを使う（Web の取り方は `editorial-rules.md` §2a）。
- 日付と時刻はすべて日本時間で扱う（コンテナは UTC。`TZ=Asia/Tokyo` を付ける）。今日の日付は `TZ=Asia/Tokyo date +%F`。
- 締切: 題材 20:15 → 台本 20:30 → 描画の待ちは **21:35 で打ち切り** → 納品 21:50 → 通知 **22:00**。
- ユーザーが選んだネタ（`WORK/choice.json` の `mode` が `user` / `free`）は、それで描くのが原則。**理由を通知に書かずに別のネタにしない。**

## フェーズ0: 準備（20:05〜）

```bash
# 定期タスクに付けたリポジトリ（Stock-briefing_public）の中で作業する。自分で clone はしない
git pull -q origin main
python3 -m venv .venv && .venv/bin/python -m pip install -q -r requirements-note.txt
TZ=Asia/Tokyo .venv/bin/python -c "from datetime import date; from note_pipeline.market import is_tse_closed; print(is_tse_closed(date.today()))"
```

- `True`（今日が東証の休場日）なら、何もせず終了する（通知もしない）。
- `mkdir -p WORK/panels WORK/out`
- **GitHub を使えるようにする（描画の起動に必要）。** 定期タスクにはリポジトリ `Stock-briefing_public` を付けてある（claude.ai の定期タスク設定。外れていると GitHub のツールが無い）。
  1. まず ToolSearch で `select:mcp__github__actions_run_trigger` を試す。定期タスクにリポジトリが付いていれば、これで見つかる（2026-11-25 の試運転はこれで通った）。
  2. 見つからず、手元のツール一覧に `mcp__claude-code-remote__add_repo` があれば、ToolSearch で探さずに**そのまま呼ぶ**
     （`owner: "ts73103212-lang"`, `repo: "Stock-briefing_public"`, `access: "push"`）。返答を `WORK/add_repo.txt` に控え、`sleep 20` の後にもう一度 1 を試す。
     add_repo がツール一覧に無ければ、この手順は飛ばす。
  3. それでも使えなければ、ここで見送る（理由「GitHub の描画を起動できず」）。
     題材や台本を作る前に判断して、時間と生成枠を無駄にしない。
- 前回の manifest: Artifact ツールで `action: read, url: https://claude.ai/artifact/9m4Jxvrm3aj12NaojgBiUW, path: "manga/manifest.json"` を読み、保存先のファイルを `WORK/prev_manifest.json` にコピーする。読めなければ前回なしとして進める。
- 載せる日: 漫画は**次の営業日の朝**に載る（金曜・祝日前日は連休明け）。
  `TZ=Asia/Tokyo .venv/bin/python -c "from datetime import date; from manga_pipeline.manifest import next_business_day; print(next_business_day(date.today()))"` → `FOR_DATE`

### 選択を確かめる（フェーズ0の最後）

ユーザーは 20:00 までに、ネタ選びページで候補（`c1`〜`c4`）を1つ選ぶ（任意で要望つき）か、自由記述だけで頼む。それをここで読む。

1. 手元のツール一覧に `ArtifactData` が無ければ、ToolSearch で `select:ArtifactData` を呼んで読み込む。
2. `rm -rf WORK/raw WORK/day.json WORK/notes.json WORK/pick.json`
3. ArtifactData `get` を3回呼ぶ。どれも `url: https://claude.ai/artifact/LVZ7n7pqEzAdpfNWqUxjXM`、`doc_id: <今日 YYYY-MM-DD>`、`out_dir: <リポジトリの絶対パス>/WORK/raw`。
   - `collection: days`（その日の候補4件）
   - `collection: notes`（候補ごとの下調べメモ。`{"date", "memos": {"c1": …}}`）
   - `collection: picks`（ユーザーの選択。`{"date", "id", "request", "free", "picked_at"}`）

   見つからない（not found のエラー、または結果が空）の文書は「無い」として扱い、何もしない（ファイルを作らない）。
4. 保存されたファイルから、**文書の中身（`data` の部分）だけ**を `WORK/day.json`・`WORK/notes.json`・`WORK/pick.json` に書き出す
   （`id`・`version` などの入れ物は入れない。無い文書のファイルは作らない）:

```bash
D=$(TZ=Asia/Tokyo date +%F)
.venv/bin/python - "$D" <<'EOF'
import json, sys
from pathlib import Path
d = sys.argv[1]
for col, name in (("days", "day"), ("notes", "notes"), ("picks", "pick")):
    src = Path("WORK/raw") / col / f"{d}.json"
    if not src.exists():
        print(col, "なし"); continue
    doc = json.loads(src.read_text(encoding="utf-8"))
    if isinstance(doc, dict) and isinstance(doc.get("data"), dict):
        doc = doc["data"]   # 入れ物（id・version つき）なら中身だけにする
    Path("WORK", f"{name}.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    print(col, "->", f"WORK/{name}.json")
EOF
```

   `out_dir` に保存されず、結果に中身が直接返ってきた場合は、その文書の `data` の部分（`date` などのキーを持つオブジェクト）を自分で同じファイル名に書く。
5. 読み分ける:

```bash
.venv/bin/python -m manga_pipeline.topics resolve --day WORK/day.json --pick WORK/pick.json --notes WORK/notes.json --prev WORK/prev_manifest.json --out WORK/choice.json
```

   - 出力は `{"mode": "user" | "free" | "auto", "for_date", "id", "notices"}`。`for_date` が `FOR_DATE` と同じか確かめる。詳しい中身は `WORK/choice.json`
     （`mode`・`candidate`・`memo`・`request`・`free`・`caution_cap_applies`・`caution_count`・`notices`・`warnings`）。
   - `WORK/choice.json` の `notices`（例：「選択した候補 c3 が見つからないため、おまかせで描きます」）は、**通知の2行目以降にそのまま入れる**
     （成功の通知では描き直しの記録の次、3行目から。フェーズ8）。黙って捨てない。
   - **ArtifactData が読み込めない・`get` がエラー（not found 以外）・上の書き出しや `resolve` が失敗した（エラーで止まった）** ときは、選択なし（`auto`）として進め、
     通知の `notices` に `選択を読めなかったため、おまかせで描きます` を足す（ユーザーの選択を黙って無視しない）。`WORK/choice.json` は次で作る
     （無いファイルを渡すと「選択なし」になる。これも失敗したら `--prev` も `WORK/none.json` にする）:
     `.venv/bin/python -m manga_pipeline.topics resolve --day WORK/none.json --pick WORK/none.json --notes WORK/none.json --prev WORK/prev_manifest.json --out WORK/choice.json`

## フェーズ1: 題材を決める（〜20:15）

`WORK/choice.json` の `mode` で分ける。どの場合も最後に `WORK/topic.md` を書く（このフェーズの末尾）。

### `mode` が `user`（候補を選んだ日）

- 題材は `candidate`（`title`・`kind`・`difficulty`・`summary`・`hook`・`characters`）、下調べは `memo`。**下の「題材の選び方」は飛ばす。** kind と難易度は候補のまま。
- `memo` の数字は 14:00 ごろ（前場）の材料で書かれている。**引けの JSON（下の材料 1）・報道の大引け値で確かめ直し**、引けの値に直して使う。確かめられない数字は使わない。
  `memo` が `null`（下調べメモが無い）なら、下の材料で自分で調べる。
- `request`（「この候補で入れてほしいこと」）があれば、台本と解説に取り入れる。
  ただし `warnings` がある、または投資助言・確かめられない数字に当たる部分は取り入れず、通知に一言書く（例：`要望のうち<部分>は<理由>のため入れていません`）。
- `caution` の候補でも、週2回の上限は見ない（ユーザーの選択を優先。`caution_cap_applies` は False）。
- **前提が引けで崩れたとき**（例：「日経と TOPIX の差が開いた」を選んだが、引けでは縮んだ）：同じ題材のまま、引けの数字に合わせて切り口を変える
  （「前場は開いたが、引けでは縮んだ。なぜか」）。これは「あなたの選択」として扱い、`WORK/topic.md` に `adjusted: true` と書く（通知に「（引けに合わせて調整）」と出る）。
  下調べメモの台本の骨子は、数字と切り口を直してよい。
  題材の中身そのもの（用語・仕組み・出来事）が成り立たないときだけ、差し替えにする（下の「差し替え」）。

### `mode` が `free`（自由記述だけで頼まれた日）

- `free` の内容から題材を立て、kind と難易度（1〜3）を自分で決める。数字は下の材料で確かめたものだけ使う。
- 失敗談を頼まれた場合は `caution` の回として描き、週2回の上限は見ない（`caution_cap_applies` は False）。
- `warnings` がある、または投資助言・確かめられない数字に当たる部分は取り入れず、通知に一言書く。頼まれた内容が投資助言にしかならないなら差し替える（下の「差し替え」）。

### `mode` が `auto`（選択なし・選択を使えなかった日）

これまでどおり、下の「題材の選び方」で自分で選ぶ。`WORK/day.json` がある日は、その候補4件から選んでもよい（その場合は `WORK/notes.json` の下調べメモも使ってよい。数字は引けで確かめ直す）。別の題材でもよい。

### 差し替え（選ばれたネタが描けないとき）

- `user` / `free` で、選ばれたネタが描けない（数字の裏付けが取れない、投資助言にしかならない、題材の中身が成り立たない、など）ときは、
  自分で選んだネタ（`auto` と同じ選び方。注意喚起の上限も守る）に切り替えて描く。`WORK/topic.md` に `picked: replaced` と差し替えの理由を書き、通知に `選択ネタは<理由>のため差し替え` と入れる。
- 差し替えてよいのは**フェーズ1〜2の間（台本の締切 20:30 まで）だけ**。描画を依頼した後は差し替えない。
  描き直しの上限を使っても重い問題が残った場合は、元のとおりその日は見送る（差し替えて描き直す時間はない）。

### 題材の選び方（`auto` と差し替えのとき）

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

- **`caution` は週2回まで。** `WORK/choice.json` の `caution_count`（`FOR_DATE` と同じ週の `caution` の回数）が 2 以上なら `caution` を選ばない。
- 同じ kind が3日続かないようにする（毎日同じだと飽きるため）。
- 題材は1つに絞る。

### `WORK/topic.md` を書く（どの場合も）

題材・kind・使う数字と出典に加えて、次を書く（フェーズ7の manifest と、フェーズ8の通知に使う）。

- `difficulty: 1|2|3`（難易度。`user` は候補の値、`free`・`auto`・差し替えは自分で決める。目安はフェーズ2の「難易度の目安」）
- `picked: user|free|auto|replaced`（`user`：`mode` が `user` で差し替えなかった日。引けに合わせて調整した日も `user`。`free`：`mode` が `free` で差し替えなかった日。`auto`：`mode` が `auto` の日。`replaced`：選ばれたネタを差し替えた日）
- `adjusted: true|false`（`user` で、引けに合わせて切り口を変えたとき true）
- 差し替えた日は、その理由（通知に使う）。取り入れなかった要望があれば、その一言。

## フェーズ2: 台本・場面プロンプト・解説を作る（〜20:30）

### 難易度の目安（`WORK/topic.md` の `difficulty`）

台本と解説の深さを、難易度に合わせる。解説の字数（350〜550 字）は難易度にかかわらず変えない。

- ☆1：用語をかみくだいて説明する。数字は1〜2個まで。
- ☆2：その日の数字と、その読み方。
- ☆3：数字や仕組み（需給・制度）まで踏み込む。

`request`（`user` の要望）は台本と解説に取り入れる（フェーズ1の条件で外した部分を除く）。

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

- `WORK/explanation.html`。漫画の下に載せる **350〜550 字**（「※投資判断はご自身で。」を除く）。`<p>` で段落に分ける（4〜5段落）。
- 構成：用語の定義 → その日の数字 → **株の豆知識・読者が「へえ」と思う事実を1つ** → 読者が明日から見られるポイント。
  - 豆知識の例：指数や制度の成り立ち、過去の似た局面で起きたこと、数字の意外な大きさ（「日経平均の値動きの◯割を上位◯銘柄が占める」など）、プロが実際に見ている指標。
  - 豆知識も数字と同じく、**出典を確かめられたものだけ**を書く。確かめられなければ、数字を使わない一般的な知識（仕組みの説明）にする。噂・推測・「〜と言われる」は書かない。
  - 投資助言に当たる表現は使わない（「買い時」「狙い目」など）。
- 書いたら字数を数える：`.venv/bin/python -c "import re,sys; t=re.sub('<[^>]+>','',open('WORK/explanation.html').read()).replace('※投資判断はご自身で。',''); print(len(t.strip()))"`
- 末尾に `<p>※投資判断はご自身で。</p>`（無いと manifest の作成がエラーになる）。

## フェーズ3: 描画を依頼する

GitHub MCP の `actions_run_trigger` を使う。

- `method: run_workflow`、`owner: ts73103212-lang`、`repo: Stock-briefing_public`、`workflow_id: manga_render.yml`、`ref: main`
- `inputs: {"request": "<WORK/request.json の中身を1行の文字列にしたもの>"}`

- 依頼の**直前に**時刻を控える（待つときに、古い `status.json` と取り違えないため）:
  `TZ=Asia/Tokyo date +%FT%T+09:00 > WORK/t0_<run_id>`

1回の描画は 8コマで約10分。

## フェーズ4: 完了を待つ（21:35 で打ち切り）

Bash を `run_in_background` で実行し、終わりの通知を待つ（その間ほかの作業はしない）。`RUN_ID` は今回の `run_id`（r1 / r2 / r3）。

```bash
D=$(TZ=Asia/Tokyo date +%F); RUN_ID=r1; T0=$(cat WORK/t0_$RUN_ID)
# run_id が一致し、かつ finished_at が依頼した時刻より後のものだけを今回の結果とみなす
until git fetch -q origin manga 2>/dev/null && git show FETCH_HEAD:manga/$D/status.json 2>/dev/null \
  | .venv/bin/python -c "import json,sys; s=json.load(sys.stdin); sys.exit(0 if s.get('run_id')==sys.argv[1] and s.get('finished_at','')>sys.argv[2] else 1)" "$RUN_ID" "$T0"; do
  [ "$(TZ=Asia/Tokyo date +%H%M)" -ge 2135 ] && { echo TIMEOUT; exit 1; }
  sleep 60
done
rm -rf WORK/panels && mkdir -p WORK/panels && git archive FETCH_HEAD manga/$D | tar -x -C WORK/panels --strip-components=2
cat WORK/panels/status.json
```

- `TIMEOUT` → 見送り（理由「描画が 21:35 までに終わらなかった」）。
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

- 描き直しは**最大2回**（`run_id` r2、r3）。**描き直すコマは2回合わせて10コマまで**（1日の生成は初回8枚と合わせて最大18枚。
  漫画の質を上げるため、ユーザーが 2026-11-25 に10コマへ変更。何回か動かして描き直しの傾向を見たうえで、合計16枚を上限にする予定）。
  10コマを超えて直したいときは、重い問題（1〜3）のコマを優先する。描き直すコマだけを `panels` に入れ、場面プロンプトに直す点を英語で足す（例：「the chart line goes DOWN」「no text anywhere」）。依頼したらフェーズ4に戻る。
- 2回目（r3）でもダメなコマ：軽い問題（5）は採用する。4 は、吹き出しの `x` を動かして顔に重ならずに置けるなら採用する。
  重い問題（1〜3）が残る場合は、その日は見送る（理由「コマの絵が規定を満たさなかった」）。ユーザーが選んだネタでも同じで、差し替えはしない。
- 21:35 を過ぎたら描き直しはしない。重い問題が残っていれば見送る。

## フェーズ6: 組版する

```bash
.venv/bin/python -m manga_pipeline.compose --script WORK/script.json --panels WORK/panels --out WORK/rows
```

- `WORK/rows/row1.jpg`〜`row4.jpg` を Read で見る。吹き出しが顔に重なっていれば、そのコマの `x` を直して組み直す。
- セリフが読めること、尻尾が話者の方を向いていることを確かめる。

## フェーズ7: 納品する（〜21:50）

```bash
.venv/bin/python -m manga_pipeline.manifest --title "<script.json の title>" --kind <kind> \
  --picked <user|free|auto|replaced> --difficulty <1|2|3> \
  --explanation WORK/explanation.html --rows WORK/rows --out WORK/out --prev WORK/prev_manifest.json
```

- `--picked` と `--difficulty` は `WORK/topic.md` の `picked`・`difficulty` のとおり（`user` は `mode` が `user` で差し替えなかった日。引けに合わせて調整した日も `user`）。
- 出力の `for_date` が `FOR_DATE` と同じか確かめる。
- Artifact ツールで `WORK/out/index.html` を `url: https://claude.ai/artifact/9m4Jxvrm3aj12NaojgBiUW` に publish する。`files` は次の5つ:
  `{"manga/row1.jpg": "WORK/out/manga/row1.jpg", …row4…, "manga/manifest.json": "WORK/out/manga/manifest.json"}`
  （パスは絶対パスにする）

## フェーズ8: 通知する（〜22:00）

PushNotification で次のどれかを送る。

- 成功：`🐾 明日の漫画ができました：<title>（<選択>）`（連休をまたぐときは「明日」を「<FOR_DATE の M/D>の」にする）。
  `（<選択>）` は `WORK/topic.md` の `picked` で決める:
  - `user`：`（あなたの選択）`。`adjusted: true` の日は `（あなたの選択（引けに合わせて調整））`
  - `free`：`（あなたの選択）`
  - `auto`：`（おまかせ）`
  - `replaced`：`（差し替え）`

  2行目に描き直しの記録を1行入れる（上限を決める材料にするため）。例：`描き直し：r2 4コマ（目×3・グラフ向き×1）、r3 なし／計12枚`
  3行目以降に、`WORK/choice.json` の `notices`（と、フェーズ0で足した `選択を読めなかったため、おまかせで描きます`）を1件1行でそのまま入れ、
  差し替えた日は `選択ネタは<理由>のため差し替え`、取り入れなかった要望があればその一言を入れる。
  例：
  ```
  🐾 明日の漫画ができました：PTSって何？（差し替え）
  描き直し：r2 2コマ（目×2）、r3 なし／計10枚
  選択ネタは数字の裏付けが取れなかったため差し替え
  ```
- 見送り：`🐾 漫画は本日見送り：<理由>`（2行目以降に `notices` があれば、成功のときと同じように入れる）
- ログイン切れ（`auth` が `expired` / `persist_failed`）：`🐾 漫画は本日見送り：Codex の再ログインが必要（docs/manga/README.md）`

見送りの日は納品先を更新しない（前回の manifest の `for_date` は過去の日なので、朝のブリーフィングは漫画欄を省く）。

## 失敗時の動き

| 状況 | 動き |
|---|---|
| 東証休場日 | 実行せず終了（通知なし） |
| 引けJSONが古い | Web 検索で補い、確認できた数字だけ使う。確かめられなければ数字を使わない題材（用語など）にする |
| 描画が 21:35 までに終わらない | 見送り通知 |
| Codex のログイン切れ・書き戻し失敗 | 見送り通知（再ログインの案内つき） |
| 2回描き直しても重い問題が残る | 見送り通知 |
| 選択を読めない（ArtifactData が使えない・`resolve` が失敗） | おまかせ（`auto`）で描き、通知に `選択を読めなかったため、おまかせで描きます` |
| 選ばれたネタが描けない（裏付けが取れない・投資助言にしかならない） | フェーズ1〜2の間なら差し替えて描き、通知に `選択ネタは<理由>のため差し替え` |
| 組版・納品でエラー | 直せれば直す。22:00 に間に合わなければ見送り通知 |
