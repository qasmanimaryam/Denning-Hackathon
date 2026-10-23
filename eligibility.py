"""
eligibility.py — Deterministic Eligibility Checking & Scholarship Ranking.

IMPORTANT HACKATHON RULE:
All eligibility, deadline, and ranking decisions are made by pure, deterministic
Python code in this module — NEVER by an LLM. The LLM is only used elsewhere to
read marksheets, extract raw webpage text, and explain/draft applications for
results already computed here.

Income Convention:
Both `profile["monthly_income_pkr"]` and `scholarship["max_family_income_pkr"]`
are expressed as MONTHLY family income in Pakistani Rupees (PKR). If a
scholarship dictionary explicitly sets `"income_period": "yearly"` (or `"annual"`),
`get_monthly_income_limit_pkr()` divides `max_family_income_pkr` by 12 to convert
it consistently to a monthly PKR limit before comparing.
"""

from __future__ import annotations

import copy
from datetime import date, datetime
from typing import Any

# Field-of-study alias map so "cs" matches "Computer Science", etc.
FIELD_ALIASES: dict[str, set[str]] = {
    "cs": {
        "cs",
        "computer science",
        "computing",
        "software engineering",
        "it",
        "information technology",
        "data science",
        "artificial intelligence",
        "ai",
    },
    "engineering": {
        "engineering",
        "electrical engineering",
        "mechanical engineering",
        "civil engineering",
        "software engineering",
        "chemical engineering",
        "electronics",
        "be",
        "bsc engineering",
    },
    "medical": {
        "medical",
        "medicine",
        "mbbs",
        "bds",
        "nursing",
        "pharmacy",
        "pharm-d",
        "allied health",
        "health sciences",
    },
    "business": {
        "business",
        "bba",
        "mba",
        "commerce",
        "accounting",
        "finance",
        "economics",
        "management",
    },
    "science": {
        "science",
        "natural sciences",
        "physics",
        "chemistry",
        "mathematics",
        "biology",
        "biotechnology",
        "pre-engineering",
        "pre-medical",
    },
    "arts": {
        "arts",
        "humanities",
        "social sciences",
        "education",
        "law",
        "english",
        "media",
    },
}


class RankedResults(list):
    """
    A `list` subclass returned by `rank()` that behaves identically to a normal
    sorted `list[dict[str, Any]]` while also exposing:
      - `.closed_recently`: list of scholarships whose deadline passed within the last 30 days.
      - `.not_eligible`: list of scholarships excluded due to failing eligibility rules.
    """

    def __init__(
        self,
        ranked_items: list[dict[str, Any]],
        closed_recently: list[dict[str, Any]] | None = None,
        not_eligible: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(ranked_items)
        self.closed_recently: list[dict[str, Any]] = closed_recently or []
        self.not_eligible: list[dict[str, Any]] = not_eligible or []


def parse_iso_date(value: date | str | None) -> date | None:
    """
    Parse an ISO date string ('YYYY-MM-DD') or `datetime.date` into a `date` object.

    Args:
        value: A `date`, ISO format string `'YYYY-MM-DD'`, or `None`.

    Returns:
        A `datetime.date` object, or `None` if `value` is empty or invalid.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        try:
            return date.fromisoformat(cleaned[:10])
        except ValueError:
            return None
    return None


def get_monthly_income_limit_pkr(scholarship: dict[str, Any]) -> float | None:
    """
    Return the scholarship's maximum family income limit normalized to MONTHLY PKR.

    INCOME LIMIT CONVENTION:
    `max_family_income_pkr` in `data/scholarships.json` is stored as MONTHLY family
    income in PKR to match `profile["monthly_income_pkr"]`. If a record has
    `"income_period": "yearly"` or `"annual"`, it is divided by 12.0 here so
    comparisons are always monthly-to-monthly in PKR.

    Args:
        scholarship: Scholarship dictionary adhering to the schema.

    Returns:
        Monthly income limit in PKR as a float, or `None` if not specified.
    """
    raw_limit = scholarship.get("max_family_income_pkr")
    if raw_limit is None:
        return None
    try:
        limit_val = float(raw_limit)
    except (TypeError, ValueError):
        return None

    period = str(scholarship.get("income_period", "monthly") or "monthly").strip().lower()
    if period in ("yearly", "annual", "year"):
        return round(limit_val / 12.0, 2)
    return limit_val


def _field_matches(allowed_fields: list[str], student_field: str) -> bool:
    """
    Check if `student_field` matches any entry in `allowed_fields`, accounting
    for common academic field aliases (e.g. 'cs' <-> 'Computer Science').
    """
    norm_allowed = [f.strip().lower() for f in allowed_fields if f and str(f).strip()]
    if not norm_allowed or "all" in norm_allowed or "any" in norm_allowed:
        return True

    norm_student = (student_field or "").strip().lower()
    if not norm_student or norm_student == "any":
        return True

    # Direct or substring match
    for allowed in norm_allowed:
        if norm_student == allowed or allowed in norm_student or norm_student in allowed:
            return True

    # Alias group match
    student_canonical_groups: set[str] = set()
    for group_key, aliases in FIELD_ALIASES.items():
        if norm_student == group_key or norm_student in aliases:
            student_canonical_groups.add(group_key)
        else:
            for alias in aliases:
                if len(alias) > 2 and (alias in norm_student or norm_student in alias):
                    student_canonical_groups.add(group_key)

    for allowed in norm_allowed:
        if allowed in student_canonical_groups:
            return True
        for group_key, aliases in FIELD_ALIASES.items():
            if (allowed == group_key or allowed in aliases) and group_key in student_canonical_groups:
                return True

    return False


def _evaluate_other_conditions(
    other_conditions: list[str] | None,
    profile: dict[str, Any],
) -> tuple[list[str], list[str]]:
    """
    Inspect `other_conditions` for deterministic rules (such as gender restrictions)
    and collect remaining human-verifiable conditions.

    Returns:
        Tuple of `(fail_reasons, maybe_reasons)`.
    """
    fail_reasons: list[str] = []
    maybe_reasons: list[str] = []

    if not other_conditions:
        return fail_reasons, maybe_reasons

    student_gender = str(profile.get("gender") or "").strip().lower()

    for cond in other_conditions:
        if not cond or not str(cond).strip():
            continue
        cond_str = str(cond).strip()
        cond_lower = cond_str.lower()

        # Check explicit gender restrictions if present
        is_female_only = (
            ("female only" in cond_lower or "female students only" in cond_lower or "women only" in cond_lower)
            and "male and female" not in cond_lower
        )
        is_male_only = (
            ("male only" in cond_lower or "male students only" in cond_lower)
            and "female" not in cond_lower
        )

        if is_female_only:
            if student_gender in ("male", "m"):
                fail_reasons.append(f"Restricted to female candidates ({cond_str})")
            elif student_gender in ("female", "f"):
                # Verified!
                continue
            else:
                maybe_reasons.append(f"Confirm gender requirement: {cond_str}")
        elif is_male_only:
            if student_gender in ("female", "f"):
                fail_reasons.append(f"Restricted to male candidates ({cond_str})")
            elif student_gender in ("male", "m"):
                continue
            else:
                maybe_reasons.append(f"Confirm gender requirement: {cond_str}")
        else:
            maybe_reasons.append(f"Confirm condition on official page: {cond_str}")

    return fail_reasons, maybe_reasons


def check(
    scholarship: dict[str, Any],
    profile: dict[str, Any],
    today: date | str | None = None,
) -> tuple[str, list[str]]:
    """
    Evaluate a student's eligibility for a single scholarship using deterministic rules.

    Rules:
      - Returns `"no"` ONLY when a clear, known rule fails (deadline passed,
        wrong degree level, wrong province, wrong field of study, monthly income
        above `max_family_income_pkr`, or academic marks below minimum).
      - Returns `"maybe"` when any relevant condition is null/unknown, or
        `deadline_iso` is null, or `deadline_confirmed` is False, or
        `other_conditions` exist that code cannot automatically verify.
      - Returns `"yes"` ONLY when every known condition passes and no important
        field is unknown.

    Args:
        scholarship: Scholarship dict following the schema in Section 5.
        profile: Student profile dict following the schema in Section 7.
        today: Reference date (`datetime.date` or ISO string `'YYYY-MM-DD'`).
               Defaults to `date.today()`.

    Returns:
        Tuple `(status, reasons)` where `status` is `"yes"`, `"maybe"`, or `"no"`,
        and `reasons` is a list of short human-readable English strings.
    """
    resolved_today = parse_iso_date(today) or date.today()

    fail_reasons: list[str] = []
    maybe_reasons: list[str] = []
    pass_reasons: list[str] = []

    # 1. Deadline check
    deadline_date = parse_iso_date(scholarship.get("deadline_iso"))
    deadline_confirmed = bool(scholarship.get("deadline_confirmed", False))

    if deadline_date is not None:
        if deadline_date < resolved_today:
            days_ago = (resolved_today - deadline_date).days
            fail_reasons.append(
                f"Deadline passed on {deadline_date.isoformat()} ({days_ago} day{'s' if days_ago != 1 else ''} ago)"
            )
        else:
            days_left = (deadline_date - resolved_today).days
            if deadline_confirmed:
                pass_reasons.append(
                    f"Application is open ({days_left} day{'s' if days_left != 1 else ''} left until {deadline_date.isoformat()})"
                )
            else:
                maybe_reasons.append(
                    f"Tentative deadline {deadline_date.isoformat()} is not yet confirmed on the official page"
                )
    else:
        maybe_reasons.append("Deadline not published, confirm on the official page")

    # 2. Study level check
    allowed_levels = scholarship.get("level")
    student_level = str(profile.get("level") or "").strip().lower()

    if allowed_levels and isinstance(allowed_levels, list):
        norm_levels = [str(lvl).strip().lower() for lvl in allowed_levels if lvl]
        if norm_levels and "all" not in norm_levels:
            if not student_level:
                maybe_reasons.append(
                    f"Requires study level ({', '.join(norm_levels)}); select your study level to confirm"
                )
            elif student_level not in norm_levels:
                fail_reasons.append(
                    f"For {', '.join(norm_levels)} students only (your profile is {student_level})"
                )
            else:
                pass_reasons.append(f"Open to {student_level} students")
        else:
            pass_reasons.append("Open to all degree levels")
    else:
        maybe_reasons.append("Eligible degree levels not published, confirm on the official page")

    # 3. Province check
    allowed_provinces = scholarship.get("provinces")
    student_province = str(profile.get("province") or "").strip()

    if allowed_provinces and isinstance(allowed_provinces, list):
        norm_provinces = [str(p).strip().lower() for p in allowed_provinces if p]
        if norm_provinces and "all" not in norm_provinces:
            if not student_province:
                maybe_reasons.append(
                    f"Restricted to {', '.join(allowed_provinces)}; select your province to confirm"
                )
            elif student_province.lower() not in norm_provinces:
                fail_reasons.append(
                    f"Restricted to {', '.join(allowed_provinces)} domicile (your profile is {student_province})"
                )
            else:
                pass_reasons.append(f"Eligible for {student_province} domicile")
        else:
            pass_reasons.append("Open to students from all provinces in Pakistan")
    else:
        maybe_reasons.append("Province eligibility not published, confirm on the official page")

    # 4. Field of study check
    allowed_fields = scholarship.get("fields")
    student_field = str(profile.get("field") or "").strip()

    if allowed_fields and isinstance(allowed_fields, list):
        norm_fields = [str(f).strip().lower() for f in allowed_fields if f]
        if norm_fields and "all" not in norm_fields and "any" not in norm_fields:
            if not student_field:
                maybe_reasons.append(
                    f"Restricted to fields ({', '.join(allowed_fields)}); enter your field to confirm"
                )
            elif not _field_matches(allowed_fields, student_field):
                fail_reasons.append(
                    f"Restricted to {', '.join(allowed_fields)} fields (your field is {student_field})"
                )
            else:
                pass_reasons.append(f"Matches your field of study ({student_field})")
        else:
            pass_reasons.append("Open to all academic fields")
    else:
        maybe_reasons.append("Eligible fields of study not published, confirm on the official page")

    # 5. Family income check (monthly PKR comparison)
    monthly_limit = get_monthly_income_limit_pkr(scholarship)
    raw_student_income = profile.get("monthly_income_pkr")
    student_income: float | None = None
    if raw_student_income is not None and str(raw_student_income).strip() != "":
        try:
            student_income = float(raw_student_income)
        except (TypeError, ValueError):
            student_income = None

    if monthly_limit is not None:
        if student_income is None:
            maybe_reasons.append(
                f"Maximum monthly family income is PKR {monthly_limit:,.0f}; enter your income to confirm"
            )
        elif student_income > monthly_limit:
            fail_reasons.append(
                f"Monthly family income (PKR {student_income:,.0f}) exceeds limit of PKR {monthly_limit:,.0f}"
            )
        else:
            pass_reasons.append(
                f"Monthly family income (PKR {student_income:,.0f}) is within limit (PKR {monthly_limit:,.0f})"
            )
    else:
        maybe_reasons.append("Income limit not published, confirm on the official page")

    # 6. Academic marks check (min_percentage and/or min_cgpa)
    min_pct = scholarship.get("min_percentage")
    min_cgpa = scholarship.get("min_cgpa")

    student_pct: float | None = None
    if profile.get("percentage") is not None and str(profile.get("percentage")).strip() != "":
        try:
            student_pct = float(profile["percentage"])
        except (TypeError, ValueError):
            student_pct = None

    student_cgpa: float | None = None
    if profile.get("cgpa") is not None and str(profile.get("cgpa")).strip() != "":
        try:
            student_cgpa = float(profile["cgpa"])
        except (TypeError, ValueError):
            student_cgpa = None

    if min_pct is None and min_cgpa is None:
        maybe_reasons.append("Minimum marks/CGPA requirement not published, confirm on the official page")
    else:
        pct_passed = False
        cgpa_passed = False

        if min_pct is not None:
            min_pct_val = float(min_pct)
            if student_pct is not None:
                if student_pct < min_pct_val:
                    fail_reasons.append(
                        f"Percentage ({student_pct:.1f}%) is below minimum required ({min_pct_val:.1f}%)"
                    )
                else:
                    pct_passed = True
                    pass_reasons.append(
                        f"Percentage ({student_pct:.1f}%) meets minimum requirement ({min_pct_val:.1f}%)"
                    )

        if min_cgpa is not None:
            min_cgpa_val = float(min_cgpa)
            if student_cgpa is not None:
                if student_cgpa < min_cgpa_val:
                    fail_reasons.append(
                        f"CGPA ({student_cgpa:.2f}) is below minimum required ({min_cgpa_val:.2f})"
                    )
                else:
                    cgpa_passed = True
                    pass_reasons.append(
                        f"CGPA ({student_cgpa:.2f}) meets minimum requirement ({min_cgpa_val:.2f})"
                    )

        # If neither failed, check if a required score was missing from the profile
        if not fail_reasons:
            if min_pct is not None and min_cgpa is not None:
                # Scholarship lists both percentage and CGPA thresholds (e.g. 70% or 3.0 CGPA)
                if not pct_passed and not cgpa_passed:
                    maybe_reasons.append(
                        f"Requires minimum {float(min_pct):.1f}% or {float(min_cgpa):.2f} CGPA; enter your marks to confirm"
                    )
            elif min_pct is not None and not pct_passed:
                maybe_reasons.append(
                    f"Requires minimum {float(min_pct):.1f}% marks; enter your percentage to confirm"
                )
            elif min_cgpa is not None and not cgpa_passed:
                maybe_reasons.append(
                    f"Requires minimum {float(min_cgpa):.2f} CGPA; enter your CGPA to confirm"
                )

    # 7. Other conditions (including optional gender rules and unverified conditions)
    other_fails, other_maybes = _evaluate_other_conditions(
        scholarship.get("other_conditions"), profile
    )
    fail_reasons.extend(other_fails)
    maybe_reasons.extend(other_maybes)

    # Final verdict determination
    if fail_reasons:
        return "no", fail_reasons

    if maybe_reasons:
        # Combine positive matches first so the student sees what fits, followed by what to verify
        return "maybe", pass_reasons + maybe_reasons

    return "yes", pass_reasons


def rank(
    scholarships: list[dict[str, Any]],
    profile: dict[str, Any],
    today: date | str | None = None,
) -> RankedResults:
    """
    Filter and rank scholarships for a student profile using deterministic scoring.

    Scoring formula (Section 7):
      - Drop status `"no"` and drop expired (`deadline_iso < today`).
      - Base score: `50` for `"yes"`, `25` for `"maybe"`.
      - `+20` if `funding == "full"`.
      - `+15` if `profile["want"]` matches `scholarship["kind"]`.
      - `+10` if `days_left > 7`.
      - `+5` if `0 <= days_left <= 7` (also sets `urgent = True` for URGENT badge).
      - `-10` if `deadline_confirmed` is False.
      - `-5` if `deadline_iso` is None (deadline unknown).

    Sorting:
      - Primary: `score` descending.
      - Secondary: `days_left` ascending (with `None` placed after known dates).

    Transparency lists attached to the returned `RankedResults` list:
      - `results.closed_recently`: scholarships whose deadline passed within the last 30 days.
      - `results.not_eligible`: scholarships excluded due to status `"no"` (non-expired or >30 days ago).

    Args:
        scholarships: List of scholarship dicts.
        profile: Student profile dict.
        today: Reference date (`datetime.date` or `'YYYY-MM-DD'`). Defaults to `date.today()`.

    Returns:
        A `RankedResults` list (subclass of `list[dict[str, Any]]`) containing the
        sorted eligible/maybe matches, with `.closed_recently` and `.not_eligible` attributes.
    """
    resolved_today = parse_iso_date(today) or date.today()
    student_want = str(profile.get("want") or "any").strip().lower()

    ranked_matches: list[dict[str, Any]] = []
    closed_recently: list[dict[str, Any]] = []
    not_eligible: list[dict[str, Any]] = []

    for item in scholarships:
        entry = copy.deepcopy(item)
        deadline_date = parse_iso_date(entry.get("deadline_iso"))
        deadline_confirmed = bool(entry.get("deadline_confirmed", False))

        days_left: int | None = None
        if deadline_date is not None:
            days_left = (deadline_date - resolved_today).days

        status, reasons = check(entry, profile, resolved_today)
        entry["days_left"] = days_left
        entry["status"] = status
        entry["reasons"] = reasons
        entry["urgent"] = bool(days_left is not None and 0 <= days_left <= 7)

        # Check if expired (deadline_iso < today)
        if days_left is not None and days_left < 0:
            days_since_closed = abs(days_left)
            entry["days_since_closed"] = days_since_closed
            entry["score"] = 0
            if 1 <= days_since_closed <= 30:
                closed_recently.append(entry)
            else:
                not_eligible.append(entry)
            continue

        # Drop status "no"
        if status == "no":
            entry["score"] = 0
            not_eligible.append(entry)
            continue

        # Calculate deterministic score for "yes" and "maybe"
        score = 50 if status == "yes" else 25

        if str(entry.get("funding") or "").strip().lower() == "full":
            score += 20

        kind = str(entry.get("kind") or "").strip().lower()
        if student_want and student_want != "any" and student_want == kind:
            score += 15

        if days_left is not None:
            if days_left > 7:
                score += 10
            elif 0 <= days_left <= 7:
                score += 5
        else:
            # Deadline unknown
            score -= 5

        if not deadline_confirmed:
            score -= 10

        entry["score"] = score
        ranked_matches.append(entry)

    # Sort by score desc, then days_left asc (None goes last)
    ranked_matches.sort(
        key=lambda x: (
            -int(x["score"]),
            x["days_left"] if x["days_left"] is not None else 999999,
            str(x.get("name") or ""),
        )
    )

    # Sort closed_recently by most recently closed first
    closed_recently.sort(key=lambda x: x.get("days_since_closed", 999))

    return RankedResults(
        ranked_items=ranked_matches,
        closed_recently=closed_recently,
        not_eligible=not_eligible,
    )
