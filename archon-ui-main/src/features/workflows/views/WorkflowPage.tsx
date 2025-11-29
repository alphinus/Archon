/**
 * Workflow Page
 * 
 * Main page component for Workflow Builder.
 * Route: /workflows
 */

import { WorkflowBuilder } from '../components/WorkflowBuilder';

export function WorkflowPage() {
    return (
        <div className="container mx-auto px-4 py-6 h-[calc(100vh-4rem)] flex flex-col">
            <div className="mb-4 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white">Workflow Builder</h1>
                    <p className="text-gray-400 mt-1">
                        Design and automate agent processes visually
                    </p>
                </div>
            </div>

            <div className="flex-1 min-h-0 border border-gray-800 rounded-lg bg-gray-900 overflow-hidden">
                <WorkflowBuilder />
            </div>
        </div>
    );
}
