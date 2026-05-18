-- Session label telemetry schema patch
-- Safe to run on local Postgres and Render Postgres.

ALTER TABLE coach_sessions
ADD COLUMN IF NOT EXISTS session_label TEXT NULL;

CREATE INDEX IF NOT EXISTS idx_coach_sessions_session_label
ON coach_sessions (session_label);
