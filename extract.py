"""
extract.py — Scholarship Webpage / PDF Fetching and Structured LLM Extraction.

Responsibilities:
  1. Sanitize and fetch public scholarship URLs (HTML or PDF) with a 20s timeout
     and standard User-Agent.
  2. Detect JavaScript-only pages that return almost no text and prompt the user
     to use the paste-text fallback.
  3. Prompt the LLM (`llm.ask`) to extract structured JSON strictly conforming to
     the Section 5 schema, never guessing missing numbers or dates.
  4. Retry JSON parsing once with a stricter prompt if the initial response is
     malformed, and validate all fields against the schema.
"""

from __future__ import annotations

import io
import re
from datetime import date
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

from eligibility import parse_iso_date
from llm import LLMError, ask, parse_json_object

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36 WazifaSaathi/1.0"
)
MAX_TEXT_CHARS = 12_000
MIN_MEANINGFUL_TEXT_CHARS = 100

BROWSER_FALLBACK_MESSAGE = (
    "This page needs a browser to load. Please paste the text of the notice below"
)

ALLOWED_KINDS = {"need_based", "merit_based", "study_abroad", "skills"}
ALLOWED_FUNDING = {"full", "partial", "unknown"}
ALLOWED_LEVELS = {"intermediate", "undergraduate", "masters", "phd"}


class ExtractionError(RuntimeError):
    """Raised when fetching or extracting a scholarship notice fails."""

    def __init__(self, message: str, needs_browser: bool = False) -> None:
        super().__init__(message)
        self.needs_browser = needs_browser


def sanitize_url(url: str) -> str:
    """
    Validate and sanitize a user-provided or source URL.

    Only `http://` and `https://` schemes on public hosts are permitted.

    Args:
        url: Raw URL string.

    Returns:
        Cleaned URL string.

    Raises:
        ExtractionError: If the URL scheme or host is invalid or unsafe.
    """
    if not url or not str(url).strip():
        raise ExtractionError("Please enter a valid scholarship URL starting with https://")

    cleaned = str(url).strip()
    parsed = urlparse(cleaned)

    if parsed.scheme.lower() not in ("http", "https"):
        raise ExtractionError(
            "Only public http:// and https:// scholarship links are supported."
        )
    if not parsed.netloc or "." not in parsed.netloc:
        raise ExtractionError("Please enter a complete web address (e.g., https://hec.gov.pk/...).")

    host_lower = parsed.hostname.lower() if parsed.hostname else ""
    if host_lower in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
        raise ExtractionError("Local network URLs are not allowed.")

    return cleaned


def _extract_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract plain text from PDF bytes using `pypdf`."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages_text: list[str] = []
    for page in reader.pages[:25]:
        page_str = page.extract_text() or ""
        if page_str.strip():
            pages_text.append(page_str.strip())
    combined = "\n\n".join(pages_text)
    collapsed = re.sub(r"\s+", " ", combined).strip()
    return collapsed[:MAX_TEXT_CHARS]


def _extract_html_text(html_text: str) -> str:
    """Strip scripts, styles, navigation, and footers from HTML and collapse whitespace."""
    soup = BeautifulSoup(html_text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "noscript", "svg", "iframe"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    collapsed = re.sub(r"\s+", " ", text).strip()
    return collapsed[:MAX_TEXT_CHARS]


def fetch(url: str, timeout: int = 12) -> dict[str, Any]:
    """
    Fetch a scholarship webpage or PDF document and extract clean text.

    Args:
        url: Public HTTP/HTTPS URL to fetch.
        timeout: Request timeout in seconds (default 20).

    Returns:
        Dictionary with keys:
        `url` (str), `content_type` (str), `text` (str), `needs_browser` (bool).

    Raises:
        ExtractionError: On network error, non-200 status, or JS-rendered empty page.
    """
    safe_url = sanitize_url(url)

    try:
        try:
            response = requests.get(
                safe_url,
                headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
                timeout=timeout,
                allow_redirects=True,
            )
        except requests.exceptions.SSLError:
            # Fallback for Pakistani gov domains (.gov.pk) with missing intermediate CA certs
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(
                safe_url,
                headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
                timeout=timeout,
                allow_redirects=True,
                verify=False,
            )
        response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise ExtractionError(
            "The scholarship website took too long to respond (timed out after 20s). "
            "You can copy and paste the notice text directly below."
        ) from exc
    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else "error"
        raise ExtractionError(
            f"Could not load page (HTTP {status_code}). The website may block automated requests. "
            "Please copy and paste the scholarship text below."
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise ExtractionError(
            "Could not connect to the website. Please check the link or paste the notice text below."
        ) from exc

    content_type = (response.headers.get("Content-Type") or "").lower()
    is_pdf = "application/pdf" in content_type or safe_url.lower().split("?")[0].endswith(".pdf")

    try:
        if is_pdf:
            extracted_text = _extract_pdf_bytes(response.content)
        else:
            extracted_text = _extract_html_text(response.text)
    except Exception as exc:
        raise ExtractionError(
            "Could not parse the document content. Please paste the text of the notice below."
        ) from exc

    if len(extracted_text.strip()) < MIN_MEANINGFUL_TEXT_CHARS:
        raise ExtractionError(BROWSER_FALLBACK_MESSAGE, needs_browser=True)

    return {
        "url": safe_url,
        "content_type": "application/pdf" if is_pdf else "text/html",
        "text": extracted_text,
        "needs_browser": False,
    }


def _build_extraction_prompt(
    text: str,
    source_url: str,
    today_iso: str,
    hint: str | None = None,
    strict_retry: bool = False,
) -> str:
    """Construct the LLM prompt for structured scholarship JSON extraction."""
    hint_line = f"Target scholarship hint: {hint}\n" if hint else ""
    retry_warning = (
        "\nIMPORTANT RETRY INSTRUCTION: Your previous response was not valid JSON. "
        "Output ONLY a single valid JSON object starting with '{' and ending with '}'. "
        "Do NOT include markdown fences or explanations.\n"
        if strict_retry
        else ""
    )

    return f"""You are a precise data extraction engine for Pakistani student scholarships.
Today's date is {today_iso}.
Source URL: {source_url}
{hint_line}{retry_warning}
Read the scholarship notice text below and extract a single JSON object with EXACTLY these fields:

{{
  "id": "unique-lowercase-slug-for-scholarship",
  "name": "string, official name of the scholarship",
  "provider": "string, organization or government body offering it",
  "kind": "need_based | merit_based | study_abroad | skills",
  "funding": "full | partial | unknown",
  "benefits": "short text e.g. 'tuition + monthly stipend', or null",
  "level": ["intermediate", "undergraduate", "masters", "phd"],
  "provinces": ["all"] or specific list like ["Sindh", "Punjab"],
  "fields": ["all"] or specific list like ["engineering", "medical", "cs"],
  "max_family_income_pkr": number (MONTHLY family income limit in PKR; if annual is stated, divide by 12) or null,
  "min_percentage": number (0-100) or null,
  "min_cgpa": number (0.0-4.0) or null,
  "other_conditions": ["short strings, e.g. 'Pakistani citizen', 'enrolled in a public university'"],
  "documents": ["CNIC", "Domicile", "Marksheet", ...],
  "open_date_iso": "YYYY-MM-DD or null",
  "deadline_iso": "YYYY-MM-DD or null",
  "deadline_confirmed": true or false,
  "apply_url": "official application link or null",
  "source_url": "{source_url}",
  "evidence": "the exact sentence or line copied from the text that supports the deadline and eligibility, or null",
  "note": "if the page lists multiple scholarships, note that you extracted the first main one, else null"
}}

GOLDEN RULES (MUST FOLLOW STRICTLY):
1. Return ONLY valid JSON. No prose before or after.
2. Any value that is NOT clearly and explicitly stated in the text MUST be null (orfalse for deadline_confirmed). NEVER guess or invent numbers, income limits, percentages, or dates.
3. Copy the exact supporting sentence from the text into "evidence".
4. Dates ("open_date_iso", "deadline_iso") MUST be in ISO format YYYY-MM-DD. Do NOT guess the year; if the year is missing or ambiguous, set deadline_iso to null and deadline_confirmed to false.
5. If the page lists several scholarships, extract the first main one (matching the hint if given) and add a short explanation in "note".

SCHOLARSHIP PAGE TEXT:
\"\"\"
{text[:MAX_TEXT_CHARS]}
\"\"\"
"""


def _slugify(value: str) -> str:
    """Create a URL-safe slug for scholarship IDs."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:64] or "extracted-scholarship"


def validate_scholarship_schema(
    raw: dict[str, Any],
    source_url: str = "pasted_text",
    today: date | str | None = None,
    fetched_by: str = "ai_extraction",
) -> dict[str, Any]:
    """
    Validate and normalize a dictionary against the Section 5 scholarship schema.

    Guarantees all required keys exist with valid types, ISO dates, and nulls
    where data is uncertain.

    Args:
        raw: Raw dictionary from LLM or JSON file.
        source_url: URL or identifier where the data originated.
        today: Verification date (defaults to `date.today()`).
        fetched_by: `"ai_extraction"` or `"manual"`.

    Returns:
        Validated scholarship dictionary with exact schema fields.
    """
    resolved_today = (parse_iso_date(today) or date.today()).isoformat()

    name = str(raw.get("name") or "Untitled Scholarship").strip()
    provider = str(raw.get("provider") or "Official Provider").strip()
    raw_id = str(raw.get("id") or "").strip()
    sch_id = raw_id if raw_id else _slugify(f"{provider}-{name}")

    kind = str(raw.get("kind") or "need_based").strip().lower()
    if kind not in ALLOWED_KINDS:
        kind = "need_based"

    funding = str(raw.get("funding") or "unknown").strip().lower()
    if funding not in ALLOWED_FUNDING:
        funding = "unknown"

    benefits_raw = raw.get("benefits")
    benefits = str(benefits_raw).strip() if benefits_raw else None

    # Level validation
    raw_levels = raw.get("level")
    levels: list[str] = []
    if isinstance(raw_levels, list):
        for lvl in raw_levels:
            norm_lvl = str(lvl).strip().lower()
            if norm_lvl in ALLOWED_LEVELS and norm_lvl not in levels:
                levels.append(norm_lvl)
    elif isinstance(raw_levels, str) and raw_levels.strip().lower() in ALLOWED_LEVELS:
        levels.append(raw_levels.strip().lower())

    # Provinces validation
    raw_provinces = raw.get("provinces")
    provinces: list[str] = ["all"]
    if isinstance(raw_provinces, list) and raw_provinces:
        cleaned_prov = [str(p).strip() for p in raw_provinces if p and str(p).strip()]
        if cleaned_prov:
            provinces = cleaned_prov

    # Fields validation
    raw_fields = raw.get("fields")
    fields: list[str] = ["all"]
    if isinstance(raw_fields, list) and raw_fields:
        cleaned_fields = [str(f).strip() for f in raw_fields if f and str(f).strip()]
        if cleaned_fields:
            fields = cleaned_fields

    # Numeric limits (null if missing or invalid)
    max_income: float | int | None = None
    if raw.get("max_family_income_pkr") is not None:
        try:
            inc_val = float(raw["max_family_income_pkr"])
            if inc_val > 0:
                max_income = int(inc_val) if inc_val.is_integer() else round(inc_val, 2)
        except (TypeError, ValueError):
            max_income = None

    min_pct: float | None = None
    if raw.get("min_percentage") is not None:
        try:
            pct_val = round(float(raw["min_percentage"]), 2)
            if 0 < pct_val <= 100:
                min_pct = pct_val
        except (TypeError, ValueError):
            min_pct = None

    min_cgpa: float | None = None
    if raw.get("min_cgpa") is not None:
        try:
            cgpa_val = round(float(raw["min_cgpa"]), 2)
            if 0 < cgpa_val <= 4.0:
                min_cgpa = cgpa_val
        except (TypeError, ValueError):
            min_cgpa = None

    # Lists of strings
    raw_conditions = raw.get("other_conditions")
    other_conditions: list[str] = []
    if isinstance(raw_conditions, list):
        other_conditions = [str(c).strip() for c in raw_conditions if c and str(c).strip()]

    raw_docs = raw.get("documents")
    documents: list[str] = []
    if isinstance(raw_docs, list):
        documents = [str(d).strip() for d in raw_docs if d and str(d).strip()]

    # ISO dates
    open_date = parse_iso_date(raw.get("open_date_iso"))
    open_date_iso = open_date.isoformat() if open_date else None

    deadline_date = parse_iso_date(raw.get("deadline_iso"))
    deadline_iso = deadline_date.isoformat() if deadline_date else None

    deadline_confirmed = bool(raw.get("deadline_confirmed", False)) and (deadline_iso is not None)

    apply_url_raw = raw.get("apply_url")
    apply_url = str(apply_url_raw).strip() if apply_url_raw else (
        source_url if source_url.startswith("http") else None
    )

    resolved_source_url = str(raw.get("source_url") or source_url).strip()
    evidence_raw = raw.get("evidence")
    evidence = str(evidence_raw).strip() if evidence_raw else None

    note_raw = raw.get("note")
    if note_raw and str(note_raw).strip():
        note_str = str(note_raw).strip()
        if evidence:
            evidence = f"{evidence} (Note: {note_str})"
        else:
            evidence = f"Note: {note_str}"

    last_verified_raw = raw.get("last_verified")
    if fetched_by == "ai_extraction":
        last_verified: str | None = resolved_today
    else:
        parsed_lv = parse_iso_date(last_verified_raw)
        last_verified = parsed_lv.isoformat() if parsed_lv else None

    return {
        "id": sch_id,
        "name": name,
        "provider": provider,
        "kind": kind,
        "funding": funding,
        "benefits": benefits,
        "level": levels,
        "provinces": provinces,
        "fields": fields,
        "max_family_income_pkr": max_income,
        "min_percentage": min_pct,
        "min_cgpa": min_cgpa,
        "other_conditions": other_conditions,
        "documents": documents,
        "open_date_iso": open_date_iso,
        "deadline_iso": deadline_iso,
        "deadline_confirmed": deadline_confirmed,
        "apply_url": apply_url,
        "source_url": resolved_source_url,
        "evidence": evidence,
        "last_verified": last_verified,
        "fetched_by": fetched_by if fetched_by in ("manual", "ai_extraction") else "ai_extraction",
    }


def extract_from_text(
    text: str,
    source_url: str = "pasted_text",
    today: date | str | None = None,
    hint: str | None = None,
) -> dict[str, Any]:
    """
    Extract a structured scholarship JSON object from raw webpage or notice text.

    Retries once with a stricter prompt if the first LLM output is not valid JSON.

    Args:
        text: Raw notice text (up to ~12,000 characters).
        source_url: Official page URL or `'pasted_text'`.
        today: Current date for `last_verified` (defaults to `date.today()`).
        hint: Optional scholarship name hint when a page contains multiple programmes.

    Returns:
        Validated scholarship dict matching Section 5 schema.

    Raises:
        ExtractionError: If text is too short or LLM extraction fails after retry.
    """
    cleaned_text = re.sub(r"\s+", " ", (text or "")).strip()
    if len(cleaned_text) < 30:
        raise ExtractionError(
            "Please provide at least a couple of sentences of scholarship notice text to analyse."
        )

    resolved_today = (parse_iso_date(today) or date.today()).isoformat()
    prompt = _build_extraction_prompt(
        text=cleaned_text,
        source_url=source_url,
        today_iso=resolved_today,
        hint=hint,
        strict_retry=False,
    )

    try:
        raw_output = ask(prompt=prompt, max_tokens=1500)
    except LLMError as exc:
        raise ExtractionError(str(exc)) from exc

    parsed: dict[str, Any] | None = None
    try:
        parsed = parse_json_object(raw_output)
    except ValueError:
        # Retry once with a stricter prompt as required by Section 8.2
        strict_prompt = _build_extraction_prompt(
            text=cleaned_text,
            source_url=source_url,
            today_iso=resolved_today,
            hint=hint,
            strict_retry=True,
        )
        try:
            retry_output = ask(prompt=strict_prompt, max_tokens=1500)
            parsed = parse_json_object(retry_output)
        except LLMError as exc:
            raise ExtractionError(str(exc)) from exc
        except ValueError as exc:
            raise ExtractionError(
                "Could not extract structured scholarship details from this text. "
                "Please try pasting just the main eligibility and deadline paragraph."
            ) from exc

    return validate_scholarship_schema(
        raw=parsed,
        source_url=source_url,
        today=resolved_today,
        fetched_by="ai_extraction",
    )


def extract_from_url(
    url: str,
    today: date | str | None = None,
    hint: str | None = None,
) -> dict[str, Any]:
    """
    Fetch a scholarship webpage or PDF URL and extract structured JSON via LLM.

    Args:
        url: Public HTTP/HTTPS URL of the scholarship page or PDF.
        today: Reference date for `last_verified` (defaults to `date.today()`).
        hint: Optional scholarship name hint.

    Returns:
        Validated scholarship dict matching Section 5 schema.

    Raises:
        ExtractionError: If fetching fails, page requires JS browser, or LLM fails.
    """
    fetched = fetch(url)
    return extract_from_text(
        text=fetched["text"],
        source_url=fetched["url"],
        today=today,
        hint=hint,
    )
