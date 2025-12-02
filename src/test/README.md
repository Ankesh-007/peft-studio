# Test Utilities Documentation

This directory contains enhanced test utilities, mock factories, and API mocking helpers for frontend testing.

## Overview

The test utilities provide:
- **Custom Matchers**: Extended assertions for common testing patterns
- **Test Utilities**: Helper functions for component testing
- **Mock Factories**: Factory functions for creating test data
- **API Mocking**: Utilities for mocking API calls and WebSocket connections
- **Async Helpers**: Tools for testing asynchronous operations

## Files

- `setup.ts` - Test setup with custom matchers
- `test-utils.tsx` - Component testing utilities
- `mock-factories.ts` - Mock data factories
- `api-mocks.ts` - API and WebSocket mocking utilities
- `index.ts` - Centralized exports
- `test-utilities.test.ts` - Examples and tests for utilities

## Usage

### Importing

```typescript
// Import everything
import { 
  createMockProfile, 
  createMockDataset,
  mockApi,
  renderWithProviders,
  expect 
} from './test';

// Or import specific utilities
import { createMockProfile } from './test/mock-factories';
import { mockApi } from './test/api-mocks';
```

## Custom Matchers

### toBeWithinRange(min, max)
Check if a number is within a specified range.

```typescript
expect(50).toBeWithinRange(0, 100);
expect(progress).toBeWithinRange(0, 100);
```

### toHaveValidTimestamp()
Validate that a string is a valid ISO timestamp.

```typescript
expect(pausedRun.paused_at).toHaveValidTimestamp();
expect(new Date().toISOString()).toHaveValidTimestamp();
```

### toBeValidPercentage()
Check if a number is a valid percentage (0-100).

```typescript
expect(gpuUtilization).toBeValidPercentage();
expect(50).toBeValidPercentage();
```

### toHaveRequiredFields(fields)
Verify that an object has all required fields.

```typescript
expect(profile).toHaveRequiredFields(['id', 'name', 'config']);
expect(dataset).toHaveRequiredFields(['id', 'path', 'format']);
```

## Mock Factories

### Profile Factory

```typescript
// Create with defaults
const profile = createMockProfile();

// Create with overrides
const customProfile = createMockProfile({
  id: 'chatbot',
  name: 'Chatbot Assistant',
  use_case: 'chatbot'
});
```

### Dataset Factory

```typescript
const dataset = createMockDataset({
  id: 'my-dataset',
  num_samples: 1000
});
```

### Model Factory

```typescript
const model = createMockModel({
  model_id: 'meta-llama/Llama-2-7b-hf',
  parameters: 7000
});
```

### Training Run Factory

```typescript
const run = createMockTrainingRun({
  status: 'running',
  progress: 65
});
```

### Wizard State Factory

```typescript
const wizardState = createMockWizardState({
  currentStep: 2,
  profile: createMockProfile(),
  dataset: createMockDataset()
});
```

### Paused Run Factory

```typescript
const pausedRun = createMockPausedRun({
  job_id: 'test-job-123',
  current_loss: 0.5
});
```

### Batch Factories

```typescript
// Create multiple items
const profiles = createMockProfiles(); // Returns 3 profiles
const runs = createMockTrainingRuns(); // Returns 4 runs with different statuses

// Create custom batches
const datasets = createMockBatch(
  (i) => createMockDataset({ id: `dataset-${i}` }),
  5
);
```

## Test Utilities

### Component Rendering

```typescript
import { renderWithProviders } from './test';

const { getByText } = renderWithProviders(<MyComponent />);
```

### Async Helpers

```typescript
// Wait for a condition
await waitForCondition(() => element.textContent === 'Loaded', 5000);

// Simple delay
await delay(100);

// Delayed rejection
await delayedReject(1000, new Error('Timeout'));
```

### Event Simulation

```typescript
// Create mock file
const file = createMockFile('test.json', 1024, 'application/json', '{}');

// Create drag event
const dragEvent = createDragEvent('drop', [file]);
```

### LocalStorage Mocking

```typescript
import { setupMockLocalStorage } from './test';

beforeEach(() => {
  setupMockLocalStorage();
});

// Now localStorage is mocked
localStorage.setItem('key', 'value');
```

## API Mocking

### Basic Setup

```typescript
import { mockApi, setupFetchMock } from './test';

beforeEach(() => {
  mockApi.reset();
  setupFetchMock();
});

afterEach(() => {
  restoreFetch();
});
```

### Mock Endpoints

```typescript
// Use default endpoints
const data = await mockApi.call('/api/hardware/detect');

// Mock custom success response
mockApi.mockSuccess('/api/custom', { data: 'test' });

// Mock error response
mockApi.mockError('/api/error', 'Something went wrong', 500);

// Mock delayed response
mockApi.mockDelayed('/api/slow', { data: 'test' }, 2000);
```

### Track API Calls

```typescript
mockApi.clearCallLog();

await mockApi.call('/api/profiles');
await mockApi.call('/api/datasets');

const log = mockApi.getCallLog();
expect(log).toHaveLength(2);
expect(log[0].endpoint).toBe('/api/profiles');
```

### Custom Handlers

```typescript
mockApi.registerHandler('/api/custom/:id', (id) => {
  return { id, data: 'custom' };
});

const result = await mockApi.call('/api/custom/123');
// result = { id: '123', data: 'custom' }
```

## WebSocket Mocking

```typescript
import { MockWebSocket } from './test';

const ws = new MockWebSocket('ws://localhost:8000');

// Listen for connection
ws.onopen = () => {
  console.log('Connected');
};

// Listen for messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

// Simulate receiving a message
ws.simulateMessage({ type: 'update', data: 'test' });

// Simulate error
ws.simulateError();

// Check sent messages
const sent = ws.getSentMessages();
expect(sent).toHaveLength(1);
```

## EventSource Mocking

```typescript
import { MockEventSource, setupEventSourceMock } from './test';

setupEventSourceMock();

const es = new MockEventSource('/api/events');

es.addEventListener('update', (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
});

// Simulate event
es.simulateEvent('update', { status: 'running' });
```

## Console Suppression

```typescript
import { suppressConsoleErrors, suppressConsoleWarnings } from './test';

it('should not log errors', () => {
  const restore = suppressConsoleErrors();
  
  // Code that logs errors
  console.error('This will not appear');
  
  restore();
});
```

## Best Practices

1. **Use Mock Factories**: Always use factories instead of creating objects manually
2. **Reset Mocks**: Reset API mocks between tests to avoid state leakage
3. **Custom Matchers**: Use custom matchers for clearer test assertions
4. **Async Testing**: Use promises instead of callbacks for async tests
5. **Cleanup**: Always restore mocks and clean up after tests

## Examples

### Testing a Component with API Calls

```typescript
import { 
  renderWithProviders, 
  mockApi, 
  setupFetchMock,
  createMockProfile,
  waitFor,
  screen 
} from './test';

describe('ProfileSelector', () => {
  beforeEach(() => {
    mockApi.reset();
    setupFetchMock();
  });

  it('should load and display profiles', async () => {
    const profiles = [
      createMockProfile({ id: '1', name: 'Profile 1' }),
      createMockProfile({ id: '2', name: 'Profile 2' })
    ];
    
    mockApi.mockSuccess('/api/profiles', { items: profiles });
    
    renderWithProviders(<ProfileSelector />);
    
    await waitFor(() => {
      expect(screen.getByText('Profile 1')).toBeInTheDocument();
      expect(screen.getByText('Profile 2')).toBeInTheDocument();
    });
  });
});
```

### Testing with Custom Matchers

```typescript
import { createMockTrainingRun, expect } from './test';

it('should have valid training run data', () => {
  const run = createMockTrainingRun();
  
  expect(run).toHaveRequiredFields(['id', 'name', 'status']);
  expect(run.progress).toBeValidPercentage();
  expect(run.started_at).toHaveValidTimestamp();
  expect(run.current_step).toBeWithinRange(0, run.total_steps);
});
```

### Testing WebSocket Communication

```typescript
import { MockWebSocket } from './test';

it('should handle WebSocket messages', async () => {
  const ws = new MockWebSocket('ws://localhost:8000');
  
  const messagePromise = new Promise((resolve) => {
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      expect(data.type).toBe('update');
      resolve();
    };
  });
  
  ws.simulateMessage({ type: 'update', progress: 50 });
  
  await messagePromise;
});
```

## Contributing

When adding new test utilities:

1. Add the utility to the appropriate file
2. Export it from `index.ts`
3. Add tests in `test-utilities.test.ts`
4. Document it in this README
5. Ensure all existing tests still pass
