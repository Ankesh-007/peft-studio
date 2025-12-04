# Component Library Documentation

## Overview

PEFT Studio's component library provides a comprehensive set of reusable, accessible UI components built with React and TypeScript. All components follow WCAG 2.1 AA accessibility standards and include proper ARIA labels, keyboard navigation, and screen reader support.

## Base Components

### AccessibleButton

A fully accessible button component with multiple variants and states.

**Props:**
```typescript
interface AccessibleButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  'aria-label': string;
  onClick?: () => void;
  children: React.ReactNode;
}
```

**Usage:**
```tsx
import { AccessibleButton } from './components/AccessibleButton';

<AccessibleButton 
  variant="primary" 
  size="medium"
  aria-label="Save configuration"
  onClick={handleSave}
>
  Save
</AccessibleButton>
```

**Variants:**
- `primary` - Blue background, white text (default)
- `secondary` - Gray background, dark text
- `ghost` - Transparent background, colored text
- `danger` - Red background, white text

### AccessibleInput

Text input component with validation and error states.

**Props:**
```typescript
interface AccessibleInputProps {
  type?: 'text' | 'number' | 'email' | 'password';
  value: string;
  onChange: (value: string) => void;
  label: string;
  error?: string;
  helperText?: string;
  disabled?: boolean;
  required?: boolean;
  'aria-label': string;
}
```

**Usage:**
```tsx
<AccessibleInput
  type="email"
  value={email}
  onChange={setEmail}
  label="Email Address"
  error={emailError}
  helperText="We'll never share your email"
  aria-label="Enter your email address"
  required
/>
```

### AccessibleSelect

Dropdown select component with search and keyboard navigation.

**Props:**
```typescript
interface AccessibleSelectProps {
  options: Array<{ value: string; label: string }>;
  value: string;
  onChange: (value: string) => void;
  label: string;
  error?: string;
  disabled?: boolean;
  searchable?: boolean;
  'aria-label': string;
}
```

**Usage:**
```tsx
<AccessibleSelect
  options={[
    { value: 'lora', label: 'LoRA' },
    { value: 'ia3', label: 'IA3' }
  ]}
  value={algorithm}
  onChange={setAlgorithm}
  label="PEFT Algorithm"
  searchable
  aria-label="Select PEFT algorithm"
/>
```

## Advanced Form Controls

### MultiSelect

Multi-select dropdown with search, tags, and keyboard navigation.

**Props:**
```typescript
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

**Usage:**
```tsx
<MultiSelect
  options={moduleOptions}
  value={selectedModules}
  onChange={setSelectedModules}
  placeholder="Select target modules"
  searchable
  maxSelected={5}
  aria-label="Select target modules for fine-tuning"
/>
```

**Features:**
- Search functionality
- Tag display for selected items
- Keyboard navigation (Arrow keys, Enter, Escape)
- Maximum selection limit
- Disabled state

### Slider

Numeric slider with real-time value display.

**Props:**
```typescript
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

**Usage:**
```tsx
<Slider
  min={0}
  max={1}
  step={0.01}
  value={learningRate}
  onChange={setLearningRate}
  label="Learning Rate"
  showValue
  formatValue={(v) => v.toExponential(2)}
  aria-label="Adjust learning rate"
/>
```

### Toggle

Toggle switch for boolean values.

**Props:**
```typescript
interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
  'aria-label': string;
}
```

**Usage:**
```tsx
<Toggle
  checked={gradientCheckpointing}
  onChange={setGradientCheckpointing}
  label="Enable Gradient Checkpointing"
  aria-label="Toggle gradient checkpointing"
/>
```

### FileUpload

Drag-and-drop file upload with validation.

**Props:**
```typescript
interface FileUploadProps {
  accept?: string;
  maxSize?: number;
  multiple?: boolean;
  onUpload: (files: File[]) => void;
  disabled?: boolean;
  'aria-label': string;
}
```

**Usage:**
```tsx
<FileUpload
  accept=".json,.yaml"
  maxSize={10 * 1024 * 1024} // 10MB
  multiple={false}
  onUpload={handleConfigUpload}
  aria-label="Upload configuration file"
/>
```

### CodeEditor

Code editor with syntax highlighting.

**Props:**
```typescript
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

**Usage:**
```tsx
<CodeEditor
  value={configJson}
  onChange={setConfigJson}
  language="json"
  height="400px"
  showLineNumbers
  theme="dark"
/>
```

## Layout Components

### Sidebar

Collapsible navigation sidebar.

**Features:**
- Collapsible with animation
- Active state highlighting
- Tooltips when collapsed
- Keyboard shortcuts
- Mobile responsive with hamburger menu

### Breadcrumbs

Navigation breadcrumb trail.

**Props:**
```typescript
interface BreadcrumbsProps {
  items: Array<{ label: string; path: string }>;
  onNavigate: (path: string) => void;
}
```

**Usage:**
```tsx
<Breadcrumbs
  items={[
    { label: 'Home', path: '/' },
    { label: 'Training', path: '/training' },
    { label: 'Configuration', path: '/training/config' }
  ]}
  onNavigate={handleNavigate}
/>
```

### MobileNav

Mobile navigation with hamburger menu and slide-out drawer.

**Features:**
- Hamburger menu icon
- Slide-out drawer animation
- Touch-friendly controls
- Backdrop overlay

## Notification Components

### Toast

Toast notification system for user feedback.

**Usage:**
```tsx
import { useToast } from '../lib/ToastContext';

const { addToast } = useToast();

addToast({
  type: 'success',
  title: 'Configuration Saved',
  message: 'Your training configuration has been saved successfully',
  duration: 5000
});
```

**Types:**
- `success` - Green indicator
- `error` - Red indicator
- `warning` - Yellow indicator
- `info` - Blue indicator

### ConnectionStatus

WebSocket connection status indicator.

**Props:**
```typescript
interface ConnectionStatusProps {
  status: 'online' | 'offline' | 'connecting';
  reconnectAttempts?: number;
  showLabel?: boolean;
}
```

**Usage:**
```tsx
<ConnectionStatus 
  status={isConnected ? 'online' : 'offline'}
  showLabel
/>
```

## Utility Hooks

### useWebSocket

Hook for managing WebSocket connections.

**Usage:**
```tsx
const { isConnected, subscribe, send } = useWebSocket(
  'ws://localhost:8000/ws/training/run-123',
  {
    autoConnect: true,
    onConnectionChange: (connected) => console.log('Connected:', connected)
  }
);

useEffect(() => {
  const unsubscribe = subscribe((data) => {
    console.log('Received:', data);
  });
  return unsubscribe;
}, [subscribe]);
```

### useDebounce

Hook for debouncing values.

**Usage:**
```tsx
const [searchTerm, setSearchTerm] = useState('');
const debouncedSearch = useDebounce(searchTerm, 500);

useEffect(() => {
  // API call with debounced value
  fetchResults(debouncedSearch);
}, [debouncedSearch]);
```

### useCachedFetch

Hook for cached API calls.

**Usage:**
```tsx
const { data, loading, error, refetch } = useCachedFetch(
  'http://localhost:8000/api/models',
  {},
  5 * 60 * 1000 // 5 minute cache
);
```

### useFocusTrap

Hook for trapping focus within modals.

**Usage:**
```tsx
const modalRef = useFocusTrap(isOpen);

return (
  <div ref={modalRef} className="modal">
    {/* Modal content */}
  </div>
);
```

### useAriaLive

Hook for screen reader announcements.

**Usage:**
```tsx
const { announce } = useAriaLive();

const handleSave = () => {
  saveConfig();
  announce('Configuration saved successfully', 'polite');
};
```

## Accessibility Guidelines

### Keyboard Navigation

All interactive components support keyboard navigation:
- **Tab/Shift+Tab**: Navigate between elements
- **Enter/Space**: Activate buttons and toggles
- **Arrow Keys**: Navigate lists and sliders
- **Escape**: Close modals and dropdowns
- **Home/End**: Jump to first/last item in lists

### ARIA Labels

Always provide descriptive ARIA labels:
```tsx
<button aria-label="Save training configuration">
  <SaveIcon />
</button>
```

### Focus Management

Use `useFocusTrap` for modals to trap focus:
```tsx
const modalRef = useFocusTrap(isModalOpen);
```

### Screen Reader Support

Announce dynamic changes:
```tsx
const { announce } = useAriaLive();
announce('Training started successfully', 'polite');
```

### Color Contrast

Ensure sufficient contrast ratios:
```tsx
import { meetsContrastRequirement } from '../lib/accessibility';

const isAccessible = meetsContrastRequirement('#ffffff', '#0066cc', 'AA');
```

## Performance Best Practices

### Code Splitting

Lazy load heavy components:
```tsx
const HeavyComponent = lazy(() => import('./HeavyComponent'));

<Suspense fallback={<LoadingSpinner />}>
  <HeavyComponent />
</Suspense>
```

### Memoization

Use React.memo for expensive components:
```tsx
const MemoizedComponent = React.memo(ExpensiveComponent, (prev, next) => {
  return prev.data === next.data;
});
```

### Request Caching

Cache API responses:
```tsx
import { fetchWithCache } from '../lib/cache';

const data = await fetchWithCache('/api/models', {}, 5 * 60 * 1000);
```

### Debouncing

Debounce search inputs:
```tsx
const debouncedSearch = useDebounce(searchTerm, 500);
```

## Testing

### Unit Testing

Test components with React Testing Library:
```tsx
import { render, screen } from '@testing-library/react';
import { AccessibleButton } from './AccessibleButton';

test('renders button with label', () => {
  render(
    <AccessibleButton aria-label="Test button">
      Click me
    </AccessibleButton>
  );
  expect(screen.getByRole('button')).toBeInTheDocument();
});
```

### Accessibility Testing

Test with jest-axe:
```tsx
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

test('has no accessibility violations', async () => {
  const { container } = render(<MyComponent />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

## Contributing

When creating new components:

1. **TypeScript**: Use strict typing for all props
2. **Accessibility**: Include ARIA labels and keyboard support
3. **Documentation**: Add JSDoc comments and usage examples
4. **Testing**: Write unit tests and accessibility tests
5. **Styling**: Use Tailwind utilities and design tokens
6. **Performance**: Consider memoization for expensive renders

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [React Testing Library](https://testing-library.com/react)
- [Tailwind CSS](https://tailwindcss.com/docs)
