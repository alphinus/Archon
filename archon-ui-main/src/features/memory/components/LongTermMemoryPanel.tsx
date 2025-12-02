/**
 * Long-Term Memory Panel
 * 
 * Displays permanent facts with importance scores.
 */

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/Badge';
import { useLongTermMemory } from '../hooks/useMemoryApi';

// TODO: Get from auth context
const MOCK_USER_ID = '550e8400-e29b-41d4-a716-446655440000';  // Valid test UUID

export function LongTermMemoryPanel() {
    const { data, isLoading, error } = useLongTermMemory(MOCK_USER_ID);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-gray-400">Loading long-term memory...</div>
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
                <div className="text-gray-500">No long-term memories found</div>
            </div>
        );
    }

    return (
        <div className="rounded-md border border-gray-800 overflow-hidden">
            <Table>
                <TableHeader>
                    <TableRow className="border-gray-800 hover:bg-gray-800/50">
                        <TableHead className="text-gray-300">Type</TableHead>
                        <TableHead className="text-gray-300">Content</TableHead>
                        <TableHead className="text-gray-300">Importance</TableHead>
                        <TableHead className="text-gray-300">Access</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {data.entries.map((fact) => (
                        <TableRow key={fact.id} className="border-gray-800 hover:bg-gray-800/50">
                            <TableCell>
                                <Badge variant="outline" className="border-blue-600/30 text-blue-300">
                                    {fact.memory_type}
                                </Badge>
                            </TableCell>
                            <TableCell className="max-w-md">
                                <p className="text-sm text-gray-300 font-mono">
                                    {JSON.stringify(fact.content).substring(0, 100)}
                                    {JSON.stringify(fact.content).length > 100 ? '...' : ''}
                                </p>
                            </TableCell>
                            <TableCell>
                                <div className="flex items-center gap-2">
                                    <Progress
                                        value={fact.importance_score * 100}
                                        className="w-20 h-2"
                                    />
                                    <span className="text-xs text-gray-400 w-12">
                                        {(fact.importance_score * 100).toFixed(0)}%
                                    </span>
                                </div>
                            </TableCell>
                            <TableCell className="text-sm text-gray-400">
                                {fact.access_count}x
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
}
