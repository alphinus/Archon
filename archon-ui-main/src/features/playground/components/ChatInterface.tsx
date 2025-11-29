/**
 * Chat Interface Component
 * 
 * Interactive chat with the agent.
 */

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Bot, User, RotateCcw } from 'lucide-react';
import { ChatMessage } from '../types/playground.types';

interface ChatInterfaceProps {
    agentId: string;
}

export function ChatInterface({ agentId }: ChatInterfaceProps) {
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState<ChatMessage[]>([
        {
            id: '1',
            role: 'system',
            content: 'Agent initialized. Ready to help.',
            timestamp: new Date().toISOString(),
        }
    ]);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    const handleSend = () => {
        if (!input.trim()) return;

        const userMsg: ChatMessage = {
            id: Date.now().toString(),
            role: 'user',
            content: input,
            timestamp: new Date().toISOString(),
            status: 'sent'
        };

        setMessages(prev => [...prev, userMsg]);
        setInput('');

        // Mock response
        setTimeout(() => {
            const botMsg: ChatMessage = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: `I received your message: "${input}". I am a mock agent for now.`,
                timestamp: new Date().toISOString(),
            };
            setMessages(prev => [...prev, botMsg]);
        }, 1000);
    };

    return (
        <div className="flex flex-col h-full bg-gray-950/50">
            <div className="p-4 border-b border-gray-800 flex justify-between items-center bg-gray-900">
                <div className="flex items-center gap-2">
                    <Bot className="h-5 w-5 text-violet-400" />
                    <span className="font-semibold text-white">Chat Session</span>
                </div>
                <Button variant="ghost" size="sm" onClick={() => setMessages([])} className="text-gray-400 hover:text-white">
                    <RotateCcw className="h-4 w-4 mr-2" />
                    Reset
                </Button>
            </div>

            <ScrollArea className="flex-1 p-4">
                <div className="space-y-4">
                    {messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-[85%] rounded-lg p-3 ${msg.role === 'user'
                                        ? 'bg-violet-600 text-white'
                                        : msg.role === 'system'
                                            ? 'bg-gray-800 text-gray-400 text-xs text-center w-full bg-transparent'
                                            : 'bg-gray-800 text-gray-100'
                                    }`}
                            >
                                {msg.role !== 'system' && (
                                    <div className="flex items-center gap-2 mb-1 opacity-70 text-xs">
                                        {msg.role === 'user' ? <User className="h-3 w-3" /> : <Bot className="h-3 w-3" />}
                                        <span className="capitalize">{msg.role}</span>
                                    </div>
                                )}
                                <p className="whitespace-pre-wrap">{msg.content}</p>
                            </div>
                        </div>
                    ))}
                    <div ref={scrollRef} />
                </div>
            </ScrollArea>

            <div className="p-4 border-t border-gray-800 bg-gray-900">
                <div className="flex gap-2">
                    <Input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="Type a message..."
                        className="bg-gray-950 border-gray-700 text-white"
                    />
                    <Button onClick={handleSend} className="bg-violet-600 hover:bg-violet-700">
                        <Send className="h-4 w-4" />
                    </Button>
                </div>
            </div>
        </div>
    );
}
