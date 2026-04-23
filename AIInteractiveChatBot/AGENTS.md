# AGENTS.md

## Application Overview

Application Name: FormIQ AI  
Chat Assistant: Cora

FormIQ AI is an enterprise application with:
- Angular frontend
- FastAPI backend
- OpenAI-powered conversational AI
- ChromaDB-based RAG
- Agent-based orchestration for form completion and review workflows

Top-level pages:
- Home
- Chat
- Documents

---

## UI Structure

Home Page:
- Landing page
- Navigation entry

Chat Page:
- Left: navigation menu
- Center: chat (Cora)
- Right:
  - Top: BC form
  - Bottom: agent review results and scores

Documents Page:
- Upload documents
- Manage documents
- Index content into ChromaDB

---

## UI Theme

Primary:
- #0F766E
- #3B82F6

Secondary:
- #E0F2F1
- #F3F4F6

Accent:
- #10B981
- #F59E0B
- #EF4444

Background:
- #F9FAFB
- #FFFFFF

Agent Status:
- Pending: gray
- Running: blue
- Completed: green
- Needs Review: amber
- Error: red

---

## Core Architecture

Frontend:
- Angular SPA
- UI only

Backend:
- FastAPI
- Handles:
  - OpenAI calls
  - agent orchestration
  - RAG retrieval
  - validation
  - scoring
  - document ingestion
  - state management

Frontend must NOT:
- call OpenAI
- store secrets

---

## Agent Framework

- Router agent
- Specialized agents
- Tool-based execution
- RAG grounding

Do NOT depend on framework session objects.

---

## POC Rule

POC is reference only.

Do NOT:
- copy business logic
- treat as final implementation

AGENTS.md overrides POC.

---

## Application State

Single structure to manage:
- sessionId
- mode
- form data
- chat history
- retrieval context
- review status
- agent results
- scores

{
  "sessionId": "",
  "mode": "CHAT",
  "form": {},
  "chat": { "history": [] },
  "retrieval": {},
  "review": {
    "status": "NOT_STARTED",
    "agentResults": {},
    "scores": {}
  }
}

Must be portable to Redis.

---

## BC Form

Fields:
- intType (IT, Data, IT & Data)
- reqType
- intName
- inOverview
- inHighlights

---

## Form Rules

- All fields editable
- No locking
- No strict wizard

---

## Source of Truth

Priority:
1. Manual edits
2. Chip selections
3. AI inference

---

## Suggested Chips

Must be context-aware

Based on:
- current question
- form state
- RAG context

### Behavior
- Update form
- Become part of chat input/context
- Treated as user input

### Support
- Single-select (intType)
- Multi-select (highlights)

---

## Chat Intent Model

Supported intents:
- FORM_UPDATE
- FORM_QUESTION
- GENERAL_CHAT
- DOC_QUESTION
- SUBMIT_ACTION
- CHIP_SELECTION

---

## Mandatory RAG

All LLM calls must:
- Retrieve from ChromaDB
- Build grounded prompt
- Call model

No hallucination.

---

## Document Upload

Separate page.

Backend:
- extract text
- chunk
- embed
- store in ChromaDB

---

## Agent Workflow

Pre-submit:
- chat + form fill

Post-submit:
- run agents
- aggregate
- generate summary
- display results

---

## Review Agents

- Security Agent
- Data Agent
- EA Agent
- Acquisition Agent
- Pattern Alignment Agent
- Concept Composer

---

## Agent Rules

Each agent:
- single responsibility
- structured input/output
- uses RAG

---

## Review Results

Must display:
- agent status
- findings
- scores
- final summary

---

## Mock Scoring

Allowed:
- random/demo scores
- must be labeled

---

## JSON Rules

Folder: /rules/

Files:
- rules_index.json
- common_rule_model.json
- security_agent_rules.json
- data_agent_rules.json
- ea_agent_rules.json
- acquisition_agent_rules.json
- pattern_alignment_agent_rules.json
- concept_composer_rules.json

---

## Rule Structure

Each rule:
- id
- enabled
- priority
- condition
- message
- recommendation
- scoreImpact

---

## Codex Behavior

Codex must:
- create rules if missing
- update JSON instead of hardcoding

---

## Rule Priority

- JSON rules
- Python logic
- LLM

---

## API

Endpoints:
- /chat
- /submit
- /review
- /upload
- /documents
- /search-docs

---

## Security

- No API keys in frontend
- Use env variables
- sanitize uploads

---

## Coding Rules

- Small modules
- Clear naming
- Logic in Python or JSON
- Avoid lock-in

---

## Do NOT

- call OpenAI from Angular
- skip RAG
- lock fields
- trust POC blindly
- hardcode rules

---

## Definition of Done

- Home / Chat / Documents pages exist
- Chat + form coexist
- Chips feed into chat
- Form editable
- RAG used everywhere
- Agents run
- Results displayed
- JSON rules present
- No secrets exposed