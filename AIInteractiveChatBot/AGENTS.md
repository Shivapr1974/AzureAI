# AGENTS.md

## Application Overview

**Application Name:** FormIQ AI  
**Chat Assistant:** Cora

FormIQ AI is an enterprise application with:
- Angular frontend
- FastAPI backend
- OpenAI-powered conversational AI
- ChromaDB-based RAG (Retrieval Augmented Generation)
- Agent-based orchestration for form completion and review workflows

UI Layout:
- Left: Navigation (hamburger menu)
- Center: Chatbot (Cora)
- Right:
  - Top: BC Form (editable)
  - Bottom: Agent Review Workflow (after submit)

---

## Core Architecture

Frontend:
- Angular SPA
- Responsible for UI, form rendering, suggestion chips, and chat interface
- Must NOT call OpenAI APIs directly

Backend:
- FastAPI
- Owns:
  - LLM interactions
  - Agent orchestration
  - Validation and scoring
  - RAG retrieval
  - Session and form state

LLM:
- OpenAI models
- Used for:
  - extraction
  - reasoning
  - summarization
  - conversational responses

RAG:
- ChromaDB vector store
- Mandatory for all LLM interactions

---

## Agent Framework

For now, use Microsoft Agent Framework concepts and patterns.

Follow a lightweight agent orchestration model:
- Router Agent determines intent and mode
- Specialized agents handle specific responsibilities
- Agents may use tools (RAG, validation, scoring)
- Agents may call LLM (must use RAG)

Do NOT tightly couple implementation to framework-specific runtime/session objects.

---

## Portability and State

Session and state must be application-owned and framework-agnostic.

Maintain separate models for:
- session state
- form state
- chat history
- retrieval context
- agent results
- scoring outputs

Do NOT rely on framework-managed session objects as the source of truth.

Design must allow future migration to:
- LangGraph
- OpenAI Agents SDK
- Microsoft Agent Framework runtime

---

## Chat Assistant: Cora

Cora is:
- helpful, concise, professional
- conversational but not overly casual
- capable of:
  - form guidance
  - clarification
  - RAG-grounded answers
  - light conversational responses (e.g., jokes)

Cora must:
- preserve form context during chat
- never lose user progress
- guide users toward completion
- respect user edits over inferred values

---

## BC Form Definition

Fields:

- intType (allowed: IT, Data, IT & Data)
- reqType (free text)
- intName (free text)
- inOverview (free text)
- inHighlights (free text)

---

## Form Behavior Rules

- All form fields must remain editable at all times
- Users can:
  - manually edit any field
  - override AI suggestions
  - revisit previous sections

Do NOT:
- lock fields after AI population
- enforce rigid step-by-step wizard flow

---

## Source of Truth

Application-owned form state is the source of truth.

Priority:
1. Manual user edits
2. Explicit suggestion selection
3. AI-extracted values

---

## Suggested Values (Chips)

Fields may have suggestion chips.

Rules:
- support single-select (e.g., intType)
- support multi-select (e.g., highlights)
- user can:
  - select suggestions
  - combine with manual input

Suggestions:
- update form state
- may be passed to chat as structured context

Do NOT restrict users to suggestions unless field is constrained.

---

## Chat Interaction Modes

Every message must be classified:

- FORM_UPDATE
- FORM_QUESTION
- GENERAL_CHAT
- DOC_QUESTION
- SUBMIT_ACTION

Do NOT assume all messages are form inputs.

Examples:
- "IT integration" → FORM_UPDATE
- "What is intType?" → FORM_QUESTION
- "Tell me a joke" → GENERAL_CHAT

---

## Mandatory RAG Rule

ALL LLM calls MUST use RAG:

Applies to:
- chat responses
- clarification
- field suggestions
- all agents
- report generation

Process:
1. Retrieve context from ChromaDB
2. Build prompt with:
   - user input
   - form state
   - chat history (trimmed)
   - retrieved context
3. Call LLM

If no useful context:
- explicitly say so
- do NOT hallucinate

---

## Document Upload (ChromaDB)

Angular must support file upload.

Backend must:
- accept files
- extract text (PDF/TXT)
- chunk text
- embed using OpenAI
- store in ChromaDB

Store metadata:
- documentId
- fileName
- uploadedAt
- chunkNumber
- source/type

Upload must be independent of chat logic.

---

## Agent Workflow

### Pre-Submit

User:
→ Chat with Cora
→ Form gradually filled via chat + UI

---

### Post-Submit Workflow

1. Router sets mode = REVIEW_RUNNING

2. Review Orchestrator triggers agents:

- Security Agent
- Data Agent
- Enterprise Architect Agent
- Acquisition Agent
- Pattern Alignment Agent

3. Agents run (prefer parallel execution)

4. Aggregate results

5. Concept Composer generates final report

6. Return results to UI

---

## Agent Responsibilities

Security Agent:
- security controls, encryption, access, compliance

Data Agent:
- classification, privacy, retention, handling

EA Agent:
- architecture, integration, scalability

Acquisition Agent:
- vendor, contracts, SLAs

Pattern Alignment:
- approved patterns, anti-patterns

Concept Composer:
- final summary/report

---

## Agent Design Rules

Each agent must:
- have one responsibility
- accept structured input
- return structured JSON
- use RAG before LLM

Do NOT:
- mix multiple responsibilities
- embed orchestration inside agents
- bypass router

---

## Scoring Rules

- scoring must be deterministic (Python)
- do NOT rely on LLM for final scores

Example:
- Rubric = 70%
- Pattern = 30%

---

## UX Behavior

- user can interrupt flow anytime
- small talk allowed
- form progress must persist

Example:
User: "Tell me a joke"
Cora:
- responds with joke
- continues guidance

---

## API Design

Separate endpoints:

- /chat
- /upload
- /submit
- /review
- /search-docs

Return consistent JSON:
- answer
- form state
- missing fields
- agent status
- scores

---

## Security Rules

- never expose API keys in frontend
- use environment variables
- sanitize uploads
- avoid logging sensitive data

---

## Coding Rules

- keep modules small and focused
- use type hints
- keep prompts separate
- keep business logic in Python

---

## Do NOT

- do not call OpenAI from Angular
- do not skip RAG
- do not hallucinate values
- do not lock form fields
- do not depend on framework session objects
- do not mix orchestration and agent logic

---

## Definition of Done

A change is complete only if:

- UI works (left/center/right layout)
- chat + form coexist
- RAG is used
- form remains editable
- suggestions work
- agent workflow executes correctly
- no secrets exposed
- behavior matches AGENTS.md