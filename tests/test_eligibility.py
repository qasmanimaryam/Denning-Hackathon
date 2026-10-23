"""
tests/test_eligibility.py — Unit Tests for Wazifa Saathi Deterministic Rules.

Covers:
  1. Full match returning "yes" when all conditions pass and nothing is unknown.
  2. Wrong degree level returning "no".
  3. Wrong province returning "no".
  4. Province "all" matching any student province.
  5. Monthly family income above `max_family_income_pkr` returning "no".
  6. Monthly family income at or below `max_family_income_pkr` passing.
  7. Yearly income period conversion (`income_period="yearly"`) to monthly PKR.
  8. Marks (percentage and CGPA) below minimum returning "no".
  9. Null fields (`max_family_income_pkr=None`, `min_percentage=None`, `deadline_iso=None`)
     becoming "maybe" with clear human-readable reasons.
  10. Unverified `other_conditions` becoming "maybe" and gender rule enforcement.
  11. Expired deadline (`deadline_iso < today`) returning "no" in `check()` and
      being dropped from active results in `rank()`.
  12. Urgent badge (`0 <= days_left <= 7`) and exact score calculation in `rank()`.
  13. Ranking sort order (score descending, then `days_left` ascending, `None` last).
  14. `closed_recently` capturing scholarships closed within the last 30 days (and
      ignoring those closed >30 days ago).
  15. Seed/demo entries (`demo_` prefix) tested end-to-end against the demo student profile.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from eligibility import check, rank

TODAY = date(2026, 10, 23)


def make_base_scholarship(**overrides: Any) -> dict[str, Any]:
    """Create a complete, verified base scholarship for deterministic testing."""
    base: dict[str, Any] = {
        "id": "test-scholarship-1",
        "name": "Test Sindh Need Scholarship",
        "provider": "Sindh Education Trust",
        "kind": "need_based",
        "funding": "full",
        "benefits": "Full tuition + PKR 10,000 monthly stipend",
        "level": ["undergraduate"],
        "provinces": ["Sindh"],
        "fields": ["all"],
        "max_family_income_pkr": 60000,
        "min_percentage": 65.0,
        "min_cgpa": None,
        "other_conditions": [],
        "documents": ["CNIC", "Domicile", "Marksheet"],
        "open_date_iso": "2026-09-01",
        "deadline_iso": "2026-11-15",
        "deadline_confirmed": True,
        "apply_url": "https://example.org/apply",
        "source_url": "https://example.org/scholarship",
        "evidence": "Open until 15 November 2026 for Sindh undergraduates.",
        "last_verified": "2026-10-23",
        "fetched_by": "manual",
    }
    base.update(overrides)
    return base


def make_demo_profile(**overrides: Any) -> dict[str, Any]:
    """Create the standard demo student profile (Sindh, undergraduate, 78%, 35k PKR, CS)."""
    profile: dict[str, Any] = {
        "level": "undergraduate",
        "province": "Sindh",
        "percentage": 78.0,
        "cgpa": None,
        "monthly_income_pkr": 35000,
        "field": "Computer Science",
        "want": "need_based",
    }
    profile.update(overrides)
    return profile


def test_01_eligible_yes_when_all_rules_pass() -> None:
    """A student meeting all known conditions with no unknown fields gets status 'yes'."""
    sch = make_base_scholarship()
    prof = make_demo_profile()
    status, reasons = check(sch, prof, TODAY)
    assert status == "yes"
    assert any("within limit" in r.lower() for r in reasons)
    assert any("meets minimum" in r.lower() for r in reasons)


def test_02_wrong_level_returns_no() -> None:
    """Student whose degree level is not in `scholarship['level']` gets 'no'."""
    sch = make_base_scholarship(level=["masters", "phd"])
    prof = make_demo_profile(level="undergraduate")
    status, reasons = check(sch, prof, TODAY)
    assert status == "no"
    assert any("masters" in r.lower() for r in reasons)


def test_03_wrong_province_returns_no() -> None:
    """Student from Punjab applying for a Sindh-only scholarship gets 'no'."""
    sch = make_base_scholarship(provinces=["Sindh"])
    prof = make_demo_profile(province="Punjab")
    status, reasons = check(sch, prof, TODAY)
    assert status == "no"
    assert any("sindh" in r.lower() for r in reasons)


def test_04_all_provinces_matches_any_province() -> None:
    """Scholarship with provinces=['all'] accepts students from any province."""
    sch = make_base_scholarship(provinces=["all"])
    prof = make_demo_profile(province="Balochistan")
    status, _ = check(sch, prof, TODAY)
    assert status == "yes"


def test_05_income_above_limit_returns_no() -> None:
    """Student with monthly income above `max_family_income_pkr` gets 'no'."""
    sch = make_base_scholarship(max_family_income_pkr=45000)
    prof = make_demo_profile(monthly_income_pkr=55000)
    status, reasons = check(sch, prof, TODAY)
    assert status == "no"
    assert any("exceeds limit" in r.lower() for r in reasons)


def test_06_income_at_or_below_limit_passes() -> None:
    """Student with monthly income exactly equal to or below the limit passes."""
    sch = make_base_scholarship(max_family_income_pkr=45000)
    prof = make_demo_profile(monthly_income_pkr=45000)
    status, _ = check(sch, prof, TODAY)
    assert status == "yes"


def test_07_yearly_income_period_converted_to_monthly() -> None:
    """Annual income limit (e.g. 600,000/year = 50,000/month) is converted consistently."""
    sch = make_base_scholarship(max_family_income_pkr=600000, income_period="yearly")
    prof_ok = make_demo_profile(monthly_income_pkr=48000)
    prof_high = make_demo_profile(monthly_income_pkr=55000)

    status_ok, _ = check(sch, prof_ok, TODAY)
    status_high, _ = check(sch, prof_high, TODAY)
    assert status_ok == "yes"
    assert status_high == "no"


def test_08_marks_below_minimum_returns_no() -> None:
    """Student with percentage or CGPA below minimum threshold gets 'no'."""
    sch_pct = make_base_scholarship(min_percentage=75.0)
    prof_low_pct = make_demo_profile(percentage=68.0)
    status_pct, reasons_pct = check(sch_pct, prof_low_pct, TODAY)
    assert status_pct == "no"
    assert any("below minimum" in r.lower() for r in reasons_pct)

    sch_cgpa = make_base_scholarship(min_percentage=None, min_cgpa=3.2)
    prof_low_cgpa = make_demo_profile(percentage=None, cgpa=2.7)
    status_cgpa, reasons_cgpa = check(sch_cgpa, prof_low_cgpa, TODAY)
    assert status_cgpa == "no"
    assert any("cgpa" in r.lower() for r in reasons_cgpa)


def test_09_null_fields_become_maybe_with_human_reasons() -> None:
    """Null income limit, null minimum marks, or null deadline produce 'maybe'."""
    sch = make_base_scholarship(
        max_family_income_pkr=None,
        min_percentage=None,
        min_cgpa=None,
        deadline_iso=None,
        deadline_confirmed=False,
    )
    prof = make_demo_profile()
    status, reasons = check(sch, prof, TODAY)
    assert status == "maybe"
    joined = " | ".join(reasons).lower()
    assert "income limit not published" in joined
    assert "minimum marks/cgpa requirement not published" in joined
    assert "deadline not published" in joined


def test_10_other_conditions_and_gender_rules() -> None:
    """Unverified other_conditions yield 'maybe'; explicit female-only rule rejects male."""
    sch_cond = make_base_scholarship(other_conditions=["Enrolled in a public university"])
    status_cond, reasons_cond = check(sch_cond, make_demo_profile(), TODAY)
    assert status_cond == "maybe"
    assert any("public university" in r.lower() for r in reasons_cond)

    sch_female = make_base_scholarship(other_conditions=["Female students only"])
    status_male, _ = check(sch_female, make_demo_profile(gender="male"), TODAY)
    status_female, _ = check(sch_female, make_demo_profile(gender="female"), TODAY)
    assert status_male == "no"
    assert status_female == "yes"


def test_11_expired_deadline_returned_as_no_and_dropped_in_rank() -> None:
    """Expired scholarships get status 'no' in `check()` and are dropped by `rank()`."""
    expired_sch = make_base_scholarship(
        id="expired-1",
        deadline_iso="2026-10-10",  # 13 days before TODAY (2026-10-23)
    )
    open_sch = make_base_scholarship(
        id="open-1",
        deadline_iso="2026-11-10",
    )
    prof = make_demo_profile()

    status_exp, reasons_exp = check(expired_sch, prof, TODAY)
    assert status_exp == "no"
    assert any("deadline passed" in r.lower() for r in reasons_exp)

    ranked = rank([expired_sch, open_sch], prof, TODAY)
    assert len(ranked) == 1
    assert ranked[0]["id"] == "open-1"


def test_12_urgent_badge_and_score_formula() -> None:
    """Scholarship closing in 0-7 days gets `urgent=True` and exact spec score."""
    urgent_sch = make_base_scholarship(
        id="urgent-sch",
        deadline_iso="2026-10-28",  # 5 days left from 2026-10-23
        funding="full",
        kind="need_based",
        deadline_confirmed=True,
    )
    prof = make_demo_profile(want="need_based")
    ranked = rank([urgent_sch], prof, TODAY)
    assert len(ranked) == 1
    item = ranked[0]
    assert item["days_left"] == 5
    assert item["urgent"] is True
    # Score: 50 (yes) + 20 (full) + 15 (want==kind) + 5 (0..7 days_left) = 90
    assert item["score"] == 90


def test_13_ranking_order_score_desc_then_days_left_asc() -> None:
    """`rank()` sorts by score descending, and breaks ties by fewer `days_left` first."""
    sch_sooner = make_base_scholarship(
        id="sooner",
        name="Sooner Scholarship",
        deadline_iso="2026-11-05",  # 13 days left (>7 -> +10)
    )
    sch_later = make_base_scholarship(
        id="later",
        name="Later Scholarship",
        deadline_iso="2026-12-01",  # 39 days left (>7 -> +10)
    )
    sch_maybe = make_base_scholarship(
        id="maybe-null-dl",
        name="Maybe Unconfirmed Scholarship",
        deadline_iso=None,
        deadline_confirmed=False,
    )

    prof = make_demo_profile()
    ranked = rank([sch_maybe, sch_later, sch_sooner], prof, TODAY)
    ids = [r["id"] for r in ranked]
    assert ids == ["sooner", "later", "maybe-null-dl"]


def test_14_closed_recently_captures_last_30_days_only() -> None:
    """`ranked.closed_recently` includes deadlines passed 1-30 days ago, not >30 days ago."""
    closed_10d = make_base_scholarship(
        id="closed-10d",
        deadline_iso="2026-10-13",  # 10 days ago
    )
    closed_60d = make_base_scholarship(
        id="closed-60d",
        deadline_iso="2026-08-15",  # 69 days ago
    )
    prof = make_demo_profile()
    ranked = rank([closed_10d, closed_60d], prof, TODAY)

    assert len(ranked) == 0
    closed_ids = [c["id"] for c in ranked.closed_recently]
    assert closed_ids == ["closed-10d"]


def test_15_seed_and_demo_entries_end_to_end() -> None:
    """Load `data/scholarships.seed.json` and verify `demo_` entries rank at the top."""
    seed_path = Path(__file__).resolve().parent.parent / "data" / "scholarships.seed.json"
    with seed_path.open("r", encoding="utf-8") as f:
        scholarships = json.load(f)

    demo_entries = [s for s in scholarships if str(s.get("id", "")).startswith("demo_")]
    assert len(demo_entries) == 3

    prof = make_demo_profile()
    ranked = rank(scholarships, prof, TODAY)

    # Top 2 matches should be the two open demo scholarships with status "yes"
    assert len(ranked) >= 2
    assert ranked[0]["id"] in ("demo_sindh_need_urgent", "demo_pak_cs_merit")
    assert ranked[0]["status"] == "yes"
    assert ranked[1]["status"] == "yes"

    # The 3rd demo entry (closed 11 days ago) should appear in closed_recently
    closed_ids = [c["id"] for c in ranked.closed_recently]
    assert "demo_recent_closed_grant" in closed_ids
