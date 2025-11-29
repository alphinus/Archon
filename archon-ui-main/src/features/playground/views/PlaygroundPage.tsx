/**
 * Playground Page
 * 
 * Main page component for Agent Playground.
 * Route: /playground
 */

import { AgentPlayground } from '../components/AgentPlayground';

export function PlaygroundPage() {
    return (
        <div className="container mx-auto px-4 py-6 h-[calc(100vh-4rem)] flex flex-col">
            <div className="mb-4">
                <h1 className="text-3xl font-bold text-white">Agent Playground</h1>
                <p className="text-gray-400 mt-1">
                    Test and debug your agents in real-time
                </p>
            </div>

            <div className="flex-1 min-h-0">
                <AgentPlayground />
            </div>
        </div>
    );
}
