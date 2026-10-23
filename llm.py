"""
llm.py — LLM Provider Abstraction for ScholarMatch (Wazifa Saathi).

Supports two providers selected by environment variable (or Streamlit secret)
`LLM_PROVIDER` ("gemini" or "anthropic"):
  - gemini: official `google-genai` SDK, model read from `GEMINI_MODEL`
  - anthropic: official `anthropic` SDK, model read from `ANTHROPIC_MODEL`

Both providers support text and multimodal image input.
If the primary provider fails (e.g., quota limit, timeout, network error),
`ask()` automatically retries once with the secondary provider if its API key
is configured.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

ENV_PATH = Path(__file__).resolve().parent / ".env"

try:
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=ENV_PATH, override=True)
except ImportError:
    load_dotenv = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
FALLBACK_GEMINI_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3-flash-preview",
]


class LLMError(RuntimeError):
    """Raised when both primary and fallback LLM providers fail or lack keys."""


def get_config(key: str, default: str | None = None) -> str | None:
    """
    Read a configuration value from `.env` / environment variables first, falling
    back to Streamlit secrets (`st.secrets`) if running in Streamlit Cloud.

    Args:
        key: Environment variable or secret key name.
        default: Default value if the key is not found or empty.

    Returns:
        The resolved configuration string or `default`.
    """
    if load_dotenv is not None and ENV_PATH.exists():
        try:
            load_dotenv(dotenv_path=ENV_PATH, override=True)
        except Exception:
            pass

    val = os.environ.get(key)
    if val is not None and str(val).strip() != "":
        return str(val).strip()

    try:
        import streamlit as st

        if key in st.secrets:
            secret_val = st.secrets[key]
            if secret_val is not None and str(secret_val).strip() != "":
                return str(secret_val).strip()
    except Exception:
        pass

    return default


def is_ai_configured() -> bool:
    """
    Check whether at least one valid-looking API key is configured.

    Returns:
        True if either GEMINI_API_KEY or ANTHROPIC_API_KEY is set and not a placeholder.
    """
    gemini_key = get_config("GEMINI_API_KEY", "")
    anthropic_key = get_config("ANTHROPIC_API_KEY", "")
    placeholders = {"", "your_gemini_api_key_here", "your_anthropic_api_key_here"}
    return (gemini_key not in placeholders) or (anthropic_key not in placeholders)


def _has_valid_key(provider: str) -> bool:
    """Return True if the specified provider has a non-placeholder API key."""
    placeholders = {"", "your_gemini_api_key_here", "your_anthropic_api_key_here"}
    if provider == "gemini":
        key = get_config("GEMINI_API_KEY", "")
        return bool(key and key not in placeholders)
    if provider == "anthropic":
        key = get_config("ANTHROPIC_API_KEY", "")
        return bool(key and key not in placeholders)
    return False


def _call_gemini(
    prompt: str,
    image_bytes: bytes | None = None,
    mime: str | None = None,
    max_tokens: int = 800,
) -> str:
    """
    Call Google Gemini using the official `google-genai` SDK.

    Automatically upgrades retired `gemini-2.5-flash` model references and falls
    back across available Gemini Flash models if one experiences a 503 spike.
    """
    api_key = get_config("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise LLMError("GEMINI_API_KEY is not set.")

    configured_model = get_config("GEMINI_MODEL", DEFAULT_GEMINI_MODEL) or DEFAULT_GEMINI_MODEL
    if configured_model in ("gemini-2.5-flash", "models/gemini-2.5-flash"):
        configured_model = DEFAULT_GEMINI_MODEL

    candidate_models = [configured_model] + [
        m for m in FALLBACK_GEMINI_MODELS if m != configured_model
    ]

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    contents: list[Any] = []
    if image_bytes is not None:
        resolved_mime = mime or "image/png"
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type=resolved_mime))
    contents.append(prompt)

    last_exc: Exception | None = None
    effective_tokens = max(int(max_tokens), 400)

    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    max_output_tokens=effective_tokens,
                    temperature=0.2,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
            text = getattr(response, "text", None)
            if text and str(text).strip():
                return str(text).strip()
        except Exception as exc:
            last_exc = exc
            continue

    if last_exc is not None:
        raise last_exc
    raise LLMError("Gemini returned an empty response.")


def _call_anthropic(
    prompt: str,
    image_bytes: bytes | None = None,
    mime: str | None = None,
    max_tokens: int = 800,
) -> str:
    """Call Anthropic Claude using the official `anthropic` SDK."""
    api_key = get_config("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your_anthropic_api_key_here":
        raise LLMError("ANTHROPIC_API_KEY is not set.")

    model_name = (
        get_config("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
        or "claude-3-5-sonnet-latest"
    )

    import anthropic

    client = anthropic.Anthropic(api_key=api_key, timeout=25.0)
    content_blocks: list[dict[str, Any]] = []

    if image_bytes is not None:
        resolved_mime = mime or "image/png"
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        content_blocks.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": resolved_mime,
                    "data": b64_image,
                },
            }
        )

    content_blocks.append({"type": "text", "text": prompt})

    message = client.messages.create(
        model=model_name,
        max_tokens=max_tokens,
        temperature=0.2,
        messages=[{"role": "user", "content": content_blocks}],
    )

    parts: list[str] = []
    for block in getattr(message, "content", []):
        block_text = getattr(block, "text", None)
        if block_text:
            parts.append(str(block_text))

    result = "\n".join(parts).strip()
    if not result:
        raise LLMError("Anthropic returned an empty response.")
    return result


def ask(
    prompt: str,
    image_bytes: bytes | None = None,
    mime: str | None = None,
    max_tokens: int = 800,
) -> str:
    """
    Send a text (and optional image) prompt to the configured LLM provider.

    Selects the primary provider via `LLM_PROVIDER` ("gemini" or "anthropic").
    If the primary provider fails due to quota, network, or missing key,
    automatically retries once with the other provider if its API key exists.
    """
    configured_provider = (get_config("LLM_PROVIDER", "gemini") or "gemini").lower()
    if configured_provider not in ("gemini", "anthropic"):
        configured_provider = "gemini"

    primary = configured_provider
    secondary = "anthropic" if primary == "gemini" else "gemini"

    if not _has_valid_key(primary) and _has_valid_key(secondary):
        primary, secondary = secondary, primary

    dispatch = {
        "gemini": _call_gemini,
        "anthropic": _call_anthropic,
    }

    primary_error: Exception | None = None
    if _has_valid_key(primary):
        try:
            return dispatch[primary](
                prompt=prompt,
                image_bytes=image_bytes,
                mime=mime,
                max_tokens=max_tokens,
            )
        except Exception as exc:
            primary_error = exc
            logger.warning("Primary LLM provider '%s' failed: %s", primary, exc)

    if _has_valid_key(secondary):
        try:
            logger.info("Retrying LLM call with fallback provider '%s'.", secondary)
            return dispatch[secondary](
                prompt=prompt,
                image_bytes=image_bytes,
                mime=mime,
                max_tokens=max_tokens,
            )
        except Exception as secondary_exc:
            logger.warning("Fallback LLM provider '%s' failed: %s", secondary, secondary_exc)
            raise LLMError(
                "AI is busy, please try again in a minute."
            ) from secondary_exc

    if primary_error is not None:
        raise LLMError("AI is busy, please try again in a minute.") from primary_error

    raise LLMError(
        "No LLM API key configured. Set GEMINI_API_KEY or ANTHROPIC_API_KEY in .env or Streamlit secrets."
    )


def clean_json_text(raw_text: str) -> str:
    """Strip Markdown code fences and isolate the JSON object substring."""
    if not raw_text:
        return ""
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return cleaned[first_brace : last_brace + 1]
    return cleaned


def parse_json_object(raw_text: str) -> dict[str, Any]:
    """Robustly parse a JSON object from LLM output text."""
    cleaned = clean_json_text(raw_text)
    if not cleaned:
        raise ValueError("Empty response from LLM when expecting JSON.")
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse JSON from LLM output: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ValueError("Expected a JSON object (dictionary), got another JSON type.")
    return parsed
