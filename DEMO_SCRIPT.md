# 🎬 Wazifa Saathi — 4-Minute Demo Script (`DEMO_SCRIPT.md`)

> **Target Duration:** 4 minutes (240 seconds)  
> **Pre-Recording Checklist:**
> 1. Start the app (`streamlit run app.py`) or open your deployed URL in an **incognito window**.
> 2. Set your browser zoom to `100%` (or toggle Chrome DevTools mobile view `430x932` briefly to show mobile-first layout).
> 3. Ensure `.env` has a valid `GEMINI_API_KEY` or `ANTHROPIC_API_KEY`.

---

## 0:00 – 0:35 | The Problem & Our Core Rule (35s)

- **On Screen:** Main landing page of **Wazifa Saathi (وظیفہ ساتھی)** showing the yellow anti-scam disclaimer banner.
- **What to Say:**
  > "Assalam-o-Alaikum! Across Sindh and Pakistan, thousands of low-income and first-generation students miss out on HEC, SEEF, BISP, and foundation scholarships because notices are scattered, written in complex English, or shared on WhatsApp after deadlines pass. Worse, scammers charge students fees to 'apply'.
  >
  > We built **Wazifa Saathi** with one strict engineering rule: **Rules by Code, Explanation by AI**. Plain, unit-tested Python code decides eligibility, filters out expired deadlines, and ranks matches. The AI does three real jobs: reading marksheet photos, extracting structured JSON from any notice, and explaining matches or drafting applications in simple English and Urdu."

---

## 0:35 – 1:30 | Vision AI Marksheet Reader & Ranked Matches (55s)

- **Click Path:**
  1. Open the sidebar on the left and click **"🎓 Load demo student"** *(or in Tab 1 expand **"📸 Upload a photo of your marksheet"** and click **"📄 Try Sample Undergrad Transcript"**)*.
  2. Point out the extracted values (`Undergraduate`, `78.5%`, `CGPA 3.42`, `Sindh`, `PKR 35,000`, `Computer Science`) inside the **editable** form fields.
  3. Set **Language for AI Explanations & Drafts** to **Urdu** (or demonstrate English then switch to Urdu) and click **"🔍 Find scholarships"**.
- **What to Highlight:**
  - The summary bar: `15 checked • 2 fully eligible • 6 need confirmation (Maybe) • 1 closing within 7 days`.
  - Card #1 shows **`✅ Eligible`** and **`🔥 URGENT (Closing Soon)`** (`5 days left`).
  - Point to the **Urdu RTL explanation** rendered in Nastaliq script (`Noto Nastaliq Urdu`) and click **"🔊 سنیں (Read Aloud)"**.
  - Expand **"📋 Eligibility Rules Checked & Required Documents"** to show deterministic Python rule checks.
  - Scroll down and briefly expand **"🚫 Not eligible"** and **"🕒 Recently closed in the last 30 days"** to show why excluded scholarships were dropped (building student trust).

---

## 1:30 – 2:15 | Sincere Application Draft Generator (45s)

- **Click Path:**
  1. On the top scholarship card, open the expander **"✍️ Write my application draft (Email / Statement of Purpose)"**.
  2. Type in the notes box: `"First in my family to attend university, scored 85% in programming lab"`.
  3. Click **"✨ Generate Draft"**.
- **What to Highlight:**
  - Point out that the AI **never invents fake achievements or numbers**—it uses only the student's verified profile and notes, and leaves clear square-bracket placeholders like `[Your Full Name]` and `[Your Roll Number / CNIC]` ready to copy.

---

## 2:15 – 3:15 | Tab 2: Check Any Scholarship Link or Notice (60s)

- **Click Path:**
  1. Click Tab 2: **"🔗 Check any scholarship link"**.
  2. Click **"📄 Load sample scholarship notice text (for demo)"** (which loads `samples/sample_scholarship_notice.txt` — *Sindh IT & Emerging Sciences Talent Scholarship 2026-27*).
  3. Click **"🔎 Analyse Scholarship"**.
- **What to Highlight:**
  - Show how `extract.py` extracts the exact structured schema (`max_family_income_pkr: PKR 65,000`, `min_percentage: 70.0%`, `deadline_iso: 2026-11-15`), copies the verbatim **Supporting Evidence Line**, and immediately runs `eligibility.check()` against the student's profile (`✅ ELIGIBLE (YES)`).
  - Click **"➕ Add to my list for this session"**.

---

## 3:15 – 4:00 | Tab 3 Checklist & Tab 4 Transparency Wrap-up (45s)

- **Click Path:**
  1. Click Tab 3: **"📋 My checklist"**.
  2. Check off 2–3 required documents (`CNIC`, `Sindh Domicile & PRC`) to show the live progress bar and the **Deadline Timeline** sorted by date.
  3. Click Tab 4: **"ℹ️ About & data"** to show the official data sources table, the zero-storage privacy guarantee (session state only, no login wall), and the anti-agent warning.
- **Closing Line:**
  > "Wazifa Saathi works on any budget smartphone, stores zero personal student data, never guesses eligibility rules, and empowers every student in Pakistan to apply on time and for free. Thank you!"
