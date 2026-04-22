"""AI応答テキストから自動採点するロジック (APIを使わない、ローカル実装)

スコアリング基準:
- 引用 (0/1): クライアント名がテキストに登場するか
- 位置 (0-3): テキスト内での相対位置
    3 = 先頭 (全文の0-25%位置)
    2 = 中盤 (25-75%位置)
    1 = 末尾 (75-100%位置)
    0 = 登場せず
- 正確性 (0-3): 簡易ヒューリスティックで提案、ユーザーが最終確認
"""
import re


def _normalize(s: str) -> str:
    """比較用の正規化 (大文字小文字・全角半角・スペース差を吸収)"""
    if not s:
        return ""
    s = s.strip().lower()
    # 一般的な法人表記を除去してマッチ精度を上げる
    for suffix in ["株式会社", "(株)", "㈱", "co., ltd.", "co.,ltd.",
                   "corporation", "corp.", "inc.", "ltd.", "kk"]:
        s = s.replace(suffix, "")
    # 連続空白を1つに
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _find_brand_position(text: str, brand: str) -> tuple[int, int, int]:
    """テキスト内でブランド名が最初に登場する位置を返す。
    Returns: (found_count, first_index, text_length)
    """
    if not text or not brand:
        return (0, -1, len(text) if text else 0)
    n_text = _normalize(text)
    n_brand = _normalize(brand)
    if not n_brand:
        return (0, -1, len(text))
    # ブランド名を分解 (漢字部分 + カナ部分)
    candidates = {n_brand}
    # "三井ダイレクト損害保険" → "三井ダイレクト" なども拾う
    for stopword in ["損害保険", "保険", "銀行", "証券", "ホールディングス"]:
        if stopword in n_brand:
            candidates.add(n_brand.replace(stopword, "").strip())
    count = 0
    first = -1
    for cand in candidates:
        if not cand:
            continue
        idx = n_text.find(cand)
        while idx != -1:
            count += 1
            if first == -1 or idx < first:
                first = idx
            idx = n_text.find(cand, idx + 1)
    return (count, first, len(n_text))


def position_score(first_index: int, total_len: int) -> int:
    """出現位置から 0-3 を返す"""
    if first_index < 0 or total_len == 0:
        return 0
    ratio = first_index / total_len
    if ratio < 0.25:
        return 3  # 先頭
    if ratio < 0.75:
        return 2  # 中盤
    return 1  # 末尾


def accuracy_heuristic(text: str, brand: str, count: int) -> int:
    """簡易な正確性ヒューリスティック。ユーザー側で確認・調整される前提"""
    if count == 0:
        return 0
    # 複数回登場 + 具体的な特徴記述があれば高スコア寄り
    n_text = text.lower() if text else ""
    feature_markers = [
        "特徴", "強み", "メリット", "弱み", "デメリット", "料金", "保険料",
        "サービス", "対応", "サポート", "割引", "割安", "商品", "評判",
        "満足度", "ランキング", "評価",
    ]
    hits = sum(1 for m in feature_markers if m in n_text)
    # 3回以上言及 + 特徴マーカー複数 → 3
    if count >= 3 and hits >= 3:
        return 3
    if count >= 2 and hits >= 2:
        return 2
    if count >= 1:
        return 1
    return 0


def analyze_response(text: str, brand: str) -> dict:
    """AI応答テキストを分析してスコア提案を返す

    Returns dict:
        cite: 0 or 1
        position: 0-3
        accuracy: 0-3 (ヒューリスティックの提案値)
        count: 登場回数
        snippet: 最初にブランドが登場する前後50文字のスニペット
    """
    count, first, total = _find_brand_position(text, brand)
    cite = 1 if count > 0 else 0
    pos = position_score(first, total) if count > 0 else 0
    acc = accuracy_heuristic(text, brand, count)

    snippet = ""
    if first >= 0 and text:
        start = max(0, first - 40)
        end = min(len(text), first + 80)
        snippet = text[start:end].replace("\n", " ")
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

    return {
        "cite": cite,
        "position": pos,
        "accuracy": acc,
        "count": count,
        "snippet": snippet,
    }
