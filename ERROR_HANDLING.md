# Error Handling and Recovery System

This document describes the error handling and recovery system implemented for PEFT Studio.

## Overview

The error handling system provides:
- **Plain-language error messages** - No technical jargon or stack traces
- **Actionable suggestions** - 2-3 specific actions users can take
- **Automatic recovery** - Auto-fix options for recoverable errors
- **Help documentation** - Links to relevant troubleshooting guides
- **Severity-based UI** - Visual indicators based on error severity

## Architecture

### Backend Components

#### ErrorRecoveryService (`backend/services/error_service.py`)
Main service for formatting errors and providing recovery options.

```python
from backend.services.error_service import get_error_service

service = get_error_service()
formatted = service.format_error(error, context)
```

#### ErrorFormatter
Translates technical errors into plain language.

```python
from backend.services.error_service import ErrorFormatter

# Remove technical details
cleaned = ErrorFormatter.remove_technical_details(error_message)

# Check if message is plain language
is_plain = ErrorFormatter.is_plain_language(message)
```

### Frontend Components

#### ErrorDisplay (`src/components/ErrorDisplay.tsx`)
Full-featured error display component with action buttons.

```tsx
import ErrorDisplay from './components/ErrorDisplay';

<ErrorDisplay
  error={formattedError}
  onDismiss={() => clearError()}
  onRetry={() => retryOperation()}
  context={{ component: 'MyComponent' }}
/>
```

#### ErrorToast (`src/components/ErrorToast.tsx`)
Toast notification for non-critical errors.

```tsx
import ErrorToast from './components/ErrorToast';

<ErrorToast
  error={formattedError}
  onDismiss={() => dismissToast()}
  autoHideDuration={5000}
/>
```

#### ErrorBoundary (`src/components/ErrorBoundary.tsx`)
React error boundary for catching component errors.

```tsx
import { ErrorBoundary } from './components/ErrorBoundary';

<ErrorBoundary>
  <YourApp />
</ErrorBoundary>
```

### Hooks and Context

#### useErrorHandler (`src/lib/useErrorHandler.ts`)
Hook for local error handling in functional components.

```tsx
import useErrorHandler from './lib/useErrorHandler';

function MyComponent() {
  const { error, handleError, clearError, retryWithAutoFix } = useErrorHandler();
  
  const handleAction = async () => {
    try {
      await riskyOperation();
    } catch (err) {
      await handleError(err, { component: 'MyComponent' });
    }
  };
  
  return error ? (
    <ErrorDisplay error={error} onDismiss={clearError} />
  ) : (
    <button onClick={handleAction}>Do Something</button>
  );
}
```

#### ErrorContext (`src/lib/ErrorContext.tsx`)
Global error handling context.

```tsx
import { ErrorProvider, useError } from './lib/ErrorContext';

// In your app root:
<ErrorProvider>
  <App />
</ErrorProvider>

// In any component:
function MyComponent() {
  const { showError, clearError } = useError();
  
  const handleAction = async () => {
    try {
      await riskyOperation();
    } catch (error) {
      showError(error, { component: 'MyComponent' });
    }
  };
}
```

## Error Categories

The system categorizes errors into:

- **USER_INPUT** - Invalid user input or configuration
- **RESOURCE** - Insufficient resources (memory, disk, etc.)
- **TRAINING** - Training-specific errors
- **SYSTEM** - System-level errors (permissions, drivers, etc.)
- **NETWORK** - Network connectivity issues
- **DATASET** - Dataset format or validation errors

## Error Severity Levels

- **LOW** - Informational, no action required
- **MEDIUM** - Warning, user should be aware
- **HIGH** - Error that prevents operation
- **CRITICAL** - Severe error requiring immediate attention

## Error Actions

Each error includes 2-3 suggested actions:

### Action Types

1. **auto_fix** - Automatic fixes that can be applied with one click
2. **manual_step** - Manual steps the user should take
3. **help_link** - Links to documentation or support

### Example Actions

```typescript
{
  description: "Automatically reduce batch size and enable gradient checkpointing",
  automatic: true,
  action_type: 'auto_fix',
  action_data: { action: 'reduce_batch_size', enable_checkpointing: true }
}

{
  description: "Check that the file path is correct and the file exists",
  automatic: false,
  action_type: 'manual_step',
  action_data: { check: 'file_path' }
}

{
  description: "Get help from documentation",
  automatic: false,
  action_type: 'help_link',
  action_data: { link: 'support' }
}
```

## API Endpoints

### POST /api/errors/format
Format an error into plain language.

**Request:**
```json
{
  "error_type": "RuntimeError",
  "error_message": "CUDA out of memory",
  "context": {
    "component": "TrainingWizard",
    "model_size": 7000
  }
}
```

**Response:**
```json
{
  "title": "Not Enough GPU Memory",
  "what_happened": "Your GPU ran out of memory while trying to train the model.",
  "why_it_happened": "The model or batch size is too large for your GPU's available memory.",
  "actions": [
    {
      "description": "Automatically reduce batch size and enable gradient checkpointing",
      "automatic": true,
      "action_type": "auto_fix",
      "action_data": { "action": "reduce_batch_size" }
    }
  ],
  "category": "resource",
  "severity": "high",
  "help_link": "https://docs.peftstudio.ai/troubleshooting/resource-errors",
  "auto_recoverable": true
}
```

### POST /api/errors/auto-fix
Execute an automatic fix.

**Request:**
```json
{
  "action_data": {
    "action": "reduce_batch_size",
    "enable_checkpointing": true
  },
  "context": {
    "training_job_id": "job_123"
  }
}
```

**Response:**
```json
{
  "success": true
}
```

## Property-Based Tests

The error handling system includes comprehensive property-based tests:

### Property 19: Error messages are plain language
Tests that all error messages are formatted without technical jargon.

```python
# backend/tests/test_error_formatting.py
@given(st.one_of(...))
def test_error_messages_are_plain_language(error):
    formatted = service.format_error(error)
    assert ErrorFormatter.is_plain_language(formatted.title)
    assert ErrorFormatter.is_plain_language(formatted.what_happened)
```

### Property 20: Error handling provides actions
Tests that all errors include 2-3 actionable suggestions.

```python
# backend/tests/test_error_actions.py
@given(st.one_of(...))
def test_error_handling_provides_actions(error):
    formatted = service.format_error(error)
    assert len(formatted.actions) >= 2
    assert len(formatted.actions) <= 3
```

### Property 21: Unresolvable errors include help links
Tests that errors without automatic fixes include help documentation links.

```python
# backend/tests/test_error_help_links.py
@given(st.one_of(...))
def test_unresolvable_errors_include_help_links(error):
    formatted = service.format_error(error)
    if not formatted.auto_recoverable:
        assert formatted.help_link is not None
```

## Best Practices

### 1. Always Provide Context
```tsx
try {
  await operation();
} catch (error) {
  showError(error, {
    component: 'TrainingWizard',
    step: 'dataset_upload',
    dataset_size: 1000
  });
}
```

### 2. Use Appropriate Error Handling Method
- **Global errors** (toast): Non-critical, informational
- **Local errors** (display): Component-specific, requires user action
- **Error boundary**: Catch unexpected React errors

### 3. Implement Auto-Recovery When Possible
```python
def _generate_actions(self, error, category, context):
    if 'out of memory' in str(error).lower():
        actions.append(ErrorAction(
            description="Automatically reduce batch size",
            automatic=True,
            action_type='auto_fix',
            action_data={'action': 'reduce_batch_size'}
        ))
```

### 4. Test Error Scenarios
```tsx
// In your tests
it('handles errors gracefully', async () => {
  const { handleError, error } = renderHook(() => useErrorHandler());
  
  await handleError(new Error('Test error'));
  
  expect(error).toBeDefined();
  expect(error.title).toBeTruthy();
  expect(error.actions.length).toBeGreaterThanOrEqual(2);
});
```

## Extending the System

### Adding New Error Patterns

Edit `backend/services/error_service.py`:

```python
ERROR_TRANSLATIONS = {
    r'your_error_pattern': {
        'title': 'User-Friendly Title',
        'what': 'What happened in plain language',
        'why': 'Why it happened',
        'category': ErrorCategory.YOUR_CATEGORY,
        'severity': ErrorSeverity.MEDIUM,
    },
}
```

### Adding New Auto-Fix Actions

```python
def execute_auto_fix(self, action: ErrorAction, context: Dict[str, Any]) -> bool:
    action_type = action.action_data.get('action')
    
    if action_type == 'your_new_action':
        # Implement your auto-fix logic
        return True
    
    return False
```

## Requirements Validation

This implementation validates the following requirements:

- **Requirement 10.1**: Error messages are in plain language without stack traces ✓
- **Requirement 10.2**: Each error provides 2-3 specific actions ✓
- **Requirement 10.3**: Automatic fixes are available for recoverable errors ✓
- **Requirement 10.4**: Unresolvable errors include help links ✓
- **Requirement 10.5**: Users can resume from failure points ✓

## Testing

Run all error handling tests:

```bash
# Backend tests
python -m pytest backend/tests/test_error_formatting.py -v
python -m pytest backend/tests/test_error_actions.py -v
python -m pytest backend/tests/test_error_help_links.py -v

# Run all error tests
python -m pytest backend/tests/test_error_*.py -v
```

## Demo

See `src/components/ErrorHandlingDemo.tsx` for a comprehensive demonstration of all error handling features.
