# Testing Bundled Backend Guide

This guide explains how to test the bundled Python backend executable locally before creating installers or deploying to production.

## Table of Contents

- [Overview](#overview)
- [Testing Workflow](#testing-workflow)
- [Unit Testing](#unit-testing)
- [Integration Testing](#integration-testing)
- [Manual Testing](#manual-testing)
- [Performance Testing](#performance-testing)
- [Platform-Specific Testing](#platform-specific-testing)
- [Automated Testing](#automated-testing)

## Overview

Testing the bundled backend is crucial to ensure:

- All dependencies are correctly bundled
- Data files are accessible
- API endpoints work correctly
- Performance is acceptable
- Process lifecycle management works
- Platform-specific features function properly

### Testing Levels

1. **Unit Tests**: Test individual components and functions
2. **Integration Tests**: Test backend integration with Electron
3. **Manual Tests**: Interactive testing of the executable
4. **Performance Tests**: Verify startup time and resource usage
5. **End-to-End Tests**: Test complete user workflows

## Testing Workflow

### Step 1: Build the Backend

```bash
# Build the backend executable
npm run build:backend

# Verify the build
npm run build:backend:verify
```

Expected output:
```
✅ Backend executable verified: backend/dist/peft_engine.exe (1.2 GB)
✅ File size is reasonable
✅ Executable exists
```

### Step 2: Run Unit Tests

```bash
# Run Python unit tests
cd backend
pytest tests/

# Run specific test file
pytest tests/test_data_file_bundling.py
pytest tests/test_runtime_path_integration.py
```

### Step 3: Test Executable Independently

```bash
# Navigate to dist directory
cd backend/dist

# Run the executable
./peft_engine  # Unix
peft_engine.exe  # Windows
```

The backend should start and display:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 4: Test API Endpoints

In another terminal:

```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Expected response
{
  "status": "healthy",
  "version": "1.0.0"
}

# Test other endpoints
curl http://localhost:8000/api/hardware/info
curl http://localhost:8000/api/datasets
```

### Step 5: Run Integration Tests

```bash
# Run integration tests
npm run test:integration

# Run specific integration test
npm run test:integration -- backend-lifecycle-verification
```

### Step 6: Test with Electron

```bash
# Build complete application
npm run build:all

# Run packaged app (without installer)
# Windows
.\release\win-unpacked\PEFT Studio.exe

# macOS
open release/mac/PEFT\ Studio.app

# Linux
./release/linux-unpacked/peft-studio
```

## Unit Testing

### Python Unit Tests

Located in `backend/tests/`, these tests verify backend functionality:

```bash
# Run all tests
cd backend
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test
pytest tests/test_data_file_bundling.py -v

# Run tests matching pattern
pytest -k "bundling"
```

### Key Test Files

**`test_data_file_bundling.py`**
- Tests that data files are bundled correctly
- Verifies runtime path resolution
- Checks file accessibility

**`test_runtime_path_integration.py`**
- Tests `runtime_paths.py` module
- Verifies path resolution in bundled mode
- Tests fallback to development mode

**`test_pyinstaller_dependency_inclusion.py`**
- Verifies all dependencies are included
- Tests import of lazy-loaded modules
- Checks for missing packages

### Writing New Unit Tests

```python
# backend/tests/test_my_feature.py
import pytest
from runtime_paths import get_resource_path

def test_resource_path_resolution():
    """Test that resource paths resolve correctly."""
    config_path = get_resource_path('config.py')
    assert config_path.endswith('config.py')
    assert os.path.exists(config_path)

def test_bundled_module_import():
    """Test that bundled modules can be imported."""
    try:
        import torch
        import transformers
        import peft
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import module: {e}")
```

## Integration Testing

### JavaScript Integration Tests

Located in `src/test/integration/`, these tests verify Electron integration:

```bash
# Run all integration tests
npm run test:integration

# Run specific test file
npm run test:integration -- backend-lifecycle-verification

# Run with watch mode
npm run test:integration -- --watch
```

### Key Test Files

**`backend-lifecycle-verification.test.ts`**
- Tests backend startup and shutdown
- Verifies process management
- Tests crash recovery

**`backend-performance-verification.test.ts`**
- Tests startup time
- Verifies memory usage
- Checks API response times

**`platform-windows.test.ts`** / **`platform-macos.test.ts`** / **`platform-linux.test.ts`**
- Platform-specific tests
- Verify executable naming
- Test platform-specific features

### Writing Integration Tests

```typescript
// src/test/integration/my-feature.test.ts
import { describe, it, expect } from 'vitest';
import { spawn } from 'child_process';
import path from 'path';

describe('My Feature Integration', () => {
  it('should start backend successfully', async () => {
    const backendPath = path.join(__dirname, '../../backend/dist/peft_engine');
    const backend = spawn(backendPath);
    
    // Wait for startup
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // Test health endpoint
    const response = await fetch('http://localhost:8000/api/health');
    expect(response.ok).toBe(true);
    
    // Cleanup
    backend.kill();
  });
});
```

## Manual Testing

### Test Checklist

Use this checklist for manual testing:

#### Basic Functionality
- [ ] Backend executable exists at `backend/dist/peft_engine[.exe]`
- [ ] Executable runs without errors
- [ ] Health endpoint responds: `curl http://localhost:8000/api/health`
- [ ] No console window appears (Windows)
- [ ] Process terminates cleanly with Ctrl+C

#### API Endpoints
- [ ] `/api/health` returns healthy status
- [ ] `/api/hardware/info` returns hardware information
- [ ] `/api/datasets` returns dataset list
- [ ] `/api/models` returns model list
- [ ] All endpoints respond within acceptable time

#### Data Files
- [ ] Configuration files are accessible
- [ ] Database file is created/accessible
- [ ] Service modules load correctly
- [ ] Connector plugins load correctly

#### Process Management
- [ ] Backend starts automatically with Electron
- [ ] Backend stops cleanly when Electron quits
- [ ] No zombie processes remain after quit
- [ ] Crash recovery works (kill backend, should restart)
- [ ] Port conflict handling works (start on port 8001 if 8000 busy)

#### Performance
- [ ] Startup time < 5 seconds
- [ ] Memory usage < 2GB
- [ ] API responses < 1 second
- [ ] No memory leaks over time

### Manual Test Procedures

#### Test 1: Standalone Execution

```bash
# Start backend
cd backend/dist
./peft_engine

# In another terminal, test endpoints
curl http://localhost:8000/api/health
curl http://localhost:8000/api/hardware/info

# Stop backend
# Press Ctrl+C in backend terminal

# Verify clean shutdown
ps aux | grep peft_engine  # Should show no processes
```

#### Test 2: Electron Integration

```bash
# Build and run
npm run build:all
./release/win-unpacked/PEFT\ Studio.exe  # Adjust for platform

# In the app:
# 1. Check that backend status shows "Connected"
# 2. Try loading a dataset
# 3. Try loading a model
# 4. Check logs for errors

# Close app
# Verify no backend processes remain
ps aux | grep peft_engine  # Should show no processes
```

#### Test 3: Crash Recovery

```bash
# Start app
./release/win-unpacked/PEFT\ Studio.exe

# Find backend process
ps aux | grep peft_engine

# Kill backend process
kill -9 <pid>

# App should show "Backend disconnected"
# Wait 5 seconds
# App should show "Backend connected" (auto-restart)
```

#### Test 4: Port Conflict

```bash
# Start a server on port 8000
python -m http.server 8000

# Start app
./release/win-unpacked/PEFT\ Studio.exe

# Backend should start on port 8001
# Check logs to verify
```

## Performance Testing

### Startup Time Test

```bash
# Test startup time
time ./backend/dist/peft_engine &
sleep 5
curl http://localhost:8000/api/health
kill %1

# Should complete in < 5 seconds
```

### Memory Usage Test

```bash
# Start backend
./backend/dist/peft_engine &
PID=$!

# Monitor memory usage
while true; do
  ps -p $PID -o rss=
  sleep 1
done

# Should be < 2GB (2097152 KB)
```

### API Response Time Test

```bash
# Test endpoint response time
time curl http://localhost:8000/api/health
time curl http://localhost:8000/api/hardware/info

# Should respond in < 1 second
```

### Load Test

```bash
# Install Apache Bench
sudo apt-get install apache2-utils  # Linux
brew install httpd  # macOS

# Run load test
ab -n 1000 -c 10 http://localhost:8000/api/health

# Check results:
# - Requests per second should be > 100
# - No failed requests
# - Mean response time < 100ms
```

## Platform-Specific Testing

### Windows Testing

```powershell
# Build for Windows
npm run build:backend:win

# Test executable
cd backend\dist
.\peft_engine.exe

# Verify no console window
# Should not show black console window

# Test with Task Manager
# 1. Start backend
# 2. Open Task Manager
# 3. Find peft_engine.exe
# 4. Check memory usage
# 5. Kill process
# 6. Verify it terminates

# Test with antivirus
# 1. Enable Windows Defender
# 2. Run executable
# 3. Should not be blocked
# 4. If blocked, add to exclusions
```

### macOS Testing

```bash
# Build for macOS
npm run build:backend:mac

# Test executable
cd backend/dist
./peft_engine

# Verify permissions
ls -l peft_engine
# Should show: -rwxr-xr-x

# Test with Activity Monitor
# 1. Start backend
# 2. Open Activity Monitor
# 3. Find peft_engine
# 4. Check CPU and memory
# 5. Quit process
# 6. Verify it terminates

# Test Gatekeeper
# 1. Download executable from another machine
# 2. Try to run
# 3. Should not be blocked (if signed)
# 4. If blocked, right-click → Open
```

### Linux Testing

```bash
# Build for Linux
npm run build:backend:linux

# Test executable
cd backend/dist
./peft_engine

# Verify permissions
ls -l peft_engine
# Should show: -rwxr-xr-x

# Test with different distributions
# - Ubuntu 20.04
# - Ubuntu 22.04
# - Fedora 38
# - Debian 11

# Test with system monitor
# 1. Start backend
# 2. Open System Monitor
# 3. Find peft_engine
# 4. Check resources
# 5. Kill process
# 6. Verify it terminates
```

## Automated Testing

### CI/CD Testing

The CI/CD pipeline automatically tests the bundled backend:

```yaml
# .github/workflows/build.yml
- name: Build backend
  run: npm run build:backend

- name: Verify backend build
  run: npm run build:backend:verify

- name: Test backend
  run: |
    cd backend
    pytest tests/

- name: Integration tests
  run: npm run test:integration
```

### Property-Based Testing

Run property-based tests to verify correctness properties:

```bash
# Run PBT tests
npm run test:pbt

# Run specific PBT test
npm run test:pbt -- backend-path-resolution
npm run test:pbt -- backend-process-cleanup
npm run test:pbt -- resource-path-accessibility
```

### Continuous Testing

Set up continuous testing during development:

```bash
# Watch mode for Python tests
cd backend
pytest --watch

# Watch mode for integration tests
npm run test:integration -- --watch

# Watch mode for all tests
npm run test -- --watch
```

## Test Reports

### Generate Test Reports

```bash
# Python test coverage
cd backend
pytest --cov=. --cov-report=html
open htmlcov/index.html

# JavaScript test coverage
npm run test:coverage
open coverage/index.html

# Integration test report
npm run test:integration -- --reporter=html
```

### Interpreting Results

**Good Results:**
- All tests pass
- Coverage > 80%
- No memory leaks
- Startup time < 5 seconds
- No zombie processes

**Warning Signs:**
- Failing tests
- Low coverage (< 60%)
- Memory usage > 2GB
- Startup time > 10 seconds
- Zombie processes remain

## Troubleshooting Test Failures

### Test Fails: Module Not Found

**Solution:** Add to `hiddenimports` in `backend/peft_engine.spec`

### Test Fails: File Not Found

**Solution:** Add to `datas` in `backend/peft_engine.spec`

### Test Fails: Timeout

**Solution:** Increase timeout or optimize startup

### Test Fails: Port in Use

**Solution:** Kill processes using port 8000-8010

### Test Fails: Permission Denied

**Solution:** `chmod +x backend/dist/peft_engine`

## Best Practices

1. **Test Early and Often**: Test after every significant change
2. **Test All Platforms**: Don't assume cross-platform compatibility
3. **Automate Tests**: Use CI/CD for consistent testing
4. **Monitor Performance**: Track startup time and memory usage
5. **Test Edge Cases**: Port conflicts, crashes, missing files
6. **Document Issues**: Record problems and solutions
7. **Version Control**: Track test results over time

## Related Documentation

- [Backend Bundling Guide](backend-bundling.md) - Main documentation
- [Troubleshooting Guide](backend-bundling-troubleshooting.md) - Common issues
- [Testing Guide](testing.md) - General testing strategies

## Summary

Testing the bundled backend involves:

1. **Build**: Create the executable
2. **Unit Test**: Test individual components
3. **Integration Test**: Test with Electron
4. **Manual Test**: Interactive verification
5. **Performance Test**: Verify speed and resources
6. **Platform Test**: Test on all platforms
7. **Automate**: Use CI/CD for continuous testing

Thorough testing ensures the bundled backend works correctly for all users across all platforms.
