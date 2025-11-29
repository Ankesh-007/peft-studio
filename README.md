# PEFT Studio

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
