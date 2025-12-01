# Telemetry System

## Overview

The telemetry system provides opt-in usage analytics, error reporting, and performance metrics collection for PEFT Studio. All data is anonymized before collection, and users have full control over what data is shared.

**Requirements:** 15.5  
**Status:** ✅ Complete

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

#### 1. TelemetryService (`backend/services/telemetry_service.py`)
Core service providing:
- **Opt-in telemetry** (disabled by default)
- **Event tracking** with automatic anonymization
- **Error reporting** with context
- **Performance metrics** collection
- **Analytics generation** with date filtering
- **Data export** and deletion
- **Session tracking** with unique IDs

Key Features:
- Automatic PII removal (email, username, API keys)
- File path anonymization (filename only)
- User ID hashing (SHA256)
- Event buffering and automatic flushing
- Persistent configuration across sessions
- Anonymous user ID generation

#### 2. TelemetryAPI (`backend/services/telemetry_api.py`)
FastAPI endpoints for telemetry management:
- `GET /api/telemetry/consent` - Get consent status
- `POST /api/telemetry/consent` - Enable/disable telemetry
- `POST /api/telemetry/events` - Track events
- `POST /api/telemetry/performance` - Track performance metrics
- `POST /api/telemetry/analytics` - Get usage analytics
- `GET /api/telemetry/export` - Export all data
- `DELETE /api/telemetry/data` - Delete all data
- `GET /api/telemetry/health` - Health check

### Frontend Components

#### 1. TelemetryConsent (`src/components/TelemetryConsent.tsx`)
User interface for managing telemetry consent:
- Enable/disable toggle with visual feedback
- Expandable section showing what data is collected
- Clear list of data that is NOT collected
- Privacy information and guarantees
- Display of anonymous user ID
- Loading and error states

#### 2. TelemetryAnalyticsDashboard (`src/components/TelemetryAnalyticsDashboard.tsx`)
Analytics dashboard displaying:
- Summary cards (total events, session duration, event types)
- Event breakdown with percentage bars
- Performance metrics table (count, avg, min, max)
- System information (OS, Python version, CPU, memory)
- Export data button
- Date range filtering (future enhancement)

### Integration

#### Main Application (`backend/main.py`)
- Imported telemetry router
- Registered telemetry API endpoints
- Ready for application-wide telemetry tracking

## Data Collection

### Data We Collect (Anonymized)
✅ Application events (start, stop, feature usage)  
✅ Error reports (anonymized stack traces)  
✅ Performance metrics (response times, resource usage)  
✅ System information (OS, Python version)  
✅ Feature usage statistics

### Data We Never Collect
❌ Personal information (names, emails)  
❌ API credentials or keys  
❌ Model data or training datasets  
❌ File paths or directory structures  
❌ IP addresses

## Anonymization Process

The telemetry service automatically anonymizes all data before storage:

1. **PII Removal**: Strips email, username, name, API keys, tokens, passwords
2. **ID Hashing**: User IDs hashed with SHA256 (16-char truncated)
3. **Path Anonymization**: Full paths reduced to filename only
4. **Error Sanitization**: Error messages truncated to first line

## Storage

### Configuration
- **Location:** `~/.peft-studio/config/telemetry_config.json`
- **Contents:** Enabled status, anonymous user ID, timestamps

### Events
- **Location:** `~/.peft-studio/config/telemetry_events.json`
- **Contents:** Last 1000 events (automatically pruned)

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

## Privacy Guarantees

1. **Opt-In Only**: Telemetry is disabled by default
2. **Full Transparency**: Users see exactly what data is collected
3. **Data Control**: Users can export or delete their data anytime
4. **Anonymization**: All data is anonymized before collection
5. **No PII**: Personal information is never collected
6. **Local Storage**: Data stored locally, not sent to external servers

## Testing

Comprehensive test suite with 26 tests covering:
- ✅ Opt-in/opt-out functionality
- ✅ Event tracking when enabled/disabled
- ✅ Data anonymization (PII removal, path sanitization)
- ✅ Error reporting with context
- ✅ Performance metrics collection
- ✅ Analytics generation and date filtering
- ✅ Data export and deletion
- ✅ Session tracking and ID generation
- ✅ Anonymous ID consistency
- ✅ Convenience functions

**Test Results:** 26 passed, 0 failed

Run tests:
```bash
cd backend
pytest tests/test_telemetry_system.py -v
```

## Compliance

The implementation is designed to be:
- **GDPR Compliant**: Data minimization, user consent, right to deletion
- **CCPA Compliant**: Opt-in, data export, data deletion
- **Privacy-First**: No third-party analytics, all data stored locally

## Files

### Backend
- `backend/services/telemetry_service.py` - Core telemetry service
- `backend/services/telemetry_api.py` - FastAPI endpoints
- `backend/tests/test_telemetry_system.py` - Comprehensive tests

### Frontend
- `src/components/TelemetryConsent.tsx` - Consent management UI
- `src/components/TelemetryAnalyticsDashboard.tsx` - Analytics dashboard

## Next Steps

To fully integrate the telemetry system:

1. **Add to Settings UI**: Include TelemetryConsent component in settings
2. **Add to Dashboard**: Include analytics dashboard in main dashboard
3. **Instrument Application**: Add telemetry tracking throughout the app
   - Track feature usage
   - Track errors
   - Track performance metrics
4. **Add Startup Prompt**: Show consent dialog on first launch
5. **Add to Documentation**: Update user documentation

## Future Enhancements

Potential improvements for future versions:
1. Aggregate analytics across multiple users (with consent)
2. Trend analysis and insights
3. Automated anomaly detection
4. Performance regression alerts
5. Feature usage heatmaps
6. A/B testing support

## Support

For questions or issues with the telemetry system:
1. Check the consent status UI for what data is collected
2. Review the analytics dashboard for your data
3. Export your data to see exactly what's stored
4. Delete your data if you no longer want it stored
