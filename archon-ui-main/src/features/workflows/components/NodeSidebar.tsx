/**
 * Node Sidebar
 * 
 * Draggable components to add to the workflow.
 */

import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Zap, Play, GitBranch, Box, Mail, Database, MessageSquare } from 'lucide-react';

export function NodeSidebar() {
    const nodeTypes = [
        {
            category: 'Triggers',
            items: [
                { icon: Zap, label: 'Event Trigger', desc: 'React to system events' },
                { icon: Clock, label: 'Schedule', desc: 'Run periodically' },
                { icon: Mail, label: 'Email', desc: 'On incoming email' },
            ]
        },
        {
            category: 'Logic',
            items: [
                { icon: GitBranch, label: 'Condition', desc: 'If/Else logic' },
                { icon: Play, label: 'Loop', desc: 'Iterate over items' },
            ]
        },
        {
            category: 'Actions',
            items: [
                { icon: Box, label: 'Run Tool', desc: 'Execute an agent tool' },
                { icon: Database, label: 'Memory', desc: 'Read/Write memory' },
                { icon: MessageSquare, label: 'Send Message', desc: 'Reply to user' },
            ]
        }
    ];

    return (
        <div className="h-full bg-gray-900 border-r border-gray-800 flex flex-col">
            <div className="p-4 border-b border-gray-800">
                <h3 className="font-semibold text-white">Components</h3>
                <p className="text-xs text-gray-400 mt-1">Drag to canvas to add</p>
            </div>

            <ScrollArea className="flex-1 p-4">
                <div className="space-y-6">
                    {nodeTypes.map((category) => (
                        <div key={category.category}>
                            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                                {category.category}
                            </h4>
                            <div className="space-y-2">
                                {category.items.map((item) => (
                                    <Card
                                        key={item.label}
                                        className="p-3 bg-gray-800 border-gray-700 hover:border-violet-500 cursor-grab active:cursor-grabbing transition-colors"
                                    >
                                        <div className="flex items-start gap-3">
                                            <div className="p-2 rounded bg-gray-900 text-violet-400">
                                                <item.icon className="h-4 w-4" />
                                            </div>
                                            <div>
                                                <div className="text-sm font-medium text-gray-200">{item.label}</div>
                                                <div className="text-xs text-gray-500">{item.desc}</div>
                                            </div>
                                        </div>
                                    </Card>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </ScrollArea>
        </div>
    );
}

import { Clock } from 'lucide-react';
