-- Aether Glimpse Admin Control Panel schema
--
-- This schema is applied explicitly by an operator/developer using psql.
-- The backend does not auto-migrate at startup. Admin tables are deliberately
-- separate from the existing Glimpse coaching/session tables.

CREATE TABLE IF NOT EXISTS admin_enterprises (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'paused', 'closed')),
    notes TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_admin_enterprises_status
ON admin_enterprises (status);

CREATE INDEX IF NOT EXISTS idx_admin_enterprises_created_at
ON admin_enterprises (created_at DESC);

CREATE TABLE IF NOT EXISTS admin_pilots (
    id TEXT PRIMARY KEY,
    enterprise_id TEXT NOT NULL REFERENCES admin_enterprises(id) ON DELETE RESTRICT,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'active', 'paused', 'closed')),
    start_at TIMESTAMPTZ NULL,
    end_at TIMESTAMPTZ NULL,
    notes TEXT NOT NULL DEFAULT '',
    feedback_pack_id TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (end_at IS NULL OR start_at IS NULL OR end_at >= start_at)
);

ALTER TABLE admin_pilots
ADD COLUMN IF NOT EXISTS feedback_pack_id TEXT NULL;

CREATE INDEX IF NOT EXISTS idx_admin_pilots_enterprise_id
ON admin_pilots (enterprise_id);

CREATE INDEX IF NOT EXISTS idx_admin_pilots_status
ON admin_pilots (status);

CREATE INDEX IF NOT EXISTS idx_admin_pilots_created_at
ON admin_pilots (created_at DESC);

CREATE TABLE IF NOT EXISTS admin_access_tokens (
    id TEXT PRIMARY KEY,
    pilot_id TEXT NOT NULL REFERENCES admin_pilots(id) ON DELETE CASCADE,
    token_type TEXT NOT NULL CHECK (token_type IN ('glimpse_app', 'dashboard')),
    token_hash TEXT NOT NULL UNIQUE,

    -- Pilot-stage compromise: this is recoverable storage so authorised admins
    -- can copy links. Keep isolated so it can be replaced with encrypted storage.
    token_recoverable TEXT NOT NULL,
    token_prefix TEXT NOT NULL,

    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'revoked', 'expired')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NULL,
    last_used_at TIMESTAMPTZ NULL,
    revoked_at TIMESTAMPTZ NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_admin_access_tokens_one_active_per_type
ON admin_access_tokens (pilot_id, token_type)
WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_admin_access_tokens_pilot_id
ON admin_access_tokens (pilot_id);

CREATE INDEX IF NOT EXISTS idx_admin_access_tokens_hash
ON admin_access_tokens (token_hash);

CREATE INDEX IF NOT EXISTS idx_admin_access_tokens_status
ON admin_access_tokens (status);

CREATE TABLE IF NOT EXISTS admin_audit_events (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor TEXT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    metadata JSONB NULL
);

CREATE INDEX IF NOT EXISTS idx_admin_audit_events_created_at
ON admin_audit_events (created_at DESC);

ALTER TABLE coach_sessions
ADD COLUMN IF NOT EXISTS pilot_id TEXT NULL;

CREATE INDEX IF NOT EXISTS idx_coach_sessions_pilot_id
ON coach_sessions (pilot_id);
