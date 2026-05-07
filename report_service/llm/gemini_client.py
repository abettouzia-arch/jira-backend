"""
Gemini client for Report Service.

Generates human-readable migration report text with:
- fallback
- retry
- clean logging
"""

import json
import logging
import os
import time

import google.generativeai as genai

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.5-flash"
MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 3


def get_gemini_api_key() -> str:
    """Return Gemini API key from environment."""
    return os.getenv("GEMINI_API_KEY", "")


def get_gemini_model() -> str:
    """Return Gemini model name from environment."""
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


def is_gemini_available() -> bool:
    """Return True if Gemini API key is configured."""
    return bool(get_gemini_api_key().strip())


def generate_report_text(prompt: str, fallback_text: str = "") -> dict:
    """
    Generate report text using Gemini.

    Returns:
        {
          "used_ai": true/false,
          "model": "...",
          "text": "...",
          "error": ""
        }
    """
    if not prompt or not prompt.strip():
        return {
            "used_ai": False,
            "model": get_gemini_model(),
            "text": fallback_text,
            "error": "Empty prompt.",
        }

    if not is_gemini_available():
        logger.warning("Gemini API key not configured. Using fallback report text.")
        return {
            "used_ai": False,
            "model": get_gemini_model(),
            "text": fallback_text,
            "error": "Gemini API key not configured.",
        }

    genai.configure(api_key=get_gemini_api_key())
    model_name = get_gemini_model()
    model = genai.GenerativeModel(model_name)

    last_error = ""

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                "Generating AI report text with Gemini model=%s attempt=%d/%d",
                model_name,
                attempt,
                MAX_RETRIES,
            )

            response = model.generate_content(prompt)
            text = getattr(response, "text", "") or ""

            if not text.strip():
                raise ValueError("Gemini returned empty text.")

            logger.info("AI report text generated successfully.")
            return {
                "used_ai": True,
                "model": model_name,
                "text": text.strip(),
                "error": "",
            }

        except Exception as error:  # pylint: disable=broad-exception-caught
            last_error = str(error)
            logger.warning(
                "Gemini report generation failed on attempt %d/%d: %s",
                attempt,
                MAX_RETRIES,
                last_error,
            )

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)

    logger.warning("Using fallback report text after Gemini failure.")
    return {
        "used_ai": False,
        "model": model_name,
        "text": fallback_text,
        "error": last_error,
    }


def generate_report_json(prompt: str, fallback_json: dict | None = None) -> dict:
    """
    Optional JSON-generation helper for future structured AI reports.
    """
    fallback_json = fallback_json or {}

    result = generate_report_text(
        prompt=prompt,
        fallback_text=json.dumps(fallback_json, ensure_ascii=False),
    )

    try:
        parsed = json.loads(result["text"])
        return {
            "used_ai": result["used_ai"],
            "model": result["model"],
            "data": parsed,
            "error": result["error"],
        }
    except json.JSONDecodeError as error:
        logger.warning("Gemini JSON parsing failed: %s", error)
        return {
            "used_ai": False,
            "model": result["model"],
            "data": fallback_json,
            "error": str(error),
        }
