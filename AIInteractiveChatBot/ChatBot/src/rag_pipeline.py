import json
import os
import uuid
from io import BytesIO

from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from fastapi import UploadFile
from pypdf import PdfReader
# from requests import session

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


async def save_uploaded_file(file: UploadFile):
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


def ask_llm(question: str, session: dict) -> str:
    user = session.get("user", {})
    results = search_index(question)
    context = build_context_from_results(results)

    history = session.get("history", [])
    last_10 = history[-10:]   
    conversation_context = ""
    history_info = f"Total conversation turns: {len(history)}"

    # User info block
    user_context = ""
    if any(user.values()):
        user_context = f"""
        Known User Information:
        - First Name: {user.get('firstName') or 'Not provided'}
        - Last Name: {user.get('lastName') or 'Not provided'}
        - Email: {user.get('email') or 'Not provided'}
        """

    for item in last_10:
        conversation_context += f"User: {item['question']}\n"
        conversation_context += f"Assistant: {item['answer']}\n"

    if len(conversation_context) > 4000:
        conversation_context = conversation_context[-4000:]

    user_prompt = f"""
    You are a helpful assistant that guides users to provide information needed for a form.

    - Understand the user’s input and capture relevant details.
    - Use the provided context if it is relevant.
    - If information is missing, ask simple follow-up questions.
    - Do not assume or make up values.
    - Keep responses short, clear, and conversational.
    
    {history_info}

    Previous Conversation:
    {conversation_context if conversation_context else "None"}

    {user_context}

    Context:
    {context if context else "No indexed content available"}
    
    Current Question: {question}
    """

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_prompt}],
        temperature=0,
        max_tokens=1000
    )

    return safe_text(resp.choices[0].message.content).strip()


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
