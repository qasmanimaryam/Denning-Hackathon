"""
views/matches.py — Ranked Scholarship Results Page for ScholarMatch.

Displays the summary stat strip, single segmented filter control (All / Eligible / Closing soon),
lazy-rendered cards (5 per batch), and collapsed transparency expanders at the bottom.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import streamlit as st

from eligibility import rank
from llm import is_ai_configured
from ui.components import (
    empty_state,
    inline_alert,
    render_back_bar,
    scholarship_card,
    secondary_button,
    section_header,
    stat_tile,
)
from ui.i18n import t


def _one_line_reason(match: dict[str, Any]) -> str:
    """Create a concise one-line summary reason for a match card."""
    reasons = match.get("reasons") or []
    status = match.get("status", "maybe")
    if status == "yes":
        return "Meets all published degree, province, income, and academic criteria."
    verify = [
        r for r in reasons if "confirm" in r.lower() or "not published" in r.lower() or "tentative" in r.lower()
    ]
    if verify:
        return f"Matches core profile — {verify[0].lower()}."
    if reasons:
        return str(reasons[0])
    return "Matches your study level and domicile; confirm details on official portal."


def render() -> None:
    """Render the Matches page."""
    pages = st.session_state["pages"]
    prof = st.session_state["profile"]

    render_back_bar(
        "Edit profile",
        pages["profile"],
        breadcrumb=f"{prof.get('level', '').title()} • {prof.get('province', '')} • PKR {int(prof.get('monthly_income_pkr', 0)):,}/mo",
    )

    section_header(
        t("matches_title"),
        t("matches_sub"),
        icon_name="sparkles",
    )

    all_scholarships = st.session_state.get("all_scholarships", [])
    ranked = rank(all_scholarships, prof, date.today())

    open_yes_count = sum(1 for m in ranked if m.get("status") == "yes")
    confirm_count = sum(1 for m in ranked if m.get("status") == "maybe")
    urgent_count = sum(1 for m in ranked if m.get("urgent"))

    # Top Summary Strip (3 Stat Tiles)
    s1, s2, s3 = st.columns(3)
    with s1:
        stat_tile(open_yes_count, t("stat_open"), color="var(--success)")
    with s2:
        stat_tile(confirm_count, t("stat_confirm"), color="var(--warning)")
    with s3:
        stat_tile(urgent_count, t("stat_urgent"), color="var(--danger)")

    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

    if not is_ai_configured():
        inline_alert(
            "AI key not active — showing deterministic rule-based matches. Click 'View details' on any card for full breakdown.",
            kind="info",
        )

    # Single Segmented Control Filter (All / Eligible / Closing soon)
    filter_options = [t("filter_all"), t("filter_eligible"), t("filter_urgent")]
    selected_seg = st.segmented_control(
        "Filter matches",
        options=filter_options,
        default=filter_options[0],
        label_visibility="collapsed",
    )

    filtered = list(ranked)
    if selected_seg == t("filter_eligible"):
        filtered = [m for m in filtered if m.get("status") == "yes"]
    elif selected_seg == t("filter_urgent"):
        filtered = [m for m in filtered if m.get("urgent")]

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # Lazy-rendered list (5 cards at a time)
    visible_limit = int(st.session_state.get("matches_visible_count", 5))
    visible_slice = filtered[:visible_limit]

    if not visible_slice:
        if empty_state(
            icon_name="compass",
            headline="No scholarships in this filter view",
            helper_text="Switch the filter above to 'All' or adjust your profile criteria.",
            action_label="Edit my profile",
            action_key="empty_edit_prof",
        ):
            st.switch_page(pages["profile"])
    else:
        for idx, item in enumerate(visible_slice):
            scholarship_card(
                match=item,
                one_line_reason=_one_line_reason(item),
                index=idx,
                detail_page=pages["detail"],
            )

        if len(filtered) > visible_limit:
            remaining = len(filtered) - visible_limit
            if secondary_button(
                f"{t('btn_show_more')} ({remaining} more)",
                key="btn_show_more_matches",
            ):
                st.session_state["matches_visible_count"] = visible_limit + 5
                st.rerun()

    st.markdown('<div style="height:18px;"></div>', unsafe_allow_html=True)

    # Transparency Expanders at the bottom
    with st.expander(f"Not eligible ({len(ranked.not_eligible)}) — why these were excluded"):
        if not ranked.not_eligible:
            st.caption("None excluded by eligibility rules.")
        else:
            for ne in ranked.not_eligible:
                reasons_str = "; ".join(ne.get("reasons") or ["Criteria not met"])
                st.markdown(f"- **{ne.get('name')}** ({ne.get('provider')}): *{reasons_str}*")

    with st.expander(f"Recently closed ({len(ranked.closed_recently)}) — opens again next year"):
        if not ranked.closed_recently:
            st.caption("No scholarships closed in the last 30 days.")
        else:
            for cl in ranked.closed_recently:
                st.markdown(
                    f"- **{cl.get('name')}** ({cl.get('provider')}) — closed `{cl.get('deadline_iso')}` "
                    f"({cl.get('days_since_closed')} days ago)."
                )


render()
