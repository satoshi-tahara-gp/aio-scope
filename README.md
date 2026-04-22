# AIO-Scope

AIO/SEO 現状診断ツール — Goodpatch Market Design Div 向け営業スタートキット

Webベースの診断ウィザードで、営業メンバーがブラウザで新規案件の AIO/SEO 診断を実施し、Excel・PowerPoint の報告書を自動生成できる。

---

## これは何

- RFP受領後2-3日で実施する「AIO/SEO 現状診断」のプロセスを Web アプリ化
- 6領域・100点満点でクライアントサイトを評価
- 競合3-5社とのベンチマーク比較
- 診断結果をワンクリックで Excel / PPT エクスポート
- Goodpatch ドメイン限定 + 共通パスワード認証

もとになった 3点セット（メソッド資料 / Excel / PPT テンプレ）は `../sales_starter_kit/` に格納。本アプリはそれらを統合しチームで使える形にしたもの。

---

## 主な機能

| 機能 | 説明 |
|------|------|
| 🔐 認証 | `@goodpatch.com` ドメインのメールアドレス + 共通パスワード |
| 📝 新規案件作成 | 案件名・クライアント・URL・競合リストを入力 |
| 📂 過去案件一覧 | スコア・ランク一覧で履歴管理 |
| ① AI引用テスト | 15クエリ × 4AI (ChatGPT/Claude/Perplexity/Gemini)。**ワンクリックでAI起動 + 応答ペーストで自動採点** (API不要・完全無料) |
| ② Google SGE | 20キーワードごとの AI Overview 表示状況を記録 (🔎検索ボタン付き) |
| ③ 構造化データ | Schema.org 9項目チェック (Rich Results Test直接起動) |
| ④ E-E-A-T | 7項目の直接採点 |
| ⑤ テクニカルSEO | Core Web Vitals ほか10項目 |
| ⑥ 競合ベンチマーク | 自社スコアと競合平均の差分を15点換算 |
| 📊 ダッシュボード | レーダーチャートで自社 vs 競合平均を可視化 |
| ✍️ 所見・アクション | 強み/弱みの言語化、改善アクション表の作成 |
| 📥 エクスポート | Excel (9シート) / PowerPoint (8スライド) / JSON (バックアップ) |

---

## ローカル起動

```bash
# リポジトリをクローン/ダウンロード
cd aio-scope

# Python仮想環境 (推奨)
python3 -m venv .venv
source .venv/bin/activate

# 依存パッケージのインストール
pip install -r requirements.txt

# アプリ起動
streamlit run app.py
```

ブラウザで `http://localhost:8501` にアクセス。

**ローカル開発用ログイン**:
- メール: `yourname@goodpatch.com`
- パスワード: `goodpatch-aio-2026` (`.streamlit/secrets.toml` に記載)

---

## 本番デプロイ (Streamlit Community Cloud)

詳細は [`docs/DEPLOY.md`](docs/DEPLOY.md) を参照。概要:

1. 田原さん個人の GitHub アカウントを作成
2. このディレクトリを GitHub リポジトリにプッシュ（private 推奨）
3. https://streamlit.io/cloud にアクセス、「New app」から GitHub リポジトリを連携
4. Secrets 設定で `app_password` と `allowed_email_domains` を設定
5. デプロイ完了 → 営業チームに URL を共有

---

## ディレクトリ構成

```
aio-scope/
├── README.md                  # 本ドキュメント
├── requirements.txt           # Python依存パッケージ
├── .gitignore
├── .streamlit/
│   ├── config.toml            # UIテーマ設定
│   ├── secrets.toml           # ローカル秘密情報 (コミット禁止)
│   └── secrets.toml.example   # 秘密情報のテンプレート
├── app.py                     # Streamlit メインアプリ
├── lib/
│   ├── auth.py                # 認証ロジック
│   ├── state.py               # セッション状態管理
│   ├── templates.py           # 領域定義・クエリテンプレート
│   ├── scoring.py             # スコア計算
│   ├── excel_export.py        # Excel生成
│   └── pptx_export.py         # PowerPoint生成
└── docs/
    ├── DEPLOY.md              # デプロイ手順
    └── USAGE.md               # 営業部員向け使い方ガイド
```

---

## データ保存に関する注意 (v1 の制約)

**v1 では診断データをセッション内（ブラウザ）でのみ保持**しています。以下の運用が必要:

- **ブラウザを閉じるとデータが消えます**。必ず「JSONエクスポート」でバックアップしてください
- 再開時は JSON ファイルをアップロードすることで続きから作業可能
- 推奨: 案件ごとに Google Drive の共有フォルダに JSON を保存

**v2 以降の予定**: Google Sheets 連携 or Supabase による自動保存

---

## 更新・メンテナンス

- 領域定義・クエリテンプレは `lib/templates.py` を編集
- 配点ルール・ランク境界は同ファイル内 `RANK_THRESHOLDS` を調整
- 四半期ごとに AIO 環境の変化（新AI / SGE仕様変更）に応じて見直し

---

## 起点となった案件

2026年4月、三井ダイレクト損害保険のWebサイトリニューアル案件で、AIO/SEO テクニカル提案の具体性不足により電通デジタルに失注。その学びから「提案着手前の診断を標準化する」仕組みとして本ツールを構築。

## ライセンス

社内利用限定 (Goodpatch Inc.)
