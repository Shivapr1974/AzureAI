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

Stay grounded in the retrieved document context and the BC form state.
If the answer is not supported by the retrieved context, say that clearly and ask the user to upload more documents or edit the form manually.
Do not hallucinate.
Keep the response concise and easy to act on.

BC Form State:
{form_context}

Retrieved Context:
{retrieval_context}

User Question:
{question}
""".strip()


def grounded_answer(question: str, state: dict) -> tuple[str, list[dict]]:
    contexts = search_documents(question, top_k=4)
    state["retrieval"]["query"] = question
    state["retrieval"]["context"] = contexts
    state["retrieval"]["documents"] = list_indexed_documents()

    if not contexts:
        return (
            "I don’t have grounded document context for that yet. Upload documents on the Documents page or continue editing the BC form manually.",
            contexts,
        )

    client = get_openai_client()
    if client is None:
        first = contexts[0]
        return (
            f"I found supporting context in {first['source']} but OPENAI_API_KEY is not configured, so I can’t generate a grounded summary yet.",
            contexts,
        )

    prompt = build_grounded_prompt(question, state, contexts)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=400,
    )
    answer = response.choices[0].message.content or ""
    return answer.strip(), contexts
