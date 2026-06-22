-- Add per-pilot feedback pack selection for Glimpse feedback forms.
--
-- The value should match a key under feedback_packs in
-- backend/config/feedback_forms.yaml. Runtime falls back to the YAML
-- default_feedback_pack_id when this is NULL, invalid, or unavailable.

ALTER TABLE admin_pilots
ADD COLUMN IF NOT EXISTS feedback_pack_id TEXT NULL;
