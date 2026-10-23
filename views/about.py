"""
views/about.py — About, Live API Status Verifier & Data Sources Page for ScholarMatch.
"""

from __future__ import annotations

import html
import time

import streamlit as st

from llm import LLMError, ask, get_config, is_ai_configured
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


def render() -> None:
    """Render the About & Live AI Connection Status screen."""
    pages = st.session_state["pages"]

    render_back_bar(t("nav_home"), pages["home"], breadcrumb="About & AI Status")

    section_header(
        t("about_title"),
        t("about_sub"),
        icon_name="shield",
    )

    # 1. Live AI API Diagnostic Card (answers "How do we know the API is working?")
    provider = (get_config("LLM_PROVIDER", "gemini") or "gemini").upper()
    model_name = (
        get_config("GEMINI_MODEL", "gemini-3-flash-preview")
        if provider == "GEMINI"
        else get_config("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
    )
    key_ready = is_ai_configured()
    status_badge = badge_html("Key configured", "eligible") if key_ready else badge_html("No key found", "maybe")

    st.markdown(
        f"""
        <div class="sm-card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                <div class="sm-heading" style="font-size:1.1rem;font-weight:600;">Live AI API Connection</div>
                <div>{status_badge}</div>
            </div>
            <div style="color:var(--text-muted);font-size:0.9rem;">
                Active provider: <strong style="color:var(--text);">{html.escape(provider)}</strong> &nbsp;•&nbsp;
                Model: <strong style="color:var(--text);">{html.escape(str(model_name))}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if primary_button("Test live AI connection now", key="about_test_api_btn"):
        ph = st.empty()
        with ph.container():
            skeleton_loader("Pinging Gemini API...", lines=2)
        t0 = time.perf_counter()
        try:
            reply = ask("Reply with: ScholarMatch AI is online and working.", max_tokens=300)
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            ph.empty()
            inline_alert(
                f"API is WORKING ({elapsed_ms} ms) — Response from {model_name}: \"{reply}\"",
                kind="success",
            )
        except LLMError as exc:
            ph.empty()
            inline_alert(f"API test failed: {exc}", kind="error")

    # 2. How It Works & Anti-Agent Notice
    st.markdown(
        """
        <div class="sm-card" style="margin-top:16px;">
            <div class="sm-heading" style="font-size:1.1rem;font-weight:600;margin-bottom:8px;">
                Rules by code, explanation by AI
            </div>
            <div style="color:var(--text-muted);font-size:0.92rem;line-height:1.6;">
                Every eligibility check, deadline comparison, and ranking score is computed by pure, unit-tested Python code (<code>eligibility.py</code>) — never by the language model.
                AI is used strictly for reading marksheet photos, extracting structured JSON from official notices, and explaining matches or drafting applications in English and Urdu.
            </div>
            <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border);color:var(--text-muted);font-size:0.9rem;">
                <strong style="color:var(--text);">Privacy & anti-scam promise:</strong> Your profile stays in this browser tab only and is never stored. Legitimate scholarships are free to apply — never pay an agent.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. Official Data Sources & Verification Dates
    st.markdown(
        '<div class="sm-heading" style="font-size:1.1rem;font-weight:600;margin:18px 0 8px 0;">Official data sources</div>',
        unsafe_allow_html=True,
    )

    if secondary_button("🔄 Re-fetch & update live scholarships from official portals", key="about_refresh_live_btn"):
        from datetime import date
        from fetch_all import refresh_scholarships

        status_box = st.empty()
        prog = st.progress(0, text="Connecting to official scholarship portals...")

        def on_prog(curr: int, total: int, hint: str) -> None:
            prog.progress(int((curr / total) * 100), text=f"Fetching live [{curr}/{total}]: {hint}")

        with status_box.container():
            skeleton_loader("Querying live government & foundation portals with AI...", lines=3)
        try:
            merged, stats = refresh_scholarships(dry_run=False, progress_callback=on_prog)
            st.session_state["all_scholarships"] = merged
            today_iso = date.today().isoformat()
            st.session_state["last_refreshed"] = today_iso
            status_box.empty()
            prog.empty()
            inline_alert(
                f"Successfully refreshed live data! {stats['ok_count']} official scholarships updated via live AI extraction.",
                kind="success",
            )
            time.sleep(1)
            st.rerun()
        except Exception as exc:
            status_box.empty()
            prog.empty()
            inline_alert(f"Live refresh error: {exc}", kind="error")

    all_scholarships = st.session_state.get("all_scholarships", [])
    rows = [
        {
            "Scholarship": s.get("name"),
            "Provider": s.get("provider"),
            "Official URL": s.get("source_url"),
            "Last verified": s.get("last_verified") or "Unverified seed",
        }
        for s in all_scholarships
    ]
    st.dataframe(rows, width="stretch")


render()
