# PEFT Studio - Quick Start Guide

## 🎯 What's Been Built

### Phase 1: Complete ✅
- **Project Infrastructure**: Electron + React + TypeScript + Tailwind CSS
- **Design System**: Professional dark theme with custom color palette
- **Python Backend**: FastAPI server with SQLite database
- **IPC Communication**: Electron bridge for frontend-backend communication

### Phase 2: Complete ✅
- **Main Layout**: Sidebar navigation + top bar + collapsible right panel
- **Dashboard View**: 
  - Hero section with stats cards
  - Recent training runs list
  - Quick actions grid
  - Real-time charts (training loss, GPU utilization)
  - System resource monitoring
- **Navigation**: Smooth transitions between views
- **Theme System**: Dark mode with accent colors

### Phase 3: In Progress 🚧
- **Dataset Upload**: Drag-and-drop interface with progress tracking
- Dataset table viewer (next)
- Dataset validator & analyzer (next)
- Format configurator (next)

## 🎨 Design System

### Colors
- **Background**: #0a0a0a (primary), #111111 (secondary), #1a1a1a (tertiary)
- **Borders**: #2a2a2a
- **Accents**: 
  - Primary: #6366f1 (indigo)
  - Success: #10b981 (emerald)
  - Warning: #f59e0b (amber)
  - Error: #ef4444 (red)
  - Info: #3b82f6 (blue)

### Typography
- **Font**: Inter (UI), JetBrains Mono (code)
- **Sizes**: Display (32px), H1 (24px), H2 (20px), H3 (16px), Body (14px)

### Components
- **Cards**: Rounded corners (12px), subtle borders, hover effects
- **Buttons**: Primary, secondary, ghost variants
- **Inputs**: Focus states with accent color rings
- **Navigation**: Active state with left border accent

## 🚀 Running the Application

### Development Mode

1. **Start the development server:**
```bash
npm run dev
```
This starts Vite on http://localhost:5173

2. **In another terminal, start Electron:**
```bash
npm run electron:dev
```

The Electron window will open and load the React app.

### What You'll See

1. **Sidebar** (left):
   - Navigation menu with icons
   - System status indicators (GPU, RAM)
   - Settings and user profile

2. **Top Bar**:
   - Breadcrumb navigation
   - Global search (⌘K)
   - New Training button
   - Notifications
   - Theme toggle
   - Help panel toggle

3. **Dashboard** (main content):
   - Welcome message with greeting
   - 4 stat cards (Models, Training, Datasets, GPU Hours)
   - Recent training runs with progress bars
   - Quick action buttons
   - Training loss chart
   - System resources chart

4. **Right Panel** (collapsible):
   - Quick help
   - Keyboard shortcuts

## 📁 File Structure

```
src/
├── components/
│   ├── Layout.tsx          # Main layout wrapper
│   ├── Sidebar.tsx         # Left navigation sidebar
│   ├── TopBar.tsx          # Top action bar
│   ├── Dashboard.tsx       # Dashboard view
│   └── DatasetUpload.tsx   # Dataset upload component
├── lib/
│   └── utils.ts            # Utility functions
├── api/
│   └── client.ts           # API client for backend
├── App.tsx                 # Root component
├── main.tsx                # React entry point
└── index.css               # Global styles + Tailwind

electron/
├── main.js                 # Electron main process
└── preload.js              # IPC bridge

backend/
├── main.py                 # FastAPI server
├── config.py               # Configuration
├── database.py             # SQLAlchemy models
└── requirements.txt        # Python dependencies
```

## 🎯 Next Steps

### Immediate Tasks
1. **Dataset Management** (Phase 3):
   - Complete dataset table viewer
   - Add dataset validation and analysis
   - Build format configurator
   - Implement dataset editor

2. **Model Browser** (Phase 4):
   - HuggingFace model search
   - Model download manager
   - Local model library

3. **Training Configuration** (Phase 5):
   - PEFT method selector
   - LoRA configuration panel
   - Training hyperparameters
   - Training wizard

### Backend Integration
- Connect frontend components to FastAPI endpoints
- Implement WebSocket for real-time updates
- Add database operations
- File upload handling

### Testing
- Test Electron IPC communication
- Verify Python backend startup
- Test file upload functionality
- Validate chart rendering

## 🐛 Troubleshooting

### Electron window doesn't open
- Make sure Vite dev server is running first
- Check that port 5173 is not in use
- Look for errors in the terminal

### Python backend not starting
- Verify Python virtual environment is activated
- Check that all dependencies are installed
- Look for port conflicts (default: 8000)

### Styles not loading
- Clear browser cache
- Restart Vite dev server
- Check Tailwind configuration

## 📚 Resources

- **Electron Docs**: https://www.electronjs.org/docs
- **React Docs**: https://react.dev
- **Tailwind CSS**: https://tailwindcss.com
- **FastAPI**: https://fastapi.tiangolo.com
- **Recharts**: https://recharts.org

## 🎨 Design References

The UI is inspired by:
- **Linear**: Clean layouts and smooth animations
- **Vercel**: Color palette and typography
- **Weights & Biases**: Technical dashboards and charts
- **Raycast**: Command palette and shortcuts
- **Arc Browser**: Modern, polished interface
