"""
views/checklist.py — Saved Documents & Deadline Timeline Page for ScholarMatch.
"""

from __future__ import annotations

import html
from datetime import date

import streamlit as st

from ui.components import (
    empty_state,
    render_back_bar,
    section_header,
    stepper,
)
from ui.i18n import t


def render() -> None:
    """Render the Checklist & Timeline screen."""
    pages = st.session_state["pages"]

    render_back_bar(t("nav_home"), pages["home"], breadcrumb="Checklist & Timeline")

    section_header(
        t("checklist_title"),
        t("checklist_sub"),
        icon_name="check",
    )

    all_scholarships = st.session_state.get("all_scholarships", [])
    selected_ids = st.session_state.get("checklist_ids", [])
    saved = [s for s in all_scholarships if s.get("id") in selected_ids]

    if not saved:
        if empty_state(
            icon_name="file-text",
            headline="Your checklist is empty",
            helper_text="Open any scholarship match and save its documents to track them here.",
            action_label=t("cta_find"),
            action_key="chk_empty_find",
        ):
            st.switch_page(pages["matches"] if st.session_state.get("profile_completed") else pages["profile"])
        return

    # 1. Deadline Timeline sorted by date with coloured dots
    st.markdown(
        '<div class="sm-heading" style="font-size:1.1rem;font-weight:600;margin-bottom:10px;">Deadline timeline</div>',
        unsafe_allow_html=True,
    )

    sorted_by_date = sorted(saved, key=lambda x: x.get("deadline_iso") or "9999-12-31")
    timeline_html = ""
    today = date.today()

    for s in sorted_by_date:
        dl = s.get("deadline_iso")
        if dl:
            d_left = (date.fromisoformat(dl) - today).days
            if d_left <= 3:
                dot_col = "var(--danger)"
                d_txt = f"{d_left}d left" if d_left >= 0 else "Closed"
            elif d_left <= 14:
                dot_col = "var(--warning)"
                d_txt = f"{d_left}d left"
            else:
                dot_col = "var(--success)"
                d_txt = f"{d_left}d left"
            date_str = f"{dl} ({d_txt})"
        else:
            dot_col = "var(--text-faint)"
            date_str = "Date unconfirmed on website"

        timeline_html += f"""
        <div style="display:flex;justify-content:space-between;align-items:center;padding:11px 0;border-bottom:1px solid var(--border);">
            <div style="display:flex;align-items:center;gap:12px;">
                <span style="width:10px;height:10px;border-radius:50%;background:{dot_col};display:inline-block;flex-shrink:0;"></span>
                <span style="font-weight:600;color:var(--text);font-size:0.95rem;">{html.escape(str(s.get("name", "")))}</span>
            </div>
            <span style="font-size:0.85rem;color:var(--text-muted);font-variant-numeric:tabular-nums;">{html.escape(date_str)}</span>
        </div>
        """

    st.markdown(f'<div class="sm-card">{timeline_html}</div>', unsafe_allow_html=True)

    # 2. Documents Grouped by Scholarship
    st.markdown(
        '<div class="sm-heading" style="font-size:1.1rem;font-weight:600;margin:18px 0 8px 0;">Documents by scholarship</div>',
        unsafe_allow_html=True,
    )

    doc_state: dict[str, bool] = st.session_state.setdefault("checked_docs", {})
    total_docs = 0
    done_docs = 0

    for s in saved:
        sid = str(s.get("id"))
        docs = s.get("documents") or []
        for d in docs:
            total_docs += 1
            if doc_state.get(f"{sid}::{d}", False):
                done_docs += 1

    if total_docs > 0:
        stepper(current_step=done_docs, total_steps=total_docs, label=f"{done_docs} of {total_docs} documents ready")

    for s in saved:
        sid = str(s.get("id"))
        docs = s.get("documents") or []
        with st.expander(f"{s.get('name')} ({len(docs)} documents)", expanded=True):
            if not docs:
                st.caption("Check official portal for document list.")
            for idx, doc_name in enumerate(docs):
                d_key = f"{sid}::{doc_name}"
                val = st.checkbox(
                    doc_name,
                    value=bool(doc_state.get(d_key, False)),
                    key=f"chk_page_{sid}_{idx}",
                )
                doc_state[d_key] = val


render()
