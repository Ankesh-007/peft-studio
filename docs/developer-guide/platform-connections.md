# Platform Connection Manager

## Overview

The Platform Connection Manager provides a comprehensive system for managing connections to external platforms (cloud GPU providers, model registries, experiment trackers, etc.) with secure credential storage and connection verification.

## Components

### Backend Services

#### 1. PlatformConnectionService (`platform_connection_service.py`)
Main service for managing platform connections.

**Features:**
- Connect/disconnect from platforms
- Verify connection status
- Test connections without storing credentials
- Update credentials
- List available platforms and active connections
- Connection statistics

**Key Methods:**
- `connect_platform(platform_name, credentials)` - Connect to a platform
- `disconnect_platform(platform_name)` - Disconnect from a platform
- `verify_connection(platform_name, timeout_seconds)` - Verify connection is valid
- `test_connection(platform_name, credentials)` - Test without storing
- `list_available_platforms()` - List all available platforms
- `list_connections()` - List active connections

#### 2. ConnectorManager (`connector_manager.py`)
Manages the lifecycle of platform connectors.

**Features:**
- Auto-discovery of connectors from plugins directory
- Connector registration and validation
- Connector isolation (failures don't affect other connectors)

**Key Methods:**
- `register(connector)` - Register a new connector
- `get(name)` - Get connector by name
- `list_connectors()` - List all registered connectors

### Frontend Components

#### 1. PlatformConnectionManager (`PlatformConnectionManager.tsx`)
Main UI component for managing platform connections.

**Features:**
- Display available platforms
- Show connection status
- Connection statistics dashboard
- Platform connection cards grid
- Credential form modal

#### 2. PlatformConnectionCard (`PlatformConnectionCard.tsx`)
Individual platform card component.

**Features:**
- Platform information display
- Connection status indicator
- Feature badges (training, inference, registry, tracking)
- Connection details (connected at, last verified)
- Action buttons (connect, verify, edit, disconnect)

#### 3. PlatformCredentialForm (`PlatformCredentialForm.tsx`)
Modal form for entering platform credentials.

**Features:**
- Dynamic credential fields based on platform requirements
- Password field visibility toggle
- Test connection functionality
- Security notice
- Form validation

## API Endpoints

### Platform Management

```
GET    /api/platforms                      - List available platforms
POST   /api/platforms/connect              - Connect to a platform
POST   /api/platforms/disconnect/{name}    - Disconnect from a platform
POST   /api/platforms/verify/{name}        - Verify connection
POST   /api/platforms/test                 - Test connection without storing
GET    /api/platforms/connections          - List active connections
GET    /api/platforms/connection/{name}    - Get specific connection
PUT    /api/platforms/credentials/{name}   - Update credentials
POST   /api/platforms/verify-all           - Verify all connections
GET    /api/platforms/stats                - Get connection statistics
```

## Security

### Credential Storage
- Credentials are stored in OS-level keystore:
  - Windows: Credential Manager
  - macOS: Keychain
  - Linux: Secret Service
- Additional encryption layer using Fernet symmetric encryption
- Credentials never logged or transmitted in plain text

### Connection Verification
- Timeout enforcement (default 5 seconds)
- Error isolation between connectors
- Secure credential validation

## Property-Based Testing

### Property 11: Platform Connection Verification

**Test File:** `test_platform_connection_verification.py`

**Properties Tested:**
1. Invalid credentials detected within 5 seconds
2. Valid credentials verified within 5 seconds
3. Timeout parameter is enforced
4. Verification result has consistent structure
5. Verification updates connection status

**Validates:** Requirements 1.4, 1.5

## Usage Example

### Backend

```python
from services.platform_connection_service import get_platform_connection_service

# Get service
service = get_platform_connection_service()

# Connect to a platform
connection = await service.connect_platform(
    platform_name='runpod',
    credentials={'api_key': 'your_api_key'}
)

# Verify connection
result = await service.verify_connection('runpod', timeout_seconds=5)
print(f"Connection valid: {result['valid']}")

# List connections
connections = service.list_connections()
for conn in connections:
    print(f"{conn.display_name}: {conn.status}")

# Disconnect
await service.disconnect_platform('runpod')
```

### Frontend

```tsx
import { PlatformConnectionManager } from './components/PlatformConnectionManager';

function App() {
  return (
    <div>
      <PlatformConnectionManager />
    </div>
  );
}
```

## Requirements Validation

### Requirement 1.1 ✓
Platform connections screen displays cards for all supported platforms with connection status.

### Requirement 1.2 ✓
Credentials are prompted and stored securely in OS keystore with encryption.

### Requirement 1.3 ✓
All API keys are encrypted and never stored in plain text.

### Requirement 1.4 ✓
Connection verification via test API call with timeout enforcement (≤5 seconds).

### Requirement 1.5 ✓
Specific error messages and troubleshooting steps displayed on connection failure.

## Testing

Run the property-based tests:

```bash
cd backend
python -m pytest tests/test_platform_connection_verification.py -v
```

All tests should pass, validating:
- Connection verification speed (≤5 seconds)
- Invalid credential detection
- Timeout enforcement
- Result structure consistency
- Status updates

## Future Enhancements

1. **Automatic Reconnection**: Retry failed connections with exponential backoff
2. **Connection Health Monitoring**: Periodic background verification
3. **Credential Rotation**: Support for automatic credential rotation
4. **Multi-Account Support**: Multiple accounts per platform
5. **Connection Profiles**: Save and load connection configurations
6. **Audit Logging**: Track all connection events for security
