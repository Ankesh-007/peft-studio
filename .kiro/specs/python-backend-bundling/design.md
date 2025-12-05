# Design Document: Python Backend Bundling

## Overview

This design document outlines the architecture and implementation strategy for bundling the Python backend into a self-contained executable within the PEFT Studio Electron application. The solution uses PyInstaller to compile the FastAPI backend and all its dependencies into platform-specific executables, eliminating the need for end users to install Python or manage dependencies manually.

The design maintains backward compatibility with the existing development workflow while adding production-ready bundling capabilities. It leverages the existing BackendServiceManager in electron/main.js and extends it to support both development (Python script) and production (bundled executable) modes seamlessly.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Electron Main Process                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         BackendServiceManager (Enhanced)               │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  Path Resolution Logic                           │ │ │
│  │  │  - Development: backend/main.py + python         │ │ │
│  │  │  - Production: resources/backend/peft_engine.exe │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  Process Lifecycle Management                    │ │ │
│  │  │  - Spawn backend process                         │ │ │
│  │  │  - Monitor health                                │ │ │
│  │  │  - Handle crashes/restarts                       │ │ │
│  │  │  - Clean shutdown (SIGTERM → SIGKILL)           │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ spawn
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Python Backend (Bundled Executable)             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  PyInstaller Bundle                                    │ │
│  │  - Python 3.10+ interpreter                           │ │
│  │  - FastAPI application (backend/main.py)              │ │
│  │  - All dependencies (torch, transformers, peft, etc.) │ │
│  │  - Service modules (lazy-loaded)                      │ │
│  │  - Configuration files                                │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/WebSocket
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Electron Renderer Process                 │
│                      (React Frontend)                        │
└─────────────────────────────────────────────────────────────┘
```

### Build Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Build Pipeline                           │
│                                                              │
│  1. Backend Compilation (PyInstaller)                       │
│     ├─ Analyze dependencies                                 │
│     ├─ Bundle Python interpreter                            │
│     ├─ Include all packages from requirements.txt           │
│     ├─ Add data files and configs                           │
│     └─ Generate platform-specific executable                │
│        └─ Output: backend/dist/peft_engine[.exe]            │
│                                                              │
│  2. Frontend Compilation (Vite + TypeScript)                │
│     ├─ Transpile TypeScript                                 │
│     ├─ Bundle React components                              │
│     ├─ Optimize assets                                      │
│     └─ Output: dist/                                        │
│                                                              │
│  3. Electron Packaging (electron-builder)                   │
│     ├─ Copy frontend dist/ to app                           │
│     ├─ Copy backend executable to extraResources            │
│     ├─ Sign executables (Windows/macOS)                     │
│     ├─ Create installer (NSIS/DMG/AppImage)                 │
│     └─ Output: release/PEFT-Studio-Setup-*.exe              │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. PyInstaller Configuration

**Purpose:** Define how the Python backend is compiled into a standalone executable.

**Location:** `backend/peft_engine.spec`

**Key Configuration:**
- Entry point: `backend/main.py`
- Output name: `peft_engine`
- Console mode: Hidden (`--noconsole`)
- Bundle mode: Single file (`--onefile`)
- Data files: Configuration files, model metadata
- Hidden imports: Dynamically loaded modules

**Interface:**
```python
# peft_engine.spec
a = Analysis(
    ['main.py'],
    pathex=['backend'],
    binaries=[],
    datas=[
        ('config.py', '.'),
        ('services/*.py', 'services'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        # Add all lazy-loaded service modules
        'services.peft_service',
        'services.hardware_service',
        # ... etc
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
```

### 2. Enhanced BackendServiceManager

**Purpose:** Manage backend process lifecycle with support for both development and production modes.

**Location:** `electron/main.js` (existing, to be enhanced)

**Key Methods:**

```javascript
class BackendServiceManager {
  // Enhanced method to resolve backend path
  getBackendPath() {
    if (app.isPackaged) {
      // Production: use bundled executable
      const platform = process.platform;
      const exeName = platform === 'win32' ? 'peft_engine.exe' : 'peft_engine';
      return path.join(process.resourcesPath, 'backend', exeName);
    } else {
      // Development: use Python script
      return {
        script: path.join(__dirname, '../backend/main.py'),
        interpreter: await this.findPythonExecutable()
      };
    }
  }

  // Enhanced start method
  async start() {
    const backendPath = this.getBackendPath();
    
    if (app.isPackaged) {
      // Spawn bundled executable
      this.process = spawn(backendPath, [], {
        env: { ...process.env, PYTHONUNBUFFERED: '1' },
        stdio: 'pipe'
      });
    } else {
      // Spawn Python script
      this.process = spawn(backendPath.interpreter, [backendPath.script], {
        env: { ...process.env, PYTHONUNBUFFERED: '1' },
        stdio: 'pipe'
      });
    }
    
    // Existing process management logic...
  }

  // Enhanced stop method with proper cleanup
  async stop() {
    if (!this.process) return;
    
    this.isShuttingDown = true;
    this.stopHealthChecks();
    
    // Send SIGTERM for graceful shutdown
    this.process.kill('SIGTERM');
    
    // Wait 1 second for graceful shutdown
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Force kill if still running
    if (this.process && !this.process.killed) {
      log.warn('Backend did not terminate gracefully, forcing kill');
      this.process.kill('SIGKILL');
    }
    
    this.process = null;
  }
}
```

### 3. Build Scripts

**Purpose:** Automate the build process for all platforms.

**Location:** `package.json` (scripts section)

**New Scripts:**
```json
{
  "scripts": {
    "build:backend": "cd backend && pyinstaller peft_engine.spec --clean",
    "build:backend:verify": "node scripts/verify-backend-build.js",
    "build:frontend": "tsc && vite build",
    "build:all": "npm run build:backend && npm run build:backend:verify && npm run build:frontend",
    "build:win": "npm run build:all && electron-builder build --win --x64",
    "build:mac": "npm run build:all && electron-builder build --mac --x64 --arm64",
    "build:linux": "npm run build:all && electron-builder build --linux --x64"
  }
}
```

**Verification Script:** `scripts/verify-backend-build.js`
```javascript
const fs = require('fs');
const path = require('path');

const platform = process.platform;
const exeName = platform === 'win32' ? 'peft_engine.exe' : 'peft_engine';
const exePath = path.join(__dirname, '../backend/dist', exeName);

if (!fs.existsSync(exePath)) {
  console.error(`❌ Backend executable not found: ${exePath}`);
  process.exit(1);
}

const stats = fs.statSync(exePath);
if (stats.size < 1024 * 1024) { // Less than 1MB is suspicious
  console.error(`❌ Backend executable is suspiciously small: ${stats.size} bytes`);
  process.exit(1);
}

console.log(`✅ Backend executable verified: ${exePath} (${(stats.size / 1024 / 1024).toFixed(2)} MB)`);
```

### 4. Electron-Builder Configuration

**Purpose:** Package the application with the bundled backend.

**Location:** `package.json` (build section, to be enhanced)

**Enhanced Configuration:**
```json
{
  "build": {
    "extraResources": [
      {
        "from": "backend/dist/peft_engine${/*}",
        "to": "backend",
        "filter": ["peft_engine*"]
      }
    ],
    "files": [
      "dist/**/*",
      "electron/**/*",
      "package.json",
      "!backend/**/*"
    ],
    "win": {
      "target": ["nsis", "portable"],
      "requestedExecutionLevel": "asInvoker"
    }
  }
}
```

### 5. Dependency Detection Module

**Purpose:** Ensure all Python dependencies are correctly identified and bundled.

**Location:** `backend/build_hooks.py` (new file)

**Implementation:**
```python
import ast
import os
from pathlib import Path

def find_all_imports(directory):
    """Recursively find all import statements in Python files."""
    imports = set()
    
    for py_file in Path(directory).rglob('*.py'):
        with open(py_file, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read())
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module.split('.')[0])
            except SyntaxError:
                print(f"Warning: Could not parse {py_file}")
    
    return sorted(imports)

def generate_hidden_imports():
    """Generate list of hidden imports for PyInstaller."""
    backend_dir = Path(__file__).parent
    imports = find_all_imports(backend_dir)
    
    # Filter out standard library modules
    stdlib_modules = {'os', 'sys', 'json', 'logging', 'asyncio', 'typing', 'datetime'}
    hidden_imports = [imp for imp in imports if imp not in stdlib_modules]
    
    return hidden_imports
```

## Data Models

### BackendExecutableInfo

```typescript
interface BackendExecutableInfo {
  path: string;              // Full path to executable
  platform: 'win32' | 'darwin' | 'linux';
  version: string;           // Backend version
  size: number;              // File size in bytes
  checksum: string;          // SHA256 checksum
  createdAt: Date;           // Build timestamp
}
```

### BuildConfiguration

```typescript
interface BuildConfiguration {
  mode: 'development' | 'production';
  platform: 'win32' | 'darwin' | 'linux';
  arch: 'x64' | 'arm64';
  backendPath: string;
  frontendPath: string;
  outputPath: string;
  signCode: boolean;
  includeDevTools: boolean;
}
```

### ProcessInfo

```typescript
interface ProcessInfo {
  pid: number;
  command: string;
  args: string[];
  cwd: string;
  env: Record<string, string>;
  startTime: Date;
  status: 'starting' | 'running' | 'stopping' | 'stopped' | 'crashed';
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Dependency Inclusion Completeness

*For any* Python module imported in the backend code (including lazy-loaded modules), when PyInstaller bundles the application, the bundled executable should include that module and allow it to be imported successfully at runtime.

**Validates: Requirements 1.2, 1.5, 7.1, 7.3**

### Property 2: Path Resolution Consistency

*For any* execution mode (development or production), when the BackendServiceManager resolves the backend path, the resolved path should point to an existing and executable file appropriate for that mode.

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 3: Process Cleanup Guarantee

*For any* application shutdown scenario (normal quit, crash, or forced termination), when the Electron application exits, no Python backend processes should remain running as zombie processes.

**Validates: Requirements 4.2, 4.3, 4.4**

### Property 4: Build Order Enforcement

*For any* build execution, when the build pipeline runs, the backend compilation should complete successfully before the frontend compilation begins, and both should complete before electron-builder is invoked.

**Validates: Requirements 6.1, 6.4**

### Property 5: Platform-Specific Naming Consistency

*For any* target platform, when the build process generates the backend executable, the executable name should follow the pattern "peft_engine" with the platform-appropriate extension (.exe for Windows, no extension for Unix-like systems).

**Validates: Requirements 2.4, 2.5**

### Property 6: Resource Path Accessibility

*For any* packaged application, when the application is installed and launched, the backend executable should be accessible via process.resourcesPath and should be executable with appropriate permissions.

**Validates: Requirements 5.1, 5.3**

### Property 7: Data File Bundling Completeness

*For any* data file or configuration file required by the backend at runtime, when PyInstaller bundles the application, the bundled executable should include that file and be able to access it at runtime.

**Validates: Requirements 1.4**

### Property 8: Critical Dependency Verification

*For any* build execution, when the backend executable is created, the build process should verify that critical dependencies (torch, transformers, peft, fastapi, uvicorn) are included in the bundle.

**Validates: Requirements 7.4**

### Property 9: Update Package Integrity

*For any* application update, when the auto-updater downloads and installs an update, the new backend executable should be included in the update package and should replace the old executable completely.

**Validates: Requirements 12.1, 12.3**

### Property 10: Error Message Specificity

*For any* backend startup failure, when the bundled executable fails to start, the error message displayed to the user should include specific information about the failure cause (missing executable, missing dependency, port conflict, etc.).

**Validates: Requirements 8.1, 8.2, 8.4**

## Error Handling

### Build-Time Errors

1. **PyInstaller Not Found**
   - Detection: Check if `pyinstaller` command is available
   - Response: Display installation instructions with platform-specific commands
   - Recovery: Halt build process with exit code 1

2. **Python Version Mismatch**
   - Detection: Check Python version before building
   - Response: Display error message requiring Python 3.10+
   - Recovery: Halt build process with exit code 1

3. **Missing Dependencies**
   - Detection: PyInstaller analysis phase fails
   - Response: Display list of missing packages from requirements.txt
   - Recovery: Suggest running `pip install -r requirements.txt`

4. **Build Verification Failure**
   - Detection: Executable not found or suspiciously small after build
   - Response: Display detailed error with expected vs actual file size
   - Recovery: Halt build process, suggest checking PyInstaller logs

5. **Code Signing Failure**
   - Detection: Signing script returns non-zero exit code
   - Response: Log warning but continue build (allow unsigned for development)
   - Recovery: Create unsigned build with warning message

### Runtime Errors

1. **Executable Not Found**
   - Detection: Backend path does not exist when starting
   - Response: Display error: "Installation may be corrupted. Please reinstall the application."
   - Recovery: Offer reinstall button, log detailed path information

2. **Executable Not Executable**
   - Detection: File exists but lacks execute permissions (Unix)
   - Response: Attempt to chmod +x, if fails display permission error
   - Recovery: Provide manual chmod instructions

3. **Missing Bundled Dependency**
   - Detection: ImportError in backend process stderr
   - Response: Parse error to extract module name, display: "Missing dependency: {module}"
   - Recovery: Log full error, suggest reporting bug with logs

4. **Port Already in Use**
   - Detection: Backend stderr contains "Address already in use"
   - Response: Attempt alternative ports 8001-8010 (existing logic)
   - Recovery: If all ports fail, display error with port range

5. **Backend Crash During Startup**
   - Detection: Process exits with non-zero code before "ready" signal
   - Response: Capture and display stderr output
   - Recovery: Attempt restart up to 3 times (existing logic)

### Error Logging Strategy

All errors should be logged to electron-log with the following structure:

```javascript
log.error('Backend Error', {
  type: 'startup_failure',
  mode: app.isPackaged ? 'production' : 'development',
  backendPath: resolvedPath,
  error: errorMessage,
  stderr: stderrOutput,
  timestamp: new Date().toISOString(),
  platform: process.platform,
  arch: process.arch
});
```

## Testing Strategy

### Unit Testing

Unit tests will verify specific components and edge cases:

1. **Path Resolution Tests**
   - Test development mode path resolution
   - Test production mode path resolution
   - Test path resolution on different platforms

2. **Build Script Tests**
   - Test build order enforcement
   - Test build verification logic
   - Test error handling for missing executables

3. **Process Management Tests**
   - Test SIGTERM sending on shutdown
   - Test SIGKILL after timeout
   - Test process cleanup verification

### Property-Based Testing

Property-based tests will verify universal properties across many inputs using the `fast-check` library for JavaScript/TypeScript tests and `hypothesis` for Python tests.

**Configuration:**
- Minimum iterations: 100 per property test
- Random seed: Configurable for reproducibility
- Shrinking: Enabled to find minimal failing cases

**Test Tagging:**
Each property-based test must include a comment with this exact format:
```javascript
// Feature: python-backend-bundling, Property {number}: {property_text}
```

**Property Test Examples:**

```javascript
// Feature: python-backend-bundling, Property 2: Path Resolution Consistency
test('path resolution returns valid executable path', () => {
  fc.assert(
    fc.property(
      fc.boolean(), // isPackaged
      fc.constantFrom('win32', 'darwin', 'linux'), // platform
      (isPackaged, platform) => {
        const path = resolveBackendPath(isPackaged, platform);
        expect(fs.existsSync(path)).toBe(true);
        expect(isExecutable(path)).toBe(true);
      }
    ),
    { numRuns: 100 }
  );
});
```

```python
# Feature: python-backend-bundling, Property 1: Dependency Inclusion Completeness
@given(st.sampled_from(get_all_backend_imports()))
def test_all_imports_bundled(module_name):
    """Test that all imported modules are included in the bundle."""
    # This would run against the bundled executable
    result = subprocess.run(
        [BUNDLED_EXECUTABLE_PATH, '-c', f'import {module_name}'],
        capture_output=True
    )
    assert result.returncode == 0, f"Failed to import {module_name}"
```

### Integration Testing

Integration tests will verify end-to-end workflows:

1. **Full Build Pipeline Test**
   - Run complete build process
   - Verify all artifacts are created
   - Verify executable runs and responds to health check

2. **Development to Production Transition Test**
   - Start app in development mode
   - Verify Python script is used
   - Build production package
   - Verify bundled executable is used

3. **Update Installation Test**
   - Install version N
   - Create update package for version N+1
   - Apply update
   - Verify new backend executable is used

### End-to-End Testing

E2E tests will verify user-facing scenarios:

1. **Fresh Installation Test**
   - Install application on clean system (no Python installed)
   - Launch application
   - Verify backend starts successfully
   - Verify frontend can communicate with backend

2. **Crash Recovery Test**
   - Launch application
   - Force-kill backend process
   - Verify automatic restart
   - Verify application remains functional

3. **Clean Uninstall Test**
   - Install application
   - Launch and use application
   - Close application
   - Verify no Python processes remain
   - Uninstall application
   - Verify all files are removed

### Platform-Specific Testing

Each platform requires specific testing:

**Windows:**
- Verify .exe extension
- Verify no console window appears
- Verify NSIS installer works
- Verify code signing (if configured)

**macOS:**
- Verify universal binary (x64 + arm64)
- Verify DMG installer works
- Verify notarization (if configured)
- Verify Gatekeeper doesn't block

**Linux:**
- Verify AppImage works
- Verify .deb package works
- Verify executable permissions
- Verify no GUI dependencies required

## Implementation Notes

### PyInstaller Considerations

1. **Hidden Imports:** The backend uses lazy loading extensively. All lazy-loaded modules must be explicitly listed in `hiddenimports` in the spec file.

2. **Data Files:** Configuration files and any JSON/YAML files used by the backend must be included via the `datas` parameter.

3. **Binary Dependencies:** PyTorch and other ML libraries include native binaries. PyInstaller should detect these automatically, but verify in testing.

4. **Size Optimization:** The bundled executable will be large (500MB-2GB) due to ML libraries. Consider:
   - Using `--onefile` for simplicity despite larger size
   - Excluding unnecessary torch backends (e.g., if only CUDA is needed)
   - Compressing the installer

### Electron-Builder Considerations

1. **Resource Path:** Use `process.resourcesPath` in production, not `__dirname`, as the directory structure changes after packaging.

2. **Extra Resources:** The `extraResources` configuration copies files outside the asar archive, making them accessible as regular files.

3. **Platform-Specific Paths:** Use `path.join()` and avoid hardcoded separators to ensure cross-platform compatibility.

4. **Signing:** Ensure the backend executable is signed along with the Electron app to avoid security warnings.

### Performance Considerations

1. **Startup Time:** The bundled executable may start slightly slower than a Python script due to unpacking. Maintain lazy loading to minimize impact.

2. **Memory Usage:** The bundled executable includes the Python interpreter and all libraries, increasing base memory usage by ~200-500MB.

3. **Disk Space:** The installer will be significantly larger (1-3GB) compared to the current version. Document this in system requirements.

### Security Considerations

1. **Code Signing:** Always sign the backend executable and the installer to avoid security warnings and antivirus false positives.

2. **Integrity Verification:** Include checksums for the backend executable in the update manifest to verify integrity during updates.

3. **Permissions:** The backend executable should run with user-level permissions, not requiring administrator access.

4. **Antivirus Compatibility:** Test with common antivirus software (Windows Defender, Norton, McAfee) to ensure no false positives.

## Dependencies

### Build Dependencies

- **PyInstaller** (>=5.0): Python package for creating standalone executables
- **Python** (>=3.10): Required for building the backend
- **Node.js** (>=18): Required for building the frontend and running electron-builder
- **electron-builder** (>=25.0): Already installed, used for packaging

### Runtime Dependencies

- **None for end users:** The bundled executable includes all dependencies
- **Electron** (>=39.0): Already included in the application

### Development Dependencies

- **fast-check** (>=3.15.0): Already installed, for property-based testing
- **vitest** (>=4.0.14): Already installed, for running tests
- **hypothesis** (>=6.92.1): Already installed in backend, for Python property-based testing

## Deployment Considerations

### Build Environment Setup

Developers need to install PyInstaller before building:

```bash
# Install PyInstaller
pip install pyinstaller

# Verify installation
pyinstaller --version
```

### CI/CD Integration

The existing GitHub Actions workflows need to be updated:

```yaml
# .github/workflows/build.yml
- name: Install Python dependencies
  run: |
    python -m pip install --upgrade pip
    pip install pyinstaller
    pip install -r backend/requirements.txt

- name: Build backend
  run: npm run build:backend

- name: Verify backend build
  run: npm run build:backend:verify

- name: Build application
  run: npm run build:win  # or build:mac, build:linux
```

### Release Process

1. Update version in package.json
2. Run `npm run build:all` to build backend and frontend
3. Run platform-specific build: `npm run build:win`, `build:mac`, or `build:linux`
4. Test the installer on a clean system
5. Sign the installer (if configured)
6. Upload to GitHub releases
7. Auto-updater will distribute to users

### Rollback Strategy

If a bundled backend has issues:

1. The auto-updater includes integrity checks that will prevent installation of corrupted updates
2. Users can manually download and install a previous version from GitHub releases
3. The development team can push a hotfix update that reverts to a known-good backend version

## Future Enhancements

1. **Incremental Updates:** Instead of downloading the entire backend executable with each update, implement delta updates for the backend.

2. **Multiple Backend Versions:** Support running different backend versions side-by-side for A/B testing or gradual rollouts.

3. **Backend Plugins:** Allow the backend to load plugins dynamically without requiring a full rebuild.

4. **Size Optimization:** Investigate splitting the backend into core + optional modules to reduce initial download size.

5. **Cloud Backend Option:** Provide an option to connect to a cloud-hosted backend instead of the local bundled version for users with limited disk space.
