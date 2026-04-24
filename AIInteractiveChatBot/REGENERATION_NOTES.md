# Regeneration Notes

This file complements `AGENTS.md` and captures concrete current behavior that should be preserved if the app is regenerated.

## Current Product Shape

- Angular frontend in `UI/ai-chatbot-ui`
- FastAPI backend in `ChatBot`
- Rules stored in `/rules`
- App is currently a working POC for:
  - conversational assistance
  - guided BC form fill
  - document indexing and search
  - JSON-driven review scoring

## Chat Behavior

- Cora is both:
  - a normal conversational assistant
  - a BC form assistant
- Chat should not feel locked into BC form mode
- Normal conversational prompts such as jokes or casual questions should still work
- Guided BC form mode should resume after casual chat instead of losing the user’s place

## Guided Form UX

- Trigger phrases like `I want to fill a BC Form` should start guided mode
- Guided mode asks one missing field at a time
- A guidance card appears inside the chat flow and shows:
  - current form field
  - hint text
  - quick chips when relevant
- Guidance card should stay visually associated with the active chat turn

## BC Form UX

- Form stays editable at all times
- No locking
- No strict wizard
- Users can mix:
  - guided chat answers
  - direct typing into form fields
  - chip selections

## Document UX

- Upload TXT and PDF files
- Index them into ChromaDB
- Show indexed documents list
- Allow removing indexed documents by source
- Document search panel should support:
  - Search
  - Clear

## Review UX

- Review is fast and currently does not need true parallel agent execution
- Present multiple reviewer sections in UI
- Each reviewer reads its own JSON rule pack
- Scores are explicitly demo/mock

## Implementation Expectations

- Preserve the current endpoints:
  - `/state`
  - `/chat`
  - `/form`
  - `/submit`
  - `/review`
  - `/upload`
  - `/documents`
  - `/documents/delete`
  - `/search-docs`
  - `/reset`
- Keep logic in Python and JSON, not Angular
- Keep OpenAI calls backend-only
- Keep rules configurable in JSON instead of hardcoding scoring rules in UI
