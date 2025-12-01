# PEFT Studio

Professional desktop application for Parameter-Efficient Fine-Tuning (PEFT) of Large Language Models.

## ✨ Features

### Core Capabilities
- **Modern UI**: Professional dark theme with smooth animations and real-time updates
- **Dashboard**: Monitor training runs, system resources, and statistics at a glance
- **Dataset Management**: Upload, validate, and analyze training data with drag-and-drop support
- **Model Browser**: Search and download models from HuggingFace with integrated metadata
- **PEFT Methods**: Support for LoRA, QLoRA, Prefix Tuning, and more fine-tuning techniques
- **Training Monitor**: Real-time progress tracking with interactive charts and metrics
- **Inference Playground**: Test and compare fine-tuned models with live inference
- **Platform Integration**: Export models to HuggingFace, Ollama, and LM Studio
- **Command Palette**: Quick access to all features with keyboard shortcuts (⌘K / Ctrl+K)
- **Error Recovery**: Plain-language error messages with automatic fix suggestions

### Design System
- **Professional Dark Theme**: Deep black background (#0a0a0a) with indigo accents (#6366f1)
- **Typography**: Inter font for UI, JetBrains Mono for code
- **Responsive Layout**: Collapsible sidebar, top action bar, and contextual help panel
- **Smooth Animations**: 60fps transitions and micro-interactions
- **Accessibility**: Keyboard navigation, ARIA labels, and WCAG AA compliant colors

### User Experience
- **Keyboard Shortcuts**: Full keyboard navigation support
- **Real-time Updates**: Live system resource monitoring and training progress
- **Visual Feedback**: Hover states, loading indicators, and status notifications
- **Contextual Help**: Quick reference panel with shortcuts and documentation links

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- CUDA GPU (recommended)

### Installation

```bash
# Install dependencies
npm install

# Create Python environment
python -m venv peft_env
peft_env\Scripts\activate  # Windows
pip install -r backend/requirements.txt
```

### Development

```bash
# Terminal 1: Frontend
npm run dev

# Terminal 2: Electron
npm run electron:dev
```

### Build

```bash
npm run build
npm run electron:build
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
├── electron/              # Electron main process
│   ├── main.js           # Main process entry
│   └── preload.js        # IPC bridge
├── src/                  # React frontend
│   ├── components/       # UI components
│   ├── lib/             # Utilities
│   ├── api/             # API client
│   ├── hooks/           # Custom React hooks
│   ├── workers/         # Web workers for performance
│   └── App.tsx          # Root component
├── backend/             # Python FastAPI backend
│   ├── main.py          # FastAPI server
│   ├── services/        # Business logic services
│   ├── connectors/      # Platform connectors
│   ├── plugins/         # Plugin system
│   ├── tests/           # Backend tests
│   └── requirements.txt
├── docs/                # Documentation
│   ├── user-guide/      # User documentation
│   ├── developer-guide/ # Developer documentation
│   └── reference/       # API reference and troubleshooting
└── package.json
```

## 📊 Project Status

**Current Version**: 0.2.0-alpha

### Completed Features
- ✅ Infrastructure: Electron + React + TypeScript + FastAPI setup
- ✅ Design System: Dark theme, typography, spacing, animations
- ✅ Layout: Sidebar navigation, top bar, command palette
- ✅ Dashboard: Real-time charts, stats cards, training runs
- ✅ Dataset Upload: Drag-and-drop interface with progress tracking
- ✅ Training Monitor: Live progress tracking and metrics
- ✅ Inference Playground: Model testing interface
- ✅ Error Handling: Plain-language errors with auto-fix suggestions
- ✅ Platform Connections: HuggingFace, Ollama integration
- ✅ Configuration Management: Import/export training configs

### In Progress
- 🚧 Model Browser: HuggingFace search and download
- 🚧 Dataset Validation: Advanced format detection and validation
- 🚧 Training Configuration: PEFT method selection and tuning

### Documentation
- 📚 [User Guide](docs/user-guide/) - Getting started and feature guides
- 📚 [Developer Guide](docs/developer-guide/) - Architecture and API docs
- 📚 [Reference](docs/reference/) - Troubleshooting and FAQ

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

## 📝 License

ISC
