/**
 * React Query hooks for Memory API
 */

import { useQuery } from '@tanstack/react-query';
import type {
    SessionMessage,
    WorkingMemoryEntry,
    LongTermMemoryEntry,
    MemoryStats
} from '../types/memory.types';

const API_BASE = 'http://localhost:8181';

// Response types from backend
interface SessionHistoryResponse {
    session_id: string;
    user_id: string;
    message_count: number;
    messages: SessionMessage[];
    has_more: boolean;
}

interface WorkingMemoryResponse {
    entries: WorkingMemoryEntry[];
    total_count: number;
    page: number;
    page_size: number;
}

interface LongTermMemoryResponse {
    entries: LongTermMemoryEntry[];
    total_count: number;
    page: number;
    page_size: number;
}

/**
 * Fetch session conversation history
 */
export function useSessionMemory(sessionId: string, options?: { limit?: number; offset?: number }) {
    const { limit = 100, offset = 0 } = options || {};

    return useQuery<SessionHistoryResponse>({
        queryKey: ['memory', 'session', sessionId, limit, offset],
        queryFn: async () => {
            const response = await fetch(
                `${API_BASE}/api/memory/session/${sessionId}?limit=${limit}&offset=${offset}`
            );

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Failed to fetch session memory' }));
                throw new Error(error.detail || 'Failed to fetch session memory');
            }

            return response.json();
        },
        enabled: !!sessionId,
        staleTime: 30000, // 30 seconds
        refetchOnWindowFocus: false,
    });
}

/**
 * Fetch working memory entries
 */
export function useWorkingMemory(
    userId: string,
    options?: { memoryType?: string; page?: number; pageSize?: number }
) {
    const { memoryType, page = 1, pageSize = 20 } = options || {};

    return useQuery<WorkingMemoryResponse>({
        queryKey: ['memory', 'working', userId, memoryType, page, pageSize],
        queryFn: async () => {
            const params = new URLSearchParams({
                user_id: userId,
                page: page.toString(),
                page_size: pageSize.toString(),
            });

            if (memoryType) {
                params.append('memory_type', memoryType);
            }

            const response = await fetch(`${API_BASE}/api/memory/working?${params}`);

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Failed to fetch working memory' }));
                throw new Error(error.detail || 'Failed to fetch working memory');
            }

            return response.json();
        },
        enabled: !!userId,
        staleTime: 30000,
        refetchOnWindowFocus: false,
    });
}

/**
 * Fetch long-term memory entries
 */
export function useLongTermMemory(
    userId: string,
    options?: { memoryType?: string; minImportance?: number; page?: number; pageSize?: number }
) {
    const { memoryType, minImportance = 0.0, page = 1, pageSize = 50 } = options || {};

    return useQuery<LongTermMemoryResponse>({
        queryKey: ['memory', 'longterm', userId, memoryType, minImportance, page, pageSize],
        queryFn: async () => {
            const params = new URLSearchParams({
                user_id: userId,
                min_importance: minImportance.toString(),
                page: page.toString(),
                page_size: pageSize.toString(),
            });

            if (memoryType) {
                params.append('memory_type', memoryType);
            }

            const response = await fetch(`${API_BASE}/api/memory/longterm?${params}`);

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Failed to fetch long-term memory' }));
                throw new Error(error.detail || 'Failed to fetch long-term memory');
            }

            return response.json();
        },
        enabled: !!userId,
        staleTime: 60000, // 1 minute (less frequently changing)
        refetchOnWindowFocus: false,
    });
}

/**
 * Fetch memory statistics
 */
export function useMemoryStats(userId: string) {
    return useQuery<MemoryStats>({
        queryKey: ['memory', 'stats', userId],
        queryFn: async () => {
            const response = await fetch(`${API_BASE}/api/memory/stats/${userId}`);

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Failed to fetch memory stats' }));
                throw new Error(error.detail || 'Failed to fetch memory stats');
            }

            return response.json();
        },
        enabled: !!userId,
        staleTime: 60000,
        refetchOnWindowFocus: false,
    });
}
