"""
drafts.py — AI Explanations & Application Draft Generation for Wazifa Saathi.

Provides two functions:
  1. `explain(match, profile, lang)`: Generates a 3-4 sentence explanation of why
     a scholarship fits the student in simple English or Urdu (Urdu script),
     strictly grounded in the deterministic eligibility output.
  2. `application_draft(match, profile, student_notes, lang)`: Writes a sincere,
     under-250-word application email / statement of purpose with explicit
     placeholders (`[add your achievement here]`) instead of invented facts.

Both functions wrap `llm.ask()` in `try/except` blocks with deterministic
fallbacks so the app remains useful even if the AI quota is exhausted.
"""

from __future__ import annotations

from typing import Any

from llm import LLMError, ask


def _fallback_explanation(
    match: dict[str, Any],
    profile: dict[str, Any],
    lang: str,
    ai_notice: str | None = None,
) -> str:
    """
    Build a deterministic 3-4 sentence explanation in English or Urdu script
    when the LLM is busy or unconfigured.
    """
    name = match.get("name", "This scholarship")
    provider = match.get("provider", "the provider")
    status = match.get("status", "maybe")
    days_left = match.get("days_left")
    benefits = match.get("benefits") or f"{match.get('funding', 'unknown')} funding"
    reasons = match.get("reasons") or []

    level = profile.get("level", "student")
    province = profile.get("province", "Pakistan")

    verify_items = [
        r for r in reasons if "confirm" in r.lower() or "not published" in r.lower() or "tentative" in r.lower()
    ]
    verify_text = (
        verify_items[0]
        if verify_items
        else "all required documents on the official website"
    )

    if str(lang).strip().lower() == "urdu":
        if days_left is not None and days_left >= 0:
            deadline_sentence = f"اس اسکالرشپ کی آخری تاریخ میں {days_left} دن باقی ہیں۔"
        else:
            deadline_sentence = "اس اسکالرشپ کی آخری تاریخ ابھی سرکاری ویب سائٹ پر تصدیق شدہ نہیں ہے۔"

        status_word = "مکمل طور پر موزوں" if status == "yes" else "ممکنہ طور پر موزوں (تصدیق ضروری)"
        urdu_text = (
            f"{name} ({provider}) آپ کے {level} پروفائل اور صوبہ ({province}) کے لحاظ سے {status_word} ہے۔ "
            f"اس پروگرام کے تحت فوائد میں '{benefits}' شامل ہیں۔ "
            f"{deadline_sentence} "
            f"درخواست دینے سے پہلے سرکاری ویب سائٹ پر ان شرائط کی لازمی تصدیق کریں: {verify_text}۔"
        )
        if ai_notice:
            return f"{urdu_text}\n({ai_notice})"
        return urdu_text

    # English fallback
    if days_left is not None and days_left >= 0:
        deadline_sentence = f"You have {days_left} day(s) left before the deadline ({match.get('deadline_iso')})."
    else:
        deadline_sentence = "The exact application deadline is not yet confirmed on the official website."

    fit_desc = (
        "you meet all published eligibility rules"
        if status == "yes"
        else "you match the core profile criteria, though some details need confirmation"
    )

    eng_text = (
        f"{name} by {provider} is a strong match for a {level} student from {province} because {fit_desc}. "
        f"It offers {benefits}. "
        f"{deadline_sentence} "
        f"Before applying, please verify on the official page: {verify_text}."
    )
    if ai_notice:
        return f"{eng_text} ({ai_notice})"
    return eng_text


def explain(
    match: dict[str, Any],
    profile: dict[str, Any],
    lang: str = "English",
) -> str:
    """
    Generate a 3-4 sentence explanation of why a scholarship suits the student.

    Strict constraints:
      - References ONLY facts present in `profile` and `match`.
      - Selectable language: `"English"` or `"Urdu"` (written in Urdu script).
      - Mentions `days_left` (or unconfirmed deadline) and any `"maybe"` conditions
        that the student must verify on the official website.
      - Never invents eligibility rules.

    Args:
        match: Ranked scholarship dictionary containing `status`, `reasons`, `days_left`, etc.
        profile: Student profile dictionary.
        lang: `"English"` or `"Urdu"`.

    Returns:
        3-4 sentence explanation string.
    """
    target_lang = (
        "Urdu (written in clear Urdu script / نستعلیق)"
        if str(lang).strip().lower() == "urdu"
        else "simple, encouraging English"
    )

    days_left = match.get("days_left")
    days_info = (
        f"{days_left} days left (deadline: {match.get('deadline_iso')})"
        if days_left is not None
        else "Deadline not confirmed on official page"
    )

    reasons_list = match.get("reasons") or []
    reasons_formatted = "\n".join(f"- {r}" for r in reasons_list)

    prompt = f"""You are a helpful scholarship advisor for Pakistani students ("Wazifa Saathi").
Write 3 to 4 short, clear sentences in {target_lang} explaining why this scholarship suits the student.

STUDENT PROFILE (use ONLY these facts):
- Degree Level: {profile.get("level")}
- Province: {profile.get("province")}
- Field of Study: {profile.get("field")}
- Percentage: {profile.get("percentage")}%
- CGPA: {profile.get("cgpa")}
- Monthly Family Income: PKR {profile.get("monthly_income_pkr")}

SCHOLARSHIP DATA (use ONLY these facts):
- Name: {match.get("name")}
- Provider: {match.get("provider")}
- Type: {match.get("kind")} ({match.get("funding")} funding)
- Benefits: {match.get("benefits") or "See official page"}
- Eligibility Status: {match.get("status")}
- Time Remaining: {days_info}
- Code-Verified Reasons & Conditions to Check:
{reasons_formatted}

STRICT RULES:
1. Write ONLY 3 to 4 short sentences in {target_lang}.
2. Mention how many days are left (or that the deadline is unconfirmed).
3. Explicitly mention any "maybe" / unconfirmed condition the student must check on the official website.
4. NEVER invent any numbers, dates, or eligibility conditions not listed above.
5. Output plain text only (no markdown headings or bullet points).
"""

    try:
        response = ask(prompt=prompt, max_tokens=800)
        return response.strip()
    except LLMError:
        return _fallback_explanation(
            match=match,
            profile=profile,
            lang=lang,
            ai_notice="AI is busy, please try again in a minute — showing summary from verified rules",
        )
    except Exception:
        return _fallback_explanation(match=match, profile=profile, lang=lang)


def _fallback_application_draft(
    match: dict[str, Any],
    profile: dict[str, Any],
    student_notes: str,
    lang: str,
) -> str:
    """Return a clean, placeholder-safe application draft when the LLM is unavailable."""
    name = match.get("name", "Scholarship Programme")
    provider = match.get("provider", "Scholarship Committee")
    level = profile.get("level", "undergraduate")
    field = profile.get("field") or "[Your Field of Study]"
    province = profile.get("province") or "[Your Province]"
    pct = f"{profile['percentage']}%" if profile.get("percentage") is not None else "[Your Percentage]"
    cgpa_str = f" (CGPA: {profile['cgpa']})" if profile.get("cgpa") is not None else ""
    income = (
        f"PKR {int(profile['monthly_income_pkr']):,}"
        if profile.get("monthly_income_pkr") is not None
        else "[Your Monthly Family Income]"
    )
    notes_line = (
        f"Furthermore, {student_notes.strip()}."
        if student_notes and student_notes.strip()
        else "Furthermore, I have consistently demonstrated dedication to my studies through [add your achievement here]."
    )

    if str(lang).strip().lower() == "urdu":
        return (
            f"بخدمت جناب اسکالرشپ کمیٹی ({provider})،\n"
            f"موضوع: {name} کے لیے درخواست\n\n"
            f"مودبانہ گزارش ہے کہ میں [اپنا پورا نام یہاں لکھیں]، صوبہ {province} سے تعلق رکھنے والا/والی "
            f"{level} ({field}) کا/کی طالب علم ہوں۔ میرے تعلیمی نمبر {pct}{cgpa_str} ہیں اور میرے خاندان کی ماہانہ آمدنی {income} ہے۔ "
            f"{notes_line}\n\n"
            f"یہ وظیفہ مجھے اپنی تعلیم بغیر کسی مالی رکاوٹ کے جاری رکھنے میں مدد دے گا۔ میں تمام مطلوبہ کاغذات منسلک کر رہا/رہی ہوں۔\n\n"
            f"والسلام،\n"
            f"[اپنا پورا نام]\n"
            f"[یونیورسٹی/کالج کا نام اور رول نمبر]\n"
            f"[رابطہ نمبر / ای میل]"
        )

    return (
        f"Subject: Application for {name} — [Your Full Name]\n\n"
        f"Respected Scholarship Committee ({provider}),\n\n"
        f"I am writing to respectfully apply for the {name}. I am a {level} student in {field} "
        f"at [Your University/College Name], holding domicile from {province}. In my recent examinations, "
        f"I achieved {pct}{cgpa_str}. My family's monthly income is {income}, and financial support is "
        f"essential for me to continue my higher education without interruption.\n\n"
        f"{notes_line} My academic goal is to [add your academic or career goal here] and contribute "
        f"positively to my community.\n\n"
        f"I have attached all required documents for your kind review. Thank you for considering my application.\n\n"
        f"Sincerely,\n"
        f"[Your Full Name]\n"
        f"[Your Roll Number / CNIC]\n"
        f"[Your Phone Number & Email]"
    )


def application_draft(
    match: dict[str, Any],
    profile: dict[str, Any],
    student_notes: str = "",
    lang: str = "English",
) -> str:
    """
    Draft a short, sincere scholarship application email or statement of purpose.

    Strict rules:
      - Never invents achievements, grades, numbers, or personal details.
      - Uses bracketed placeholders like `[add your achievement here]` where info is missing.
      - Keeps length under 250 words with a respectful tone.

    Args:
        match: Scholarship dict.
        profile: Student profile dict.
        student_notes: Optional personal notes or achievements entered by the student.
        lang: `"English"` or `"Urdu"`.

    Returns:
        Draft application text (<250 words).
    """
    target_lang = (
        "Urdu (in formal Urdu script)"
        if str(lang).strip().lower() == "urdu"
        else "English"
    )

    notes_clean = (student_notes or "").strip() or "None provided — use placeholders like [add your achievement here]"

    prompt = f"""You are helping a Pakistani student write a short, sincere scholarship application email / statement of purpose for:
Scholarship: {match.get("name")}
Provider: {match.get("provider")}
Scholarship Type: {match.get("kind")}

Verified Student Profile:
- Study Level: {profile.get("level")}
- Field of Study: {profile.get("field") or "[Your Field of Study]"}
- Province: {profile.get("province")}
- Percentage: {profile.get("percentage") if profile.get("percentage") is not None else "[Your Percentage]"}
- CGPA: {profile.get("cgpa") if profile.get("cgpa") is not None else "[Your CGPA if applicable]"}
- Monthly Family Income (PKR): {profile.get("monthly_income_pkr")}

Student's Extra Notes:
{notes_clean}

STRICT RULES:
1. Write in {target_lang}.
2. Keep it strictly under 220 words with a humble, respectful, and sincere academic tone.
3. NEVER invent any achievements, awards, family stories, numbers, or personal details.
4. Wherever information is missing (such as name, institution name, roll number, or specific achievements), insert clear placeholders in square brackets like [Your Full Name], [Your Institution Name], [add your achievement here].
"""

    try:
        response = ask(prompt=prompt, max_tokens=900)
        return response.strip()
    except LLMError:
        draft = _fallback_application_draft(match, profile, student_notes, lang)
        return f"{draft}\n\n---\nNote: AI is busy, please try again in a minute. Above is a ready-to-fill template based on your profile."
    except Exception:
        return _fallback_application_draft(match, profile, student_notes, lang)
