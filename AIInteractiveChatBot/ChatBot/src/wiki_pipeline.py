import os
import re
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from fastapi import UploadFile
from pydantic import BaseModel
from pypdf import PdfReader

# Load .env variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WIKI_ROOT = os.getenv("WIKI_ROOT", "./wiki")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set")

client = OpenAI(api_key=OPENAI_API_KEY)


class WikiPage(BaseModel):
    category: str
    slug: str
    title: str
    content: str


def safe_text(text):
    return text if text else ""


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def build_wiki_path(category: str, slug: str) -> str:
    category = slugify(category or "misc")
    slug = slugify(slug or "untitled")
    folder = os.path.join(WIKI_ROOT, category)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, f"{slug}.md")


def extract_text_from_txt(content: bytes) -> str:
    return content.decode("utf-8", errors="ignore")


def extract_text_from_pdf(content: bytes) -> str:
    pdf_reader = PdfReader(BytesIO(content))
    pages = []

    for page in pdf_reader.pages:
        pages.append(page.extract_text() or "")

    return "\n".join(pages)


def compile_to_wiki(text: str, source: str = "manual_input"):
    if not text.strip():
        return {"message": "No content to save", "count": 0, "source": source}

    prompt = f"""
    Analyze the document and return JSON with:
    - category: one of systems, processes, entities, projects, glossary, misc
    - slug: short filename
    - title: page title
    - content: markdown wiki page content

    Keep the content concise, structured, and useful for answering future questions.

    Source: {source}

    Document:
    {text[:12000]}
    """

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0
    )

    page = WikiPage.model_validate_json(resp.choices[0].message.content)
    path = build_wiki_path(page.category, page.slug)

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {page.title}\n\n{page.content}\n\n---\nSource: {source}\n")

    return {
        "message": "Saved to Wiki successfully",
        "count": 1,
        "source": source,
        "path": path
    }


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

    return compile_to_wiki(text=text, source=filename)


def search_wiki(query: str, top_k: int = 5):
    files = list(Path(WIKI_ROOT).rglob("*.md"))
    scored = []

    query_words = query.lower().split()

    for file in files:
        text = file.read_text(encoding="utf-8")
        lower_text = text.lower()
        score = 0

        for word in query_words:
            score += lower_text.count(word)

        if score > 0:
            scored.append((score, str(file), text))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]


def build_context_from_results(results) -> str:
    chunks = []

    for score, path, doc in results:
        chunks.append(f"Source: {path} | Score: {score}\n{doc}")

    return "\n\n---\n\n".join(chunks)


def ask_llm(question: str, session: dict) -> str:
    user = session.get("user", {})
    results = search_wiki(question)
    context = build_context_from_results(results)

    history = session.get("history", [])
    last_10 = history[-10:]
    conversation_context = ""
    history_info = f"Total conversation turns: {len(history)}"

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

    - Understand the user input and capture relevant details.
    - Use the provided wiki context if relevant.
    - If information is missing, ask simple follow-up questions.
    - Do not assume or make up values.
    - Keep responses short, clear, and conversational.

    {history_info}

    Previous Conversation:
    {conversation_context if conversation_context else "None"}

    {user_context}

    Wiki Context:
    {context if context else "No wiki content available"}

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
