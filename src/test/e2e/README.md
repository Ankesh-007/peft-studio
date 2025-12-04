# End-to-End (E2E) Tests

This directory contains end-to-end tests for PEFT Studio that test complete user workflows and frontend-backend integration.

## Overview

E2E tests verify that the application works correctly from the user's perspective, testing:
- Application startup and initialization
- Navigation between views
- Frontend-backend integration
- Error handling and recovery
- Complete user workflows

## Test Structure

### Test Files

- `app-startup.e2e.test.tsx` - Tests application startup flow
- `navigation.e2e.test.tsx` - Tests navigation and view switching
- `frontend-backend-integration.e2e.test.tsx` - Tests API integration

### Test Configuration

E2E tests use a dedicated Vitest configuration file: `vitest.e2e.config.ts`

Key settings:
- Environment: `jsdom`
- Test timeout: 30 seconds (E2E tests may take longer)
- Setup file: `src/test/setup.ts`
- File pattern: `**/*.e2e.test.{ts,tsx}`

## Running E2E Tests

### Run all E2E tests
```bash
npm run test:e2e
```

### Run specific test file
```bash
npm run test:e2e src/test/e2e/app-startup.e2e.test.tsx
```

### Run with watch mode (development)
```bash
npx vitest --config vitest.e2e.config.ts
```

### Run with coverage
```bash
npx vitest --run --coverage --config vitest.e2e.config.ts
```

## Writing E2E Tests

### Best Practices

1. **Test User Workflows**: Focus on complete user journeys, not individual components
2. **Use Realistic Data**: Test with data that resembles production scenarios
3. **Handle Async Operations**: Use `waitFor` for async state changes
4. **Mock External Dependencies**: Mock backend APIs and Electron APIs
5. **Test Error Scenarios**: Include tests for error handling and recovery
6. **Keep Tests Independent**: Each test should be able to run in isolation

### Example Test Structure

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../../App';

describe('E2E: Feature Name', () => {
  beforeEach(() => {
    // Clear state
    sessionStorage.clear();
    localStorage.clear();
    
    // Setup mocks
    // ...
  });

  it('should complete user workflow', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    // Wait for app to be ready
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /dashboard/i })).toBeInTheDocument();
    }, { timeout: 5000 });
    
    // Perform user actions
    await user.click(screen.getByRole('button', { name: /training/i }));
    
    // Assert expected outcomes
    expect(screen.getByText(/training wizard/i)).toBeInTheDocument();
  });
});
```

### Common Patterns

#### Waiting for App Ready
```typescript
const waitForAppReady = async () => {
  await waitFor(
    () => {
      const dashboardButton = screen.queryByRole('button', { name: /dashboard/i });
      expect(dashboardButton).toBeInTheDocument();
    },
    { timeout: 5000 }
  );
};
```

#### Mocking Backend API
```typescript
const mockFetch = vi.fn();
global.fetch = mockFetch;

mockFetch.mockResolvedValueOnce({
  ok: true,
  json: async () => ({ status: 'healthy' }),
});
```

#### Mocking Electron API
```typescript
if (!window.electron) {
  (window as any).electron = {
    invoke: vi.fn(),
    on: vi.fn(),
    removeListener: vi.fn(),
  };
}
```

## Test Coverage

E2E tests should cover:

- ✅ Application startup and initialization
- ✅ Navigation between all main views
- ✅ Backend availability detection
- ✅ Error handling for various failure scenarios
- ✅ Frontend-backend integration
- 🔄 Complete training workflow (future)
- 🔄 Deployment workflow (future)
- 🔄 Configuration management (future)

## Troubleshooting

### Tests Timeout
- Increase timeout in test or config
- Check if async operations are properly awaited
- Verify mocks are set up correctly

### Tests Fail Intermittently
- Ensure tests are independent
- Check for race conditions
- Add proper wait conditions

### Mock Not Working
- Verify mock is set up before component renders
- Check mock implementation matches expected API
- Clear mocks between tests

## CI/CD Integration

E2E tests run automatically in CI/CD pipeline:
- On pull requests
- On main branch commits
- As part of comprehensive testing workflow

See `.github/workflows/comprehensive-testing.yml` for CI configuration.

## Requirements Validation

These E2E tests validate the following requirements:
- **Requirement 3.3**: End-to-end tests execute complete workflow tests
- **Requirement 3.5**: Tests provide detailed failure information
- **Requirement 6.1-6.3**: Tests pass on Ubuntu, macOS, and Windows

## Future Enhancements

- [ ] Add Playwright for real browser testing
- [ ] Add visual regression testing
- [ ] Add performance benchmarking
- [ ] Add accessibility testing
- [ ] Add mobile viewport testing
- [ ] Add network throttling tests
