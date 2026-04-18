# app.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.rag_pipeline import ask_llm_with_search

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    question = body.get("question", "").strip()
    if not question:
        return {"answer": "Please enter a question."}

    answer = ask_llm_with_search(question)
    return {"answer": answer}