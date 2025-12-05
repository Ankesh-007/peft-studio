# Backend Bundling Troubleshooting Guide

This guide provides solutions to common issues encountered when building and running the bundled Python backend.

## Table of Contents

- [Build-Time Issues](#build-time-issues)
- [Runtime Issues](#runtime-issues)
- [Performance Issues](#performance-issues)
- [Platform-Specific Issues](#platform-specific-issues)
- [Debugging Techniques](#debugging-techniques)

## Build-Time Issues

### PyInstaller Not Found

**Symptoms:**
```
'pyinstaller' is not recognized as an internal or external command
```

**Cause:** PyInstaller is not installed or not in PATH

**Solutions:**

1. **Install PyInstaller:**
   ```bash
   pip install pyinstaller
   ```

2. **Verify installation:**
   ```bash
   pyinstaller --version
   ```

3. **If still not found, use full path:**
   ```bash
   python -m PyInstaller backend/peft_engine.spec
   ```

4. **Check Python Scripts directory is in PATH:**
   - Windows: `C:\Users\<username>\AppData\Local\Programs\Python\Python310\Scripts`
   - macOS/Linux: `~/.local/bin` or `/usr/local/bin`

---

### Python Version Mismatch

**Symptoms:**
```
Python 3.10+ required, found 3.9.x
Build environment verification failed
```

**Cause:** Python version is too old

**Solutions:**

1. **Install Python 3.10 or higher:**
   - Download from [python.org](https://www.python.org/downloads/)
   - Or use package manager:
     ```bash
     # macOS
     brew install python@3.10
     
     # Ubuntu
     sudo apt-get install python3.10
     
     # Windows
     winget install Python.Python.3.10
     ```

2. **Use specific Python version:**
   ```bash
   python3.10 -m pip install pyinstaller
   python3.10 -m PyInstaller backend/peft_engine.spec
   ```

3. **Create virtual environment with correct version:**
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate  # Unix
   venv\Scripts\activate     # Windows
   pip install -r backend/requirements.txt
   pip install pyinstaller
   ```

---

### Missing Dependencies

**Symptoms:**
```
ModuleNotFoundError: No module named 'torch'
ModuleNotFoundError: No module named 'fastapi'
```

**Cause:** Backend dependencies not installed

**Solutions:**

1. **Install all dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Verify installation:**
   ```bash
   pip list | grep torch
   pip list | grep fastapi
   ```

3. **If using virtual environment, ensure it's activated:**
   ```bash
   # Check which Python is being used
   which python  # Unix
   where python  # Windows
   ```

---

### Hidden Import Errors

**Symptoms:**
```
ImportError: cannot import name 'X' from 'Y'
ModuleNotFoundError at runtime (but module is installed)
```

**Cause:** PyInstaller didn't detect dynamically imported modules

**Solutions:**

1. **Add to hiddenimports in `backend/peft_engine.spec`:**
   ```python
   hiddenimports=[
       # Existing imports...
       'your_module_name',
       'your_package.*',  # Include all submodules
   ]
   ```

2. **Common hidden imports to add:**
   ```python
   hiddenimports=[
       # Uvicorn
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
       
       # Services (lazy-loaded)
       'services.peft_service',
       'services.hardware_service',
       'services.dataset_service',
       # ... add all service modules
       
       # Connectors (plugins)
       'connectors.*',
       'plugins.connectors.*',
   ]
   ```

3. **Use dependency detection script:**
   ```bash
   python backend/build_hooks.py
   ```
   This will analyze all imports and suggest additions.

4. **Rebuild after adding imports:**
   ```bash
   npm run build:backend
   ```

---

### Data Files Not Bundled

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'config.py'
```

**Cause:** Data files not included in PyInstaller bundle

**Solutions:**

1. **Add to datas in `backend/peft_engine.spec`:**
   ```python
   datas=[
       ('config.py', '.'),
       ('database.py', '.'),
       ('services/*.py', 'services'),
       ('data/*.json', 'data'),
   ]
   ```

2. **Use runtime path resolution:**
   ```python
   from runtime_paths import get_resource_path
   
   config_path = get_resource_path('config.py')
   ```

3. **Verify files are bundled:**
   ```bash
   # Extract bundle to inspect (Unix)
   python -c "import PyInstaller.utils.hooks as h; print(h.get_package_paths('your_package'))"
   ```

---

### Build Fails with Permission Error

**Symptoms:**
```
PermissionError: [WinError 5] Access is denied
[Errno 13] Permission denied: 'backend/dist/peft_engine.exe'
```

**Cause:** File is in use or antivirus is blocking

**Solutions:**

1. **Close running instances:**
   ```bash
   # Windows
   taskkill /F /IM peft_engine.exe
   
   # Unix
   pkill -9 peft_engine
   ```

2. **Disable antivirus temporarily:**
   - Add `backend/dist/` to exclusions
   - Or disable real-time protection during build

3. **Run as administrator (Windows):**
   - Right-click PowerShell → Run as Administrator
   - Then run build command

4. **Clean build directory:**
   ```bash
   rm -rf backend/dist backend/build
   npm run build:backend
   ```

---

### Executable Too Large

**Symptoms:**
```
Backend executable is 3.5 GB
Installer is too large to distribute
```

**Cause:** All dependencies bundled, including large ML libraries

**Solutions:**

1. **Expected size:** 500MB - 2GB is normal for ML applications

2. **Exclude unused packages:**
   ```python
   # In peft_engine.spec
   excludes=[
       'matplotlib',  # If not used
       'scipy',       # If not used
       'pandas',      # If not used
       'jupyter',     # Development only
   ]
   ```

3. **Use onedir instead of onefile:**
   ```python
   # In peft_engine.spec
   exe = EXE(
       # ...
       onefile=False,  # Creates directory instead of single file
   )
   ```
   This is faster and sometimes smaller.

4. **Strip debug symbols:**
   ```python
   exe = EXE(
       # ...
       strip=True,
   )
   ```

5. **Use UPX compression (optional):**
   ```python
   exe = EXE(
       # ...
       upx=True,
   )
   ```
   Note: May trigger antivirus false positives.

---

### Build Fails on CI/CD

**Symptoms:**
```
GitHub Actions build fails
PyInstaller not found in CI
```

**Cause:** CI environment not properly configured

**Solutions:**

1. **Verify workflow includes PyInstaller installation:**
   ```yaml
   - name: Install PyInstaller
     run: pip install pyinstaller
   ```

2. **Install backend dependencies:**
   ```yaml
   - name: Install backend dependencies
     run: |
       cd backend
       pip install -r requirements.txt
   ```

3. **Check Python version in CI:**
   ```yaml
   - name: Set up Python
     uses: actions/setup-python@v4
     with:
       python-version: '3.10'
   ```

4. **Review CI logs:**
   - Go to Actions tab on GitHub
   - Click on failed workflow
   - Review build logs for specific errors

---

## Runtime Issues

### Executable Not Found

**Symptoms:**
```
Backend executable not found: /path/to/peft_engine
Installation may be corrupted. Please reinstall.
```

**Cause:** Executable not included in installer or wrong path

**Solutions:**

1. **Verify executable exists:**
   ```bash
   # Check if file exists
   ls backend/dist/peft_engine*
   ```

2. **Check electron-builder configuration:**
   ```json
   {
     "build": {
       "extraResources": [
         {
           "from": "backend/dist/peft_engine${/*}",
           "to": "backend",
           "filter": ["peft_engine*"]
         }
       ]
     }
   }
   ```

3. **Rebuild application:**
   ```bash
   npm run build:backend
   npm run build:all
   ```

4. **Check installed app structure:**
   - Windows: `C:\Program Files\PEFT Studio\resources\backend\`
   - macOS: `PEFT Studio.app/Contents/Resources/backend/`
   - Linux: `/opt/PEFT Studio/resources/backend/`

---

### Permission Denied (Unix)

**Symptoms:**
```
Permission denied: /path/to/peft_engine
EACCES: permission denied
```

**Cause:** Executable doesn't have execute permissions

**Solutions:**

1. **App attempts automatic fix:**
   The BackendServiceManager tries `chmod +x` automatically.

2. **Manual fix:**
   ```bash
   chmod +x /path/to/peft_engine
   ```

3. **For AppImage:**
   ```bash
   chmod +x PEFT-Studio.AppImage
   ```

4. **Check file permissions:**
   ```bash
   ls -l /path/to/peft_engine
   # Should show: -rwxr-xr-x
   ```

---

### Missing Module at Runtime

**Symptoms:**
```
ModuleNotFoundError: No module named 'X'
ImportError: cannot import name 'Y'
```

**Cause:** Module not included in bundle (hidden import issue)

**Solutions:**

1. **Add to hiddenimports and rebuild:**
   ```python
   # In backend/peft_engine.spec
   hiddenimports=[
       # ... existing
       'missing_module_name',
   ]
   ```

2. **Check if module is lazy-loaded:**
   Look for dynamic imports in the code:
   ```python
   # These need to be in hiddenimports
   importlib.import_module('module_name')
   __import__('module_name')
   ```

3. **Test import in bundled executable:**
   ```bash
   cd backend/dist
   ./peft_engine -c "import module_name; print('OK')"
   ```

4. **Rebuild with verbose output:**
   ```bash
   pyinstaller --log-level DEBUG backend/peft_engine.spec
   ```
   Check the build log for warnings about missing modules.

---

### Backend Crashes on Startup

**Symptoms:**
```
Backend process exited with code 1
Backend failed to start
```

**Cause:** Various runtime errors

**Solutions:**

1. **Check application logs:**
   - Windows: `%APPDATA%\PEFT Studio\logs\main.log`
   - macOS: `~/Library/Logs/PEFT Studio/main.log`
   - Linux: `~/.config/PEFT Studio/logs/main.log`

2. **Run executable directly to see errors:**
   ```bash
   cd backend/dist
   ./peft_engine
   ```
   Check console output for error messages.

3. **Enable debug mode:**
   Edit `backend/peft_engine.spec`:
   ```python
   exe = EXE(
       # ...
       console=True,  # Show console window
       debug=True,    # Enable debug output
   )
   ```
   Rebuild and run again.

4. **Check for missing data files:**
   ```python
   # In your code, add logging
   import sys
   print(f"Running from: {sys._MEIPASS if getattr(sys, 'frozen', False) else __file__}")
   ```

5. **Verify all dependencies are bundled:**
   ```bash
   npm run build:backend:verify
   ```

---

### Port Already in Use

**Symptoms:**
```
Address already in use: 8000
OSError: [Errno 48] Address already in use
```

**Cause:** Another process is using port 8000

**Solutions:**

1. **App automatically tries ports 8000-8010:**
   The BackendServiceManager handles this automatically.

2. **Find and kill process using the port:**
   ```bash
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID <pid> /F
   
   # macOS/Linux
   lsof -ti:8000 | xargs kill -9
   ```

3. **Change port range in `electron/main.js`:**
   ```javascript
   // Modify port range if needed
   for (let port = 8000; port <= 8020; port++) {
       // ...
   }
   ```

---

### Data Files Not Accessible

**Symptoms:**
```
FileNotFoundError: config.py not found
Cannot read configuration file
```

**Cause:** Data files not bundled or wrong path

**Solutions:**

1. **Use runtime path resolution:**
   ```python
   from runtime_paths import get_resource_path
   
   config_path = get_resource_path('config.py')
   with open(config_path) as f:
       config = f.read()
   ```

2. **Verify files are bundled:**
   Check `backend/peft_engine.spec`:
   ```python
   datas=[
       ('config.py', '.'),
       # ... other files
   ]
   ```

3. **Debug path resolution:**
   ```python
   import sys
   import os
   
   if getattr(sys, 'frozen', False):
       print(f"Bundle path: {sys._MEIPASS}")
       print(f"Files: {os.listdir(sys._MEIPASS)}")
   ```

---

## Performance Issues

### Slow Startup Time

**Symptoms:**
```
Backend takes 10+ seconds to start
Application feels sluggish on launch
```

**Cause:** Large dependencies loaded at startup

**Solutions:**

1. **Verify lazy loading is enabled:**
   Check `backend/services/lazy_imports.py` is being used.

2. **Profile startup:**
   ```python
   import time
   start = time.time()
   # ... import statements
   print(f"Import took {time.time() - start:.2f}s")
   ```

3. **Add to antivirus exclusions:**
   - Windows Defender: Add `peft_engine.exe` to exclusions
   - Other antivirus: Add application directory

4. **Use SSD instead of HDD:**
   Bundled executables benefit significantly from faster disk I/O.

5. **Reduce startup dependencies:**
   Move heavy imports to lazy-loaded modules.

---

### High Memory Usage

**Symptoms:**
```
Backend uses 2GB+ RAM
System becomes slow
```

**Cause:** All dependencies loaded in memory

**Solutions:**

1. **Expected memory usage:** 500MB - 1.5GB is normal for ML applications

2. **Ensure lazy loading works:**
   Heavy modules should only load when needed.

3. **Monitor memory usage:**
   ```python
   import psutil
   process = psutil.Process()
   print(f"Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB")
   ```

4. **Use onedir instead of onefile:**
   ```python
   # In peft_engine.spec
   exe = EXE(
       # ...
       onefile=False,
   )
   ```
   This can reduce memory usage.

5. **Unload unused models:**
   Implement model unloading in your code.

---

### Slow API Responses

**Symptoms:**
```
API calls take longer than in development
Timeout errors
```

**Cause:** Various performance issues

**Solutions:**

1. **Check if running in debug mode:**
   Ensure `console=False` and `debug=False` in production builds.

2. **Profile API endpoints:**
   ```python
   import time
   
   @app.get("/api/endpoint")
   async def endpoint():
       start = time.time()
       # ... logic
       print(f"Endpoint took {time.time() - start:.2f}s")
   ```

3. **Check disk I/O:**
   Bundled executables may have slower file access.

4. **Verify network connectivity:**
   Ensure firewall isn't blocking the backend.

---

## Platform-Specific Issues

### Windows

#### Antivirus False Positives

**Symptoms:**
```
Windows Defender blocks executable
Antivirus quarantines peft_engine.exe
```

**Solutions:**

1. **Sign the executable:**
   ```bash
   $env:CSC_LINK = "path\to\certificate.pfx"
   $env:CSC_KEY_PASSWORD = "password"
   npm run build:win
   ```

2. **Add to exclusions:**
   - Windows Defender → Virus & threat protection → Exclusions
   - Add `peft_engine.exe`

3. **Submit to Microsoft:**
   - If false positive, submit to: https://www.microsoft.com/en-us/wdsi/filesubmission

#### Console Window Appears

**Symptoms:**
```
Black console window appears with the app
```

**Solutions:**

1. **Verify console mode in spec:**
   ```python
   exe = EXE(
       # ...
       console=False,  # Should be False
   )
   ```

2. **Rebuild:**
   ```bash
   npm run build:backend
   ```

---

### macOS

#### Gatekeeper Blocks Execution

**Symptoms:**
```
"peft_engine" cannot be opened because the developer cannot be verified
```

**Solutions:**

1. **Sign and notarize:**
   ```bash
   export CSC_LINK="path/to/certificate.p12"
   export APPLE_ID="your@email.com"
   export APPLE_ID_PASSWORD="app-specific-password"
   npm run build:mac
   ```

2. **User workaround:**
   - Right-click executable → Open
   - Click "Open" in dialog

3. **Remove quarantine attribute:**
   ```bash
   xattr -d com.apple.quarantine /path/to/peft_engine
   ```

#### Universal Binary Issues

**Symptoms:**
```
Executable doesn't run on Apple Silicon
Rosetta 2 required
```

**Solutions:**

1. **Build on macOS with both architectures:**
   Must build on macOS 11+ with Xcode 12+

2. **Verify universal binary:**
   ```bash
   lipo -info backend/dist/peft_engine
   # Should show: x86_64 arm64
   ```

3. **Build separately if needed:**
   ```bash
   # On Intel Mac
   npm run build:backend:mac

   # On Apple Silicon Mac
   npm run build:backend:mac
   ```

---

### Linux

#### GLIBC Version Mismatch

**Symptoms:**
```
version `GLIBC_2.34' not found
```

**Cause:** Built on newer Linux, running on older

**Solutions:**

1. **Build on older Linux:**
   Use Ubuntu 20.04 or CentOS 7 for maximum compatibility.

2. **Use Docker for consistent builds:**
   ```dockerfile
   FROM ubuntu:20.04
   RUN apt-get update && apt-get install -y python3.10
   # ... build steps
   ```

3. **Static linking (advanced):**
   Modify PyInstaller to use static linking.

#### Missing FUSE

**Symptoms:**
```
AppImage requires FUSE to run
dlopen(): error loading libfuse.so.2
```

**Solutions:**

1. **Install FUSE:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install libfuse2
   
   # Fedora
   sudo dnf install fuse-libs
   
   # Arch
   sudo pacman -S fuse2
   ```

2. **Extract and run:**
   ```bash
   ./PEFT-Studio.AppImage --appimage-extract
   ./squashfs-root/AppRun
   ```

---

## Debugging Techniques

### Enable Verbose Logging

1. **PyInstaller build:**
   ```bash
   pyinstaller --log-level DEBUG backend/peft_engine.spec
   ```

2. **Runtime logging:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **Electron logging:**
   Check logs in:
   - Windows: `%APPDATA%\PEFT Studio\logs\`
   - macOS: `~/Library/Logs/PEFT Studio/`
   - Linux: `~/.config/PEFT Studio/logs/`

### Test Executable Independently

```bash
# Run executable directly
cd backend/dist
./peft_engine

# Test specific functionality
./peft_engine -c "import torch; print(torch.__version__)"

# Check health endpoint
curl http://localhost:8000/api/health
```

### Inspect Bundle Contents

```bash
# Extract PyInstaller bundle (Unix)
python -c "import PyInstaller.archive.readers as r; r.CArchiveReader('backend/dist/peft_engine').extract('extracted')"

# List contents
ls extracted/

# Check for missing files
```

### Use Debug Build

```python
# In peft_engine.spec
exe = EXE(
    # ...
    console=True,   # Show console
    debug=True,     # Enable debug
)
```

### Monitor Process

```bash
# Windows
tasklist | findstr peft_engine

# Unix
ps aux | grep peft_engine

# Monitor resources
top -p $(pgrep peft_engine)
```

### Check Network Connectivity

```bash
# Test if backend is listening
netstat -an | grep 8000

# Test health endpoint
curl -v http://localhost:8000/api/health

# Check firewall
# Windows
netsh advfirewall show allprofiles

# Linux
sudo ufw status
```

## Getting Help

If you're still experiencing issues:

1. **Check logs:**
   - Application logs
   - Build logs
   - System logs

2. **Gather information:**
   - Platform and version
   - Python version
   - PyInstaller version
   - Error messages
   - Steps to reproduce

3. **Search existing issues:**
   - GitHub Issues
   - PyInstaller documentation
   - Stack Overflow

4. **Open a new issue:**
   - Include all gathered information
   - Attach relevant logs
   - Describe expected vs actual behavior

## Related Documentation

- [Backend Bundling Guide](backend-bundling.md) - Main documentation
- [Build and Installers](build-and-installers.md) - Build process
- [Testing Guide](testing.md) - Testing strategies

## Summary

Most backend bundling issues fall into these categories:

- **Build Issues**: Usually missing dependencies or configuration
- **Runtime Issues**: Often hidden imports or data file paths
- **Performance Issues**: Typically lazy loading or antivirus
- **Platform Issues**: Usually permissions or signing

The key to troubleshooting is:
1. Check logs first
2. Test executable independently
3. Enable debug mode
4. Verify configuration
5. Rebuild if needed

With proper configuration and testing, the bundled backend provides a seamless user experience across all platforms.
