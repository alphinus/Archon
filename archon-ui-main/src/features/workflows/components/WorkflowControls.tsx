/**
 * Workflow Controls
 * 
 * Toolbar for managing workflow state (Save, Run, etc.)
 */

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Play, Save, Settings } from 'lucide-react';

export function WorkflowControls() {
    return (
        <div className="h-14 border-b border-gray-800 bg-gray-900 px-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
                <Input
                    className="bg-transparent border-none text-white font-semibold w-64 focus-visible:ring-0 px-0 text-lg"
                    defaultValue="Untitled Workflow"
                />
                <span className="px-2 py-0.5 rounded-full bg-yellow-500/10 text-yellow-500 text-xs border border-yellow-500/20">
                    Draft
                </span>
            </div>

            <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white">
                    <Settings className="h-4 w-4 mr-2" />
                    Settings
                </Button>
                <Button variant="outline" size="sm" className="border-gray-700 text-gray-300 hover:bg-gray-800">
                    <Save className="h-4 w-4 mr-2" />
                    Save
                </Button>
                <Button size="sm" className="bg-green-600 hover:bg-green-700 text-white">
                    <Play className="h-4 w-4 mr-2" />
                    Run
                </Button>
            </div>
        </div>
    );
}
