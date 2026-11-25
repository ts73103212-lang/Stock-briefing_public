# 朝ブリーフィング：8コマ漫画の貼り方

前日の夕方に、定期タスク「朝マンガ 夕方制作（平日17:45）」が8コマ漫画（横2コマ×4段の画像4枚）と解説を作り、
非公開の Artifact「朝マンガ納品」`https://claude.ai/artifact/9m4Jxvrm3aj12NaojgBiUW` に置いている。
朝のブリーフィングは、それを**読んで貼るだけ**にする（漫画を作り直したり、文章を書き足したりしない）。
設計書: `docs/superpowers/specs/2026-11-23-morning-manga-design.md` §7.7

## 手順

1. Artifact ツールで manifest を読む。
   `action: "read"`, `url: "https://claude.ai/artifact/9m4Jxvrm3aj12NaojgBiUW"`, `path: "manga/manifest.json"`
   - `for_date` が**今日（JST）でなければ、漫画欄を丸ごと省く**（注記もしない）。前日分の誤掲載を防ぐため。
   - 読めない・Artifact ツールが使えないときも、漫画欄を省く。ブリーフィング自体は通常どおり送る。
2. 画像4枚を読む。
   `action: "read"`, `url: 同上`, `paths: ["manga/row1.jpg", "manga/row2.jpg", "manga/row3.jpg", "manga/row4.jpg"]`
   - 結果に出る保存先の**絶対パス**を控える。
   - 各ファイルの sha256 を `sha256sum <保存先>` で取り、manifest の `rows[].sha256` と一致するか確かめる。
     1枚でも一致しない・読めないときは、漫画欄を省く。
3. 漫画欄は、メール本文の**最下部（STEP 3 の最後の銘柄欄の後ろ、フッターの前）**にまとめて置く。
   銘柄ごとのチャート（各銘柄欄の中）の間には入れない。N は添付リスト内の0始まりの番号で、
   チャートの添付の数がKなら、漫画は att K 〜 att K+3 になる（表示される場所は `<img>` を置いた場所で決まり、番号とは関係ない）。
   ```html
   <div style="font-weight:bold;font-size:16px;margin-top:20px;color:#111111;">🐾 コーギー先生の8コマ相場教室「{title}」</div>
   <img src="cid:attN" alt="8コマ漫画 1段目" width="100%" style="max-width:680px;height:auto;display:block;margin:4px 0">
   <img src="cid:attN+1" alt="8コマ漫画 2段目" width="100%" style="max-width:680px;height:auto;display:block;margin:4px 0">
   <img src="cid:attN+2" alt="8コマ漫画 3段目" width="100%" style="max-width:680px;height:auto;display:block;margin:4px 0">
   <img src="cid:attN+3" alt="8コマ漫画 4段目" width="100%" style="max-width:680px;height:auto;display:block;margin:4px 0">
   <div style="font-weight:bold;margin-top:12px;color:#111111;">📝 解説</div>
   {explanation_html}
   ```
   - `{title}` と `{explanation_html}` は manifest の値をそのまま使う（言い換えない・足さない）。
     解説の末尾の「※投資判断はご自身で。」も消さない。
4. 添付リスト（create_draft の attachments）の**並び順**では、チャートの添付の後ろに row1〜row4 の順で並べる。base64 は書かない。
   （これは添付リストの中の順番のことで、本文での表示位置は手順3のとおり最下部）
   ```json
   {"content": "sha256:<64桁のsha256>:<手順2の保存先の絶対パス>", "filename": "manga_row1.jpg", "mimeType": "image/jpeg", "inline": true}
   ```
5. 添付付きの下書き作成が失敗したら、**まず漫画を外して**（漫画欄の HTML と漫画の添付4つを消して）作り直して送る。
   それでも失敗したら、チャートの手順（`docs/briefing-charts.md` 手順7）どおりチャートも外す。
   漫画を外したことは本文に書かない。ブリーフィング自体は必ず送る。
