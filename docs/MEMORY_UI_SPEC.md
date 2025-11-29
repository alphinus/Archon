# 🎨 MEMORY INSPECTOR UI - TECHNICAL SPECIFICATION

**Feature:** Memory Inspector  
**Route:** `/memory`  
**Status:** 📋 Design Complete → Ready for Implementation  
**Priority:** P0 (Critical)

---

## 🎯 OVERVIEW

A comprehensive UI for visualizing and managing Archon's 4-layer memory system. Users can inspect Session Memory (Redis), Working Memory (Postgres), Long-Term Memory (Postgres), and assembled context in real-time.

**Design Philosophy:** Follow existing Archon UI patterns (dark theme, card-based, Radix UI components, responsive).

---

## 📐 COMPONENT ARCHITECTURE

```
src/features/memory/
├── components/
│   ├── MemoryInspector.tsx          # Root component (container)
│   ├── SessionMemoryPanel.tsx       # Tab 1: Session messages
│   ├── WorkingMemoryPanel.tsx       # Tab 2: Working memory entries
│   ├── LongTermMemoryPanel.tsx      # Tab 3: Long-term facts
│   ├── MemoryStatsCard.tsx          # Statistics dashboard
│   ├── ContextPreview.tsx           # Assembled context JSON viewer
│   ├── AALControls.tsx              # Memory settings panel
│   ├── MemorySearchBar.tsx          # Search/filter component
│   └── MemoryEntryCard.tsx          # Reusable entry card
├── hooks/
│   ├── useMemoryData.ts             # React Query: fetch memories
│   ├── useMemoryStats.ts            # React Query: fetch stats
│   ├── useMemorySettings.ts         # Zustand: AAL settings
│   └── useMemorySearch.ts           # Client-side search logic
├── services/
│   └── memoryService.ts             # API client wrapper
├── types/
│   └── memory.types.ts              # TypeScript interfaces
├── utils/
│   └── memoryFormatters.ts          # Date, token formatting
└── views/
    └── MemoryPage.tsx               # Page wrapper
```

---

## 🧩 COMPONENT SPECIFICATIONS

### 1. MemoryInspector.tsx

**Purpose:** Main container with tabbed interface

**Dependencies:**
- `@radix-ui/react-tabs`
- `useMemoryData` hook

**Structure:**
```tsx
export function MemoryInspector({ userId, sessionId }: Props) {
  const [activeTab, setActiveTab] = useState('session');
  const { data, isLoading } = useMemoryData(userId, sessionId);
  
  return (
    <div className="memory-inspector">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="session">Session</TabsTrigger>
          <TabsTrigger value="working">Working</TabsTrigger>
          <TabsTrigger value="longterm">Long-Term</TabsTrigger>
        </TabsList>
        
        <TabsContent value="session">
          <SessionMemoryPanel data={data?.session} />
        </TabsContent>
        <TabsContent value="working">
          <WorkingMemoryPanel data={data?.working} />
        </TabsContent>
        <TabsContent value="longterm">
          <LongTermMemoryPanel data={data?.longterm} />
        </TabsContent>
      </Tabs>
      
      <MemoryStatsCard userId={userId} />
      <AALControls />
    </div>
  );
}
```

**Styling:**
- Dark background (#0a0a0a)
- Tabs with violet accent (#8b5cf6)
- Responsive grid: 2 columns (desktop), 1 column (mobile)

---

### 2. SessionMemoryPanel.tsx

**Purpose:** Display conversation messages from Redis

**API:** `GET /api/memory/session/{session_id}`

**Data Structure:**
```typescript
interface SessionMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}
```

**UI:**
```tsx
export function SessionMemoryPanel({ data }: Props) {
  if (!data?.length) return <EmptyState />;
  
  return (
    <div className="session-panel">
      {data.map((msg, idx) => (
        <MessageBubble key={idx} role={msg.role} content={msg.content} timestamp={msg.timestamp} />
      ))}
    </div>
  );
}
```

**Styling:**
- Chat-bubble layout
- User messages: right-aligned, blue gradient
- Assistant messages: left-aligned, gray
- Timestamps: subtle, small font
- Max height: 600px, scrollable

---

### 3. WorkingMemoryPanel.tsx

**Purpose:** Display recent memory entries (7-30 days TTL)

**API:** `GET /api/memory/working?user_id={id}`

**Data Structure:**
```typescript
interface WorkingMemoryEntry {
  id: string;
  user_id: string;
  memory_type: string;
  content: string;
  metadata: Record<string, any>;
  created_at: string;
  expires_at: string;
}
```

**UI:**
```tsx
export function WorkingMemoryPanel({ data }: Props) {
  const [searchQuery, setSearchQuery] = useState('');
  const filtered = useMemorySearch(data, searchQuery);
  
  return (
    <div className="working-panel">
      <MemorySearchBar value={searchQuery} onChange={setSearchQuery} />
      <div className="memory-grid">
        {filtered.map(entry => (
          <MemoryEntryCard key={entry.id} entry={entry} />
        ))}
      </div>
    </div>
  );
}
```

**Styling:**
- Grid layout: 2 columns (desktop), 1 column (tablet/mobile)
- Cards: dark (#1a1a1a), rounded, hover effect
- Each card shows: type badge, content (truncated), metadata tags, timestamp
- Search bar: top-right, live filtering

---

### 4. LongTermMemoryPanel.tsx

**Purpose:** Display important facts (persistent)

**API:** `GET /api/memory/longterm?user_id={id}`

**Data Structure:**
```typescript
interface LongTermMemoryEntry {
  id: string;
  user_id: string;
  memory_type: string;
  content: string;
  importance: number; // 0.0 - 1.0
  metadata: Record<string, any>;
  created_at: string;
  last_accessed: string;
  access_count: number;
}
```

**UI:**
```tsx
export function LongTermMemoryPanel({ data }: Props) {
  const [sortBy, setSortBy] = useState<'importance' | 'recent'>('importance');
  const sorted = useMemo(() => sortMemories(data, sortBy), [data, sortBy]);
  
  return (
    <div className="longterm-panel">
      <div className="controls">
        <Select value={sortBy} onValueChange={setSortBy}>
          <SelectTrigger>Sort by</SelectTrigger>
          <SelectContent>
            <SelectItem value="importance">Importance</SelectItem>
            <SelectItem value="recent">Recent</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div className="facts-table">
        {sorted.map(fact => (
          <FactRow key={fact.id} fact={fact} />
        ))}
      </div>
    </div>
  );
}
```

**Styling:**
- Table layout (not grid)
- Columns: Importance (bar chart), Content, Type, Last Accessed, Actions
- Importance: visual bar (0-100%), color-coded (red→yellow→green)
- Actions: View Details, Delete (with confirmation)

---

### 5. MemoryStatsCard.tsx

**Purpose:** Display memory statistics

**API:** `GET /api/memory/stats/{user_id}`

**Data Structure:**
```typescript
interface MemoryStats {
  working_count: number;
  longterm_count: number;
  total_tokens: number;
  avg_importance: number;
}
```

**UI:**
```tsx
export function MemoryStatsCard({ userId }: Props) {
  const { data } = useMemoryStats(userId);
  
  return (
    <Card className="stats-card">
      <CardHeader>
        <CardTitle>Memory Statistics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="stats-grid">
          <StatItem label="Working Memories" value={data?.working_count} />
          <StatItem label="Long-Term Facts" value={data?.longterm_count} />
          <StatItem label="Total Tokens" value={data?.total_tokens} />
          <StatItem label="Avg Importance" value={(data?.avg_importance * 100).toFixed(1) + '%'} />
        </div>
      </CardContent>
    </Card>
  );
}
```

**Styling:**
- Compact card in sidebar
- 2x2 grid for stats
- Large numbers, small labels
- Animated counter (react-countup)

---

### 6. ContextPreview.tsx

**Purpose:** Show assembled context JSON

**UI:**
```tsx
export function ContextPreview({ userId, sessionId }: Props) {
  const { data: context } = useAssembledContext(userId, sessionId);
  
  return (
    <Card className="context-preview">
      <CardHeader>
        <CardTitle>Assembled Context</CardTitle>
        <Button onClick={() => downloadJSON(context)} size="sm">
          Export JSON
        </Button>
      </CardHeader>
      <CardContent>
        <pre className="json-preview">
          {JSON.stringify(context, null, 2)}
        </pre>
      </CardContent>
    </Card>
  );
}
```

**Styling:**
- Syntax-highlighted JSON (react-json-view or prism)
- Collapsible sections
- Copy button per section
- Max height: 400px, scrollable

---

### 7. AALControls.tsx

**Purpose:** Memory system configuration

**State Management:** Zustand store

**UI:**
```tsx
export function AALControls() {
  const { settings, updateSettings } = useMemorySettings();
  
  return (
    <Card className="aal-controls">
      <CardHeader>
        <CardTitle>Memory Controls</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="controls-grid">
          <Switch
            checked={settings.memoryEnabled}
            onCheckedChange={(v) => updateSettings({ memoryEnabled: v })}
          >
            Enable Memory System
          </Switch>
          
          <Label>Max Context Tokens</Label>
          <Slider
            value={[settings.maxTokens]}
            onValueChange={(v) => updateSettings({ maxTokens: v[0] })}
            min={2000}
            max={16000}
            step={1000}
          />
          <span className="slider-value">{settings.maxTokens}</span>
        </div>
      </CardContent>
    </Card>
  );
}
```

**Settings:**
- Enable/Disable Memory: Toggle
- Max Context Tokens: Slider (2000-16000)
- Session TTL: Number input (1-60 minutes)
- Working TTL: Number input (7-90 days)
- Display in sidebar (always visible)

---

## 🔌 API INTEGRATION

### memoryService.ts

```typescript
import { apiClient } from '@/lib/apiClient';

export const memoryService = {
  async getSessionMemory(sessionId: string) {
    return apiClient.get(`/api/memory/session/${sessionId}`);
  },
  
  async getWorkingMemory(userId: string, limit = 50) {
    return apiClient.get(`/api/memory/working`, {
      params: { user_id: userId, limit }
    });
  },
  
  async getLongTermMemory(userId: string, minImportance = 0.5) {
    return apiClient.get(`/api/memory/longterm`, {
      params: { user_id: userId, min_importance: minImportance }
    });
  },
  
  async getStats(userId: string) {
    return apiClient.get(`/api/memory/stats/${userId}`);
  }
};
```

---

## 🪝 HOOKS

### useMemoryData.ts

```typescript
import { useQuery } from '@tanstack/react-query';
import { memoryService } from '../services/memoryService';

export function useMemoryData(userId: string, sessionId: string) {
  return useQuery({
    queryKey: ['memory', userId, sessionId],
    queryFn: async () => {
      const [session, working, longterm] = await Promise.all([
        memoryService.getSessionMemory(sessionId),
        memoryService.getWorkingMemory(userId),
        memoryService.getLongTermMemory(userId)
      ]);
      
      return { session, working, longterm };
    },
    refetchInterval: 30000, // Refresh every 30s
    staleTime: 10000
  });
}
```

### useMemorySettings.ts

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface MemorySettings {
  memoryEnabled: boolean;
  maxTokens: number;
  sessionTTL: number;
  workingTTL: number;
}

export const useMemorySettings = create<MemorySettings>()(
  persist(
    (set) => ({
      memoryEnabled: true,
      maxTokens: 8000,
      sessionTTL: 30,
      workingTTL: 30,
      updateSettings: (partial: Partial<MemorySettings>) => set(partial)
    }),
    { name: 'archon-memory-settings' }
  )
);
```

---

## 🎨 STYLING GUIDELINES

### Colors (Matching Archon Theme)
```css
:root {
  --bg-primary: #0a0a0a;
  --bg-secondary: #1a1a1a;
  --bg-tertiary: #2a2a2a;
  
  --text-primary: #ffffff;
  --text-secondary: #a0a0a0;
  --text-muted: #6b6b6b;
  
  --accent-violet: #8b5cf6;
  --accent-blue: #3b82f6;
  --accent-green: #10b981;
  --accent-red: #ef4444;
  
  --border: #2a2a2a;
  --border-hover: #3a3a3a;
}
```

### Component Classes
```css
.memory-inspector {
  @apply space-y-6 p-6;
}

.memory-grid {
  @apply grid grid-cols-1 md:grid-cols-2 gap-4;
}

.memory-entry-card {
  @apply bg-secondary rounded-lg p-4 border border-border hover:border-border-hover transition-colors;
}

.message-bubble {
  @apply p-3 rounded-lg max-w-[80%];
}

.message-bubble.user {
  @apply ml-auto bg-gradient-to-r from-violet-600 to-blue-600 text-white;
}

.message-bubble.assistant {
  @apply mr-auto bg-secondary text-text-primary;
}
```

---

## 📱 RESPONSIVE DESIGN

### Breakpoints
- Mobile: < 640px (1 column)
- Tablet: 640px - 1024px (1-2 columns)
- Desktop: > 1024px (2-3 columns)

### Mobile Optimizations
- Tabbed interface stacks vertically
- Stats card moves to top
- Search bar full-width
- Reduced padding
- Simplified cards (hide metadata)

---

## ♿ ACCESSIBILITY

### Requirements (WCAG 2.1 AA)
- All interactive elements: keyboard navigable
- Focus indicators: visible (2px offset)
- Color contrast: 4.5:1 minimum
- Screen reader labels: complete
- Skip links: available
- Reduced motion: respects `prefers-reduced-motion`

### Implementation
```tsx
<Button aria-label="Export context as JSON" onClick={handleExport}>
  Export
</Button>

<Search role="search" aria-label="Search memories" />

<TabList aria-label="Memory types">
  <Tab>Session</Tab>
  <Tab>Working</Tab>
  <Tab>Long-Term</Tab>
</TabList>
```

---

## ⚡ PERFORMANCE

### Optimization Strategies
1. **Virtual Scrolling** - Use `@tanstack/react-virtual` for long lists
2. **Lazy Loading** - Load tabs on-demand (React.lazy)
3. **Memoization** - useMemo for expensive filters/sorts
4. **Debounced Search** - 300ms delay for search input
5. **Query Caching** - TanStack Query with 30s stale time

### Bundle Size Target
- Initial: < 50KB gzipped
- With all features: < 150KB gzipped

---

## 🧪 TESTING

### Unit Tests (Vitest)
```typescript
describe('MemoryInspector', () => {
  it('renders tabs correctly', () => {
    render(<MemoryInspector userId="test" sessionId="test" />);
    expect(screen.getByText('Session')).toBeInTheDocument();
  });
  
  it('switches tabs on click', async () => {
    render(<MemoryInspector userId="test" sessionId="test" />);
    await userEvent.click(screen.getByText('Working'));
    expect(screen.getByTestId('working-panel')).toBeVisible();
  });
});
```

### Integration Tests
```typescript
describe('Memory API Integration', () => {
  it('fetches and displays session memory', async () => {
    const { user } = setupTest();
    render(<SessionMemoryPanel />);
    
    await waitFor(() => {
      expect(screen.getByText('Hello, Archon!')).toBeInTheDocument();
    });
  });
});
```

---

## 🚀 DEPLOYMENT

### Build Command
```bash
cd archon-ui-main
npm run build
```

### Environment Variables
```bash
VITE_API_URL=http://localhost:8181
VITE_WS_URL=ws://localhost:8181
```

### CDN Assets
- Fonts: Google Fonts (Inter)
- Icons: Lucide React

---

## 📋 IMPLEMENTATION CHECKLIST

- [ ] Create feature directory structure
- [ ] Implement hooks (useMemoryData, useMemoryStats, useMemorySettings)
- [ ] Build services layer (memoryService.ts)
- [ ] Define TypeScript types
- [ ] Create MemoryInspector.tsx
- [ ] Create SessionMemoryPanel.tsx
- [ ] Create WorkingMemoryPanel.tsx
- [ ] Create LongTermMemoryPanel.tsx
- [ ] Create MemoryStatsCard.tsx
- [ ] Create ContextPreview.tsx
- [ ] Create AALControls.tsx
- [ ] Create MemoryPage.tsx
- [ ] Add route to App.tsx
- [ ] Add navigation link to MainLayout
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Accessibility audit
- [ ] Performance testing
- [ ] User testing
- [ ] Documentation

---

**Estimated Time:** 5-7 days (1 developer)  
**Dependencies:** Backend Memory API endpoints (already complete)  
**Blockers:** None

**This specification is ready for implementation. Start with hooks → services → components → page.**
