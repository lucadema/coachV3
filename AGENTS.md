# AGENTS.md

## Project
Coach V3 is a Python PoC with:
- FastAPI backend in `backend/`
- Streamlit frontend in `frontend/`
- stage modules in `backend/stages/`
- smoke regression script in `smoke_test.py`

## Working style
- Plan first for any non-trivial task before editing code.
- Read the relevant files before changing anything.
- Preserve the current working scaffold unless the task explicitly requires a contract change.
- Prefer the smallest clean change that satisfies the task.
- Do not redesign architecture unless explicitly asked.

## Architecture rules
- `controller.py` owns orchestration, session retrieval/persistence, and macro-stage transitions.
- Stage modules own local FSM and stage-local logic.
- `engine.py` owns LLM interaction, prompt construction, parsing, and validation support.
- YAML owns prompt/config content only and is not the FSM owner.
- Keep the PoC simple. Avoid unnecessary abstractions and wrapper classes.

## Naming rules
- Macro-stage field name: `stage`
- Local state field name: `state`
- User input field: `user_message`
- LLM outputs: `evaluation_message`, `coach_message`
- Debug/trace field: `debug_message`
- Canonical session object: `session`

## Contracts and safety
- Do not duplicate information in models unless there is a clear boundary reason.
- For internal in-process calls, prefer plain parameters/returns over wrapper classes when possible.
- Do not break current API routes unless explicitly required.
- Keep frontend, backend, smoke tests, and deployment scripts aligned.

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

## Validation
Before considering a task complete:
- run or update `smoke_test.py`
- verify imports and contracts remain consistent
- verify local FastAPI + Streamlit flow if the task touches contracts
- keep debug/tracing explicit so failures are easy to diagnose

## Deployment
The repo already has deployment helpers.
Do not change these unless necessary:
- `deploy.sh`
- `check_remote.sh`
- `run_local.sh`

## Done when
A task is done only when:
- the requested change is implemented
- smoke/regression checks are updated if needed
- debug/tracing remains useful
- no unnecessary unrelated refactors were introduced
