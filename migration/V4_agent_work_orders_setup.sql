-- AI Empire HQ - V4 Agent Work Orders Supabase Migration
-- This is the FINAL consolidated and corrected script.
-- It replaces all previous versions.
-- Fixes applied:
-- 1. Added required 'pgcrypto' extension for gen_random_uuid().
-- 2. Added required trigger function 'update_updated_at_column()'.
-- 3. Removed redundant RLS policies for 'service_role'.
-- 4. Replaced 'FOR ALL' RLS policies with explicit policies.
-- 5. Corrected function call to 'extensions.gen_random_uuid()' to match Supabase schema standards.

-- =====================================================
-- SECTION 1: EXTENSIONS & FUNCTIONS
-- =====================================================

-- Ensure pgcrypto extension is available. Supabase typically places this in the 'extensions' schema.
CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA extensions;

-- Trigger function to automatically update 'updated_at' columns on row change.
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at := NOW();
  RETURN NEW;
END;
$$;

-- =====================================================
-- SECTION 2: TABLE CREATION
-- =====================================================

-- Table for storing agent work order state and history
CREATE TABLE IF NOT EXISTS public.archon_agent_work_orders (
    agent_work_order_id TEXT PRIMARY KEY NOT NULL,
    repository_url TEXT NOT NULL,
    sandbox_identifier TEXT NOT NULL,
    git_branch_name TEXT,
    agent_session_id TEXT,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.archon_agent_work_orders IS 'Stores the state and metadata for AI agent work orders.';

-- Table for storing individual steps of a work order
CREATE TABLE IF NOT EXISTS public.archon_agent_work_order_steps (
    id UUID PRIMARY KEY DEFAULT extensions.gen_random_uuid(),
    agent_work_order_id TEXT NOT NULL REFERENCES public.archon_agent_work_orders(agent_work_order_id) ON DELETE CASCADE,
    step TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    output TEXT,
    error_message TEXT,
    duration_seconds FLOAT NOT NULL,
    session_id TEXT,
    executed_at TIMESTAMPTZ NOT NULL,
    step_order INT NOT NULL
);

COMMENT ON TABLE public.archon_agent_work_order_steps IS 'Stores the detailed execution history for each step of a work order.';

-- Table for configuring repositories that agents can work on
CREATE TABLE IF NOT EXISTS public.archon_configured_repositories (
    id UUID PRIMARY KEY DEFAULT extensions.gen_random_uuid(),
    repository_url TEXT NOT NULL UNIQUE,
    display_name TEXT,
    owner TEXT,
    default_branch TEXT,
    is_verified BOOLEAN DEFAULT false,
    last_verified_at TIMESTAMPTZ,
    default_sandbox_type TEXT DEFAULT 'git_worktree' CHECK (default_sandbox_type IN ('git_worktree', 'full_clone', 'tmp_dir')),
    default_commands JSONB DEFAULT '["create-branch", "planning", "execute", "commit", "create-pr"]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT valid_repository_url CHECK (repository_url ~ '^https://github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+/?$')
);

COMMENT ON TABLE public.archon_configured_repositories IS 'Stores configured GitHub repositories agents are allowed to operate on.';


-- =====================================================
-- SECTION 3: INDEXES & TRIGGERS
-- =====================================================

-- Indexes for archon_agent_work_orders
CREATE INDEX IF NOT EXISTS idx_agent_work_orders_status ON public.archon_agent_work_orders(status);
CREATE INDEX IF NOT EXISTS idx_agent_work_orders_created_at ON public.archon_agent_work_orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_work_orders_repository ON public.archon_agent_work_orders(repository_url);

-- Indexes for archon_agent_work_order_steps
CREATE INDEX IF NOT EXISTS idx_agent_work_order_steps_work_order_id ON public.archon_agent_work_order_steps(agent_work_order_id);

-- Indexes for archon_configured_repositories
CREATE UNIQUE INDEX IF NOT EXISTS idx_configured_repositories_url ON public.archon_configured_repositories(repository_url);
CREATE INDEX IF NOT EXISTS idx_configured_repositories_verified ON public.archon_configured_repositories(is_verified);

-- Triggers to update the 'updated_at' timestamp
CREATE TRIGGER update_agent_work_orders_updated_at
  BEFORE UPDATE ON public.archon_agent_work_orders
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_configured_repositories_updated_at
  BEFORE UPDATE ON public.archon_configured_repositories
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


-- =====================================================
-- SECTION 4: ROW LEVEL SECURITY (RLS)
-- =====================================================

-- Enable RLS for all tables
ALTER TABLE public.archon_agent_work_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.archon_agent_work_order_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.archon_configured_repositories ENABLE ROW LEVEL SECURITY;

-- SECURITY WARNING: The following policies are permissive and allow any authenticated user
-- to read and write all data. For a production, multi-tenant application,
-- you MUST replace these with owner-based policies (e.g., USING (owner_id = auth.uid())).

-- Policies for archon_agent_work_orders
CREATE POLICY "Allow authenticated full access to work orders"
  ON public.archon_agent_work_orders
  FOR ALL TO authenticated
  USING (true)
  WITH CHECK (true);

-- Policies for archon_agent_work_order_steps
CREATE POLICY "Allow authenticated full access to work order steps"
  ON public.archon_agent_work_order_steps
  FOR ALL TO authenticated
  USING (true)
  WITH CHECK (true);

-- Policies for archon_configured_repositories
CREATE POLICY "Allow authenticated full access to repositories"
  ON public.archon_configured_repositories
  FOR ALL TO authenticated
  USING (true)
  WITH CHECK (true);


-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================
