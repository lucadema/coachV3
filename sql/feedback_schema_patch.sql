-- Configurable feedback schema patch

ALTER TABLE coach_sessions
ADD COLUMN IF NOT EXISTS feedback_pack_id TEXT NULL,
ADD COLUMN IF NOT EXISTS feedback_responses JSONB NULL;
