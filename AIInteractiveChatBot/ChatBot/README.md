# 🤖 AI ChatBot with RAG (ChromaDB + OpenAI)

This project is a simple AI chatbot backend built using:
- FastAPI
- OpenAI
- ChromaDB (for RAG - Retrieval Augmented Generation)

The chatbot can:
- Store documents into ChromaDB
- Search relevant content
- Answer questions using OpenAI
- Guide users to fill form-like information conversationally

---

# 🚀 Project Structure

AIChatBot/
│
├── app.py                # Main FastAPI app
├── requirements.txt
├── .env
├── .venv/               # Virtual environment
└── chroma_db/           # Local Chroma storage

---

# ⚙️ Setup Instructions

## 1. Create Virtual Environment

python -m venv .venv

## 2. Activate Environment

### Windows (PowerShell)
.venv\Scripts\Activate.ps1

### Windows (CMD)
.venv\Scripts\activate.bat

---

## 3. Install Dependencies

pip install -r requirements.txt

---

# 🔑 Environment Variables

Create a `.env` file:

OPENAI_API_KEY=your_api_key_here
CHROMA_DB_PATH=./chroma_db
COLLECTION_NAME=docs

---

# ▶️ Run Application

uvicorn app:app --reload

Open:
http://127.0.0.1:8000

---

# 🧠 How It Works

## 1. Save Data (RAG Ingestion)
- Text is chunked
- Stored in ChromaDB
- Embeddings generated using OpenAI

## 2. Search
- User question converted to embedding
- Chroma returns top relevant chunks

## 3. LLM Response
- Context + question sent to OpenAI
- Model generates structured answer

---

# 💬 Chatbot Behavior

The chatbot:
- Extracts user info (name, email, etc.)
- Asks follow-up questions
- Guides user step-by-step
- Avoids making assumptions

---

# 📌 Example Flow

User:
My name is Shiva

Bot:
Got your name as Shiva. What is your email?

---

# ⚡ API Endpoints (Future)

You can extend this with:

POST /upload → Upload documents  
POST /ask → Ask chatbot  
POST /form → Submit form  

---

# 🛠 Requirements

openai==1.109.1  
chromadb==1.3.4  
fastapi==0.110.0  
uvicorn==0.38.0  
python-dotenv==1.2.1  
pypdf==6.2.0  
requests==2.32.5  

---

# ⚠️ Common Issues

## PowerShell Execution Policy Error
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

## Uvicorn Import Error
Use:
uvicorn app:app --reload

## Missing API Key
Ensure `.env` has:
OPENAI_API_KEY=your_key

---

# 🚀 Next Steps

- Add Angular frontend
- Auto-fill forms from chatbot
- Add validation APIs (Spring Boot / FastAPI)
- Add Redis caching
- Add streaming responses
- Deploy to Azure

---

# 👍 Summary

This is a simple, production-ready foundation for:
- Chatbot + RAG
- AI-assisted form filling
- Scalable backend architecture

---

Happy coding 🚀