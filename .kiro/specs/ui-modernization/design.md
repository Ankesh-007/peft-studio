# UI Integration & Modernization Design Document

## Overview

This design document outlines the technical architecture and implementation approach for modernizing PEFT Studio's user interface and completing the integration between the comprehensive backend API and frontend components. The design focuses on exposing existing backend capabilities through an intuitive, modern UI while maintaining performance, accessibility, and maintainability.

### Design Goals

1. **Complete Backend Integration**: Expose all backend API capabilities through the UI
2. **Real-Time Updates**: Implement WebSocket connections for live training monitoring
3. **Modern Component Library**: Build reusable, accessible components with consistent styling
4. **Responsive Design**: Ensure the application works seamlessly across devices
5. **Performance Optimization**: Maintain smooth interactions even with large datasets
6. **Accessibility Compliance**: Meet WCAG 2.1 AA standards for all components

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React + TypeScript)            │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Components  │  │    Hooks     │  │   Context    │     │
│  │   Library    │  │  (Custom)    │  │  Providers   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  WebSocket   │  │  API Client  │  │    State     │     │
│  │   Manager    │  │  (REST/HTTP) │  │  Management  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI + Python)                │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  WebSocket   │  │  REST API    │  │   Services   │     │
│  │   Endpoints  │  │  Endpoints   │  │    Layer     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Component Architecture

```
src/
├── components/
│   ├── ui/                    # Base component library
│   │   ├── Button/
│   │   ├── Input/
│   │   ├── Select/
│   │   ├── Toast/
│   │   ├── Modal/
│   │   ├── Dropdown/
│   │   └── ...
│   ├── forms/                 # Form-specific components
│   │   ├── MultiSelect/
│   │   ├── Slider/
│   │   ├── CodeEditor/
│   │   ├── FileUpload/
│   │   └── ...
│   ├── layout/                # Layout components
│   │   ├── Sidebar/
│   │   ├── TopBar/
│   │   ├── Breadcrumbs/
│   │   └── ...
│   ├── features/              # Feature-specific components
│   │   ├── training/
│   │   ├── deployment/
│   │   ├── experiments/
│   │   └── ...
│   └── shared/                # Shared utility components
│       ├── LoadingStates/
│       ├── ErrorBoundary/
│       └── ...
├── hooks/
│   ├── useWebSocket.ts
│   ├── useApi.ts
│   ├── useToast.ts
│   └── ...
├── contexts/
│   ├── ToastContext.tsx
│   ├── ThemeContext.tsx
│   └── ...
├── services/
│   ├── websocket.ts
│   ├── api.ts
│   └── ...
└── types/
    ├── api.ts
    ├── components.ts
    └── ...
```

## Components and Interfaces

### 1. WebSocket Integration

#### WebSocket Manager Service

```typescript
// services/websocket.ts
interface WebSocketMessage {
  type: 'training_update' | 'deployment_status' | 'system_alert';
  data: any;
  timestamp: string;
}

class WebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();

  connect(url: string): void;
  disconnect(): void;
  subscribe(event: string, callback: (data: any) => void): () => void;
  send(message: WebSocketMessage): void;
  private handleReconnect(): void;
  private handleMessage(event: MessageEvent): void;
}
```

#### useWebSocket Hook

```typescript
// hooks/useWebSocket.ts
interface UseWebSocketOptions {
  url: string;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Error) => void;
  reconnect?: boolean;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  subscribe: (event: string, callback: (data: any) => void) => () => void;
  send: (message: WebSocketMessage) => void;
  disconnect: () => void;
}

function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn;
```

### 2. Toast Notification System

#### Toast Context

```typescript
// contexts/ToastContext.tsx
interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  duration?: number;
  dismissible?: boolean;
}

interface ToastContextValue {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => string;
  removeToast: (id: string) => void;
  clearAll: () => void;
}
```

#### Toast Component

```typescript
// components/ui/Toast/Toast.tsx
interface ToastProps {
  toast: Toast;
  onDismiss: (id: string) => void;
}

const Toast: React.FC<ToastProps> = ({ toast, onDismiss }) => {
  // Implementation with animations, accessibility
};
```

### 3. Enhanced Form Controls

#### MultiSelect Component

```typescript
// components/forms/MultiSelect/MultiSelect.tsx
interface MultiSelectOption {
  value: string;
  label: string;
  disabled?: boolean;
  group?: string;
}

interface MultiSelectProps {
  options: MultiSelectOption[];
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
  searchable?: boolean;
  maxSelected?: number;
  disabled?: boolean;
  error?: string;
  'aria-label': string;
}
```

#### Slider Component

```typescript
// components/forms/Slider/Slider.tsx
interface SliderProps {
  min: number;
  max: number;
  step?: number;
  value: number;
  onChange: (value: number) => void;
  label?: string;
  showValue?: boolean;
  formatValue?: (value: number) => string;
  disabled?: boolean;
  'aria-label': string;
}
```

#### CodeEditor Component

```typescript
// components/forms/CodeEditor/CodeEditor.tsx
interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language: 'json' | 'python' | 'yaml' | 'javascript';
  height?: string;
  readOnly?: boolean;
  showLineNumbers?: boolean;
  theme?: 'dark' | 'light';
  error?: string;
}
```

### 4. Enhanced Training Configuration

#### Training Configuration Form

```typescript
// components/features/training/TrainingConfigForm.tsx
interface TrainingConfig {
  algorithm: 'lora' | 'ia3' | 'prefix_tuning' | 'p_tuning' | 'prompt_tuning';
  algorithmParams: {
    r?: number;
    lora_alpha?: number;
    lora_dropout?: number;
    target_modules?: string[];
    // ... other algorithm-specific params
  };
  quantization: '4bit' | '8bit' | 'none';
  gradientCheckpointing: boolean;
  optimizer: {
    type: 'adamw' | 'sgd' | 'adafactor';
    learningRate: number;
    weightDecay: number;
    warmupSteps: number;
    gradientAccumulationSteps: number;
  };
  training: {
    batchSize: number;
    epochs: number;
    maxSteps?: number;
    evalSteps: number;
    saveSteps: number;
  };
}

interface TrainingConfigFormProps {
  initialConfig?: Partial<TrainingConfig>;
  onSubmit: (config: TrainingConfig) => void;
  onCancel: () => void;
}
```

### 5. Real-Time Training Monitor

#### Training Monitor with WebSocket

```typescript
// components/features/training/TrainingMonitor.tsx
interface TrainingMetrics {
  step: number;
  epoch: number;
  loss: number;
  learningRate: number;
  gpuMemory: number;
  gpuUtilization: number;
  tokensPerSecond: number;
  estimatedTimeRemaining: number;
}

interface TrainingMonitorProps {
  runId: string;
  runName: string;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
}

const TrainingMonitor: React.FC<TrainingMonitorProps> = (props) => {
  const { isConnected, subscribe } = useWebSocket({
    url: `ws://localhost:8000/ws/training/${props.runId}`,
  });

  const [metrics, setMetrics] = useState<TrainingMetrics[]>([]);

  useEffect(() => {
    const unsubscribe = subscribe('training_update', (data) => {
      setMetrics(prev => [...prev, data]);
    });
    return unsubscribe;
  }, [subscribe]);

  // Render implementation
};
```

### 6. Sidebar Navigation

#### Collapsible Sidebar

```typescript
// components/layout/Sidebar/Sidebar.tsx
interface NavItem {
  id: string;
  label: string;
  icon: React.ComponentType;
  path: string;
  badge?: number;
  children?: NavItem[];
}

interface SidebarProps {
  items: NavItem[];
  collapsed: boolean;
  onToggle: () => void;
  activeItem: string;
  onNavigate: (path: string) => void;
}
```

### 7. Settings Panel

#### Settings with Tabs

```typescript
// components/Settings/Settings.tsx
interface SettingsCategory {
  id: string;
  label: string;
  icon: React.ComponentType;
  component: React.ComponentType<SettingsCategoryProps>;
}

interface SettingsCategoryProps {
  settings: any;
  onChange: (key: string, value: any) => void;
  onSave: () => void;
}

const settingsCategories: SettingsCategory[] = [
  { id: 'appearance', label: 'Appearance', icon: Palette, component: AppearanceSettings },
  { id: 'notifications', label: 'Notifications', icon: Bell, component: NotificationSettings },
  { id: 'training', label: 'Training Defaults', icon: Zap, component: TrainingSettings },
  { id: 'storage', label: 'Storage', icon: Database, component: StorageSettings },
  { id: 'privacy', label: 'Privacy', icon: Shield, component: PrivacySettings },
  { id: 'advanced', label: 'Advanced', icon: Settings, component: AdvancedSettings },
];
```

## Data Models

### API Response Types

```typescript
// types/api.ts
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  metadata?: {
    timestamp: string;
    requestId: string;
  };
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

interface TrainingRun {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed';
  config: TrainingConfig;
  metrics: TrainingMetrics[];
  startTime: string;
  endTime?: string;
  checkpoints: Checkpoint[];
}

interface Deployment {
  id: string;
  name: string;
  modelId: string;
  status: 'deploying' | 'active' | 'failed' | 'stopped';
  endpoint: string;
  provider: string;
  metrics: DeploymentMetrics;
  cost: CostEstimate;
  createdAt: string;
}

interface Experiment {
  id: string;
  name: string;
  description?: string;
  tags: string[];
  runs: TrainingRun[];
  bestRun?: string;
  createdAt: string;
  updatedAt: string;
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: WebSocket Reconnection Reliability
*For any* WebSocket connection that is disconnected, the system should automatically attempt reconnection with exponential backoff, and all subscribed listeners should continue to receive messages once reconnected
**Validates: Requirements 2.8**

### Property 2: Toast Notification Uniqueness
*For any* set of toast notifications displayed simultaneously, each toast should have a unique ID and be visually distinguishable from others
**Validates: Requirements 4.5**

### Property 3: Form Validation Consistency
*For any* form input that fails validation, the error message should be displayed immediately and the form should not be submittable until all validations pass
**Validates: Requirements 1.7, 13.8**

### Property 4: Settings Persistence Round-Trip
*For any* settings configuration that is saved, retrieving the settings should return the exact same values that were saved
**Validates: Requirements 5.8**

### Property 5: Component Accessibility Compliance
*For any* interactive component, it should have proper ARIA labels, keyboard navigation support, and focus management
**Validates: Requirements 10.8, 15.1, 15.2**

### Property 6: Responsive Layout Adaptation
*For any* viewport width change, the layout should adapt within 300ms without breaking visual hierarchy or causing content overflow
**Validates: Requirements 12.8**

### Property 7: Real-Time Metric Update Ordering
*For any* sequence of training metrics received via WebSocket, they should be displayed in chronological order based on step number
**Validates: Requirements 2.2, 2.3**

### Property 8: Offline Queue Preservation
*For any* operation queued while offline, it should remain in the queue until successfully synced or explicitly cancelled by the user
**Validates: Requirements 9.2, 9.6**

### Property 9: Navigation State Consistency
*For any* navigation action, the active navigation item should match the current route and be visually highlighted
**Validates: Requirements 3.2**

### Property 10: Virtual Scrolling Performance
*For any* list with more than 100 items, only visible items plus a buffer should be rendered in the DOM
**Validates: Requirements 14.1**

## Error Handling

### Error Boundary Strategy

```typescript
// components/shared/ErrorBoundary/ErrorBoundary.tsx
interface ErrorBoundaryProps {
  fallback?: React.ComponentType<{ error: Error; reset: () => void }>;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  children: React.ReactNode;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  // Catches React component errors
  // Logs to error service
  // Displays fallback UI
  // Provides reset functionality
}
```

### API Error Handling

```typescript
// services/api.ts
class ApiError extends Error {
  constructor(
    public code: string,
    public message: string,
    public status: number,
    public details?: any
  ) {
    super(message);
  }
}

async function handleApiError(response: Response): Promise<never> {
  const data = await response.json();
  throw new ApiError(
    data.error?.code || 'UNKNOWN_ERROR',
    data.error?.message || 'An unknown error occurred',
    response.status,
    data.error?.details
  );
}
```

### User-Friendly Error Messages

```typescript
// lib/errorMessages.ts
const errorMessages: Record<string, string> = {
  'NETWORK_ERROR': 'Unable to connect to the server. Please check your internet connection.',
  'VALIDATION_ERROR': 'Please check your input and try again.',
  'UNAUTHORIZED': 'Your session has expired. Please log in again.',
  'NOT_FOUND': 'The requested resource was not found.',
  'SERVER_ERROR': 'Something went wrong on our end. Please try again later.',
};

function getUserFriendlyError(error: ApiError): string {
  return errorMessages[error.code] || error.message;
}
```

## Testing Strategy

### Unit Testing

**Component Testing**
- Test each component in isolation with React Testing Library
- Test all prop combinations and variants
- Test accessibility features (ARIA labels, keyboard navigation)
- Test error states and loading states

**Hook Testing**
- Test custom hooks with @testing-library/react-hooks
- Test WebSocket connection, reconnection, and message handling
- Test API client with mocked fetch responses
- Test form validation logic

**Service Testing**
- Test WebSocket manager connection lifecycle
- Test API client request/response handling
- Test error handling and retry logic

### Integration Testing

**Feature Flow Testing**
- Test complete user flows (e.g., create training run → monitor → view results)
- Test WebSocket integration with backend
- Test form submission and API integration
- Test navigation and routing

**WebSocket Testing**
```typescript
// tests/integration/websocket.test.ts
describe('WebSocket Integration', () => {
  it('should receive real-time training updates', async () => {
    const mockServer = new WS('ws://localhost:8000/ws/training/test-run');
    
    render(<TrainingMonitor runId="test-run" />);
    
    await waitFor(() => {
      expect(mockServer).toHaveReceivedMessages([
        { type: 'subscribe', event: 'training_update' }
      ]);
    });
    
    mockServer.send({
      type: 'training_update',
      data: { step: 100, loss: 0.5 }
    });
    
    expect(screen.getByText('Step: 100')).toBeInTheDocument();
    expect(screen.getByText('Loss: 0.5')).toBeInTheDocument();
  });
});
```

### Accessibility Testing

**Automated Testing**
```typescript
// tests/accessibility/components.test.ts
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

describe('Component Accessibility', () => {
  it('should have no accessibility violations', async () => {
    const { container } = render(<TrainingConfigForm />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

**Manual Testing Checklist**
- [ ] All interactive elements are keyboard accessible
- [ ] Focus indicators are visible
- [ ] Screen reader announces all important information
- [ ] Color contrast meets WCAG AA standards
- [ ] Forms have proper labels and error messages
- [ ] Modals trap focus and restore on close

### Performance Testing

**Metrics to Track**
- Initial page load time (target: < 3s on 3G)
- Time to interactive (target: < 5s)
- Component render time (target: < 16ms for 60fps)
- WebSocket message processing time (target: < 100ms)
- Virtual scroll performance (target: smooth scrolling with 10,000+ items)

**Performance Testing Tools**
- Lighthouse for page load metrics
- React DevTools Profiler for component performance
- Chrome DevTools Performance tab for runtime analysis

## Performance Optimization

### Code Splitting

```typescript
// Lazy load route components
const Dashboard = lazy(() => import('./components/Dashboard'));
const TrainingMonitor = lazy(() => import('./components/TrainingMonitor'));
const Settings = lazy(() => import('./components/Settings'));

// Lazy load heavy dependencies
const CodeEditor = lazy(() => import('./components/forms/CodeEditor'));
```

### Memoization Strategy

```typescript
// Memoize expensive computations
const processedMetrics = useMemo(() => {
  return metrics.map(m => ({
    ...m,
    formattedLoss: m.loss.toFixed(4),
    formattedTime: formatDuration(m.timestamp)
  }));
}, [metrics]);

// Memoize components that receive stable props
const MemoizedMetricCard = React.memo(MetricCard, (prev, next) => {
  return prev.value === next.value && prev.label === next.label;
});
```

### Virtual Scrolling

```typescript
// Use react-window for large lists
import { FixedSizeList } from 'react-window';

const VirtualizedList: React.FC<{ items: any[] }> = ({ items }) => {
  return (
    <FixedSizeList
      height={600}
      itemCount={items.length}
      itemSize={80}
      width="100%"
    >
      {({ index, style }) => (
        <div style={style}>
          <ListItem item={items[index]} />
        </div>
      )}
    </FixedSizeList>
  );
};
```

### Request Caching

```typescript
// Implement SWR-style caching
const cache = new Map<string, { data: any; timestamp: number }>();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

async function fetchWithCache<T>(url: string): Promise<T> {
  const cached = cache.get(url);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }
  
  const data = await fetch(url).then(r => r.json());
  cache.set(url, { data, timestamp: Date.now() });
  return data;
}
```

## Security Considerations

### Input Validation

```typescript
// Validate all user inputs before sending to API
function validateTrainingConfig(config: TrainingConfig): ValidationResult {
  const errors: Record<string, string> = {};
  
  if (config.optimizer.learningRate <= 0 || config.optimizer.learningRate > 1) {
    errors.learningRate = 'Learning rate must be between 0 and 1';
  }
  
  if (config.training.batchSize < 1 || config.training.batchSize > 128) {
    errors.batchSize = 'Batch size must be between 1 and 128';
  }
  
  return {
    valid: Object.keys(errors).length === 0,
    errors
  };
}
```

### XSS Prevention

```typescript
// Sanitize user-generated content
import DOMPurify from 'dompurify';

function sanitizeHtml(html: string): string {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],
    ALLOWED_ATTR: ['href']
  });
}
```

### Secure WebSocket Connection

```typescript
// Use WSS in production
const wsUrl = process.env.NODE_ENV === 'production'
  ? `wss://${window.location.host}/ws`
  : `ws://localhost:8000/ws`;

// Include authentication token
const ws = new WebSocket(`${wsUrl}?token=${authToken}`);
```

## Deployment Considerations

### Environment Configuration

```typescript
// config/environment.ts
interface EnvironmentConfig {
  apiUrl: string;
  wsUrl: string;
  enableTelemetry: boolean;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
}

const config: EnvironmentConfig = {
  apiUrl: process.env.VITE_API_URL || 'http://localhost:8000',
  wsUrl: process.env.VITE_WS_URL || 'ws://localhost:8000/ws',
  enableTelemetry: process.env.VITE_ENABLE_TELEMETRY === 'true',
  logLevel: (process.env.VITE_LOG_LEVEL as any) || 'info',
};
```

### Build Optimization

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'chart-vendor': ['recharts', 'd3'],
          'form-vendor': ['react-hook-form', 'zod'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
});
```

## Migration Strategy

### Phase 1: Foundation (Week 1-2)
1. Set up component library structure
2. Implement WebSocket manager and hooks
3. Create toast notification system
4. Build enhanced form controls
5. Update sidebar navigation

### Phase 2: Feature Integration (Week 3-4)
1. Enhance training configuration UI
2. Integrate real-time training monitor
3. Build deployment management UI
4. Implement experiment tracking
5. Create comprehensive settings panel

### Phase 3: Polish & Optimization (Week 5-6)
1. Implement responsive design
2. Add accessibility features
3. Optimize performance
4. Add animations and transitions
5. Complete testing coverage

## Conclusion

This design provides a comprehensive architecture for modernizing PEFT Studio's UI while maintaining backward compatibility and ensuring high performance, accessibility, and maintainability. The modular component structure allows for incremental implementation, and the clear separation of concerns makes the codebase easy to understand and extend.
