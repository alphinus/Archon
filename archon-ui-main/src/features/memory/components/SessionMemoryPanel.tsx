/**
 * Session Memory Panel
 * 
 * Displays session conversation history from Redis.
 */

import { Card } from '@/components/ui/Card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { User, Bot } from 'lucide-react';
import { useSessionMemory } from '../hooks/useMemoryApi';


// TODO: Get from auth context
const MOCK_SESSION_ID = 'session_123';

export function SessionMemoryPanel() {
    const { data, isLoading, error } = useSessionMemory(MOCK_SESSION_ID);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-gray-400">Loading session history...</div>
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

    if (!data || data.messages.length === 0) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-gray-500">No messages in this session</div>
            </div>
        );
    }

    return (
        <ScrollArea className="h-full p-4">
            <div className="space-y-4">
                <div className="text-sm text-gray-400 mb-4">
                    Session: {data.session_id} • {data.message_count} messages
                </div>

                {data.messages.map((msg, idx) => (
                    <Card key={idx} className={`p-4 ${msg.role === 'user' ? 'bg-violet-900/20' : 'bg-gray-800'
                        }`}>
                        <div className="flex items-start gap-3">
                            <div className="mt-1">
                                {msg.role === 'user' ? (
                                    <User className="h-5 w-5 text-violet-400" />
                                ) : (
                                    <Bot className="h-5 w-5 text-blue-400" />
                                )}
                            </div>
                            <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-sm font-semibold text-gray-200 capitalize">
                                        {msg.role}
                                    </span>
                                    <span className="text-xs text-gray-500">
                                        {new Date(msg.timestamp).toLocaleTimeString()}
                                    </span>
                                </div>
                                <p className="text-sm text-gray-300 whitespace-pre-wrap">{msg.content}</p>
                            </div>
                        </div>
                    </Card>
                ))}
            </div>
        </ScrollArea>
    );
}
