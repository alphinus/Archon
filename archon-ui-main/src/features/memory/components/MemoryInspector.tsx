/**
 * Memory Inspector Component
 * 
 * Main container with tabbed interface for exploring memory layers.
 */

import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card } from '@/components/ui/Card';
import { SessionMemoryPanel } from './SessionMemoryPanel';
import { WorkingMemoryPanel } from './WorkingMemoryPanel';
import { LongTermMemoryPanel } from './LongTermMemoryPanel';
import { MemoryStatsCard } from './MemoryStatsCard';

interface MemoryInspectorProps {
    userId: string;
    sessionId: string;
}

export function MemoryInspector({ userId, sessionId }: MemoryInspectorProps) {
    const [activeTab, setActiveTab] = useState('session');

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main content - 2 columns */}
            <div className="lg:col-span-2">
                <Card className="bg-gray-900 border-gray-800 p-6">
                    <div className="mb-4">
                        <h2 className="text-xl font-semibold text-white mb-1">Memory Layers</h2>
                        <p className="text-sm text-gray-400">
                            View and manage memory across all layers
                        </p>
                    </div>

                    <Tabs value={activeTab} onValueChange={setActiveTab}>
                        <TabsList className="grid w-full grid-cols-3 bg-gray-800">
                            <TabsTrigger
                                value="session"
                                className="data-[state=active]:bg-violet-600 data-[state=active]:text-white"
                            >
                                Session
                            </TabsTrigger>
                            <TabsTrigger
                                value="working"
                                className="data-[state=active]:bg-violet-600 data-[state=active]:text-white"
                            >
                                Working
                            </TabsTrigger>
                            <TabsTrigger
                                value="longterm"
                                className="data-[state=active]:bg-violet-600 data-[state=active]:text-white"
                            >
                                Long-Term
                            </TabsTrigger>
                        </TabsList>

                        <TabsContent value="session" className="mt-6">
                            <SessionMemoryPanel />
                        </TabsContent>

                        <TabsContent value="working" className="mt-6">
                            <WorkingMemoryPanel />
                        </TabsContent>

                        <TabsContent value="longterm" className="mt-6">
                            <LongTermMemoryPanel />
                        </TabsContent>
                    </Tabs>
                </Card>
            </div>

            {/* Sidebar - 1 column */}
            <div className="space-y-6">
                <MemoryStatsCard />
            </div>
        </div>
    );
}
