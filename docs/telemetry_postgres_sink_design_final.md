# Telemetry PostgreSQL Sink Design

## Purpose

This document defines the next telemetry implementation step for CoachV3 / Glimpse.

The console telemetry seam already exists. The goal now is to add a PostgreSQL persistence sink behind the same telemetry service API, without changing the rest of the backend behaviour.

Telemetry must remain a side effect. It must never alter coaching behaviour, session state transitions, prompts, LLM outputs, response timing expectations, or error handling in the main application flow.

## Scope

This step adds:

1. A PostgreSQL telemetry sink.
2. A SQL schema file that creates the required telemetry tables.
3. Environment-variable based sink selection.
4. Local Postgres support using the local database `glimpsedb`.
5. Render Postgres support using the Render internal database URL.
6. Safe failure handling: telemetry errors are logged but never propagated.

This step does not add:

- dashboard UI
- Excel export
- PostHog integration
- schema auto-creation at backend startup
- migrations framework
- raw transcript storage
- raw prompt storage
- raw user message storage

## Architecture

The existing backend should continue to call the telemetry service through simple public functions.

```text
backend/controller.py
backend/engine.py
        ↓
backend/telemetry/service.py
        ↓
selected sink
        ↓
ConsoleTelemetrySink / NoopTelemetrySink / PostgresTelemetrySink
```

The persistence mechanism must be isolated behind the sink interface. Later, PostHog or another sink should be added by changing the sink implementation and environment configuration, not by changing controller or engine logic.

## Environment variables

Use these variables:

```env
TELEMETRY_ENABLED=true
TELEMETRY_SINK=postgres
TELEMETRY_DATABASE_URL=postgresql://lucadematteis@localhost:5432/glimpsedb
```

For local console telemetry:

```env
TELEMETRY_ENABLED=true
TELEMETRY_SINK=console
```

For disabled telemetry:

```env
TELEMETRY_ENABLED=false
TELEMETRY_SINK=noop
```

For Render:

```env
TELEMETRY_ENABLED=true
TELEMETRY_SINK=postgres
TELEMETRY_DATABASE_URL=<Render Internal Database URL>
```

Do not introduce `TELEMETRY_AUTO_CREATE_SCHEMA`. The backend should assume the schema already exists. Schema creation is handled by the explicit SQL file in `sql/telemetry_schema.sql`.

## Tables

There are two tables:

1. `coach_sessions` — one row per user session, updated over the life of the session.
2. `coach_llm_usage` — one row per LLM call.

The app's session identifier should be stored as `app_session_id`. This avoids coupling the runtime session ID to the database auto-increment primary key.

## Session telemetry model

A session row is created when the user submits the initial problem statement and presses continue. A row should not be created merely because the frontend has initialised a blank session.

The row is then updated as the session progresses.

The session record should capture:

- start time
- latest interaction time
- close time, where known
- status
- current stage
- optional `session_label`
- turn count
- synthesis generated flag
- pathways generated flag
- PDF downloaded flag
- feedback answers
- feedback dropdown values
- feedback payload, if useful

The duration does not need to be stored. It can be derived from `last_interaction_at - started_at`.

`session_label` comes from the frontend URL query parameter `session_label` via
generic launch context metadata. It is not frontend telemetry, authentication,
or user identity. The backend sanitises it and stores it only on
`coach_sessions.session_label`, never on `coach_llm_usage`. It can be used to
filter out test, demo, or internal sessions.

## LLM telemetry model

Each LLM call should create one row in `coach_llm_usage`.

The implementation should use a single operation label rather than separate fields for stage, state, call type and call purpose.

Recommended operation label format:

```text
<stage-config-name>.<state-name>.<interaction-type>
```

Examples:

```text
classification.evaluating.evaluation
coaching.guiding.coaching
synthesis.preparing.coaching
pathways.preparing.coaching
```

This should be generated inside `backend/engine.py` because `_run_interaction(...)` already has access to `stage_yaml_path`, `state_name`, and `interaction_type`.

## Token usage

Capture token usage from the LLM response where available.

At minimum:

- input tokens
- output tokens
- total tokens

Also capture optional token details if available:

- cached input tokens
- reasoning tokens

The code must be robust to SDK response shape differences. If a field is absent, store `NULL` rather than failing.

## Safety and privacy

Do not store:

- raw user messages
- full conversation history
- raw prompts
- raw model outputs
- synthesis text
- pathway text
- names, emails, or company names unless explicitly introduced later through a conscious privacy decision

Telemetry should store metadata only.

## Failure handling

Telemetry must never break the app.

Every public telemetry function and every sink operation must catch exceptions internally.

If the PostgreSQL database is down, missing, misconfigured, slow, or missing tables:

- the main backend flow must continue
- the error should be logged to console/logger
- no exception should propagate into controller, engine, FastAPI routes, or frontend responses

## Dependencies

Use `psycopg[binary]` unless the project already has a PostgreSQL client dependency.

Add it to the backend dependency file used by the project, for example `requirements.txt`.

## Local setup

The local database name is:

```text
glimpsedb
```

Suggested local connection string:

```env
TELEMETRY_DATABASE_URL=postgresql://lucadematteis@localhost:5432/glimpsedb
```

Create tables manually using:

```bash
psql "postgresql://lucadematteis@localhost:5432/glimpsedb" -f sql/telemetry_schema.sql
```

Then run the backend with:

```env
TELEMETRY_ENABLED=true
TELEMETRY_SINK=postgres
TELEMETRY_DATABASE_URL=postgresql://lucadematteis@localhost:5432/glimpsedb
```

Inspect data with:

```bash
psql "postgresql://lucadematteis@localhost:5432/glimpsedb"
```

Then:

```sql
SELECT * FROM coach_sessions ORDER BY id DESC LIMIT 5;
SELECT * FROM coach_llm_usage ORDER BY id DESC LIMIT 10;
```

## Acceptance criteria

1. With `TELEMETRY_SINK=console`, existing console telemetry still works.
2. With `TELEMETRY_SINK=postgres`, telemetry writes to local Postgres.
3. With `TELEMETRY_ENABLED=false`, no telemetry is emitted.
4. If `TELEMETRY_DATABASE_URL` is missing or invalid, the app still works.
5. If tables are missing, the app still works and logs a safe telemetry error.
6. No raw user messages, full prompts, conversation history, synthesis text, or pathway text are stored.
7. The existing coaching flow still works normally.
8. Existing tests pass.
