# PEFT Studio

A professional desktop application for Parameter-Efficient Fine-Tuning (PEFT) of Large Language Models with full customization, platform integration, and local execution capabilities.

## ✨ Features

- **🎨 Modern UI**: Professional design with dark theme, inspired by Linear, Vercel, and modern SaaS dashboards
- **📊 Dashboard**: Real-time monitoring of training runs, system resources, and statistics
- **📁 Dataset Management**: Upload, format, validate, and analyze training datasets
- **🤖 Model Browser**: Search and download models from HuggingFace Hub
- **⚡ PEFT Methods**: Support for LoRA, QLoRA, Prefix Tuning, and more
- **📈 Training Monitor**: Real-time training progress with interactive charts
- **🧪 Inference Playground**: Test your fine-tuned models
- **🚀 Platform Integration**: Export to HuggingFace, Ollama, LM Studio

## 🎯 Design Philosophy

PEFT Studio follows a professional, modern design system:
- **Color Palette**: Deep blacks (#0a0a0a) with indigo accents (#6366f1)
- **Typography**: Inter for UI, JetBrains Mono for code
- **Spacing**: 4px base unit system
- **Components**: Card-based layouts with smooth transitions

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.10+
- CUDA-capable GPU (recommended)

### Installation

1. **Install Node.js dependencies:**
```bash
npm install
```

2. **Create Python virtual environment:**
```bash
python -m venv peft_env
```

3. **Activate virtual environment:**
- Windows: `peft_env\Scripts\activate`
- Linux/Mac: `source peft_env/bin/activate`

4. **Install Python dependencies:**
```bash
pip install -r backend/requirements.txt
```

### Development

**Option 1: Run both servers together (recommended):**
```bash
npm start
```

**Option 2: Run separately:**

Terminal 1 - Frontend:
```bash
npm run dev
```

Terminal 2 - Electron:
```bash
npm run electron:dev
```

Terminal 3 - Backend (optional, if not auto-started):
```bash
cd backend
python main.py
```

### Build

Build for production:
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

## 📝 License

ISC
