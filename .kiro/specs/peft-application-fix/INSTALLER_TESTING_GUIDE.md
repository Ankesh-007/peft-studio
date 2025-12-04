# Installer Testing Guide for Release 1.0.1

## Overview

This guide provides comprehensive testing procedures for PEFT Studio v1.0.1 installers across all platforms.

## Testing Objectives

Verify that release 1.0.1 fixes the following issues:
1. ✅ Backend service starts correctly (no blank window)
2. ✅ All PEFT algorithms display (LoRA, QLoRA, DoRA, PiSSA, RSLoRA)
3. ✅ Dependency verification works on startup
4. ✅ Error handling provides clear messages
5. ✅ Application recovers gracefully from errors

## Test Environments

### Windows Testing
- **OS**: Windows 10 (version 1909+) or Windows 11
- **Architecture**: x64
- **Prerequisites**: None (Python will be checked by app)
- **Installers to Test**:
  - `PEFT Studio-Setup-1.0.1.exe` (NSIS installer)
  - `PEFT Studio-Portable-1.0.1.exe` (Portable version)

### macOS Testing
- **OS**: macOS 10.13 (High Sierra) or later
- **Architecture**: x64 (Intel) and arm64 (Apple Silicon)
- **Prerequisites**: None
- **Installers to Test**:
  - `PEFT Studio-1.0.1-x64.dmg` (Intel)
  - `PEFT Studio-1.0.1-arm64.dmg` (Apple Silicon)

### Linux Testing
- **OS**: Ubuntu 20.04 LTS or later (or equivalent)
- **Architecture**: x64
- **Prerequisites**: None
- **Installers to Test**:
  - `PEFT Studio-1.0.1-x64.AppImage`
  - `PEFT Studio-1.0.1-x64.deb`

## Pre-Test Setup

### Clean System Requirements

For accurate testing, use a clean system or VM:

1. **No previous PEFT Studio installation**
2. **No Python installed** (to test dependency detection)
3. **Fresh user profile** (no cached settings)

### Optional: Python Installation

To test with Python:
- Python 3.10, 3.11, or 3.12
- No ML packages installed initially

## Test Procedures

### Test 1: Fresh Installation (No Python)

**Purpose**: Verify dependency detection and error messages

**Steps**:
1. Download installer for your platform
2. Verify checksum against `SHA256SUMS.txt`
3. Run installer
4. Launch PEFT Studio
5. **Expected**: Dependency check screen appears
6. **Expected**: Clear message about missing Python
7. **Expected**: Instructions on how to install Python
8. **Expected**: "Retry" button available

**Pass Criteria**:
- ✅ Application starts (no blank window)
- ✅ Dependency status UI displays
- ✅ Python missing error is clear and actionable
- ✅ No crashes or freezes

### Test 2: Installation with Python (No ML Packages)

**Purpose**: Verify ML package dependency detection

**Steps**:
1. Install Python 3.10+ (if not already installed)
2. Launch PEFT Studio
3. **Expected**: Dependency check shows Python ✓
4. **Expected**: Missing packages listed (torch, transformers, peft)
5. **Expected**: Clear installation instructions provided

**Pass Criteria**:
- ✅ Python detected correctly
- ✅ Missing packages identified
- ✅ Installation instructions clear
- ✅ "Retry" button works after installing packages

### Test 3: Full Installation (All Dependencies)

**Purpose**: Verify normal startup flow

**Steps**:
1. Install Python 3.10+
2. Install required packages:
   ```bash
   pip install torch transformers peft
   ```
3. Launch PEFT Studio
4. **Expected**: Splash screen with progress indicators
5. **Expected**: Backend service starts
6. **Expected**: Main application interface loads
7. **Expected**: No errors or blank screens

**Pass Criteria**:
- ✅ Splash screen shows progress
- ✅ Backend starts within 30 seconds
- ✅ Main UI loads completely
- ✅ No console errors

### Test 4: PEFT Algorithm Display

**Purpose**: Verify all PEFT options are visible

**Steps**:
1. Launch PEFT Studio (with all dependencies)
2. Navigate to Training Configuration or Training Wizard
3. Look for PEFT algorithm selection
4. **Expected**: All 5 algorithms visible:
   - LoRA (Low-Rank Adaptation)
   - QLoRA (Quantized LoRA)
   - DoRA (Weight-Decomposed Low-Rank Adaptation)
   - PiSSA (Principal Singular values Adaptation)
   - RSLoRA (Rank-Stabilized LoRA)

**Pass Criteria**:
- ✅ All 5 algorithms listed
- ✅ Each has description
- ✅ Parameters display when selected
- ✅ Tooltips work on hover

### Test 5: Backend Service Reliability

**Purpose**: Verify backend health monitoring and restart

**Steps**:
1. Launch PEFT Studio
2. Wait for backend to start
3. Manually kill Python backend process (Task Manager/Activity Monitor)
4. **Expected**: Application detects backend crash
5. **Expected**: Automatic restart attempt
6. **Expected**: User notification if restart fails

**Pass Criteria**:
- ✅ Backend crash detected within 10 seconds
- ✅ Automatic restart attempted
- ✅ Clear error message if restart fails
- ✅ Manual restart option available

### Test 6: Error Handling

**Purpose**: Verify error messages are clear and actionable

**Steps**:
1. Test various error conditions:
   - Start with port 8000 already in use
   - Start without Python
   - Start with incompatible Python version
2. **Expected**: Each error shows:
   - What went wrong
   - Why it happened
   - How to fix it

**Pass Criteria**:
- ✅ Error messages are plain language
- ✅ Technical details available but not overwhelming
- ✅ Fix instructions are actionable
- ✅ Recovery options provided

### Test 7: Startup Performance

**Purpose**: Verify startup time is acceptable

**Steps**:
1. Launch PEFT Studio (with all dependencies)
2. Measure time from launch to main UI
3. **Expected**: < 30 seconds on modern hardware

**Pass Criteria**:
- ✅ Startup completes in reasonable time
- ✅ Progress indicators show activity
- ✅ No long freezes or hangs

### Test 8: Basic Functionality

**Purpose**: Verify core features work

**Steps**:
1. Browse models (if HuggingFace connection available)
2. Upload a sample dataset
3. Configure training settings
4. View PEFT configuration options
5. Check settings and preferences

**Pass Criteria**:
- ✅ Model browser loads
- ✅ Dataset upload works
- ✅ Training configuration accessible
- ✅ PEFT options functional
- ✅ Settings save correctly

## Platform-Specific Tests

### Windows-Specific

1. **NSIS Installer**:
   - ✅ Installation wizard completes
   - ✅ Desktop shortcut created (if selected)
   - ✅ Start menu entry created
   - ✅ Uninstaller works correctly

2. **Portable Version**:
   - ✅ Runs without installation
   - ✅ Creates portable data directory
   - ✅ No registry modifications

### macOS-Specific

1. **DMG Installation**:
   - ✅ DMG mounts correctly
   - ✅ Drag-to-Applications works
   - ✅ App launches from Applications
   - ✅ No Gatekeeper issues (if unsigned)

2. **Code Signing** (if applicable):
   - ✅ App is properly signed
   - ✅ No security warnings
   - ✅ Notarization successful

### Linux-Specific

1. **AppImage**:
   - ✅ Runs without installation
   - ✅ Executable permissions set correctly
   - ✅ Desktop integration works

2. **DEB Package**:
   - ✅ Installs via package manager
   - ✅ Dependencies resolved
   - ✅ Desktop entry created
   - ✅ Uninstalls cleanly

## Test Results Template

```markdown
## Test Results for PEFT Studio v1.0.1

**Platform**: [Windows/macOS/Linux]
**Installer**: [Filename]
**Tester**: [Name]
**Date**: [YYYY-MM-DD]

### Test 1: Fresh Installation (No Python)
- [ ] Pass / [ ] Fail
- Notes: 

### Test 2: Installation with Python (No ML Packages)
- [ ] Pass / [ ] Fail
- Notes:

### Test 3: Full Installation (All Dependencies)
- [ ] Pass / [ ] Fail
- Notes:

### Test 4: PEFT Algorithm Display
- [ ] Pass / [ ] Fail
- Notes:

### Test 5: Backend Service Reliability
- [ ] Pass / [ ] Fail
- Notes:

### Test 6: Error Handling
- [ ] Pass / [ ] Fail
- Notes:

### Test 7: Startup Performance
- [ ] Pass / [ ] Fail
- Startup Time: ___ seconds
- Notes:

### Test 8: Basic Functionality
- [ ] Pass / [ ] Fail
- Notes:

### Overall Result
- [ ] All tests passed - Ready for release
- [ ] Some tests failed - Issues need addressing
- [ ] Critical failures - Do not release

### Issues Found
1. 
2. 
3. 

### Recommendations
```

## Automated Testing

While manual testing is essential, automated tests can verify core functionality:

```bash
# Run all tests
npm test

# Run specific test suites
npm test -- backend/tests/test_backend_service_initialization.py
npm test -- backend/tests/test_dependency_verification.py
npm test -- src/test/pbt/peft-algorithm-completeness.pbt.test.ts
```

## Regression Testing

Verify that previous functionality still works:

1. **Model Browser**: Search and filter models
2. **Dataset Upload**: Upload and validate datasets
3. **Training Configuration**: Configure training runs
4. **Settings**: Update and save preferences
5. **Platform Connections**: Connect to HuggingFace, etc.

## Performance Benchmarks

Compare with v1.0.0:

- Startup time: Should be similar or faster
- Memory usage: Should be similar or lower
- UI responsiveness: Should be smooth (60fps)

## Known Limitations

Document any known issues that are acceptable for release:

1. GPU training requires CUDA-compatible NVIDIA GPU
2. Large model downloads may take time
3. Some cloud providers require manual credential setup

## Sign-Off

Before release, obtain sign-off from:

- [ ] Developer (functionality verified)
- [ ] QA Tester (all tests passed)
- [ ] Product Owner (release approved)

## Related Documentation

- `docs/user-guide/installation-windows.md`
- `docs/user-guide/installation-macos.md`
- `docs/user-guide/installation-linux.md`
- `docs/reference/troubleshooting.md`
- `docs/user-guide/checksum-verification.md`
