# Admin Telemetry Export Design

## Purpose

Add a backend-only admin endpoint that exports telemetry data from PostgreSQL into a downloadable Excel workbook.

This is an administration capability, not part of the user-facing coaching flow. It must not require any React frontend changes and must not alter how telemetry is recorded.

The current telemetry model has two responsibilities:

1. **Session telemetry**: one row per user session, updated over the life of the session.
2. **LLM telemetry**: one row per LLM call.

The export endpoint should read these tables and produce a file that non-technical team members can open in Excel.

---

## Design Principles

### 1. Backend-only

No frontend changes are required.

The export is accessed manually through a URL such as:

```text
GET /admin/telemetry/export.xlsx?token=<secret>
```

This keeps the React app telemetry-agnostic and avoids adding admin concerns to the user journey.

### 2. Isolated from normal app flow

The export route must not affect:

- coaching sessions
- stage transitions
- LLM calls
- telemetry recording
- PDF generation
- frontend behaviour

The route is read-only from the database.

### 3. Protected by a simple token

For the PoC, protect the endpoint with a shared secret stored in an environment variable:

```env
TELEMETRY_EXPORT_TOKEN=<long-random-secret>
```

The route should require:

```text
?token=<same-secret>
```

If the token is missing or incorrect, return `403 Forbidden`.

Do not log the token.

### 4. Use the same database configuration as telemetry

The export should read from the database configured by:

```env
TELEMETRY_DATABASE_URL=...
```

If the variable is missing or the database is unreachable, return a clear HTTP error from the export endpoint only. This should not affect normal app operation.

### 5. Do not export raw sensitive conversation content

The export should include telemetry metadata only.

Do not export:

- raw user messages
- raw prompts
- full conversation history
- raw synthesis text
- raw pathway text

The current telemetry tables should already avoid storing those fields.

---

## Proposed backend modules

Add:

```text
backend/admin/
  __init__.py
  telemetry_export_routes.py

backend/telemetry/
  export.py
```

Implemented route mount:

```text
backend/api.py includes backend.admin.telemetry_export_routes.router
```

The export implementation is read-only and does not create, migrate, or update
telemetry tables.

### `backend/admin/telemetry_export_routes.py`

Responsibilities:

- define the FastAPI route
- validate the token
- call the export builder
- return the workbook as a file response or streaming response
- avoid exposing database details to the client

### `backend/telemetry/export.py`

Responsibilities:

- connect to Postgres
- run read-only queries
- build an Excel workbook
- return workbook bytes
- keep SQL and workbook construction isolated from API route code

---

## Endpoint

```text
GET /admin/telemetry/export.xlsx?token=<secret>
```

Recommended response headers:

```text
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="aether-glimpse-telemetry-YYYYMMDD-HHMMSS.xlsx"
```

---

## Workbook structure

The workbook should contain three sheets.

### Sheet 1: `Sessions`

Source: `coach_sessions`

Recommended columns:

```text
id
app_session_id
session_label
started_at
last_interaction_at
closed_at
status
current_stage
turns_count
synthesis_generated
pathways_generated
pdf_downloaded
feedback_submitted_at
feedback_answer_1
feedback_answer_2
feedback_dropdown_values
feedback_payload
last_error
duration_seconds
created_at
updated_at
```

Use `COALESCE(closed_at, last_interaction_at)` to calculate duration.

Example duration expression:

```sql
EXTRACT(EPOCH FROM (COALESCE(closed_at, last_interaction_at) - started_at)) AS duration_seconds
```

### Sheet 2: `LLM Usage`

Source: `coach_llm_usage`

Recommended columns:

```text
id
app_session_id
created_at
llm_operation
provider
model
input_tokens
output_tokens
total_tokens
cached_input_tokens
reasoning_tokens
success
latency_ms
error_type
error_message
metadata
```

### Sheet 3: `Session Token Summary`

Source: join between `coach_sessions` and `coach_llm_usage`

Recommended columns:

```text
session_id
app_session_id
session_label
started_at
last_interaction_at
status
current_stage
turns_count
synthesis_generated
pathways_generated
pdf_downloaded
llm_calls
input_tokens_total
output_tokens_total
total_tokens_total
cached_input_tokens_total
reasoning_tokens_total
successful_llm_calls
failed_llm_calls
duration_seconds
```

Suggested query shape:

```sql
SELECT
    s.id AS session_id,
    s.app_session_id,
    s.session_label,
    s.started_at,
    s.last_interaction_at,
    s.status,
    s.current_stage,
    s.turns_count,
    s.synthesis_generated,
    s.pathways_generated,
    s.pdf_downloaded,
    COUNT(u.id) AS llm_calls,
    COALESCE(SUM(u.input_tokens), 0) AS input_tokens_total,
    COALESCE(SUM(u.output_tokens), 0) AS output_tokens_total,
    COALESCE(SUM(u.total_tokens), 0) AS total_tokens_total,
    COALESCE(SUM(u.cached_input_tokens), 0) AS cached_input_tokens_total,
    COALESCE(SUM(u.reasoning_tokens), 0) AS reasoning_tokens_total,
    COUNT(u.id) FILTER (WHERE u.success = TRUE) AS successful_llm_calls,
    COUNT(u.id) FILTER (WHERE u.success = FALSE) AS failed_llm_calls,
    EXTRACT(EPOCH FROM (COALESCE(s.closed_at, s.last_interaction_at) - s.started_at)) AS duration_seconds
FROM coach_sessions s
LEFT JOIN coach_llm_usage u
    ON u.app_session_id = s.app_session_id
GROUP BY
    s.id,
    s.app_session_id,
    s.session_label,
    s.started_at,
    s.last_interaction_at,
    s.closed_at,
    s.status,
    s.current_stage,
    s.turns_count,
    s.synthesis_generated,
    s.pathways_generated,
    s.pdf_downloaded
ORDER BY s.started_at DESC;
```

---

## Optional query parameters

For the first implementation, keep this minimal.

Required:

```text
token
```

Optional but useful if simple to implement:

```text
limit
```

Example:

```text
/admin/telemetry/export.xlsx?token=<secret>&limit=1000
```

If implemented, `limit` should default to a sensible value such as `5000` and have a maximum cap such as `20000`.

Do not add date filters unless they are very easy and low risk. They can come later.

---

## Dependency

Use `openpyxl` for creating the Excel workbook.

If the project does not already include it, add it to the backend dependency file, usually:

```text
requirements.txt
```

or the appropriate backend dependency manifest.

Postgres access should use the existing Postgres dependency introduced by the telemetry sink, likely `psycopg[binary]`.

---

## Error handling

Export endpoint failures should return appropriate HTTP errors but must not affect normal app operation.

Recommended behaviour:

- missing token: `403 Forbidden`
- invalid token: `403 Forbidden`
- missing `TELEMETRY_EXPORT_TOKEN`: `503 Service Unavailable`
- missing `TELEMETRY_DATABASE_URL`: `503 Service Unavailable`
- database query failure: `500 Internal Server Error`
- workbook build failure: `500 Internal Server Error`

Do not leak database credentials or secrets in error responses.

---

## Security notes

For this PoC, a shared token is acceptable.

Rules:

- token must be stored only in environment variables
- token must not be committed to source code
- token must not appear in logs
- endpoint must not be linked from the public React UI
- exported workbook must not contain raw user conversation content

Later, this can be replaced with proper admin authentication.

---

## Testing checklist

### Local

1. Ensure local Postgres is running.
2. Ensure telemetry tables exist in `glimpsedb`.
3. Set:

```env
TELEMETRY_DATABASE_URL=postgresql://lucadematteis@localhost:5432/glimpsedb
TELEMETRY_EXPORT_TOKEN=<local-secret>
```

4. Run backend locally.
5. Open:

```text
http://localhost:<backend-port>/admin/telemetry/export.xlsx?token=<local-secret>
```

6. Confirm a workbook downloads.
7. Confirm sheets exist:
   - `Sessions`
   - `LLM Usage`
   - `Session Token Summary`
8. Confirm wrong token returns `403`.
9. Confirm no frontend changes are required.

### Render

1. Set `TELEMETRY_DATABASE_URL` to Render internal database URL.
2. Set `TELEMETRY_EXPORT_TOKEN` to a long random secret.
3. Deploy backend.
4. Open:

```text
https://<backend-host>/admin/telemetry/export.xlsx?token=<secret>
```

5. Confirm workbook downloads.
6. Confirm wrong token returns `403`.

---

## Future extensions

The `/admin` route structure can later support:

- `/admin/telemetry/sessions.csv`
- `/admin/telemetry/llm-usage.csv`
- `/admin/telemetry/summary.csv`
- `/admin/telemetry/dashboard`
- `/admin/health`
- `/admin/version`
- proper admin authentication

Do not implement these now unless explicitly requested.
