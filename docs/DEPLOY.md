# デプロイガイド — Streamlit Community Cloud

AIO-Scope を Streamlit Community Cloud に無料デプロイする手順。所要時間 約30分（GitHub初回設定含む）。

---

## Step 0. 事前準備

必要なアカウント:

- **GitHub** (個人アカウント無料) — コードホスト
- **Streamlit Community Cloud** (GitHubログイン) — デプロイ先

## Step 1. GitHub アカウント作成 + セットアップ

### 1-1. GitHub アカウントを作成

[github.com](https://github.com/signup) にアクセスし、田原さん個人のメールで無料アカウントを作成。

推奨ユーザー名: `satoshi-tahara-gp` や `tahara-goodpatch` など、業務用途と分かる名前。

### 1-2. GitHub CLI をインストール (Mac)

ターミナルで:

```bash
# Homebrew 経由 (要 Homebrew インストール)
brew install gh

# または公式インストーラー
# https://cli.github.com/ からダウンロード
```

Homebrewが未導入なら以下で最短導入:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 1-3. GitHub にログイン (CLI)

```bash
gh auth login
```

対話形式で:
1. `GitHub.com` を選択
2. `HTTPS` を選択
3. `Y` (Yes to credential caching)
4. `Login with a web browser` を選択
5. 表示される one-time code をコピー、ブラウザでペースト
6. GitHubで許可 → 完了

### 1-4. git ユーザー情報を設定

```bash
git config --global user.name "田原諭"
git config --global user.email "あなたのメール@goodpatch.com"
```

---

## Step 2. リポジトリを GitHub にプッシュ

```bash
cd /Users/lease-emp-mac-satoshi-tahara/Desktop/Cloudecode_test_file/aio-scope

# Git初期化
git init
git add .
git commit -m "Initial commit: AIO-Scope v1"

# GitHub リポジトリを作成 + push (private推奨)
gh repo create aio-scope --private --source=. --push
```

これで `https://github.com/<ユーザー名>/aio-scope` にコードが上がります。

### ⚠️ 重要: 機密情報の確認

`.gitignore` で `.streamlit/secrets.toml` は除外されているが、**念のため push 前に確認**:

```bash
git status
```

`secrets.toml` が表示されたら、コミット前に除外:

```bash
git rm --cached .streamlit/secrets.toml
git commit -m "Remove secrets from tracking"
```

---

## Step 3. Streamlit Community Cloud でデプロイ

### 3-1. アカウント作成

[share.streamlit.io](https://share.streamlit.io/) にアクセス、「Continue with GitHub」でログイン。初回は GitHub の権限付与画面で許可。

### 3-2. New app

右上「New app」をクリック:

- **Repository**: `<ユーザー名>/aio-scope`
- **Branch**: `main`
- **Main file path**: `app.py`
- **App URL** (任意): `goodpatch-aio-scope` など覚えやすいサブドメイン

### 3-3. Advanced settings → Secrets

「Advanced settings」を展開し、Secrets に以下をペースト:

```toml
app_password = "本番用のパスワード (半角英数記号で20文字以上推奨)"
allowed_email_domains = ["goodpatch.com", "anywhere.goodpatch.com"]
```

### 3-4. Deploy

「Deploy!」ボタンを押すと、初回ビルドが始まります (3-5分)。完了すると `https://goodpatch-aio-scope.streamlit.app` のような URL が発行されます。

---

## Step 4. アクセス制限の強化 (オプション)

### A. App は private にする

Streamlit Cloud の「Settings → Sharing」で「Only specific users」を選択し、営業チームメンバーの GitHub アカウント or メールを追加。

この設定だと **GitHub ログインが必須** になるため、アプリ内の password 認証と合わせて2段階の保護になる。

### B. 営業チームに URL + パスワード を共有

営業メンバー向けの案内テンプレート:

```text
件名: AIO-Scope (AIO/SEO診断ツール) のご案内

Market Design Divの皆様

UI/UX提案と並走できるAIO/SEO診断ツールを立ち上げました。
RFP受領後、提案着手前に実施して、テクニカル面の根拠をクライアントに提示するのが目的です。

URL: https://goodpatch-aio-scope.streamlit.app
パスワード: [別途Slack DMでお知らせします]
ログインは @goodpatch.com のメールアドレスが必要です。

使い方マニュアル: ./USAGE.md をご参照ください。
不明点は #aio-scope チャンネルまたは田原まで。
```

---

## Step 5. 更新・運用

### コード修正を反映

```bash
cd aio-scope
# 修正...
git add .
git commit -m "修正内容"
git push
```

Streamlit Cloud は push を検知して自動デプロイ (1-2分)。

### パスワード更新

Streamlit Cloud の「Settings → Secrets」で `app_password` を書き換えて save。即時反映。

### 営業メンバーの追加・削除

- B の「private共有」設定の場合: Streamlit Cloud の「Settings → Sharing」でメール追加
- 全員共有（password保護のみ）の場合: 操作不要 (ドメインが合えば誰でもログイン可)

---

## トラブルシューティング

### ❌ 「Error: command not found: gh」
→ Step 1-2 の GitHub CLI インストールが未完了。`brew install gh` を実行

### ❌ Streamlit Cloud のビルドで依存エラー
→ `requirements.txt` の Python バージョン不整合の可能性。Streamlit Cloud の「Settings → Advanced → Python version」で 3.11 か 3.12 を指定

### ❌ ログインできない
→ secrets.toml の `allowed_email_domains` を確認。デフォルトは `goodpatch.com` と `anywhere.goodpatch.com`

### ❌ PPT / Excel がダウンロードできない
→ メモリ不足の可能性。Streamlit Cloud 無料枠は 1GB RAM。大規模案件でパフォーマンス問題が出たら有料プランか Docker 自前ホストを検討

---

## v2 以降の展望

- Google Sheets 連携 (gspread) でチーム共有の案件データベース化
- Google OAuth 統合で ドメイン制限をより厳密に
- AI Overview トラッキングの自動化 (SerpAPI など)
- 過去案件データからの学習・ベンチマーク化
