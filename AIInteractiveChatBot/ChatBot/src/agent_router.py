import re
import httpx

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


class CreateUserAgent:
    async def run(self, message: str, session: dict) -> str:
        user = session["user"]

        if message.lower() == "cancel":
            reset_user(session)
            return "User creation cancelled. Back to normal chat mode."

        if not user["firstName"]:
            user["firstName"] = message
            return "Enter last name:"

        if not user["lastName"]:
            user["lastName"] = message
            return "Enter email:"

        if not user["email"]:
            if not message:
                return "Email is required. Please enter email:"

            if not re.match(EMAIL_REGEX, message):
                return "Invalid email format. Please enter a valid email:"

            user["email"] = message

            payload = {
                "firstName": user["firstName"],
                "lastName": user["lastName"],
                "email": user["email"]
            }

            # async with httpx.AsyncClient() as client:
            #     response = await client.post("http://127.0.0.1:8000/submit", json=payload)
            #     response.raise_for_status()

            reset_user(session)
            return {
                "answer": "User created successfully.",
                "user": payload,
                "mode": "CHAT"
            }

        return "Please continue entering user details."


class CreateStudentAgent:
    async def run(self, message: str, session: dict) -> str:
        student = session["student"]

        if message.lower() == "cancel":
            reset_student(session)
            return "Student creation cancelled. Back to normal chat mode."

        if not student["studentId"]:
            student["studentId"] = message
            return "Enter first name:"

        if not student["firstName"]:
            student["firstName"] = message
            return "Enter last name:"

        if not student["lastName"]:
            student["lastName"] = message
            return "Enter email:"

        if not student["email"]:
            if not re.match(EMAIL_REGEX, message):
                return "Invalid email format. Please enter a valid email:"
            student["email"] = message
            return "Enter grade:"

        if not student["grade"]:
            student["grade"] = message

            payload = {
                "studentId": student["studentId"],
                "firstName": student["firstName"],
                "lastName": student["lastName"],
                "email": student["email"],
                "grade": student["grade"]
            }

            # async with httpx.AsyncClient() as client:
            #     response = await client.post("http://127.0.0.1:8000/submit", json=payload)
            #     response.raise_for_status()

            reset_student(session)
            return {
                "answer": "Student created successfully.",
                "student": payload,
                "mode": "CHAT"
            }

        return "Please continue entering student details."


class RouterAgent:
    def __init__(self):
        self.create_user_agent = CreateUserAgent()
        self.create_student_agent = CreateStudentAgent()

    async def run(self, message: str, session: dict, ask_llm_func) -> str:
        lowered = message.lower().strip()

        if session.get("mode") == "CREATE_USER":
            return await self.create_user_agent.run(message, session)

        if session.get("mode") == "CREATE_STUDENT":
            return await self.create_student_agent.run(message, session)

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


async def handle_agent_message(message: str, session: dict, ask_llm_func) -> str:
    return await router_agent.run(message, session, ask_llm_func)