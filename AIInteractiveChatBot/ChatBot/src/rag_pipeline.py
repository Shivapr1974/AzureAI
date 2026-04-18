import os
import uuid
from io import BytesIO

from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from fastapi import UploadFile
from pypdf import PdfReader

# Load .env variables
load_dotenv()

CHROMA_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "docs")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set")

client = OpenAI(api_key=OPENAI_API_KEY)

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

embedding_function = OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name="text-embedding-3-small"
)

collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_function
)


def safe_text(text):
    return text if text else ""


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50):
    words = text.split()
    chunks = []

    if not words:
        return chunks

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        start += max(chunk_size - overlap, 1)

    return chunks


def save_index(text: str, source: str = "manual_input"):
    chunks = chunk_text(text)

    if not chunks:
        return {"message": "No content to save", "count": 0, "source": source}

    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [{"source": source, "chunk": i + 1} for i in range(len(chunks))]

    collection.add(
        ids=ids,
        documents=chunks,
        metadatas=metadatas
    )

    return {
        "message": "Saved to ChromaDB successfully",
        "count": len(chunks),
        "source": source
    }


def extract_text_from_txt(content: bytes) -> str:
    return content.decode("utf-8", errors="ignore")


def extract_text_from_pdf(content: bytes) -> str:
    pdf_reader = PdfReader(BytesIO(content))
    pages = []

    for page in pdf_reader.pages:
        pages.append(page.extract_text() or "")

    return "\n".join(pages)


async def save_uploaded_file_to_chroma(file: UploadFile):
    content = await file.read()
    filename = file.filename or "uploaded_file"

    lower_name = filename.lower()

    if lower_name.endswith(".txt"):
        text = extract_text_from_txt(content)
    elif lower_name.endswith(".pdf"):
        text = extract_text_from_pdf(content)
    else:
        return {
            "message": "Unsupported file type. Please upload .txt or .pdf",
            "count": 0,
            "source": filename
        }

    return save_index(text=text, source=filename)


def search_index(query: str, top_k: int = 5):
    return collection.query(
        query_texts=[query],
        n_results=top_k
    )


def build_context_from_results(results: dict) -> str:
    chunks = []

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    for i, doc in enumerate(docs):
        meta = metas[i] if i < len(metas) else {}
        source = meta.get("source", "unknown")
        chunk_no = meta.get("chunk", "?")
        chunks.append(f"Source: {source} | Chunk: {chunk_no}\n{doc}")

    return "\n\n---\n\n".join(chunks)


def ask_llm_with_search(question: str) -> str:
    results = search_index(question)
    context = build_context_from_results(results)

    user_prompt = f"""
You are a helpful assistant that guides users to provide information needed for a form.

- Understand the user’s input and capture relevant details.
- Use the provided context if it is relevant.
- If information is missing, ask simple follow-up questions.
- Do not assume or make up values.
- Keep responses short, clear, and conversational.

Context:
{context if context else "No indexed content available"}

Question: {question}
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_prompt}],
        temperature=0,
        max_tokens=1000
    )

    return safe_text(resp.choices[0].message.content).strip()