/**
 * Agent Playground Component
 * 
 * Main container layout for the playground.
 */

import { useState } from 'react';
import { ChatInterface } from './ChatInterface';
import { ToolLogPanel } from './ToolLogPanel';
import { AgentConfigPanel } from './AgentConfigPanel';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable';

export function AgentPlayground() {
    const [selectedAgentId, setSelectedAgentId] = useState('agent_001');

    return (
        <div className="h-full border border-gray-800 rounded-lg bg-gray-900 overflow-hidden">
            <ResizablePanelGroup direction="horizontal">
                {/* Left: Chat Interface */}
                <ResizablePanel defaultSize={50} minSize={30}>
                    <ChatInterface agentId={selectedAgentId} />
                </ResizablePanel>

                <ResizableHandle className="bg-gray-800" />

                {/* Right: Tools & Config */}
                <ResizablePanel defaultSize={50} minSize={30}>
                    <ResizablePanelGroup direction="vertical">
                        {/* Top Right: Tool Logs */}
                        <ResizablePanel defaultSize={60} minSize={30}>
                            <ToolLogPanel />
                        </ResizablePanel>

                        <ResizableHandle className="bg-gray-800" />

                        {/* Bottom Right: Configuration */}
                        <ResizablePanel defaultSize={40} minSize={20}>
                            <AgentConfigPanel
                                selectedAgentId={selectedAgentId}
                                onAgentChange={setSelectedAgentId}
                            />
                        </ResizablePanel>
                    </ResizablePanelGroup>
                </ResizablePanel>
            </ResizablePanelGroup>
        </div>
    );
}
