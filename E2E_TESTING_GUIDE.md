# End-to-End Testing Guide

## Overview

This document describes the comprehensive end-to-end (E2E) testing suite for PEFT Studio. The E2E tests validate the complete workflow across all platforms, test performance on various hardware configurations, verify security measures, and ensure offline mode functionality.

## Test Categories

### 1. Complete Workflow Tests (`test_e2e_complete_workflow.py`)

Tests the complete workflow from model selection to deployment:

- **Platform Connection**: Verify connection to all supported platforms
- **Model Browsing**: Test model discovery across registries
- **Training Configuration**: Validate configuration completeness
- **Job Submission**: Test job orchestration
- **Artifact Management**: Verify artifact download and storage
- **Deployment**: Test deployment to inference platforms
- **Offline Mode**: Validate offline queue and sync

**Run:**
```bash
pytest backend/tests/test_e2e_complete_workflow.py -v
```

### 2. Platform Integration Tests (`test_e2e_platform_integration.py`)

Tests integration with each supported platform:

- **Compute Providers**: RunPod, Lambda Labs, Vast.ai
- **Model Registries**: HuggingFace, Civitai, Ollama
- **Experiment Trackers**: W&B, Comet ML, Arize Phoenix
- **Deployment Platforms**: Predibase, Together AI, Modal, Replicate
- **Evaluation Platforms**: DeepEval, HoneyHive

**Run:**
```bash
pytest backend/tests/test_e2e_platform_integration.py -v
```

### 3. Performance Validation Tests (`test_e2e_performance_validation.py`)

Tests performance characteristics:

- **Startup Performance**: Cold start < 3s, warm start < 1s
- **Memory Usage**: Idle < 500MB, under load < 700MB
- **CPU Usage**: Idle < 1%, efficient under load
- **Disk I/O**: Read/write throughput validation
- **Network Performance**: API response time, WebSocket latency
- **Low-End Hardware**: Simulation of limited resources
- **Scalability**: Concurrent operations, large datasets

**Run:**
```bash
pytest backend/tests/test_e2e_performance_validation.py -v
```

### 4. Security Audit Tests (`test_e2e_security_audit.py`)

Comprehensive security testing:

- **Credential Security**: Encryption, OS keystore integration
- **Data Encryption**: AES-256 encryption validation
- **Input Validation**: SQL injection, XSS, path traversal prevention
- **Secure Communications**: HTTPS enforcement, certificate validation
- **Authentication**: Token-based auth, expiration
- **Rate Limiting**: Per-user limits, proper responses
- **Security Headers**: CSRF, CORS, security headers
- **Audit Logging**: Security event logging
- **Data Privacy**: Telemetry opt-in, PII removal
- **File Handling**: Upload validation, size limits

**Run:**
```bash
pytest backend/tests/test_e2e_security_audit.py -v
```

## Running E2E Tests

### Quick Start

Run all E2E tests with mock data:

```bash
python backend/tests/run_e2e_tests.py
```

### With Real API Credentials

Set environment variables for real API testing:

```bash
export RUNPOD_API_KEY="your_key"
export LAMBDA_API_KEY="your_key"
export VASTAI_API_KEY="your_key"
export HUGGINGFACE_TOKEN="your_token"
export WANDB_API_KEY="your_key"

python backend/tests/run_e2e_tests.py --with-real-api
```

### Quick Tests Only

Run only quick tests (skip performance tests):

```bash
python backend/tests/run_e2e_tests.py --quick
```

### Security Tests Only

Run only security audit tests:

```bash
python backend/tests/run_e2e_tests.py --security-only
```

### Verbose Output

Show detailed test output:

```bash
python backend/tests/run_e2e_tests.py --verbose
```

## Test Requirements

### Environment Setup

1. **Python 3.8+** with all dependencies installed:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **pytest** and testing dependencies:
   ```bash
   pip install pytest pytest-asyncio hypothesis
   ```

3. **System resources**:
   - Minimum 2GB RAM
   - 1GB free disk space
   - Internet connection (for real API tests)

### Optional: Real API Credentials

For comprehensive testing with real platforms, set these environment variables:

- `RUNPOD_API_KEY`: RunPod API key
- `LAMBDA_API_KEY`: Lambda Labs API key
- `VASTAI_API_KEY`: Vast.ai API key
- `HUGGINGFACE_TOKEN`: HuggingFace access token
- `WANDB_API_KEY`: Weights & Biases API key
- `COMETML_API_KEY`: Comet ML API key
- `PREDIBASE_API_KEY`: Predibase API key
- `TOGETHERAI_API_KEY`: Together AI API key

**Note**: Tests will run with mock data if credentials are not provided.

## Test Coverage

### Requirements Coverage

The E2E tests validate all requirements:

- ✅ **Requirement 1**: Platform connections (1.1-1.5)
- ✅ **Requirement 2**: Model browsing (2.1-2.5)
- ✅ **Requirement 3**: Compute provider selection (3.1-3.5)
- ✅ **Requirement 4**: Training configuration (4.1-4.5)
- ✅ **Requirement 5**: Training execution (5.1-5.5)
- ✅ **Requirement 6**: Experiment tracking (6.1-6.5)
- ✅ **Requirement 7**: Model evaluation (7.1-7.5)
- ✅ **Requirement 8**: Adapter registry (8.1-8.5)
- ✅ **Requirement 9**: Deployment (9.1-9.5)
- ✅ **Requirement 10**: Local inference (10.1-10.5)
- ✅ **Requirement 11**: Gradio demos (11.1-11.5)
- ✅ **Requirement 12**: Offline mode (12.1-12.5)
- ✅ **Requirement 13**: Connector system (13.1-13.5)
- ✅ **Requirement 14**: Performance (14.1-14.5)
- ✅ **Requirement 15**: Security (15.1-15.5)
- ✅ **Requirement 16**: Multi-run management (16.1-16.5)
- ✅ **Requirement 17**: Run comparison (17.1-17.5)
- ✅ **Requirement 18**: Configuration management (18.1-18.5)
- ✅ **Requirement 19**: Logging (19.1-19.5)
- ✅ **Requirement 20**: Dashboard (20.1-20.5)

### Platform Coverage

Tests cover all supported platforms:

**Compute Providers:**
- RunPod
- Lambda Labs
- Vast.ai
- Local GPU

**Model Registries:**
- HuggingFace Hub
- Civitai
- Ollama

**Experiment Trackers:**
- Weights & Biases
- Comet ML
- Arize Phoenix

**Deployment Platforms:**
- Predibase
- Together AI
- Modal
- Replicate

**Evaluation Platforms:**
- DeepEval
- HoneyHive

## Performance Benchmarks

### Target Metrics

| Metric | Target | Test |
|--------|--------|------|
| Cold Start Time | < 3s | ✅ |
| Warm Start Time | < 1s | ✅ |
| Idle Memory | < 500MB | ✅ |
| Idle CPU | < 1% | ✅ |
| Bundle Size | < 200MB | ✅ |
| API Response | < 100ms | ✅ |
| WebSocket Latency | < 50ms | ✅ |

### Low-End Hardware Simulation

Tests validate performance on:
- Single-core CPU
- 2GB RAM
- Slow HDD (< 50MB/s)
- Limited network bandwidth

## Security Validation

### Security Checklist

- ✅ Credentials encrypted at rest (AES-256)
- ✅ OS keystore integration (Windows/macOS/Linux)
- ✅ No plaintext credentials in storage
- ✅ No credentials in logs
- ✅ HTTPS enforcement for external APIs
- ✅ SSL certificate validation
- ✅ SQL injection prevention
- ✅ XSS prevention
- ✅ Path traversal prevention
- ✅ Command injection prevention
- ✅ CSRF protection
- ✅ Rate limiting (per-user)
- ✅ Security headers (X-Frame-Options, etc.)
- ✅ Audit logging for security events
- ✅ Telemetry opt-in only
- ✅ PII anonymization
- ✅ File upload validation
- ✅ File size limits

## Offline Mode Validation

### Offline Functionality Tests

- ✅ Network status detection
- ✅ Offline queue persistence
- ✅ Operation queueing while offline
- ✅ Sync on reconnection
- ✅ Conflict resolution
- ✅ Cached model metadata
- ✅ Local training capability
- ✅ Local inference capability

## Continuous Integration

### CI/CD Integration

Add to your CI/CD pipeline:

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r backend/requirements.txt
      - name: Run E2E tests
        run: python backend/tests/run_e2e_tests.py --quick
      - name: Run security tests
        run: python backend/tests/run_e2e_tests.py --security-only
```

### Nightly Tests with Real APIs

```yaml
# .github/workflows/nightly-e2e.yml
name: Nightly E2E Tests

on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily

jobs:
  e2e-real-api:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - name: Install dependencies
        run: pip install -r backend/requirements.txt
      - name: Run E2E tests with real APIs
        env:
          RUNPOD_API_KEY: ${{ secrets.RUNPOD_API_KEY }}
          HUGGINGFACE_TOKEN: ${{ secrets.HUGGINGFACE_TOKEN }}
        run: python backend/tests/run_e2e_tests.py --with-real-api
```

## Troubleshooting

### Common Issues

**1. Tests fail with "Module not found"**
```bash
# Install all dependencies
pip install -r backend/requirements.txt
```

**2. Performance tests fail on slow hardware**
```bash
# Run quick tests only
python backend/tests/run_e2e_tests.py --quick
```

**3. Real API tests fail**
```bash
# Check environment variables
echo $RUNPOD_API_KEY
echo $HUGGINGFACE_TOKEN

# Verify credentials are valid
# Tests will automatically fall back to mock data if credentials are invalid
```

**4. Security tests fail**
```bash
# Ensure OS keystore is available
# Windows: Credential Manager
# macOS: Keychain
# Linux: Secret Service (gnome-keyring or kwallet)
```

### Debug Mode

Run tests with maximum verbosity:

```bash
pytest backend/tests/test_e2e_complete_workflow.py -vv -s --tb=long
```

## Best Practices

### Before Committing

Run quick E2E tests:
```bash
python backend/tests/run_e2e_tests.py --quick
```

### Before Releasing

Run full E2E test suite:
```bash
python backend/tests/run_e2e_tests.py --verbose
```

### Security Audit

Run security tests before any release:
```bash
python backend/tests/run_e2e_tests.py --security-only --verbose
```

### Performance Regression

Monitor performance metrics:
```bash
pytest backend/tests/test_e2e_performance_validation.py -v
```

## Reporting Issues

When reporting E2E test failures, include:

1. **Test output**: Full verbose output
2. **Environment**: OS, Python version, hardware specs
3. **Configuration**: Mock vs real API, credentials used
4. **Logs**: Application logs from test run
5. **Steps to reproduce**: Exact commands used

## Contributing

### Adding New E2E Tests

1. Create test file in `backend/tests/`
2. Follow naming convention: `test_e2e_*.py`
3. Use pytest fixtures from `conftest.py`
4. Add to test runner in `run_e2e_tests.py`
5. Update this documentation

### Test Structure

```python
class TestNewFeature:
    """Test new feature E2E"""
    
    def test_feature_workflow(self):
        """Test complete workflow for new feature"""
        # Setup
        # Execute
        # Verify
        # Cleanup
        pass
```

## Summary

The E2E test suite provides comprehensive validation of:

- ✅ Complete workflows across all platforms
- ✅ Real API integration (optional)
- ✅ Performance on low-end hardware
- ✅ Security measures and best practices
- ✅ Offline mode functionality
- ✅ Cross-platform compatibility
- ✅ Error handling and recovery
- ✅ Scalability and concurrency

Run regularly to ensure system reliability and correctness!
