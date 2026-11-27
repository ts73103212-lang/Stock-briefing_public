# 朝マンガ ネタ選び Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 平日 13:55 に漫画のネタ候補4件をネタ選びページに出し、20:00 までのユーザーの選択（候補＋要望、または自由記述）を 20:05 の夕方制作が読んで描くようにする。選択がなければこれまでどおり Claude が選ぶ。

**Architecture:** 判断の決まった部分（候補 JSON の検証・注意喚起の週内回数・選択の読み分け・manifest の履歴）は `manga_pipeline/topics.py` と `manifest.py` に Python で切り出してテストする。ネタ選びページ `docs/manga/picker.html` は note のネタ選びページ（ブランチ `claude/dazzling-goldberg-ceo0fc` の `docs/note-pipeline/picker.html`）と同じ作りの単一 HTML で、Artifact の `db` 機能（`days` / `notes` / `picks`）を使う。候補出しタスク（新規・sonnet）と夕方制作タスク（既存・opus、時刻変更）は、それぞれ `docs/manga/` の手順書を読んで動く。

**Tech Stack:** Python 3.13（pytest、`.venv` に `requirements-note.txt`）、素の HTML/JS（Artifact の `db` 機能）、Node の Playwright 1.63（ページの動作確認。コンテナに導入済み）、claude.ai の定期タスク・ArtifactData・PushNotification。

**Spec:** `docs/superpowers/specs/2026-11-27-manga-topic-picker-design.md`（以下「設計書」）。前提として `docs/superpowers/specs/2026-11-23-morning-manga-design.md`（「元の設計書」）と、いまの `docs/manga/evening-task-prompt.md`。

## Global Constraints

- note のネタ選びページ・note の定期タスク・朝ブリーフィングの動作は変えない（設計書 §2）。`note_pipeline/` は import するだけで、変更しない。
- 候補の題材・セリフ・下調べメモ・ユーザーの選択は、リポジトリに書かない・コミットしない（`WORK/` は `.gitignore` 済み）。リポジトリに入れてよいのはページのソース・手順書・コード・テストだけ（設計書 §6.4）。テストの見本データは架空の短い文にする。
- 時刻はすべて日本時間（`Asia/Tokyo`）。コンテナは UTC。
- 候補出し：cron `CRON_TZ=Asia/Tokyo 55 13 * * 1-5`、モデル sonnet、毎回新しいセッション、スマホ通知あり、リポジトリは付けない（公開リポジトリを clone で読む）。通知は 14:30 まで。
- 夕方制作：cron `CRON_TZ=Asia/Tokyo 5 20 * * 1-5`、モデル opus のまま。締切は 題材 20:15 → 台本 20:30 → 描画の待ち 21:35 打ち切り → 納品 21:50 → 通知 22:00。
- 選択の締切 `"20:00"`。候補はちょうど4件、id は `c1`〜`c4`。`kind` は `theme` / `term` / `stock` / `caution`。`difficulty` は 1 / 2 / 3。
- 注意喚起の上限は週2回（`for_date` と同じ週の月〜金）。ユーザーの選択（候補・自由記述）には適用しない。
- manifest の `history` の各項目に `picked: "user" | "free" | "auto" | "replaced"` と `difficulty: 1|2|3` を足す。
- 投資助言に当たる表現は使わない。判定は `note_pipeline.lint.check_text` を流用する。
- ページの文字は Meiryo UI を先頭に（`"Meiryo UI","メイリオ",Meiryo,...`）。Artifact のページ契約（`<title>` で始め、doctype/html/head/body を書かない、色は `:root` のトークン＋ダークモード、16px の左右余白）を守る。
- 通知の文言（設計書のまま）:
  - 候補出し：`🐾 漫画のネタ候補が出ました（締切 20:00）：①<c1の題> ②<c2> ③<c3> ④<c4>` ＋ページのリンク
  - 制作の成功：`🐾 明日の漫画ができました：<title>（あなたの選択 / おまかせ / 差し替え）`。引けに合わせて切り口を変えた日は `（あなたの選択（引けに合わせて調整））`。差し替えは `選択ネタは<理由>のため差し替え` を添える。

## Review Focus

1. **選んだ id が候補に無い・候補の日の文書が無い**（候補出しが失敗した日に古いページから保存した、など）→ おまかせで描き、通知に理由を必ず書く。黙って別のネタにしない。→ Task 2 `test_resolve_unknown_id_falls_back_with_notice`
2. **候補が選択の後に作り直された**（候補出しの再実行で `days` の `created_at` が `picked_at` より新しい）→ 選んだ id の中身が変わっている可能性があるので、おまかせにして通知に書く。候補出しの手順書は、`picks/<今日>` があれば `days` を上書きしない。→ Task 2 `test_resolve_pick_older_than_candidates`、Task 4 の手順
3. **id と free が両方入っている・空白だけの要望/自由記述**（ページを経ずに書かれた、古いページ）→ id を優先し free は捨てて通知、空白だけは「無し」として扱う。→ Task 2 `test_resolve_id_wins_over_free`・`test_resolve_blank_strings_are_none`
4. **締切後・候補の無い日にページを開いた／開きっぱなしで 20:00 をまたいで保存を押した** → 選択欄を閉じて「締切済み」、保存は書き込まない。候補の無い日は「今日の候補はまだありません」と出し、過去の日は見るだけ。→ Task 3 の Playwright 確認 `deadline`・`no-today`
5. **注意喚起の週の数え方**（金曜作成→月曜掲載で週が替わる、同じ `for_date` を作り直した履歴、`picked` の無い古い履歴）→ `for_date` の週で数え、同じ `for_date` の項目は数えない、古い形式の履歴でも落ちない。→ Task 1 `test_caution_count_*`、Task 5 `test_history_old_entries_without_picked`

---

## File Structure

| ファイル | 役割 |
|---|---|
| Create `manga_pipeline/topics.py` | 候補の日の文書の組み立てと検証（`build_day`）、注意喚起の週内回数（`caution_count` / `caution_note`）、選択の読み分け（`resolve_pick`）、CLI `build-day` / `resolve` |
| Create `tests/manga_pipeline/test_topics.py` | 上のテスト |
| Modify `manga_pipeline/manifest.py` | `build_manifest` に `picked` / `difficulty` を足し、`history` に残す。CLI に `--picked` / `--difficulty` |
| Modify `tests/manga_pipeline/test_manifest.py` | 既存の呼び出しを新しい引数に合わせ、履歴のテストを足す |
| Create `docs/manga/picker.html` | ネタ選びページ（Artifact に公開するソース） |
| Create `tests/manga_pipeline/picker_check.mjs` | Playwright でページを開き、偽の `db` で動作を確かめる |
| Create `tests/manga_pipeline/test_picker_html.py` | 上を pytest から呼ぶ（node / playwright が無ければ skip） |
| Create `docs/manga/candidates-task-prompt.md` | 候補出しタスクの手順書 |
| Modify `docs/manga/evening-task-prompt.md` | 選択の読み分け・時刻・通知・manifest の引数 |
| Modify `docs/manga/briefing-manga.md:3` | タスク名の時刻（17:45 → 20:05）だけ直す |

---

### Task 1: 候補の日の文書と注意喚起の数え方（`topics.py` 前半）

**Files:**
- Create: `manga_pipeline/topics.py`
- Test: `tests/manga_pipeline/test_topics.py`

**Interfaces:**
- Consumes: `manga_pipeline.manifest.KINDS`, `manga_pipeline.manifest.next_business_day(d: date) -> date`, `manga_pipeline.manifest.JST`, `note_pipeline.lint.check_text(text: str) -> list[str]`
- Produces:
  - 定数 `DEADLINE = "20:00"`, `CANDIDATE_IDS = ["c1", "c2", "c3", "c4"]`, `CHARACTERS = {"corgi", "mirai", "gonda"}`, `CAUTION_CAP = 2`, `TITLE_MAX = 40`, `SUMMARY_MAX = 120`, `HOOK_MAX = 80`
  - `caution_count(history: list[dict], for_date: date) -> int` — `history` のうち `kind == "caution"` で、`for_date` と同じ週（月曜始まり）にあり、`for_date` そのものではない項目の数。
  - `caution_note(history: list[dict], for_date: date) -> str | None` — `caution_count >= CAUTION_CAP` なら `f"今週{count + 1}回目"`、それ以外は `None`。
  - `build_day(made_at: datetime, candidates: list[dict], memos: dict[str, str], history: list[dict]) -> tuple[dict, dict]` — `(day_doc, notes_doc)` を返す。問題があれば全部まとめて `ValueError`（メッセージは1行1件）。
    - `day_doc = {"date": made_at の JST 日付, "for_date": next_business_day(date), "deadline": "20:00", "created_at": ISO（JST・分まで）, "candidates": [...]}`
    - 各候補は入力の `{id, title, kind, difficulty, summary, hook, characters}` を残し、`caution_count_note` は `kind == "caution"` のときだけ `caution_note(history, for_date)` で上書き（`None` ならキーを付けない）。それ以外の kind に入力で付いていれば消す。
    - `notes_doc = {"date": date, "memos": {"c1": memos["c1"], ...}}`
  - CLI: `python -m manga_pipeline.topics build-day --candidates F --memos F --prev F --day-out F --notes-out F [--made-at ISO]`。`--candidates` は `{"candidates": [...]}`、`--memos` は `{"c1": "<下調べメモ>", ...}`、`--prev` は前回 manifest（無いファイルなら履歴なし）。成功で `{"date", "for_date", "kinds": [...], "caution_notes": {...}}` を標準出力、失敗で問題を stderr に出して終了コード 1。

- [ ] **Step 1: 失敗するテストを書く**

`tests/manga_pipeline/test_topics.py`（見本データは架空の短い文。ヘルパー `_cands()` は c1 term☆1・c2 theme☆2・c3 stock☆2・c4 caution☆3 を返し、`_memos()` は4件の短いメモ）:

```python
def test_caution_count_same_week_only():
    h = [{"for_date": "2026-11-24", "kind": "caution"}, {"for_date": "2026-11-26", "kind": "caution"},
         {"for_date": "2026-11-20", "kind": "caution"}, {"for_date": "2026-11-25", "kind": "term"}]
    assert caution_count(h, date(2026, 11, 27)) == 2

def test_caution_count_excludes_same_for_date():
    h = [{"for_date": "2026-11-27", "kind": "caution"}]
    assert caution_count(h, date(2026, 11, 27)) == 0

def test_caution_count_new_week_on_monday():
    h = [{"for_date": "2026-11-24", "kind": "caution"}, {"for_date": "2026-11-26", "kind": "caution"}]
    assert caution_count(h, date(2026, 11, 30)) == 0

def test_caution_note():
    h = [{"for_date": "2026-11-24", "kind": "caution"}, {"for_date": "2026-11-25", "kind": "caution"}]
    assert caution_note(h, date(2026, 11, 27)) == "今週3回目"
    assert caution_note(h[:1], date(2026, 11, 27)) is None

def test_build_day_shape():
    day, notes = build_day(datetime(2026, 11, 27, 14, 5, tzinfo=JST), _cands(), _memos(), [])
    assert day["date"] == "2026-11-27" and day["for_date"] == "2026-11-30" and day["deadline"] == "20:00"
    assert day["created_at"].startswith("2026-11-27T14:05")
    assert [c["id"] for c in day["candidates"]] == ["c1", "c2", "c3", "c4"]
    assert "caution_count_note" not in day["candidates"][3]
    assert notes == {"date": "2026-11-27", "memos": _memos()}

def test_build_day_sets_caution_note_from_history():
    h = [{"for_date": "2026-11-24", "kind": "caution"}, {"for_date": "2026-11-26", "kind": "caution"}]
    day, _ = build_day(datetime(2026, 11, 26, 14, 0, tzinfo=JST), _cands(), _memos(), h)
    assert day["candidates"][3]["caution_count_note"] == "今週3回目"   # for_date 11/27

def test_build_day_drops_note_on_non_caution():
    c = _cands(); c[0]["caution_count_note"] = "今週3回目"
    day, _ = build_day(datetime(2026, 11, 27, 14, 0, tzinfo=JST), c, _memos(), [])
    assert "caution_count_note" not in day["candidates"][0]

@pytest.mark.parametrize("mutate, word", [
    (lambda c: c.pop(), "4"),                                    # 3件
    (lambda c: c[1].update(id="c1"), "id"),                      # id の重複・順番違い
    (lambda c: c[0].update(kind="gossip"), "kind"),
    (lambda c: c[0].update(difficulty=4), "difficulty"),
    (lambda c: c[0].update(difficulty=True), "difficulty"),     # bool は数として扱わない
    (lambda c: c[0].update(title="  "), "title"),
    (lambda c: c[0].update(title="あ" * 41), "title"),
    (lambda c: c[0].update(summary="あ" * 121), "summary"),
    (lambda c: c[0].update(hook=""), "hook"),
    (lambda c: c[0].update(characters=["corgi", "tanaka"]), "characters"),
    (lambda c: c[0].update(characters=[]), "characters"),
    (lambda c: [x.update(kind="term") for x in c], "kind"),     # 4件すべて同じ kind
    (lambda c: c[2].update(summary="今が買い時の銘柄"), "推奨"),  # check_text に掛かる
])
def test_build_day_rejects(mutate, word):
    c = _cands(); mutate(c)
    with pytest.raises(ValueError, match=word):
        build_day(datetime(2026, 11, 27, 14, 0, tzinfo=JST), c, _memos(), [])

def test_build_day_needs_memo_for_each():
    m = _memos(); m["c3"] = " "
    with pytest.raises(ValueError, match="c3"):
        build_day(datetime(2026, 11, 27, 14, 0, tzinfo=JST), _cands(), m, [])

def test_cli_build_day(tmp_path):   # 書き出した2ファイルの date と、標準出力の for_date を確かめる
    ...  # 入力を tmp_path に書き、--prev は存在しないパスにする。returncode 0、day_out の for_date == "2026-11-30"

def test_cli_build_day_error_exit(tmp_path):   # 3件の候補で returncode 1、stderr に "4" を含む
    ...
```

- [ ] **Step 2: テストが失敗することを確かめる**

Run: `.venv/bin/python -m pytest tests/manga_pipeline/test_topics.py -q`
Expected: FAIL（`ModuleNotFoundError: No module named 'manga_pipeline.topics'`）

- [ ] **Step 3: `manga_pipeline/topics.py` に定数・`caution_count`・`caution_note`・`build_day`・CLI の `build-day` を書く**

`argparse` のサブコマンド（`build-day` と、Task 2 で足す `resolve`）。問題は集めてから `ValueError("\n".join(problems))`。週の判定は `d - timedelta(days=d.weekday())` が同じかどうか。`check_text` は title・summary・hook に掛け、ヒットは `"<id>.<field>: <check_text の文>"` として問題に入れる。モジュールの docstring に CLI の使い方（`manifest.py` と同じ書き方）。

- [ ] **Step 4: テストが通ることを確かめる**

Run: `.venv/bin/python -m pytest tests/manga_pipeline/test_topics.py -q`
Expected: PASS

- [ ] **Step 5: コミット**

```bash
git add manga_pipeline/topics.py tests/manga_pipeline/test_topics.py
git commit -m "feat(manga): ネタ候補の日の文書の検証と注意喚起の週内回数"
```

---

### Task 2: 選択の読み分け（`resolve_pick`）

**Files:**
- Modify: `manga_pipeline/topics.py`
- Test: `tests/manga_pipeline/test_topics.py`

**Interfaces:**
- Consumes: Task 1 の `caution_count`, `next_business_day`, `check_text`
- Produces:
  - `resolve_pick(today: date, day: dict | None, pick: dict | None, notes: dict | None, history: list[dict]) -> dict`。返り値:
    ```
    {"mode": "user" | "free" | "auto",
     "for_date": "YYYY-MM-DD",            # next_business_day(today)
     "candidate": dict | None,           # mode == "user" のときの days の候補
     "memo": str | None,                 # 同じ候補の notes.memos[id]（無ければ None）
     "request": str | None,              # mode == "user" のときだけ
     "free": str | None,                 # mode == "free" のときだけ
     "caution_cap_applies": bool,        # mode == "auto" のときだけ True
     "caution_count": int,               # caution_count(history, for_date)
     "notices": list[str],               # 通知に書く一言（日本語）。無ければ []
     "warnings": list[str]}              # request / free に check_text が掛かった文
    ```
  - 読み分けの規則（上から順に）:
    1. `day` が無い、または `day["date"] != today` → 候補なし扱い。
    2. `pick` の `request` / `free` は前後の空白を取り、空なら `None`。
    3. `pick["id"]` がある：
       - 候補なし、または `day` の候補に id が無い → `auto`、notices に `f"選択した候補 {id} が見つからないため、おまかせで描きます"`。
       - `pick["picked_at"]` が `day["created_at"]` より前（両方 ISO として datetime 比較。どちらか読めなければこの判定は飛ばす）→ `auto`、notices に `"候補が選択の後に作り直されたため、おまかせで描きます"`。
       - それ以外 → `user`。`free` も入っていれば捨てて notices に `"自由記述は、候補を選んだので使いません"`。
    4. id が無く `free` がある → `free`（候補なしでもよい）。`request` は捨てる（notices なし）。
    5. どちらも無い／`pick` が無い → `auto`、notices なし。
  - CLI: `python -m manga_pipeline.topics resolve --day F --pick F --notes F --prev F --out F [--today YYYY-MM-DD]`。どのファイルも、存在しなければ `None`（`--prev` は `history: []`）。`--today` の既定は JST の今日。結果を `--out` に書き、`{"mode", "for_date", "id", "notices"}` を標準出力。

- [ ] **Step 1: 失敗するテストを書く**

`TODAY = date(2026, 11, 27)`、`_day()` は Task 1 の `build_day(datetime(2026,11,27,14,5,tzinfo=JST), ...)` の day_doc、`_notes()` はその notes_doc。

```python
def test_resolve_user_pick_with_request():
    r = resolve_pick(TODAY, _day(), {"id": "c2", "request": " PTSの時間帯も ", "free": None,
                     "picked_at": "2026-11-27T06:12:00Z"}, _notes(), [])
    assert r["mode"] == "user" and r["candidate"]["id"] == "c2" and r["memo"] == _memos()["c2"]
    assert r["request"] == "PTSの時間帯も" and r["free"] is None
    assert r["caution_cap_applies"] is False and r["notices"] == [] and r["for_date"] == "2026-11-30"

def test_resolve_free_only():
    r = resolve_pick(TODAY, _day(), {"id": None, "request": "x", "free": "ゴンダ先輩の失敗談", "picked_at": "2026-11-27T06:00:00Z"}, _notes(), [])
    assert r["mode"] == "free" and r["free"] == "ゴンダ先輩の失敗談" and r["request"] is None and r["candidate"] is None
    assert r["caution_cap_applies"] is False

def test_resolve_free_without_day():
    r = resolve_pick(TODAY, None, {"id": None, "free": "PTSの話", "picked_at": "2026-11-27T06:00:00Z"}, None, [])
    assert r["mode"] == "free"

def test_resolve_no_pick_is_auto():
    h = [{"for_date": "2026-11-24", "kind": "caution"}]
    r = resolve_pick(TODAY, _day(), None, _notes(), h)
    assert r["mode"] == "auto" and r["caution_cap_applies"] is True and r["notices"] == []
    assert r["caution_count"] == 0   # for_date 11/30 は翌週

def test_resolve_cleared_pick_is_auto():
    assert resolve_pick(TODAY, _day(), {"id": None, "request": None, "free": None}, _notes(), [])["mode"] == "auto"

def test_resolve_unknown_id_falls_back_with_notice():
    r = resolve_pick(TODAY, _day(), {"id": "c5", "picked_at": "2026-11-27T06:00:00Z"}, _notes(), [])
    assert r["mode"] == "auto" and "c5" in r["notices"][0]

def test_resolve_day_of_other_date_is_no_candidates():
    d = _day(); d["date"] = "2026-11-26"
    r = resolve_pick(TODAY, d, {"id": "c1", "picked_at": "2026-11-27T06:00:00Z"}, _notes(), [])
    assert r["mode"] == "auto" and r["notices"]

def test_resolve_pick_older_than_candidates():
    r = resolve_pick(TODAY, _day(), {"id": "c1", "picked_at": "2026-11-27T04:00:00Z"}, _notes(), [])  # 13:00 JST < 14:05
    assert r["mode"] == "auto" and "作り直" in r["notices"][0]

def test_resolve_id_wins_over_free():
    r = resolve_pick(TODAY, _day(), {"id": "c3", "free": "別の話", "picked_at": "2026-11-27T06:00:00Z"}, _notes(), [])
    assert r["mode"] == "user" and r["free"] is None and r["notices"]

def test_resolve_blank_strings_are_none():
    r = resolve_pick(TODAY, _day(), {"id": None, "request": "  ", "free": " \n", "picked_at": "2026-11-27T06:00:00Z"}, _notes(), [])
    assert r["mode"] == "auto"

def test_resolve_memo_missing_is_none():
    r = resolve_pick(TODAY, _day(), {"id": "c1", "picked_at": "2026-11-27T06:00:00Z"}, None, [])
    assert r["mode"] == "user" and r["memo"] is None

def test_resolve_warns_on_advice_words():
    r = resolve_pick(TODAY, _day(), {"id": None, "free": "今が買い時の株を教えて", "picked_at": "2026-11-27T06:00:00Z"}, _notes(), [])
    assert r["mode"] == "free" and r["warnings"]

def test_cli_resolve_missing_files(tmp_path):   # どのファイルも無い → returncode 0、out の mode == "auto"
    ...
```

- [ ] **Step 2: テストが失敗することを確かめる**

Run: `.venv/bin/python -m pytest tests/manga_pipeline/test_topics.py -q -k resolve`
Expected: FAIL（`ImportError: cannot import name 'resolve_pick'`）

- [ ] **Step 3: `resolve_pick(...)` と CLI の `resolve` を `manga_pipeline/topics.py` に足す**

時刻の比較は `datetime.fromisoformat`（`Z` も読める）で aware 同士を比べる。

- [ ] **Step 4: テストが通ることを確かめる**

Run: `.venv/bin/python -m pytest tests/manga_pipeline/test_topics.py -q`
Expected: PASS

- [ ] **Step 5: コミット**

```bash
git add manga_pipeline/topics.py tests/manga_pipeline/test_topics.py
git commit -m "feat(manga): ユーザーのネタ選択の読み分け"
```

---

### Task 3: ネタ選びページ `picker.html`

**Files:**
- Create: `docs/manga/picker.html`
- Create: `tests/manga_pipeline/picker_check.mjs`
- Create: `tests/manga_pipeline/test_picker_html.py`

**Interfaces:**
- Consumes: 保存領域の形（Task 1 の `day_doc`）。`picks/<date>` に書く形は Task 2 の `resolve_pick` が読む形。
- Produces:
  - 保存領域 `picks/<作成日>` に `{"date": "YYYY-MM-DD", "id": "c1".."c4" | null, "request": str | null, "free": str | null, "picked_at": new Date().toISOString()}` を `set` する。id がある保存では `free` を必ず `null`、id が無い保存では `request` を必ず `null` にする。「おまかせに戻す」は3つとも `null`。
  - `db` の使い方は note のページと同じ：`claude.use("db")`、`db.collection("days").orderBy("date","desc").limit(7).onSnapshot(cb, err)`、`db.doc("picks/"+date).onSnapshot(cb)`、`db.doc("picks/"+date).set(doc)`。
  - Playwright 確認で使う要素の id: `#cards`（候補カード。各カードは `data-id="c1"` と `input[type=radio][name=pick][value=c1]`）、`#request`（候補を選ぶと出る要望欄）、`#free-radio` と `#free`（自由記述だけで頼む）、`#save`、`#auto`（おまかせに戻す）、`#status`（受付中・締切済み）、`#current`（いまの選択）、`#msg`、`#days`（直近の日の切り替え）。

- [ ] **Step 1: 準備：作りを確かめる**

`git show origin/claude/dazzling-goldberg-ceo0fc:docs/note-pipeline/picker.html` を読み、色のトークン・`jstNow()`・`isOpen(day)`・`start()`・`save()` の作りを流用元にする。公開する前に `artifact-capabilities` スキルを読み、`db` 機能の宣言と `claude.use("db")` の呼び方が note のページのままでよいか確かめる（違えばスキルに合わせ、`picker_check.mjs` の偽の db も合わせる）。

- [ ] **Step 2: 失敗する確認を書く**

`picker_check.mjs`：`file://…/docs/manga/picker.html` を開き、`addInitScript` で偽の `window.claude.use("db")` を入れる（`days` は引数で渡す配列、`picks` は Map、`set` の呼び出しを `window.__sets` に積む）。`page.clock.setFixedTime(...)` で時刻を固定。シナリオ名を引数で受け、失敗なら終了コード 1。見本の days は 2026-11-27 作成・for_date 2026-11-30・c4 に `caution_count_note: "今週3回目"`。

| シナリオ | 時刻（JST） | 確かめること |
|---|---|---|
| `render` | 11/27 15:12 | カード4枚、☆の数が difficulty どおり、種類の表示（用語・振り返り・話題・注意喚起）、`11/30(月) 朝に掲載`、`締切 20:00`、c4 に `今週3回目`、`#request` は候補を選ぶまで非表示 |
| `pick-request` | 11/27 15:12 | c2 を選び要望を入れて保存 → `__sets` 最後が `{date:"2026-11-27", id:"c2", request:"PTSの時間帯も入れて", free:null}`（picked_at 以外）、`#current` に `c2` と要望 |
| `free-exclusive` | 11/27 15:12 | c1＋要望を入れてから自由記述に切り替えて保存 → `{id:null, request:null, free:"<文>"}` |
| `blank-free` | 11/27 15:12 | 自由記述を選んで空白だけ → `#save` が押せない（または押しても `set` されず `#msg` に案内） |
| `auto` | 11/27 15:12 | 「おまかせに戻す」→ `{id:null, request:null, free:null}` |
| `reload` | 11/27 15:12 | 既存の picks `{id:"c3", request:"x"}` があると、開いたとき c3 が選ばれ要望欄に `x` |
| `deadline` | 11/27 20:00 | 入力がすべて無効、`#status` に `締切済み`、保存しても `set` されない |
| `cross-deadline` | 19:59 で開き、時計を 20:01 に進めてから保存 | `set` されない、`#msg` に締切の案内 |
| `no-today` | 11/30 10:00（days は 11/27 のみ） | `今日の候補はまだありません` と出し、11/27 の候補は見るだけ（入力無効） |
| `no-db` | `claude.use` が null を返す | `このページは、サインインした本人だけが使えます。` |

`test_picker_html.py`：`shutil.which("node")` が無い、または `node -e "require('playwright')"` が失敗すれば `pytest.skip`。シナリオごとに `subprocess.run(["node", "tests/manga_pipeline/picker_check.mjs", name], cwd=REPO, timeout=60)` を `parametrize` し、returncode 0 を期待。加えて、ソースが `<title>朝マンガ ネタ選び</title>` で始まり、`<!doctype`・`<html`・`<body` を含まず、`Meiryo UI` と `prefers-color-scheme: dark` を含むことを確かめる（`test_manifest.py::test_index_follows_artifact_page_contract` と同じ書き方）。

- [ ] **Step 3: 確認が失敗することを確かめる**

Run: `.venv/bin/python -m pytest tests/manga_pipeline/test_picker_html.py -q`
Expected: FAIL（picker.html が無い）

- [ ] **Step 4: `docs/manga/picker.html` を書く**

画面は設計書 §6.1 の図のとおり（1列のカード、カードを選ぶとその下に要望欄、最後に「自由記述だけで頼む」、画面下に保存バーと「いまの選択」）。保存の直前にも `isOpen(current)` を確かめる（開きっぱなしで締切をまたいだとき用）。毎分の再描画で締切を過ぎたら入力を閉じる。直近7日の候補は `#days` の切り替えで見られる（過去の日は見るだけ）。要望・自由記述の下書きは `localStorage`（try/catch で囲む）。入力の長さは要望 200 字・自由記述 300 字まで。

- [ ] **Step 5: 確認が通ることを確かめる**

Run: `.venv/bin/python -m pytest tests/manga_pipeline/test_picker_html.py -q`
Expected: PASS（10シナリオ＋ページ契約）

- [ ] **Step 6: Artifact として公開し、URL を控える**

Artifact ツールで `docs/manga/picker.html` を publish（新規。`icon: "comic"`、`capabilities` は Step 1 で確かめた `db` の宣言、description「朝マンガのネタ候補から1件を選ぶページ」）。返ってきた URL を以降 `<MANGA_PICKER_URL>` と呼び、Task 4・Task 6 の手順書に書き込む。ArtifactData で `days/2026-01-01`（架空の日）に Task 1 の見本の形の文書を `set` → ページで見えることを確かめ → `delete` する。

- [ ] **Step 7: コミット**

```bash
git add docs/manga/picker.html tests/manga_pipeline/picker_check.mjs tests/manga_pipeline/test_picker_html.py
git commit -m "feat(manga): 朝マンガ ネタ選びページ"
```

---

### Task 4: 候補出しタスクの手順書

**Files:**
- Create: `docs/manga/candidates-task-prompt.md`

**Interfaces:**
- Consumes: `python -m manga_pipeline.topics build-day ...`（Task 1）、`<MANGA_PICKER_URL>`（Task 3）、納品先 `https://claude.ai/artifact/9m4Jxvrm3aj12NaojgBiUW` の `manga/manifest.json`、note のネタ選び `https://claude.ai/artifact/9VFKNAzE2WiupWAPoj7bir`
- Produces: ネタ選びページの `days/<今日>` と `notes/<今日>`。通知。

- [ ] **Step 1: 手順書を書く**

構成は `evening-task-prompt.md` に合わせる（冒頭の引用ブロックに URL と設計書、共通の約束、フェーズ、失敗時の表）。中身は設計書 §6.2 のとおりで、次の決めごとを入れる:

- フェーズ0（13:55〜）：`git clone -q --depth 1 https://github.com/ts73103212-lang/Stock-briefing_public repo && cd repo`、venv、`is_tse_closed` が True なら通知なしで終了。作業は `WORK/`。前回 manifest を Artifact `read`（`path: "manga/manifest.json"`）→ `WORK/prev_manifest.json`（読めなければ無し）。ページの直近5日の `days` を ArtifactData `query`（`order_by date desc, limit 5`）→ 題名を `WORK/recent_titles.txt`。note の `days/<今日>` を `get`（読めなければ飛ばす）。
- **再実行のガード**：`picks/<今日>` を `get` し、すでにあれば `days` を上書きせず、通知 `🐾 漫画のネタ候補は作り直しませんでした（すでに選択があります）` で終了。無く `days/<今日>` がある場合だけ、`version` を `if_version` に渡して上書きする。
- フェーズ1（〜14:15）：材料は `macro_result.json`・`macro_result_midday.json`・`screening_result_midday.json`・Web 検索（ニュースは5〜8件）。大引けの数字はまだ無いので、候補の文に引けの数字を断定で書かない（「前場で」と書く）。
- フェーズ2（〜14:20）：4件と下調べメモを `WORK/candidates.json`・`WORK/memos.json` に書く。種類を散らす（theme・term・stock から少なくとも各1件を目安）。難易度は設計書 §6.1 の基準表（☆1 用語の基本／☆2 指標・値動きの読み方／☆3 需給・制度の応用）を手順書にそのまま載せる。`characters` は登場人物のキー。下調べメモは「使う数字と出典 URL・台本の骨子（起承転結を各1行）・豆知識の出典」。確かめられない数字・豆知識は候補に入れない。`caution_count_note` は書かない（`build-day` が履歴から付ける）。
- フェーズ3：`.venv/bin/python -m manga_pipeline.topics build-day --candidates WORK/candidates.json --memos WORK/memos.json --prev WORK/prev_manifest.json --day-out WORK/day_doc.json --notes-out WORK/notes_doc.json`。終了コード 1 なら stderr の問題を直して再実行（3回まで）。ArtifactData `set`（`collection: days` / `notes`、`doc_id: <今日>`、`file_path`）→ `get` で4件あることを確かめる。
- フェーズ4（14:30 まで）：PushNotification（Global Constraints の文言＋ `<MANGA_PICKER_URL>`）。
- 失敗時：14:30 までに保存できなければ `🐾 漫画のネタ候補は本日なし：<理由>（今夜は Claude が選んで描きます）`。休場日は通知なし。
- 公開リポジトリには何も書かない（push しない）。

- [ ] **Step 2: 手順書の中のコマンドを手元で通す**

Task 1 のテストの見本を `WORK/` に置いて、手順書のフェーズ0の venv・`is_tse_closed`・フェーズ3の `build-day` コマンドをそのまま貼って実行する。
Expected: `build-day` が `{"date": ..., "for_date": ..., ...}` を出し、`WORK/day_doc.json` と `WORK/notes_doc.json` ができる。終わったら `WORK/` の見本は消す。

- [ ] **Step 3: コミット**

```bash
git add docs/manga/candidates-task-prompt.md
git commit -m "docs(manga): ネタ候補タスクの手順書"
```

---

### Task 5: manifest の履歴に選択の有無と難易度を残す

**Files:**
- Modify: `manga_pipeline/manifest.py:39-60`（`build_manifest`）、`:103-125`（CLI）
- Test: `tests/manga_pipeline/test_manifest.py`

**Interfaces:**
- Consumes: なし
- Produces:
  - `PICKED = {"user", "free", "auto", "replaced"}`
  - `build_manifest(made_at, title, kind, explanation_html, rows, prev, *, picked: str, difficulty: int) -> dict`。`picked` が `PICKED` に無い、`difficulty` が 1〜3 の int でない（bool は不可）なら `ValueError`。`history` の新しい項目は `{"for_date", "kind", "picked", "difficulty"}`。古い項目はそのまま残す（キーを足さない）。
  - CLI に `--picked`（必須、choices `PICKED`）と `--difficulty`（必須、`type=int`, choices 1〜3）。

- [ ] **Step 1: テストを直し、足す**

既存の `build_manifest(...)` の呼び出しすべてに `picked="auto", difficulty=1` を足し、`test_cli`・`test_cli_prev_missing_is_ok` の引数に `--picked auto --difficulty 1` を足す。履歴の等値比較は新しいキーを含めて書き直す（`test_history_keeps_last5` の最後は `{"for_date": "2026-11-25", "kind": "caution", "picked": "auto", "difficulty": 1}`）。足すテスト:

```python
def test_history_records_picked_and_difficulty(tmp_path):
    m = build_manifest(datetime(2026, 11, 27, 21, 40, tzinfo=JST), "t", "term", EXPL, _rows(tmp_path), None,
                       picked="user", difficulty=2)
    assert m["history"] == [{"for_date": "2026-11-30", "kind": "term", "picked": "user", "difficulty": 2}]

def test_history_old_entries_without_picked(tmp_path):
    prev = {"history": [{"for_date": "2026-11-26", "kind": "caution"}]}
    m = build_manifest(datetime(2026, 11, 26, 21, 0, tzinfo=JST), "t", "theme", EXPL, _rows(tmp_path), prev,
                       picked="replaced", difficulty=3)
    assert m["history"][0] == {"for_date": "2026-11-26", "kind": "caution"}
    assert m["history"][1]["picked"] == "replaced"

@pytest.mark.parametrize("kw", [{"picked": "mine", "difficulty": 1}, {"picked": "auto", "difficulty": 0},
                                {"picked": "auto", "difficulty": True}])
def test_rejects_bad_picked_or_difficulty(tmp_path, kw):
    with pytest.raises(ValueError):
        build_manifest(datetime(2026, 11, 24, 18, 0, tzinfo=JST), "t", "term", EXPL, _rows(tmp_path), None, **kw)

def test_cli_requires_picked(tmp_path):   # --picked なしで returncode != 0
    ...
```

- [ ] **Step 2: テストが失敗することを確かめる**

Run: `.venv/bin/python -m pytest tests/manga_pipeline/test_manifest.py -q`
Expected: FAIL（`unexpected keyword argument 'picked'`）

- [ ] **Step 3: `build_manifest` と CLI を直す**

モジュールの docstring の CLI 例にも `--picked` / `--difficulty` を足す。

- [ ] **Step 4: テストが通ることを確かめる**

Run: `.venv/bin/python -m pytest tests/manga_pipeline -q`
Expected: PASS（全件）

- [ ] **Step 5: コミット**

```bash
git add manga_pipeline/manifest.py tests/manga_pipeline/test_manifest.py
git commit -m "feat(manga): manifest の履歴に選択の有無と難易度を残す"
```

> この変更で manifest の CLI は `--picked` が必須になる。夕方制作は `main` を pull して動くので、Task 6 の手順書と**同じマージで main に入れる**（Task 7）。

---

### Task 6: 夕方制作の手順書を直す

**Files:**
- Modify: `docs/manga/evening-task-prompt.md`
- Modify: `docs/manga/briefing-manga.md:3`（`夕方制作（平日17:45）` → `夕方制作（平日20:05）`）

**Interfaces:**
- Consumes: `python -m manga_pipeline.topics resolve ...`（Task 2）、`manifest --picked --difficulty`（Task 5）、`<MANGA_PICKER_URL>`（Task 3）
- Produces: なし（手順書）

- [ ] **Step 1: 手順書を直す**

設計書 §6.3 のとおり。具体的には:

- 題名を `（平日 20:05 JST）`、冒頭の最優先を「**22:00 JST までに納品と通知**」、共通の約束の締切を Global Constraints の5つの時刻に。フェーズ4のループの打ち切りを `-ge 2135`、`TIMEOUT` の理由を「描画が 21:35 までに終わらなかった」、フェーズ5の「19:15 を過ぎたら」を 21:35、フェーズ7を「〜21:50」、フェーズ8を「〜22:00」、失敗時の表の 19:15 / 19:30 も合わせる。設計書の行に `docs/superpowers/specs/2026-11-27-manga-topic-picker-design.md` を足す。
- フェーズ0の最後に **「選択を確かめる」** を足す：ArtifactData `get` で `<MANGA_PICKER_URL>` の `days/<今日>`・`notes/<今日>`・`picks/<今日>` を取り、それぞれ `WORK/day.json`・`WORK/notes.json`・`WORK/pick.json` に保存（無ければ作らない）。続けて
  `.venv/bin/python -m manga_pipeline.topics resolve --day WORK/day.json --pick WORK/pick.json --notes WORK/notes.json --prev WORK/prev_manifest.json --out WORK/choice.json`。
  `WORK/choice.json` の `notices` は通知の2行目以降にそのまま入れる。
- フェーズ1を `mode` で分ける:
  - `user`：題材は `candidate`、下調べは `memo`。題材決めは飛ばし、`memo` の数字を**引けの JSON・報道の大引け値で確かめ直す**。`request` は台本と解説に取り入れる（`warnings` がある、または投資助言・未確認の数字に当たる部分は取り入れず、通知に一言）。`caution` の週2回上限は見ない。
  - 前提が引けで崩れたとき（設計書 §6.3 の例をそのまま載せる）→ 同じ題材で切り口を変え、`WORK/topic.md` に `adjusted: true`。題材の中身（用語・仕組み・出来事）が成り立たないときだけ差し替え。
  - `free`：自由記述から題材を立て、kind・難易度を決める。失敗談なら `caution` で、上限は見ない。
  - `auto`：これまでどおり。`caution_cap_applies` が True なので、`caution_count` が 2 以上なら `caution` を選ばない（いまの手での数え方の段落はこの1行に置き換える）。`day` の候補から選んでもよい。
  - どの場合も難易度を決めて `WORK/topic.md` に書く。
- フェーズ2の台本・解説のルールに、難易度の目安（設計書 §6.3：☆1 用語をかみくだき数字は1〜2個まで／☆2 その日の数字と読み方／☆3 需給・制度まで。解説は 350〜550 字のまま）を足す。
- **差し替え**（選ばれたネタが描けない：裏付けが取れない・投資助言にしかならない、など）は、フェーズ1〜2の間だけ。Claude の選んだネタに切り替え、`picked` は `replaced`、通知に `選択ネタは<理由>のため差し替え`。描き直しの上限で重い問題が残った場合は、元のとおり見送る（差し替えない）。
- フェーズ7の manifest コマンドに `--picked <user|free|auto|replaced> --difficulty <1|2|3>` を足す（`user` は `mode == "user"` で差し替えなかった日。引けに合わせて調整した日も `user`）。
- フェーズ8の成功文を Global Constraints の文言に（`（あなたの選択）` / `（あなたの選択（引けに合わせて調整））` / `（おまかせ）` / `（差し替え）`。`free` は「あなたの選択」）。2行目の描き直しの記録はそのまま、3行目以降に `notices` と差し替えの理由。

- [ ] **Step 2: 手順書の中のコマンドを手元で通す**

Task 2 のテストの見本を `WORK/day.json`・`WORK/pick.json`・`WORK/notes.json` に置き、フェーズ0の `resolve` コマンドと、ダミーの rows でフェーズ7の manifest コマンドを、手順書から貼ってそのまま実行する。
Expected: `resolve` が `{"mode": "user", ...}`、manifest が `{"for_date": ..., ...}` を出す。`grep -nE '19:(15|25|30)|1915|17:45|18:(00|10)' docs/manga/evening-task-prompt.md docs/manga/briefing-manga.md` が何も出さない。終わったら `WORK/` の見本は消す。

- [ ] **Step 3: 全テスト**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS（manga_pipeline・note_pipeline とも）

- [ ] **Step 4: コミット**

```bash
git add docs/manga/evening-task-prompt.md docs/manga/briefing-manga.md
git commit -m "docs(manga): 夕方制作を20:05にし、ユーザーのネタ選択を読む"
```

---

### Task 7: 本番への切り替え（ユーザーの承認が要る）

**Files:** なし（GitHub の PR と claude.ai の定期タスク）

**Interfaces:**
- Consumes: Task 1〜6 のすべて、`<MANGA_PICKER_URL>`
- Produces: 定期タスク「朝マンガ ネタ候補（平日13:55）」、時刻を変えた「朝マンガ 夕方制作（平日20:05）」

切り替えは**平日の 22:00 以降か週末**に行う（main に入った手順書と定期タスクの時刻がずれた状態で 17:45 や 20:05 の実行が走らないように）。2026-11-27（金）に計画を作ったので、11/28〜29 に切り替えて 11/30（月）から本番が目安。

- [ ] **Step 1: ユーザーに確かめる**

PR の作成、新しい定期タスクの作成、夕方制作の時刻・名前の変更を、まとめてユーザーに承認してもらう（設計書 §7）。

- [ ] **Step 2: PR を作り、ユーザーにマージしてもらう**

作業ブランチから `main` への PR。本文に「manifest の CLI に `--picked` が必須になるので、手順書と同時に入れる」ことと、テスト結果（`.venv/bin/python -m pytest -q` の最後の行）を書く。

- [ ] **Step 3: 新しい定期タスクを作る**

`create_trigger`：名前「朝マンガ ネタ候補（平日13:55）」、`cron_expression: "CRON_TZ=Asia/Tokyo 55 13 * * 1-5"`、`create_new_session_on_fire: true`、`notifications: {"push": true}`、`initiation: "human_request"`。指示文は「公開リポジトリ ts73103212-lang/Stock-briefing_public を clone し、`docs/manga/candidates-task-prompt.md` を読んで、そのとおりに進める」。続けて `update_trigger` で `model` を sonnet にする（設計書 §3 のユーザー判断）。

- [ ] **Step 4: 夕方制作の定期タスクを変える**

`list_triggers` で「朝マンガ 夕方制作」を探し、`get_trigger` で中身を確かめてから、`update_trigger` で `cron_expression: "CRON_TZ=Asia/Tokyo 5 20 * * 1-5"` と名前「朝マンガ 夕方制作（平日20:05）」に変える（プロンプトとリポジトリの付与は変えない。プロンプトに 17:45 の時刻が書かれていれば、それだけ直す）。

- [ ] **Step 5: 試運転**

`fire_trigger` で候補出しタスクを1回だけ動かし、ページに4件出ること・通知が来ることを確かめる（週末は `is_tse_closed` で止まるので、`fire_trigger` の `text` に「試運転：休場日の判定を飛ばし、作成日を直近の営業日として扱う」と渡す）。終わったら試運転の `days` / `notes` を `delete` する。夕方制作は動かさない（生成枠を使うため。11/30 の本番で確かめる）。

- [ ] **Step 6: ユーザーに報告**

ページの URL、2つの定期タスクの次の実行時刻、11/30（月）の流れ（13:55 候補 → 20:00 締切 → 22:00 までに通知 → 12/1 朝のメール）を伝える。
