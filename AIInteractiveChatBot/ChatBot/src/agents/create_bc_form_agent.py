import json

from src.rag_pipeline import ask_llm

VALID_INT_TYPES = {"IT", "Data", "IT & Data"}


def reset_bc_form(session: dict):
    session["mode"] = "CHAT"
    session["active_agent"] = None
    session["bcForm"] = {
        "reqSubName": "Shiva Ram",
        "intType": "",
        "reqType": "",
        "intName": "",
        "inOverview": "",
        "inHighlights": ""
    }


def get_next_bc_field(bc_form: dict) -> str | None:
    if not bc_form["intType"]:
        return "intType"
    if not bc_form["reqType"]:
        return "reqType"
    if not bc_form["intName"]:
        return "intName"
    if not bc_form["inOverview"]:
        return "inOverview"
    if not bc_form["inHighlights"]:
        return "inHighlights"
    return None


def get_field_prompt(field: str) -> str:
    prompts = {
        "intType": "Enter Int Type (allowed values: IT, Data, IT & Data). Example: IT",
        "reqType": "Enter Req Type (free text).",
        "intName": "Enter Int Name (free text).",
        "inOverview": "Enter In Overview (free text).",
        "inHighlights": "Enter In Highlights (free text)."
    }
    return prompts[field]


def normalize_int_type(value: str) -> str:
    text = value.strip().lower()

    if text == "it":
        return "IT"
    if text == "data":
        return "Data"
    if text in {"it & data", "it and data"}:
        return "IT & Data"

    return value.strip()


def classify_or_answer_bc_form(
    message: str,
    expected_field: str,
    session: dict
) -> dict:
    rules = ""
    if expected_field == "intType":
        rules = "For intType, valid values are exactly: IT, Data, IT & Data."

    prompt = f"""
You are helping with an interactive BC Form workflow.

Expected field: {expected_field}

{rules}

Return ONLY valid JSON in one of these forms:

For field input:
{{"intent":"field_input","field":"{expected_field}","value":"..."}}

For a user question:
{{"intent":"chat","answer":"..."}}

For cancel:
{{"intent":"cancel"}}

Rules:
- If the user is clearly providing the expected field, return field_input.
- If the user is asking a question, return chat and answer it briefly.
- If the user wants to stop, return cancel.
- Otherwise, prefer field_input for free-form fields.
- Do not output anything outside JSON.

User message:
{message}
"""

    raw = ask_llm(prompt, session)

    try:
        return json.loads(raw)
    except Exception:
        return {
            "intent": "field_input",
            "field": expected_field,
            "value": message.strip()
        }


class CreateBCFormAgent:
    async def run(self, message: str, session: dict, ask_llm_func) -> str | dict:
        bc_form = session["bcForm"]
        expected_field = get_next_bc_field(bc_form)

        if expected_field is None:
            payload = {
                "reqSubName": bc_form["reqSubName"],
                "intType": bc_form["intType"],
                "reqType": bc_form["reqType"],
                "intName": bc_form["intName"],
                "inOverview": bc_form["inOverview"],
                "inHighlights": bc_form["inHighlights"]
            }
            reset_bc_form(session)
            return {
                "answer": "BC Form created successfully.",
                "bcForm": payload,
                "mode": "CHAT"
            }

        if message.lower().strip() == "cancel":
            reset_bc_form(session)
            return "BC Form creation cancelled. Back to normal chat mode."

        result = classify_or_answer_bc_form(message, expected_field, session)
        intent = result.get("intent")

        if intent == "cancel":
            reset_bc_form(session)
            return "BC Form creation cancelled. Back to normal chat mode."

        if intent == "chat":
            return result.get("answer", "Please continue.")

        if intent == "field_input":
            value = (result.get("value") or "").strip()

            if expected_field == "intType":
                value = normalize_int_type(value)

                if value not in VALID_INT_TYPES:
                    return "Invalid Int Type. Please enter one of: IT, Data, IT & Data."

                bc_form["intType"] = value

            elif expected_field == "reqType":
                if not value:
                    return "Req Type is required."
                bc_form["reqType"] = value

            elif expected_field == "intName":
                if not value:
                    return "Int Name is required."
                bc_form["intName"] = value

            elif expected_field == "inOverview":
                if not value:
                    return "In Overview is required."
                bc_form["inOverview"] = value

            elif expected_field == "inHighlights":
                if not value:
                    return "In Highlights is required."
                bc_form["inHighlights"] = value

            next_field = get_next_bc_field(bc_form)

            if next_field:
                return get_field_prompt(next_field)

            payload = {
                "reqSubName": bc_form["reqSubName"],
                "intType": bc_form["intType"],
                "reqType": bc_form["reqType"],
                "intName": bc_form["intName"],
                "inOverview": bc_form["inOverview"],
                "inHighlights": bc_form["inHighlights"]
            }

            reset_bc_form(session)
            return {
                "answer": "BC Form created successfully.",
                "bcForm": payload,
                "mode": "CHAT"
            }

        return get_field_prompt(expected_field)