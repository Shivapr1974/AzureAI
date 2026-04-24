from __future__ import annotations

from typing import Any

from src.rag_pipeline import grounded_answer
from src.review_engine import run_review
from src.state_store import BC_FORM_FIELDS, append_chat_message, apply_form_updates, get_public_state


GUIDED_FIELD_PROMPTS = {
    "intType": "What is the Integration Type? You can enter IT, Data, or IT & Data.",
    "reqType": "What is the Request Type?",
    "intName": "What is the Integration Name?",
    "inOverview": "What is the Integration Overview?",
    "inHighlights": "What are the Integration Highlights?",
}

GUIDED_FIELD_HINTS = {
    "intType": "Pick the primary integration category: IT, Data, or IT & Data.",
    "reqType": "Describe the kind of request, for example new capability request, enhancement, or change.",
    "intName": "Use the business-friendly or system integration name. Free text is fine.",
    "inOverview": "Write a short summary of the business need, systems involved, and intended outcome. Free text is fine.",
    "inHighlights": "List the most important points, dependencies, risks, or review notes. Free text is fine.",
}

GUIDED_CANCEL_TERMS = {"cancel", "stop", "exit", "never mind", "nevermind"}
GENERAL_CHAT_MARKERS = (
    "joke",
    "funny",
    "laugh",
    "hello",
    "hi",
    "hey",
    "how are you",
    "who are you",
    "what can you do",
    "thank you",
    "thanks",
    "tell me",
    "write me",
)


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


def get_next_missing_field(state: dict) -> str | None:
    form = state["form"]
    for field in BC_FORM_FIELDS:
        if not str(form.get(field, "") or "").strip():
            return field
    return None


def get_guided_prompt(field: str) -> str:
    return GUIDED_FIELD_PROMPTS[field]


def is_help_question(message: str) -> bool:
    lowered = message.lower().strip()
    if lowered.endswith("?"):
        return True

    starters = ("what", "how", "why", "can", "should", "help", "example", "explain")
    return lowered.startswith(starters)


def looks_like_general_chat(message: str, current_field: str) -> bool:
    lowered = message.lower().strip()

    if any(marker in lowered for marker in GENERAL_CHAT_MARKERS):
        if current_field == "intType" and lowered in {"it", "data", "it & data", "it and data"}:
            return False
        return True

    starters = (
        "tell me",
        "write",
        "make",
        "say",
        "chat",
        "let's talk",
        "lets talk",
    )
    return lowered.startswith(starters)


def set_guided_mode(state: dict, enabled: bool) -> None:
    state["mode"] = "GUIDED_FORM" if enabled else "CHAT"


def save_guided_field_value(state: dict, field: str, value: str) -> str | None:
    cleaned = value.strip()
    if not cleaned:
        return f"{GUIDED_FIELD_PROMPTS[field]} Please enter a value."

    if field == "intType":
        normalized = detect_form_updates(f"int type is {cleaned}").get("intType", cleaned)
        if normalized not in {"IT", "Data", "IT & Data"}:
            return "Integration Type must be IT, Data, or IT & Data."
        apply_form_updates(state, {field: normalized}, source="MANUAL_EDIT")
        return None

    apply_form_updates(state, {field: cleaned}, source="MANUAL_EDIT")
    return None


def build_next_guided_response(state: dict, prefix: str | None = None) -> str:
    next_field = get_next_missing_field(state)
    if next_field is None:
        set_guided_mode(state, False)
        completion = (
            "The BC Form is fully filled in. You can still edit any field on the right, or click Submit to run review."
        )
        if prefix:
            return f"{prefix} {completion}"
        return completion

    prompt = get_guided_prompt(next_field)
    if prefix:
        return f"{prefix} {prompt}"
    return prompt


def handle_guided_form_turn(state: dict, message: str) -> dict:
    lowered = message.lower().strip()
    if lowered in GUIDED_CANCEL_TERMS:
        set_guided_mode(state, False)
        return create_response_payload(
            state,
            answer="Guided BC form flow cancelled. Your current values are still kept in the form.",
            intent="FORM_QUESTION",
        )

    explicit_updates = detect_form_updates(message)
    if explicit_updates:
        apply_form_updates(state, explicit_updates, source="MANUAL_EDIT")
        changed = ", ".join(explicit_updates.keys())
        answer = build_next_guided_response(
            state,
            prefix=f"Updated the BC form from chat input: {changed}.",
        )
        return create_response_payload(state, answer=answer, intent="FORM_UPDATE")

    current_field = get_next_missing_field(state)
    if current_field is None:
        return create_response_payload(
            state,
            answer=build_next_guided_response(state),
            intent="FORM_UPDATE",
        )

    if is_help_question(message):
        answer = f"{GUIDED_FIELD_HINTS[current_field]} {get_guided_prompt(current_field)}"
        return create_response_payload(state, answer=answer, intent="FORM_QUESTION")

    if looks_like_general_chat(message, current_field):
        answer, _contexts = grounded_answer(message, state)
        reminder = f"When you're ready, {get_guided_prompt(current_field)}"
        return create_response_payload(
            state,
            answer=f"{answer}\n\n{reminder}",
            intent="GENERAL_CHAT",
        )

    validation_error = save_guided_field_value(state, current_field, message)
    if validation_error:
        return create_response_payload(state, answer=validation_error, intent="FORM_QUESTION")

    field_name = current_field
    answer = build_next_guided_response(state, prefix=f"Saved {field_name}.")
    return create_response_payload(state, answer=answer, intent="FORM_UPDATE")


def build_suggested_chips(state: dict) -> list[dict]:
    chips: list[dict] = []
    form = state["form"]
    guided_field = get_next_missing_field(state) if state.get("mode") == "GUIDED_FORM" else None

    if not form["intType"] and (guided_field is None or guided_field == "intType"):
        chips.extend(
            [
                {"label": "IT", "value": "IT", "field": "intType", "multiSelect": False},
                {"label": "Data", "value": "Data", "field": "intType", "multiSelect": False},
                {"label": "IT & Data", "value": "IT & Data", "field": "intType", "multiSelect": False},
            ]
        )

    if not form["reqType"] and (guided_field is None or guided_field == "reqType"):
        chips.append(
            {
                "label": "New capability",
                "value": "New capability request",
                "field": "reqType",
                "multiSelect": False,
            }
        )

    if not form["inHighlights"] and (guided_field is None or guided_field == "inHighlights"):
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

    if guided_field is None and state["review"]["status"] in {"NOT_STARTED", "COMPLETED"}:
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

    if chip is None and state.get("mode") == "GUIDED_FORM":
        append_chat_message(state, "user", cleaned, "FORM_UPDATE")
        return handle_guided_form_turn(state, cleaned)

    intent = infer_intent(cleaned, chip)
    append_chat_message(state, "user", cleaned, intent)

    if intent == "CHIP_SELECTION" and chip is not None:
        if chip.field:
            current_field = get_next_missing_field(state) if state.get("mode") == "GUIDED_FORM" else None
            if current_field and chip.field != current_field:
                answer = (
                    f"We're currently filling {current_field}. "
                    f"Please answer that first, or type a value directly."
                )
                return create_response_payload(state, answer=answer, intent="FORM_QUESTION")

            if chip.multiSelect and state["form"].get(chip.field):
                combined = f"{state['form'][chip.field]}, {chip.value}"
                apply_form_updates(state, {chip.field: combined}, source="CHIP_SELECTION")
            else:
                apply_form_updates(state, {chip.field: chip.value}, source="CHIP_SELECTION")

            if state.get("mode") == "GUIDED_FORM":
                answer = build_next_guided_response(
                    state,
                    prefix=f"Applied chip selection to {chip.field}.",
                )
            else:
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
        set_guided_mode(state, True)
        answer = build_next_guided_response(
            state,
            prefix=(
                "We can start the BC Form now. You can answer in plain text, and for free-text fields you can type anything."
            ),
        )
        return create_response_payload(state, answer=answer, intent=intent)

    if intent == "SUBMIT_ACTION":
        return handle_submit(state, {})

    answer, _contexts = grounded_answer(cleaned, state)
    return create_response_payload(state, answer=answer, intent=intent)
