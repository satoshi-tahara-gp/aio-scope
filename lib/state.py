"""プロジェクト状態管理: session_state + JSONエクスポート/インポート"""
import json
from datetime import datetime
from copy import deepcopy

import streamlit as st

from .templates import AI_QUERY_TEMPLATES, AI_SERVICES, SGE_KEYWORDS_COUNT


def _empty_ai_quote_rows():
    rows = []
    for i, (cat, tpl) in enumerate(AI_QUERY_TEMPLATES):
        row = {"category": cat, "template": tpl, "query": tpl}
        for ai in AI_SERVICES:
            row[ai] = {"cite": 0, "position": 0, "accuracy": 0, "response": ""}
        rows.append(row)
    return rows


def _empty_sge_rows():
    return [
        {"keyword": "", "volume": "", "overview": False, "cite": False, "link": False, "note": ""}
        for _ in range(SGE_KEYWORDS_COUNT)
    ]


def new_project(name: str, client: str, url: str, industry: str,
                competitors: list, user_email: str) -> dict:
    now = datetime.now().isoformat()
    return {
        "id": f"proj_{int(datetime.now().timestamp() * 1000)}",
        "name": name,
        "client_name": client,
        "target_url": url,
        "industry": industry,
        "competitors": competitors,
        "owner_email": user_email,
        "created_at": now,
        "updated_at": now,
        "status": "in_progress",
        "diagnosis": {
            "ai_quote": {"rows": _empty_ai_quote_rows(), "notes": ""},
            "sge": {"rows": _empty_sge_rows(), "notes": ""},
            "schema": {"items": {}, "notes": ""},
            "eeat": {"items": {}, "notes": ""},
            "tech_seo": {"items": {}, "notes": ""},
            "competitor": {
                "competitors": [
                    {"name": c, "scores": [0, 0, 0, 0, 0]}
                    for c in competitors
                ],
                "notes": "",
            },
        },
        "findings": {"strengths": [], "weaknesses": []},
        "actions": [],
    }


def ensure_projects_store():
    if "projects" not in st.session_state:
        st.session_state.projects = {}
    if "current_project_id" not in st.session_state:
        st.session_state.current_project_id = None


def current_project():
    ensure_projects_store()
    pid = st.session_state.current_project_id
    if pid and pid in st.session_state.projects:
        return st.session_state.projects[pid]
    return None


def save_current_project(proj: dict):
    ensure_projects_store()
    proj["updated_at"] = datetime.now().isoformat()
    st.session_state.projects[proj["id"]] = proj


def project_to_json(project: dict) -> str:
    return json.dumps(project, ensure_ascii=False, indent=2)


def project_from_json(s: str) -> dict:
    return json.loads(s)


def all_projects():
    ensure_projects_store()
    return list(st.session_state.projects.values())


def set_current(pid: str):
    ensure_projects_store()
    st.session_state.current_project_id = pid


def delete_project(pid: str):
    ensure_projects_store()
    if pid in st.session_state.projects:
        del st.session_state.projects[pid]
    if st.session_state.current_project_id == pid:
        st.session_state.current_project_id = None
