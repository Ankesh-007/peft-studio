# Design Document

## Overview

PEFT Studio will be transformed into a unified desktop platform that integrates with all major cloud GPU providers, model registries, experiment tracking tools, and deployment platforms. The architecture follows an offline-first, modular design with a pluggable connector system that allows easy integration of new platforms.

The system consists of three main layers:
1. **Frontend Layer**: Electron-based desktop UI with React and Tailwind CSS
2. **Backend Layer**: Python FastAPI service for orchestration, connectors, and local inference
3. **Connector Layer**: Pluggable modules for platform integration

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Electron Desktop App                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  React UI  │  │  WebSocket │  │   Gradio   │            │
│  │  + Tailwind│  │   Client   │  │   Embed    │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
                          │ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│              Python FastAPI Backend (localhost)              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │Orchestrator│  │  Connector │  │  Inference │            │
│  │  Service   │  │  Manager   │  │   Engine   │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│                    Connector Layer                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ RunPod   │ │HuggingFace│ │ Predibase│ │  W&B     │      │
│  │Connector │ │ Connector │ │Connector │ │Connector │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│                    External Platforms                        │
│  RunPod │ Lambda │ Vast.ai │ HuggingFace │ Predibase │...  │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

**Frontend (Electron + React)**
- Main window with navigation
- Platform connection manager
- Model browser and selector
- Training configuration wizard
- Real-time monitoring dashboard
- Inference playground
- Experiment comparison view
- Settings and preferences

**Backend (FastAPI)**
- REST API for CRUD operations
- WebSocket server for real-time updates
- Job orchestration and state management
- Connector registry and lifecycle management
- Local inference engine
- Cache management
- Offline queue management

**Storage**
- SQLite database for metadata
- Local file system for artifacts (.safetensors, logs)
- OS keystore for credentials
- IndexedDB for frontend cache

## Components and Interfaces

### 1. Connector Interface

All platform connectors must implement this standard interface:

```python
class PlatformConnector(ABC):
    @abstractmethod
    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Verify connection and store credentials"""
        pass
    
    @abstractmethod
    async def submit_job(self, config: TrainingConfig) -> str:
        """Submit training job, return job_id"""
        pass
    
    @abstractmethod
    async def stream_logs(self, job_id: str) -> AsyncIterator[str]:
        """Stream logs in real-time"""
        pass
    
    @abstractmethod
    async def fetch_artifact(self, job_id: str) -> bytes:
        """Download trained adapter"""
        pass
    
    @abstractmethod
    async def upload_artifact(self, path: str, metadata: Dict) -> str:
        """Upload adapter to registry"""
        pass
    
    @abstractmethod
    async def list_resources(self) -> List[Resource]:
        """List available compute resources"""
        pass
    
    @abstractmethod
    async def get_pricing(self, resource_id: str) -> PricingInfo:
        """Get current pricing for resource"""
        pass
```

### 2. Training Configuration

```python
@dataclass
class TrainingConfig:
    # Model
    base_model: str
    model_source: str  # huggingface, civitai, ollama
    
    # PEFT
    algorithm: str  # lora, qlora, dora, pissa, rslora
    rank: int
    alpha: int
    dropout: float
    target_modules: List[str]
    
    # Quantization
    quantization: Optional[str]  # int8, int4, nf4
    
    # Training
    learning_rate: float
    batch_size: int
    gradient_accumulation_steps: int
    num_epochs: int
    warmup_steps: int
    
    # Compute
    provider: str  # runpod, lambda, vastai, local
    resource_id: str
    
    # Dataset
    dataset_path: str
    validation_split: float
    
    # Tracking
    experiment_tracker: Optional[str]  # wandb, cometml, phoenix
    project_name: str
    
    # Output
    output_dir: str
    checkpoint_steps: int
```


### 3. Orchestrator Service

The orchestrator manages training jobs across all providers:

```python
class TrainingOrchestrator:
    def __init__(self):
        self.connector_manager = ConnectorManager()
        self.job_queue = JobQueue()
        self.state_manager = StateManager()
    
    async def start_training(self, config: TrainingConfig) -> str:
        """Start training on selected provider"""
        connector = self.connector_manager.get(config.provider)
        job_id = await connector.submit_job(config)
        await self.state_manager.save_job(job_id, config)
        asyncio.create_task(self._monitor_job(job_id, connector))
        return job_id
    
    async def _monitor_job(self, job_id: str, connector: PlatformConnector):
        """Monitor job and stream updates"""
        async for log in connector.stream_logs(job_id):
            await self.broadcast_log(job_id, log)
        
        # Download artifact when complete
        artifact = await connector.fetch_artifact(job_id)
        await self.save_artifact(job_id, artifact)
```

### 4. Connector Manager

Manages lifecycle of all connectors:

```python
class ConnectorManager:
    def __init__(self):
        self.connectors: Dict[str, PlatformConnector] = {}
        self.discover_connectors()
    
    def discover_connectors(self):
        """Auto-discover connectors from plugins directory"""
        for module in self._scan_plugins():
            connector = self._load_connector(module)
            self.register(connector)
    
    def register(self, connector: PlatformConnector):
        """Register a new connector"""
        self.connectors[connector.name] = connector
    
    def get(self, name: str) -> PlatformConnector:
        """Get connector by name"""
        return self.connectors.get(name)
```

### 5. Offline Queue Manager

Handles operations when offline:

```python
class OfflineQueueManager:
    def __init__(self):
        self.queue = deque()
        self.db = SQLiteDB()
    
    async def enqueue(self, operation: Operation):
        """Add operation to queue"""
        self.queue.append(operation)
        await self.db.save_operation(operation)
    
    async def sync(self):
        """Sync queued operations when online"""
        while self.queue:
            operation = self.queue.popleft()
            try:
                await operation.execute()
                await self.db.mark_complete(operation.id)
            except Exception as e:
                self.queue.appendleft(operation)
                break
```

## Data Models

### Database Schema

```sql
-- Training Jobs
CREATE TABLE training_jobs (
    id TEXT PRIMARY KEY,
    config JSON NOT NULL,
    provider TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error TEXT,
    metrics JSON
);

-- Adapters
CREATE TABLE adapters (
    id TEXT PRIMARY KEY,
    job_id TEXT REFERENCES training_jobs(id),
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    size_bytes INTEGER,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Platform Connections
CREATE TABLE platform_connections (
    id TEXT PRIMARY KEY,
    platform_name TEXT NOT NULL,
    status TEXT NOT NULL,
    last_verified TIMESTAMP,
    metadata JSON
);

-- Offline Queue
CREATE TABLE offline_queue (
    id TEXT PRIMARY KEY,
    operation_type TEXT NOT NULL,
    payload JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending'
);

-- Model Cache
CREATE TABLE model_cache (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    model_id TEXT NOT NULL,
    metadata JSON,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);
```

### File System Structure

```
~/.peft-studio/
├── config/
│   ├── settings.json
│   └── connectors.json
├── data/
│   ├── peft_studio.db
│   └── cache/
│       ├── models/
│       └── datasets/
├── artifacts/
│   ├── adapters/
│   │   ├── {job_id}/
│   │   │   ├── adapter_model.safetensors
│   │   │   ├── adapter_config.json
│   │   │   └── training_args.json
│   └── exports/
├── logs/
│   ├── training/
│   └── system/
└── plugins/
    └── connectors/
        ├── runpod_connector.py
        ├── huggingface_connector.py
        └── ...
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Connector interface compliance
*For any* registered connector, calling all interface methods should succeed without raising NotImplementedError
**Validates: Requirements 13.1, 13.2**

### Property 2: Credential encryption round-trip
*For any* API credential stored in the keystore, retrieving and decrypting should produce the original value
**Validates: Requirements 15.1, 15.2**

### Property 3: Offline queue persistence
*For any* operation enqueued while offline, the operation should persist across application restarts until successfully synced
**Validates: Requirements 12.2, 12.4**

### Property 4: Training configuration completeness
*For any* training configuration, all required fields should be populated before submission is allowed
**Validates: Requirements 4.1, 4.2**

### Property 5: Cost estimation accuracy
*For any* training configuration, estimated cost should be within 20% of actual cost for completed runs
**Validates: Requirements 3.2, 17.4**

### Property 6: Model metadata caching
*For any* model browsed while online, metadata should be available offline for at least 24 hours
**Validates: Requirements 2.4, 12.1**

### Property 7: Adapter artifact integrity
*For any* downloaded adapter, the file hash should match the hash provided by the training platform
**Validates: Requirements 5.5, 8.2**

### Property 8: Hot-swap adapter loading
*For any* two adapters on the same base model, switching between them should not require reloading the base model
**Validates: Requirements 10.5**

### Property 9: Multi-run isolation
*For any* two concurrent training runs, metrics and logs should never be mixed or cross-contaminated
**Validates: Requirements 16.1, 16.3**

### Property 10: Configuration export round-trip
*For any* training configuration, exporting then importing should produce an equivalent configuration
**Validates: Requirements 18.1, 18.2**

### Property 11: Platform connection verification
*For any* platform connection, the system should detect invalid credentials within 5 seconds
**Validates: Requirements 1.4, 1.5**

### Property 12: Resource usage limits
*For any* application state, idle memory usage should never exceed 500MB and idle CPU should never exceed 1%
**Validates: Requirements 14.1, 14.4**

### Property 13: Experiment tracker synchronization
*For any* training run with experiment tracking enabled, all metrics should be logged to the tracker within 30 seconds of generation
**Validates: Requirements 6.2, 6.3**

### Property 14: Deployment endpoint availability
*For any* deployed adapter, the inference endpoint should respond to test requests within 10 seconds
**Validates: Requirements 9.4, 9.5**

### Property 15: Gradio demo generation
*For any* adapter, generating a Gradio demo should produce a functional interface with working inference
**Validates: Requirements 11.1, 11.2**

### Property 16: Error log completeness
*For any* training error, the diagnostic report should include timestamp, error message, stack trace, and system state
**Validates: Requirements 19.2, 19.5**

### Property 17: Dashboard data freshness
*For any* active training run, dashboard metrics should update within 5 seconds of new data availability
**Validates: Requirements 20.2, 20.5**

### Property 18: Connector failure isolation
*For any* connector failure, other connectors should continue functioning normally
**Validates: Requirements 13.3**

### Property 19: Startup time constraint
*For any* application launch, the main UI should be interactive within 3 seconds
**Validates: Requirements 14.1**

### Property 20: Bundle size constraint
*For any* production build, the total installation size should not exceed 200MB
**Validates: Requirements 14.2**

## Error Handling

### Error Categories

1. **Connection Errors**
   - Network timeout
   - Invalid credentials
   - Platform API unavailable
   - Rate limiting

2. **Training Errors**
   - Out of memory
   - Model not found
   - Dataset format invalid
   - Compute resource unavailable

3. **System Errors**
   - Disk space insufficient
   - Permission denied
   - Corrupted data
   - Version incompatibility

### Error Recovery Strategies

**Connection Errors:**
- Implement exponential backoff (1s, 2s, 4s, 8s, max 3 retries)
- Cache last successful response
- Switch to offline mode automatically
- Provide manual retry option

**Training Errors:**
- Auto-save checkpoint before failure
- Suggest configuration adjustments
- Offer alternative compute providers
- Enable resume from last checkpoint

**System Errors:**
- Prompt for user action (free disk space, grant permissions)
- Provide detailed troubleshooting steps
- Generate diagnostic report
- Offer safe mode startup

### Error Messages

All error messages follow this format:
```
[Plain Language Description]

What happened:
- Specific details about the error

What you can do:
1. [Action 1]
2. [Action 2]
3. [Action 3]

[Get Help Button] [Retry Button]
```


## Testing Strategy

### Unit Testing

**Backend Services:**
- Test each connector independently with mocked API responses
- Test orchestrator job lifecycle management
- Test offline queue persistence and sync
- Test credential encryption/decryption
- Test configuration validation

**Frontend Components:**
- Test UI components in isolation with React Testing Library
- Test state management with Redux/Zustand
- Test WebSocket connection handling
- Test offline mode UI behavior

### Property-Based Testing

Use **Hypothesis** (Python) for backend and **fast-check** (TypeScript) for frontend.

**Backend Properties:**
- Generate random training configurations and verify validation
- Generate random connector responses and verify parsing
- Generate random file sizes and verify streaming behavior
- Generate random credential strings and verify encryption round-trip

**Frontend Properties:**
- Generate random UI states and verify rendering
- Generate random user interactions and verify state updates
- Generate random network conditions and verify offline behavior

### Integration Testing

**End-to-End Flows:**
1. Connect platform → Browse models → Configure training → Start job → Monitor → Download adapter
2. Upload adapter → Deploy to platform → Test inference → Create Gradio demo
3. Start multiple runs → Compare results → Export configuration
4. Go offline → Queue operations → Go online → Verify sync

**Platform Integration:**
- Test with real API credentials in CI/CD (using secrets)
- Test with mock servers for development
- Test error scenarios (rate limits, timeouts, invalid responses)

### Performance Testing

**Metrics to Track:**
- Application startup time (target: <3s)
- Memory usage idle (target: <200MB)
- Memory usage during training (target: <500MB)
- CPU usage idle (target: <1%)
- Bundle size (target: <200MB)
- API response time (target: <100ms)
- WebSocket latency (target: <50ms)

**Load Testing:**
- Test with 10 concurrent training runs
- Test with 1000+ cached models
- Test with 100MB+ dataset files
- Test with 50+ adapters in library

### Security Testing

**Credential Security:**
- Verify credentials never logged
- Verify credentials encrypted at rest
- Verify credentials transmitted over HTTPS only
- Verify OS keystore integration

**Data Privacy:**
- Verify telemetry is opt-in
- Verify no PII in logs
- Verify user confirmation before uploads
- Verify data encryption for sensitive fields

## Deployment Strategy

### Development Environment

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Production Build

```bash
# Build frontend
npm run build

# Package Electron app
npm run package

# Output:
# - Windows: dist/PEFT-Studio-Setup-1.0.0.exe
# - macOS: dist/PEFT-Studio-1.0.0.dmg
# - Linux: dist/PEFT-Studio-1.0.0.AppImage
```

### Distribution

**Platforms:**
- GitHub Releases (primary)
- Microsoft Store (Windows)
- Mac App Store (macOS)
- Snap Store (Linux)

**Auto-Update:**
- Use electron-updater
- Check for updates on startup
- Download in background
- Prompt user to restart

### CI/CD Pipeline

```yaml
# .github/workflows/build.yml
name: Build and Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node
        uses: actions/setup-node@v3
      - name: Setup Python
        uses: actions/setup-python@v4
      - name: Run tests
        run: |
          npm test
          pytest
      - name: Build
        run: npm run package
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
```

## Performance Optimization

### Frontend Optimizations

**Code Splitting:**
```typescript
// Lazy load routes
const Dashboard = lazy(() => import('./components/Dashboard'));
const Training = lazy(() => import('./components/Training'));
const Inference = lazy(() => import('./components/Inference'));

// Lazy load heavy components
const ChartComponent = lazy(() => import('./components/Chart'));
```

**Memoization:**
```typescript
// Memoize expensive computations
const expensiveValue = useMemo(() => {
  return computeExpensiveValue(data);
}, [data]);

// Memoize components
const MemoizedComponent = memo(Component);
```

**Virtual Scrolling:**
```typescript
// Use react-window for large lists
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={items.length}
  itemSize={50}
>
  {Row}
</FixedSizeList>
```

### Backend Optimizations

**Lazy Loading:**
```python
# Load ML libraries only when needed
def load_model():
    import torch
    import transformers
    # ... load model
```

**Connection Pooling:**
```python
# Reuse HTTP connections
session = aiohttp.ClientSession()

# Reuse database connections
engine = create_async_engine(
    "sqlite+aiosqlite:///peft_studio.db",
    pool_size=5,
    max_overflow=10
)
```

**Caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_model_metadata(model_id: str):
    # Expensive API call
    return fetch_metadata(model_id)
```

### Asset Optimization

**Images:**
- Convert to WebP format
- Generate multiple sizes for responsive images
- Use lazy loading with intersection observer
- Implement blur-up placeholders

**Fonts:**
- Subset fonts to include only used characters
- Use font-display: swap
- Preload critical fonts

**Bundle:**
- Minify JavaScript and CSS
- Tree shake unused code
- Use compression (gzip/brotli)
- Analyze bundle with webpack-bundle-analyzer


## Security Architecture

### Credential Management

**Storage:**
```python
import keyring

# Store credentials
keyring.set_password("peft-studio", "runpod-api-key", api_key)

# Retrieve credentials
api_key = keyring.get_password("peft-studio", "runpod-api-key")

# Delete credentials
keyring.delete_password("peft-studio", "runpod-api-key")
```

**Encryption:**
```python
from cryptography.fernet import Fernet

class SecureStorage:
    def __init__(self):
        # Key stored in OS keystore
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> bytes:
        return self.cipher.encrypt(data.encode())
    
    def decrypt(self, encrypted: bytes) -> str:
        return self.cipher.decrypt(encrypted).decode()
```

### API Security

**Authentication:**
- Use token-based authentication for all API calls
- Rotate tokens periodically
- Implement token refresh mechanism
- Never log tokens or credentials

**Authorization:**
- Verify user permissions before operations
- Implement rate limiting per user
- Track API usage and quotas

**Data Transmission:**
- Use HTTPS for all external API calls
- Validate SSL certificates
- Implement certificate pinning for critical endpoints

### Data Privacy

**Telemetry:**
```python
class TelemetryService:
    def __init__(self):
        self.enabled = self._get_user_preference()
    
    def track_event(self, event: str, properties: Dict):
        if not self.enabled:
            return
        
        # Anonymize data
        anonymized = self._anonymize(properties)
        
        # Send to analytics
        self._send(event, anonymized)
    
    def _anonymize(self, data: Dict) -> Dict:
        # Remove PII
        data.pop('email', None)
        data.pop('username', None)
        # Hash identifiers
        if 'user_id' in data:
            data['user_id'] = hashlib.sha256(
                data['user_id'].encode()
            ).hexdigest()
        return data
```

**User Consent:**
- Explicit opt-in for telemetry
- Clear explanation of what data is collected
- Easy opt-out mechanism
- Export user data on request

## Connector Implementation Guide

### Creating a New Connector

**1. Create connector file:**
```python
# plugins/connectors/example_connector.py
from typing import Dict, List, AsyncIterator
from connectors.base import PlatformConnector, Resource, PricingInfo

class ExampleConnector(PlatformConnector):
    name = "example"
    display_name = "Example Platform"
    
    def __init__(self):
        self.api_key = None
        self.base_url = "https://api.example.com"
    
    async def connect(self, credentials: Dict[str, str]) -> bool:
        self.api_key = credentials.get("api_key")
        # Verify connection
        response = await self._make_request("/verify")
        return response.status == 200
    
    async def submit_job(self, config: TrainingConfig) -> str:
        payload = self._build_payload(config)
        response = await self._make_request("/jobs", method="POST", json=payload)
        return response.json()["job_id"]
    
    async def stream_logs(self, job_id: str) -> AsyncIterator[str]:
        async with self._websocket(f"/jobs/{job_id}/logs") as ws:
            async for message in ws:
                yield message
    
    async def fetch_artifact(self, job_id: str) -> bytes:
        response = await self._make_request(f"/jobs/{job_id}/artifact")
        return await response.read()
    
    async def upload_artifact(self, path: str, metadata: Dict) -> str:
        with open(path, 'rb') as f:
            response = await self._make_request(
                "/artifacts",
                method="POST",
                data=f,
                json=metadata
            )
        return response.json()["artifact_id"]
    
    async def list_resources(self) -> List[Resource]:
        response = await self._make_request("/resources")
        return [self._parse_resource(r) for r in response.json()]
    
    async def get_pricing(self, resource_id: str) -> PricingInfo:
        response = await self._make_request(f"/resources/{resource_id}/pricing")
        return self._parse_pricing(response.json())
```

**2. Register connector:**
```python
# connectors/__init__.py
from .example_connector import ExampleConnector

CONNECTORS = [
    ExampleConnector,
    # ... other connectors
]
```

**3. Add configuration:**
```json
// config/connectors.json
{
  "example": {
    "enabled": true,
    "credentials_required": ["api_key"],
    "features": ["training", "inference", "registry"],
    "documentation_url": "https://docs.example.com"
  }
}
```

### Connector Testing

```python
# tests/test_example_connector.py
import pytest
from connectors.example_connector import ExampleConnector

@pytest.fixture
async def connector():
    conn = ExampleConnector()
    await conn.connect({"api_key": "test_key"})
    return conn

@pytest.mark.asyncio
async def test_submit_job(connector):
    config = TrainingConfig(...)
    job_id = await connector.submit_job(config)
    assert job_id is not None

@pytest.mark.asyncio
async def test_stream_logs(connector):
    logs = []
    async for log in connector.stream_logs("test_job_id"):
        logs.append(log)
    assert len(logs) > 0
```

## UI/UX Design Patterns

### Navigation Structure

```
Dashboard (Home)
├── Training
│   ├── New Training Run
│   ├── Active Runs
│   └── Run History
├── Models
│   ├── Browse Models
│   ├── My Adapters
│   └── Deployed Models
├── Inference
│   ├── Playground
│   ├── Gradio Demos
│   └── API Testing
├── Platforms
│   ├── Connections
│   ├── Compute Resources
│   └── Usage & Billing
├── Experiments
│   ├── Tracking
│   ├── Comparison
│   └── Analysis
└── Settings
    ├── Preferences
    ├── Security
    └── About
```

### Key UI Components

**Platform Connection Card:**
```tsx
<PlatformCard
  name="RunPod"
  status="connected"
  icon={<RunPodIcon />}
  onConnect={() => handleConnect('runpod')}
  onDisconnect={() => handleDisconnect('runpod')}
  features={['Training', 'Inference']}
  lastVerified="2 hours ago"
/>
```

**Training Configuration Wizard:**
```tsx
<Wizard steps={[
  { title: 'Select Model', component: <ModelSelector /> },
  { title: 'Configure PEFT', component: <PEFTConfig /> },
  { title: 'Choose Compute', component: <ComputeSelector /> },
  { title: 'Upload Dataset', component: <DatasetUpload /> },
  { title: 'Review & Launch', component: <ReviewLaunch /> }
]} />
```

**Real-time Monitoring Dashboard:**
```tsx
<MonitoringDashboard
  jobId={jobId}
  metrics={['loss', 'learning_rate', 'gpu_usage']}
  refreshInterval={5000}
  onPause={() => handlePause(jobId)}
  onStop={() => handleStop(jobId)}
/>
```

### Responsive Design

**Breakpoints:**
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

**Adaptive Layouts:**
- Mobile: Single column, bottom navigation
- Tablet: Two columns, side navigation
- Desktop: Three columns, persistent sidebar

### Accessibility

**WCAG 2.1 AA Compliance:**
- Keyboard navigation for all features
- Screen reader support with ARIA labels
- Color contrast ratio ≥ 4.5:1
- Focus indicators on all interactive elements
- Skip navigation links

**Keyboard Shortcuts:**
- `Ctrl/Cmd + N`: New training run
- `Ctrl/Cmd + K`: Command palette
- `Ctrl/Cmd + ,`: Settings
- `Ctrl/Cmd + /`: Help
- `Esc`: Close modal/dialog

