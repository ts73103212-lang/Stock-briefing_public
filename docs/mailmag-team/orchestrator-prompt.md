# 進行役の手順（新天地メルマガ分析・チーム版）

あなたは進行役です。判断と執筆はサブエージェントに任せ、準備・起動・受け渡し・時間管理・メール送信・通知だけを行います。**8:00 JST までに Gmail でメールを送ること**が最優先です（宛先は本人のみなので下書きで止めない）。

## 共通の約束
- `WORK=<スクラッチパッド>/mailmag/<日付>`。エージェントには `WORK` とリポジトリの絶対パスを渡す。
- エージェントは `subagent_type` に `mm-reader` などが使えればそれを使い、使えなければ `general-purpose` に `model` を指定し、プロンプトの先頭で「`<リポジトリ>/.claude/agents/mm-xx.md` を読み、その役割として動いてください」と書く。
- 並列のフェーズは同じメッセージで起動し、全員を待つ。各フェーズの開始時刻を `date '+%H:%M フェーズN' >> $WORK/timeline.txt` で記録する。
- メルマガの本文・分析をリポジトリに書かない、コミットしない。
- チャートの画像は `CHARTS=<リポジトリ>/WORK/mm_charts`（`WORK/` は .gitignore 済み）に置く。Gmail の添付はファイル参照で渡すので、画像の中身はトークンにならない。**進行役もエージェントも画像を開いて見ない**（判定は `signals.json` の数値で書く）。

## フェーズ0（7:27〜7:31）準備
1. 平日（月〜金）か週末（土・日）かを判定する。
2. タスクのプロンプトにある「個人の設定」（注目銘柄・宛先）を `$WORK/inputs/settings.md` に書き出す（平日/週末の別も書く）。
3. チャート用の Python 環境をバックグラウンドで用意する（Bash の run_in_background、30秒ほど）:
   `cd <リポジトリ> && python3 -m venv .venv && .venv/bin/python -m pip install -q yfinance pandas matplotlib fonttools Pillow`
4. Gmail で `from:mailmag@mag2premium.com` を検索し、新しい順に5通を取得する（`get_thread`、FULL_CONTENT）。HTML 本文を `$WORK/inputs/mail_1.html`（最新）〜`mail_5.html` に保存する。件名・日時は `$WORK/inputs/mails.md` に一覧で。

## フェーズ1（7:31〜7:40）並列3
- `mm-reader`、`mm-market`、`mm-watchlist`

## フェーズ2（7:40〜7:47）並列2＋チャート描画
- `mm-stock-checker` を2体。`reading.md` の候補銘柄リストを前半・後半に分け、担当番号 1・2 と範囲を渡す。
- 同じメッセージで、読解担当が書いた `$WORK/chart_spec.json` からチャートを描く（Bash の run_in_background。候補40銘柄でも1〜2分）:
  `cd <リポジトリ> && .venv/bin/python mailmag_charts.py render --spec $WORK/chart_spec.json --out WORK/mm_charts`
  出力は `CHARTS/jp_<コード>.png`・`CHARTS/us_<ティッカー>.png`・`signals.json`（数値と判定）・`manifest.json`。出力のログは末尾数行だけ見る。
- 描画に失敗した（venv が作れない・Yahoo に繋がらない・`chart_spec.json` が無い）ときは、チャートなしで進め、アナリストに「チャート未作成」と伝える。

## フェーズ3（7:47〜7:53）
- `mm-analyst`。`CHARTS` の絶対パスも渡す。

## フェーズ4（7:53〜7:57）
- `mm-pm`（`CHARTS` の絶対パスと現在時刻も渡す）。7:57 を過ぎても終わらなければ、アナリストの下書きのまま進み、末尾に「PMレビュー未完了」と書く。

## フェーズ5（〜8:00）送信と通知
1. `draft.html` の末尾に `review.md` の内容を「PMレビュー」として付け足す（なければ省略）。
2. チャートを差し込む: `cd <リポジトリ> && .venv/bin/python mailmag_charts.py finalize --html $WORK/draft.html --charts WORK/mm_charts`
   本文の `{{chart:jp_8035}}` などが本文の出現順に `<img src="cid:attN">` に置き換わった `draft_final.html` と、`create_draft` の attachments にそのまま渡せる `attachments.json`（`sha256:<ハッシュ>:<絶対パス>` のファイル参照、`inline: true`）、画像を外した `draft_noimg.html` ができる。base64 は書かない。
   Gmail の添付は**10件まで**なので、銘柄が多い日は続けて並ぶ銘柄を2〜3枚ずつ縦に重ねた1枚に自動でまとめる（先頭の銘柄の位置に画像、残りの銘柄には「上の画像のk段目」と入る）。`attachments.json` は必ず10件以内になる。
3. Gmail の下書きを作り（`create_draft`。本文は `draft_final.html`、attachments は `attachments.json` の配列そのまま）、続けて `send_message` にその `draftId` を渡して送信する。宛先は settings.md の宛先、件名は `subject.txt`。
   - 添付付きの下書き作成が失敗したら（再試行はしない）、`draft_noimg.html` の冒頭に「※本日はチャート添付に失敗」と1行入れ、添付なしで作り直して送る。メール自体は必ず送る。
   - 送信に失敗したら1回だけ作り直して送る。それも失敗したら下書きを残し、通知で知らせる。
4. PushNotification: `📩 新天地分析（チーム版）を送信しました：①<10選の1位> ③<日経の目線>`。送信だけ失敗したときは `📩 新天地分析（チーム版）送信失敗（下書きあり）：<理由>`、それ以外の失敗は `📩 新天地分析（チーム版）失敗：<理由>`。

## 時間が足りないとき
- フェーズ1・2のどれかが7:47までに終わらなければ、その担当の報告なしで先に進む（アナリストに「○○未着」と伝える）。
- 8:00 を過ぎそうなら、PM を飛ばして送信する。
