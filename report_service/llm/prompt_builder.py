"""
Prompt builder for Report Service.

Builds structured prompts for Gemini to generate
human-readable migration reports.
"""

from datetime import datetime


def build_report_prompt(report: dict) -> str:
    """
    Build a prompt for generating a high-level migration report.

    Args:
        report: structured report dict from report_builder

    Returns:
        string prompt
    """
    current_date = datetime.utcnow().strftime("%Y-%m-%d")

    summary = report.get("summary", "")
    score = report.get("migration_score", 0)
    recommendation = report.get("migration_recommendation", "")
    components = report.get("sections", {}).get("components", [])

    blockers = [
        component for component in components
        if component.get("final_risk") == "BLOCKER"
    ]

    prompt = f"""
You are a Jira Cloud migration expert.

Generate a professional migration report based on the following data.

=== CONTEXT ===
Report Date: {current_date}
Migration Score: {score}/100

Summary:
{summary}

Global Recommendation:
{recommendation}

=== BLOCKERS ===
"""

    for blocker in blockers[:5]:
        prompt += f"""
- Component: {blocker.get("component_id")}
  Risk: {blocker.get("final_risk")}
  Issue: {blocker.get("reasoning_summary")}
  Fix: {blocker.get("recommended_action")}
"""

    prompt += f"""

=== INSTRUCTIONS ===

Write a clear, structured report with:

1. Executive Summary
2. Key Risks
3. Migration Strategy
4. Recommended Next Steps

Constraints:
- Use this exact report date: {current_date}
- Do NOT write [Current Date]
- Keep it concise, between 300 and 500 words
- Use a professional consulting tone
- Do NOT repeat raw JSON
- Do NOT invent components or risks not present in the input data
"""

    return prompt.strip()
