/**
 * Tool Log Panel
 * 
 * Displays tool execution history.
 */

import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Terminal, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { ToolExecution } from '../types/playground.types';

export function ToolLogPanel() {
    // Mock data
    const logs: ToolExecution[] = [
        {
            id: '1',
            tool_name: 'memory_search',
            input: { query: 'project status', limit: 5 },
            output: { results: [] },
            status: 'completed',
            timestamp: new Date(Date.now() - 5000).toISOString(),
            duration_ms: 120
        },
        {
            id: '2',
            tool_name: 'calculator',
            input: { expression: '24 * 7' },
            output: 168,
            status: 'completed',
            timestamp: new Date(Date.now() - 15000).toISOString(),
            duration_ms: 45
        },
        {
            id: '3',
            tool_name: 'web_search',
            input: { query: 'latest python version' },
            status: 'failed',
            timestamp: new Date(Date.now() - 30000).toISOString(),
            duration_ms: 2500
        }
    ];

    return (
        <div className="flex flex-col h-full bg-gray-950/30">
            <div className="p-3 border-b border-gray-800 bg-gray-900 flex items-center gap-2">
                <Terminal className="h-4 w-4 text-blue-400" />
                <span className="font-semibold text-white text-sm">Tool Executions</span>
            </div>

            <ScrollArea className="flex-1 p-0">
                <div className="divide-y divide-gray-800">
                    {logs.map((log) => (
                        <div key={log.id} className="p-3 hover:bg-gray-900/50 transition-colors">
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                    {log.status === 'completed' ? (
                                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                                    ) : log.status === 'failed' ? (
                                        <XCircle className="h-4 w-4 text-red-500" />
                                    ) : (
                                        <Clock className="h-4 w-4 text-yellow-500 animate-pulse" />
                                    )}
                                    <span className="font-mono text-sm text-blue-300">{log.tool_name}</span>
                                </div>
                                <span className="text-xs text-gray-500">
                                    {new Date(log.timestamp).toLocaleTimeString()} • {log.duration_ms}ms
                                </span>
                            </div>

                            <div className="space-y-1">
                                <div className="text-xs text-gray-400">Input:</div>
                                <pre className="text-xs bg-gray-950 p-2 rounded border border-gray-800 text-gray-300 overflow-x-auto">
                                    {JSON.stringify(log.input, null, 2)}
                                </pre>

                                {log.output && (
                                    <>
                                        <div className="text-xs text-gray-400 mt-2">Output:</div>
                                        <pre className="text-xs bg-gray-950 p-2 rounded border border-gray-800 text-green-300 overflow-x-auto">
                                            {JSON.stringify(log.output, null, 2)}
                                        </pre>
                                    </>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </ScrollArea>
        </div>
    );
}
