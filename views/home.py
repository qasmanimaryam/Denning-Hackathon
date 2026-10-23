"""
views/home.py — Home Page for ScholarMatch (One Feature: Value Prop & Entry CTA).
"""

from __future__ import annotations

import html

import streamlit as st

from ui.components import badge_html, icon_svg, primary_button, secondary_button
from ui.i18n import is_urdu, t


def render() -> None:
    """Render the ScholarMatch Home screen."""
    pages = st.session_state["pages"]
    dir_style = 'dir="rtl"' if is_urdu() else ""

    # Hero Card with radial glow
    st.markdown(
        f"""
        <div class="sm-hero" {dir_style}>
            <div>{badge_html(t("tagline"), "demo")}</div>
            <h1>{html.escape(t("hero_title"))}</h1>
            <p>{html.escape(t("hero_sub"))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Single obvious primary CTA
    if primary_button(t("cta_find"), key="home_primary_find"):
        st.session_state["wizard_step"] = 1
        st.switch_page(pages["profile"])

    # Tiny secondary actions row
    sc1, sc2 = st.columns(2)
    with sc1:
        if secondary_button(t("cta_link_secondary"), key="home_sec_link"):
            st.switch_page(pages["link_checker"])
    with sc2:
        if secondary_button(t("btn_load_demo"), key="home_load_demo"):
            st.session_state["profile"] = {
                "level": "undergraduate",
                "province": "Sindh",
                "percentage": 78.0,
                "cgpa": 3.42,
                "monthly_income_pkr": 35000,
                "field": "Computer Science",
                "want": "need_based",
            }
            st.session_state["profile_completed"] = True
            st.switch_page(pages["matches"])

    st.markdown('<div style="height:18px;"></div>', unsafe_allow_html=True)

    # 3 Icon Trust Tiles
    t1, t2, t3 = st.columns(3)
    tiles = [
        (t1, "clock", t("trust_1_title"), t("trust_1_desc")),
        (t2, "sparkles", t("trust_2_title"), t("trust_2_desc")),
        (t3, "shield", t("trust_3_title"), t("trust_3_desc")),
    ]
    for col, ic, title, desc in tiles:
        with col:
            st.markdown(
                f"""
                <div class="sm-card" style="padding:18px;min-height:132px;">
                    <div style="color:var(--primary);margin-bottom:8px;">{icon_svg(ic, 20)}</div>
                    <div class="sm-heading" style="font-size:0.96rem;font-weight:600;margin-bottom:4px;">
                        {html.escape(title)}
                    </div>
                    <div style="color:var(--text-muted);font-size:0.84rem;line-height:1.45;">
                        {html.escape(desc)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


render()
