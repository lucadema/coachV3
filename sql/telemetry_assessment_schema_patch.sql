-- General telemetry assessment schema patch

ALTER TABLE coach_sessions
ADD COLUMN IF NOT EXISTS problem_category TEXT NULL;

ALTER TABLE coach_sessions
ADD COLUMN IF NOT EXISTS engagement_signal TEXT NULL;
