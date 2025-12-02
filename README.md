# PEFT Studio

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/Ankesh-007/peft-studio/workflows/CI/badge.svg)](https://github.com/Ankesh-007/peft-studio/actions)
[![Tests](https://github.com/Ankesh-007/peft-studio/workflows/Tests/badge.svg)](https://github.com/Ankesh-007/peft-studio/actions)
[![GitHub release](https://img.shields.io/github/v/release/Ankesh-007/peft-studio)](https://github.com/Ankesh-007/peft-studio/releases)
[![GitHub stars](https://img.shields.io/github/stars/Ankesh-007/peft-studio?style=social)](https://github.com/Ankesh-007/peft-studio/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Ankesh-007/peft-studio?style=social)](https://github.com/Ankesh-007/peft-studio/network/members)
[![GitHub issues](https://img.shields.io/github/issues/Ankesh-007/peft-studio)](https://github.com/Ankesh-007/peft-studio/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/Ankesh-007/peft-studio)](https://github.com/Ankesh-007/peft-studio/pulls)
[![GitHub contributors](https://img.shields.io/github/contributors/Ankesh-007/peft-studio)](https://github.com/Ankesh-007/peft-studio/graphs/contributors)
[![GitHub last commit](https://img.shields.io/github/last-commit/Ankesh-007/peft-studio)](https://github.com/Ankesh-007/peft-studio/commits/main)

Professional desktop application for Parameter-Efficient Fine-Tuning (PEFT) of Large Language Models.

## ✨ Features

- **Modern UI**: Dark theme with smooth animations and real-time updates
- **Dashboard**: Monitor training runs, system resources, and statistics
- **Dataset Management**: Upload, validate, and analyze training data
- **Model Browser**: Search and download models from HuggingFace
- **PEFT Methods**: LoRA, QLoRA, Prefix Tuning, and more
- **Training Monitor**: Real-time progress with interactive charts
- **Inference Playground**: Test fine-tuned models
- **Platform Integration**: Export to HuggingFace, Ollama, LM Studio

## 🚀 Quick Start

### Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** 18 or higher ([Download](https://nodejs.org/))
- **Python** 3.10 or higher ([Download](https://www.python.org/downloads/))
- **Git** ([Download](https://git-scm.com/downloads))
- **CUDA GPU** (recommended for training, but CPU mode is supported)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Ankesh-007/peft-studio.git
   cd peft-studio
   ```

2. **Install Node.js dependencies**
   ```bash
   npm install
   ```

3. **Set up Python environment**
   
   **Windows:**
   ```bash
   python -m venv peft_env
   peft_env\Scripts\activate
   pip install -r backend/requirements.txt
   ```
   
   **macOS/Linux:**
   ```bash
   python3 -m venv peft_env
   source peft_env/bin/activate
   pip install -r backend/requirements.txt
   ```

4. **Verify installation**
   ```bash
   npm test
   cd backend && pytest
   ```

### Development

Run the application in development mode:

```bash
# Terminal 1: Start the frontend development server
npm run dev

# Terminal 2: Start the Electron application
npm run electron:dev
```

The application will open automatically. The frontend will hot-reload on changes.

### Building for Production

Create production builds for your platform:

```bash
# Build the frontend
npm run build

# Build the Electron application
npm run electron:build
```

Built applications will be available in the `release/` directory.

### Platform-Specific Builds

```bash
# Windows
npm run package:win

# macOS
npm run package:mac

# Linux
npm run package:linux
```

## 🏗️ Architecture

- **Frontend**: Electron + React + TypeScript + Tailwind CSS
- **UI Components**: Lucide React icons + Recharts
- **Backend**: Python FastAPI
- **ML Framework**: PyTorch + Transformers + PEFT + bitsandbytes
- **Database**: SQLite
- **IPC**: Electron IPC for frontend-backend communication

## 📁 Project Structure

```
peft-studio/
├── electron/           # Electron main process
│   ├── main.js        # Main process entry
│   └── preload.js     # IPC bridge
├── src/               # React frontend
│   ├── components/    # UI components
│   ├── lib/          # Utilities
│   ├── api/          # API client
│   └── App.tsx       # Root component
├── backend/          # Python FastAPI backend
│   ├── main.py       # FastAPI server
│   ├── config.py     # Configuration
│   ├── database.py   # SQLAlchemy models
│   └── requirements.txt
└── package.json
```

## 🎨 UI Components

- **Layout**: Sidebar navigation + top bar + main content
- **Dashboard**: Stats cards, training runs, charts
- **Dataset Upload**: Drag-and-drop with progress tracking
- **Charts**: Line charts, bar charts using Recharts
- **Theme**: Dark mode with customizable accents

## 🔧 Configuration

The application uses a design system with:
- Custom Tailwind configuration
- Design tokens for colors, spacing, typography
- Reusable component classes
- Smooth animations and transitions

## 🆘 Getting Help

We're here to help! If you encounter any issues or have questions:

- **🐛 Bug Reports**: Found a bug? [Open an issue](https://github.com/Ankesh-007/peft-studio/issues/new?template=bug_report.md) on GitHub
- **💡 Feature Requests**: Have an idea? [Request a feature](https://github.com/Ankesh-007/peft-studio/issues/new?template=feature_request.md)
- **❓ Questions**: Need help? [Start a discussion](https://github.com/Ankesh-007/peft-studio/discussions) or [ask a question](https://github.com/Ankesh-007/peft-studio/issues/new?template=question.md)
- **📚 Documentation**: Check out our [troubleshooting guide](https://github.com/Ankesh-007/peft-studio/blob/main/docs/reference/troubleshooting.md) for common issues

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

MIT License - see the [LICENSE](LICENSE) file for details
