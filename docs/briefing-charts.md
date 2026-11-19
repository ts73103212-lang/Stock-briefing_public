# 朝ブリーフィング：チャート画像の貼り方

朝の GitHub Actions（Fetch_morning_r2.yml）が、スクリーニング通過銘柄の週足/日足チャート（出来高付き）を
`charts/<証券コード>.png` に作り、専用ブランチ `charts`（毎朝、履歴1コミットに上書き）へ公開している。`charts/manifest.json` に一覧（generated_at と、銘柄ごとの file / last_bar / sha256）を書いている。

## 手順

1. 作業前に `git pull -q origin main` で最新化し、続けて次でチャートを取得して `charts/manifest.json` を読む。
   ```bash
   rm -rf charts && mkdir charts && git fetch -q origin charts && git archive origin/charts | tar -x -C charts
   ```
   チャートは傾向（週足のトレンド・日足での位置・出来高の増減）を見るためのもの。日付が多少古くても添付して配信する。
   - 早朝は Yahoo の日足に前営業日の足がまだ載っていないことがあるため、Actions が60分足とスクリーニング終値・出来高で
     その日の足を補っている。補った銘柄には manifest に `"patched_bars": ["YYYY-MM-DD"]` が付く。
     `patched_bars` が付いていても通常どおり添付する（始値だけ60分足由来の概算で、傾向の把握には影響しない）。注記も不要。
   - manifest の `last_bar` が直近営業日より古い銘柄も、添付は見送らない。その銘柄のチャート直下に
     「※チャートは MM/DD までの足」と1行添え、分析は JSON の最新値と組み合わせる。
   - チャートの取得（上の git fetch / archive）自体に失敗したときだけ、全銘柄「チャート取得不可」として進める。
   - X投稿ネタなど、同じチャートを使う他のルーティンも同じ扱いにする。
2. STEP 3 で選んだ各銘柄が manifest に載っていれば、その画像を使う。
   載っていない銘柄は画像なしでよい（その銘柄の欄に「チャート取得不可」と1行書く）。
   チャートのために自分でライブラリを入れたり、画像を作り直したりしない。
3. 本文では、各銘柄の「════ [ticker] … ════」見出しの直後（指標の前）に次を置く。
   N は添付リスト内の0始まりの番号。
   ```html
   <img src="cid:attN" alt="[ticker] 週足/日足チャート" width="100%" style="max-width:680px;height:auto;display:block;margin:6px 0;">
   ```
4. 【推奨理由】には、チャートの形（週足のトレンド、日足での位置、出来高の増減）にも1行触れる。
5. 添付（create_draft の attachments）は本文に出てくる順に並べ、各要素を次の形にする。
   base64 は書かない。ファイル参照で渡す。
   ```json
   {"content": "sha256:<64桁のsha256>:<charts/<file> の絶対パス>", "filename": "<file>", "mimeType": "image/png", "inline": true}
   ```
   - 絶対パスは `pwd` で確かめたリポジトリの実際のパスにする（例: `/home/user/Stock-briefing_public/charts/9048.png`）。
   - sha256 は `sha256sum charts/<file>` で実ファイルから取る。
6. その下書きを send_message の draftId で送る。
7. 添付付きの下書き作成が失敗した場合は、img タグと添付を外した本文で作り直して送り、
   本文冒頭に「※本日はチャート添付に失敗」と1行入れる。ブリーフィング自体は必ず送る。
