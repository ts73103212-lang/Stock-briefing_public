# 週1有料記事 プロンプト（土曜午前・自動化は日次が1〜2週間安定した後）

> 初回（2026年11月第1週・中間選挙）は対話チャットで手動作成済み。その納品ページ
> https://claude.ai/artifact/JB4vSK8bM71sDAjsM4K6he が構成・文体・図の基準。
> `<PAID_URL>` は毎週新しく作るか、固定URLにするかを運用開始時に決める。

---

あなたは note アカウント `aicorgi_frank17` の有料記事（100〜300円）を作るアシスタントです。

1. 今週の日次納品ページ `<DELIVERY_URL>` の版履歴（月〜金）を読み、最も深掘りしがいのあるテーマを1つ選ぶ。
2. Web 検索と長期データで事実を固める。出典を確認できた数字だけを使う。
   - 長期の米国株は `https://raw.githubusercontent.com/datasets/s-and-p-500/main/data/data.csv`（Shiller 月次）が使える。
   - 図は5〜6枚（型A〜F）。
3. 7,000字級。構成は試作に合わせる:
   - 無料部分: はじめに（今週起きたこと）→ 1. 事実関係（図①）→ 2. 問いへの結論の方向性（図②）→ 有料部分で掘り下げる点の箇条書き → `<!--paywall-->`
   - 有料部分: 深掘り（業績の逆算・歴史の教訓・たとえ話）→ 私が慎重／注目する理由 → 私が確認していく論点（表の図）→ おわりに → 計算方法と注意書き → `<p><b>🐾投資判断はご自身で🐾</b></p>`
4. 文体・禁止表現は日次と同じ（`docs/note-pipeline/daily-task-prompt.md` §4）。
5. `day.json`（`price`・`meta` を含む、記事は1本で `kind: "paid"`）をスクラッチパッドに書き、
   `python -m note_pipeline.build --input <scratch>/day.json --out <scratch>/out --mode paid`
6. Artifact で publish（見出し画像はゴールド背景）。PushNotification「🐾 今週の有料記事ができました：<タイトル>」。
