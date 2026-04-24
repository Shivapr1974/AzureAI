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
- /state
- /form
- /reset
- /documents/delete

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

---

## Current Implementation Notes

These notes describe the current working behavior of the codebase so it can be regenerated more accurately.

### Frontend Theme

- Current UI palette is dark navy and light blue, not the earlier teal-first palette
- Left sidebar remains dark/navy
- Main content area is light with navy/blue accents

### Chat Page Behavior

- Left sidebar: navigation and session status
- Center panel: Cora chat
- Right panel top: BC form
- Right panel bottom: review results
- `Start New Session` button is next to form actions, not in the left sidebar

### Guided BC Form Flow

- Saying things like `I want to fill a BC Form` starts guided BC form mode
- Guided mode asks for the next missing BC form field in this order:
  - intType
  - reqType
  - intName
  - inOverview
  - inHighlights
- User can answer in plain free text
- `intType` is constrained to:
  - IT
  - Data
  - IT & Data
- `reqType`, `intName`, `inOverview`, and `inHighlights` allow free text
- Guided mode also allows explicit field-style updates such as:
  - `integration name: ...`
  - `overview: ...`
- Guided mode should not force all chat into form capture
- Normal chat like `tell me a joke` should still work while guided mode is active
- After a normal chat answer during guided mode, Cora should gently return to the current missing field
- Typing any of these cancels guided mode while keeping existing form values:
  - `cancel`
  - `stop`
  - `exit`
  - `never mind`
  - `nevermind`

### Suggested Chips

- Suggested chips are treated as user input
- Suggested chips update form values
- Suggested chips should appear near the guided prompt area in the chat panel, not at the top of the chat panel
- In guided mode, chips should only be shown for the current missing field
- Guided mode must not allow a later-field chip to skip earlier missing fields
- `intType` chips are single-select
- `inHighlights` chips support multi-select style accumulation

### Session Reset

- `Start New Session` clears:
  - BC form values
  - chat history
  - retrieval context
  - review state
- Reset creates a new session id

### Documents Page

- Documents page supports:
  - upload and indexing into ChromaDB
  - listing indexed documents
  - search against indexed chunks
  - delete/remove indexed documents by source
- ChromaDB Lookup has:
  - `Search` button
  - `Clear` button to clear search text and current search results

### Review Execution

- Review is currently implemented as one backend review pass, not true parallel runtime agents
- UI still presents separate agent sections:
  - Security Agent
  - Data Agent
  - EA Agent
  - Acquisition Agent
  - Pattern Alignment Agent
  - Concept Composer
- Agent scores are JSON-rule-driven mock/demo scores
- Each review area starts at 100
- Matching rule impacts reduce the score
- Overall score is the average of agent scores
- Mock/demo labeling must remain visible in the UI

### RAG and Chat Behavior

- Document-backed questions should use retrieved ChromaDB context when available
- If retrieved context exists, grounded prompting should be used
- If no relevant RAG context exists, Cora should still be able to respond to normal chat and lightweight assistance requests
- If the user is asking for document-backed facts and no retrieval context is found, Cora should say that no supporting document context was found
- Frontend must not call OpenAI directly

### Backend State Shape

- State includes:
  - sessionId
  - mode
  - form
  - chat.history
  - retrieval.query
  - retrieval.context
  - retrieval.documents
  - review.status
  - review.agentResults
  - review.scores
  - review.summary
- Form source priority remains:
  1. Manual edits
  2. Chip selections
  3. AI inference
