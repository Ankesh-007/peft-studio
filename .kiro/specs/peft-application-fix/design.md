# Design Document

## Overview

This design addresses the critical issues preventing PEFT Studio from functioning after installation. The root causes are:

1. **Backend Service Not Starting**: The Python backend is not initializing properly, causing a blank window
2. **Missing PEFT Options**: The UI doesn't display all available PEFT algorithms
3. **No Dependency Verification**: Users don't know if Python/CUDA dependencies are installed
4. **Bloated Repository**: Unnecessary files increase download size and clutter the repo
5. **Incomplete Error Handling**: Users see blank screens instead of helpful error messages

The solution involves improving the backend startup process, enhancing the UI to show all PEFT options, adding dependency checks, cleaning up the repository, and implementing better error handling.

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Electron Main Process                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Backend Service Manager                                │ │
│  │  - Start Python FastAPI server                         │ │
│  │  - Monitor health and restart if needed                │ │
│  │  - Handle IPC communication                            │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            ├─ IPC ─┐
                            │       │
┌───────────────────────────▼───┐   │   ┌──────────────────────▼──────┐
│   React Frontend (Renderer)   │   │   │   Python Backend (FastAPI)  │
│  ┌──────────────────────────┐ │   │   │  ┌───────────────────────┐  │
│  │  Dependency Checker      │ │   │   │  │  PEFT Service         │  │
│  │  - Verify Python         │ │   │   │  │  - LoRA               │  │
│  │  - Verify CUDA           │ │   │   │  │  - QLoRA              │  │
│  │  - Verify packages       │ │   │   │  │  - DoRA               │  │
│  └──────────────────────────┘ │   │   │  │  - PiSSA              │  │
│  ┌──────────────────────────┐ │   │   │  │  - RSLoRA             │  │
│  │  PEFT Configuration UI   │ │◄──┼───┤  └───────────────────────┘  │
│  │  - Algorithm selector    │ │   │   │  ┌───────────────────────┐  │
│  │  - Parameter controls    │ │   │   │  │  Hardware Service     │  │
│  │  - Real-time validation  │ │   │   │  │  - GPU detection      │  │
│  └──────────────────────────┘ │   │   │  │  - CUDA validation    │  │
│  ┌──────────────────────────┐ │   │   │  └───────────────────────┘  │
│  │  Error Display           │ │   │   │  ┌───────────────────────┐  │
│  │  - Startup errors        │ │   │   │  │  Health Check         │  │
│  │  - Dependency issues     │ │   │   │  │  - /api/health        │  │
│  │  - Recovery actions      │ │   │   │  │  - /api/dependencies  │  │
│  └──────────────────────────┘ │   │   │  └───────────────────────┘  │
└────────────────────────────────┘   │   └─────────────────────────────┘
                                     │
                            Health Checks
                            Status Updates
```

## Components and Interfaces

### 1. Backend Service Manager (Electron Main Process)

**Purpose**: Manage the Python backend lifecycle

**Interface**:
```typescript
interface BackendServiceManager {
  start(): Promise<BackendStatus>;
  stop(): Promise<void>;
  restart(): Promise<BackendStatus>;
  getStatus(): BackendStatus;
  onStatusChange(callback: (status: BackendStatus) => void): void;
}

interface BackendStatus {
  running: boolean;
  port: number;
  pid?: number;
  error?: string;
  startTime?: Date;
}
```

**Key Methods**:
- `startPythonBackend()`: Launch FastAPI server with proper error handling
- `checkBackendHealth()`: Poll /api/health endpoint
- `handleBackendCrash()`: Restart backend and notify frontend
- `killBackendProcess()`: Clean shutdown of Python process

### 2. Dependency Checker (Frontend)

**Purpose**: Verify all required dependencies are installed

**Interface**:
```typescript
interface DependencyChecker {
  checkAll(): Promise<DependencyReport>;
  checkPython(): Promise<DependencyCheck>;
  checkCUDA(): Promise<DependencyCheck>;
  checkPackages(): Promise<PackageCheck[]>;
}

interface DependencyReport {
  allPassed: boolean;
  checks: DependencyCheck[];
  recommendations: string[];
}

interface DependencyCheck {
  name: string;
  required: boolean;
  installed: boolean;
  version?: string;
  expectedVersion?: string;
  error?: string;
  fixInstructions?: string;
}
```

### 3. PEFT Configuration UI (Frontend)

**Purpose**: Display all PEFT algorithms and their parameters

**Interface**:
```typescript
interface PEFTConfigurationProps {
  onConfigChange: (config: PEFTConfig) => void;
  hardwareProfile?: HardwareProfile;
  modelInfo?: ModelInfo;
}

interface PEFTConfig {
  algorithm: 'lora' | 'qlora' | 'dora' | 'pissa' | 'rslora';
  r: number;
  loraAlpha: number;
  loraDropout: number;
  targetModules: string[];
  useRSLoRA: boolean;
  useDoRA: boolean;
  usePiSSA: boolean;
}

interface AlgorithmOption {
  id: string;
  name: string;
  description: string;
  recommended: boolean;
  requirements: string[];
  parameters: ParameterDefinition[];
}
```

### 4. Enhanced Backend Health API

**New Endpoints**:

```python
@app.get("/api/health")
async def health_check():
    """Quick health check - no heavy imports"""
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/api/dependencies")
async def check_dependencies():
    """Check all Python dependencies"""
    return {
        "python_version": sys.version,
        "torch_available": torch_available,
        "cuda_available": cuda_available,
        "transformers_version": transformers_version,
        "peft_version": peft_version,
        "unsloth_available": unsloth_available,
        "missing_packages": []
    }

@app.get("/api/peft/algorithms")
async def list_peft_algorithms():
    """Get all supported PEFT algorithms with descriptions"""
    return {
        "algorithms": [
            {
                "id": "lora",
                "name": "LoRA",
                "description": "Low-Rank Adaptation - efficient fine-tuning",
                "recommended": True,
                "parameters": [...]
            },
            {
                "id": "qlora",
                "name": "QLoRA",
                "description": "Quantized LoRA - 4-bit quantization for lower memory",
                "recommended": True,
                "parameters": [...]
            },
            {
                "id": "dora",
                "name": "DoRA",
                "description": "Weight-Decomposed Low-Rank Adaptation",
                "recommended": False,
                "parameters": [...]
            },
            {
                "id": "pissa",
                "name": "PiSSA",
                "description": "Principal Singular values and Singular vectors Adaptation",
                "recommended": False,
                "parameters": [...]
            },
            {
                "id": "rslora",
                "name": "RSLoRA",
                "description": "Rank-Stabilized LoRA",
                "recommended": False,
                "parameters": [...]
            }
        ]
    }
```

## Data Models

### PEFT Algorithm Configuration

```python
class PEFTAlgorithm(str, Enum):
    LORA = "lora"
    QLORA = "qlora"
    DORA = "dora"
    PISSA = "pissa"
    RSLORA = "rslora"

@dataclass
class PEFTConfig:
    algorithm: PEFTAlgorithm
    r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    target_modules: List[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ])
    bias: str = "none"
    task_type: str = "CAUSAL_LM"
    use_rslora: bool = False
    use_dora: bool = False
    use_pissa: bool = False
```

### Dependency Status

```typescript
interface DependencyStatus {
  python: {
    installed: boolean;
    version: string;
    path: string;
  };
  cuda: {
    available: boolean;
    version?: string;
    devices: GPUDevice[];
  };
  packages: {
    torch: PackageInfo;
    transformers: PackageInfo;
    peft: PackageInfo;
    unsloth: PackageInfo;
    bitsandbytes: PackageInfo;
  };
}

interface PackageInfo {
  installed: boolean;
  version?: string;
  required: string;
  compatible: boolean;
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Backend Service Initialization
*For any* application startup, the backend service should either start successfully and respond to health checks, or fail with a clear error message explaining the issue.
**Validates: Requirements 1.1, 1.2, 1.4**

### Property 2: PEFT Algorithm Completeness
*For any* PEFT algorithm defined in the backend (LoRA, QLoRA, DoRA, PiSSA, RSLoRA), the frontend UI should display that algorithm as a selectable option with its parameters.
**Validates: Requirements 2.1, 2.2**

### Property 3: Dependency Verification Accuracy
*For any* dependency check, if a required dependency is missing, the system should report it as missing and provide installation instructions.
**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 4: Repository Cleanup Idempotence
*For any* cleanup operation, running it multiple times should produce the same result as running it once (no files should be removed that weren't already removed).
**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

### Property 5: Error Message Clarity
*For any* error condition, the system should display an error message that includes: what went wrong, why it happened, and how to fix it.
**Validates: Requirements 6.4, 7.3**

### Property 6: Backend Health Monitoring
*For any* running backend service, health checks should succeed within 5 seconds, or the service should be marked as unhealthy and restarted.
**Validates: Requirements 1.1, 7.1**

## Error Handling

### Startup Errors

1. **Python Not Found**
   - Detection: Check `python --version` command
   - Message: "Python 3.10+ is required but not found. Please install Python from python.org"
   - Recovery: Show installation link, offer to open browser

2. **Backend Port Conflict**
   - Detection: Port 8000 already in use
   - Message: "Backend port 8000 is in use. Trying alternative port..."
   - Recovery: Try ports 8001-8010, update frontend config

3. **Missing Python Packages**
   - Detection: Import errors in backend
   - Message: "Required packages missing: torch, transformers, peft. Click to install."
   - Recovery: Offer to run `pip install -r requirements.txt`

4. **CUDA Not Available**
   - Detection: `torch.cuda.is_available()` returns False
   - Message: "CUDA not detected. Training will use CPU (slower). Install CUDA for GPU acceleration."
   - Recovery: Continue with CPU, show CUDA installation guide

### Runtime Errors

1. **Backend Crash**
   - Detection: Health check fails 3 times
   - Message: "Backend service stopped unexpectedly. Restarting..."
   - Recovery: Automatic restart, show logs if restart fails

2. **Out of Memory**
   - Detection: CUDA OOM error
   - Message: "GPU out of memory. Try reducing batch size or using quantization."
   - Recovery: Suggest configuration changes

3. **Model Load Failure**
   - Detection: HuggingFace Hub error
   - Message: "Failed to load model. Check internet connection and model name."
   - Recovery: Retry with exponential backoff

## Testing Strategy

### Unit Tests

1. **Backend Service Manager**
   - Test starting/stopping Python process
   - Test health check polling
   - Test error handling for missing Python
   - Test port conflict resolution

2. **Dependency Checker**
   - Test Python version detection
   - Test CUDA availability check
   - Test package version parsing
   - Test error message generation

3. **PEFT Configuration**
   - Test algorithm list fetching
   - Test parameter validation
   - Test configuration serialization

### Property-Based Tests

We will use Hypothesis (Python) and fast-check (TypeScript) for property-based testing.

**Test Framework**: Hypothesis 6.92.1+ (Python), fast-check 3.15.0+ (TypeScript)
**Test Configuration**: Minimum 100 iterations per property test

1. **Property 1: Backend Service Initialization**
   ```python
   @given(st.integers(min_value=8000, max_value=9000))
   def test_backend_starts_on_any_available_port(port):
       """Backend should start on any available port"""
       service = BackendServiceManager(port=port)
       status = service.start()
       assert status.running or status.error is not None
   ```

2. **Property 2: PEFT Algorithm Completeness**
   ```typescript
   fc.assert(
     fc.property(fc.constantFrom(...PEFTAlgorithms), (algorithm) => {
       const uiOptions = getPEFTOptions();
       return uiOptions.some(opt => opt.id === algorithm);
     })
   );
   ```

3. **Property 3: Dependency Verification Accuracy**
   ```python
   @given(st.lists(st.text(), min_size=1))
   def test_missing_packages_reported(missing_packages):
       """All missing packages should be reported"""
       report = check_dependencies(mock_missing=missing_packages)
       for pkg in missing_packages:
           assert any(pkg in check.name for check in report.checks if not check.installed)
   ```

### Integration Tests

1. **End-to-End Startup**
   - Launch Electron app
   - Verify backend starts
   - Verify UI loads
   - Verify PEFT options appear

2. **Dependency Check Flow**
   - Mock missing Python
   - Verify error message
   - Verify recovery instructions

3. **PEFT Configuration Flow**
   - Select each algorithm
   - Verify parameters update
   - Verify validation works

## Implementation Plan

### Phase 1: Backend Service Management (Priority: Critical)

1. Enhance `electron/main.js`:
   - Add robust Python process management
   - Implement health check polling
   - Add automatic restart on crash
   - Improve error logging

2. Add backend health endpoints:
   - `/api/health` - Quick health check
   - `/api/dependencies` - Dependency status
   - `/api/startup/status` - Detailed startup info

### Phase 2: PEFT Options Display (Priority: High)

1. Update backend PEFT service:
   - Add algorithm descriptions
   - Add parameter definitions
   - Add recommended use cases

2. Create PEFT configuration component:
   - Algorithm selector with descriptions
   - Dynamic parameter controls
   - Real-time validation
   - Help tooltips

### Phase 3: Dependency Verification (Priority: High)

1. Create dependency checker service:
   - Python version check
   - CUDA availability check
   - Package version checks
   - Generate fix instructions

2. Add dependency status UI:
   - Show all checks on startup
   - Display errors prominently
   - Provide one-click fixes where possible

### Phase 4: Repository Cleanup (Priority: Medium)

1. Identify files to remove:
   - Build artifacts in `release/`
   - Test cache in `.hypothesis/`, `.pytest_cache/`
   - Redundant docs
   - Old spec files

2. Update `.gitignore`:
   - Add patterns for removed files
   - Ensure they don't come back

3. Create cleanup script:
   - Automated cleanup before release
   - Verify no critical files removed

### Phase 5: Release Process (Priority: Medium)

1. Version bump to 1.0.1
2. Generate changelog
3. Build installers
4. Test installers on clean systems
5. Publish GitHub release

## Repository Cleanup Details

### Files to Remove

**Build Artifacts** (Safe to remove, regenerated on build):
- `release/` - All built installers
- `dist/` - Frontend build output
- `build/` - Electron build cache

**Test Artifacts** (Safe to remove, regenerated on test):
- `.hypothesis/` - Hypothesis test cache
- `.pytest_cache/` - Pytest cache
- `backend/.hypothesis/` - Backend test cache
- `backend/.pytest_cache/` - Backend pytest cache
- `coverage/` - Test coverage reports

**Redundant Documentation** (Consolidate or remove):
- `DEPLOYMENT_COMPLETE.md` - Merge into CHANGELOG
- `RELEASE_v1.0.0_COMPLETE.md` - Merge into CHANGELOG
- `RELEASE_TESTING_COMPLETE.md` - Merge into CHANGELOG
- `FILES_CREATED.md` - Remove (outdated)
- `BUILD_SUMMARY.md` - Merge into BUILDING.md
- `CLEANUP_COMPLETE.md` - Remove (task complete)
- `CLEANUP_STATUS.md` - Remove (task complete)
- `REPOSITORY_CLEANUP_COMPLETE.md` - Remove (task complete)
- `REPO_CLEANUP_PLAN.md` - Remove (task complete)
- `TEST_STATUS.md` - Move to docs/developer-guide/

**Spec Files** (Keep active, remove completed):
- `.kiro/specs/codebase-cleanup/` - Remove (completed)
- `.kiro/specs/github-releases-installer/` - Keep (reference)
- `.kiro/specs/unified-llm-platform/` - Keep (future work)

### Updated .gitignore

```gitignore
# Build outputs
dist/
build/
release/
out/

# Test artifacts
.hypothesis/
.pytest_cache/
coverage/
.nyc_output/

# Temporary documentation
*_COMPLETE.md
*_STATUS.md
*_SUMMARY.md
```

## Security Considerations

1. **Backend Process Isolation**
   - Run Python backend with minimal privileges
   - Validate all IPC messages
   - Sanitize file paths

2. **Dependency Verification**
   - Verify package signatures where possible
   - Warn about unofficial packages
   - Check for known vulnerabilities

3. **Error Messages**
   - Don't expose system paths in production
   - Sanitize error messages
   - Log full details securely

## Performance Considerations

1. **Fast Startup**
   - Lazy load heavy Python imports
   - Start backend in parallel with UI
   - Cache dependency checks

2. **Responsive UI**
   - Show loading states during checks
   - Don't block on backend startup
   - Progressive enhancement

3. **Memory Efficiency**
   - Unload unused models
   - Clear caches periodically
   - Monitor memory usage

## Deployment

### Build Process

1. Clean workspace
2. Install dependencies
3. Run tests
4. Build frontend
5. Package Electron app
6. Generate checksums
7. Create GitHub release

### Release Checklist

- [ ] Version bumped in package.json
- [ ] CHANGELOG.md updated
- [ ] All tests passing
- [ ] Installers built for all platforms
- [ ] Checksums generated
- [ ] Release notes written
- [ ] GitHub release created
- [ ] Documentation updated

## Migration Notes

### For Users

- No data migration needed
- Settings preserved
- Automatic update available

### For Developers

- New dependency checker API
- Enhanced PEFT configuration
- Improved error handling patterns
