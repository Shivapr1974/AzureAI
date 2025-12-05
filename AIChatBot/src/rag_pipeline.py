import json
import os
from dotenv import load_dotenv
from openai import OpenAI
import requests


# Load .env variables
load_dotenv()

SEARCH_URL = os.getenv("AZURE_SEARCH_URL")
INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
API_VERSION = os.getenv("API_VERSION")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def extract_title_and_body(raw_content: str):
    """
    Extracts `title` from YAML front matter and returns (title, body_without_front_matter).
    If no front matter exists, returns (None, raw_content).
    """
    if not raw_content:
        return None, ""

    text = raw_content.replace("\r\n", "\n")

    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            front_matter = parts[1]
            body = parts[2]

            title = None
            for line in front_matter.splitlines():
                line = line.strip()
                if line.lower().startswith("title:"):
                    title = line.split(":", 1)[1].strip()
                    break

            return title, body.lstrip("\n")

    return None, raw_content


def search_index(query: str):
    """
    Calls Azure AI Search and returns the raw JSON response.
    """
    url = f"{SEARCH_URL}/indexes/{INDEX_NAME}/docs/search?api-version={API_VERSION}"

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_SEARCH_KEY
    }

    body = {
        "search": query,
        "top": 5,
        "count": True
    }

    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    return response.json()

def build_context_from_results(results: dict) -> str:
    """
    Builds a text context from Azure Search results:
    TITLE
    <body>
    ---
    """
    chunks = []

    for doc in results.get("value", []):
        raw_content = doc.get("content", "")
        title_from_content, body = extract_title_and_body(raw_content)

        title = (
            title_from_content
            or doc.get("title")
            or doc.get("metadata_storage_name")
            or "(no title)"
        )

        chunks.append(f"TITLE: {title}\n{body.strip()}")

    return "\n\n---\n\n".join(chunks)

def safe_text(value):
    return value if isinstance(value, str) else ""

def ask_llm_with_search(question: str) -> str:
    """
    Runs Azure Search, feeds the results to OpenAI, and returns a nicely formatted answer.
    """
    # 1. Get search results from Azure AI Search
    results = search_index(question)

    # 2. Build context from docs (titles + content)
    context = build_context_from_results(results)

    # 3. Build prompt for LLM
    user_prompt = f"""
    You are an Azure cloud adoption assistant.

    Use ONLY the following context to answer the question. 
    If something is not in the context, say you don't know.

    Context:
    {context}

    Question: {question}

    Format the answer in clear markdown:
    - Use headings where useful
    - Use bullet points for lists
    - Be concise but complete.
    """

    # 4. Call OpenAI Chat Completions
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": user_prompt}
        ],
        temperature=0,
        max_tokens=1500
    )

    msg_content = resp.choices[0].message.content
    answer = safe_text(msg_content).strip()
    return answer


if __name__ == "__main__":
    question = "What is a good cloud adoption strategy and how do landing zones help?"
    answer = ask_llm_with_search(question)

    print("\n======================================")
    print("💬 ANSWER FROM LLM")
    print("======================================\n")
    print(answer)
    print("\n======================================\n")