/**
 * Playground TypeScript Types
 */

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    status?: 'sending' | 'sent' | 'error';
}

export interface ToolExecution {
    id: string;
    tool_name: string;
    input: Record<string, any>;
    output?: any;
    status: 'running' | 'completed' | 'failed';
    timestamp: string;
    duration_ms?: number;
}

export interface AgentConfig {
    id: string;
    name: string;
    model: string;
    temperature: number;
    system_prompt: string;
    tools: string[];
}
