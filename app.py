"""
AIO-Scope: AIO/SEO現状診断ツール
Goodpatch Market Design Div 向け営業スタートキット

Usage (local):
    pip install -r requirements.txt
    streamlit run app.py
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from lib.auth import require_auth, logout
from lib.state import (
    ensure_projects_store, current_project, save_current_project,
    new_project, all_projects, set_current, delete_project,
    project_to_json, project_from_json,
)
from lib.templates import (
    AREAS, AREA_ORDER, AI_SERVICES, AI_QUERY_TEMPLATES,
    SCHEMA_ITEMS, EEAT_ITEMS, TECH_SEO_ITEMS, rank_from_score,
    ai_launch_url, google_search_url, rich_results_test_url,
    pagespeed_url, schema_validator_url, wayback_url,
)
from lib.scoring import score_all
from lib.auto_score import analyze_response
from lib.excel_export import build_xlsx
from lib.pptx_export import build_pptx


st.set_page_config(
    page_title="AIO-Scope / AIO/SEO現状診断",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# Authentication gate
# ============================================================
require_auth()
ensure_projects_store()


# ============================================================
# Sidebar
# ============================================================
with st.sidebar:
    st.markdown(
        "<div style='font-size:24px; font-weight:700; color:#1E293B; "
        "letter-spacing:-0.02em; margin-bottom:0.3rem;'>AIO-Scope</div>"
        "<div style='color:#64748B; font-size:11px; margin-bottom:1.5rem;'>"
        "AIO/SEO診断 v1 &nbsp;|&nbsp; Goodpatch</div>",
        unsafe_allow_html=True,
    )

    st.markdown(f"👤 **{st.session_state.user_email}**")
    if st.button("🚪 ログアウト", use_container_width=True):
        logout()
        st.rerun()

    st.divider()

    # Project selector
    projects = all_projects()
    options = ["➕ 新規案件を作成"]
    id_map = {"➕ 新規案件を作成": None}
    for p in sorted(projects, key=lambda x: x.get("updated_at", ""), reverse=True):
        sc = score_all(p)
        label = f"📂 {p['name']} — {sc['total']:.0f}pt"
        options.append(label)
        id_map[label] = p["id"]

    current_id = st.session_state.current_project_id
    default_idx = 0
    for i, opt in enumerate(options):
        if id_map[opt] == current_id:
            default_idx = i
            break

    selected = st.radio(
        "案件選択",
        options,
        index=default_idx,
        label_visibility="collapsed",
    )
    set_current(id_map[selected])

    st.divider()

    # Import / Export
    st.markdown("#### 📦 案件データ")
    uploaded = st.file_uploader(
        "JSONファイルから案件を読み込み",
        type=["json"],
        key="json_upload",
        label_visibility="collapsed",
    )
    if uploaded is not None:
        try:
            imported = project_from_json(uploaded.read().decode("utf-8"))
            save_current_project(imported)
            set_current(imported["id"])
            st.success(f"読み込み完了: {imported['name']}")
            st.rerun()
        except Exception as e:
            st.error(f"読み込み失敗: {e}")

    proj = current_project()
    if proj is not None:
        js = project_to_json(proj)
        st.download_button(
            "💾 JSONエクスポート (バックアップ)",
            data=js,
            file_name=f"{proj['name']}.json",
            mime="application/json",
            use_container_width=True,
        )
        if st.button("🗑 この案件を削除", use_container_width=True):
            delete_project(proj["id"])
            st.rerun()


# ============================================================
# Main area
# ============================================================
proj = current_project()

if proj is None:
    # ---------- 新規案件作成画面 ----------
    st.title("🎯 新規案件を作成")
    st.caption("RFPを受領したらまずここから。3日間の診断プロセスを開始します。")

    with st.form("new_project"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(
                "案件名 *",
                placeholder="例: 三井ダイレクト損害保険リニューアル",
            )
            client = st.text_input(
                "クライアント名 *",
                placeholder="例: 三井ダイレクト損害保険株式会社",
            )
            industry = st.text_input(
                "業界カテゴリ",
                placeholder="例: ダイレクト自動車保険",
            )
        with col2:
            url = st.text_input(
                "対象URL",
                placeholder="https://www.example.co.jp/",
            )
            competitors_raw = st.text_area(
                "競合社 (1行に1社、最大5社)",
                placeholder="例:\nソニー損保\nイーデザイン損保\nSBI損保",
                height=150,
            )

        submitted = st.form_submit_button(
            "🚀 案件を作成して診断開始", type="primary", use_container_width=True
        )
        if submitted:
            if not name or not client:
                st.error("案件名とクライアント名は必須です")
            else:
                competitors = [c.strip() for c in competitors_raw.split("\n") if c.strip()][:5]
                p = new_project(name, client, url, industry, competitors,
                                st.session_state.user_email)
                save_current_project(p)
                set_current(p["id"])
                st.rerun()

    st.divider()

    # 過去案件
    st.markdown("### 📋 過去・進行中の案件")
    if not projects:
        st.info("まだ案件がありません。上のフォームから新規作成してください。")
    else:
        rows = []
        for p in sorted(projects, key=lambda x: x.get("updated_at", ""), reverse=True):
            sc = score_all(p)
            rank, desc, _ = rank_from_score(sc["total"])
            rows.append({
                "案件名": p["name"],
                "クライアント": p.get("client_name", ""),
                "担当": p.get("owner_email", ""),
                "スコア": f"{sc['total']:.0f} / 100",
                "ランク": f"{rank} ({desc})",
                "更新": p.get("updated_at", "")[:10],
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

else:
    # ---------- 既存案件の診断ウィザード ----------
    sc = score_all(proj)
    rank, rank_desc, rank_color = rank_from_score(sc["total"])

    # ヘッダー
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f"## 🎯 {proj['name']}")
        st.caption(
            f"クライアント: {proj.get('client_name', '—')} "
            f"| 業界: {proj.get('industry', '—')} "
            f"| URL: {proj.get('target_url', '—')}"
        )
    with col2:
        st.metric("総合スコア", f"{sc['total']:.0f} / 100")
    with col3:
        st.markdown(
            f"<div style='text-align:right; margin-top:0.5rem;'>"
            f"<div style='font-size:11px; color:#64748B;'>ランク</div>"
            f"<div style='font-size:42px; font-weight:700; color:{rank_color};"
            f"line-height:1;'>{rank}</div>"
            f"<div style='font-size:10px; color:#64748B;'>{rank_desc}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # タブ構成: 情報/6領域/ダッシュボード/所見/エクスポート
    tabs = st.tabs([
        "📝 案件情報",
        "① AI引用",
        "② SGE",
        "③ 構造化データ",
        "④ E-E-A-T",
        "⑤ テクニカル",
        "⑥ 競合",
        "📊 ダッシュボード",
        "✍️ 所見",
        "📥 エクスポート",
    ])

    # ============ Tab 0: 案件情報 ============
    with tabs[0]:
        st.subheader("案件情報の編集")
        c1, c2 = st.columns(2)
        with c1:
            proj["name"] = st.text_input("案件名", value=proj["name"])
            proj["client_name"] = st.text_input("クライアント名", value=proj.get("client_name", ""))
            proj["industry"] = st.text_input("業界カテゴリ", value=proj.get("industry", ""))
        with c2:
            proj["target_url"] = st.text_input("対象URL", value=proj.get("target_url", ""))
            comp_raw = "\n".join(proj.get("competitors", []))
            new_comp_raw = st.text_area("競合社 (1行1社)", value=comp_raw, height=150)
            new_comps = [c.strip() for c in new_comp_raw.split("\n") if c.strip()][:5]
            if new_comps != proj.get("competitors", []):
                proj["competitors"] = new_comps
                # 競合テーブルも再初期化
                proj["diagnosis"]["competitor"]["competitors"] = [
                    {"name": c, "scores": [0, 0, 0, 0, 0]} for c in new_comps
                ]
        save_current_project(proj)
        st.success("✅ 変更は自動保存されています")

    # ============ Tab 1: AI引用 ============
    with tabs[1]:
        st.subheader(f"① AI引用露出度 (20点満点, 現在 {sc['ai_quote']}/20)")
        st.caption(
            "各クエリの🚀ボタンでAIを開いて応答を確認 → 下のセレクトボックスで登場位置を選ぶだけ。"
            "ペースト不要です。"
        )

        aiq = proj["diagnosis"]["ai_quote"]

        # Helper to swap placeholders in query
        def fill_placeholders(q):
            q = q.replace("{企業名}", proj.get("client_name", "{企業名}"))
            q = q.replace("{業界}", proj.get("industry", "{業界}"))
            q = q.replace("{業界カテゴリ}", proj.get("industry", "{業界}"))
            q = q.replace("{ユーザー課題}", proj.get("industry", "") + " 保険選び")
            comps = proj.get("competitors", [])
            if len(comps) >= 1: q = q.replace("{競合A}", comps[0])
            if len(comps) >= 2: q = q.replace("{競合B}", comps[1])
            if len(comps) >= 3: q = q.replace("{競合C}", comps[2])
            return q

        # Position option labels with emoji + point weight
        POS_OPTIONS = [0, 3, 2, 1]  # なし / 先頭 / 中盤 / 末尾
        POS_LABELS = {
            0: "❌ 登場なし (0pt)",
            3: "📍 先頭に登場 (3pt)",
            2: "⚪ 中盤に登場 (2pt)",
            1: "⚫ 末尾に登場 (1pt)",
        }

        for i, row in enumerate(aiq["rows"]):
            filled = fill_placeholders(row["template"])
            row["query"] = filled  # Keep query in sync with template-based fill

            # Header with completion status
            rated = sum(
                1 for ai in AI_SERVICES
                if int(row.get(ai, {}).get("position", 0) or 0) > 0
                or row.get(ai, {}).get("_rated")
            )
            total_ai = len(AI_SERVICES)

            with st.container(border=True):
                # Query as bold, category chip as pill
                st.markdown(
                    f"**Q{i+1}** "
                    f"<span style='background:#EEF2FF;color:#4338CA;padding:2px 8px;"
                    f"border-radius:10px;font-size:11px;margin-right:6px;'>"
                    f"{row['category']}</span> "
                    f"{filled}",
                    unsafe_allow_html=True,
                )
                ai_cols = st.columns(len(AI_SERVICES))
                for idx, ai in enumerate(AI_SERVICES):
                    scores = row.setdefault(ai, {"cite": 0, "position": 0, "accuracy": 0})
                    with ai_cols[idx]:
                        sub_cols = st.columns([1.2, 2])
                        sub_cols[0].link_button(
                            f"🚀 {ai}",
                            ai_launch_url(ai, filled),
                            use_container_width=True,
                        )
                        current_pos = int(scores.get("position", 0) or 0)
                        try:
                            default_idx = POS_OPTIONS.index(current_pos)
                        except ValueError:
                            default_idx = 0
                        new_pos = sub_cols[1].selectbox(
                            f"{ai} 登場位置",
                            options=POS_OPTIONS,
                            format_func=lambda x: POS_LABELS[x],
                            index=default_idx,
                            key=f"aiq_{i}_{ai}_pos",
                            label_visibility="collapsed",
                        )
                        scores["position"] = new_pos
                        # cite を position から派生 (互換性用)
                        scores["cite"] = 1 if new_pos > 0 else 0

        aiq["notes"] = st.text_area(
            "📝 全体メモ (所見の下書きなどご自由に)",
            value=aiq.get("notes", ""),
            placeholder="AI引用全体の傾向メモ",
            key="aiq_notes",
            height=80,
        )
        save_current_project(proj)

    # ============ Tab 2: SGE ============
    with tabs[2]:
        st.subheader(f"② Google SGE / AI Overview (15点満点, 現在 {sc['sge']}/15)")
        st.caption(
            "💡 各行の「🔎 Google検索」ボタンでシークレット検索が開きます。AI Overview表示と自社引用の有無をチェック。"
        )

        sge = proj["diagnosis"]["sge"]
        # Header row
        hcols = st.columns([0.5, 3, 1.2, 1.2, 1.2, 1.2, 2, 1.5])
        hcols[0].caption("#")
        hcols[1].caption("キーワード")
        hcols[2].caption("検索Vol")
        hcols[3].caption("Overview表示")
        hcols[4].caption("自社引用")
        hcols[5].caption("リンク")
        hcols[6].caption("メモ")
        hcols[7].caption("検索")

        for i, row in enumerate(sge["rows"]):
            cols = st.columns([0.5, 3, 1.2, 1.2, 1.2, 1.2, 2, 1.5])
            cols[0].markdown(f"**{i+1}**")
            row["keyword"] = cols[1].text_input(
                "キーワード", value=row.get("keyword", ""),
                key=f"sge_kw_{i}", label_visibility="collapsed",
                placeholder="検索キーワード",
            )
            row["volume"] = cols[2].text_input(
                "Vol", value=row.get("volume", ""), key=f"sge_vol_{i}",
                label_visibility="collapsed", placeholder="検索Vol",
            )
            row["overview"] = cols[3].checkbox(
                "Overview", value=row.get("overview", False), key=f"sge_ov_{i}",
                label_visibility="collapsed",
            )
            row["cite"] = cols[4].checkbox(
                "自社引用", value=row.get("cite", False), key=f"sge_cite_{i}",
                label_visibility="collapsed",
            )
            row["link"] = cols[5].checkbox(
                "リンク", value=row.get("link", False), key=f"sge_link_{i}",
                label_visibility="collapsed",
            )
            row["note"] = cols[6].text_input(
                "メモ", value=row.get("note", ""), key=f"sge_note_{i}",
                label_visibility="collapsed", placeholder="メモ",
            )
            if row.get("keyword"):
                cols[7].link_button(
                    "🔎 検索", google_search_url(row["keyword"]),
                    use_container_width=True,
                )

        sge["notes"] = st.text_area(
            "全体メモ", value=sge.get("notes", ""), key="sge_notes",
        )
        save_current_project(proj)

    # ============ Tab 3: Schema ============
    with tabs[3]:
        st.subheader(f"③ 構造化データ (20点満点, 現在 {sc['schema']}/20)")
        st.caption("各項目を 0=なし / 1=部分的 / 2=完全 で評価")

        # External tool buttons
        tl_cols = st.columns(2)
        tl_cols[0].link_button(
            "🔍 Google Rich Results Test で確認",
            rich_results_test_url(proj.get("target_url", "")),
            use_container_width=True,
        )
        tl_cols[1].link_button(
            "🔍 Schema.org Validator で確認",
            schema_validator_url(),
            use_container_width=True,
        )

        schema_data = proj["diagnosis"]["schema"]
        items_map = schema_data.setdefault("items", {})

        for i, (name, pt) in enumerate(SCHEMA_ITEMS):
            cols = st.columns([3, 1, 2, 2])
            cols[0].markdown(f"**{name}** ({pt}点満点)")
            impl = int(items_map.get(str(i), 0) or 0)
            selected = cols[1].selectbox(
                "実装", [0, 1, 2],
                index=impl,
                key=f"schema_{i}",
                label_visibility="collapsed",
                format_func=lambda x: {0: "なし", 1: "部分", 2: "完全"}[x],
            )
            items_map[str(i)] = selected
            got = round(pt * selected / 2, 2)
            cols[2].markdown(
                f"<div style='text-align:right; padding-top:0.3rem;'>"
                f"取得: <strong>{got}</strong> / {pt}</div>",
                unsafe_allow_html=True,
            )
            cols[3].progress(selected / 2)

        schema_data["notes"] = st.text_area(
            "メモ", value=schema_data.get("notes", ""), key="schema_notes",
        )
        save_current_project(proj)

    # ============ Tab 4: E-E-A-T ============
    with tabs[4]:
        st.subheader(f"④ E-E-A-T (15点満点, 現在 {sc['eeat']}/15)")
        st.caption("Experience / Expertise / Authoritativeness / Trust の観点で採点")

        # External tool buttons
        tl_cols = st.columns(2)
        if proj.get("target_url"):
            tl_cols[0].link_button(
                "🕰 Wayback Machineで更新履歴を確認",
                wayback_url(proj["target_url"]),
                use_container_width=True,
            )
            tl_cols[1].link_button(
                "🔗 対象サイトを開く",
                proj["target_url"],
                use_container_width=True,
            )

        eeat_data = proj["diagnosis"]["eeat"]
        items_map = eeat_data.setdefault("items", {})

        for i, (name, pt) in enumerate(EEAT_ITEMS):
            cols = st.columns([3, 3, 1])
            cols[0].markdown(f"**{name}** (最大 {pt}点)")
            current = float(items_map.get(str(i), 0) or 0)
            val = cols[1].slider(
                "採点", 0.0, float(pt), current, 0.5,
                key=f"eeat_{i}", label_visibility="collapsed",
            )
            items_map[str(i)] = val
            cols[2].markdown(
                f"<div style='text-align:right; padding-top:0.3rem;'>"
                f"<strong>{val}</strong> / {pt}</div>",
                unsafe_allow_html=True,
            )

        eeat_data["notes"] = st.text_area(
            "メモ", value=eeat_data.get("notes", ""), key="eeat_notes",
        )
        save_current_project(proj)

    # ============ Tab 5: Technical SEO ============
    with tabs[5]:
        st.subheader(f"⑤ テクニカルSEO (15点満点, 現在 {sc['tech_seo']}/15)")
        st.caption("Core Web Vitals / crawlability / security を評価")

        # External tool buttons
        st.link_button(
            "⚡ PageSpeed Insights で Core Web Vitals を測定",
            pagespeed_url(proj.get("target_url", "")),
            use_container_width=True,
        )

        tech_data = proj["diagnosis"]["tech_seo"]
        items_map = tech_data.setdefault("items", {})

        for i, (name, pt) in enumerate(TECH_SEO_ITEMS):
            cols = st.columns([3, 3, 1])
            cols[0].markdown(f"**{name}** (最大 {pt}点)")
            current = float(items_map.get(str(i), 0) or 0)
            val = cols[1].slider(
                "採点", 0.0, float(pt), current, 0.5,
                key=f"tech_{i}", label_visibility="collapsed",
            )
            items_map[str(i)] = val
            cols[2].markdown(
                f"<div style='text-align:right; padding-top:0.3rem;'>"
                f"<strong>{val}</strong> / {pt}</div>",
                unsafe_allow_html=True,
            )

        tech_data["notes"] = st.text_area(
            "メモ", value=tech_data.get("notes", ""), key="tech_notes",
        )
        save_current_project(proj)

    # ============ Tab 6: Competitor ============
    with tabs[6]:
        st.subheader(f"⑥ 競合ベンチマーク (15点満点, 現在 {sc['competitor']}/15)")
        st.caption(
            "競合各社について領域1-5を同じ基準で採点。"
            "各競合は「[AI名]で検索」ボタンから簡易チェックできます"
        )

        comp_data = proj["diagnosis"]["competitor"]
        comps = comp_data.setdefault("competitors", [])

        # 案件情報の競合に合わせて調整
        comp_names_in_info = proj.get("competitors", [])
        if len(comps) != len(comp_names_in_info):
            comps = [{"name": n, "scores": [0, 0, 0, 0, 0]} for n in comp_names_in_info]
            comp_data["competitors"] = comps

        # 自社
        st.markdown("**📍 自社スコア (領域1-5、他タブから自動転記)**")
        self_scores = [sc["ai_quote"], sc["sge"], sc["schema"], sc["eeat"], sc["tech_seo"]]
        self_cols = st.columns(6)
        self_cols[0].markdown(f"**{proj.get('client_name', '自社')}**")
        for i, s in enumerate(self_scores):
            self_cols[i + 1].metric(f"領域{i+1}", f"{s:.1f}")

        st.divider()
        st.markdown("**🥊 競合スコア (手動入力)**")
        area_maxes = [20, 15, 20, 15, 15]
        industry = proj.get("industry", "")
        for ci, c in enumerate(comps):
            with st.expander(f"🥊 {c['name']}", expanded=False):
                # Quick-launch buttons for scoping this competitor
                st.caption("この競合をAIに聞いて観察したい場合:")
                probe = f"{c['name']} {industry} の特徴・強み・評判"
                st.code(probe, language=None)
                b_cols = st.columns(4)
                for j, ai in enumerate(AI_SERVICES):
                    b_cols[j].link_button(
                        f"🚀 {ai}",
                        ai_launch_url(ai, probe),
                        use_container_width=True,
                    )
                st.divider()
                # Scores
                c["scores"] = c.get("scores", [0, 0, 0, 0, 0])
                cols = st.columns(5)
                for i in range(5):
                    val = float(c["scores"][i] or 0)
                    new_val = cols[i].number_input(
                        f"領域{i+1} (/{area_maxes[i]})",
                        min_value=0.0, max_value=float(area_maxes[i]),
                        value=val, step=0.5,
                        key=f"comp_{ci}_{i}",
                    )
                    c["scores"][i] = new_val

        comp_data["notes"] = st.text_area(
            "メモ", value=comp_data.get("notes", ""), key="comp_notes",
        )
        save_current_project(proj)

    # ============ Tab 7: Dashboard ============
    with tabs[7]:
        st.subheader("📊 ダッシュボード")

        # メトリクス行
        mcols = st.columns(6)
        for i, key in enumerate(AREA_ORDER):
            a = AREAS[key]
            delta_pct = int(sc[key] / a["max_points"] * 100) if a["max_points"] else 0
            mcols[i].metric(
                f"領域{a['num']} {a['name'][:8]}",
                f"{sc[key]:.1f}",
                f"{delta_pct}%",
            )

        # Radar chart
        st.markdown("#### 領域別充足率レーダーチャート")
        categories = [f"領域{AREAS[k]['num']}\n{AREAS[k]['name']}" for k in AREA_ORDER]
        values = [sc[k] / AREAS[k]["max_points"] * 100 if AREAS[k]["max_points"] else 0
                  for k in AREA_ORDER]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            fillcolor="rgba(99, 102, 241, 0.2)",
            line=dict(color="#6366F1", width=2),
            name="自社",
        ))

        # 競合平均を重ねる
        comps = proj["diagnosis"]["competitor"].get("competitors", [])
        valid = [c for c in comps if sum(float(s or 0) for s in c.get("scores", [])) > 0]
        if valid:
            area_maxes_for_radar = [20, 15, 20, 15, 15, 15]  # 競合は領域6なし
            avg_scores = []
            for i in range(5):
                vals = [float(c["scores"][i] or 0) for c in valid]
                avg_scores.append(sum(vals) / len(vals))
            # 領域6は計算対象外: ダミーで差分=0 (7.5)
            competitor_radar = [s / m * 100 for s, m in
                                zip(avg_scores + [7.5], area_maxes_for_radar)]
            fig.add_trace(go.Scatterpolar(
                r=competitor_radar + [competitor_radar[0]],
                theta=categories + [categories[0]],
                fill="toself",
                fillcolor="rgba(239, 68, 68, 0.1)",
                line=dict(color="#EF4444", width=2, dash="dash"),
                name="競合平均",
            ))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            height=500,
            margin=dict(l=60, r=60, t=40, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)

        # 総合スコア大表示
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(
                f"""<div style='background:#1E293B; color:white; padding:2rem;
                border-radius:12px; text-align:center;'>
                <div style='font-size:12px; color:#6366F1; letter-spacing:0.1em;'>TOTAL SCORE</div>
                <div style='font-size:96px; font-weight:700; line-height:1;'>{sc['total']:.0f}</div>
                <div style='font-size:14px; color:#CBD5E1;'>/ 100 点</div>
                <div style='margin-top:1rem; display:inline-block; background:{rank_color};
                padding:0.4rem 1.2rem; border-radius:99px; font-weight:700; font-size:14px;'>
                Rank {rank}: {rank_desc}</div>
                </div>""",
                unsafe_allow_html=True,
            )

        with col2:
            # 領域別バー
            for key in AREA_ORDER:
                a = AREAS[key]
                pct = sc[key] / a["max_points"] if a["max_points"] else 0
                st.markdown(f"**領域{a['num']}: {a['name']}** &nbsp; {sc[key]:.1f} / {a['max_points']}")
                st.progress(pct)

    # ============ Tab 8: Findings ============
    with tabs[8]:
        st.subheader("✍️ 所見・改善アクションの整理")
        st.caption(
            "診断結果をふまえた所見と改善施策を書き出し、"
            "Excel/PPTエクスポート時に反映されます"
        )

        findings = proj.setdefault("findings", {"strengths": [], "weaknesses": []})

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🟢 強み")
            s_raw = st.text_area(
                "強み (1行1項目、最大5件)",
                value="\n".join(findings.get("strengths", [])),
                height=200,
                key="strengths_input",
                placeholder=(
                    "例:\n"
                    "・UI/UX評価で業界上位、特にナビゲーション設計\n"
                    "・Core Web Vitalsが全項目緑\n"
                    "・Organization Schemaが完全実装済み"
                ),
            )
            findings["strengths"] = [s.strip(" ・") for s in s_raw.split("\n") if s.strip()][:5]

        with col2:
            st.markdown("#### 🔴 弱み")
            w_raw = st.text_area(
                "弱み (1行1項目、最大5件)",
                value="\n".join(findings.get("weaknesses", [])),
                height=200,
                key="weaknesses_input",
                placeholder=(
                    "例:\n"
                    "・FAQ/HowTo Schemaが未実装\n"
                    "・AI Overview引用率が業界平均より15ポイント低い\n"
                    "・著者情報ページが未整備"
                ),
            )
            findings["weaknesses"] = [w.strip(" ・") for w in w_raw.split("\n") if w.strip()][:5]

        st.divider()
        st.markdown("#### 🎯 改善アクション")
        actions = proj.setdefault("actions", [])

        # Editable table
        action_df_data = []
        for a in actions:
            action_df_data.append({
                "施策": a.get("title", ""),
                "対象領域": a.get("area", ""),
                "Impact": a.get("impact", "M"),
                "Effort": a.get("effort", "M"),
                "Period": a.get("period", "中期"),
            })
        if not action_df_data:
            action_df_data = [{"施策": "", "対象領域": "", "Impact": "M",
                               "Effort": "M", "Period": "中期"} for _ in range(3)]

        edited = st.data_editor(
            pd.DataFrame(action_df_data),
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "施策": st.column_config.TextColumn("施策名", width="large"),
                "対象領域": st.column_config.TextColumn("対象領域", width="small"),
                "Impact": st.column_config.SelectboxColumn(
                    "Impact", options=["H", "M", "L"], width="small",
                ),
                "Effort": st.column_config.SelectboxColumn(
                    "Effort", options=["H", "M", "L"], width="small",
                ),
                "Period": st.column_config.SelectboxColumn(
                    "Period", options=["Quick Win", "中期", "長期"], width="medium",
                ),
            },
            key="actions_editor",
        )

        proj["actions"] = [
            {
                "title": r["施策"],
                "area": r["対象領域"],
                "impact": r["Impact"],
                "effort": r["Effort"],
                "period": r["Period"],
            }
            for _, r in edited.iterrows()
            if str(r.get("施策", "")).strip()
        ]

        save_current_project(proj)

    # ============ Tab 9: Export ============
    with tabs[9]:
        st.subheader("📥 エクスポート")
        st.caption("Excel / PowerPoint / JSON でダウンロード")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### 📊 Excel")
            st.markdown(
                "全領域のスコアリング明細を Cover + 6領域 + 所見シート構成で出力。"
                "クライアント共有 or 社内ナレッジとして保存。"
            )
            try:
                xlsx_bytes = build_xlsx(proj)
                st.download_button(
                    "⬇️ Excelダウンロード",
                    data=xlsx_bytes,
                    file_name=f"{proj['name']}_診断.xlsx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument"
                        ".spreadsheetml.sheet"
                    ),
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Excel生成エラー: {e}")

        with col2:
            st.markdown("#### 🎨 PowerPoint")
            st.markdown(
                "クライアントに見せる8スライドの報告書。Cover / Summary / "
                "6領域スコア / 強み弱み / アクション / Next Step を含む。"
            )
            try:
                pptx_bytes = build_pptx(proj)
                st.download_button(
                    "⬇️ PowerPointダウンロード",
                    data=pptx_bytes,
                    file_name=f"{proj['name']}_診断レポート.pptx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument"
                        ".presentationml.presentation"
                    ),
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"PPT生成エラー: {e}")

        with col3:
            st.markdown("#### 💾 JSON")
            st.markdown(
                "案件データのバックアップ。後で同じアプリに読み込み直せる。"
                "Google Driveに保存しておけばチームでの共有も可能。"
            )
            st.download_button(
                "⬇️ JSONダウンロード",
                data=project_to_json(proj),
                file_name=f"{proj['name']}.json",
                mime="application/json",
                use_container_width=True,
            )

        st.divider()
        st.info(
            "💡 **Tip**: Excel/PPTをGoogle Driveの "
            "[プロジェクトフォルダ](https://drive.google.com/drive/u/0/folders/"
            "1aQOBmIrxmSIZ6LvTQLXT2IFJXxdtsnrl) に保存すると営業チームで共有しやすくなります"
        )
