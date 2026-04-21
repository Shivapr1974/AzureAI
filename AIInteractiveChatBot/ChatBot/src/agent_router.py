import json
import re

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def reset_user(session: dict):
    session["mode"] = "CHAT"
    session["active_agent"] = None
    session["user"] = {
        "firstName": "",
        "lastName": "",
        "email": ""
    }


def reset_student(session: dict):
    session["mode"] = "CHAT"
    session["active_agent"] = None
    session["student"] = {
        "studentId": "",
        "firstName": "",
        "lastName": "",
        "email": "",
        "grade": ""
    }


def get_next_user_field(user: dict) -> str | None:
    if not user["firstName"]:
        return "firstName"
    if not user["lastName"]:
        return "lastName"
    if not user["email"]:
        return "email"
    return None


def get_next_student_field(student: dict) -> str | None:
    if not student["studentId"]:
        return "studentId"
    if not student["firstName"]:
        return "firstName"
    if not student["lastName"]:
        return "lastName"
    if not student["email"]:
        return "email"
    if not student["grade"]:
        return "grade"
    return None


def parse_classifier_response(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        return {
            "intent": "chat",
            "message": text
        }


def classify_workflow_input(message: str, expected_field: str, ask_llm_func, session: dict) -> dict:
    prompt = f"""
You are a classifier for an interactive form workflow.

Expected field: {expected_field}

Classify the user message into ONE of these:

1. field_input
2. chat
3. cancel

Return ONLY valid JSON in one of these forms:

{{"intent":"field_input","field":"{expected_field}","value":"..."}}
{{"intent":"chat"}}
{{"intent":"cancel"}}

Rules:
- Return "field_input" only if the user clearly provides a value for the expected field.
- Return "chat" if the user is asking a question, making a side comment, asking for clarification, refusing, or saying something that should not fill the field yet.
- Return "cancel" only if the user clearly wants to stop or cancel the workflow.
- Do not explain anything outside JSON.

User message:
{message}
"""
    raw = ask_llm_func(prompt, session)
    return parse_classifier_response(raw)


class CreateUserAgent:
    async def run(self, message: str, session: dict, ask_llm_func) -> str | dict:
        user = session["user"]
        expected_field = get_next_user_field(user)

        if expected_field is None:
            payload = {
                "firstName": user["firstName"],
                "lastName": user["lastName"],
                "email": user["email"]
            }
            reset_user(session)
            return {
                "answer": "User created successfully.",
                "user": payload,
                "mode": "CHAT"
            }

        result = classify_workflow_input(message, expected_field, ask_llm_func, session)
        intent = result.get("intent")

        if intent == "cancel":
            reset_user(session)
            return "User creation cancelled. Back to normal chat mode."

        if intent == "chat":
            clarification_prompt = f"""
The user is currently in CREATE_USER workflow.
The field currently being collected is: {expected_field}.

Known user data:
- firstName: {user.get('firstName') or 'Not provided'}
- lastName: {user.get('lastName') or 'Not provided'}
- email: {user.get('email') or 'Not provided'}

Answer the user naturally and helpfully.
Do NOT mark the field as filled.
Do NOT invent user values.
At the end, gently remind them what field is still needed.

User message:
{message}
"""
            return ask_llm_func(clarification_prompt, session)

        if intent == "field_input":
            value = (result.get("value") or "").strip()

            if expected_field == "firstName":
                if not value:
                    return "First name is required. Please enter first name:"
                user["firstName"] = value
                return "Enter last name:"

            if expected_field == "lastName":
                if not value:
                    return "Last name is required. Please enter last name:"
                user["lastName"] = value
                return "Enter email:"

            if expected_field == "email":
                if not value:
                    return "Email is required. Please enter email:"
                if not re.match(EMAIL_REGEX, value):
                    return "Invalid email format. Please enter a valid email:"
                user["email"] = value

                payload = {
                    "firstName": user["firstName"],
                    "lastName": user["lastName"],
                    "email": user["email"]
                }

                reset_user(session)
                return {
                    "answer": "User created successfully.",
                    "user": payload,
                    "mode": "CHAT"
                }

        return f"I still need {expected_field}. Please provide it when ready."


class CreateStudentAgent:
    async def run(self, message: str, session: dict, ask_llm_func) -> str | dict:
        student = session["student"]
        expected_field = get_next_student_field(student)

        if expected_field is None:
            payload = {
                "studentId": student["studentId"],
                "firstName": student["firstName"],
                "lastName": student["lastName"],
                "email": student["email"],
                "grade": student["grade"]
            }
            reset_student(session)
            return {
                "answer": "Student created successfully.",
                "student": payload,
                "mode": "CHAT"
            }

        result = classify_workflow_input(message, expected_field, ask_llm_func, session)
        intent = result.get("intent")

        if intent == "cancel":
            reset_student(session)
            return "Student creation cancelled. Back to normal chat mode."

        if intent == "chat":
            clarification_prompt = f"""
The user is currently in CREATE_STUDENT workflow.
The field currently being collected is: {expected_field}.

Known student data:
- studentId: {student.get('studentId') or 'Not provided'}
- firstName: {student.get('firstName') or 'Not provided'}
- lastName: {student.get('lastName') or 'Not provided'}
- email: {student.get('email') or 'Not provided'}
- grade: {student.get('grade') or 'Not provided'}

Answer the user naturally and helpfully.
Do NOT mark the field as filled.
Do NOT invent student values.
At the end, gently remind them what field is still needed.

User message:
{message}
"""
            return ask_llm_func(clarification_prompt, session)

        if intent == "field_input":
            value = (result.get("value") or "").strip()

            if expected_field == "studentId":
                if not value:
                    return "Student ID is required. Please enter student ID:"
                student["studentId"] = value
                return "Enter first name:"

            if expected_field == "firstName":
                if not value:
                    return "First name is required. Please enter first name:"
                student["firstName"] = value
                return "Enter last name:"

            if expected_field == "lastName":
                if not value:
                    return "Last name is required. Please enter last name:"
                student["lastName"] = value
                return "Enter email:"

            if expected_field == "email":
                if not value:
                    return "Email is required. Please enter email:"
                if not re.match(EMAIL_REGEX, value):
                    return "Invalid email format. Please enter a valid email:"
                student["email"] = value
                return "Enter grade:"

            if expected_field == "grade":
                if not value:
                    return "Grade is required. Please enter grade:"
                student["grade"] = value

                payload = {
                    "studentId": student["studentId"],
                    "firstName": student["firstName"],
                    "lastName": student["lastName"],
                    "email": student["email"],
                    "grade": student["grade"]
                }

                reset_student(session)
                return {
                    "answer": "Student created successfully.",
                    "student": payload,
                    "mode": "CHAT"
                }

        return f"I still need {expected_field}. Please provide it when ready."


class RouterAgent:
    def __init__(self):
        self.create_user_agent = CreateUserAgent()
        self.create_student_agent = CreateStudentAgent()

    async def run(self, message: str, session: dict, ask_llm_func) -> str | dict:
        lowered = message.lower().strip()

        if session.get("mode") == "CREATE_USER":
            return await self.create_user_agent.run(message, session, ask_llm_func)

        if session.get("mode") == "CREATE_STUDENT":
            return await self.create_student_agent.run(message, session, ask_llm_func)

        if lowered == "create user":
            session["mode"] = "CREATE_USER"
            session["active_agent"] = "CreateUserAgent"
            session["user"] = {
                "firstName": "",
                "lastName": "",
                "email": ""
            }
            return "Sure. Enter first name:"

        if lowered == "create student":
            session["mode"] = "CREATE_STUDENT"
            session["active_agent"] = "CreateStudentAgent"
            session["student"] = {
                "studentId": "",
                "firstName": "",
                "lastName": "",
                "email": "",
                "grade": ""
            }
            return "Sure. Enter student id:"

        return ask_llm_func(message, session)


router_agent = RouterAgent()


async def handle_agent_message(message: str, session: dict, ask_llm_func) -> str | dict:
    return await router_agent.run(message, session, ask_llm_func)