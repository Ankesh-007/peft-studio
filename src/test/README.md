# Frontend Test Organization

This directory contains all frontend tests for PEFT Studio, organized by test type.

## Directory Structure

```
src/test/
├── components/          # Component-level tests
│   ├── ConfigurationManagement.test.tsx
│   ├── DeploymentManagement.test.tsx
│   ├── GradioDemoGenerator.test.tsx
│   ├── InferencePlayground.test.tsx
│   ├── LoggingDiagnostics.test.tsx
│   ├── PausedRunDisplay.test.tsx
│   └── UpdateNotification.test.tsx
├── integration/         # Integration tests
│   ├── accessibility.test.tsx
│   ├── onboarding.test.tsx
│   └── wizard-steps-integration.test.tsx
├── unit/               # Unit tests
│   ├── bundle-size-constraint.test.ts
│   ├── cost-estimate-fields.test.ts
│   ├── estimate-completeness.test.ts
│   ├── estimate-intervals.test.ts
│   ├── loss-curve-color-coding.test.ts
│   ├── performance.test.ts
│   ├── prompt-generation.test.ts
│   ├── tooltip-completeness.test.ts
│   └── worker.test.ts
├── setup.ts            # Test setup and configuration
└── README.md           # This file
```

## Test Categories

### Component Tests (`components/`)
Tests for individual React components, focusing on:
- Component rendering
- User interactions
- Props handling
- State management
- Component-specific logic

### Integration Tests (`integration/`)
Tests that verify multiple components or systems working together:
- Accessibility compliance across the application
- User onboarding flows
- Multi-step wizard interactions
- Feature integration

### Unit Tests (`unit/`)
Tests for individual functions, utilities, and isolated logic:
- Bundle size constraints
- Cost estimation calculations
- Performance utilities
- Worker thread functionality
- Data validation and formatting

## Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run specific test category
npm test -- src/test/components
npm test -- src/test/integration
npm test -- src/test/unit

# Run a specific test file
npm test -- src/test/components/ConfigurationManagement.test.tsx
```

## Writing New Tests

When adding new tests:

1. **Component Tests**: Place in `components/` if testing a single React component
2. **Integration Tests**: Place in `integration/` if testing multiple components or features together
3. **Unit Tests**: Place in `unit/` if testing pure functions, utilities, or isolated logic

### Test Naming Convention

- Component tests: `ComponentName.test.tsx`
- Integration tests: `feature-name-integration.test.tsx`
- Unit tests: `feature-name.test.ts` or `utility-name.test.ts`

### Test Structure

```typescript
import { describe, it, expect } from 'vitest';

describe('ComponentName', () => {
  it('should render correctly', () => {
    // Test implementation
  });

  it('should handle user interaction', () => {
    // Test implementation
  });
});
```

## Test Configuration

Test configuration is managed in:
- `vitest.config.ts` - Vitest configuration
- `src/test/setup.ts` - Global test setup

## Best Practices

1. **Keep tests focused**: Each test should verify one specific behavior
2. **Use descriptive names**: Test names should clearly describe what is being tested
3. **Avoid test interdependence**: Tests should be able to run independently
4. **Mock external dependencies**: Use mocks for API calls, external services, etc.
5. **Test user behavior**: Focus on testing what users see and do, not implementation details
6. **Maintain test coverage**: Aim for high coverage of critical paths

## Related Documentation

- [Testing Guide](../../docs/developer-guide/testing.md) - Comprehensive testing documentation
- [Contributing Guide](../../docs/CONTRIBUTING.md) - Guidelines for contributing tests
