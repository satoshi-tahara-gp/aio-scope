"""診断の各領域で使うテンプレート・定義"""

# =====================================================================
# 領域メタデータ: 名前・満点・説明
# =====================================================================
AREAS = {
    "ai_quote": {"num": 1, "name": "AI引用露出度", "max_points": 20,
                 "color": "#6366F1", "desc": "生成AIチャットでの引用状況"},
    "sge": {"num": 2, "name": "Google SGE / AI Overview", "max_points": 15,
            "color": "#06B6D4", "desc": "Google検索AI Overviewでの露出"},
    "schema": {"num": 3, "name": "構造化データ", "max_points": 20,
               "color": "#7C3AED", "desc": "Schema.org実装状況"},
    "eeat": {"num": 4, "name": "E-E-A-T", "max_points": 15,
             "color": "#10B981", "desc": "Experience/Expertise/Authority/Trust"},
    "tech_seo": {"num": 5, "name": "テクニカルSEO", "max_points": 15,
                 "color": "#F59E0B", "desc": "Core Web Vitals / Crawl基盤"},
    "competitor": {"num": 6, "name": "競合ベンチマーク", "max_points": 15,
                   "color": "#EF4444", "desc": "競合3-5社との差分"},
}

AREA_ORDER = ["ai_quote", "sge", "schema", "eeat", "tech_seo", "competitor"]

# =====================================================================
# 領域1: AI引用 - クエリテンプレート (8個、業界別にカスタマイズ可)
# 15から8に削減: 各観点(ブランド/カテゴリ/比較/課題/長尾)を最小構成でカバー
# =====================================================================
AI_QUERY_TEMPLATES = [
    ("ブランド", "{企業名} の特徴・強みは？"),
    ("ブランド", "{企業名} の評判・デメリット"),
    ("カテゴリ", "{業界} おすすめ比較"),
    ("カテゴリ", "{業界} ランキング TOP5"),
    ("比較", "{競合A} と {企業名} の違い"),
    ("課題", "{業界} 選び方のポイント"),
    ("長尾", "{業界} 初心者向け"),
    ("長尾", "{業界} 料金相場"),
]

# v1.2: 自動URL入力対応の2AI (ChatGPT/Perplexity) のみで運用。Claude/Gemini は手動ペーストが必要なため除外
AI_SERVICES = ["ChatGPT", "Perplexity"]

# =====================================================================
# 領域3: 構造化データ - 9項目
# =====================================================================
SCHEMA_ITEMS = [
    ("Schema.org Organization", 2),
    ("Schema.org Product / Service", 3),
    ("Schema.org FAQ", 3),
    ("Schema.org HowTo", 2),
    ("Schema.org Article / BreadcrumbList", 2),
    ("Schema.org Review", 2),
    ("OGP / Twitter Cards", 2),
    ("JSON-LD実装 (Microdataではなく)", 2),
    ("バリデーション通過 (エラーなし)", 2),
]

# =====================================================================
# 領域4: E-E-A-T - 7項目
# =====================================================================
EEAT_ITEMS = [
    ("著者情報の明示 (著者ページ・プロフィール)", 2),
    ("執筆者・監修者の専門性表記", 3),
    ("企業・組織情報 (About us / 会社概要)", 2),
    ("更新日時の明示", 2),
    ("引用・参考文献の記載", 2),
    ("問い合わせ先・所在地の明示", 2),
    ("第三者評価 (受賞・メディア掲載)", 2),
]

# =====================================================================
# 領域5: テクニカルSEO - 10項目
# =====================================================================
TECH_SEO_ITEMS = [
    ("Core Web Vitals (LCP/FID/CLS) 全緑", 3),
    ("モバイルフレンドリー", 1),
    ("robots.txt / XML sitemap 適切", 2),
    ("canonical タグ適切", 1),
    ("内部リンク構造 / パンくず", 2),
    ("URL構造 (階層・可読性)", 1),
    ("HTTPS / セキュリティヘッダー", 1),
    ("PageSpeed Insights スコア", 2),
    ("404エラー・リダイレクトチェーン", 1),
    ("Crawl Budget (大規模サイトのみ)", 1),
]

# =====================================================================
# 領域2: SGE - デフォルトキーワード数
# =====================================================================
SGE_KEYWORDS_COUNT = 20

# =====================================================================
# ランク境界
# =====================================================================
RANK_THRESHOLDS = [
    (85, "S", "業界トップクラス", "#10B981"),
    (70, "A", "良好", "#22C55E"),
    (50, "B", "一般的", "#F59E0B"),
    (30, "C", "要改善", "#F97316"),
    (0, "D", "リニューアル必須", "#EF4444"),
]


def rank_from_score(score: float):
    """総合スコアからランク・説明・色を返す"""
    for threshold, rank, desc, color in RANK_THRESHOLDS:
        if score >= threshold:
            return rank, desc, color
    return "D", "リニューアル必須", "#EF4444"


# =====================================================================
# AI サービスへのクエリ起動URL (query param対応のもののみ直接渡す)
# =====================================================================
from urllib.parse import quote_plus


def ai_launch_url(service: str, query: str) -> str:
    """各AIサービスでクエリを実行するためのURL。
    対応していないサービスはトップページに飛ばす (ユーザーは手動でペースト)。
    """
    q = quote_plus(query or "")
    urls = {
        "ChatGPT":    f"https://chatgpt.com/?q={q}",
        "Claude":     "https://claude.ai/new",  # query paramをサポートしていない
        "Perplexity": f"https://www.perplexity.ai/search?q={q}",
        "Gemini":     "https://gemini.google.com/app",  # 直接パラメータは不安定
    }
    return urls.get(service, "https://www.google.com/search?q=" + q)


def google_search_url(keyword: str) -> str:
    """Google検索 (AI Overview確認用)"""
    return f"https://www.google.com/search?q={quote_plus(keyword or '')}"


# =====================================================================
# 外部診断ツール URL
# =====================================================================
def rich_results_test_url(url: str = "") -> str:
    """Google Rich Results Test"""
    if url:
        return f"https://search.google.com/test/rich-results?url={quote_plus(url)}"
    return "https://search.google.com/test/rich-results"


def pagespeed_url(url: str = "") -> str:
    """PageSpeed Insights"""
    if url:
        return f"https://pagespeed.web.dev/analysis?url={quote_plus(url)}"
    return "https://pagespeed.web.dev/"


def schema_validator_url() -> str:
    """Schema Markup Validator"""
    return "https://validator.schema.org/"


def wayback_url(url: str = "") -> str:
    """Wayback Machine (更新履歴確認)"""
    if url:
        return f"https://web.archive.org/web/*/{url}"
    return "https://web.archive.org/"
