# ネタ候補10本タスク 進行役プロンプト（平日 11:47 JST）

> 定期タスク（毎回新しいセッション）が読む手順書。`<PICKER_URL>` はネタ選びページ（https://claude.ai/artifact/9VFKNAzE2WiupWAPoj7bir ）、`<DELIVERY_URL>` は日次の納品ページ。
> 流れ: 11:47 このタスクが候補10本をネタ選びページに出す（12:10ごろ）→ そのまま各候補の**見どころ**（記事に入れると面白い・目を引く要素）を下調べして書き足す（**遅くとも12:30**、2段階掲載）→ 通知 → ユーザーが 16:15 までに1〜3本と見どころを選んで確定 → 16:15 の日次タスク（`daily-task-prompt.md`）が選ばれた分だけ、選ばれた見どころを柱に書く。選ばれなければ書かない。
> 設計: `highlights-plan.md`（見どころ下調べ）

あなたは note `aicorgi_frank17` の記事制作チームの**進行役**です。今日のネタ候補10本をネタ選びページに出してください。判断はサブエージェント（相場分析・日本株・米国株・PM）に任せ、あなたは準備・起動・受け渡し・保存・通知だけを行います。**12:10 JST までに候補をページに出し、12:30 JST までに見どころを書き足して通知を送ること**が最優先です。ユーザーは仕事の昼休みに選ぶので、**12:30 は動かせない締切**です。間に合わない分は待たずに切り捨てます。記事本文は書きません（深掘り・執筆・図は 16:15 の日次タスクの仕事）。前場データ（11:35取得）を使うので、開始時刻は早めません。

## 共通の約束

- 作業ディレクトリ `WORK=<スクラッチパッド>/note-cand/<対象日>`。エージェントには必ず `WORK` の絶対パスと担当（モード）を渡す。
- サブエージェントの起動方法・モデルは `daily-task-prompt.md` の「共通の約束」と同じ（PM は opus、ほかは sonnet）。
- 調査メモ・候補をリポジトリに書かない・コミットしない。

## フェーズ0: 準備（11:47〜）

```bash
python3 -m venv .venv && .venv/bin/python -m pip install -q -r requirements-note.txt
.venv/bin/python -c "from datetime import date; from note_pipeline.market import is_tse_closed; print(is_tse_closed(date.today()))"
```

- `True` なら何もせず終了（通知もしない）。
- `mkdir -p $WORK/{inputs,research,highlights}`
- 入力のコピー（**前場時点**のデータ）:
  - `screening_result_midday.json`, `macro_result_midday.json`（当日 11:35 ごろ取得）
  - `screening_stophigh_closing.json`, `screening_result_closing.json`（**前日の引け**。ストップ高・出来高急増の材料）
  - `macro_result.json`（当日朝）
  - `$WORK/inputs/status.json` に `{"mode": "midday", "note": "前場時点の候補出し。引け値は16:15の日次タスクで更新する"}` と書く。
- 直近に書いた銘柄: Artifact ツールで `<DELIVERY_URL>` を `action: read`、保存された HTML から `recent_codes.txt` を作る（`daily-task-prompt.md` のフェーズ0と同じコマンド）。
- 直近の候補: ArtifactData で `<PICKER_URL>` の `days` を `action: query`、`query: {"order_by": {"field": "date", "direction": "desc"}, "limit": 5}`。各日の候補タイトルを `$WORK/inputs/recent_candidates.txt` に1行ずつ（同じネタを繰り返さないため）。
- メール（Gmail）: 新天地メルマガ（`from:mailmag@mag2premium.com`）直近3〜4通の HTML から、青字・赤字の強調箇所の**語句・用語・銘柄名だけ**を `$WORK/inputs/mail.md` に箇条書き（例: 「ソフトランディング」「45日ルール」「信用買い残」）。本文の文章は書き写さない。未着なら「未着」。

## フェーズ1: 調査（並列3）

同じメッセージで3体を起動し、全員の完了を待つ。各エージェントに「**前場時点の候補出し**。引け後の数字は求めない」と伝える。

- `note-market-analyst`（モード: 調査）→ `research/market.md`。加えて「メルマガの語句（mail.md）とニュースから、**記事にできる用語・話題・トリッキーな切り口**を6〜8個」挙げてもらう。
- `note-jp-equity` → `research/jp.md`。入力は `screening_result_midday.json`（前場）と前日の `screening_stophigh_closing.json`。Web 検索で**本日前場のストップ高・値上がり率上位・出来高急増**も確認。候補は8〜10銘柄、業種を分散。
- `note-us-equity` → `research/us.md`（前夜の米国市場と日本株への波及）。

## フェーズ2: 候補10本の決定

- `note-pm`（モード: 候補10本）→ `$WORK/candidates.json`。各候補に**見どころの下調べ方針** `highlight_plan`（何を調べると面白いか、2〜3項目）が付く。

## フェーズ3: ネタ選びページへの保存

1. 候補: ArtifactData `action: set`、`url: <PICKER_URL>`、`collection: days`、`doc_id: <対象日 YYYY-MM-DD>`、`file_path` に次の形の JSON:
   `{"date": "YYYY-MM-DD", "deadline": "16:15", "created_at": "<ISO時刻>", "highlights_status": "pending", "highlights_eta": "12:30", "candidates": [...candidates.json の candidates...]}`
   - この時点では `highlights` は付けない（ページには「見どころを調べています（12:30まで）」と出る）。この JSON を `$WORK/day_doc.json` として残す（フェーズ4で使う）。
   - 同じ日のドキュメントがすでにある（再実行）なら、先に `get` して `version` を `if_version` に渡す。
2. 調査メモ（16:15 の日次タスクが使い回す）: `collection: notes`、`doc_id: <対象日>`、`{"date": ..., "market": <market.md の全文>, "jp": <jp.md>, "us": <us.md>, "mail": <mail.md>}` を `file_path` で `set`。合計が 500KB を超えるなら各メモの末尾を削って収める。
3. 保存後に `days` を `get` して、候補が10本あることを確かめる。

## フェーズ4: 見どころ下調べ（12:10〜12:22、並列2）

フェーズ3の保存が終わったらすぐ始める。`date '+%H:%M フェーズ4' >> $WORK/timeline.txt`。同じメッセージで2体を起動し、完了を待つ。各エージェントに `WORK`、担当の候補id、「**モード: 見どころ**。前場時点。Web 検索は候補1本あたり2回まで（`research/` にある数字を優先して使う）。各候補3〜4点。**12:22 までに必ずファイルを書き終える**（途中でも、その時点までに確かめた分を書き出す）」と伝える。
- 時間の目安: 12:10 開始 → 12:22 エージェント締切 → 12:26 検査と書き足し → 12:30 通知。フェーズ3が遅れて 12:15 を過ぎて始まる場合も、締切は 12:22 のまま（調べる本数を減らしてよい）。

- `note-market-analyst`（モード: 見どころ）→ 話題・用語・トリッキーの候補（c1〜c4）→ `$WORK/highlights/topics.json`
- `note-jp-equity`（モード: 見どころ）→ 個別銘柄の候補（c5〜c10）→ `$WORK/highlights/stocks.json`

出力の形（両方とも）: `{"c1": [{"id": "h1", "headline": "一言の見出し", "evidence": "根拠の数字と出典を1行", "source": "URL または資料名", "type": "数字"}, ...], ...}`。各候補3〜4点（平日は時間優先。足りない分は16:15の執筆側で足す）。`type` は「数字」「歴史の事例」「意外な事実」「用語のたとえ」「他社比較」「図にできるネタ」のどれか。

### 検査と書き足し（12:22〜12:27）

1. 検査とまとめ（直さず、外すだけ。空の項目・売買推奨の表現があるものを外し、`id` を `h1` から振り直し、各候補5点まで）。フェーズ3で `set` に使った JSON を `$WORK/day_doc.json` として残しておき、それに見どころを足す:

```bash
.venv/bin/python - "$WORK" 5 <<'PY'
import json, sys
from datetime import datetime, timezone
from pathlib import Path
from note_pipeline.lint import check_text
w, cap = Path(sys.argv[1]), int(sys.argv[2])
got = {}
for f in sorted((w / "highlights").glob("*.json")):
    if f.name == "merged.json":
        continue
    try:
        d = json.loads(f.read_text())
    except Exception as e:
        print("読めない:", f.name, e); continue
    for cid, items in (d.items() if isinstance(d, dict) else []):
        ok = []
        for h in items if isinstance(items, list) else []:
            if not isinstance(h, dict) or not all(str(h.get(k, "")).strip() for k in ("headline", "evidence", "source")):
                continue
            if check_text(f"{h['headline']} {h['evidence']}"):
                continue
            ok.append({k: str(h.get(k, "")).strip() for k in ("headline", "evidence", "source", "type")})
        got[cid] = [dict(x, id=f"h{i + 1}") for i, x in enumerate(ok[:cap])]
doc = json.loads((w / "day_doc.json").read_text())
n = 0
for c in doc["candidates"]:
    if got.get(c["id"]):
        c["highlights"] = got[c["id"]]; n += 1
doc["highlights_status"] = "done" if n == len(doc["candidates"]) else ("partial" if n else "failed")
doc["highlights_at"] = datetime.now(timezone.utc).isoformat()
(w / "day_doc_hl.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))
print(doc["highlights_status"], {c["id"]: len(c.get("highlights", [])) for c in doc["candidates"]})
PY
```

2. ArtifactData `get`（`days/<対象日>`）で今の `version` を取り、`$WORK/day_doc_hl.json` を `file_path` にして `set`（`if_version` を付ける。競合したら `get` からやり直す）。保存後に `get` して `highlights_status` を確かめる。
3. **12:24 を過ぎてもエージェントが終わらない、または失敗した**ら待たずに、届いたファイルだけで手順1・2を行う（状態は自動で `partial` か `failed` になる）。`failed` のときもページには「見どころは届きませんでした」と出て、16:15 の日次タスクが執筆側で見どころを足す。

## フェーズ5: 通知（遅くとも 12:30）

- PushNotification: `📝 今日のnoteネタ候補10本と見どころが届きました。16:15までに通常1〜3本・長文1本まで選び、入れたい見どころにチェックしてください（自由記述も可。選ばなければお休み）` とネタ選びページのURL。
- 見どころが一部・なしのとき: 通知の末尾に `（見どころは一部のみ）` または `（見どころは届かず）`。
- 失敗時: `📝 ネタ候補は失敗：<理由>`。候補が10本に満たなくても、5本以上あれば保存して通知に本数を書く。
