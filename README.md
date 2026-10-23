# 🎓 ScholarMatch 

> **DITE Hackathon 2026–27** | **Theme:** Education  
> **Team Name:** Vectors  
> **Team Members:** `Alishba`, `Maryam`, `Laraib`  
> **Live App URL:** `[Paste Hugging Face Spaces / Streamlit Cloud URL Here]`  
> **Demo Video (4 min):** `[Paste YouTube / Loom / Google Drive Video Link Here]`

---

## 1. Problem Statement

Thousands of low-income and first-generation students across Sindh and Pakistan miss out on life-changing scholarships every year because announcements are scattered across dozens of government, HEC, foundation, and international portals, written in complex bureaucratic English, or circulated on WhatsApp with missing deadlines.  solves this by letting a student enter their profile (or snap a photo of their marksheet) on any mobile phone to instantly see which scholarships are **open right now**, why they qualify in simple English or Urdu (نستعلیق), what documents to prepare, and how to draft a sincere application—without ever paying an agent.

---

## 2. Core Architecture: "Rules by Code, Explanation by AI"

**Crucial Design Decision:**  
**All eligibility, deadline filtering, and ranking decisions are made by deterministic plain Python code (`eligibility.py`), NEVER by the LLM. The LLM never decides eligibility.**

Why? Hallucinating a deadline or an income threshold can cause a real student to waste money on attestation or miss a genuine opportunity. Therefore:
- **Deterministic Python (`eligibility.py`):** Evaluates degree level, province/domicile, field of study, monthly family income (PKR), minimum percentage/CGPA, and ISO deadline dates (`deadline_iso` vs. today's date). Any unknown/null requirement is transparently flagged as `"maybe"` (`"⚠️ Confirm on official page"`), never guessed.
- **AI Doing Real Work (`profile_reader.py`, `extract.py`, `drafts.py`):** The LLM is used strictly for three structured tasks where AI excels:

| # | AI Component | Module | Model / SDK | Input | Output |
|---|---|---|---|---|---|
| **(a)** | **Marksheet Vision** | `profile_reader.py` | Gemini (`google-genai` / `GEMINI_MODEL`) or Claude (`anthropic` / `ANTHROPIC_MODEL`) | Photo/scan of a Pakistani board marksheet or university transcript (`bytes`) | Structured JSON (`level`, `percentage`, `cgpa`, `board_or_university`, `year`, `confidence`) pre-filling editable form inputs |
| **(b)** | **Notice & Webpage Extraction** | `extract.py` | Gemini or Claude via `llm.ask()` | Cleaned text from an official scholarship URL or PDF (`BeautifulSoup` / `pypdf`) or pasted notice text | Strict Section 5 JSON schema with `null` for unstated values and verbatim `evidence` sentence |
| **(c)** | **Bilingual Explanation & Application Drafts** | `drafts.py` | Gemini or Claude via `llm.ask()` | Code-verified match object + student profile + language (`English` or `Urdu`) | 3–4 sentence grounded explanation (with Urdu RTL & speech synthesis) + `<250`-word application email with `[...]` placeholders |

---

## 3. Tech Stack

- **Language:** Python 3.11+
- **Frontend / UI:** Streamlit (`layout="centered"`, mobile-first responsive cards, Google Fonts `Noto Nastaliq Urdu` RTL support, Web Speech API `ur-PK` / `en-US` read-aloud)
- **Parsing & Scraping:** `requests`, `beautifulsoup4`, `pypdf`
- **LLM Abstraction (`llm.py`):**
  - Supports `LLM_PROVIDER="gemini"` (official `google-genai` SDK, model via `GEMINI_MODEL`) and `LLM_PROVIDER="anthropic"` (official `anthropic` SDK, model via `ANTHROPIC_MODEL`).
  - Automatic cross-provider retry fallback: if the primary provider fails (quota/network), `llm.ask()` automatically retries once with the secondary provider if its API key is present.
- **Storage:** Zero database (`data/scholarships.json` + `data/scholarships.seed.json` on disk; student profile in `st.session_state` only).
- **Testing:** `pytest` (15 deterministic unit tests in `tests/test_eligibility.py`).

---

## 4. Important Note on Seed Data & Verification Before Demo

To prevent harming students with invented or outdated numbers:
- `data/scholarships.seed.json` contains **12 real scholarship programmes** with only their stable, verified metadata (`name`, `provider`, `kind`, `level`, `source_url`, `apply_url`), while uncertain yearly fields (`deadline_iso`, `max_family_income_pkr`, `min_percentage`, `min_cgpa`) are set to `null` with `deadline_confirmed: false` and `last_verified: null`. The UI badges these as **Unverified — Confirm on official site**.
- **Before the live demo**, verify and fill each entry from its official website—or run `python fetch_all.py` to fetch and extract the latest live notices automatically!
- Additionally, `data/scholarships.seed.json` includes **3 synthetic demo entries** prefixed with `demo_` and badged **`🧪 DEMO DATA`** (plus a top banner in the UI) so you can demonstrate `"yes"` eligibility, the **`🔥 URGENT`** countdown badge (`<= 7` days left), and the **`Recently closed`** transparency section even when offline.

---

## 5. Project Structure

```text
wazifa-saathi/
  app.py                      # Streamlit mobile-first multi-tab UI
  llm.py                      # Provider abstraction (Gemini + Anthropic), retries, JSON cleaning
  eligibility.py              # Pure Python check() and rank() functions
  extract.py                  # Webpage/PDF fetcher + LLM structured JSON extraction
  fetch_all.py                # CLI script: refresh data/scholarships.json from data/sources.json
  profile_reader.py           # Vision AI: marksheet image -> structured profile JSON
  drafts.py                   # Bilingual English/Urdu match explanations & application drafts
  data/
    sources.json              # Official scholarship URLs to fetch
    scholarships.json         # Active cached scholarship data
    scholarships.seed.json    # 12 hand-checked seed entries + 3 clearly badged demo_ entries
  samples/
    sample_marksheet_intermediate.png  # Clearly fake BISE Hyderabad marksheet for demo
    sample_marksheet_undergrad.png     # Clearly fake Univ. of Sindh transcript for demo
    sample_scholarship_notice.txt      # Sample notice text for Tab 2 paste-text fallback
  tests/
    test_eligibility.py       # 15 pytest unit tests for check() and rank()
  .env.example                # Template for environment variables
  .gitignore                  # Excludes .env, secrets.toml, __pycache__, etc.
  requirements.txt            # Pinned minimum dependencies
  DEMO_SCRIPT.md              # 4-minute step-by-step hackathon presentation script
  README.md                   # Project documentation
```

---

## 6. Local Setup & Running

### Step 1: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure API keys
Copy `.env.example` to `.env` and add your Gemini and/or Anthropic API key:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_actual_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

# Optional fallback or primary provider:
ANTHROPIC_API_KEY=your_actual_anthropic_api_key
ANTHROPIC_MODEL=claude-3-5-sonnet-latest
```

### Step 3: Run unit tests
```bash
pytest -v
```

### Step 4: (Optional) Refresh scholarship data from official URLs
```bash
# Dry run first (does not overwrite data/scholarships.json):
python fetch_all.py --dry-run

# Live refresh:
python fetch_all.py
```

### Step 5: Launch the Streamlit app
```bash
streamlit run app.py
```

---

## 7. Deployment Guide

### Option A: Streamlit Community Cloud
1. Push this repository to GitHub (verify `.env` is ignored via `.gitignore`).
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **New app**.
3. Select your repository, branch `main`, and main file path `app.py`.
4. Click **Advanced settings... -> Secrets** and paste your keys in TOML format:
   ```toml
   LLM_PROVIDER = "gemini"
   GEMINI_API_KEY = "your_gemini_api_key_here"
   GEMINI_MODEL = "gemini-2.5-flash"
   ANTHROPIC_API_KEY = "your_anthropic_api_key_here"
   ANTHROPIC_MODEL = "claude-3-5-sonnet-latest"
   ```
5. Click **Deploy!** and test the public URL in an incognito window.

### Option B: Hugging Face Spaces (Streamlit SDK)
1. Go to [huggingface.co/new-space](https://huggingface.co/new-space).
2. Name your Space `wazifa-saathi`, select **Streamlit** as the Space SDK, and choose **Public**.
3. Upload or `git push` all project files to the Space repository.
4. In your Space, open **Settings -> Variables and secrets**:
   - Add **Variables**:
     - `LLM_PROVIDER` = `gemini`
     - `GEMINI_MODEL` = `gemini-2.5-flash`
     - `ANTHROPIC_MODEL` = `claude-3-5-sonnet-latest`
   - Add **Secrets**:
     - `GEMINI_API_KEY` = `your_gemini_api_key_here`
     - `ANTHROPIC_API_KEY` = `your_anthropic_api_key_here`
5. Wait ~2 minutes for the container to build, then open the public Space URL in an incognito window.

### Keep the App Awake Before Judging
Free tiers on Streamlit Community Cloud and Hugging Face Spaces go to sleep after periods of inactivity:
1. **15 minutes before judging begins**, open your deployed public URL in an incognito browser tab and click **"🎓 Load demo student"** in the sidebar so the container is warm and `@st.cache_data` caches are populated.
2. On Hugging Face Spaces, ensure your Space isn't paused in **Settings -> Space Sleep Time**.
3. Keep `data/scholarships.json` committed in the repo so initial page load requires zero live scraping.

---

## 8. Data Sources & Credits

All real seed entries reference official Pakistani government, foundation, or international scholarship portals:

| Scholarship | Provider | Official Source | Last Verified |
|---|---|---|---|
| HEC Need-Based Scholarship Program | Higher Education Commission (HEC) | [hec.gov.pk/NBS](https://www.hec.gov.pk/english/scholarshipsgrants/NBS/Pages/default.aspx) | Unverified (Seed — run `fetch_all.py`) |
| HEC Undergraduate & National Scholarships | Higher Education Commission (HEC) | [hec.gov.pk](https://www.hec.gov.pk/english/scholarshipsgrants/Pages/default.aspx) | Unverified (Seed) |
| BISP / Ehsaas Education Support | Benazir Income Support Programme | [bisp.gov.pk](https://www.bisp.gov.pk) | Unverified (Seed) |
| Dalda Foundation Trust Scholarship | Dalda Foundation Trust | [daldafoundation.pk](https://www.daldafoundation.pk) | Unverified (Seed) |
| Sindh Educational Endowment Fund (SEEF) | Govt. of Sindh College Education Dept. | [seef.sindh.gov.pk](https://seef.sindh.gov.pk) | Unverified (Seed) |
| Sindh Education Foundation (SEF) Programmes | Sindh Education Foundation | [sef.org.pk](https://www.sef.org.pk) | Unverified (Seed) |
| Pakistan Bait-ul-Mal Education Stipend | Pakistan Bait-ul-Mal (PBM) | [pbm.gov.pk](https://www.pbm.gov.pk) | Unverified (Seed) |
| My University Need-Based Financial Aid | University Financial Aid Office | Campus FAO Portal (Placeholder) | Unverified (Seed) |
| USEFP Fulbright Master's & PhD Program | USEFP Pakistan | [usefp.org](https://www.usefp.org) | Unverified (Seed) |
| DAAD Postgraduate Scholarships (EPOS) | DAAD Pakistan | [daad.pk](https://www.daad.pk) | Unverified (Seed) |
| UK Government Chevening Scholarships | FCDO UK / Chevening | [chevening.org](https://www.chevening.org/scholarship/pakistan/) | Unverified (Seed) |
| Türkiye Bursları Scholarships | YTB Turkey | [turkiyeburslari.gov.tr](https://www.turkiyeburslari.gov.tr) | Unverified (Seed) |

---

## 9. Limitations & Ethical Notes

- **Guidance Only:** Scholarship rules and deadlines can change via corrigendum notices. Students must always confirm final requirements on the linked official website.
- **Zero Student Data Stored:** No database, no tracking cookies, and no login wall. Marksheet images and profile inputs exist only in ephemeral RAM (`st.session_state`) during the active session and are never logged.
- **Anti-Agent Protection:** Every screen reminds students: *"No scholarship requires you to pay an agent."*

---

## 10. Screenshots

> `[Placeholder: Insert Screenshot 1 — Tab 1 Mobile View with Marksheet Reader & Ranked Cards]`  
> `[Placeholder: Insert Screenshot 2 — Urdu RTL Explanation & Application Draft Generator]`  
> `[Placeholder: Insert Screenshot 3 — Tab 2 Live Link / Notice Analyser & Tab 3 Document Checklist]`
