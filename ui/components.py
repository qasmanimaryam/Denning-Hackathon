"""
ui/components.py — Reusable Dark-Theme UI Components for ScholarMatch.

Provides accessible, WCAG AA compliant components using inline Lucide-style SVG
icons (never relying on colour alone), staggered entrance animations, skeleton
shimmers, and clean card layouts.
"""

from __future__ import annotations

import hashlib
import html
import json
from typing import Any

import streamlit as st

from llm import is_ai_configured
from ui.i18n import is_urdu, t

ICONS: dict[str, str] = {
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "alert": '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
    "help": '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "x": '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "flame": '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
    "sparkles": '<path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "compass": '<circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>',
    "file-text": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>',
    "link": '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    "arrow-left": '<line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>',
}


def icon_svg(name: str, size: int = 15, color: str = "currentColor") -> str:
    """Return an inline SVG string for a named Lucide line icon."""
    path = ICONS.get(name, ICONS["sparkles"])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px;flex-shrink:0;">'
        f"{path}</svg>"
    )


def primary_button(label: str, key: str, stretch: bool = True) -> bool:
    """Render the single primary action button for a screen."""
    return st.button(
        label,
        key=key,
        type="primary",
        width="stretch" if stretch else "content",
    )


def secondary_button(label: str, key: str, stretch: bool = True) -> bool:
    """Render a ghost / secondary surface action button."""
    return st.button(
        label,
        key=key,
        type="secondary",
        width="stretch" if stretch else "content",
    )


def icon_button(icon_name: str, label: str, key: str, stretch: bool = False) -> bool:
    """Render a secondary button prefixed with a clean label."""
    _ = icon_name
    return st.button(
        label,
        key=key,
        type="secondary",
        width="stretch" if stretch else "content",
    )


def badge_html(label: str, variant: str = "eligible") -> str:
    """
    Build an accessible pill badge containing both an SVG icon and text label.
    Variants: 'eligible' | 'maybe' | 'urgent' | 'closed' | 'demo'
    """
    variant_map = {
        "eligible": ("sm-badge-eligible", "check"),
        "maybe": ("sm-badge-maybe", "help"),
        "urgent": ("sm-badge-urgent", "flame"),
        "closed": ("sm-badge-closed", "clock"),
        "demo": ("sm-badge-demo", "sparkles"),
    }
    css_cls, ic_name = variant_map.get(variant, ("sm-badge-closed", "clock"))
    return f'<span class="sm-badge {css_cls}">{icon_svg(ic_name, 13)}<span>{html.escape(label)}</span></span>'


def badge(label: str, variant: str = "eligible") -> None:
    """Render a standalone badge via st.markdown."""
    st.markdown(badge_html(label, variant), unsafe_allow_html=True)


def days_left_chip_html(days_left: int | None) -> str:
    """
    Render a days-left chip whose colour shifts by urgency:
    green (>14d), amber (4-14d), red (<=3d), or muted if unknown.
    """
    if days_left is None:
        return f'<span class="sm-badge sm-badge-closed">{icon_svg("clock", 13)}<span>Date unconfirmed</span></span>'
    if days_left < 0:
        return f'<span class="sm-badge sm-badge-closed">{icon_svg("clock", 13)}<span>Closed</span></span>'
    if days_left <= 3:
        cls = "sm-badge sm-chip-red"
        ic = "flame"
    elif days_left <= 14:
        cls = "sm-badge sm-chip-amber"
        ic = "clock"
    else:
        cls = "sm-badge sm-chip-green"
        ic = "clock"
    text = f"{days_left}d left" if days_left > 0 else "Closes today"
    return f'<span class="{cls}">{icon_svg(ic, 13)}<span>{text}</span></span>'


def stat_tile(value: str | int, label: str, color: str = "var(--text)") -> None:
    """Render a minimal stat tile (tabular figure + muted label)."""
    st.markdown(
        f"""
        <div class="sm-stat-tile">
            <div class="sm-stat-num" style="color:{color};">{html.escape(str(value))}</div>
            <div class="sm-stat-label">{html.escape(label)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def stepper(current_step: int, total_steps: int, label: str = "") -> None:
    """Render a smooth progress bar and step counter for the Profile Wizard."""
    pct = max(5, min(100, int((current_step / max(1, total_steps)) * 100)))
    step_text = label or t("wizard_step_of", step=current_step, total=total_steps)
    st.markdown(
        f"""
        <div style="display:flex;justify-content:space-between;align-items:center;font-size:0.85rem;color:var(--text-muted);margin-top:4px;">
            <span style="font-weight:600;color:var(--text);">{html.escape(step_text)}</span>
            <span style="font-variant-numeric:tabular-nums;">{pct}%</span>
        </div>
        <div class="sm-stepper-track">
            <div class="sm-stepper-fill" style="width:{pct}%;"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, description: str = "", icon_name: str | None = None) -> None:
    """Render a clean page or section header (title + one-line muted helper text)."""
    ic_html = f'<span style="color:var(--primary);margin-right:8px;">{icon_svg(icon_name, 22)}</span>' if icon_name else ""
    dir_attr = 'dir="rtl" style="text-align:right;"' if is_urdu() else ""
    desc_html = (
        f'<p style="color:var(--text-muted);font-size:0.98rem;margin:4px 0 18px 0;">{html.escape(description)}</p>'
        if description
        else '<div style="height:10px;"></div>'
    )
    st.markdown(
        f"""
        <div {dir_attr}>
            <h1 style="font-size:1.75rem;font-weight:700;margin:4px 0 2px 0;display:flex;align-items:center;">
                {ic_html}<span>{html.escape(title)}</span>
            </h1>
            {desc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def card(content_html: str, header_html: str = "", footer_html: str = "", delay_ms: int = 0) -> None:
    """Render a glass-depth dark surface card with optional header and footer."""
    anim_style = f"animation-delay: {min(delay_ms, 240)}ms;" if delay_ms > 0 else ""
    hdr = f'<div style="margin-bottom:10px;">{header_html}</div>' if header_html else ""
    ftr = f'<div style="margin-top:14px;padding-top:12px;border-top:1px solid var(--border);">{footer_html}</div>' if footer_html else ""
    st.markdown(
        f'<div class="sm-card" style="{anim_style}">{hdr}{content_html}{ftr}</div>',
        unsafe_allow_html=True,
    )


def empty_state(
    icon_name: str,
    headline: str,
    helper_text: str,
    action_label: str | None = None,
    action_key: str | None = None,
) -> bool:
    """Render a calm empty state card with an optional primary CTA."""
    st.markdown(
        f"""
        <div class="sm-card" style="text-align:center;padding:36px 24px;">
            <div style="color:var(--primary);margin-bottom:10px;">{icon_svg(icon_name, 28)}</div>
            <div class="sm-heading" style="font-size:1.15rem;font-weight:600;margin-bottom:6px;">
                {html.escape(headline)}
            </div>
            <div style="color:var(--text-muted);font-size:0.92rem;max-width:420px;margin:0 auto;">
                {html.escape(helper_text)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if action_label and action_key:
        return primary_button(action_label, key=action_key)
    return False


def skeleton_loader(message: str = "Working...", lines: int = 3) -> None:
    """Render shimmering placeholder bars with a friendly human status message."""
    widths = ["92%", "78%", "64%", "85%"]
    bars = "".join(
        f'<div class="sm-skeleton-line" style="width:{widths[i % len(widths)]};"></div>'
        for i in range(lines)
    )
    st.markdown(
        f"""
        <div class="sm-card">
            <div style="display:flex;align-items:center;gap:8px;color:var(--text-muted);font-size:0.88rem;margin-bottom:14px;">
                <span style="color:var(--primary);">{icon_svg("sparkles", 15)}</span>
                <span>{html.escape(message)}</span>
            </div>
            {bars}
        </div>
        """,
        unsafe_allow_html=True,
    )


def inline_alert(message: str, kind: str = "info") -> None:
    """Render a clean inline alert banner (info, success, warning, error)."""
    palette = {
        "info": ("var(--info)", "rgba(96, 165, 250, 0.10)", "rgba(96, 165, 250, 0.28)", "alert"),
        "success": ("var(--success)", "rgba(52, 211, 153, 0.10)", "rgba(52, 211, 153, 0.28)", "check"),
        "warning": ("var(--warning)", "rgba(251, 191, 36, 0.10)", "rgba(251, 191, 36, 0.28)", "alert"),
        "error": ("var(--danger)", "rgba(248, 113, 113, 0.12)", "rgba(248, 113, 113, 0.32)", "x"),
    }
    col, bg, bdr, ic = palette.get(kind, palette["info"])
    st.markdown(
        f"""
        <div style="background:{bg};border:1px solid {bdr};border-radius:var(--radius-ctrl);padding:12px 16px;margin:10px 0;display:flex;align-items:flex-start;gap:10px;">
            <span style="color:{col};margin-top:2px;">{icon_svg(ic, 16)}</span>
            <span style="color:var(--text);font-size:0.92rem;line-height:1.5;">{html.escape(message)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_speech_button(text: str, lang: str, key_id: str) -> None:
    """Render a dark-surface browser speechSynthesis button (`ur-PK` or `en-US`) using `st.iframe`."""
    if not text:
        return
    voice_lang = "ur-PK" if str(lang).strip().lower() in ("urdu", "ur") else "en-US"
    btn_label = "Listen in Urdu" if voice_lang == "ur-PK" else "Listen aloud"
    escaped_js_text = json.dumps(text)
    safe_id = hashlib.md5(key_id.encode("utf-8")).hexdigest()[:10]

    snippet = f"""<!DOCTYPE html>
    <html>
    <body style="margin:0;padding:0;background:#0B0D12;color:#F2F4F8;">
    <div style="display:flex;align-items:center;gap:8px;margin:2px 0;">
      <button id="spk_{safe_id}" style="
          background:#181C25;
          color:#F2F4F8;
          border:1px solid rgba(255,255,255,0.10);
          border-radius:10px;
          padding:6px 13px;
          font-family:Inter,sans-serif;
          font-size:12.5px;
          font-weight:600;
          cursor:pointer;">
        {btn_label}
      </button>
      <button id="stop_{safe_id}" style="
          background:#12151C;
          color:#9AA3B2;
          border:1px solid rgba(255,255,255,0.08);
          border-radius:10px;
          padding:6px 10px;
          font-family:Inter,sans-serif;
          font-size:12px;
          cursor:pointer;">
        Stop
      </button>
      <span id="status_{safe_id}" style="font-family:Inter,sans-serif;font-size:12px;color:#2DD4BF;"></span>
    </div>
    <script>
      const btn = document.getElementById("spk_{safe_id}");
      const stopBtn = document.getElementById("stop_{safe_id}");
      const statusEl = document.getElementById("status_{safe_id}");
      btn.onclick = function() {{
        if (!('speechSynthesis' in window)) {{
          statusEl.innerText = "Audio not supported on this browser.";
          return;
        }}
        window.speechSynthesis.cancel();
        const utter = new SpeechSynthesisUtterance({escaped_js_text});
        utter.lang = "{voice_lang}";
        utter.rate = 0.95;
        utter.onstart = () => {{ statusEl.innerText = "Playing..."; }};
        utter.onend = () => {{ statusEl.innerText = ""; }};
        utter.onerror = () => {{ statusEl.innerText = "Voice unavailable on this device."; }};
        window.speechSynthesis.speak(utter);
      }};
      stopBtn.onclick = function() {{
        if ('speechSynthesis' in window) {{
          window.speechSynthesis.cancel();
          statusEl.innerText = "";
        }}
      }};
    </script>
    </body>
    </html>
    """
    if hasattr(st, "iframe"):
        st.iframe(snippet, height=40)
    else:
        import streamlit.components.v1 as components

        components.html(snippet, height=40)


def scholarship_card(
    match: dict[str, Any],
    one_line_reason: str,
    index: int = 0,
    detail_page: Any = None,
) -> None:
    """
    Render a Scholarship Match Card following Section 5 specs:
      - Left: name and provider; Right: status badge (+ Demo badge if demo_)
      - Middle row: benefits line + days-left chip (green >14, amber 4-14, red <=3)
      - Bottom: one-line reason, then 'View details' and 'Official site' buttons.
    """
    sch_id = str(match.get("id") or "")
    is_demo = sch_id.startswith("demo_")
    status = match.get("status", "maybe")
    days_left = match.get("days_left")
    delay_ms = min(index * 40, 240)

    badges = ""
    if is_demo:
        badges += badge_html("Demo", "demo") + " "
    if status == "yes":
        badges += badge_html("Eligible", "eligible")
    else:
        badges += badge_html("Maybe", "maybe")

    benefits = match.get("benefits") or f"{str(match.get('funding') or 'Partial').title()} funding"
    chip_html = days_left_chip_html(days_left)

    st.markdown(
        f"""
        <div class="sm-card" style="animation-delay:{delay_ms}ms;margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap;">
                <div>
                    <div class="sm-heading" style="font-size:1.12rem;font-weight:700;color:var(--text);">
                        {html.escape(str(match.get("name", "")))}
                    </div>
                    <div style="color:var(--text-muted);font-size:0.88rem;margin-top:2px;">
                        {html.escape(str(match.get("provider", "")))}
                    </div>
                </div>
                <div style="display:flex;gap:6px;align-items:center;">{badges}</div>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin:14px 0 10px 0;padding:10px 12px;background:var(--surface-2);border-radius:10px;">
                <span style="font-size:0.9rem;color:var(--text);font-weight:500;">{html.escape(str(benefits))}</span>
                {chip_html}
            </div>
            <div style="color:var(--text-muted);font-size:0.9rem;line-height:1.5;">
                {html.escape(one_line_reason)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1.3, 1])
    with c1:
        if st.button(
            t("btn_view_details"),
            key=f"view_det_{sch_id}_{index}",
            type="secondary",
            width="stretch",
        ):
            st.session_state["selected_scholarship_id"] = sch_id
            if detail_page is not None:
                st.switch_page(detail_page)
    with c2:
        src_url = match.get("apply_url") or match.get("source_url")
        if src_url and str(src_url).startswith("http"):
            st.link_button(t("btn_official_site"), str(src_url), width="stretch")
        else:
            st.button("Campus FAO", disabled=True, key=f"no_url_{sch_id}_{index}", width="stretch")

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)


def render_top_nav(pages: dict[str, Any], active_key: str) -> None:
    """
    Render the slim top bar:
      - Brand logo ('ScholarMatch') + live AI connection dot on left
      - 4 primary nav items: Home, Find, Link checker, Checklist + EN/اردو toggle.
    """
    ai_ok = is_ai_configured()
    dot_col = "#34D399" if ai_ok else "#FBBF24"
    ai_label = "AI Live" if ai_ok else "Rules Only"

    checklist_count = len(st.session_state.get("checklist_ids", []))
    chk_text = f"{t('nav_checklist')} ({checklist_count})" if checklist_count else t("nav_checklist")

    st.markdown(
        f"""
        <div style="display:flex;justify-content:space-between;align-items:center;padding:4px 0 12px 0;border-bottom:1px solid var(--border);margin-bottom:14px;">
            <div style="display:flex;align-items:center;gap:10px;">
                <span style="width:10px;height:10px;border-radius:50%;background:var(--primary);display:inline-block;box-shadow:0 0 10px var(--primary);"></span>
                <span class="sm-heading" style="font-size:1.15rem;font-weight:700;">{html.escape(t("app_name"))}</span>
            </div>
            <div style="display:flex;align-items:center;gap:6px;font-size:0.75rem;color:var(--text-muted);background:var(--surface);padding:4px 10px;border-radius:999px;border:1px solid var(--border);">
                <span style="width:7px;height:7px;border-radius:50%;background:{dot_col};display:inline-block;"></span>
                <span>{ai_label}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ncol1, ncol2, ncol3, ncol4, ncol5 = st.columns([1, 1, 1.25, 1.2, 0.85])
    with ncol1:
        if st.button(
            t("nav_home"),
            key="topnav_home",
            type="secondary",
            width="stretch",
        ):
            st.switch_page(pages["home"])
    with ncol2:
        if st.button(
            t("nav_find"),
            key="topnav_find",
            type="secondary",
            width="stretch",
        ):
            target = pages["matches"] if st.session_state.get("profile_completed") else pages["profile"]
            st.switch_page(target)
    with ncol3:
        if st.button(
            t("nav_link"),
            key="topnav_link",
            type="secondary",
            width="stretch",
        ):
            st.switch_page(pages["link_checker"])
    with ncol4:
        if st.button(
            chk_text,
            key="topnav_chk",
            type="secondary",
            width="stretch",
        ):
            st.switch_page(pages["checklist"])
    with ncol5:
        cur_lang = st.session_state.get("lang", "English")
        toggle_lbl = "اردو" if cur_lang == "English" else "EN"
        if st.button(toggle_lbl, key="topnav_lang", type="secondary", width="stretch"):
            st.session_state["lang"] = "Urdu" if cur_lang == "English" else "English"
            st.rerun()

    _ = active_key


def render_back_bar(label: str, target_page: Any, breadcrumb: str = "") -> None:
    """Render a visible Back button and breadcrumb on every non-Home page."""
    bcol1, bcol2 = st.columns([1.2, 2.8])
    with bcol1:
        if st.button(f"← {label}", key=f"back_btn_{label}_{breadcrumb}", type="secondary"):
            st.switch_page(target_page)
    with bcol2:
        if breadcrumb:
            st.markdown(
                f'<div style="color:var(--text-faint);font-size:0.84rem;padding-top:10px;text-align:right;">{html.escape(breadcrumb)}</div>',
                unsafe_allow_html=True,
            )


def render_footer(about_page: Any, last_refreshed: str) -> None:
    """Render the footer with the About & AI Status page link and mandatory disclaimer."""
    st.markdown(
        f"""
        <div style="margin-top:40px;padding-top:18px;border-top:1px solid var(--border);color:var(--text-faint);font-size:0.82rem;line-height:1.5;">
            <div style="margin-bottom:8px;color:var(--text-muted);">
                {html.escape(t("disclaimer"))}
            </div>
            <div>Data last refreshed: {html.escape(last_refreshed)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    fcol1, fcol2 = st.columns([1.4, 2.6])
    with fcol1:
        if st.button(t("nav_about"), key="footer_about_btn", type="secondary"):
            st.switch_page(about_page)
    with fcol2:
        st.caption("ScholarMatch — Built for Pakistani students. Session-only memory.")
