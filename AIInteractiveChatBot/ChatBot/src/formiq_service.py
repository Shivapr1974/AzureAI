from __future__ import annotations

from typing import Any

from src.rag_pipeline import grounded_answer
from src.review_engine import run_review
from src.state_store import append_chat_message, apply_form_updates, get_public_state


def infer_intent(message: str, chip: Any | None = None) -> str:
    if chip is not None:
        return "CHIP_SELECTION"

    lowered = message.lower().strip()
    if any(term in lowered for term in ["bc form", "business case form", "fill a form", "start a form"]):
        return "FORM_QUESTION"
    if any(term in lowered for term in ["submit", "run review", "review this", "score this"]):
        return "SUBMIT_ACTION"
    if any(term in lowered for term in ["document", "upload", "source", "policy", "search docs"]):
        return "DOC_QUESTION"
    if any(term in lowered for term in ["int type", "req type", "integration", "overview", "highlight"]):
        return "FORM_QUESTION"
    if detect_form_updates(message):
        return "FORM_UPDATE"
    return "GENERAL_CHAT"


def detect_form_updates(message: str) -> dict[str, str]:
    lowered = message.lower()
    updates: dict[str, str] = {}

    if "it & data" in lowered or "it and data" in lowered:
        updates["intType"] = "IT & Data"
    elif "int type is it" in lowered or lowered.strip() == "it":
        updates["intType"] = "IT"
    elif "int type is data" in lowered or lowered.strip() == "data":
        updates["intType"] = "Data"

    field_markers = {
        "req type": "reqType",
        "integration name": "intName",
        "int name": "intName",
        "overview": "inOverview",
        "highlights": "inHighlights",
    }

    for marker, field in field_markers.items():
        token = f"{marker}:"
        if token in lowered:
            original_index = lowered.index(token) + len(token)
            updates[field] = message[original_index:].strip()

    return {field: value for field, value in updates.items() if value}


def build_suggested_chips(state: dict) -> list[dict]:
    chips: list[dict] = []
    form = state["form"]

    if not form["intType"]:
        chips.extend(
            [
                {"label": "IT", "value": "IT", "field": "intType", "multiSelect": False},
                {"label": "Data", "value": "Data", "field": "intType", "multiSelect": False},
                {"label": "IT & Data", "value": "IT & Data", "field": "intType", "multiSelect": False},
            ]
        )

    if not form["reqType"]:
        chips.append(
            {
                "label": "New capability",
                "value": "New capability request",
                "field": "reqType",
                "multiSelect": False,
            }
        )

    if not form["inHighlights"]:
        chips.extend(
            [
                {
                    "label": "Security review",
                    "value": "Security review needed",
                    "field": "inHighlights",
                    "multiSelect": True,
                },
                {
                    "label": "Data sharing",
                    "value": "Includes data sharing considerations",
                    "field": "inHighlights",
                    "multiSelect": True,
                },
            ]
        )

    if state["review"]["status"] in {"NOT_STARTED", "COMPLETED"}:
        chips.append(
            {
                "label": "Run review",
                "value": "Run review",
                "field": None,
                "multiSelect": False,
            }
        )

    return chips[:6]


def create_response_payload(
    state: dict,
    answer: str,
    intent: str,
    suggested_chips: list[dict] | None = None,
) -> dict:
    append_chat_message(state, "assistant", answer, intent)
    return {
        "sessionId": state["sessionId"],
        "answer": answer,
        "intent": intent,
        "suggestedChips": suggested_chips if suggested_chips is not None else build_suggested_chips(state),
        "appState": get_public_state(state),
    }


def handle_form_update(state: dict, form: dict[str, Any]) -> str:
    changed_fields = apply_form_updates(state, form, source="MANUAL_EDIT")
    if not changed_fields:
        return "No BC form changes were applied."

    readable = ", ".join(changed_fields)
    return f"Saved manual BC form updates for: {readable}."


def handle_submit(state: dict, form: dict[str, Any]) -> dict:
    if form:
        handle_form_update(state, form)

    run_review(state)
    answer = (
        "Submission captured and review agents completed. "
        "Scores are labeled as demo/mock outputs until the production scoring service is connected."
    )
    return create_response_payload(state, answer=answer, intent="SUBMIT_ACTION")


def handle_chat_turn(state: dict, message: str, chip: Any | None = None) -> dict:
    if chip is not None:
        user_text = chip.label
    else:
        user_text = message or ""

    cleaned = user_text.strip()
    if not cleaned:
        return {
            "sessionId": state["sessionId"],
            "answer": "Please enter a message.",
            "intent": "GENERAL_CHAT",
            "suggestedChips": build_suggested_chips(state),
            "appState": get_public_state(state),
        }

    intent = infer_intent(cleaned, chip)
    append_chat_message(state, "user", cleaned, intent)

    if intent == "CHIP_SELECTION" and chip is not None:
        if chip.field:
            if chip.multiSelect and state["form"].get(chip.field):
                combined = f"{state['form'][chip.field]}, {chip.value}"
                apply_form_updates(state, {chip.field: combined}, source="CHIP_SELECTION")
            else:
                apply_form_updates(state, {chip.field: chip.value}, source="CHIP_SELECTION")
            answer = f"Applied chip selection to {chip.field}."
        elif chip.value.lower() == "run review":
            run_review(state)
            answer = "Review completed from the suggested chip. Demo/mock scores are now available."
            return create_response_payload(state, answer=answer, intent=intent)
        else:
            answer = f"Captured chip selection: {chip.value}."
        return create_response_payload(state, answer=answer, intent=intent)

    if intent == "FORM_UPDATE":
        updates = detect_form_updates(cleaned)
        if updates:
            apply_form_updates(state, updates, source="MANUAL_EDIT")
            changed = ", ".join(updates.keys())
            answer = f"Updated the BC form from chat input: {changed}."
            return create_response_payload(state, answer=answer, intent=intent)

    if intent == "FORM_QUESTION":
        answer = (
            "We can start the BC Form now. Fill the fields on the right, or tell me values like "
            "'int type is IT', 'req type: new capability request', or 'overview: ...'."
        )
        return create_response_payload(state, answer=answer, intent=intent)

    if intent == "SUBMIT_ACTION":
        return handle_submit(state, {})

    answer, _contexts = grounded_answer(cleaned, state)
    return create_response_payload(state, answer=answer, intent=intent)
