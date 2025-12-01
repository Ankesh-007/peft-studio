# Telemetry System Implementation

## Overview

The telemetry system provides opt-in usage analytics, error reporting, and performance metrics collection for PEFT Studio. All data is anonymized before collection, and users have full control over what data is shared.

**Requirements:** 15.5

## Features

### 1. Opt-In Telemetry
- Telemetry is **disabled by default**
- Users must explicitly enable telemetry
- Clear consent UI showing what data is collected
- Easy opt-out mechanism
- Settings persist across sessions

### 2. Event Tracking with Anonymization
- Track application events (feature usage, actions)
- Automatic anonymization of sensitive data
- PII fields removed (email, username, API keys)
- File paths anonymized (only filename kept)
- User IDs hashed for privacy

### 3. Usage Analytics Dashboard
- View total events and event breakdown
- Performance metrics summary
- Session duration tracking
- System information (anonymized)
- Export data as JSON

### 4. Error Reporting
- Automatic error tracking with context
- Stack traces anonymized
- System information included
- Error categorization by type

### 5. Performance Metrics Collection
- Track API response times
- Monitor resource usage
- Calculate averages, min, max
- Identify performance bottlenecks

## Architecture

### Backend Components

#### TelemetryService
Main service class that handles all telemetry operations:
- Event tracking and buffering
- Data anonymization
- Storage management
- Analytics generation

#### TelemetryAPI
FastAPI endpoints for telemetry management:
- `GET /api/telemetry/consent` - Get consent status
- `POST /api/telemetry/consent` - Update consent
- `POST /api/telemetry/events` - Track event
- `POST /api/telemetry/performance` - Track performance metric
- `POST /api/telemetry/analytics` - Get analytics
- `GET /api/telemetry/export` - Export all data
- `DELETE /api/telemetry/data` - Delete all data

### Frontend Components

#### TelemetryConsent
React component for managing telemetry consent:
- Enable/disable telemetry
- View what data is collected
- View what data is NOT collected
- Display anonymous user ID

#### TelemetryAnalyticsDashboard
React component for viewing usage analytics:
- Summary cards (total events, session duration, event types)
- Event breakdown with percentages
- Performance metrics table
- System information
- Export data button

## Data Collection

### Data We Collect (Anonymized)
- Application events (start, stop, feature usage)
- Error reports (anonymized stack traces)
- Performance metrics (response times, resource usage)
- System information (OS, Python version)
- Feature usage statistics

### Data We Never Collect
- Personal information (names, emails)
- API credentials or keys
- Model data or training datasets
- File paths or directory structures
- IP addresses

## Anonymization Process

The telemetry service automatically anonymizes all data before storage:

1. **PII Removal**: Email, username, name, API keys, tokens, passwords
2. **ID Hashing**: User IDs are hashed using SHA256
3. **Path Anonymization**: Full file paths reduced to filename only
4. **Error Sanitization**: Error messages truncated to first line only

## Storage

### Configuration
- Location: `~/.peft-studio/config/telemetry_config.json`
- Contains: enabled status, anonymous user ID, timestamps

### Events
- Location: `~/.peft-studio/config/telemetry_events.json`
- Contains: Last 1000 events
- Automatically pruned to prevent excessive storage

### Anonymous User ID
- Generated from machine-specific information
- Consistent across sessions
- Cannot be traced back to user
- 16-character hash

## Usage Examples

### Backend Usage

```python
from services.telemetry_service import track_event, track_error, track_performance

# Track an event
await track_event("training_started", {
    "algorithm": "lora",
    "model_size": "7B"
})

# Track an error
try:
    # Some operation
    pass
except Exception as e:
    await track_error(e, {"context": "training"})

# Track performance
await track_performance("api_response_time", 150.5, "ms")
```

### Frontend Usage

```typescript
// Enable telemetry
const response = await fetch('/api/telemetry/consent', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ enabled: true })
});

// Track an event
await fetch('/api/telemetry/events', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    event_type: 'model_loaded',
    properties: { model_name: 'llama-2-7b' }
  })
});

// Get analytics
const analytics = await fetch('/api/telemetry/analytics', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({})
});
```

## Privacy Guarantees

1. **Opt-In Only**: Telemetry is disabled by default
2. **Full Transparency**: Users see exactly what data is collected
3. **Data Control**: Users can export or delete their data anytime
4. **Anonymization**: All data is anonymized before collection
5. **No PII**: Personal information is never collected
6. **Local Storage**: Data stored locally, not sent to external servers

## Testing

Comprehensive test suite covers:
- Opt-in/opt-out functionality
- Event tracking and anonymization
- Error reporting
- Performance metrics
- Analytics generation
- Data export and deletion
- Session tracking
- Anonymous ID generation

Run tests:
```bash
pytest backend/tests/test_telemetry_system.py -v
```

## Integration Points

### Application Startup
```python
from services.telemetry_service import get_telemetry

telemetry = get_telemetry()
await telemetry.track_event("app_started")
```

### Application Shutdown
```python
await telemetry.shutdown()  # Flushes remaining events
```

### Error Handling
```python
try:
    # Application code
    pass
except Exception as e:
    await track_error(e, {"context": "operation_name"})
    raise
```

### Performance Monitoring
```python
import time

start = time.time()
# Operation
duration = (time.time() - start) * 1000
await track_performance("operation_time", duration, "ms")
```

## Configuration

### Enable Telemetry
```python
telemetry = get_telemetry()
telemetry.enable()
```

### Disable Telemetry
```python
telemetry.disable()
```

### Check Status
```python
if telemetry.is_enabled():
    await track_event("some_event")
```

## Future Enhancements

Potential improvements for future versions:
1. Aggregate analytics across multiple users (with consent)
2. Trend analysis and insights
3. Automated anomaly detection
4. Performance regression alerts
5. Feature usage heatmaps
6. A/B testing support

## Compliance

The telemetry system is designed with privacy in mind:
- GDPR compliant (data minimization, user consent, right to deletion)
- CCPA compliant (opt-in, data export, data deletion)
- No third-party analytics services
- All data stored locally

## Support

For questions or issues with the telemetry system:
1. Check the consent status UI for what data is collected
2. Review the analytics dashboard for your data
3. Export your data to see exactly what's stored
4. Delete your data if you no longer want it stored
