from __future__ import annotations

import os
import re
import uuid
from collections import Counter
from io import BytesIO

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv
from fastapi import UploadFile
from openai import OpenAI
from pypdf import PdfReader


load_dotenv()

CHROMA_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "formiq_docs")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

_openai_client: OpenAI | None = None
_chroma_client: chromadb.PersistentClient | None = None
_collection = None


def get_openai_client() -> OpenAI | None:
    global _openai_client
    if not OPENAI_API_KEY:
        return None
    if _openai_client is None:
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client


def get_collection():
    global _chroma_client, _collection
    if _collection is not None:
        return _collection

    if not OPENAI_API_KEY:
        return None

    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

    embedding_function = OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name="text-embedding-3-small",
    )

    _collection = _chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function,
    )
    return _collection


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", name or "")
    return cleaned[:120] or f"upload_{uuid.uuid4().hex}.txt"


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 75) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        start += max(chunk_size - overlap, 1)
    return chunks


def extract_text_from_pdf(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_text_from_file(filename: str, content: bytes) -> str:
    lower_name = filename.lower()
    if lower_name.endswith(".txt"):
        return content.decode("utf-8", errors="ignore")
    if lower_name.endswith(".pdf"):
        return extract_text_from_pdf(content)
    raise ValueError("Unsupported file type. Please upload .txt or .pdf files.")


def save_index(text: str, source: str) -> dict:
    collection = get_collection()
    if collection is None:
        return {
            "message": "Document could not be indexed because OPENAI_API_KEY is missing. Add the key to enable ChromaDB embeddings.",
            "count": 0,
            "source": source,
        }

    chunks = chunk_text(text)
    if not chunks:
        return {
            "message": "No content could be extracted from the document.",
            "count": 0,
            "source": source,
        }

    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [
        {"source": source, "chunk": index + 1}
        for index in range(len(chunks))
    ]
    collection.add(ids=ids, documents=chunks, metadatas=metadatas)
    return {
        "message": "Document indexed in ChromaDB successfully.",
        "count": len(chunks),
        "source": source,
    }


async def save_uploaded_file(file: UploadFile) -> dict:
    filename = sanitize_filename(file.filename or "uploaded_file.txt")
    content = await file.read()

    try:
        text = extract_text_from_file(filename, content)
    except ValueError as exc:
        return {"message": str(exc), "count": 0, "source": filename}

    return save_index(text=text, source=filename)


def list_indexed_documents() -> list[dict]:
    collection = get_collection()
    if collection is None:
        return []

    try:
        records = collection.get(include=["metadatas"])
    except Exception:
        return []

    counts: Counter[str] = Counter()
    for metadata in records.get("metadatas", []):
        if metadata:
            counts[metadata.get("source", "unknown")] += 1

    documents = [
        {"source": source, "chunkCount": chunk_count}
        for source, chunk_count in sorted(counts.items())
    ]
    return documents


def delete_indexed_document(source: str) -> dict:
    cleaned_source = source.strip()
    if not cleaned_source:
        return {"message": "Document source is required.", "deleted": 0, "source": source}

    collection = get_collection()
    if collection is None:
        return {
            "message": "Document deletion is unavailable because the Chroma collection is not initialized.",
            "deleted": 0,
            "source": cleaned_source,
        }

    try:
        records = collection.get(where={"source": cleaned_source})
    except Exception:
        return {
            "message": "Unable to look up the document for deletion.",
            "deleted": 0,
            "source": cleaned_source,
        }

    ids = records.get("ids", []) if records else []
    if not ids:
        return {
            "message": f"No indexed document named {cleaned_source} was found.",
            "deleted": 0,
            "source": cleaned_source,
        }

    try:
        collection.delete(ids=ids)
    except Exception:
        return {
            "message": f"Unable to delete {cleaned_source} from ChromaDB.",
            "deleted": 0,
            "source": cleaned_source,
        }

    return {
        "message": f"Removed {cleaned_source} from indexed documents.",
        "deleted": len(ids),
        "source": cleaned_source,
    }


def search_documents(query: str, top_k: int = 5) -> list[dict]:
    query = query.strip()
    if not query:
        return []

    collection = get_collection()
    if collection is None:
        return []

    try:
        results = collection.query(query_texts=[query], n_results=top_k)
    except Exception:
        return []

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    payload: list[dict] = []

    for index, document in enumerate(documents):
        metadata = metadatas[index] if index < len(metadatas) else {}
        distance = distances[index] if index < len(distances) else None
        payload.append(
            {
                "source": metadata.get("source", "unknown"),
                "chunk": metadata.get("chunk", "?"),
                "text": document,
                "distance": distance,
            }
        )

    return payload


def build_grounded_prompt(question: str, state: dict, contexts: list[dict]) -> str:
    form = state.get("form", {})
    form_context = "\n".join(
        f"- {field}: {value or 'Not provided'}"
        for field, value in form.items()
    )
    retrieval_context = "\n\n".join(
        f"Source: {item['source']} | Chunk: {item['chunk']}\n{item['text']}"
        for item in contexts
    ) or "No retrieved document context available."

    return f"""
You are Cora, the FormIQ AI assistant.

Use the retrieved document context when helpful.
Use the BC form state when it helps answer the question.
Allow non-grounded replies when the retrieved context is missing or not useful for the user's question.
Do not hallucinate.
Keep the response concise and easy to act on.

BC Form State:
{form_context}

Retrieved Context:
{retrieval_context}

User Question:
{question}
""".strip()


def build_fallback_prompt(question: str, state: dict) -> str:
    form = state.get("form", {})
    form_context = "\n".join(
        f"- {field}: {value or 'Not provided'}"
        for field, value in form.items()
    )

    return f"""
You are Cora, the FormIQ AI assistant.

No useful retrieved document context was found for this message.
You should still answer helpfully and naturally.

Rules:
- If the user is making normal conversation, respond normally.
- If the user is asking about the BC form, use the current form state when helpful.
- If the user appears to want document-backed facts, be honest that no useful supporting document context was found.
- Keep the answer concise and easy to act on.

Current BC Form State:
{form_context}

User Question:
{question}
""".strip()


def grounded_answer(question: str, state: dict) -> tuple[str, list[dict]]:
    contexts = search_documents(question, top_k=4)
    state["retrieval"]["query"] = question
    state["retrieval"]["context"] = contexts
    state["retrieval"]["documents"] = list_indexed_documents()

    client = get_openai_client()
    if not contexts:
        if client is None:
            return (
                "I could not find document context, but you can still keep chatting with me. "
                "If you want grounded document answers, upload files on the Documents page.",
                contexts,
            )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": build_fallback_prompt(question, state)}],
            temperature=0.4,
            max_tokens=300,
        )
        answer = response.choices[0].message.content or ""
        return answer.strip(), contexts

    if client is None:
        first = contexts[0]
        return (
            f"I found supporting context in {first['source']} but OPENAI_API_KEY is not configured, so I cannot generate a grounded summary yet.",
            contexts,
        )

    prompt = build_grounded_prompt(question, state, contexts)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=400,
    )
    answer = response.choices[0].message.content or ""
    return answer.strip(), contexts
