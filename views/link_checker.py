"""
views/link_checker.py — Single-Feature Link & Notice Checker Page for ScholarMatch.
"""

from __future__ import annotations

import html
from datetime import date
from pathlib import Path
from typing import Any

import streamlit as st

from eligibility import check
from extract import (
    BROWSER_FALLBACK_MESSAGE,
    ExtractionError,
    extract_from_text,
    extract_from_url,
)
from ui.components import (
    badge_html,
    inline_alert,
    primary_button,
    render_back_bar,
    secondary_button,
    section_header,
    skeleton_loader,
)
from ui.i18n import t

BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLES_DIR = BASE_DIR / "samples"


@st.cache_data(show_spinner=False, ttl=3600)
def _cached_url(url: str, today_iso: str) -> dict[str, Any]:
    return extract_from_url(url=url, today=today_iso)


@st.cache_data(show_spinner=False, ttl=3600)
def _cached_text(text: str, today_iso: str) -> dict[str, Any]:
    return extract_from_text(text=text, source_url="pasted_text", today=today_iso)


def render() -> None:
    """Render the Link Checker page."""
    pages = st.session_state["pages"]
    prof = st.session_state["profile"]

    render_back_bar(t("nav_home"), pages["home"], breadcrumb="Link Checker")

    section_header(
        t("link_title"),
        t("link_sub"),
        icon_name="link",
    )

    sc1, sc2 = st.columns([1.4, 2.6])
    with sc1:
        if secondary_button("Load sample notice", key="lnk_load_sample"):
            sample_p = SAMPLES_DIR / "sample_scholarship_notice.txt"
            if sample_p.exists():
                st.session_state["sample_notice_text"] = sample_p.read_text(encoding="utf-8")
                st.rerun()

    raw_input = st.text_area(
        "Paste scholarship URL (https://...) or full announcement text",
        value=st.session_state.get("sample_notice_text", ""),
        height=145,
        placeholder="Paste an official scholarship link or copy-paste a WhatsApp / website notice here...",
    )

    if st.session_state.get("needs_browser_fallback"):
        inline_alert(BROWSER_FALLBACK_MESSAGE, kind="warning")

    if primary_button(t("btn_check_link"), key="lnk_primary_check"):
        st.session_state["needs_browser_fallback"] = False
        cleaned = (raw_input or "").strip()
        if not cleaned:
            inline_alert("Paste a scholarship link or announcement text above first.", kind="warning")
        else:
            ph = st.empty()
            with ph.container():
                skeleton_loader("Checking deadlines and eligibility rules...", lines=4)

            today_iso = date.today().isoformat()
            is_single_url = (
                "\n" not in cleaned
                and len(cleaned) < 400
                and cleaned.lower().startswith(("http://", "https://"))
            )
            try:
                if is_single_url:
                    extracted = _cached_url(cleaned, today_iso)
                else:
                    extracted = _cached_text(cleaned, today_iso)
                st.session_state["analysed_scholarship"] = extracted
            except ExtractionError as exc:
                if exc.needs_browser:
                    st.session_state["needs_browser_fallback"] = True
                else:
                    inline_alert(str(exc), kind="error")
            finally:
                ph.empty()

    analysed = st.session_state.get("analysed_scholarship")
    if analysed:
        st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

        status, reasons = check(analysed, prof, date.today())
        if status == "yes":
            inline_alert("You meet all published criteria for this scholarship.", kind="success")
            v_badge = badge_html("Eligible", "eligible")
        elif status == "maybe":
            inline_alert("You match the main profile, but some details need confirmation on the official site.", kind="warning")
            v_badge = badge_html("Maybe — confirm details", "maybe")
        else:
            inline_alert(f"Not eligible based on your current profile: {'; '.join(reasons)}", kind="error")
            v_badge = badge_html("Not eligible", "closed")

        inc = (
            f"PKR {int(analysed['max_family_income_pkr']):,}/month"
            if analysed.get("max_family_income_pkr") is not None
            else "Not stated on page"
        )
        marks_parts = []
        if analysed.get("min_percentage") is not None:
            marks_parts.append(f"{analysed['min_percentage']}%")
        if analysed.get("min_cgpa") is not None:
            marks_parts.append(f"{analysed['min_cgpa']} CGPA")
        marks_str = " or ".join(marks_parts) if marks_parts else "Not stated on page"

        docs_str = ", ".join(analysed.get("documents") or []) or "See official website"
        dl_str = analysed.get("deadline_iso") or "Not stated on page"

        st.markdown(
            f"""
            <div class="sm-card">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                    <div class="sm-heading" style="font-size:1.2rem;font-weight:700;">
                        {html.escape(str(analysed.get("name", "")))}
                    </div>
                    <div>{v_badge}</div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;background:var(--surface-2);padding:14px;border-radius:12px;">
                    <div>
                        <div style="font-size:0.75rem;color:var(--text-faint);text-transform:uppercase;">Deadline</div>
                        <div style="font-weight:600;color:var(--text);">{html.escape(str(dl_str))}</div>
                    </div>
                    <div>
                        <div style="font-size:0.75rem;color:var(--text-faint);text-transform:uppercase;">Income limit</div>
                        <div style="font-weight:600;color:var(--text);">{html.escape(inc)}</div>
                    </div>
                    <div>
                        <div style="font-size:0.75rem;color:var(--text-faint);text-transform:uppercase;">Marks needed</div>
                        <div style="font-weight:600;color:var(--text);">{html.escape(marks_str)}</div>
                    </div>
                    <div>
                        <div style="font-size:0.75rem;color:var(--text-faint);text-transform:uppercase;">Provider</div>
                        <div style="font-weight:600;color:var(--text);">{html.escape(str(analysed.get("provider", "")))}</div>
                    </div>
                </div>
                <div style="margin-top:12px;font-size:0.9rem;color:var(--text-muted);">
                    <strong style="color:var(--text);">Documents:</strong> {html.escape(docs_str)}
                </div>
                <div style="margin-top:12px;padding-top:10px;border-top:1px solid var(--border);color:var(--text-muted);font-style:italic;font-size:0.86rem;">
                    "{html.escape(str(analysed.get("evidence") or "No verbatim quote extracted."))}"
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if secondary_button("Save to my checklist for this session", key="lnk_save_session"):
            existing_ids = {s.get("id") for s in st.session_state["all_scholarships"]}
            if analysed.get("id") not in existing_ids:
                st.session_state["all_scholarships"].append(analysed)
            if analysed.get("id") not in st.session_state["checklist_ids"]:
                st.session_state["checklist_ids"].append(analysed.get("id"))
            inline_alert("Saved to your session checklist.", kind="success")


render()
