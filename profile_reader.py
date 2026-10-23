"""
profile_reader.py — Vision AI Component for Reading Student Marksheets.

Uses the multimodal LLM abstraction (`llm.ask`) to inspect a photo or scan of a
Pakistani board marksheet (Matric/Intermediate BISE) or university transcript
and return structured JSON that pre-fills the student profile form (editable by
the student before searching).
"""

from __future__ import annotations

from typing import Any

from llm import LLMError, ask, parse_json_object

VISION_PROMPT = """You are an academic document reader for Pakistani students.
Examine the attached image carefully.

First, determine whether the image is an academic marksheet, result card, transcript, or certificate.
Return ONLY a valid JSON object with the exact keys below (no markdown, no extra text):

{
  "is_marksheet": true or false,
  "level": "intermediate" | "undergraduate" | "masters" | null,
  "percentage": number (0 to 100) or null,
  "cgpa": number (0.0 to 4.0) or null,
  "board_or_university": "string or null",
  "year": "string or null",
  "confidence": "low" | "medium" | "high",
  "note": "short polite message if image is blurry or not a marksheet, else null"
}

Strict rules:
1. If the image is NOT a marksheet, transcript, or academic result card, set "is_marksheet": false, set all data fields to null, set "confidence": "low", and write a polite explanation in "note".
2. NEVER guess or invent numbers. If percentage or CGPA is not clearly visible on the document, set it to null. If total marks and obtained marks are clearly shown (e.g., 858 / 1100), you may compute the exact percentage (e.g., 78.0).
3. For HSSC / FSc / FA / ICom / Intermediate board results, set "level" to "intermediate" (or "undergraduate" if applying for next degree — keep "intermediate" if the card is an Intermediate result card).
4. For BS / BE / BBA / BSc university transcripts, set "level" to "undergraduate".
5. For MS / MPhil / MBA transcripts, set "level" to "masters".
6. Output ONLY raw JSON.
"""


def _sanitize_profile_json(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and normalize the extracted JSON fields from the vision model.

    Args:
        raw: Dictionary parsed from the LLM response.

    Returns:
        Sanitized dictionary with guaranteed keys and validated numeric ranges.
    """
    is_marksheet = bool(raw.get("is_marksheet", True))

    # Normalize level
    raw_level = str(raw.get("level") or "").strip().lower()
    level: str | None = None
    if raw_level in ("intermediate", "hssc", "fsc", "fa", "icom", "ics", "matric"):
        level = "intermediate"
    elif raw_level in ("undergraduate", "bs", "bsc", "be", "bba", "bachelors", "bachelor"):
        level = "undergraduate"
    elif raw_level in ("masters", "master", "ms", "mphil", "mba", "ma", "msc"):
        level = "masters"

    # Normalize percentage (0 - 100)
    percentage: float | None = None
    if raw.get("percentage") is not None:
        try:
            pct_val = round(float(raw["percentage"]), 2)
            if 0.0 <= pct_val <= 100.0:
                percentage = pct_val
        except (TypeError, ValueError):
            percentage = None

    # Normalize CGPA (0 - 4.0, or up to 5.0 if a 5-point scale is noted)
    cgpa: float | None = None
    if raw.get("cgpa") is not None:
        try:
            cgpa_val = round(float(raw["cgpa"]), 2)
            if 0.0 <= cgpa_val <= 4.0:
                cgpa = cgpa_val
        except (TypeError, ValueError):
            cgpa = None

    board_or_uni = raw.get("board_or_university")
    board_or_uni_str = str(board_or_uni).strip() if board_or_uni else None

    year = raw.get("year")
    year_str = str(year).strip() if year else None

    confidence = str(raw.get("confidence") or "low").strip().lower()
    if confidence not in ("low", "medium", "high"):
        confidence = "low"

    note = raw.get("note")
    note_str = str(note).strip() if note else None

    if not is_marksheet and not note_str:
        note_str = (
            "This image does not appear to be an academic marksheet or transcript. "
            "Please upload a clear photo of your result card or enter your marks manually below."
        )

    return {
        "ok": is_marksheet,
        "is_marksheet": is_marksheet,
        "level": level,
        "percentage": percentage,
        "cgpa": cgpa,
        "board_or_university": board_or_uni_str,
        "year": year_str,
        "confidence": confidence,
        "note": note_str,
        "error": None if is_marksheet else note_str,
    }


def read_marksheet(image_bytes: bytes, mime: str = "image/png") -> dict[str, Any]:
    """
    Read a student's marksheet image using the vision LLM and return structured data.

    Args:
        image_bytes: Raw image bytes (PNG, JPEG, WEBP).
        mime: MIME type of the uploaded image.

    Returns:
        Dictionary with keys:
        `ok`, `is_marksheet`, `level`, `percentage`, `cgpa`,
        `board_or_university`, `year`, `confidence`, `note`, `error`.
    """
    if not image_bytes:
        return {
            "ok": False,
            "is_marksheet": False,
            "level": None,
            "percentage": None,
            "cgpa": None,
            "board_or_university": None,
            "year": None,
            "confidence": "low",
            "note": "No image data received.",
            "error": "No image data received.",
        }

    try:
        raw_response = ask(
            prompt=VISION_PROMPT,
            image_bytes=image_bytes,
            mime=mime,
            max_tokens=900,
        )
        parsed = parse_json_object(raw_response)
        return _sanitize_profile_json(parsed)
    except LLMError as exc:
        return {
            "ok": False,
            "is_marksheet": False,
            "level": None,
            "percentage": None,
            "cgpa": None,
            "board_or_university": None,
            "year": None,
            "confidence": "low",
            "note": None,
            "error": (
                f"{exc} You can still enter your percentage/CGPA manually in the form below."
            ),
        }
    except Exception:
        return {
            "ok": False,
            "is_marksheet": False,
            "level": None,
            "percentage": None,
            "cgpa": None,
            "board_or_university": None,
            "year": None,
            "confidence": "low",
            "note": None,
            "error": (
                "Could not read the marksheet clearly from this photo. "
                "Please try a clearer photo or type your marks directly into the form below."
            ),
        }
