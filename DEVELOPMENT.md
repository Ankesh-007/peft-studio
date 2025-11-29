# PEFT Studio - Development Guide

## 🎨 Design System Implementation

### Color System
All colors are defined in `tailwind.config.js` and can be used with Tailwind classes:

```tsx
// Background colors
<div className="bg-dark-bg-primary">     // #0a0a0a
<div className="bg-dark-bg-secondary">   // #111111
<div className="bg-dark-bg-tertiary">    // #1a1a1a

// Text colors
<span className="text-dark-text-primary">    // #ffffff
<span className="text-dark-text-secondary">  // #a1a1aa
<span className="text-dark-text-tertiary">   // #71717a

// Accent colors
<button className="bg-accent-primary">   // #6366f1 (indigo)
<div className="text-accent-success">    // #10b981 (emerald)
<span className="text-accent-warning">   // #f59e0b (amber)
<div className="border-accent-error">    // #ef4444 (red)
```

### Typography
Use semantic font size classes:

```tsx
<h1 className="text-display">   // 32px, bold
<h1 className="text-h1">        // 24px, semibold
<h2 className="text-h2">        // 20px, semibold
<h3 className="text-h3">        // 16px, semibold
<p className="text-body">       // 14px, normal
<span className="text-small">   // 12px, normal
<span className="text-tiny">    // 11px, normal
```

### Spacing
Use the 4px base unit system:

```tsx
<div className="p-4">    // 4px padding
<div className="m-8">    // 8px margin
<div className="gap-12"> // 12px gap
<div className="px-16">  // 16px horizontal padding
<div className="py-20">  // 20px vertical padding
```

### Component Classes
Pre-built component classes in `src/index.css`:

```tsx
// Cards
<div className="card">              // Base card style
<div className="card card-hover">   // Card with hover effect

// Buttons
<button className="btn-primary">    // Primary action button
<button className="btn-secondary">  // Secondary button
<button className="btn-ghost">      // Ghost/outline button

// Inputs
<input className="input">           // Styled input field

// Navigation
<div className="nav-item">          // Navigation item
<div className="nav-item nav-item-active">  // Active nav item
```

## 🧩 Component Architecture

### Layout Components

**Layout.tsx** - Main application wrapper
- Manages sidebar collapse state
- Controls right panel visibility
- Provides consistent structure

**Sidebar.tsx** - Left navigation
- Navigation menu with icons
- System status indicators
- User profile section
- Collapsible design

**TopBar.tsx** - Top action bar
- Breadcrumb navigation
- Global search / command palette
- Quick actions
- Theme toggle
- Notifications

### Feature Components

**Dashboard.tsx** - Main dashboard view
- Stats cards with trends
- Recent training runs
- Quick action buttons
- Real-time charts (Recharts)
- System resource monitoring

**DatasetUpload.tsx** - File upload interface
- Drag-and-drop zone
- Upload progress tracking
- File validation
- Multiple import options

**CommandPalette.tsx** - Quick command interface
- Fuzzy search
- Keyboard navigation
- Categorized commands
- Keyboard shortcuts (⌘K)

## 🔧 Utility Functions

Located in `src/lib/utils.ts`:

```typescript
// Merge Tailwind classes
cn('base-class', condition && 'conditional-class')

// Format file sizes
formatBytes(1024) // "1 KB"

// Format durations
formatDuration(3665) // "1h 1m"

// Format numbers
formatNumber(1500) // "1.5K"

// Get time-based greeting
getTimeGreeting() // "Good morning" / "Good afternoon" / "Good evening"
```

## 📡 API Integration

### Frontend API Client
Located in `src/api/client.ts`:

```typescript
import { apiClient } from './api/client';

// Dataset operations
await apiClient.listDatasets();
await apiClient.uploadDataset(file);
await apiClient.deleteDataset(id);

// Model operations
await apiClient.listModels();
await apiClient.searchModels(query);
await apiClient.downloadModel(modelId);

// Training operations
await apiClient.startTraining(config);
await apiClient.pauseTraining(id);
await apiClient.stopTraining(id);

// System operations
await apiClient.getSystemInfo();
```

### Electron IPC
Available via `window.api` (defined in `electron/preload.js`):

```typescript
// Training operations
window.api.startTraining(config);
window.api.pauseTraining(id);
window.api.stopTraining(id);

// Real-time updates
window.api.onTrainingProgress((data) => {
  console.log('Progress:', data);
});

window.api.onTrainingComplete((data) => {
  console.log('Completed:', data);
});
```

## 🎯 Creating New Components

### Step 1: Create Component File
```tsx
// src/components/MyComponent.tsx
import React from 'react';
import { Icon } from 'lucide-react';
import { cn } from '../lib/utils';

interface MyComponentProps {
  title: string;
  onAction?: () => void;
}

const MyComponent: React.FC<MyComponentProps> = ({ title, onAction }) => {
  return (
    <div className="card">
      <h2 className="text-h2 mb-16">{title}</h2>
      <button className="btn-primary" onClick={onAction}>
        Action
      </button>
    </div>
  );
};

export default MyComponent;
```

### Step 2: Use Design System
- Use semantic color classes (`text-dark-text-primary`)
- Use spacing scale (`p-16`, `gap-12`)
- Use component classes (`card`, `btn-primary`)
- Add hover states and transitions
- Follow the 4px spacing system

### Step 3: Add Icons
```tsx
import { Icon1, Icon2 } from 'lucide-react';

<Icon1 size={20} className="text-accent-primary" />
```

### Step 4: Add Animations
```tsx
// Hover effects
<div className="transition-all duration-200 hover:-translate-y-0.5">

// Loading states
<div className="animate-pulse">

// Custom animations (defined in index.css)
<div className="animate-scale-in">
```

## 📊 Working with Charts

Using Recharts library:

```tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

<ResponsiveContainer width="100%" height={200}>
  <LineChart data={data}>
    <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
    <XAxis dataKey="step" stroke="#71717a" />
    <YAxis stroke="#71717a" />
    <Tooltip
      contentStyle={{
        backgroundColor: '#111111',
        border: '1px solid #2a2a2a',
        borderRadius: '8px',
      }}
    />
    <Line
      type="monotone"
      dataKey="loss"
      stroke="#6366f1"
      strokeWidth={2}
    />
  </LineChart>
</ResponsiveContainer>
```

## 🔍 State Management

Currently using React hooks. For complex state, consider:

1. **Local State** (useState):
```tsx
const [isOpen, setIsOpen] = useState(false);
```

2. **Context API** (for global state):
```tsx
// Create context
const AppContext = createContext();

// Provider
<AppContext.Provider value={value}>
  {children}
</AppContext.Provider>

// Consumer
const value = useContext(AppContext);
```

3. **Future**: Consider Zustand or Redux for complex state

## 🧪 Testing Strategy

### Unit Tests (Future)
```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom
```

### Component Tests
```tsx
import { render, screen } from '@testing-library/react';
import MyComponent from './MyComponent';

test('renders component', () => {
  render(<MyComponent title="Test" />);
  expect(screen.getByText('Test')).toBeInTheDocument();
});
```

### E2E Tests (Future)
Consider Playwright or Cypress for Electron testing

## 🚀 Performance Optimization

### Code Splitting
```tsx
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./components/Dashboard'));

<Suspense fallback={<Loading />}>
  <Dashboard />
</Suspense>
```

### Memoization
```tsx
import { memo, useMemo, useCallback } from 'react';

// Memoize component
const MyComponent = memo(({ data }) => {
  return <div>{data}</div>;
});

// Memoize values
const expensiveValue = useMemo(() => {
  return computeExpensiveValue(data);
}, [data]);

// Memoize callbacks
const handleClick = useCallback(() => {
  doSomething();
}, []);
```

### Virtual Scrolling
For large lists, use react-window or react-virtualized

## 📝 Code Style Guidelines

### Naming Conventions
- **Components**: PascalCase (`MyComponent.tsx`)
- **Utilities**: camelCase (`formatBytes`)
- **Constants**: UPPER_SNAKE_CASE (`API_BASE_URL`)
- **CSS Classes**: kebab-case or Tailwind utilities

### File Organization
```
src/
├── components/       # React components
│   ├── common/      # Reusable components
│   ├── features/    # Feature-specific components
│   └── layouts/     # Layout components
├── lib/             # Utilities and helpers
├── api/             # API clients
├── hooks/           # Custom React hooks
├── types/           # TypeScript types
└── styles/          # Global styles
```

### Import Order
```tsx
// 1. React imports
import React, { useState } from 'react';

// 2. Third-party imports
import { Icon } from 'lucide-react';

// 3. Local imports
import { cn } from '../lib/utils';
import MyComponent from './MyComponent';
```

## 🐛 Debugging

### React DevTools
Install React DevTools extension for Chrome/Firefox

### Electron DevTools
Open DevTools in Electron:
```javascript
mainWindow.webContents.openDevTools();
```

### Console Logging
```tsx
console.log('Debug:', data);
console.error('Error:', error);
console.warn('Warning:', warning);
```

### Network Requests
Monitor API calls in Network tab of DevTools

## 🔐 Security Best Practices

### IPC Security
- Use `contextIsolation: true`
- Use `nodeIntegration: false`
- Validate all IPC messages
- Sanitize user inputs

### API Security
- Validate all API responses
- Handle errors gracefully
- Use HTTPS for external APIs
- Store sensitive data securely

## 📦 Building for Production

### Development Build
```bash
npm run build
```

### Electron Build
```bash
npm run electron:build
```

### Platform-Specific Builds
```bash
# Windows
npm run electron:build -- --win

# macOS
npm run electron:build -- --mac

# Linux
npm run electron:build -- --linux
```

## 🎓 Learning Resources

- **React**: https://react.dev
- **TypeScript**: https://www.typescriptlang.org/docs
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Electron**: https://www.electronjs.org/docs
- **Lucide Icons**: https://lucide.dev
- **Recharts**: https://recharts.org/en-US

## 🤝 Contributing

1. Follow the design system
2. Write clean, readable code
3. Add comments for complex logic
4. Test your changes
5. Update documentation
