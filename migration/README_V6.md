-- Run this migration to enable Event Reliability features
-- Execute in Supabase SQL Editor or via psql

-- Migration already created at: migration/V6_event_reliability.sql
-- This file just documents that it needs to be run

-- To apply:
-- 1. Open Supabase Dashboard → SQL Editor
-- 2. Paste contents of V6_event_reliability.sql
-- 3. Execute

-- Tables created:
-- - event_failures (Dead Letter Queue)
-- - event_replay_log (Audit trail)

-- Note: Migration is idempotent (uses IF NOT EXISTS)
