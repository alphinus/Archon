/**
 * Workflow Canvas
 * 
 * The visual graph editor area.
 * Note: React Flow integration would go here.
 */

import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';

export function WorkflowCanvas() {
    return (
        <div className="h-full bg-gray-950/50 relative overflow-hidden">
            {/* Grid Background Pattern */}
            <div className="absolute inset-0"
                style={{
                    backgroundImage: 'radial-gradient(#374151 1px, transparent 1px)',
                    backgroundSize: '20px 20px',
                    opacity: 0.2
                }}
            />

            {/* Mock Nodes for Visualization */}
            <div className="absolute top-1/4 left-1/4 w-64 p-4 bg-gray-800 border border-violet-500 rounded-lg shadow-lg">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-bold text-white">Trigger: New Email</span>
                    <div className="w-2 h-2 rounded-full bg-green-500" />
                </div>
                <p className="text-xs text-gray-400">Starts when email received</p>
            </div>

            <div className="absolute top-1/2 left-1/2 w-64 p-4 bg-gray-800 border border-blue-500 rounded-lg shadow-lg transform -translate-x-1/2 -translate-y-1/2">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-bold text-white">Action: Analyze Sentiment</span>
                    <div className="w-2 h-2 rounded-full bg-blue-500" />
                </div>
                <p className="text-xs text-gray-400">Uses GPT-4 to analyze tone</p>
            </div>

            {/* Connecting Line Mock */}
            <svg className="absolute inset-0 pointer-events-none">
                <path
                    d="M 400 250 L 600 400"
                    stroke="#4b5563"
                    strokeWidth="2"
                    fill="none"
                    markerEnd="url(#arrow)"
                />
                <defs>
                    <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
                        <path d="M0,0 L0,6 L9,3 z" fill="#4b5563" />
                    </marker>
                </defs>
            </svg>

            {/* Empty State / Call to Action */}
            <div className="absolute bottom-8 right-8">
                <Button className="bg-violet-600 hover:bg-violet-700 shadow-lg">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Node
                </Button>
            </div>
        </div>
    );
}
