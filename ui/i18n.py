"""
ui/i18n.py — Bilingual Interface Strings (English & Urdu) for ScholarMatch.
"""

from __future__ import annotations

import streamlit as st

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "app_name": "ScholarMatch",
        "tagline": "Open scholarships matched by rules, explained by AI.",
        "nav_home": "Home",
        "nav_find": "Find",
        "nav_link": "Link checker",
        "nav_checklist": "Checklist",
        "nav_about": "About & API status",
        "hero_title": "Find the scholarships that are open for you, right now.",
        "hero_sub": "Enter your marks and province in four quick steps to see verified scholarships you actually qualify for.",
        "cta_find": "Find my scholarships",
        "cta_link_secondary": "Check a scholarship link",
        "trust_1_title": "Open now",
        "trust_1_desc": "Expired deadlines are filtered out automatically.",
        "trust_2_title": "Rules by code, explained by AI",
        "trust_2_desc": "Python checks your eligibility; AI explains it simply.",
        "trust_3_title": "Free, nothing stored",
        "trust_3_desc": "Your profile stays in this tab only and is never saved.",
        "wizard_step_of": "Step {step} of {total}",
        "btn_back": "Back",
        "btn_next": "Continue",
        "btn_show_matches": "Show my matches",
        "btn_load_demo": "Load demo student",
        "matches_title": "Your scholarship matches",
        "matches_sub": "Ranked by eligibility, funding coverage, and deadline urgency.",
        "stat_open": "Open for you",
        "stat_confirm": "To confirm",
        "stat_urgent": "Closing this week",
        "filter_all": "All",
        "filter_eligible": "Eligible",
        "filter_urgent": "Closing soon",
        "btn_view_details": "View details",
        "btn_official_site": "Official site",
        "btn_show_more": "Show more scholarships",
        "detail_back": "Back to matches",
        "tab_overview": "Overview",
        "tab_requirements": "Requirements",
        "tab_documents": "Documents checklist",
        "btn_apply_official": "Apply on official site",
        "btn_write_app": "Write my application",
        "draft_title": "Write your application draft",
        "draft_sub": "Add a few personal notes and get a sincere email or statement of purpose.",
        "btn_generate_draft": "Write my draft",
        "btn_regenerate": "Regenerate",
        "draft_review_note": "Review and personalise before sending.",
        "link_title": "Check any scholarship link",
        "link_sub": "Paste an official scholarship URL or announcement text to verify deadlines and your eligibility.",
        "btn_check_link": "Check scholarship",
        "checklist_title": "Your checklist & timeline",
        "checklist_sub": "Track documents and upcoming deadlines for the scholarships you saved.",
        "about_title": "About ScholarMatch & AI Status",
        "about_sub": "How eligibility rules, data sources, and the live AI connection work.",
        "disclaimer": "Guidance only. Confirm deadlines and eligibility on the official website. No scholarship requires payment to an agent.",
    },
    "ur": {
        "app_name": "ScholarMatch | اسکالر میچ",
        "tagline": "قواعد کے مطابق تصدیق شدہ وظائف، مصنوعی ذہانت کی آسان وضاحت کے ساتھ۔",
        "nav_home": "ہوم",
        "nav_find": "تلاش کریں",
        "nav_link": "لنک چیکر",
        "nav_checklist": "چیک لسٹ",
        "nav_about": "معلومات اور اے آئی اسٹیٹس",
        "hero_title": "وہ اسکالرشپس تلاش کریں جو اس وقت آپ کے لیے کھلی ہیں۔",
        "hero_sub": "چار آسان مراحل میں اپنی تعلیمی تفصیلات درج کریں اور اپنے پروفائل کے مطابق کھلے وظائف دیکھیں۔",
        "cta_find": "میری اسکالرشپس تلاش کریں",
        "cta_link_secondary": "اسکالرشپ کا لنک چیک کریں",
        "trust_1_title": "اس وقت کھلے وظائف",
        "trust_1_desc": "ختم شدہ تاریخ والے وظائف خودکار طور پر ہٹا دیے جاتے ہیں۔",
        "trust_2_title": "فیصلہ کوڈ سے، وضاحت اے آئی سے",
        "trust_2_desc": "اہلیت کی جانچ پائتھن کوڈ کرتا ہے، اے آئی آسان زبان میں سمجھاتی ہے۔",
        "trust_3_title": "مکمل مفت اور محفوظ",
        "trust_3_desc": "آپ کا ڈیٹا کہیں محفوظ نہیں کیا جاتا۔",
        "wizard_step_of": "مرحلہ {step} از {total}",
        "btn_back": "واپس",
        "btn_next": "آگے بڑھیں",
        "btn_show_matches": "میری اسکالرشپس دکھائیں",
        "btn_load_demo": "ڈیمو اسٹوڈنٹ لوڈ کریں",
        "matches_title": "آپ کے لیے موزوں اسکالرشپس",
        "matches_sub": "اہلیت، فنڈنگ اور آخری تاریخ کے لحاظ سے ترتیب شدہ۔",
        "stat_open": "آپ کے لیے موزوں",
        "stat_confirm": "تصدیق طلب",
        "stat_urgent": "اس ہفتے بند ہونے والی",
        "filter_all": "تمام",
        "filter_eligible": "مکمل اہل",
        "filter_urgent": "جلد بند ہونے والی",
        "btn_view_details": "تفصیلات دیکھیں",
        "btn_official_site": "سرکاری ویب سائٹ",
        "btn_show_more": "مزید اسکالرشپس دکھائیں",
        "detail_back": "واپس نتائج پر",
        "tab_overview": "جائزہ",
        "tab_requirements": "شرائط",
        "tab_documents": "کاغذات کی فہرست",
        "btn_apply_official": "سرکاری ویب سائٹ پر اپلائی کریں",
        "btn_write_app": "درخواست لکھیں",
        "draft_title": "اپنی اسکالرشپ درخواست تیار کریں",
        "draft_sub": "اپنے بارے میں چند نکات لکھیں اور بہترین درخواست کا مسودہ حاصل کریں۔",
        "btn_generate_draft": "میری درخواست لکھیں",
        "btn_regenerate": "دوبارہ لکھیں",
        "draft_review_note": "بھیجنے سے پہلے خالی جگہوں [...] کو اپنی تفصیلات سے پر کریں۔",
        "link_title": "کوئی بھی اسکالرشپ لنک یا اشتہار چیک کریں",
        "link_sub": "کسی بھی اسکالرشپ کا لنک یا متن پیسٹ کریں اور فوری اہلیت جانیں۔",
        "btn_check_link": "اسکالرشپ چیک کریں",
        "checklist_title": "آپ کی کاغذات کی فہرست اور تاریخیں",
        "checklist_sub": "اپنی منتخب کردہ اسکالرشپس کے کاغذات اور آخری تاریخوں کو ٹریک کریں۔",
        "about_title": "اسکالر میچ اور اے آئی اسٹیٹس",
        "about_sub": "یہ ایپ کیسے کام کرتی ہے اور لائیو اے آئی کنکشن کی صورتحال۔",
        "disclaimer": "صرف رہنمائی کے لیے۔ آخری تاریخ اور اہلیت کی تصدیق ہمیشہ سرکاری ویب سائٹ پر کریں۔ کسی بھی ایجنٹ کو پیسے نہ دیں۔",
    },
}


def get_lang_code() -> str:
    """Return `'ur'` when Urdu mode is active in session state, else `'en'`."""
    lang = str(st.session_state.get("lang", "English")).strip().lower()
    return "ur" if lang in ("urdu", "ur", "اردو") else "en"


def is_urdu() -> bool:
    """Return True if the active UI language is Urdu."""
    return get_lang_code() == "ur"


def t(key: str, **kwargs: object) -> str:
    """Translate a UI string key into the active session language (`en` or `ur`)."""
    code = get_lang_code()
    template = STRINGS.get(code, STRINGS["en"]).get(key) or STRINGS["en"].get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template
