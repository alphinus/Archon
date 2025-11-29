/**
 * Workflow TypeScript Types
 */

export interface WorkflowNode {
    id: string;
    type: 'trigger' | 'action' | 'condition' | 'end';
    position: { x: number; y: number };
    data: {
        label: string;
        config?: Record<string, any>;
    };
}

export interface WorkflowEdge {
    id: string;
    source: string;
    target: string;
    label?: string;
}

export interface Workflow {
    id: string;
    name: string;
    description: string;
    nodes: WorkflowNode[];
    edges: WorkflowEdge[];
    created_at: string;
    updated_at: string;
    status: 'draft' | 'active' | 'archived';
}
