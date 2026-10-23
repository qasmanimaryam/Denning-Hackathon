"""
app.py — Entry Point & Multipage Router for ScholarMatch.

Configures global dark-theme tokens (`ui/theme.py`), session state, custom minimal
top navigation (`Home`, `Find`, `Link checker`, `Checklist`), and routes across
8 single-feature pages via `st.navigation` + `st.Page`.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import streamlit as st

from ui.components import render_footer, render_top_nav
from ui.theme import apply_theme

st.set_page_config(
    page_title="ScholarMatch — Open Scholarships for Pakistani Students",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "scholarships.json"
SEED_PATH = BASE_DIR / "data" / "scholarships.seed.json"


def load_scholarships() -> tuple[list[dict[str, Any]], str]:
    """Load scholarships from `data/scholarships.json` with fallback to `scholarships.seed.json`."""
    target = DATA_PATH if DATA_PATH.exists() else SEED_PATH
    if not target.exists():
        return [], date.today().isoformat()
    try:
        with target.open("r", encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else []
    except Exception:
        items = []

    # Exclude synthetic demo records so only real official scholarships are used
    items = [s for s in items if not str(s.get("id", "")).startswith("demo_")]

    verified_dates = [
        str(s.get("last_verified"))
        for s in items
        if s.get("last_verified")
    ]
    if verified_dates:
        refreshed = max(verified_dates)
    else:
        refreshed = date.today().isoformat()
    return items, refreshed


def init_state() -> None:
    """Initialize session state keys (student data is held in session memory only)."""
    if "all_scholarships" not in st.session_state:
        items, refreshed = load_scholarships()
        st.session_state["all_scholarships"] = items
        st.session_state["last_refreshed"] = refreshed

    items = st.session_state.get("all_scholarships", [])
    real_ids = [str(s.get("id")) for s in items if not str(s.get("id", "")).startswith("demo_")]
    default_selected = real_ids[0] if real_ids else "demo_sindh_need_urgent"
    default_checklist = real_ids[:2] if len(real_ids) >= 2 else ["demo_sindh_need_urgent", "demo_pak_cs_merit"]

    defaults: dict[str, Any] = {
        "profile": {
            "level": "undergraduate",
            "province": "Sindh",
            "percentage": 78.0,
            "cgpa": 3.42,
            "monthly_income_pkr": 35000,
            "field": "Computer Science",
            "want": "need_based",
        },
        "lang": "English",
        "wizard_step": 1,
        "profile_completed": False,
        "matches_visible_count": 5,
        "selected_scholarship_id": default_selected,
        "checklist_ids": default_checklist,
        "checked_docs": {},
        "draft_outputs": {},
        "marksheet_result": None,
        "analysed_scholarship": None,
        "needs_browser_fallback": False,
        "sample_notice_text": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def main() -> None:
    """Configure navigation, inject theme CSS, and render the active page."""
    apply_theme()
    init_state()

    pages = {
        "home": st.Page("views/home.py", title="Home", icon=":material/home:", default=True),
        "profile": st.Page("views/profile.py", title="Profile Wizard", icon=":material/tune:"),
        "matches": st.Page("views/matches.py", title="Matches", icon=":material/auto_awesome:"),
        "detail": st.Page("views/detail.py", title="Scholarship Detail", icon=":material/description:"),
        "application_helper": st.Page(
            "views/application_helper.py", title="Application Helper", icon=":material/edit_note:"
        ),
        "link_checker": st.Page("views/link_checker.py", title="Link Checker", icon=":material/link:"),
        "checklist": st.Page("views/checklist.py", title="Checklist", icon=":material/checklist:"),
        "about": st.Page("views/about.py", title="About & AI Status", icon=":material/verified_user:"),
    }
    st.session_state["pages"] = pages

    current_page = st.navigation(list(pages.values()), position="hidden")

    render_top_nav(pages=pages, active_key=current_page.title)
    current_page.run()
    render_footer(
        about_page=pages["about"],
        last_refreshed=st.session_state.get("last_refreshed", date.today().isoformat()),
    )


if __name__ == "__main__":
    main()
