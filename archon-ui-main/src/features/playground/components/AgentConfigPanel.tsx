/**
 * Agent Configuration Panel
 * 
 * Settings for the active agent.
 */

import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Textarea } from '@/components/ui/textarea';
import { Settings2 } from 'lucide-react';

interface AgentConfigPanelProps {
    selectedAgentId: string;
    onAgentChange: (id: string) => void;
}

export function AgentConfigPanel({ selectedAgentId, onAgentChange }: AgentConfigPanelProps) {
    return (
        <div className="flex flex-col h-full bg-gray-900 border-t border-gray-800">
            <div className="p-3 border-b border-gray-800 flex items-center gap-2">
                <Settings2 className="h-4 w-4 text-gray-400" />
                <span className="font-semibold text-white text-sm">Configuration</span>
            </div>

            <div className="p-4 space-y-4 overflow-y-auto">
                <div className="space-y-2">
                    <Label className="text-xs text-gray-400">Select Agent</Label>
                    <Select value={selectedAgentId} onValueChange={onAgentChange}>
                        <SelectTrigger className="bg-gray-950 border-gray-700">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="agent_001">Customer Support Agent</SelectItem>
                            <SelectItem value="agent_002">Code Reviewer</SelectItem>
                            <SelectItem value="agent_003">Data Analyst</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                <div className="space-y-2">
                    <Label className="text-xs text-gray-400">Model</Label>
                    <Select defaultValue="gpt-4-turbo">
                        <SelectTrigger className="bg-gray-950 border-gray-700">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="gpt-4-turbo">GPT-4 Turbo</SelectItem>
                            <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                            <SelectItem value="claude-3-opus">Claude 3 Opus</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                <div className="space-y-2">
                    <div className="flex justify-between">
                        <Label className="text-xs text-gray-400">Temperature</Label>
                        <span className="text-xs text-gray-500">0.7</span>
                    </div>
                    <Slider defaultValue={[0.7]} max={1} step={0.1} className="py-2" />
                </div>

                <div className="space-y-2">
                    <Label className="text-xs text-gray-400">System Prompt</Label>
                    <Textarea
                        className="bg-gray-950 border-gray-700 min-h-[100px] text-xs font-mono"
                        defaultValue="You are a helpful AI assistant. You have access to various tools..."
                    />
                </div>
            </div>
        </div>
    );
}
