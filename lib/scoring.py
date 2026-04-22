"""診断データからスコアを算出する純粋関数群"""
from .templates import AI_QUERY_TEMPLATES, AI_SERVICES, SCHEMA_ITEMS, EEAT_ITEMS, TECH_SEO_ITEMS, SGE_KEYWORDS_COUNT


# =====================================================================
# 領域1: AI引用 (20点満点)
# =====================================================================
# 各クエリ x 各AI で 引用(0-1) + 位置(0-3) + 正確性(0-3) = 最大7点
# 15クエリ x 4AI x 7 = 420点 → 20点換算
def score_ai_quote(data: dict) -> float:
    """v1.3: 位置スコアのみで算出 (先頭=3/中=2/末=1/なし=0)。
    引用/正確性は位置から自動的に決まるため不要。
    """
    if not data:
        return 0.0
    rows = data.get("rows", [])
    total = 0
    max_total = len(rows) * len(AI_SERVICES) * 3
    for row in rows:
        for ai in AI_SERVICES:
            scores = row.get(ai, {})
            pos = min(3, max(0, int(scores.get("position", 0) or 0)))
            total += pos
    if max_total == 0:
        return 0.0
    return round(total / max_total * 20, 1)


# =====================================================================
# 領域2: SGE (15点満点)
# =====================================================================
# 20キーワード x 3指標 (表示/引用/リンク) = 60点 → 15点換算
def score_sge(data: dict) -> float:
    if not data:
        return 0.0
    total = 0
    max_total = SGE_KEYWORDS_COUNT * 3
    for row in data.get("rows", []):
        total += (1 if row.get("overview") else 0)
        total += (1 if row.get("cite") else 0)
        total += (1 if row.get("link") else 0)
    if max_total == 0:
        return 0.0
    return round(total / max_total * 15, 1)


# =====================================================================
# 領域3: 構造化データ (20点満点)
# =====================================================================
# 各項目: 配点 × 実装状況(0=なし / 1=部分 / 2=完全) / 2
def score_schema(data: dict) -> float:
    if not data:
        return 0.0
    total = 0.0
    for i, (name, pt) in enumerate(SCHEMA_ITEMS):
        impl = data.get("items", {}).get(str(i), 0)
        impl = min(2, max(0, int(impl or 0)))
        total += pt * impl / 2
    return round(total, 1)


# =====================================================================
# 領域4: E-E-A-T (15点満点)
# =====================================================================
# 各項目: 0〜配点 の直接入力
def score_eeat(data: dict) -> float:
    if not data:
        return 0.0
    total = 0.0
    for i, (name, pt) in enumerate(EEAT_ITEMS):
        s = data.get("items", {}).get(str(i), 0)
        s = min(pt, max(0, float(s or 0)))
        total += s
    return round(total, 1)


# =====================================================================
# 領域5: テクニカルSEO (15点満点)
# =====================================================================
def score_tech_seo(data: dict) -> float:
    if not data:
        return 0.0
    total = 0.0
    for i, (name, pt) in enumerate(TECH_SEO_ITEMS):
        s = data.get("items", {}).get(str(i), 0)
        s = min(pt, max(0, float(s or 0)))
        total += s
    return round(total, 1)


# =====================================================================
# 領域6: 競合ベンチマーク (15点満点)
# =====================================================================
# 自社合計 vs 競合平均合計 を -7.5〜+7.5 にマップし、7.5 + diff で 0〜15 に収める
def score_competitor(data: dict, self_totals: dict) -> float:
    """
    data: {"competitors": [{"name": "...", "scores": [a1, a2, a3, a4, a5]}]}
    self_totals: {"ai_quote": X, "sge": Y, ...} (5領域のみ使用)
    """
    if not data:
        return 7.5
    comps = data.get("competitors", [])
    valid = [c for c in comps if c.get("scores") and sum(float(s or 0) for s in c["scores"]) > 0]
    if not valid:
        return 7.5  # 競合データなし → 中央値
    comp_totals = [sum(float(s or 0) for s in c["scores"]) for c in valid]
    comp_avg = sum(comp_totals) / len(comp_totals)
    self_sum = (
        self_totals.get("ai_quote", 0)
        + self_totals.get("sge", 0)
        + self_totals.get("schema", 0)
        + self_totals.get("eeat", 0)
        + self_totals.get("tech_seo", 0)
    )
    diff_ratio = (self_sum - comp_avg) / 85  # -1.0 to +1.0
    score = 7.5 + diff_ratio * 7.5
    return round(max(0, min(15, score)), 1)


# =====================================================================
# 総合スコア
# =====================================================================
def score_all(project: dict) -> dict:
    """プロジェクト全データから全領域スコアと総合を算出"""
    diag = project.get("diagnosis", {})
    s1 = score_ai_quote(diag.get("ai_quote", {}))
    s2 = score_sge(diag.get("sge", {}))
    s3 = score_schema(diag.get("schema", {}))
    s4 = score_eeat(diag.get("eeat", {}))
    s5 = score_tech_seo(diag.get("tech_seo", {}))
    s6 = score_competitor(
        diag.get("competitor", {}),
        {"ai_quote": s1, "sge": s2, "schema": s3, "eeat": s4, "tech_seo": s5},
    )
    total = round(s1 + s2 + s3 + s4 + s5 + s6, 1)
    return {
        "ai_quote": s1,
        "sge": s2,
        "schema": s3,
        "eeat": s4,
        "tech_seo": s5,
        "competitor": s6,
        "total": total,
    }
