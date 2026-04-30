from typing import Any

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.formiq_service import (
    create_response_payload,
    handle_chat_turn,
    handle_form_update,
    handle_submit,
)
from src.mock_project_service import generate_mock_project_comparison
from src.rag_pipeline import (
    delete_indexed_document,
    list_indexed_documents,
    save_uploaded_file,
    search_documents,
)
from src.review_engine import run_review
from src.state_store import get_public_state, session_store


class SuggestedChipRequest(BaseModel):
    label: str
    value: str
    field: str | None = None
    multiSelect: bool = False


class ChatRequest(BaseModel):
    sessionId: str | None = None
    question: str | None = None
    message: str | None = None
    chip: SuggestedChipRequest | None = None


class FormUpdateRequest(BaseModel):
    sessionId: str | None = None
    form: dict[str, Any] = Field(default_factory=dict)


class ReviewRequest(BaseModel):
    sessionId: str | None = None
    form: dict[str, Any] = Field(default_factory=dict)


class SearchRequest(BaseModel):
    sessionId: str | None = None
    query: str


class DeleteDocumentRequest(BaseModel):
    sessionId: str | None = None
    source: str


class MockProjectRequest(BaseModel):
    sessionId: str | None = None
    form: dict[str, Any] = Field(default_factory=dict)


app = FastAPI(title="FormIQ AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/state")
async def get_state(sessionId: str | None = None):
    state = session_store.get_or_create(sessionId)
    return {
        "sessionId": state["sessionId"],
        "appState": get_public_state(state),
        "suggestedChips": [],
    }


@app.post("/reset")
async def reset_state(request: ChatRequest):
    state = session_store.reset(request.sessionId)
    return {
        "sessionId": state["sessionId"],
        "answer": "Started a new session. The BC form, chat history, retrieval context, and review results were cleared.",
        "intent": "GENERAL_CHAT",
        "suggestedChips": [],
        "appState": get_public_state(state),
    }


@app.post("/chat")
async def chat(request: ChatRequest):
    state = session_store.get_or_create(request.sessionId)
    question = (request.message or request.question or "").strip()

    payload = handle_chat_turn(state=state, message=question, chip=request.chip)
    return payload


@app.post("/form")
async def update_form(request: FormUpdateRequest):
    state = session_store.get_or_create(request.sessionId)
    answer = handle_form_update(state, request.form)
    return create_response_payload(state, answer=answer, intent="FORM_UPDATE")


@app.post("/submit")
async def submit(request: ReviewRequest):
    state = session_store.get_or_create(request.sessionId)
    payload = handle_submit(state, request.form)
    return payload


@app.post("/review")
async def review(request: ReviewRequest):
    state = session_store.get_or_create(request.sessionId)
    if request.form:
        handle_form_update(state, request.form)

    run_review(state)
    return create_response_payload(
        state,
        answer="Review completed. Scores are labeled as demo/mock until the production scoring model is finalized.",
        intent="SUBMIT_ACTION",
    )


@app.post("/review/mock-project")
async def review_mock_project(request: MockProjectRequest):
    state = session_store.get_or_create(request.sessionId)
    if request.form:
        handle_form_update(state, request.form)

    comparison = generate_mock_project_comparison(state)
    return {
        "sessionId": state["sessionId"],
        "comparison": comparison,
        "appState": get_public_state(state),
    }


@app.post("/upload")
async def upload_file(
    sessionId: str | None = Form(None),
    file: UploadFile = File(...),
):
    state = session_store.get_or_create(sessionId)
    result = await save_uploaded_file(file)
    state["retrieval"]["documents"] = list_indexed_documents()
    return {
        **result,
        "sessionId": state["sessionId"],
        "appState": get_public_state(state),
    }


@app.get("/documents")
async def documents(sessionId: str | None = None):
    state = session_store.get_or_create(sessionId)
    documents = list_indexed_documents()
    state["retrieval"]["documents"] = documents
    return {
        "sessionId": state["sessionId"],
        "documents": documents,
        "appState": get_public_state(state),
    }


@app.post("/documents/delete")
async def delete_document(request: DeleteDocumentRequest):
    state = session_store.get_or_create(request.sessionId)
    result = delete_indexed_document(request.source)
    documents = list_indexed_documents()
    state["retrieval"]["documents"] = documents
    state["retrieval"]["context"] = [
        item for item in state["retrieval"]["context"]
        if item.get("source") != request.source
    ]

    return {
        **result,
        "sessionId": state["sessionId"],
        "documents": documents,
        "appState": get_public_state(state),
    }


@app.post("/search-docs")
async def search_docs(request: SearchRequest):
    state = session_store.get_or_create(request.sessionId)
    results = search_documents(request.query, top_k=5)
    state["retrieval"]["query"] = request.query
    state["retrieval"]["context"] = results
    state["retrieval"]["documents"] = list_indexed_documents()
    return {
        "sessionId": state["sessionId"],
        "results": results,
        "appState": get_public_state(state),
    }
