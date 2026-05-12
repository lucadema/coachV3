# CoachV3 telemetry extension — console-first implementation

## Purpose

Add a small telemetry seam to the backend without introducing a database, PostHog, or any external persistence yet.

This first step records telemetry to the console only. The purpose is to prove the instrumentation points safely before adding PostgreSQL persistence later.

## Design principle

Telemetry is a side effect. It must never affect the normal coaching flow.

If telemetry fails, the backend should continue exactly as if telemetry did not exist.

## Scope for this step

Implement two telemetry types:

1. **Session telemetry**
   - One conceptual record per user session.
   - For now this is emitted as console messages rather than persisted.
   - Later this can become an upsert into a `coach_sessions` table.

2. **LLM telemetry**
   - One record per LLM call.
   - For now this is emitted as console messages rather than persisted.
   - Later this can become an insert into a `coach_llm_usage` table.

No database code should be added in this step.

## Existing code context

The current backend already has two good insertion areas:

- `backend/controller.py` owns session loading, persistence, macro-stage routing, and user turn handling.
- `backend/engine.py` owns prompt assembly and the LLM boundary.

Therefore:

- session telemetry should be called from `controller.py`, especially `handle_user_msg(...)`.
- LLM telemetry should be called from `engine.py`, around `_call_llm(...)`.

## Proposed module structure

Create a new package:

```text
backend/telemetry/
  __init__.py
  service.py
  sinks.py
```

Optional if useful:

```text
backend/telemetry/models.py
```

Keep it small. Do not overengineer.

## Storage abstraction

Use a simple sink abstraction so the persistence layer can be swapped later.

For this step, implement:

```text
ConsoleTelemetrySink
NoopTelemetrySink
```

Later, the same service layer can route to:

```text
PostgresTelemetrySink
PostHogTelemetrySink
MultiTelemetrySink
```

The rest of the backend should not care which sink is active.

## Configuration

Use environment variables:

```text
TELEMETRY_ENABLED=true
TELEMETRY_SINK=console
```

Suggested behaviour:

- If `TELEMETRY_ENABLED` is missing, default to `true` for this console-first phase.
- If `TELEMETRY_ENABLED=false`, use `NoopTelemetrySink`.
- If `TELEMETRY_SINK` is missing, default to `console`.

This allows the console implementation to work both locally and on Render.

## Console output format

Emit one-line JSON payloads with a fixed prefix so they are easy to find in logs.

Example:

```text
TELEMETRY {"event":"session_started","session_id":"...","stage":"classification","state":"evaluating","turns_count":0,"timestamp":"2026-05-12T10:00:00Z"}
```

Use UTC ISO timestamps.

Do not log raw user messages, full prompts, full LLM outputs, problem statements, synthesis text, or pathway text in telemetry.

## Session telemetry API

Expose safe functions from `backend.telemetry.service` and re-export them from `backend.telemetry.__init__`.

Suggested functions:

```python
def record_session_started(
    *,
    session_id: str,
    stage: str | None,
    state: str | None,
    turns_count: int | None,
) -> None: ...


def record_session_updated(
    *,
    session_id: str,
    stage: str | None,
    state: str | None,
    turns_count: int | None,
    synthesis_generated: bool | None = None,
    pathways_generated: bool | None = None,
    pdf_downloaded: bool | None = None,
    status: str | None = None,
) -> None: ...


def record_session_closed(
    *,
    session_id: str,
    stage: str | None,
    state: str | None,
    turns_count: int | None,
    status: str = "completed",
) -> None: ...


def record_feedback_submitted(
    *,
    session_id: str,
    answer_1: bool | None = None,
    answer_2: bool | None = None,
    dropdown_values: list[str] | None = None,
    payload: dict | None = None,
) -> None: ...
```

For this first step, feedback and PDF telemetry may only be wired if the corresponding endpoints are already obvious in the backend. Do not refactor UI or API flow just to add them.

## LLM telemetry API

Expose:

```python
def record_llm_call(
    *,
    session_id: str | None,
    llm_operation: str,
    provider: str = "openai",
    model: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    total_tokens: int | None = None,
    cached_input_tokens: int | None = None,
    reasoning_tokens: int | None = None,
    success: bool = True,
    latency_ms: int | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
    metadata: dict | None = None,
) -> None: ...
```

Use a single field, `llm_operation`, rather than separate `stage`, `state`, `call_type`, and `call_purpose`.

Generate it inside `engine.py` as:

```python
llm_operation = f"{Path(stage_yaml_path).stem}.{state_name}.{interaction_type}"
```

Example values:

```text
classification.evaluating.evaluation
coaching.guiding.evaluation
coaching.guiding.coaching
synthesis.preparing.coaching
pathways.preparing.coaching
```

## LLM usage extraction

The current backend uses the OpenAI Responses API call:

```python
response = client.responses.create(model=model, input=prompt)
```

After the response returns, read `response.usage` if available.

Support both naming styles defensively:

```python
input_tokens = usage.input_tokens or usage.prompt_tokens
output_tokens = usage.output_tokens or usage.completion_tokens
total_tokens = usage.total_tokens
```

Also attempt optional fields where present:

```python
cached_input_tokens
reasoning_tokens
```

These fields may be unavailable and should remain `None`.

## Minimal insertion points

### `controller.py`

In `handle_user_msg(...)`:

1. After loading the session and before incrementing the turn count, if this is the first user message, call `record_session_started(...)`.
2. After `_run_stage_loop(...)` and after any assistant message is appended, call `record_session_updated(...)`.
3. Do not change session behaviour, state transitions, or persistence logic.

Pass only safe metadata:

```text
session_id
stage
state
turn_count
stage_turn_count if useful
status if inferable
```

### `engine.py`

Add an optional keyword-only parameter to `evaluate(...)` and `coach(...)`:

```python
telemetry_session_id: str | None = None
```

Pass this through `_run_interaction(...)` into `_call_llm(...)` as part of a small telemetry context.

Do not require callers to pass extra stage/state/call-type metadata. The engine already knows enough to derive `llm_operation`.

## Required safety behaviour

Every public telemetry function must catch all exceptions and return `None`.

Telemetry must not:

- raise exceptions into the app flow
- block user interactions
- alter session state
- alter LLM prompts or outputs
- store or print raw user content
- introduce database or network calls in this first step

## Expected result

After implementation, running a local or Render session should show console lines such as:

```text
TELEMETRY {"event":"session_started",...}
TELEMETRY {"event":"session_updated",...}
TELEMETRY {"event":"llm_call",...}
```

If the LLM is disabled, session telemetry should still print. LLM telemetry may either be absent or may record a skipped/disabled status, as long as the choice is documented and consistent.

## Later migration path

The next step can add:

```text
PostgresTelemetrySink
```

without changing the controller or engine instrumentation calls.

That sink can map:

- session telemetry to `coach_sessions` upserts
- LLM telemetry to `coach_llm_usage` inserts

