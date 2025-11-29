/**
 * Memory Page
 * 
 * Main page component for Memory Inspector.
 * Route: /memory
 */

import { MemoryInspector } from '../components/MemoryInspector';

export function MemoryPage() {
    // TODO: Get user_id and session_id from context/URL
    const userId = 'test_user_001';
    const sessionId = 'test_session_001';

    return (
        <div className="container mx-auto px-4 py-6">
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-white">Memory Inspector</h1>
                <p className="text-gray-400 mt-2">
                    Explore Archon's 4-layer memory system
                </p>
            </div>

            <MemoryInspector userId={userId} sessionId={sessionId} />
        </div>
    );
}
