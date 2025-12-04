# PEFT Studio v1.0.1

This release fixes critical issues with backend service initialization and adds complete PEFT algorithm display.

## 🐛 Fixed

- **Backend Service Not Starting**: Fixed critical issue where Python backend service was not initializing properly, causing blank window on application startup
- **Backend Health Monitoring**: Added automatic health check polling and restart mechanism for crashed backend services
- **Port Conflict Resolution**: Implemented automatic alternative port selection when default port is in use
- **Dependency Verification**: Added comprehensive dependency checking on startup with clear error messages and fix instructions

## ✨ Added

- **PEFT Algorithm Display**: All five PEFT algorithms now visible in UI (LoRA, QLoRA, DoRA, PiSSA, RSLoRA) with descriptions and parameter controls
- **Algorithm Metadata**: Added detailed descriptions, recommended use cases, and parameter definitions for each PEFT algorithm
- **Dependency Status UI**: New component displays Python version, CUDA availability, and package installation status on startup
- **Startup Error Screen**: Clear error messages with diagnostic information and actionable recovery steps
- **Enhanced Splash Screen**: Progress indicators showing current initialization step during startup
- **Health Check Endpoints**: New `/api/health`, `/api/dependencies`, and `/api/startup/status` endpoints for monitoring

## 🔧 Improved

- **Error Handling**: Comprehensive error recovery mechanisms with automatic restart and manual recovery options
- **User Feedback**: Real-time status updates during application startup with progress indicators
- **Error Messages**: All errors now include what went wrong, why it happened, and how to fix it
- **Backend Process Management**: Robust Python process lifecycle management with proper cleanup on exit
- **Startup Flow**: Streamlined initialization sequence with better error detection and reporting

## 🧹 Cleaned

- **Repository Size**: Removed build artifacts, test caches, and redundant documentation files
- **Build Artifacts**: Cleaned `release/`, `dist/`, and `build/` directories (except essential files)
- **Test Artifacts**: Removed `.hypothesis/` and `.pytest_cache/` directories
- **Documentation**: Consolidated redundant completion status files into CHANGELOG

## 📦 Downloads

**Note**: Installers will be available once the release is built. For now, you can build from source:

```bash
git clone https://github.com/Ankesh-007/peft-studio.git
cd peft-studio
git checkout v1.0.1
npm install
npm run build
npm run electron:build
```

## 📋 System Requirements

**Minimum**:
- OS: Windows 10, macOS 11, or Ubuntu 20.04
- RAM: 8GB
- Storage: 10GB free space
- CPU: 4-core processor

**Recommended**:
- OS: Windows 11, macOS 13, or Ubuntu 22.04
- RAM: 16GB or more
- Storage: 50GB+ free space
- GPU: NVIDIA GPU with 8GB+ VRAM and CUDA support
- CPU: 8-core processor or better

## 🚀 Getting Started

1. Clone the repository or download the installer (when available)
2. Follow the installation instructions for your platform
3. Launch the application
4. Follow the dependency check prompts if needed
5. Start fine-tuning!

For detailed instructions, see the [Quick Start Guide](https://github.com/Ankesh-007/peft-studio/blob/main/docs/user-guide/quick-start.md).

## 📚 Documentation

- [Installation Guide](https://github.com/Ankesh-007/peft-studio/blob/main/docs/user-guide/installation.md)
- [Troubleshooting](https://github.com/Ankesh-007/peft-studio/blob/main/docs/reference/troubleshooting.md)
- [Full Documentation](https://github.com/Ankesh-007/peft-studio/tree/main/docs)

## 🐛 Known Issues

- GPU training requires CUDA-compatible NVIDIA GPU
- Some cloud providers require manual credential setup
- Large model downloads may take significant time depending on connection speed

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/Ankesh-007/peft-studio/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Ankesh-007/peft-studio/discussions)
- **Security**: See [SECURITY.md](https://github.com/Ankesh-007/peft-studio/blob/main/SECURITY.md)

## 🔄 Upgrading from v1.0.0

This release includes automatic update support. If you have v1.0.0 installed:

1. Launch PEFT Studio
2. You should see an update notification
3. Click "Download Update" to install v1.0.1
4. Restart the application

Alternatively, download and install manually from this release page.

## 📝 Full Changelog

See [CHANGELOG.md](https://github.com/Ankesh-007/peft-studio/blob/main/CHANGELOG.md) for complete details.

---

**Full Changelog**: https://github.com/Ankesh-007/peft-studio/compare/v1.0.0...v1.0.1
