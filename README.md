# Azure Cloud Adoption RAG Chatbot (FastAPI + Azure AI Search + LLM)

This project is a **Retrieval-Augmented Generation (RAG)** chatbot designed to answer questions about the **Azure Cloud Adoption Framework**, including topics like Landing Zones, Governance, Cost Optimization, Networking, Identity, Management, and Operations.

It uses:

- **Azure Blob Storage** → store your `.md` content  
- **Azure AI Search** → index and retrieve relevant chunks  
- **FastAPI** → backend API + lightweight chat UI  
- **OpenAI or Azure LLMs** → generate grounded answers  
- **Custom HTML/JS chat interface** → served directly by FastAPI  

This is a fully working, production-ready example of how to build a **server-rendered RAG chatbot** without Angular/React.

---

## 🚀 Features

### 🔍 Retrieval-Augmented Generation
- Queries Azure AI Search for relevant `.md` content  
- Extracts YAML front matter titles  
- Builds clean context  
- Sends context + question to an LLM  
- Returns **grounded**, markdown-formatted answers  

### ⚡ FastAPI Backend
- `/chat` endpoint runs the full RAG pipeline  
- No frontend framework required  
- Serves an HTML chatbot UI directly from Python  

### 🌐 Azure Search Integration
- Search query via REST API  
- Fetches top 5 relevant documents  
- Builds final context for RAG  

### 🤖 LLM-Agnostic
Supports:
- OpenAI GPT-4o / GPT-4o-mini  
- Azure OpenAI GPT-4.1 / GPT-4o  
- Azure Model Catalog: Phi-3.5, Llama 3.x  

### 💬 Built-in Chat UI
- Custom HTML chat interface  
- Markdown rendering via marked.js  
- Spinner & message bubbles  
- No external assets needed  

---

## 📂 Project Structure

```
/your-project
│
├── app.py               # FastAPI app + chat UI
├── src/
│   └── rag_pipeline.py  # RAG logic (search -> context -> LLM)
├── .env                 # Environment variables
├── requirements.txt     # Python deps
└── README.md            # <-- This file
```

---

## 🧪 How It Works (High-Level)

### 1️⃣ Upload Markdown Files → Azure Blob Storage
Each file includes YAML front matter:

```md
---
title: Azure Landing Zones Overview
topic: landing-zones
audience: architects
---

# Azure Landing Zones
...
```

### 2️⃣ Azure AI Search Index + Indexer
The indexer extracts:

- title  
- topic  
- audience  
- content  
- metadata_storage_name  

### 3️⃣ FastAPI Receives User Question

```json
{ "question": "What is a landing zone?" }
```

### 4️⃣ It Calls Azure Search
Returns relevant chunks.

### 5️⃣ Builds RAG Prompt
Combines:

```
TITLE: Landing Zones
<body text>

---
```

### 6️⃣ Calls LLM  
Generates structured markdown.

### 7️⃣ HTML UI Renders Markdown  
Cleanly displayed to user.

---

## ⚙️ Installation

### 1️⃣ Clone Repo
```bash
git clone https://github.com/<your-user>/<your-repo>.git
cd <your-repo>
```

### 2️⃣ Create venv
```bash
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Create `.env`

```
AZURE_SEARCH_URL=https://<your-service>.search.windows.net
AZURE_SEARCH_INDEX=cloud-adoption-content-index
AZURE_SEARCH_KEY=xxxx
API_VERSION=2023-11-01

# If using OpenAI
OPENAI_API_KEY=sk-xxxx
```

### For Azure OpenAI:
```
OPENAI_API_BASE=https://<azure-openai>.openai.azure.com
OPENAI_API_KEY=<key>
OPENAI_API_VERSION=2024-xx-xx
OPENAI_DEPLOYMENT=<model-deployment>
```

---

## ▶️ Run App Locally

```bash
uvicorn app:app --reload
```

UI loads at:

```
http://127.0.0.1:8000/
```

---

## 🧪 Test RAG Pipeline

```bash
python src/rag_pipeline.py
```

---

## 🚀 Deployment (Optional)

### Azure App Service
- Deploy Python App
- Add environment variables  
- Done

### Azure Container Apps
- Optional Dockerfile  
- Good for scaling  

---

## 📌 Future Enhancements

- Add citations  
- Switch to vector/semantic hybrid search  
- Switch to Azure Phi-3.5-mini (free)  
- Conversation memory  
- User authentication (AAD)

---

## 📜 License

MIT or any license you choose.
