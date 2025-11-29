-- Event Reliability: Dead Letter Queue
-- Stores failed events for retry and auditing

CREATE TABLE IF NOT EXISTS event_failures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    user_id TEXT,
    error_message TEXT,
    stack_trace TEXT,
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    last_retry_at TIMESTAMPTZ,
    next_retry_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'retrying', 'resolved', 'failed'))
);

-- Index for efficient queries
CREATE INDEX IF NOT EXISTS idx_event_failures_status ON event_failures(status);
CREATE INDEX IF NOT EXISTS idx_event_failures_next_retry ON event_failures(next_retry_at) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_event_failures_user_id ON event_failures(user_id);

-- Event replay log
CREATE TABLE IF NOT EXISTS event_replay_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_failure_id UUID REFERENCES event_failures(id),
    replayed_at TIMESTAMPTZ DEFAULT NOW(),
    success BOOLEAN NOT NULL,
    error_message TEXT
);

COMMENT ON TABLE event_failures IS 'Dead letter queue for failed events';
COMMENT ON TABLE event_replay_log IS 'Audit log for event replay attempts';
