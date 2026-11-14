# 朝ブリーフィング：チャート画像の貼り方

朝の GitHub Actions（Fetch_morning_r2.yml）が、スクリーニング通過銘柄の週足/日足チャート（出来高付き）を
`charts/<証券コード>.png` に作り、`charts/manifest.json` に一覧（generated_at と、銘柄ごとの file / last_bar / sha256）を書いている。

## 手順

1. 作業前に `git pull -q origin main` で最新化し、`charts/manifest.json` を読む。
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
