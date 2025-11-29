/**
 * Memory TypeScript Types
 * 
 * Type definitions for Archon's memory system.
 */

export interface SessionMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
}

export interface WorkingMemoryEntry {
    id: string;
    user_id: string;
    memory_type: string;
    content: Record<string, any>;
    metadata: Record<string, any>;
    created_at: string;
    expires_at: string | null;
}

export interface LongTermMemoryEntry {
    id: string;
    user_id: string;
    memory_type: string;
    content: Record<string, any>;
    importance_score: number;  // Backend uses "importance_score" not "importance"
    metadata: Record<string, any>;
    created_at: string;
    last_accessed_at: string;  // Backend uses "last_accessed_at" not "last_accessed"
    access_count: number;
}


export interface AssembledContext {
    messages: Array<Record<string, any>>;
    facts: Array<Record<string, any>>;
    total_tokens: number;
    source_counts: Record<string, number>;
    status: 'healthy' | 'degraded' | 'cached' | 'error';
    error?: string;
}

export interface MemoryStats {
    user_id: string;
    working_memory_count: number;
    longterm_memory_count: number;
    total_memories: number;
    avg_importance?: number;  // Optional, might not always be present
}

export type MemoryType = 'session' | 'working' | 'longterm' | 'all';
