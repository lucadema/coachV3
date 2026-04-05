# Coach V3 Architecture

## Purpose

This document captures the **V3 design intent** agreed during the design session. It is intended as a handoff guide for implementation work.

Important rule:

- **Current source files are the source of truth for exact names, imports, and concrete contracts.**
- This document is the **architectural intent and design rationale**.
- If this document and the current code differ on a minor naming/detail point, **prefer the current code**, then preserve the architectural rules defined here.

---

## Source of truth hierarchy

When implementing changes, use this order:

1. `AGENTS.md`
2. `docs/architecture_v3.md` (this document)
3. Current code files in the repo
4. Existing tests and smoke tests

Practical interpretation:

- **Architecture and separation of concerns** come from this document.
- **Exact model names and signatures** should be checked against the current files before editing.
- If a model or route name has drifted since this document was written, keep the current working code consistent and update tests accordingly.

---

## Design goals for V3

V3 is a simplification and cleanup of the earlier PoC versions.

Key goals:

- Make the orchestration clearer and more deterministic.
- Keep macro-stage control separate from stage-local logic.
- Keep the LLM interaction layer separate from orchestration.
- Avoid duplicating state transition logic across code and YAML.
- Keep YAML for prompt/config assets, not as the canonical FSM.
- Preserve a scaffold that is easy to extend incrementally.

This is still a **PoC**, so the priority is:

- clarity
- safety
- clean structure
- low-friction iteration

not premature optimization or scaling complexity.

---

## Core architecture

### High-level split

The V3 backend is organized around four concerns:

1. **Controller**
2. **Stage modules**
3. **Engine**
4. **YAML configuration/prompt assets**

### Controller responsibility

`controller.py` is:

- the **macro-stage router**
- the **session orchestrator**
- responsible for the **end-to-end cognitive process**

It should:

- know the current **macro-stage** only
- load and persist session state
- invoke the correct stage module
- apply macro-stage transitions
- set the correct initial local state when macro-stage changes

It should **not**:

- own stage-local FSM logic
- own detailed LLM prompt composition
- perform hidden stage-specific reasoning that belongs in stage modules

### Stage module responsibility

Stage modules are:

- `classification.py`
- `coaching.py`
- `synthesis.py`
- `pathways.py`
- `closure.py`

Each stage module:

- is responsible only for its own stage
- owns its own **local FSM**
- manages local transitions and local decision rules
- receives the current in-memory session from controller
- updates session fields relevant to the stage
- returns an updated session plus optional next macro-stage

Stage modules should **not**:

- fetch sessions from storage directly
- own cross-stage orchestration
- redefine global architecture concerns

### Engine responsibility

`engine.py` or equivalent is responsible for:

- handling interaction with the LLM
- constructing prompts by combining:
  - chat history
  - stage-specific YAML context
  - local-state-specific YAML context
  - any other turn-specific context
- performing turn-specific parsing/checks/validation
- returning useful evaluation and debug outputs

The engine should **not**:

- own macro-stage transitions
- own the canonical FSM
- access persistence/storage directly

### YAML responsibility

YAML files own:

- prompts
- criteria
- instructions
- text fragments
- optional state/stage prompt metadata

YAML should **not** own:

- the canonical FSM
- actual state transition rules
- controller logic

A prompt may use state context, but YAML is not the source of truth for the FSM.

---

## Macro-stages and local states

Naming convention:

- `macro_stage` is named simply **`stage`** in code and contracts.
- Local stage state is named **`state`**.

### Macro-stage order

There are **no backward macro-stage transitions**.

Macro-stage flow:

`classification -> coaching -> synthesis -> pathways -> closure`

### Stage definitions

#### 1. Classification

Purpose:

- determine whether the opening input can enter the process

Local states:

- `evaluating`
- `ambiguous`
- `completed`
- `cancelled`

Interpretation:

- `evaluating`: the opening input is being assessed
- `ambiguous`: clarification is required before the stage can resolve
- `completed`: accepted; process may move to Coaching
- `cancelled`: rejected; session terminates

Local transitions:

- `evaluating -> ambiguous`
- `evaluating -> completed`
- `evaluating -> cancelled`
- `ambiguous -> evaluating`
- `ambiguous -> cancelled`

Important rule:

- **bounded ambiguity**: if already in `classification.state == "ambiguous"` and clarification still does not resolve the issue, reject/cancel rather than looping indefinitely.

#### 2. Coaching

Purpose:

- guide the user until the problem is sufficiently understood

Local states:

- `guiding`
- `completed`
- `cancelled`

Local transitions:

- `guiding -> guiding`
- `guiding -> completed`
- `guiding -> cancelled`

Design note:

- internal micro-steps such as evaluation / selecting the next question remain implicit inside `coaching.py`; they do not need to be explicit public states.

#### 3. Synthesis

Purpose:

- formulate and validate the problem synthesis

Local states:

- `preparing`
- `validating`
- `refining`
- `completed`
- `cancelled`

Local transitions:

- `preparing -> validating`
- `preparing -> cancelled`
- `validating -> completed`
- `validating -> refining`
- `validating -> cancelled`
- `refining -> validating`
- `refining -> cancelled`

Design note:

- challenges to the synthesis are handled inside Synthesis through `refining`, not by returning to Coaching.

#### 4. Pathways

Purpose:

- generate and present possible resolution pathways

Local states:

- `preparing`
- `presenting`
- `completed`
- `cancelled`

Local transitions:

- `preparing -> presenting`
- `preparing -> cancelled`
- `presenting -> completed`
- `presenting -> cancelled`

#### 5. Closure

Purpose:

- conclude the session

Local states:

- `preparing`
- `completed`

Local transitions:

- `preparing -> completed`

### Terminal states

Terminal session outcomes are represented by:

- `classification.cancelled`
- `coaching.cancelled`
- `synthesis.cancelled`
- `pathways.cancelled`
- `closure.completed`

Additionally, session lifecycle flags exist on the session object:

- `cancelled`
- `completed`

---

## Initial local state per macro-stage

When the controller moves into a macro-stage, it must set the correct initial local state:

- `classification -> evaluating`
- `coaching -> guiding`
- `synthesis -> preparing`
- `pathways -> preparing`
- `closure -> preparing`

This rule belongs to controller/orchestration logic.

---

## Naming conventions locked for V3

Use these names consistently:

- macro-stage field name: `stage`
- user input: `user_message`
- LLM response for evaluation/internal reasoning: `evaluation_message`
- LLM response intended for the user: `coach_message`
- debug/trace text: `debug_message`
- session object name: `session`

API naming preference:

- use `Init` rather than `Initialise`
- use `Reply` rather than `Response`
- use `Msg` rather than `Message`

Note:

- existing working routes/files may still contain older names in places; current code remains source of truth for exact symbols during implementation.

---

## Enums locked for V3

### Global enum

- `Stage`

### Local state enums

- `ClassificationState`
- `CoachingState`
- `SynthesisState`
- `PathwaysState`
- `ClosureState`

### Chat enum

- `ChatRole`

Design note:

- `session.state` remains a **plain string field** in the session object.
- Local state enums exist to constrain code paths and avoid typos, but session serialization can still store the string value.

---

## Core models locked for V3

### Internal models

- `Session`
- `ChatMessage`
- `StageCmd`
- `StageReply`

### `Session`

The session object is the core internal working object.

Its agreed fields are:

- `session_id`
- `stage`
- `state`
- `user_message`
- `evaluation_message`
- `coach_message`
- `debug_message`
- `chat_history`
- `stage_context`
- `cancelled`
- `completed`
- `created_at`
- `updated_at`

Design rules:

- `stage` is owned by controller
- `state` is owned by the current stage module
- `stage_context` is owned by the active stage module
- visible conversation history is stored in `chat_history`
- `debug_message` stays a **plain string** for now
- `session.state` remains a **plain string** for now

### `ChatMessage`

`chat_history` should use typed chat messages rather than raw dicts.

Minimum shape:

- `role: ChatRole`
- `message: str`

### `StageCmd`

The controller passes a stage module a minimal wrapped command:

- `session: Session`

### `StageReply`

A stage module returns:

- `session: Session`
- `next_stage: Stage | None`

Interpretation:

- `next_stage = None`: remain in current macro-stage
- `next_stage = some Stage`: controller advances to that macro-stage
- cancellation/completion are reflected on the session object itself

---

## API contracts

There are two logical boundaries:

1. frontend `app.py <-> api.py`
2. `api.py <-> controller.py`

The exact class names in code should be verified against current files, but the intended split is:

### Frontend/API boundary

Use a reduced frontend-safe session view rather than exposing full internal session state.

Suggested models discussed:

- `SessionView`
- `InitReply`
- `UserMsg`
- `UserMsgReply`
- `DebugReply`

Principle:

- frontend should receive only the minimum required to render state and continue the session
- internal fields such as large stage context or internal details should stay backend-side

### API/controller boundary

Suggested models discussed:

- `InitCmd`
- `InitReply`
- `UserMsgCmd`
- `UserMsgReply`
- `DebugCmd`
- `DebugReply`

Principle:

- `api.py` translates HTTP-level contracts into controller-level commands/results
- `controller.py` works with the full internal session object

Implementation note:

- current code files should be checked for the exact names currently in use
- this document captures the intended separation, not a mandate to rename working code unnecessarily

---

## Session loading and persistence

Locked decision:

- session persistence should be implemented in a simple `state_store.py`

Design rule:

- `controller.py` owns session retrieval and persistence
- stage modules do **not** fetch session data themselves
- `engine.py` does **not** fetch session data itself
- controller loads the full session once, then passes the in-memory object to stages and engine as needed

This is important because:

- `engine.py` is likely the component that most needs `chat_history` for prompt construction
- but the engine should not own persistence concerns
- backend design should stay simple and safe for the PoC

Practical flow:

- `app.py -> api.py`: pass `session_id` and `user_message`
- `api.py -> controller.py`: pass `session_id` and `user_message`
- `controller.py`: load full `session`
- `controller.py -> stage module`: pass loaded in-memory `session`
- `controller.py -> engine.py`: pass loaded in-memory `session`
- `controller.py`: persist updated session

This avoids:

- repeated loading by stage modules
- repeated loading by engine
- repeated transfer of large chat history across the HTTP boundary

---

## Error handling

Locked decision:

- API errors remain normal HTTP errors for now

No formal API error reply model is required yet.

---

## Debugging and traceability

V3 should keep debugging explicit and easy to inspect.

Rules:

- always set meaningful `debug_message`
- keep `evaluation_message` useful and inspectable
- make parsing failures and fallback behavior visible in `debug_message`
- prefer clear and explicit trace text over hidden magic

Locked simplification:

- `debug_message` remains a plain string for now, not a structured object

---

## Current implementation scaffold assumptions

The initial backend scaffold includes these components:

- `backend/models.py`
- `backend/enums.py`
- `backend/state_store.py`
- `backend/controller.py`
- `backend/engine.py`
- `backend/stages/` with stage modules
- `backend/api.py`

Current scaffold intent:

- stage modules may still be placeholders except for the slice currently being implemented
- route names and working frontend/deployment scripts should be preserved unless the task explicitly requires change

---

## First functional slice to implement

The agreed first real functional slice for V3 is:

- make **Classification** real
- keep Coaching, Synthesis, Pathways, and Closure as placeholders

Classification must support:

- valid
- ambiguous
- invalid

Additional rule:

- bounded ambiguity

Controller must set initial local states correctly when macro-stage changes:

- classification -> evaluating
- coaching -> guiding
- synthesis -> preparing
- pathways -> preparing
- closure -> preparing

Engine requirements for the first slice:

- implement the minimum classification support in `backend/engine.py`
- use YAML-backed prompt/config support for Classification
- preserve explicit debug and evaluation outputs

Testing requirements for the first slice:

- valid classification
- ambiguous classification
- invalid classification
- bounded ambiguity
- baseline regression checks

---

## Design philosophy for Codex work

When making changes:

- preserve the current scaffold unless the task explicitly requires changes
- prefer the smallest clean solution
- do not redesign working contracts unnecessarily
- keep the current frontend and deployment working
- identify contract mismatches before editing
- make incremental, testable improvements

---

## Practical guidance for Codex

Before editing:

1. read `AGENTS.md`
2. read this architecture document
3. inspect the relevant current files
4. identify any contract drift between document and code
5. treat current code as source of truth for exact names/signatures
6. implement the smallest safe change

When in doubt:

- preserve architecture
- preserve working routes/contracts unless task requires change
- prefer explicit debug output
- keep local FSM logic inside stage modules
- keep macro-stage transitions in controller
- keep prompt/config assets in YAML

