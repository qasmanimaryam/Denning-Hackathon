"""
views/detail.py — Single Scholarship Detail Page for ScholarMatch.

Displays one scholarship with Overview (AI explanation), Requirements (icon checklist),
and Documents (saved to Checklist), plus 'Apply on official site' and 'Write my application'.
"""

from __future__ import annotations

import hashlib
import html
import json
from datetime import date
from typing import Any

import streamlit as st

from drafts import explain
from eligibility import rank
from ui.components import (
    badge_html,
    days_left_chip_html,
    empty_state,
    icon_svg,
    render_back_bar,
    render_speech_button,
    secondary_button,
    skeleton_loader,
)
from ui.i18n import is_urdu, t


@st.cache_data(show_spinner=False, ttl=3600)
def _cached_explain(
    sch_id: str,
    prof_hash: str,
    lang: str,
    match_json: str,
    prof_json: str,
) -> str:
    """Cache AI explanation per (scholarship_id, profile_hash, language)."""
    _ = (sch_id, prof_hash)
    return explain(
        match=json.loads(match_json),
        profile=json.loads(prof_json),
        lang=lang,
    )


def _profile_hash(profile: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(profile, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def render() -> None:
    """Render the Scholarship Detail screen."""
    pages = st.session_state["pages"]
    prof = st.session_state["profile"]
    lang = st.session_state.get("lang", "English")

    render_back_bar(t("detail_back"), pages["matches"], breadcrumb="Matches → Scholarship Detail")

    all_scholarships = st.session_state.get("all_scholarships", [])
    ranked = rank(all_scholarships, prof, date.today())
    combined = list(ranked) + ranked.closed_recently + ranked.not_eligible

    selected_id = st.session_state.get("selected_scholarship_id")
    target: dict[str, Any] | None = None
    for item in combined:
        if item.get("id") == selected_id:
            target = item
            break
    if target is None and combined:
        target = combined[0]
        st.session_state["selected_scholarship_id"] = target.get("id")

    if target is None:
        if empty_state(
            "compass",
            "No scholarship selected",
            "Choose a scholarship from your matches list first.",
            action_label="Back to matches",
            action_key="det_empty_back",
        ):
            st.switch_page(pages["matches"])
        return

    sch_id = str(target.get("id") or "")
    status = target.get("status", "maybe")
    is_demo = sch_id.startswith("demo_")

    badges = ""
    if is_demo:
        badges += badge_html("Demo", "demo") + " "
    if status == "yes":
        badges += badge_html("Eligible", "eligible")
    elif status == "maybe":
        badges += badge_html("Maybe — confirm details", "maybe")
    else:
        badges += badge_html("Not eligible", "closed")

    chip = days_left_chip_html(target.get("days_left"))
    verified_label = target.get("last_verified") or "Unverified seed — confirm on official portal"
    benefits = target.get("benefits") or f"{str(target.get('funding') or 'Partial').title()} funding"

    # Detail Header Card
    st.markdown(
        f"""
        <div class="sm-card">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:10px;">
                <div>{badges}</div>
                <div>{chip}</div>
            </div>
            <h1 style="font-size:1.55rem;font-weight:700;margin:4px 0;">
                {html.escape(str(target.get("name", "")))}
            </h1>
            <div style="color:var(--text-muted);font-size:0.95rem;margin-bottom:12px;">
                {html.escape(str(target.get("provider", "")))}
            </div>
            <div style="padding:10px 14px;background:var(--surface-2);border-radius:10px;font-size:0.92rem;color:var(--text);">
                <strong>Benefits:</strong> {html.escape(str(benefits))}
            </div>
            <div style="margin-top:10px;font-size:0.8rem;color:var(--text-faint);">
                Last verified on: {html.escape(str(verified_label))}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3 Detail Tabs: Overview, Requirements, Documents
    tab_ov, tab_req, tab_docs = st.tabs(
        [t("tab_overview"), t("tab_requirements"), t("tab_documents")]
    )

    with tab_ov:
        ph = st.empty()
        with ph.container():
            skeleton_loader("Explaining how this scholarship fits your profile...", lines=3)
        explanation = _cached_explain(
            sch_id=sch_id,
            prof_hash=_profile_hash(prof),
            lang=lang,
            match_json=json.dumps(target, default=str),
            prof_json=json.dumps(prof, default=str),
        )
        ph.empty()

        if is_urdu():
            st.markdown(
                f'<div class="sm-urdu" dir="rtl">{html.escape(explanation)}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="sm-card" style="background:var(--surface-2);">
                    <div style="font-size:0.98rem;line-height:1.65;color:var(--text);">
                        {html.escape(explanation)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        render_speech_button(explanation, lang=lang, key_id=f"det_spk_{sch_id}_{lang}")

        if target.get("evidence"):
            st.markdown(
                f"""
                <div style="margin-top:12px;padding:12px 16px;border-left:2px solid var(--border-hover);color:var(--text-muted);font-style:italic;font-size:0.88rem;">
                    "{html.escape(str(target.get("evidence")))}"
                </div>
                """,
                unsafe_allow_html=True,
            )

    with tab_req:
        reasons = target.get("reasons") or []
        rows_html = ""
        for r in reasons:
            r_low = r.lower()
            if "confirm" in r_low or "not published" in r_low or "tentative" in r_low:
                ic = icon_svg("help", 16, "#FBBF24")
                tag_lbl = "Confirm on website"
                col = "var(--warning)"
            elif "below" in r_low or "exceeds" in r_low or "restricted" in r_low or "passed" in r_low or "only" in r_low:
                ic = icon_svg("x", 16, "#F87171")
                tag_lbl = "Not met"
                col = "var(--danger)"
            else:
                ic = icon_svg("check", 16, "#34D399")
                tag_lbl = "Met"
                col = "var(--success)"

            rows_html += f"""
            <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;padding:11px 0;border-bottom:1px solid var(--border);">
                <div style="display:flex;align-items:center;gap:10px;font-size:0.92rem;color:var(--text);">
                    {ic}<span>{html.escape(r)}</span>
                </div>
                <span style="font-size:0.76rem;font-weight:600;color:{col};white-space:nowrap;">{tag_lbl}</span>
            </div>
            """
        st.markdown(f'<div class="sm-card">{rows_html}</div>', unsafe_allow_html=True)

    with tab_docs:
        docs = target.get("documents") or []
        in_chk = sch_id in st.session_state.get("checklist_ids", [])

        chk_toggle_label = "Saved in your Checklist (click to remove)" if in_chk else "Save this scholarship to my Checklist"
        if secondary_button(chk_toggle_label, key=f"det_save_chk_{sch_id}"):
            cur_list = list(st.session_state.get("checklist_ids", []))
            if sch_id in cur_list:
                cur_list.remove(sch_id)
            else:
                cur_list.append(sch_id)
            st.session_state["checklist_ids"] = cur_list
            st.rerun()

        if not docs:
            st.caption("No specific documents listed yet. Check the official portal.")
        else:
            doc_state: dict[str, bool] = st.session_state.setdefault("checked_docs", {})
            for idx, doc_name in enumerate(docs):
                d_key = f"{sch_id}::{doc_name}"
                checked = st.checkbox(
                    doc_name,
                    value=bool(doc_state.get(d_key, False)),
                    key=f"det_doc_{sch_id}_{idx}",
                )
                doc_state[d_key] = checked
                if checked and sch_id not in st.session_state.get("checklist_ids", []):
                    st.session_state["checklist_ids"].append(sch_id)

    st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)

    # Bottom Sticky Action Bar: "Apply on official site" (primary) + "Write my application" (secondary)
    act1, act2 = st.columns([1.2, 1])
    apply_url = target.get("apply_url") or target.get("source_url")
    with act1:
        if apply_url and str(apply_url).startswith("http"):
            st.link_button(t("btn_apply_official"), str(apply_url), type="primary", width="stretch")
        else:
            st.button("Apply via university Financial Aid Office", disabled=True, width="stretch")
    with act2:
        if secondary_button(t("btn_write_app"), key=f"det_write_app_{sch_id}"):
            st.session_state["selected_scholarship_id"] = sch_id
            st.switch_page(pages["application_helper"])


render()
