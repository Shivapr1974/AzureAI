from __future__ import annotations

import json
from typing import Any

from src.rag_pipeline import get_openai_client


FORM_FIELDS = [
    ("intType", "Integration Type"),
    ("reqType", "Request Type"),
    ("intName", "Integration Name"),
    ("inOverview", "Integration Overview"),
    ("inHighlights", "Integration Highlights"),
]


def build_mock_project_prompt(state: dict) -> str:
    form = state.get("form", {})
    review = state.get("review", {})
    agent_results = review.get("agentResults", {})
    findings_lines: list[str] = []

    for agent_name, result in agent_results.items():
        findings = result.get("findings", [])
        if not findings:
            findings_lines.append(f"- {agent_name}: no findings")
            continue

        findings_lines.append(f"- {agent_name}:")
        for finding in findings[:3]:
            findings_lines.append(
                f"  - {finding.get('message', '')} Recommendation: {finding.get('recommendation', '')}"
            )

    findings_block = "\n".join(findings_lines) if findings_lines else "- No review findings available."
    form_block = "\n".join(
        f"- {label}: {form.get(key, '') or 'Not provided'}"
        for key, label in FORM_FIELDS
    )

    return f"""
You are helping compare a submitted BC form against a mock example project that probably should have been captured earlier.

Generate:
1. a plausible mock project version of the BC form
2. a field-by-field comparison between the entered form and the mock project
3. a concise comparison summary
4. practical next steps

Return ONLY valid JSON with this exact structure:
{{
  "mockProject": {{
    "intType": "",
    "reqType": "",
    "intName": "",
    "inOverview": "",
    "inHighlights": ""
  }},
  "comparisonSummary": "",
  "fieldComparisons": [
    {{
      "field": "intType",
      "label": "Integration Type",
      "enteredValue": "",
      "mockValue": "",
      "assessment": "Aligned",
      "notes": ""
    }}
  ],
  "recommendedNextSteps": ["", ""]
}}

Allowed assessment values:
- Aligned
- Partial
- Missing
- Different

Current BC Form:
{form_block}

Review Findings:
{findings_block}
""".strip()


def build_fallback_comparison(state: dict) -> dict[str, Any]:
    form = state.get("form", {})
    mock_project: dict[str, str] = {}
    field_comparisons: list[dict[str, str]] = []

    for field, label in FORM_FIELDS:
        entered_value = str(form.get(field, "") or "")
        if entered_value.strip():
            mock_value = entered_value
            assessment = "Partial" if field in {"inOverview", "inHighlights"} else "Aligned"
            notes = (
                "Using the entered value as the mock baseline because no LLM comparison was available."
            )
        else:
            mock_value = f"Example {label}"
            assessment = "Missing"
            notes = "This field is missing from the current form and should be added."

        mock_project[field] = mock_value
        field_comparisons.append(
            {
                "field": field,
                "label": label,
                "enteredValue": entered_value or "Not provided",
                "mockValue": mock_value,
                "assessment": assessment,
                "notes": notes,
            }
        )

    return {
        "mockProject": mock_project,
        "comparisonSummary": (
            "This is a fallback mock comparison generated without the LLM. "
            "Use it as a placeholder until the model-backed comparison is available."
        ),
        "fieldComparisons": field_comparisons,
        "recommendedNextSteps": [
            "Fill in any missing BC form fields.",
            "Expand overview and highlights with more concrete project detail.",
        ],
        "isMock": True,
    }


def generate_mock_project_comparison(state: dict) -> dict[str, Any]:
    client = get_openai_client()
    if client is None:
        comparison = build_fallback_comparison(state)
        state["review"]["mockProjectComparison"] = comparison
        return comparison

    prompt = build_mock_project_prompt(state)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=900,
        )
        raw = response.choices[0].message.content or ""
        parsed = json.loads(raw)
    except Exception:
        parsed = build_fallback_comparison(state)

    parsed["isMock"] = True
    state["review"]["mockProjectComparison"] = parsed
    return parsed
