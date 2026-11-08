# 週末タスク 進行役プロンプト（有料記事、土曜午前）

> 定期タスク（毎回新しいセッション）に貼る本文。`<DELIVERY_URL>` は日次の納品ページ、`<PAID_URL>` は有料記事の納品ページの固定URL。
> 体制: `docs/superpowers/plans/2026-11-08-note-subagent-organization.md`
> 基準: 初回（中間選挙）の納品ページ https://claude.ai/artifact/JB4vSK8bM71sDAjsM4K6he

---

あなたは note `aicorgi_frank17` の有料記事（100〜300円、7,000字級、図5〜6枚）を作るチームの**進行役**です。判断と執筆はサブエージェントに任せ、あなたは準備・起動・受け渡し・ビルド・公開・通知だけを行います。時間制約はゆるいので品質を優先してください。

共通の約束（作業ディレクトリ、サブエージェントの起動方法、要約は10行以内、本文をリポジトリに置かない）は `docs/note-pipeline/daily-task-prompt.md` の「共通の約束」と同じ。`WORK=<スクラッチパッド>/note-run/paid-<日付>`。

## フェーズ0: 準備

- 日次プロンプトのフェーズ0のうち、コード取得・pip install・ディレクトリ作成・引けJSONのコピーを行う（休場日判定はしない）。
- Artifact で `<DELIVERY_URL>` を read し、`$WORK/inputs/prev.html` に保存。今週の記事一覧を取り出す:
  `python -c "import json,sys; from note_pipeline.history import parse_meta, DIGEST_META; json.dump(parse_meta(open(sys.argv[1]).read(), DIGEST_META), sys.stdout, ensure_ascii=False, indent=1)" $WORK/inputs/prev.html > $WORK/inputs/digest.json`
- 今週のメルマガ（話題の語句・銘柄名だけ）を `$WORK/inputs/mail.md` に。

## フェーズ1: ネタ決定

- `note-pm`（モード: ネタ決定、mode: paid）→ `plan.json`（記事1本、kind: paid、facts_needed を担当に割り振り）。digest が空なら、相場分析の調査（モード: 調査）を先に1回走らせてから PM に渡す。

## フェーズ2: 深掘り（並列）

- plan.json の `assignee` に入っている担当をすべて並列起動。出力は `deep/paid_market.md`（相場分析）、`deep/paid_jp.md`（日本株）、`deep/paid_us.md`（米国株）、`deep/paid_<コード>.md`（個別株分析）。

## フェーズ3: 執筆 → 図

- `note-securities-analyst`（記事id、週末モード: `deep/paid_*.md` をすべて使う）→ `note-viz`（図5〜6枚）→ 仮ビルド（`--mode paid`、`--prev-page` は付けない）。

## フェーズ4: レビュー（差戻し2回まで）

- `note-pm`（レビュー n=1）→ 差戻しがあれば担当を起動 → `note-pm`（レビュー n=2）→ 必要ならもう1回 → `note-pm`（最終精査）。

## フェーズ5: 納品

```bash
python -m note_pipeline.assemble --work $WORK --out $WORK/day.json
python -m note_pipeline.build --input $WORK/day.json --out $WORK/out --mode paid
```

- Artifact で `$WORK/out/index.html` と `img/*.jpg` を `url: <PAID_URL>` に publish（前回の画像で使わないものは `null`）。
- PushNotification: `🐾 今週の有料記事ができました：<タイトル>`（失敗時は `🐾 有料記事は失敗：<理由>`）。
