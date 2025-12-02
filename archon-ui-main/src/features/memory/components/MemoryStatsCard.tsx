/**
 * Memory Stats Card
 *
 * Displays memory usage statistics from backend.
 */

import { Card } from '@/components/ui/Card';
import { Database, Zap, TrendingUp } from 'lucide-react';
import { useMemoryStats } from '../hooks/useMemoryApi';


// TODO: Get from auth context
const MOCK_USER_ID = '550e8400-e29b-41d4-a716-446655440000';  // Valid test UUID

export function MemoryStatsCard() {
    const { data, isLoading, error } = useMemoryStats(MOCK_USER_ID);

    if (isLoading) {
        return (
            <Card className="bg-gray-900 border-gray-800 p-4">
                <div className="text-white text-sm font-semibold mb-3">Memory Statistics</div>
                <div className="text-gray-400 text-sm">Loading stats...</div>
            </Card>
        );
    }

    if (error) {
        return (
            <Card className="bg-gray-900 border-gray-800 p-4">
                <div className="text-white text-sm font-semibold mb-3">Memory Statistics</div>
                <div className="text-red-400 text-sm">Failed to load stats</div>
            </Card>
        );
    }

    return (
        <Card className="bg-gray-900 border-gray-800 p-4">
            <div className="text-white text-sm font-semibold mb-4">Memory Statistics</div>

            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Database className="h-4 w-4 text-blue-400" />
                        <span className="text-sm text-gray-400">Total Memories</span>
                    </div>
                    <span className="text-lg font-bold text-white">
                        {data?.total_memories || 0}
                    </span>
                </div>

                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Zap className="h-4 w-4 text-yellow-400" />
                        <span className="text-sm text-gray-400">Working</span>
                    </div>
                    <span className="text-sm font-semibold text-gray-300">
                        {data?.working_memory_count || 0}
                    </span>
                </div>

                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-green-400" />
                        <span className="text-sm text-gray-400">Long-Term</span>
                    </div>
                    <span className="text-sm font-semibold text-gray-300">
                        {data?.longterm_memory_count || 0}
                    </span>
                </div>

                {data?.avg_importance !== undefined && (
                    <div className="pt-2 border-t border-gray-800">
                        <div className="text-xs text-gray-500 mb-1">Avg Importance</div>
                        <div className="text-sm font-semibold text-violet-400">
                            {(data.avg_importance * 100).toFixed(1)}%
                        </div>
                    </div>
                )}
            </div>
        </Card>
    );
}
