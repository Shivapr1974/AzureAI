from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import re

from src.rag_pipeline import ask_llm_with_search, save_uploaded_file_to_chroma

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

# Simple mock session for now
# Later this can move to Redis
session = {
    "mode": "CHAT",
    "state": None,
    "user": {
        "firstName": "",
        "lastName": "",
        "email": ""
    },
    "history": []
}


def reset_user_flow():
    session["mode"] = "CHAT"
    session["state"] = None
    session["user"] = {
        "firstName": "",
        "lastName": "",
        "email": ""
    }


def handle_normal_chat(message: str) -> str:
    lowered = message.lower().strip()

    if lowered == "create user":
        session["mode"] = "CREATE_USER"
        session["state"] = "FIRST_NAME"
        session["user"] = {
            "firstName": "",
            "lastName": "",
            "email": ""
        }
        return "Sure. Enter first name:"

    # Normal chatbot mode goes through your RAG pipeline
    answer = ask_llm_with_search(message, session);
    # store history
    session["history"].append({
        "question": message,
        "answer": answer
    })
    return answer;


@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    message = body.get("question", "").strip()

    if not message:
        return {"answer": "Please enter something."}

    mode = session["mode"]

    if mode == "CHAT":
        answer = handle_normal_chat(message)
        return {"answer": answer}

    if mode == "CREATE_USER":
        state = session["state"]
        user = session["user"]

        if message.lower() == "cancel":
            reset_user_flow()
            return {"answer": "User creation cancelled. Back to normal chat mode."}

        if state == "FIRST_NAME":
            user["firstName"] = message
            session["state"] = "LAST_NAME"
            return {"answer": "Enter last name:"}

        if state == "LAST_NAME":
            user["lastName"] = message
            session["state"] = "EMAIL"
            return {"answer": "Enter email:"}

        if state == "EMAIL":
            if not message:
                return {"answer": "Email is required. Please enter email:"}

            if not re.match(EMAIL_REGEX, message):
                return {"answer": "Invalid email format. Please enter a valid email:"}

            user["email"] = message

            completed_user = {
                "firstName": user["firstName"],
                "lastName": user["lastName"],
                "email": user["email"]
            }

            reset_user_flow()

            return {
                "answer": "User created successfully.",
                "user": completed_user
            }

    return {"answer": "Something went wrong."}


@app.post("/submit")
async def submit(request: Request):
    body = await request.json()
    return {
        "message": "Fake submit successful",
        "submittedUser": body
    }


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    result = await save_uploaded_file_to_chroma(file)
    return result