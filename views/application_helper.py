"""
views/application_helper.py — Dedicated Application Draft Writer Page for ScholarMatch.
"""

from __future__ import annotations

import html
from datetime import date

import streamlit as st

from drafts import application_draft
from eligibility import rank
from ui.components import (
    inline_alert,
    primary_button,
    render_back_bar,
    render_speech_button,
    secondary_button,
    section_header,
    skeleton_loader,
)
from ui.i18n import t


def render() -> None:
    """Render the Application Helper screen."""
    pages = st.session_state["pages"]
    prof = st.session_state["profile"]

    render_back_bar("Back to scholarship", pages["detail"], breadcrumb="Detail → Application Helper")

    section_header(
        t("draft_title"),
        t("draft_sub"),
        icon_name="file-text",
    )

    all_scholarships = st.session_state.get("all_scholarships", [])
    ranked = rank(all_scholarships, prof, date.today())
    options = list(ranked) if ranked else all_scholarships

    if not options:
        inline_alert("No scholarships available. Return to Home to load scholarships.", kind="warning")
        return

    id_to_sch = {str(s.get("id")): s for s in options}
    id_list = list(id_to_sch.keys())

    current_id = str(st.session_state.get("selected_scholarship_id") or id_list[0])
    default_idx = id_list.index(current_id) if current_id in id_list else 0

    chosen_id = st.selectbox(
        "1. Choose scholarship",
        options=id_list,
        index=default_idx,
        format_func=lambda sid: f"{id_to_sch[sid].get('name')} ({id_to_sch[sid].get('provider')})",
    )
    st.session_state["selected_scholarship_id"] = chosen_id
    chosen_sch = id_to_sch[chosen_id]

    notes = st.text_area(
        "2. Add a few personal notes (optional)",
        placeholder="e.g., First in my family to attend university, scored 85% in programming lab, need hostel support...",
        height=95,
    )

    lang_choice = st.segmented_control(
        "3. Draft language",
        options=["English", "اردو"],
        default="اردو" if st.session_state.get("lang") == "Urdu" else "English",
    )
    target_lang = "Urdu" if lang_choice == "اردو" else "English"

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    generate_clicked = primary_button(t("btn_generate_draft"), key="app_helper_gen_btn")

    saved_drafts = st.session_state.setdefault("draft_outputs", {})
    existing = saved_drafts.get(chosen_id)

    if generate_clicked:
        ph = st.empty()
        with ph.container():
            skeleton_loader("Drafting your sincere application...", lines=4)
        draft_text = application_draft(
            match=chosen_sch,
            profile=prof,
            student_notes=notes,
            lang=target_lang,
        )
        ph.empty()
        saved_drafts[chosen_id] = {"text": draft_text, "lang": target_lang}
        existing = saved_drafts[chosen_id]

    if existing:
        draft_str = existing["text"]
        d_lang = existing["lang"]

        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        inline_alert(t("draft_review_note"), kind="info")

        if d_lang == "Urdu":
            st.markdown(
                f'<div class="sm-urdu" dir="rtl">{html.escape(draft_str)}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("**Copy draft (click copy icon in top-right of box):**")
        st.code(draft_str, language="markdown")

        c1, c2, c3 = st.columns([1.2, 1.2, 1])
        with c1:
            if secondary_button(t("btn_regenerate"), key="app_helper_regen_btn"):
                ph = st.empty()
                with ph.container():
                    skeleton_loader("Regenerating draft...", lines=4)
                new_text = application_draft(
                    match=chosen_sch,
                    profile=prof,
                    student_notes=notes,
                    lang=target_lang,
                )
                ph.empty()
                saved_drafts[chosen_id] = {"text": new_text, "lang": target_lang}
                st.rerun()
        with c2:
            st.download_button(
                "Download (.txt)",
                data=draft_str.encode("utf-8"),
                file_name=f"draft_{chosen_id}.txt",
                mime="text/plain",
                width="stretch",
            )
        with c3:
            render_speech_button(draft_str, lang=d_lang, key_id=f"app_hlp_spk_{chosen_id}")


render()
