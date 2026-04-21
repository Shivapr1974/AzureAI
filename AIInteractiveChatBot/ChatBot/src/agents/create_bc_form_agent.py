from src.rag_pipeline import classify_workflow_input

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

        text = message.strip()
        lowered = text.lower()

        if lowered == "cancel":
            reset_bc_form(session)
            return "BC Form creation cancelled. Back to normal chat mode."

        # intType is the only field that needs real validation/classification
        if expected_field == "intType":
            result = classify_workflow_input(
                message,
                expected_field,
                ask_llm_func,
                session
            )

            intent = result.get("intent")

            if intent == "cancel":
                reset_bc_form(session)
                return "BC Form creation cancelled. Back to normal chat mode."

            if intent == "chat":
                clarification_prompt = f"""
The user is currently filling a BC Form.
The current field is intType.

Rules:
- reqSubName is auto-populated as Shiva Ram
- intType must be one of: IT, Data, IT & Data

Answer the user's question briefly.
Do not say the field was filled.
Do not repeat all instructions.

User message:
{message}
"""
                return ask_llm_func(clarification_prompt, session)

            if intent == "field_input":
                value = normalize_int_type((result.get("value") or "").strip())

                if value not in VALID_INT_TYPES:
                    return "Invalid Int Type. Please enter one of: IT, Data, IT & Data."

                bc_form["intType"] = value
                next_field = get_next_bc_field(bc_form)

                if next_field:
                    return get_field_prompt(next_field)

            return get_field_prompt("intType")

        # All remaining fields are free form.
        # Accept any non-empty value directly without LLM classification.
        if expected_field == "reqType":
            if not text:
                return "Req Type is required."
            bc_form["reqType"] = text
            next_field = get_next_bc_field(bc_form)
            return get_field_prompt(next_field)

        if expected_field == "intName":
            if not text:
                return "Int Name is required."
            bc_form["intName"] = text
            next_field = get_next_bc_field(bc_form)
            return get_field_prompt(next_field)

        if expected_field == "inOverview":
            if not text:
                return "In Overview is required."
            bc_form["inOverview"] = text
            next_field = get_next_bc_field(bc_form)
            return get_field_prompt(next_field)

        if expected_field == "inHighlights":
            if not text:
                return "In Highlights is required."
            bc_form["inHighlights"] = text

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