🤖 AI ChatBot with RAG + Agent Workflow

**(ChromaDB + OpenAI + FastAPI)**

This project is an **AI-powered chatbot backend*that combines:

🔍 **RAG (Retrieval Augmented Generation)*using ChromaDB
🤖 **LLM responses*using OpenAI
🧠 **Session-based memory + agent routing**
📝 **Conversational form workflows*(User / Student creation)



🚀 Key Features

📄 Upload and index documents (TXT / PDF) into ChromaDB
🔎 Semantic search over stored documents
💬 Context-aware chatbot with conversation history
🧭 **Agent-based routing**:

  Chat mode (LLM + RAG)
  Create User flow
  Create Student flow
🧠 Session memory (history + structured data)
🔌 Ready for Redis-based session persistence
⚡ Lightweight design (easy migration to LangGraph / Agent frameworks)



🏗️ Architecture Overview


Angular UI
   ↓
FastAPI (app.py)
   ↓
RouterAgent (agent_router.py)
   ↓
 ├── CreateUserAgent (deterministic flow)
 ├── CreateStudentAgent (deterministic flow)
 └── RAG Pipeline (rag_pipeline.py)
         ↓
     ChromaDB + OpenAI




📂 Project Structure


AIInteractiveChatBot/
│
├── app.py                FastAPI entry point
├── src/
│   ├── agent_router.py   Agent routing + workflows
│   └── rag_pipeline.py   RAG + LLM logic
│
├── chroma_db/            Local vector store
├── requirements.txt
├── .env
└── .venv/




⚙️ Setup Instructions

#1. Create Virtual Environment

bash
python -m venv .venv


#2. Activate

**PowerShell**

bash
.venv\Scripts\Activate.ps1


**CMD**

bash
.venv\Scripts\activate.bat




#3. Install Dependencies

bash
pip install -r requirements.txt




🔑 Environment Variables

Create `.env`:


OPENAI_API_KEY=your_api_key_here
CHROMA_DB_PATH=./chroma_db
COLLECTION_NAME=docs




▶️ Run Application

bash
uvicorn app:app --reload


Open:


http://127.0.0.1:8000




**🧠 How It Works**

**#1. Document Ingestion (RAG)**

Files uploaded via `/upload`
Text extracted and chunked
Stored in ChromaDB with embeddings

**#2. Chat Flow**

User input → RouterAgent
Routed to:

  Agent workflow (User/Student)
  OR RAG + LLM

**#3. LLM Processing**

Last 10 conversation turns included
User info injected (if available)
Relevant document chunks added
Final prompt sent to OpenAI



**💬 Chatbot Modes**

**🟢 Chat Mode (Default)**

Uses RAG + LLM
Context-aware answers
Uses history + user info



**🔵 Create User Flow**

**Step-by-step data collection:**

  First Name → Last Name → Email
Email validation
Returns structured JSON



**🟣 Create Student Flow**

**Collects:**

  Student ID → Name → Email → Grade
Returns structured JSON



📌 Example


User: create user
Bot: Enter first name:

User: Shiva
Bot: Enter last name:

User: Ramakrishnan
Bot: Enter email:




**📡 API Endpoints**

| Endpoint       | Description                  |
| -- | - |
| POST `/chat`   | Main chatbot interaction     |
| POST `/upload` | Upload documents to RAG      |
| POST `/submit` | Mock API for form submission |



**🛠 Tech Stack**

FastAPI
OpenAI (gpt-4o-mini)
ChromaDB
Python
pypdf



**⚠️ Common Issues**

**PowerShell Execution Policy**

bash
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned


Uvicorn Import Error

bash
uvicorn app:app --reload


**Missing API Key**

Ensure `.env` contains:


OPENAI_API_KEY=...


**🚀 Future Enhancements**

🔗 Redis-based session persistence
⚡ Streaming responses
🧩 Azure deployment
🔄 Observability + logging



**🎯 Design Philosophy**

Lightweight, framework-agnostic
Clear separation: routing vs LLM vs storage
Easy migration to agent frameworks
Deterministic flows for structured data capture



**👍 Summary**

This project demonstrates a **hybrid AI system** that combines:

RAG-based knowledge retrieval
Agent-driven workflows
Conversational data capture

👉 A strong foundation for building **enterprise AI assistants**



Happy coding 🚀
