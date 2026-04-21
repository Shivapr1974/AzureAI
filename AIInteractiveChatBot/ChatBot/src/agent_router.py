import json
import re

from src.agents.create_bc_form_agent import CreateBCFormAgent
from src.rag_pipeline import classify_workflow_input


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
        self.create_bc_form_agent = CreateBCFormAgent()

    async def run(self, message: str, session: dict, ask_llm_func) -> str | dict:
        lowered = message.lower().strip()

        if session.get("mode") == "CREATE_USER":
            return await self.create_user_agent.run(message, session, ask_llm_func)

        if session.get("mode") == "CREATE_STUDENT":
            return await self.create_student_agent.run(message, session, ask_llm_func)

        if session.get("mode") == "CREATE_BC_FORM":
            return await self.create_bc_form_agent.run(message, session, ask_llm_func)


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
        
        if lowered == "create bc form":
            session["mode"] = "CREATE_BC_FORM"
            session["active_agent"] = "CreateBCFormAgent"
            session["bcForm"] = {
                "reqSubName": "Shiva Ram",
                "intType": "",
                "reqType": "",
                "intName": "",
                "inOverview": "",
                "inHighlights": ""
            }
            return (
                "Req Sub Name is auto-populated as Shiva Ram.<br>"
                "Enter Int Type (IT, Data, IT & Data)."
            )

        return ask_llm_func(message, session)


router_agent = RouterAgent()


async def handle_agent_message(message: str, session: dict, ask_llm_func) -> str | dict:
    return await router_agent.run(message, session, ask_llm_func)