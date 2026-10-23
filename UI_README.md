# ScholarMatch — UI Architecture & Design System (`UI_README.md`)

> **Brand:** **ScholarMatch** — *"Open scholarships matched by rules, explained by AI."*  
> **Design Philosophy:** One feature per page, Linear/Vercel/Arc-inspired dark mode, WCAG AA contrast, progressive disclosure, and mobile-first ergonomics.

---

## 1. Visual Design Tokens (`ui/theme.py` & `.streamlit/config.toml`)

All visual tokens are defined once as CSS variables in [`ui/theme.py`](file:///c:/Users/FI/Desktop/AI%20HACKATHON%20DENNUNG/ui/theme.py) and mirrored in [`.streamlit/config.toml`](file:///c:/Users/FI/Desktop/AI%20HACKATHON%20DENNUNG/.streamlit/config.toml):

| Token | Value | Purpose |
|---|---|---|
| `--bg` | `#0B0D12` | Primary page background |
| `--surface` | `#12151C` | Elevated card surface |
| `--surface-2` | `#181C25` | Raised / hover / nested surface |
| `--border` | `rgba(255, 255, 255, 0.08)` | Hairline glass border |
| `--text` | `#F2F4F8` | Primary high-contrast body & heading text |
| `--text-muted` | `#9AA3B2` | Secondary descriptions & labels |
| `--text-faint` | `#6B7385` | Breadcrumbs, timestamps & captions |
| `--primary` | `#7C5CFF` | Primary violet accent (`--primary-hover: #8E73FF`) |
| `--accent` | `#2DD4BF` | Positive teal highlight |
| `--success` / `--warning` / `--danger` | `#34D399` / `#FBBF24` / `#F87171` | Semantic status colours (always paired with an inline SVG icon + word) |

### Typography & Spacing
- **Headings:** `Plus Jakarta Sans` (`600–700`, `-0.02em` tracking)
- **Body:** `Inter` (`16px` base, `1.6` line-height, `tabular-nums` for counts and days left)
- **Urdu (RTL):** `Noto Nastaliq Urdu` (`dir="rtl"`, `line-height: 2.05`, right-aligned)
- **Layout:** `760px` centred max-width, `16px` card radius, `12px` control radius, `999px` pill badges.

---

## 2. Information Architecture (One Feature Per Page)

All 8 screens live in `views/` and are registered via `st.navigation` + `st.Page` in [`app.py`](file:///c:/Users/FI/Desktop/AI%20HACKATHON%20DENNUNG/app.py):

1. [`views/home.py`](file:///c:/Users/FI/Desktop/AI%20HACKATHON%20DENNUNG/views/home.py) — Hero value proposition, single primary CTA (`"Find my scholarships"`), and 3 icon trust tiles.
2. [`views/profile.py`](file:///c:/Users/FI/Desktop/AI%20HACKATHON%20DENNUNG/views/profile.py) — 4-step wizard (`Step 1` Degree & Province → `Step 2` Marks & Marksheet Vision Scanner → `Step 3` Family Income Slider → `Step 4` Field & Preference).
3. [`views/matches.py`](file:///c:/Users/FI/Desktop/AI%20HACKATHON%20DENNUNG/views/matches.py) — Ranked results with 3 stat tiles, segmented filter (`All / Eligible / Closing soon`), and lazy-rendered cards (`5` per batch).
4. [`views/detail.py`](file:///c:/Users/FI/Desktop/AI%20HACKATHON%20DENNUNG/views/detail.py) — Single scholarship view with `Overview` (AI explanation), `Requirements` (icon checklist), and `Documents checklist` tabs.
5. [`views/application_helper.py`](file:///c:/Users/FI/Desktop/AI%20HACKATHON%20DENNUNG/views/application_helper.py) — Dedicated application email / essay generator with English/Urdu toggle, copy box, and regenerate button.
6. [`views/link_checker.py`](file:///c:/Users/FI/Desktop/AI%20HACKATHON%20DENNUNG/views/link_checker.py) — Single-input URL / notice text analyzer with key-value extraction card and profile eligibility verdict.
7. [`views/checklist.py`](file:///c:/Users/FI/Desktop/AI%20HACKATHON%20DENNUNG/views/checklist.py) — Saved documents grouped by scholarship and deadline timeline with coloured urgency dots.
8. [`views/about.py`](file:///c:/Users/FI/Desktop/AI%20HACKATHON%20DENNUNG/views/about.py) — Live Gemini/Anthropic API Connection Tester, architecture overview, and official data sources table.

---

## 3. How to Add a New Page

1. **Create the view file** in `views/my_new_page.py`:
   ```python
   import streamlit as st
   from ui.components import render_back_bar, section_header, primary_button
   from ui.i18n import t

   def render() -> None:
       pages = st.session_state["pages"]
       render_back_bar(t("nav_home"), pages["home"], breadcrumb="My New Feature")
       section_header("One Clear Headline", "One line of helper text.", icon_name="sparkles")
       if primary_button("Do primary action", key="my_new_action"):
           st.success("Action completed!")

   render()
   ```
2. **Add bilingual labels** (if needed) to `STRINGS["en"]` and `STRINGS["ur"]` in [`ui/i18n.py`](file:///c:/Users/FI/Desktop/AI%20HACKATHON%20DENNUNG/ui/i18n.py).
3. **Register the `st.Page`** inside the `pages` dictionary in [`app.py`](file:///c:/Users/FI/Desktop/AI%20HACKATHON%20DENNUNG/app.py):
   ```python
   "my_new_page": st.Page("views/my_new_page.py", title="My New Feature"),
   ```
4. **Navigate to it** from any button using `st.switch_page(st.session_state["pages"]["my_new_page"])`.
