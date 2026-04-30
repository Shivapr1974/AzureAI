from __future__ import annotations

import json
from pathlib import Path

from src.rag_pipeline import search_documents


REPO_ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = REPO_ROOT / "rules"


def load_rules_index() -> dict:
    path = RULES_DIR / "rules_index.json"
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_agent_config(file_name: str) -> dict:
    path = RULES_DIR / file_name
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def evaluate_rule(rule: dict, form: dict) -> bool:
    condition = rule.get("condition", {})
    field = condition.get("field", "")
    value = str(form.get(field, "") or "")
    condition_type = condition.get("type")

    if condition_type == "field_empty":
        return not value.strip()

    if condition_type == "field_not_in":
        allowed = {item.lower() for item in condition.get("allowed", [])}
        return value.strip().lower() not in allowed

    if condition_type == "length_below":
        minimum = int(condition.get("minimum", 0))
        return len(value.strip()) < minimum

    if condition_type == "missing_keywords":
        keywords = [item.lower() for item in condition.get("keywords", [])]
        lowered = value.lower()
        return not all(keyword in lowered for keyword in keywords)

    if condition_type == "contains_any":
        keywords = [item.lower() for item in condition.get("keywords", [])]
        lowered = value.lower()
        return any(keyword in lowered for keyword in keywords)

    return False


def summarize_agent(agent_name: str, findings: list[dict]) -> str:
    if not findings:
        return f"{agent_name} found no rule violations in this demo run."
    top_finding = findings[0]
    return f"{agent_name} flagged {len(findings)} item(s). Highest priority issue: {top_finding['message']}"


def run_review(state: dict) -> None:
    rules_index = load_rules_index()
    form = state["form"]
    agent_results: dict[str, dict] = {}
    scores: dict[str, float | str] = {}
    total_score = 0

    state["review"]["status"] = "RUNNING"
    state["review"]["mockProjectComparison"] = None

    for agent in rules_index.get("agents", []):
        config = load_agent_config(agent["file"])
        evidence = search_documents(config.get("ragQuery", "business case form"), top_k=3)
        findings: list[dict] = []
        score = 100

        for rule in sorted(config.get("rules", []), key=lambda item: item.get("priority", 999)):
            if not rule.get("enabled", True):
                continue
            if not evaluate_rule(rule, form):
                continue

            score += int(rule.get("scoreImpact", 0))
            findings.append(
                {
                    "id": rule["id"],
                    "priority": rule["priority"],
                    "message": rule["message"],
                    "recommendation": rule["recommendation"],
                    "scoreImpact": rule["scoreImpact"],
                }
            )

        bounded_score = max(0, min(100, score))
        total_score += bounded_score
        status = "COMPLETED" if not findings else "NEEDS_REVIEW"
        summary = summarize_agent(agent["name"], findings)

        agent_results[agent["name"]] = {
            "status": status,
            "findings": findings,
            "score": bounded_score,
            "summary": summary,
            "evidence": evidence,
            "isMock": True,
        }
        scores[agent["name"]] = bounded_score

    overall = round(total_score / max(len(agent_results), 1), 1)
    scores["overall"] = overall
    scores["label"] = "Demo/mock scores driven by JSON rules."

    state["review"]["agentResults"] = agent_results
    state["review"]["scores"] = scores
    state["review"]["summary"] = (
        f"Review complete. Overall demo score: {overall}. "
        "These scores are mock outputs based on the JSON rule packs and retrieved document context."
    )
    state["review"]["status"] = (
        "NEEDS_REVIEW"
        if any(result["findings"] for result in agent_results.values())
        else "COMPLETED"
    )
