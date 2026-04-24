from __future__ import annotations

from copy import deepcopy
from uuid import uuid4


BC_FORM_FIELDS = [
    "intType",
    "reqType",
    "intName",
    "inOverview",
    "inHighlights",
]

SOURCE_PRIORITY = {
    "AI_INFERENCE": 1,
    "CHIP_SELECTION": 2,
    "MANUAL_EDIT": 3,
}


def build_initial_state(session_id: str | None = None) -> dict:
    resolved_session_id = session_id or str(uuid4())
    form = {field: "" for field in BC_FORM_FIELDS}
    return {
        "sessionId": resolved_session_id,
        "mode": "CHAT",
        "ui": {
            "formRequested": False,
        },
        "form": form,
        "chat": {"history": []},
        "retrieval": {
            "query": "",
            "context": [],
            "documents": [],
        },
        "review": {
            "status": "NOT_STARTED",
            "agentResults": {},
            "scores": {},
            "summary": "",
            "isMock": True,
        },
        "_meta": {
            "formSources": {field: "" for field in BC_FORM_FIELDS},
        },
    }


def get_public_state(state: dict) -> dict:
    public_state = deepcopy(state)
    public_state.pop("_meta", None)
    return public_state


def append_chat_message(state: dict, role: str, text: str, intent: str | None = None) -> None:
    state["chat"]["history"].append(
        {
            "role": role,
            "text": text,
            "intent": intent or "",
        }
    )


def apply_form_updates(state: dict, updates: dict, source: str) -> list[str]:
    changed_fields: list[str] = []
    meta = state.setdefault("_meta", {}).setdefault("formSources", {})

    for field, raw_value in updates.items():
        if field not in BC_FORM_FIELDS:
            continue

        value = normalize_form_value(field, raw_value)
        current_source = meta.get(field, "")
        if SOURCE_PRIORITY.get(source, 0) < SOURCE_PRIORITY.get(current_source, 0):
            continue

        state["form"][field] = value
        meta[field] = source
        changed_fields.append(field)

    return changed_fields


def normalize_form_value(field: str, value) -> str:
    if value is None:
        return ""

    if isinstance(value, list):
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        return ", ".join(cleaned)

    text = str(value).strip()
    if field == "intType":
        lowered = text.lower()
        if lowered == "it":
            return "IT"
        if lowered == "data":
            return "Data"
        if lowered in {"it & data", "it and data"}:
            return "IT & Data"

    return text


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, dict] = {}

    def get_or_create(self, session_id: str | None = None) -> dict:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]

        state = build_initial_state(session_id)
        self._sessions[state["sessionId"]] = state
        return state

    def reset(self, session_id: str | None = None) -> dict:
        if session_id and session_id in self._sessions:
            self._sessions.pop(session_id, None)

        state = build_initial_state()
        self._sessions[state["sessionId"]] = state
        return state


session_store = SessionStore()
