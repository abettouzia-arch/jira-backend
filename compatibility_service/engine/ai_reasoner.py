"""
AI reasoner for the Compatibility Service.

Uses an LLM to refine the deterministic compatibility baseline
with retrieved documentation evidence from the Knowledge Service.
"""

import json
import logging
import os

import google.generativeai as genai

logger = logging.getLogger(__name__)


ALLOWED_FINAL_STATUSES = [
    "COMPATIBLE",
    "PARTIAL",
    "INCOMPATIBLE",
    "REWRITE_REQUIRED",
    "NEEDS_REVIEW",
    "NEEDS_RECREATION",
    "DEPRECATED",
]

ALLOWED_RISK_LEVELS = [
    "INFO",
    "MINOR",
    "MAJOR",
    "BLOCKER",
]


def get_gemini_api_key() -> str:
    """Return Gemini API key from environment."""
    return os.getenv("GEMINI_API_KEY", "")


def get_gemini_model() -> str:
    """Return Gemini model name from environment."""
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def is_ai_available() -> bool:
    """Return True if Gemini configuration is available."""
    return bool(get_gemini_api_key().strip())


def _configure_gemini() -> None:
    """Configure Gemini client."""
    genai.configure(api_key=get_gemini_api_key())


def _build_prompt(
    component: dict,
    rule_result: dict,
    evidence_chunks: list[dict],
) -> str:
    """Build the LLM prompt for hybrid compatibility reasoning."""
    compact_evidence = [
        {
            "source": chunk.get("source", ""),
            "chunk_index": chunk.get("chunk_index", 0),
            "distance": chunk.get("distance"),
            "text": chunk.get("text", "")[:1200],
        }
        for chunk in evidence_chunks[:5]
    ]

    prompt = f"""
You are a Jira Cloud migration compatibility expert.

Your job is to refine a deterministic compatibility assessment using
retrieved documentation evidence.

You are given:
1. The original parsed component
2. The deterministic rule-based compatibility result
3. Documentation evidence retrieved via RAG

STRICT RULES:
- Be conservative.
- Do NOT mark clearly unsupported features as COMPATIBLE.
- If the rule-based result is INCOMPATIBLE because of obvious blocker features
  such as java_api, direct_database_query, filesystem_access, jdbc_connection_usage,
  keep the result INCOMPATIBLE unless the evidence strongly proves otherwise.
- Use the RAG evidence to refine the final recommendation and explanation.
- Return ONLY valid JSON.
- Do not include markdown.
- Do not include extra commentary.

Allowed final_status values:
{json.dumps(ALLOWED_FINAL_STATUSES)}

Allowed risk_level values:
{json.dumps(ALLOWED_RISK_LEVELS)}

Expected JSON format:
{{
  "final_status": "PARTIAL",
  "risk_level": "MAJOR",
  "confidence": 0.82,
  "reasoning_summary": "Short explanation",
  "recommended_action": "Concrete migration advice"
}}

Original component:
{json.dumps(component, indent=2)}

Rule-based result:
{json.dumps(rule_result, indent=2)}

RAG evidence:
{json.dumps(compact_evidence, indent=2)}
"""
    return prompt.strip()


def _normalize_ai_result(ai_result: dict, rule_result: dict) -> dict:
    """
    Normalize and validate the AI response.
    Falls back to rule_result values when output is incomplete or invalid.
    """
    final_status = ai_result.get("final_status", rule_result.get("final_status"))
    risk_level = ai_result.get("risk_level", rule_result.get("final_risk"))
    confidence = ai_result.get("confidence", 0.0)
    reasoning_summary = ai_result.get("reasoning_summary", "")
    recommended_action = ai_result.get(
        "recommended_action",
        rule_result.get("recommended_action", ""),
    )

    if final_status not in ALLOWED_FINAL_STATUSES:
        final_status = rule_result.get("final_status", "NEEDS_REVIEW")

    if risk_level not in ALLOWED_RISK_LEVELS:
        risk_level = rule_result.get("final_risk", "MINOR")

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0

    confidence = max(0.0, min(confidence, 1.0))
    confidence = round(confidence, 2)

    if not isinstance(reasoning_summary, str):
        reasoning_summary = ""

    if not isinstance(recommended_action, str):
        recommended_action = rule_result.get("recommended_action", "")

    return {
        "final_status": final_status,
        "risk_level": risk_level,
        "confidence": confidence,
        "reasoning_summary": reasoning_summary.strip(),
        "recommended_action": recommended_action.strip(),
    }


def reason_with_ai(
    component: dict,
    rule_result: dict,
    evidence_chunks: list[dict],
) -> dict:
    """
    Run AI reasoning on top of the rule-based result and RAG evidence.

    Returns:
        dict with:
        {
          "final_status": "...",
          "risk_level": "...",
          "confidence": 0.0,
          "reasoning_summary": "...",
          "recommended_action": "..."
        }

        If AI is unavailable or fails, returns a safe fallback based on rule_result.
    """
    fallback = {
        "final_status": rule_result.get("final_status", "NEEDS_REVIEW"),
        "risk_level": rule_result.get("final_risk", "MINOR"),
        "confidence": rule_result.get("confidence", 0.0),
        "reasoning_summary": rule_result.get(
            "reasoning_summary",
            "No AI reasoning available. Using rule-based compatibility result.",
        ),
        "recommended_action": rule_result.get("recommended_action", ""),
    }

    if not is_ai_available():
        logger.info("Gemini API key not configured. Falling back to rule-based result.")
        return fallback

    prompt = _build_prompt(component, rule_result, evidence_chunks)

    try:
        _configure_gemini()
        model = genai.GenerativeModel(get_gemini_model())
        response = model.generate_content(prompt)

        usage_metadata = getattr(response, "usage_metadata", None)
        if usage_metadata is not None:
            logger.info(
                "AI quota usage for component %s | model=%s | "
                "prompt_tokens=%s | candidates_tokens=%s | total_tokens=%s",
                component.get("component_id", "unknown"),
                get_gemini_model(),
                usage_metadata.prompt_token_count,
                usage_metadata.candidates_token_count,
                usage_metadata.total_token_count,
            )

        raw_text = getattr(response, "text", "") or ""
        raw_text = (
            raw_text.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        parsed = json.loads(raw_text)
        normalized = _normalize_ai_result(parsed, rule_result)

        logger.info(
            "AI reasoning completed for component %s | final_status=%s | confidence=%.2f",
            component.get("component_id", "unknown"),
            normalized["final_status"],
            normalized["confidence"],
        )

        return normalized

    except (json.JSONDecodeError, ValueError, TypeError) as error:
        logger.warning(
            "Invalid AI response for component %s: %s",
            component.get("component_id", "unknown"),
            error,
        )
        return fallback

    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.warning(
            "AI reasoning failed for component %s: %s",
            component.get("component_id", "unknown"),
            error,
        )
        return fallback
