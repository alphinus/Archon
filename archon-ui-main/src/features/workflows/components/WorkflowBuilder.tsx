/**
 * Workflow Builder Component
 * 
 * Main editor interface with sidebar and canvas.
 */

import { useState } from 'react';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable';
import { NodeSidebar } from './NodeSidebar';
import { WorkflowCanvas } from './WorkflowCanvas';
import { WorkflowControls } from './WorkflowControls';

export function WorkflowBuilder() {
    return (
        <div className="h-full flex flex-col">
            <WorkflowControls />

            <div className="flex-1 min-h-0">
                <ResizablePanelGroup direction="horizontal">
                    {/* Left: Component Sidebar */}
                    <ResizablePanel defaultSize={20} minSize={15} maxSize={30}>
                        <NodeSidebar />
                    </ResizablePanel>

                    <ResizableHandle className="bg-gray-800" />

                    {/* Center: Canvas */}
                    <ResizablePanel defaultSize={80}>
                        <WorkflowCanvas />
                    </ResizablePanel>
                </ResizablePanelGroup>
            </div>
        </div>
    );
}
