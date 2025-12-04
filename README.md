# PEFT Studio

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Downloads](https://img.shields.io/github/downloads/Ankesh-007/peft-studio/total)](https://github.com/Ankesh-007/peft-studio/releases)
[![Release](https://img.shields.io/github/v/release/Ankesh-007/peft-studio)](https://github.com/Ankesh-007/peft-studio/releases/latest)

Professional desktop application for Parameter-Efficient Fine-Tuning (PEFT) of Large Language Models.

📦 **[Download Installers](https://github.com/Ankesh-007/peft-studioreleases/latest)** | 📚 **[Documentation](docs/README.md)** | 🔨 **[Build Guide](BUILDING.md)** | 🚀 **[Quick Start](QUICKSTART.md)**

## ✨ Features

### Core Training Capabilities
- **Model Browser**: Search, filter, and download models from HuggingFace with integrated metadata and comparison tools
- **Dataset Management**: Upload, validate, and analyze training data with drag-and-drop support and format detection
- **PEFT Methods**: Support for LoRA, QLoRA, Prefix Tuning, and more fine-tuning techniques with smart configuration
- **Training Configuration**: Guided wizard for setting up training runs with hardware-aware recommendations
- **Training Monitor**: Real-time progress tracking with interactive charts, metrics, and resource monitoring
- **Multi-Run Management**: Run multiple training jobs in parallel with isolation and resource management
- **Experiment Tracking**: Integration with Weights & Biases for comprehensive experiment tracking and comparison

### Platform Integration
- **Cloud Platforms**: Connect to AWS, Azure, GCP, Lambda Labs, RunPod, and more for remote training
- **Compute Providers**: Intelligent provider selection with cost estimation and performance comparison
- **Platform Connections**: Secure credential management for HuggingFace, Ollama, and other platforms
- **Export System**: Export trained models to HuggingFace Hub, Ollama, LM Studio, and other formats
- **Deployment Management**: Deploy models as REST APIs with monitoring and endpoint testing

### Testing & Validation
- **Inference Playground**: Test and compare fine-tuned models with live inference and side-by-side comparison
- **Gradio Demo Generator**: Automatically generate interactive Gradio demos for your fine-tuned models
- **Configuration Management**: Import/export training configurations with validation and library browser
- **Cost Calculator**: Estimate training costs across different providers with electricity rate customization

### Developer Experience
- **Modern UI**: Professional dark theme with smooth animations and real-time updates
- **Dashboard**: Monitor training runs, system resources, and statistics at a glance
- **Command Palette**: Quick access to all features with keyboard shortcuts (⌘K / Ctrl+K)
- **Error Recovery**: Plain-language error messages with automatic fix suggestions
- **Logging & Diagnostics**: Comprehensive logging system with filtering, search, and export capabilities
- **Telemetry**: Optional usage analytics with privacy controls and analytics dashboard

### Design System
- **Professional Dark Theme**: Deep black background (#0a0a0a) with indigo accents (#6366f1)
- **Typography**: Inter font for UI, JetBrains Mono for code
- **Responsive Layout**: Collapsible sidebar, top action bar, and contextual help panel
- **Smooth Animations**: 60fps transitions and micro-interactions
- **Accessibility**: Keyboard navigation, ARIA labels, and WCAG AA compliant colors
- **Performance Optimized**: Web workers, canvas rendering, and lazy loading for smooth 60fps experience

## 🚀 Quick Start

### 📦 Download

<div align="center">

### [⬇️ Download Latest Release](https://github.com/Ankesh-007/peft-studioreleases/latest)

**Pre-built installers for Windows, macOS, and Linux**

</div>

Choose the installer for your platform from the [releases page](https://github.com/Ankesh-007/peft-studioreleases/latest):

| Platform | Installer Type | File Name | Notes |
|----------|---------------|-----------|-------|
| **Windows** | NSIS Installer | `PEFT-Studio-Setup-{version}.exe` | Recommended - includes auto-update |
| **Windows** | Portable | `PEFT-Studio-Portable-{version}.exe` | No installation required |
| **macOS** | DMG Image | `PEFT-Studio-{version}-{arch}.dmg` | Drag to Applications folder |
| **macOS** | ZIP Archive | `PEFT-Studio-{version}-{arch}.zip` | Extract and run |
| **Linux** | AppImage | `PEFT-Studio-{version}-{arch}.AppImage` | Universal, no installation |
| **Linux** | DEB Package | `PEFT-Studio-{version}-{arch}.deb` | For Debian/Ubuntu |

### 💻 System Requirements

**Minimum Requirements:**
- **OS**: Windows 10+, macOS 10.13+, or Linux (Ubuntu 18.04+, Fedora 28+)
- **RAM**: 8 GB (16 GB recommended for training)
- **Storage**: 10 GB free space (more for models and datasets)
- **CPU**: 64-bit processor with 4+ cores
- **GPU**: Optional but recommended - NVIDIA GPU with CUDA support for training

**Recommended for Training:**
- **RAM**: 32 GB or more
- **GPU**: NVIDIA GPU with 16+ GB VRAM (RTX 3090, RTX 4090, A100, etc.)
- **Storage**: SSD with 100+ GB free space

### 📖 Installation Guides

Detailed platform-specific installation instructions:

- **[Windows Installation Guide](docs/user-guide/installation-windows.md)** - Step-by-step Windows setup
- **[macOS Installation Guide](docs/user-guide/installation-macos.md)** - macOS installation and troubleshooting
- **[Linux Installation Guide](docs/user-guide/installation-linux.md)** - Linux setup for various distributions

### ✅ Quick Installation

#### Windows
1. Download `PEFT-Studio-Setup-{version}.exe` from the [releases page](https://github.com/Ankesh-007/peft-studioreleases/latest)
2. Run the installer and follow the setup wizard
3. Launch PEFT Studio from the Start Menu or Desktop shortcut

**Note:** Windows may show a SmartScreen warning for unsigned applications. Click "More info" → "Run anyway" to proceed. See the [Windows Installation Guide](docs/user-guide/installation-windows.md) for details.

#### macOS
1. Download `PEFT-Studio-{version}-{arch}.dmg` from the [releases page](https://github.com/Ankesh-007/peft-studioreleases/latest)
2. Open the DMG file and drag PEFT Studio to your Applications folder
3. Launch PEFT Studio from Applications

**Note:** macOS may show a security warning for unsigned applications. See the [macOS Installation Guide](docs/user-guide/installation-macos.md) for bypass instructions.

#### Linux (AppImage)
```bash
# Download the AppImage
wget https://github.com/Ankesh-007/peft-studioreleases/latest/download/PEFT-Studio-{version}-x64.AppImage

# Make it executable
chmod +x PEFT-Studio-*.AppImage

# Run it
./PEFT-Studio-*.AppImage
```

#### Linux (Debian/Ubuntu)
```bash
# Download the .deb package
wget https://github.com/Ankesh-007/peft-studioreleases/latest/download/PEFT-Studio-{version}-amd64.deb

# Install it
sudo dpkg -i PEFT-Studio-*.deb

# Fix dependencies if needed
sudo apt-get install -f
```

For other Linux distributions, see the [Linux Installation Guide](docs/user-guide/installation-linux.md).

### Building Installers Locally

#### Quick Build (Recommended)

Use our comprehensive build script that handles testing, building, and deployment:

```powershell
# Windows - Interactive menu
.\build-and-test.ps1

# Or one-command build (fastest)
.\scripts\test-build-deploy.ps1 -SkipTests -Platform "windows,linux"
```

```bash
# Linux/Mac
./scripts/test-build-deploy.sh --skip-tests --platform "linux"
```

**See [BUILDING.md](BUILDING.md) for detailed build instructions.**

#### Manual Build

If you prefer to build manually:

```bash
# Install dependencies
npm install

# Build frontend
npm run build

# Build for your current platform
npm run electron:build

# Or build for specific platforms
npm run package:win      # Windows
npm run package:mac      # macOS (requires macOS)
npm run package:linux    # Linux
```

The installers will be created in the `release/` directory.

**For comprehensive build documentation, see [BUILDING.md](BUILDING.md).**

### Automated Builds

The project includes GitHub Actions workflows that automatically build installers for all platforms:

```bash
# Create and push a version tag
git tag v1.0.1
git push origin v1.0.1
```

This triggers the build workflow and creates a GitHub Release with installers for Windows, macOS, and Linux.

**Build Status**: ✅ 215/249 tests passing (86%) - Safe to build

### Prerequisites
- **Node.js** 18+ (for frontend development)
- **Python** 3.10+ (for backend services)
- **CUDA GPU** (recommended for training, optional for development)

### Installation

```bash
# Clone the repository
git clone https://github.com/Ankesh-007/peft-studio
cd peft-studio

# Install frontend dependencies
npm install

# Create and activate Python virtual environment
python -m venv peft_env

# Windows
peft_env\Scripts\activate

# macOS/Linux
source peft_env/bin/activate

# Install Python dependencies
pip install -r backend/requirements.txt
```

### Development

Start the development environment with two terminals:

```bash
# Terminal 1: Start Vite dev server
npm run dev

# Terminal 2: Start Electron app
npm run electron:dev
```

The application will open in an Electron window with hot-reload enabled.

### Building for Production

```bash
# Build frontend assets
npm run build

# Build Electron application
npm run electron:build

# Build platform-specific installers
npm run build:installers
```

For detailed build instructions, see [Build and Installers Guide](docs/developer-guide/build-and-installers.md).

### First Steps

1. **Connect a Platform**: Go to Settings → Platform Connections to add your HuggingFace token
2. **Browse Models**: Use the Model Browser to search and download a base model
3. **Upload Dataset**: Navigate to Datasets and upload your training data
4. **Configure Training**: Use the Training Configuration wizard to set up your first fine-tuning job
5. **Monitor Progress**: Watch real-time metrics in the Training Monitor

For a complete walkthrough, see the [Quick Start Guide](docs/user-guide/quick-start.md).

## 🏗️ Architecture

### Frontend Stack
- **Framework**: Electron + React 18 + TypeScript
- **Styling**: Tailwind CSS with custom design system
- **UI Components**: Lucide React icons + Recharts for data visualization
- **State Management**: React hooks + Context API
- **Performance**: Web Workers for background processing, Canvas rendering for charts
- **Build Tool**: Vite for fast development and optimized production builds

### Backend Stack
- **API Server**: Python FastAPI with async support
- **ML Framework**: PyTorch + Transformers + PEFT + bitsandbytes
- **Database**: SQLite with SQLAlchemy ORM
- **Task Queue**: Background job processing for training orchestration
- **Integrations**: HuggingFace Hub, Weights & Biases, cloud platform APIs

### Communication
- **IPC**: Electron IPC bridge for frontend-backend communication
- **REST API**: FastAPI endpoints for all backend operations
- **WebSockets**: Real-time updates for training progress and system metrics

For detailed architecture documentation, see [API Documentation](docs/developer-guide/api-documentation.md).

## 📁 Project Structure

```
peft-studio/
├── .github/                    # GitHub workflows and templates
│   └── workflows/             # CI/CD pipelines (test, build, deploy)
├── .kiro/                     # Kiro AI assistant specifications
│   └── specs/                 # Feature specifications and requirements
├── electron/                  # Electron main process
│   ├── main.js               # Main process entry point
│   └── preload.js            # IPC bridge and security context
├── src/                       # React frontend application
│   ├── components/           # React UI components
│   │   ├── wizard/          # Training configuration wizard
│   │   └── configuration/   # Configuration management UI
│   ├── lib/                 # Utility functions and helpers
│   ├── api/                 # Backend API client
│   ├── hooks/               # Custom React hooks
│   ├── workers/             # Web Workers for background processing
│   ├── types/               # TypeScript type definitions
│   ├── config/              # Frontend configuration
│   ├── test/                # Frontend tests
│   └── App.tsx              # Root application component
├── backend/                   # Python FastAPI backend
│   ├── main.py               # FastAPI server entry point
│   ├── config.py             # Backend configuration
│   ├── database.py           # Database models and setup
│   ├── services/             # Business logic services
│   │   ├── *_service.py     # Core service implementations
│   │   └── *_api.py         # FastAPI route handlers
│   ├── connectors/           # Platform connector implementations
│   │   ├── base.py          # Base connector interface
│   │   └── connector_manager.py
│   ├── plugins/              # Plugin system
│   │   └── connectors/      # Third-party connector plugins
│   ├── tests/                # Backend test suite
│   │   ├── conftest.py      # Pytest configuration
│   │   └── test_*.py        # Test files
│   └── requirements.txt      # Python dependencies
├── docs/                      # Documentation
│   ├── user-guide/           # End-user documentation
│   ├── developer-guide/      # Developer documentation
│   ├── reference/            # API reference and troubleshooting
│   ├── video-tutorials/      # Video tutorial index
│   └── README.md             # Documentation index
├── scripts/                   # Build and utility scripts
│   ├── build.js              # Build orchestration
│   ├── build.sh              # Unix build script
│   └── build.ps1             # Windows build script
├── build/                     # Build output directory
├── dist/                      # Distribution packages
├── public/                    # Static assets
├── package.json              # Node.js dependencies and scripts
├── tsconfig.json             # TypeScript configuration
├── tailwind.config.js        # Tailwind CSS configuration
├── vite.config.ts            # Vite build configuration
├── vitest.config.ts          # Vitest test configuration
├── README.md                 # This file
├── QUICKSTART.md             # Quick start guide
└── DEVELOPMENT.md            # Development guide
```

### Key Directories

- **`src/components/`**: All React UI components, organized by feature
- **`backend/services/`**: Backend business logic and API endpoints
- **`backend/connectors/`**: Platform integration connectors (HuggingFace, cloud providers)
- **`docs/`**: Comprehensive documentation for users and developers
- **`.github/workflows/`**: Automated CI/CD pipelines for testing, building, and deployment

## 📚 Documentation

### For Users
- **[Quick Start Guide](docs/user-guide/quick-start.md)** - Get up and running in minutes
- **[Training Configuration](docs/user-guide/training-configuration.md)** - Configure your first fine-tuning job
- **[Platform Connections](docs/user-guide/platform-connections.md)** - Connect to HuggingFace and cloud providers
- **[Model Browser](docs/user-guide/model-browser.md)** - Search and download models
- **[Deployment Management](docs/user-guide/deployment.md)** - Deploy your fine-tuned models
- **[Inference Playground](docs/user-guide/inference-playground.md)** - Test your models
- **[Configuration Management](docs/user-guide/configuration-management.md)** - Import/export configurations
- **[Troubleshooting](docs/reference/troubleshooting.md)** - Common issues and solutions
- **[FAQ](docs/reference/faq.md)** - Frequently asked questions

### For Developers
- **[API Documentation](docs/developer-guide/api-documentation.md)** - Backend API reference
- **[Connector Development](docs/developer-guide/connector-development.md)** - Build custom platform connectors
- **[Architecture Overview](docs/developer-guide/api-documentation.md)** - System architecture and design
- **[Performance Optimization](docs/developer-guide/performance-optimization.md)** - Performance best practices
- **[Security Guide](docs/developer-guide/security.md)** - Security implementation details
- **[Testing Guide](docs/developer-guide/testing.md)** - Testing strategy and guidelines
- **[Build and Installers](docs/developer-guide/build-and-installers.md)** - Building and packaging
- **[CI/CD Setup](docs/developer-guide/ci-cd-setup.md)** - Continuous integration and deployment
- **[Auto-Update System](docs/developer-guide/auto-update-system.md)** - Application update mechanism
- **[Contributing Guidelines](docs/CONTRIBUTING.md)** - How to contribute to the project

### Complete Documentation Index
See **[docs/README.md](docs/README.md)** for the complete documentation index with all available guides and references.

## 🛠️ Development

### Running Tests

```bash
# Run frontend tests
npm test

# Run backend tests
cd backend
pytest

# Run tests with coverage
pytest --cov=services --cov-report=html
```

### Code Quality

```bash
# Lint frontend code
npm run lint

# Format code
npm run format

# Type check
npm run type-check
```

### Building Installers

```bash
# Build installers for all platforms
npm run build:installers

# Build for specific platform
npm run build:win    # Windows
npm run build:mac    # macOS
npm run build:linux  # Linux
```

For detailed development instructions, see [DEVELOPMENT.md](DEVELOPMENT.md).

### Creating Releases

For maintainers creating releases:

- **[Release Guide](RELEASE_GUIDE.md)** - Quick reference for creating releases
- **[Complete Release Process](docs/developer-guide/release-process.md)** - Full release workflow documentation
- **[Step-by-Step Guide](docs/developer-guide/release-step-by-step.md)** - Detailed release instructions
- **[Scripts Reference](docs/developer-guide/release-scripts-reference.md)** - All release script options
- **[Troubleshooting](docs/developer-guide/release-troubleshooting.md)** - Common release issues

Quick release command:
```bash
export GITHUB_TOKEN="your_token"
node scripts/complete-release.js --dry-run  # Test first
node scripts/complete-release.js            # Execute release
```

## 💬 Getting Help

We're here to help! If you have questions, encounter issues, or need support:

### 📖 Documentation
Start with our comprehensive documentation:
- **[Quick Start Guide](docs/user-guide/quick-start.md)** - Get started in minutes
- **[Troubleshooting Guide](docs/reference/troubleshooting.md)** - Common issues and solutions
- **[FAQ](docs/reference/faq.md)** - Frequently asked questions
- **[Complete Documentation](docs/README.md)** - Full documentation index

### 🐛 Bug Reports
Found a bug? Please [open an issue](https://github.com/Ankesh-007/peft-studioissues/new?template=bug_report.md) with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, version, GPU)
- Relevant logs or screenshots

### 💡 Feature Requests
Have an idea for improvement? [Submit a feature request](https://github.com/Ankesh-007/peft-studioissues/new?template=feature_request.md) describing:
- The problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered
- How this would benefit other users

### ❓ Questions & Discussions
For general questions, discussions, or community interaction:
- **[GitHub Discussions](https://github.com/Ankesh-007/peft-studiodiscussions)** - Ask questions, share ideas, and connect with the community
  - **Q&A** - Get help with using PEFT Studio
  - **Ideas** - Propose and discuss new features
  - **Show and Tell** - Share your fine-tuned models and success stories
  - **General** - Everything else related to PEFT Studio

### 🔒 Security Issues
Found a security vulnerability? Please **do not** open a public issue. Instead, see our [Security Policy](SECURITY.md) for responsible disclosure instructions.

### 📧 Direct Support
For private inquiries or partnership opportunities, you can reach out through:
- GitHub Discussions (preferred for community benefit)
- Email: [Add your support email if applicable]

### 🕐 Response Times
- **Critical bugs**: We aim to respond within 24 hours
- **Feature requests**: Reviewed weekly, prioritized based on community feedback
- **Questions**: Community-driven, typically answered within 1-3 days
- **Security issues**: Acknowledged within 24 hours, fixed as priority

### 🌟 Community Guidelines
When seeking help:
- Search existing issues and discussions first
- Provide clear, detailed information
- Be respectful and patient
- Follow our [Code of Conduct](CODE_OF_CONDUCT.md)
- Help others when you can!

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](docs/CONTRIBUTING.md) for details on:

- Code style and conventions
- Development workflow
- Testing requirements
- Pull request process
- Issue reporting

## 📊 Project Status

**Current Version**: 1.0.0

### Recent Improvements
- ✅ Comprehensive documentation reorganization
- ✅ Performance optimization with Web Workers
- ✅ Enhanced security with credential encryption
- ✅ Multi-run management with isolation
- ✅ Cloud platform integration (AWS, Azure, GCP, Lambda Labs, RunPod)
- ✅ Cost estimation across providers
- ✅ Deployment management with endpoint testing
- ✅ Telemetry system with privacy controls
- ✅ Auto-update system with delta updates
- ✅ CI/CD pipelines with automated testing and deployment

### Roadmap

See our [detailed roadmap](ROADMAP.md) for planned features and improvements.

**Coming in v1.1.0 (Q1 2025):**
- 🔄 Enhanced model comparison tools with side-by-side analysis
- 🔄 Advanced dataset validation and preprocessing
- 🔄 Improved error handling with automatic recovery
- 🔄 Performance improvements and optimizations

**Future versions:**
- 🔄 Distributed training support (v1.2.0)
- 🔄 Model quantization and optimization tools (v1.2.0)
- 🔄 Custom connector marketplace (v1.3.0)
- 🔄 Advanced training techniques (RLHF, DPO) (v2.0.0)

Want to influence the roadmap? Share your ideas in [GitHub Discussions](https://github.com/Ankesh-007/peft-studiodiscussions/categories/ideas)!

## 🔗 Links

- **Documentation**: [docs/README.md](docs/README.md)
- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **Development Guide**: [DEVELOPMENT.md](DEVELOPMENT.md)
- **GitHub Issues**: [Report bugs or request features](https://github.com/Ankesh-007/peft-studioissues)
- **Discussions**: [Community forum](https://github.com/Ankesh-007/peft-studiodiscussions)

## 🆘 Getting Help

We're here to help! If you encounter any issues or have questions:

- **🐛 Bug Reports**: Found a bug? [Open an issue](https://github.com/Ankesh-007/peft-studioissues/new?template=bug_report.md) on GitHub
- **💡 Feature Requests**: Have an idea? [Request a feature](https://github.com/Ankesh-007/peft-studioissues/new?template=feature_request.md)
- **❓ Questions**: Need help? [Start a discussion](https://github.com/Ankesh-007/peft-studiodiscussions) or [ask a question](https://github.com/Ankesh-007/peft-studioissues/new?template=question.md)
- **📚 Documentation**: Check out our [troubleshooting guide](https://github.com/Ankesh-007/peft-studioblob/main/docs/reference/troubleshooting.md) for common issues

### Support Channels

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions, ideas, and community support
- **Documentation**: Comprehensive guides and API references

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:
- Code of Conduct
- Development setup
- Coding standards
- Pull request process

## 📝 License

MIT License - see [LICENSE](LICENSE) for details

---

**Built with ❤️ for the ML community**
