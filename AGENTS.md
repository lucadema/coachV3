# AGENTS.md

## Project
Coach V3 is a Python PoC with:
- FastAPI backend in `backend/`
- Streamlit frontend in `frontend/`
- stage modules in `backend/stages/`
- smoke regression script in `smoke_test.py`

## Current architecture source
Use this reading order before editing:
1. `AGENTS.md`
2. `docs/architecture_v3_1.md` — latest execution model and stage mechanics
3. `docs/architecture_v3.md` — broader V3 architecture and rationale
4. current code files in the repo
5. tests and smoke tests

If `architecture_v3.md` and `architecture_v3_1.md` differ on execution flow, state behavior, or controller/stage/engine responsibilities, prefer `architecture_v3_1.md`.

For exact names, imports, routes, model fields, and signatures, prefer the current working code.

## Working style
- Plan first for any non-trivial task before editing code.
- Read the relevant files before changing anything.
- Preserve the current working scaffold unless the task explicitly requires a contract change.
- Prefer the smallest clean change that satisfies the task.
- Do not redesign architecture unless explicitly asked.

## Architecture boundaries
- `controller.py` owns orchestration, session retrieval/persistence, and macro-stage transitions.
- Stage modules own local FSM and stage-local logic.
- `engine.py` owns LLM interaction, prompt construction, parsing, and validation support.
- YAML owns prompt/config content only and is not the FSM owner.
- The session is the single source of truth. Do not introduce stage handoff artifacts.
- Keep the PoC simple. Avoid unnecessary abstractions and wrapper classes.

## Macro-stages and local states
Use `docs/architecture_v3_1.md` as the source of truth for:
- macro-stage order
- local states
- state types (`evaluative`, `production`, `waiting`, `terminal`)
- controller / stage / engine responsibilities
- session field roles

Do not duplicate the full FSM in this file.

## Naming rules
Use these names unless the current code already uses a working equivalent that must be preserved:
- macro-stage field: `stage`
- local state field: `state`
- user input field: `user_message`
- LLM/internal output: `evaluation_message`
- user-facing LLM output: `coach_message`
- debug/trace field: `debug_message`
- canonical session object: `session`

## V3.1 execution rules
- `evaluation_message` is internal assessment only. Evaluation does not generate user-facing text.
- `coach_message` is the only generated user-facing text, including synthesis, pathways, and closure.
- A state may be one of: `evaluative`, `production`, `waiting`, `terminal`.
- A transition that requires judgement must go through evaluation. Deterministic transitions do not.
- `user_message` may contain normal user text or UI-injected control / selection flags.
- Later stages read needed context directly from session fields and chat history.

## Contracts and change policy
- Do not duplicate information in models unless there is a clear boundary reason.
- For internal in-process calls, prefer plain parameters and returns over extra wrapper classes when possible.
- Do not break current API routes unless explicitly required.
- Keep frontend, backend, smoke tests, and deployment scripts aligned.
- If the scaffold already uses a working helper or reply shape, preserve it unless there is a clear benefit to changing it.

## Files usually relevant
- `backend/api.py`
- `backend/controller.py`
- `backend/models.py`
- `backend/enums.py`
- `backend/state_store.py`
- `backend/engine.py`
- `backend/stages/*.py`
- `frontend/app.py`
- `smoke_test.py`
- `docs/architecture_v3.md`
- `docs/architecture_v3_1.md`

## Validation
Before considering a task complete:
- run or update `smoke_test.py`
- verify imports and contracts remain consistent
- verify local FastAPI + Streamlit flow if the task touches contracts
- keep debug and tracing explicit so failures are easy to diagnose

## Deployment
The repo already has deployment helpers. Do not change these unless necessary:
- `deploy.sh`
- `check_remote.sh`
- `run_local.sh`

## Done when
A task is done only when:
- the requested change is implemented
- smoke or regression checks are updated if needed
- debug and tracing remain useful
- no unnecessary unrelated refactors were introduced
