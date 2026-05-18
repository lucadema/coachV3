-- Telemetry schema for CoachV3 / Glimpse
--
-- This schema is created explicitly by an operator/developer using psql.
-- The backend must not create or migrate this schema automatically at startup.

CREATE TABLE IF NOT EXISTS coach_sessions (
    id BIGSERIAL PRIMARY KEY,

    app_session_id TEXT NOT NULL UNIQUE,

    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_interaction_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ NULL,

    status TEXT NOT NULL DEFAULT 'active',
    current_stage TEXT NOT NULL DEFAULT 'problem_submitted',
    session_label TEXT NULL,
    turns_count INTEGER NOT NULL DEFAULT 0 CHECK (turns_count >= 0),

    synthesis_generated BOOLEAN NOT NULL DEFAULT FALSE,
    pathways_generated BOOLEAN NOT NULL DEFAULT FALSE,
    pdf_downloaded BOOLEAN NOT NULL DEFAULT FALSE,

    feedback_submitted_at TIMESTAMPTZ NULL,
    feedback_answer_1 BOOLEAN NULL,
    feedback_answer_2 BOOLEAN NULL,
    feedback_dropdown_values TEXT[] NULL,
    feedback_payload JSONB NULL,

    last_error TEXT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_coach_sessions_started_at
ON coach_sessions (started_at DESC);

CREATE INDEX IF NOT EXISTS idx_coach_sessions_status
ON coach_sessions (status);

CREATE INDEX IF NOT EXISTS idx_coach_sessions_session_label
ON coach_sessions (session_label);

CREATE INDEX IF NOT EXISTS idx_coach_sessions_last_interaction_at
ON coach_sessions (last_interaction_at DESC);

CREATE TABLE IF NOT EXISTS coach_llm_usage (
    id BIGSERIAL PRIMARY KEY,

    app_session_id TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    llm_operation TEXT NOT NULL,

    provider TEXT NOT NULL DEFAULT 'openai',
    model TEXT NULL,

    input_tokens INTEGER NULL CHECK (input_tokens IS NULL OR input_tokens >= 0),
    output_tokens INTEGER NULL CHECK (output_tokens IS NULL OR output_tokens >= 0),
    total_tokens INTEGER NULL CHECK (total_tokens IS NULL OR total_tokens >= 0),

    cached_input_tokens INTEGER NULL CHECK (cached_input_tokens IS NULL OR cached_input_tokens >= 0),
    reasoning_tokens INTEGER NULL CHECK (reasoning_tokens IS NULL OR reasoning_tokens >= 0),

    success BOOLEAN NOT NULL DEFAULT TRUE,
    latency_ms INTEGER NULL CHECK (latency_ms IS NULL OR latency_ms >= 0),
    error_type TEXT NULL,
    error_message TEXT NULL,

    metadata JSONB NULL,

    CONSTRAINT fk_coach_llm_usage_app_session
        FOREIGN KEY (app_session_id)
        REFERENCES coach_sessions(app_session_id)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS idx_coach_llm_usage_app_session_id
ON coach_llm_usage (app_session_id);

CREATE INDEX IF NOT EXISTS idx_coach_llm_usage_created_at
ON coach_llm_usage (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_coach_llm_usage_operation
ON coach_llm_usage (llm_operation);
