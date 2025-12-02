# PEFT Studio v1.0.0 - Initial Public Release

🎉 **Welcome to PEFT Studio!** This is the first public release of our professional desktop application for Parameter-Efficient Fine-Tuning (PEFT) of Large Language Models.

## 🚀 What is PEFT Studio?

PEFT Studio is a cross-platform desktop application that makes fine-tuning large language models accessible and efficient. Built with Electron, React, and Python, it provides a professional interface for training, monitoring, and deploying fine-tuned models.

## ✨ Key Features

### Core Capabilities
- **🖥️ Cross-Platform Desktop App**: Works on Windows, macOS, and Linux
- **🎨 Modern UI**: Professional dark theme with smooth animations
- **📊 Real-Time Monitoring**: Track training progress with interactive charts
- **📁 Dataset Management**: Upload, validate, and analyze training datasets
- **🤖 Model Browser**: Search and download models from HuggingFace Hub
- **⚡ PEFT Methods**: Support for LoRA, QLoRA, Prefix Tuning, and more
- **🎮 Inference Playground**: Test and evaluate your fine-tuned models
- **🔄 Platform Integration**: Export to HuggingFace, Ollama, and LM Studio

### Advanced Features
- **💰 Cost Calculator**: Real-time training cost estimation with customizable electricity rates
- **☁️ Cloud Platform Comparison**: Compare costs and performance across providers
- **⏸️ Paused Run Management**: Save and resume training runs with checkpoint management
- **🔔 Notification System**: Desktop and in-app notifications for training events
- **❓ Contextual Help**: Technical term detection, tooltips, and interactive tutorials
- **♿ Accessibility**: Full keyboard navigation and screen reader support

### Developer Features
- **✅ Comprehensive Testing**: Unit tests, integration tests, and property-based testing
- **🔍 Code Quality**: ESLint, Prettier, Black, and flake8 integration
- **🏗️ Modern Build System**: Vite for fast development, Electron Builder for packaging
- **📚 Documentation**: Complete user and developer documentation

## 📦 Installation

### Prerequisites
- **Node.js**: 18.x or higher
- **Python**: 3.10 or higher
- **GPU**: CUDA-compatible GPU recommended (NVIDIA)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space minimum

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Ankesh-007/peft-studio.git
   cd peft-studio
   ```

2. **Install dependencies**
   ```bash
   npm install
   cd backend && pip install -r requirements.txt && cd ..
   ```

3. **Start the application**
   ```bash
   npm run dev
   ```

For detailed installation instructions, see the [README](https://github.com/Ankesh-007/peft-studio#readme).

## 🛠️ Technical Stack

- **Frontend**: Electron 33.x, React 18.x, TypeScript 5.x, Tailwind CSS 3.x
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy
- **ML Framework**: PyTorch, Transformers, PEFT, bitsandbytes
- **UI Libraries**: Lucide React (icons), Recharts (charts)
- **Testing**: Vitest, pytest, fast-check, Hypothesis
- **Build Tools**: Vite, Electron Builder

## 📖 Documentation

- [README](https://github.com/Ankesh-007/peft-studio/blob/main/README.md) - Quick start and overview
- [FEATURES](https://github.com/Ankesh-007/peft-studio/blob/main/FEATURES.md) - Detailed feature showcase
- [CONTRIBUTING](https://github.com/Ankesh-007/peft-studio/blob/main/CONTRIBUTING.md) - Contribution guidelines
- [DEVELOPMENT](https://github.com/Ankesh-007/peft-studio/blob/main/DEVELOPMENT.md) - Development guide
- [SECURITY](https://github.com/Ankesh-007/peft-studio/blob/main/SECURITY.md) - Security policy

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](https://github.com/Ankesh-007/peft-studio/blob/main/CONTRIBUTING.md) for details on:
- Code style and standards
- Development workflow
- Testing requirements
- Commit conventions

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/Ankesh-007/peft-studio/blob/main/LICENSE) file for details.

## 🙏 Acknowledgments

Thank you to all the open-source projects that made PEFT Studio possible:
- HuggingFace Transformers and PEFT
- PyTorch and the ML community
- Electron and React teams
- All contributors and testers

## 🐛 Known Limitations

- **GPU Support**: Currently optimized for NVIDIA GPUs with CUDA
- **Model Size**: Large models (>13B parameters) require significant VRAM
- **Training Speed**: Depends heavily on hardware capabilities
- **Cloud Integration**: Some cloud platforms require manual configuration

## 📬 Getting Help

- **🐛 Bug Reports**: [Open an issue](https://github.com/Ankesh-007/peft-studio/issues/new?template=bug_report.md)
- **💡 Feature Requests**: [Request a feature](https://github.com/Ankesh-007/peft-studio/issues/new?template=feature_request.md)
- **❓ Questions**: [Start a discussion](https://github.com/Ankesh-007/peft-studio/discussions)

## 🗺️ Roadmap

Planned features for future releases:
- Light theme support
- Advanced filtering and search
- Bulk operations for datasets and models
- Collaborative features
- Plugin system for extensions
- AI-powered configuration suggestions
- Multi-GPU and distributed training support

---

**⭐ If you find PEFT Studio useful, please consider giving it a star on GitHub!**

For the complete changelog, see [CHANGELOG.md](https://github.com/Ankesh-007/peft-studio/blob/main/CHANGELOG.md).
