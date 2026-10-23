"""
ui/theme.py — Design Tokens & Global Dark-Theme CSS for ScholarMatch.

Injects CSS variables, Google Fonts (Plus Jakarta Sans, Inter, Noto Nastaliq Urdu),
component styles, staggered animations, skeleton shimmer, and Streamlit overrides.
"""

from __future__ import annotations

import streamlit as st

THEME_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Noto+Nastaliq+Urdu:wght@400;700&family=Plus+Jakarta+Sans:wght@600;700&display=swap');

:root {
  --bg: #0B0D12;
  --surface: #12151C;
  --surface-2: #181C25;
  --border: rgba(255, 255, 255, 0.08);
  --border-hover: rgba(255, 255, 255, 0.16);
  --text: #F2F4F8;
  --text-muted: #9AA3B2;
  --text-faint: #6B7385;
  --primary: #7C5CFF;
  --primary-hover: #8E73FF;
  --primary-grad: linear-gradient(135deg, #7C5CFF 0%, #4F8CFF 100%);
  --accent: #2DD4BF;
  --success: #34D399;
  --warning: #FBBF24;
  --danger: #F87171;
  --info: #60A5FA;
  --radius-card: 16px;
  --radius-ctrl: 12px;
  --radius-pill: 999px;
}

/* Base & Layout */
html, body, .stApp {
  background-color: var(--bg) !important;
  color: var(--text) !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 16px;
  line-height: 1.6;
}
h1, h2, h3, h4, .sm-heading {
  font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
  letter-spacing: -0.02em;
  color: var(--text) !important;
}
.block-container {
  max-width: 760px !important;
  padding: 1.25rem 1rem 5.5rem 1rem !important;
  margin: 0 auto !important;
}
/* Hide default Streamlit chrome */
#MainMenu, header[data-testid="stHeader"], footer, [data-testid="stToolbar"] {
  display: none !important;
}
[data-testid="stSidebar"] {
  background-color: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}

/* Animations */
@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes shimmer {
  0% { background-position: -400px 0; }
  100% { background-position: 400px 0; }
}
@keyframes pulseUrgent {
  0%, 100% { box-shadow: 0 0 0 0 rgba(248, 113, 113, 0.35); }
  50% { box-shadow: 0 0 0 5px rgba(248, 113, 113, 0); }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}

/* Reusable Surfaces & Cards */
.sm-card {
  background: var(--surface);
  border: 1px solid var(--border);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04), 0 8px 24px rgba(0, 0, 0, 0.28);
  border-radius: var(--radius-card);
  padding: 20px 22px;
  margin-bottom: 16px;
  animation: fadeSlideUp 220ms ease-out both;
  transition: border-color 180ms ease-out, background-color 180ms ease-out;
}
.sm-card:hover {
  border-color: var(--border-hover);
}
.sm-hero {
  position: relative;
  background: radial-gradient(circle at 50% 0%, rgba(124, 92, 255, 0.14), transparent 70%), var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 40px 28px;
  text-align: center;
  margin: 12px 0 24px 0;
  animation: fadeSlideUp 240ms ease-out both;
}
.sm-hero h1 {
  font-size: 2.35rem;
  font-weight: 700;
  line-height: 1.18;
  margin: 12px 0 12px 0;
}
.sm-hero p {
  color: var(--text-muted);
  font-size: 1.05rem;
  max-width: 540px;
  margin: 0 auto 20px auto;
}

/* Badges & Chips */
.sm-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 11px;
  border-radius: var(--radius-pill);
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.sm-badge-eligible {
  background: rgba(52, 211, 153, 0.14);
  color: var(--success);
  border: 1px solid rgba(52, 211, 153, 0.32);
}
.sm-badge-maybe {
  background: rgba(251, 191, 36, 0.14);
  color: var(--warning);
  border: 1px solid rgba(251, 191, 36, 0.32);
}
.sm-badge-urgent {
  background: rgba(248, 113, 113, 0.16);
  color: var(--danger);
  border: 1px solid rgba(248, 113, 113, 0.4);
  animation: pulseUrgent 2.2s infinite;
}
.sm-badge-closed {
  background: rgba(154, 163, 178, 0.12);
  color: var(--text-muted);
  border: 1px solid var(--border);
}
.sm-badge-demo {
  background: rgba(124, 92, 255, 0.16);
  color: #B4A2FF;
  border: 1px solid rgba(124, 92, 255, 0.36);
}
.sm-chip-green { color: var(--success); background: rgba(52, 211, 153, 0.1); border: 1px solid rgba(52, 211, 153, 0.25); }
.sm-chip-amber { color: var(--warning); background: rgba(251, 191, 36, 0.1); border: 1px solid rgba(251, 191, 36, 0.25); }
.sm-chip-red { color: var(--danger); background: rgba(248, 113, 113, 0.12); border: 1px solid rgba(248, 113, 113, 0.3); }

/* Stat Tiles & Stepper */
.sm-stat-tile {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-card);
  padding: 16px 18px;
}
.sm-stat-num {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1.75rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1.15;
}
.sm-stat-label {
  color: var(--text-muted);
  font-size: 0.85rem;
  margin-top: 4px;
}
.sm-stepper-track {
  width: 100%;
  height: 6px;
  background: var(--surface-2);
  border-radius: var(--radius-pill);
  overflow: hidden;
  margin: 8px 0 20px 0;
}
.sm-stepper-fill {
  height: 100%;
  background: var(--primary-grad);
  border-radius: var(--radius-pill);
  transition: width 220ms ease-out;
}

/* Urdu RTL & Skeleton Loader */
.sm-urdu {
  direction: rtl;
  text-align: right;
  font-family: 'Noto Nastaliq Urdu', 'Jameel Noori Nastaleeq', serif;
  font-size: 1.12rem;
  line-height: 2.05;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-right: 3px solid var(--primary);
  border-radius: var(--radius-ctrl);
  padding: 16px 20px;
  color: var(--text);
}
.sm-skeleton-line {
  height: 14px;
  border-radius: 6px;
  background: linear-gradient(90deg, var(--surface) 25%, var(--surface-2) 50%, var(--surface) 75%);
  background-size: 800px 100%;
  animation: shimmer 1.6s infinite linear;
  margin-bottom: 10px;
}

/* Streamlit Widget Overrides */
.stButton > button, .stLinkButton > a, .stDownloadButton > button {
  min-height: 44px !important;
  border-radius: var(--radius-ctrl) !important;
  font-weight: 600 !important;
  font-size: 0.95rem !important;
  transition: transform 160ms ease-out, background 160ms ease-out, border-color 160ms ease-out !important;
}
.stButton > button[kind="primary"] {
  background: var(--primary-grad) !important;
  color: #FFFFFF !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(124, 92, 255, 0.28) !important;
}
.stButton > button[kind="primary"]:hover {
  transform: translateY(-1px);
  filter: brightness(1.06);
}
.stButton > button[kind="secondary"], .stLinkButton > a, .stDownloadButton > button {
  background: var(--surface-2) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}
.stButton > button:hover, .stLinkButton > a:hover, .stDownloadButton > button:hover {
  transform: translateY(-1px);
  border-color: var(--border-hover) !important;
}
.stButton > button:active {
  transform: scale(0.98);
}
.stButton > button:focus-visible, input:focus-visible, textarea:focus-visible {
  outline: 2px solid var(--primary) !important;
  outline-offset: 2px !important;
}
[data-testid="stForm"], [data-testid="stExpander"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-card) !important;
}
</style>
"""


def apply_theme() -> None:
    """Inject the global ScholarMatch CSS variables and component styles once per page."""
    if hasattr(st, "html"):
        st.html(THEME_CSS)
    else:
        st.markdown(THEME_CSS, unsafe_allow_html=True)
