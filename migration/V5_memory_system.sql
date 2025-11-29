-- Migration V5: Memory System - Working & Long-Term Memory
-- Description: Creates tables for Working Memory (hot data) and Long-Term Memory (permanent storage)
-- Author: Antigravity
-- Date: 2025-11-28

-- ============================================================================
-- WORKING MEMORY (Hot Data - 7-30 days TTL)
-- ============================================================================

CREATE TABLE IF NOT EXISTS working_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    session_id VARCHAR(50),
    memory_type VARCHAR(50) NOT NULL,  -- 'conversation', 'action', 'decision'
    content JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    relevance_score FLOAT DEFAULT 1.0  -- Can decay over time (0.0 - 1.0)
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_working_memory_user_type_created 
    ON working_memory(user_id, memory_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_working_memory_expires 
    ON working_memory(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_working_memory_session 
    ON working_memory(session_id) WHERE session_id IS NOT NULL;

COMMENT ON TABLE working_memory IS 'Recent context and activity (7-30 days retention)';
COMMENT ON COLUMN working_memory.memory_type IS 'Type: conversation, action, decision';
COMMENT ON COLUMN working_memory.relevance_score IS 'Decays over time, items below 0.1 can be cleaned up';

-- ============================================================================
-- LONG-TERM MEMORY (Permanent Storage)
-- ============================================================================

CREATE TABLE IF NOT EXISTS long_term_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    memory_type VARCHAR(50) NOT NULL,  -- 'fact', 'preference', 'skill', 'relationship'
    content JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    importance_score FLOAT DEFAULT 0.5  -- 0.0 - 1.0
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_long_term_memory_user_type 
    ON long_term_memory(user_id, memory_type);
CREATE INDEX IF NOT EXISTS idx_long_term_memory_importance 
    ON long_term_memory(user_id, importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_long_term_memory_accessed 
    ON long_term_memory(last_accessed_at);

COMMENT ON TABLE long_term_memory IS 'Permanent knowledge base (facts, preferences, skills)';
COMMENT ON COLUMN long_term_memory.memory_type IS 'Type: fact, preference, skill, relationship';
COMMENT ON COLUMN long_term_memory.importance_score IS 'Decays for rarely accessed items';

-- ============================================================================
-- CLEANUP FUNCTION (for Working Memory TTL enforcement)
-- ============================================================================

CREATE OR REPLACE FUNCTION cleanup_expired_working_memory()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM working_memory
    WHERE expires_at < NOW()
       OR (relevance_score < 0.1 AND created_at < NOW() - INTERVAL '7 days');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_working_memory IS 'Cleanup expired or low-relevance working memories';

-- ============================================================================
-- IMPORTANCE DECAY FUNCTION (for Long-Term Memory)
-- ============================================================================

CREATE OR REPLACE FUNCTION decay_long_term_importance()
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    UPDATE long_term_memory
    SET importance_score = importance_score * 0.95
    WHERE last_accessed_at < NOW() - INTERVAL '30 days'
      AND importance_score > 0.1;
    
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION decay_long_term_importance IS 'Decay importance of rarely accessed memories';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Run these to verify migration success:
-- SELECT COUNT(*) FROM working_memory;
-- SELECT COUNT(*) FROM long_term_memory;
-- SELECT cleanup_expired_working_memory();
-- SELECT decay_long_term_importance();
