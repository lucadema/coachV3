# Session Label Launch Context Design

## Purpose

Add an optional `session_label` value that can be passed in the application URL and stored with backend session telemetry.

Example URL:

```text
https://<app-url>/?session_label=luca
```

The purpose is to support filtering of internal, demo, test, or named participant sessions in telemetry exports and database queries.

This is not authentication and not user identity. It is a lightweight session attribution label.

## Design principle

The React frontend should remain telemetry-agnostic.

The frontend should not know about:

- telemetry tables
- Postgres
- telemetry sinks
- analytics implementation
- `coach_sessions`
- `coach_llm_usage`

The frontend should only handle this as generic launch context:

```text
URL parameter -> launch context -> normal backend request metadata
```

The backend remains the owner of telemetry.

This field is stored only in `coach_sessions.session_label`. It is not added to
`coach_llm_usage`, LLM metadata, prompts, debug traces, or any frontend
analytics library.

## Recommended naming

Use only:

```text
session_label
```

Do not use `user` as the canonical name because it implies identity or authentication. The label may contain values such as:

```text
luca
test
demo
internal
client_preview
sharon
```

## Data flow

```text
URL query parameter
    ?session_label=luca
        ↓
Frontend launch context helper
        ↓
Existing backend API request payload
        ↓
Backend client context sanitisation
        ↓
Session metadata / telemetry start/update call
        ↓
coach_sessions.session_label
```

## Frontend change

Add a small isolated helper such as:

```text
glimpse/src/utils/launchContext.ts
```

The helper reads the URL query string and returns a safe context object:

```ts
export type LaunchContext = {
  sessionLabel?: string;
};
```

The frontend API client should include this value as optional metadata in normal backend requests, for example:

```json
{
  "message": "...",
  "client_context": {
    "session_label": "luca"
  }
}
```

or, if the existing frontend/backend naming style is camelCase:

```json
{
  "message": "...",
  "clientContext": {
    "sessionLabel": "luca"
  }
}
```

Codex should inspect the existing API request models and use the existing project naming convention. The backend should accept the chosen form robustly.

## Backend change

Add a small backend helper such as:

```text
backend/client_context.py
```

Responsibilities:

- accept optional client context from API requests
- extract `session_label`
- sanitise it
- return `None` if missing or invalid
- never raise for malformed input

The backend must sanitise again even if the frontend sanitises first.

## Sanitisation rules

Recommended rules:

- value is optional
- trim whitespace
- lowercase for consistency
- maximum 64 characters
- allow only:
  - letters
  - numbers
  - underscore `_`
  - hyphen `-`
  - dot `.`
- reject or clean anything else
- never accept email addresses or long free text as labels

A conservative regular expression is:

```text
^[a-z0-9_.-]{1,64}$
```

If the value does not pass validation, store `NULL` and continue normally.

## Database change

Add a nullable column to `coach_sessions`:

```sql
ALTER TABLE coach_sessions
ADD COLUMN IF NOT EXISTS session_label TEXT NULL;
```

Update `sql/telemetry_schema.sql` so new databases include:

```sql
session_label TEXT NULL,
```

If the codebase has any automatic `CREATE TABLE IF NOT EXISTS coach_sessions` SQL inside the Postgres telemetry sink, update that SQL too.

If auto-create exists, also make sure the sink can safely add the missing column to an existing table with:

```sql
ALTER TABLE coach_sessions
ADD COLUMN IF NOT EXISTS session_label TEXT NULL;
```

If auto-create does not exist, do not introduce it just for this change unless the current implementation already expects that behaviour.

## Telemetry behaviour

The session row should store the label when the telemetry session row is first created.

If the session already exists and a valid `session_label` becomes available later, the telemetry layer may update the row only if `session_label` is currently `NULL`.

Do not overwrite a non-null existing `session_label` during the same session.

## Failure behaviour

This change must never break the app.

If URL parsing fails, ignore the label.
If request metadata is missing, continue normally.
If backend sanitisation rejects the value, continue normally.
If telemetry storage fails, continue normally.

## Privacy note

This is a session label, not an identity field. Do not encourage use of full names, email addresses, company names, or sensitive identifiers.

## Example SQL query

```sql
SELECT
    session_label,
    COUNT(*) AS sessions,
    COUNT(*) FILTER (WHERE synthesis_generated) AS synthesis_sessions,
    COUNT(*) FILTER (WHERE pathways_generated) AS pathway_sessions,
    COUNT(*) FILTER (WHERE pdf_downloaded) AS pdf_downloads
FROM coach_sessions
GROUP BY session_label
ORDER BY sessions DESC;
```
