# 朝マンガ：ユーザー作業の手順書

朝ブリーフィングの8コマ漫画は、GitHub Actions（`manga_render.yml`）の上で Codex CLI が絵を描く。
Codex は ChatGPT のログイン情報（`auth.json`）で動くため、最初に一度だけ、次の2つを GitHub に登録する。

| Secrets の名前 | 中身 | 用途 |
|---|---|---|
| `CODEX_AUTH_JSON` | PC の `~/.codex/auth.json` を base64 にした文字列 | Actions 上の Codex のログイン |
| `SECRETS_PAT` | 「Secrets の書き込みだけ」を許可したトークン（fine-grained PAT） | Codex が更新したログイン情報を、Actions が自分で Secrets に保存し直すため |

> ⚠️ どちらも**パスワードと同じ扱い**。チャット・メール・メモ帳などに貼らない。
> コピーしたら、すぐに GitHub の画面に貼り付ける。

作業は全部で 4 つ。上から順に進める。所要時間は 15 分ほど。

---

## 1. auth.json を用意する

### 1-1. PC の Codex でログインしておく

PC で Codex を使ってログイン済みなら、そのままでよい。
まだなら、PowerShell（Mac はターミナル）で次を実行し、ブラウザで ChatGPT にログインする。

```
codex login
```

### 1-2. auth.json があるか確かめる

- Windows：エクスプローラーのアドレス欄に `%USERPROFILE%\.codex` と入れて開き、`auth.json` があるか見る。
- Mac／Linux：ターミナルで `ls ~/.codex/auth.json`

> `auth.json` が無い場合：ログイン情報が OS のキーチェーンに保存されている。
> `~/.codex/config.toml`（Windows は `%USERPROFILE%\.codex\config.toml`）に
> 次の1行を足して保存し、`codex login` をやり直すと `auth.json` ができる。
> ```
> cli_auth_credentials_store = "file"
> ```

### 1-3. base64 にしてクリップボードに入れる

- **Windows（PowerShell）**：次を実行すると、結果がクリップボードに入る（画面には出ない）。
  ```
  [Convert]::ToBase64String([IO.File]::ReadAllBytes("$HOME\.codex\auth.json")) | Set-Clipboard
  ```
- **Mac**：
  ```
  base64 -i ~/.codex/auth.json | pbcopy
  ```
- **Linux**：
  ```
  base64 -w0 ~/.codex/auth.json
  ```
  （出てきた1行の長い文字列をコピーする）

コピーしたら、そのまま「3. Secrets に登録する」の `CODEX_AUTH_JSON` に貼る。

---

## 2. トークン（fine-grained PAT）を作る

GitHub の画面で、1手ずつ次のとおり押す。

1. GitHub にログインし、**右上の自分のアイコン**を押す。
2. メニューの下の方にある **Settings** を押す。
3. 左のメニューの**一番下**にある **Developer settings** を押す。
4. 左のメニューの **Personal access tokens** を押して開き、その下の **Fine-grained tokens** を押す。
5. 右上の **Generate new token** を押す（パスワードや2段階認証を聞かれたら入れる）。
6. 次のとおり入力する。
   - **Token name**：`manga-secrets`（何でもよい）
   - **Description**：`朝マンガ：Codex ログイン情報の書き戻し用`（空でもよい）
   - **Resource owner**：自分のアカウントのまま
   - **Expiration**：**Custom** を選び、今日から**1年後の日付**を選ぶ（選べる最長でよい）
7. **Repository access** で **Only select repositories** を選び、
   出てきた **Select repositories** の欄から **`Stock-briefing_public`** を1つだけ選ぶ。
8. **Permissions** の欄で、リポジトリの権限を1つだけ足す。
   - 画面に **Add permissions** ボタンがある場合：押して、一覧から **Secrets** にチェックを入れ、
     その行の右側の Access を **Read and write** にする。
   - 画面に **Repository permissions** という折りたたみがある場合：開いて、**Secrets** の行を探し、
     右側の **Access: No access** を **Read and write** に変える。
   - ほかの項目（Contents、Actions など）は触らない。
     **Metadata: Read-only** は自動で付くので、そのままでよい。
9. 一番下の **Generate token** を押す（確認画面が出たら、もう一度 **Generate token**）。
10. `github_pat_` で始まる文字列が1回だけ表示される。右のコピーボタンでコピーし、
    そのまま「3. Secrets に登録する」の `SECRETS_PAT` に貼る。
    （この画面を閉じると二度と表示されない。閉じてしまったら、そのトークンを Delete して作り直す）

---

## 3. Secrets に登録する

2つとも、同じ画面で登録する。

1. リポジトリ **`Stock-briefing_public`** のページを開く。
2. 上のタブの一番右の **Settings** を押す（歯車のマーク）。
3. 左のメニューの **Secrets and variables** を押して開き、その下の **Actions** を押す。
4. **Secrets** タブのまま、緑の **New repository secret** を押す。
5. 1つ目を登録する。
   - **Name**：`CODEX_AUTH_JSON`
   - **Secret**：1-3 でコピーした base64 の文字列を貼る
   - **Add secret** を押す
6. もう一度 **New repository secret** を押し、2つ目を登録する。
   - **Name**：`SECRETS_PAT`
   - **Secret**：2 でコピーした `github_pat_…` を貼る
   - **Add secret** を押す
7. 一覧に `CODEX_AUTH_JSON` と `SECRETS_PAT` の2つが並べば完了。

---

## 4. PC のログインを分ける（大事）

Actions に渡した `auth.json` を、**PC 側で使い続けない**。
同じログイン情報を2か所で使うと、片方がトークンを更新したときに、もう片方がログインできなくなる。

1. **`codex logout` は使わない**（ログイン情報そのものを無効にして、Actions 側まで使えなくなるおそれがある）。
   代わりに、PC の `auth.json` ファイルを**削除**する。
   - Windows：`%USERPROFILE%\.codex` フォルダを開き、`auth.json` を削除する。
   - Mac／Linux：`rm ~/.codex/auth.json`
2. PC で `codex login` をやり直す。これで PC は Actions とは別のログイン状態になる。

ここまで済んだら、Claude に「Secrets 登録したよ」と伝える。

---

## 「Codex の再ログインが必要」と通知が来たとき

夕方の通知が「🐾 漫画は本日見送り：Codex の再ログインが必要（docs/manga/README.md）」だった場合は、
Actions 側のログイン情報が切れている（または、更新後の保存に失敗した）。次の順でやり直す。

1. 「1. auth.json を用意する」をやり直す（PC で新しくログインして、base64 をコピーする）。
2. 「3. Secrets に登録する」の画面で、`CODEX_AUTH_JSON` の右の**鉛筆マーク（Update）**を押し、
   新しい文字列を貼って **Update secret** を押す。
3. 「4. PC のログインを分ける」をやり直す。

`SECRETS_PAT` は、期限（1年）が切れるまでそのままでよい。
期限が近づくと GitHub からメールが来るので、そのときは「2. トークンを作る」をやり直し、
`SECRETS_PAT` を Update する。
