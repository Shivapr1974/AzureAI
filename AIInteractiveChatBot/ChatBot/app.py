from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from src.wiki_pipeline import ask_llm, save_uploaded_file
from src.agent_router import handle_agent_message

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session = {
    "mode": "CHAT",
    "active_agent": None,
    "user": {
        "firstName": "",
        "lastName": "",
        "email": ""
    },
    "student": {
        "studentId": "",
        "firstName": "",
        "lastName": "",
        "email": "",
        "grade": ""
    },
    "history": []
}


@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    message = body.get("question", "").strip()

    if not message:
        return {"answer": "Please enter something."}

    answer = await handle_agent_message(message, session, ask_llm)
    
    if isinstance(answer, dict):
        return answer

    session["history"].append({
        "question": message,
        "answer": answer
    })

    return {"answer": answer}


@app.post("/submit")
async def submit(request: Request):
    body = await request.json()
    return {
        "message": "Fake submit successful",
        "submittedUser": body
    }


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    result = await save_uploaded_file(file)
    return result