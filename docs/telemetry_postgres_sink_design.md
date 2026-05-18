# Telemetry PostgreSQL Sink Design

This file mirrors the active Postgres telemetry design in
`docs/telemetry_postgres_sink_design_final.md`.

## Session Label Note

`session_label` is optional launch/session metadata from the URL query
parameter `session_label`. The React frontend passes it only as generic client
context. The backend sanitises it and stores it only in
`coach_sessions.session_label`.

It is not authentication, not user identity, and not frontend analytics. It is
not written to `coach_llm_usage` and must not carry raw prompts, user messages,
conversation history, synthesis text, or pathway text. Its intended use is
filtering test, demo, or internal sessions from real user sessions.
