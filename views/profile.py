"""
views/profile.py — 4-Step Student Profile Wizard for ScholarMatch.

One question group per step:
  - Step 1: Degree level + Province
  - Step 2: Academic marks (with optional "Scan my marksheet instead" shortcut)
  - Step 3: Monthly family income (slider + numeric input)
  - Step 4: Field of study + Scholarship preference -> "Show my matches"
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from llm import is_ai_configured
from profile_reader import read_marksheet
from ui.components import (
    inline_alert,
    primary_button,
    render_back_bar,
    secondary_button,
    section_header,
    skeleton_loader,
    stepper,
)
from ui.i18n import t

BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLES_DIR = BASE_DIR / "samples"

LEVEL_OPTIONS = ["intermediate", "undergraduate", "masters"]
PROVINCE_OPTIONS = [
    "Sindh",
    "Punjab",
    "KPK",
    "Balochistan",
    "Gilgit-Baltistan",
    "AJK",
    "Islamabad",
    "Other",
]
WANT_OPTIONS = ["any", "need_based", "merit_based", "study_abroad", "skills"]


def _income_range_label(income: int) -> str:
    """Return a friendly household income tier description."""
    if income <= 35000:
        return "Low income household — qualifies for almost all need-based programmes"
    if income <= 60000:
        return "Moderate-low income — qualifies for HEC, SEEF, and provincial need aid"
    if income <= 100000:
        return "Middle income — qualifies for merit and select need-cum-merit grants"
    return "Higher income — best matched with merit-based and study-abroad fellowships"


def render() -> None:
    """Render the 4-step Profile Wizard."""
    pages = st.session_state["pages"]
    step = int(st.session_state.get("wizard_step", 1))
    step = max(1, min(4, step))
    prof = st.session_state["profile"]

    if step == 1:
        render_back_bar(t("nav_home"), pages["home"], breadcrumb="Profile Setup")
    else:
        bcol1, bcol2 = st.columns([1.2, 2.8])
        with bcol1:
            if st.button(f"← {t('btn_back')}", key=f"wiz_top_back_{step}", type="secondary"):
                st.session_state["wizard_step"] = step - 1
                st.rerun()
        with bcol2:
            st.markdown(
                f'<div style="color:var(--text-faint);font-size:0.84rem;padding-top:10px;text-align:right;">Profile Setup • Step {step} of 4</div>',
                unsafe_allow_html=True,
            )

    stepper(current_step=step, total_steps=4)

    # =====================================================
    # STEP 1: Degree Level & Province
    # =====================================================
    if step == 1:
        section_header(
            "Where and what are you studying?",
            "We use your current degree level and domicile province to filter eligible programmes.",
            icon_name="compass",
        )
        lvl_idx = LEVEL_OPTIONS.index(prof["level"]) if prof.get("level") in LEVEL_OPTIONS else 1
        level_val = st.selectbox(
            "Current degree level",
            options=LEVEL_OPTIONS,
            index=lvl_idx,
            format_func=lambda x: x.title(),
        )

        prov_idx = (
            PROVINCE_OPTIONS.index(prof["province"])
            if prof.get("province") in PROVINCE_OPTIONS
            else 0
        )
        province_val = st.selectbox(
            "Domicile province / region",
            options=PROVINCE_OPTIONS,
            index=prov_idx,
        )

        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        if primary_button(t("btn_next"), key="step1_next"):
            prof["level"] = level_val
            prof["province"] = province_val
            st.session_state["wizard_step"] = 2
            st.rerun()

    # =====================================================
    # STEP 2: Academic Marks + Marksheet Vision Shortcut
    # =====================================================
    elif step == 2:
        section_header(
            "What are your recent exam marks?",
            "Enter your latest board percentage or university CGPA, or scan a photo of your marksheet.",
            icon_name="file-text",
        )

        with st.expander("Scan my marksheet instead (AI Vision shortcut)", expanded=False):
            uploaded = st.file_uploader(
                "Upload marksheet or transcript photo (PNG, JPG, WEBP)",
                type=["png", "jpg", "jpeg", "webp"],
            )
            sc1, sc2 = st.columns(2)
            sample_bytes: bytes | None = None
            sample_name = ""
            with sc1:
                if secondary_button("Try sample Intermediate card", key="s2_samp_int"):
                    p = SAMPLES_DIR / "sample_marksheet_intermediate.png"
                    if p.exists():
                        sample_bytes = p.read_bytes()
                        sample_name = p.name
            with sc2:
                if secondary_button("Try sample Undergrad transcript", key="s2_samp_ug"):
                    p = SAMPLES_DIR / "sample_marksheet_undergrad.png"
                    if p.exists():
                        sample_bytes = p.read_bytes()
                        sample_name = p.name

            target_bytes: bytes | None = None
            target_mime = "image/png"
            if uploaded is not None:
                target_bytes = uploaded.getvalue()
                target_mime = uploaded.type or "image/png"
                st.image(target_bytes, caption="Uploaded marksheet", width="stretch")
                if not secondary_button("Read marks from uploaded photo", key="s2_read_upload"):
                    target_bytes = None
            elif sample_bytes is not None:
                target_bytes = sample_bytes
                st.image(target_bytes, caption=f"Sample: {sample_name}", width="stretch")

            if target_bytes is not None:
                placeholder = st.empty()
                with placeholder.container():
                    skeleton_loader("Reading your marksheet...", lines=3)
                res = read_marksheet(target_bytes, mime=target_mime)
                if not res.get("ok") and not is_ai_configured() and sample_name:
                    if "intermediate" in sample_name:
                        res = {
                            "ok": True,
                            "level": "intermediate",
                            "percentage": 78.0,
                            "cgpa": None,
                            "board_or_university": "BISE Hyderabad (Sample)",
                            "year": "2025",
                            "confidence": "high",
                        }
                    else:
                        res = {
                            "ok": True,
                            "level": "undergraduate",
                            "percentage": 78.5,
                            "cgpa": 3.42,
                            "board_or_university": "University of Sindh (Sample)",
                            "year": "2026",
                            "confidence": "high",
                        }
                placeholder.empty()
                st.session_state["marksheet_result"] = res
                if res.get("ok"):
                    if res.get("level") in LEVEL_OPTIONS:
                        prof["level"] = res["level"]
                    if res.get("percentage") is not None:
                        prof["percentage"] = float(res["percentage"])
                    if res.get("cgpa") is not None:
                        prof["cgpa"] = float(res["cgpa"])

            ms = st.session_state.get("marksheet_result")
            if ms:
                if ms.get("ok"):
                    inline_alert(
                        f"Read marksheet from {ms.get('board_or_university') or 'document'} "
                        f"(confidence: {str(ms.get('confidence', 'medium')).upper()}). You can edit the numbers below.",
                        kind="success",
                    )
                else:
                    inline_alert(
                        ms.get("error") or "Could not read marksheet clearly. Please enter your marks below.",
                        kind="warning",
                    )

        pct_default = float(prof["percentage"]) if prof.get("percentage") is not None else 78.0
        pct_val = st.number_input(
            "Percentage marks (0 to 100)",
            min_value=0.0,
            max_value=100.0,
            value=pct_default,
            step=0.5,
            help="Enter marks between 0 and 100.",
        )

        cgpa_default = float(prof["cgpa"]) if prof.get("cgpa") is not None else 0.0
        cgpa_val = st.number_input(
            "University CGPA on a 4.0 scale (leave 0 if Intermediate)",
            min_value=0.0,
            max_value=4.0,
            value=cgpa_default,
            step=0.05,
        )

        if pct_val <= 0 and cgpa_val <= 0:
            inline_alert("Enter a percentage between 1 and 100 or a CGPA up to 4.0.", kind="warning")

        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        if primary_button(t("btn_next"), key="step2_next"):
            prof["percentage"] = float(pct_val) if pct_val > 0 else None
            prof["cgpa"] = float(cgpa_val) if cgpa_val > 0 else None
            st.session_state["wizard_step"] = 3
            st.rerun()

    # =====================================================
    # STEP 3: Monthly Family Income
    # =====================================================
    elif step == 3:
        section_header(
            "What is your family's monthly income?",
            "Many Pakistani scholarships reserve funding for households below a monthly PKR ceiling.",
            icon_name="shield",
        )

        current_inc = int(prof.get("monthly_income_pkr") or 35000)
        slider_inc = st.slider(
            "Monthly family income (PKR)",
            min_value=0,
            max_value=250000,
            value=min(current_inc, 250000),
            step=2500,
            format="PKR %d",
        )
        exact_inc = st.number_input(
            "Or type exact monthly income (PKR)",
            min_value=0,
            max_value=5000000,
            value=slider_inc,
            step=1000,
        )

        st.caption(f"Range guide: {_income_range_label(int(exact_inc))}")
        inline_alert("Used only on this device session. Never stored.", kind="info")

        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        if primary_button(t("btn_next"), key="step3_next"):
            prof["monthly_income_pkr"] = int(exact_inc)
            st.session_state["wizard_step"] = 4
            st.rerun()

    # =====================================================
    # STEP 4: Field of Study & Scholarship Preference
    # =====================================================
    else:
        section_header(
            "What field and scholarship type do you want?",
            "Almost done. Tell us your major and what kind of support you prefer.",
            icon_name="sparkles",
        )

        field_val = st.text_input(
            "Field of study or subject group",
            value=str(prof.get("field") or "Computer Science"),
            placeholder="e.g., Computer Science, Pre-Engineering, MBBS, Business",
        )

        want_idx = WANT_OPTIONS.index(prof["want"]) if prof.get("want") in WANT_OPTIONS else 0
        want_val = st.selectbox(
            "What type of scholarship are you looking for?",
            options=WANT_OPTIONS,
            index=want_idx,
            format_func=lambda x: "Any open scholarship" if x == "any" else x.replace("_", " ").title(),
        )

        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        if primary_button(t("btn_show_matches"), key="step4_finish"):
            prof["field"] = field_val.strip() or "all"
            prof["want"] = want_val
            st.session_state["profile_completed"] = True
            st.session_state["matches_visible_count"] = 5
            st.switch_page(pages["matches"])


render()
