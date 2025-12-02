/**
 * Working Memory Panel
 * 
 * Displays recent memory entries (7-30 days TTL) in card grid.
 */

import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useWorkingMemory } from '../hooks/useMemoryApi';

// TODO: Get from auth context
const MOCK_USER_ID = '550e8400-e29b-41d4-a716-446655440000';  // Valid test UUID

export function WorkingMemoryPanel() {
    const { data, isLoading, error } = useWorkingMemory(MOCK_USER_ID);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-gray-400">Loading working memory...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-red-400">Error: {error.message}</div>
            </div>
        );
    }

    if (!data || data.entries.length === 0) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-gray-500">No working memories found</div>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
            {data.entries.map((mem) => (
                <Card key={mem.id} className="bg-gray-800 border-gray-700 hover:border-gray-600 transition-colors p-4">
                    <div className="flex items-center justify-between mb-3">
                        <Badge variant="secondary" className="bg-violet-600/20 text-violet-300 border-violet-600/30">
                            {mem.memory_type}
                        </Badge>
                        <span className="text-xs text-gray-400">
                            {new Date(mem.created_at).toLocaleDateString()}
                        </span>
                    </div>

                    <div className="text-sm text-gray-300 mb-3 font-mono bg-gray-900 p-2 rounded max-h-24 overflow-y-auto">
                        {JSON.stringify(mem.content, null, 2)}
                    </div>

                    {mem.expires_at && (
                        <div className="text-xs text-gray-500">
                            Expires: {new Date(mem.expires_at).toLocaleDateString()}
                        </div>
                    )}
                </Card>
            ))}
        </div>
    );
}
