# Quick Start Script for PEFT Studio
# This script helps new users get started quickly

Write-Host "🚀 PEFT Studio Quick Start" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check Node.js
Write-Host "Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "  ✅ Node.js $nodeVersion installed" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Node.js not found. Please install Node.js 18+ from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "  ✅ $pythonVersion installed" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Python not found. Please install Python 3.9+ from https://python.org/" -ForegroundColor Red
    exit 1
}

# Install frontend dependencies
Write-Host ""
Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Failed to install frontend dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "  ✅ Frontend dependencies installed" -ForegroundColor Green

# Install backend dependencies
Write-Host ""
Write-Host "Installing backend dependencies..." -ForegroundColor Yellow
Set-Location backend
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Failed to install backend dependencies" -ForegroundColor Red
    Set-Location ..
    exit 1
}
Set-Location ..
Write-Host "  ✅ Backend dependencies installed" -ForegroundColor Green

# Create .env file if it doesn't exist
Write-Host ""
Write-Host "Checking environment configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "  Creating .env file..." -ForegroundColor Yellow
    @"
# PEFT Studio Environment Configuration
# Copy this file to .env and fill in your values

# API Keys (optional - add as needed)
# HUGGINGFACE_TOKEN=your_token_here
# WANDB_API_KEY=your_key_here
# HONEYHIVE_API_KEY=your_key_here

# Database
DATABASE_URL=sqlite:///./peft_studio.db

# Server
BACKEND_PORT=8000
FRONTEND_PORT=5173

# Environment
NODE_ENV=development
"@ | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "  ✅ Created .env file - please configure your API keys" -ForegroundColor Green
} else {
    Write-Host "  ✅ .env file already exists" -ForegroundColor Green
}

# Success message
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To start PEFT Studio:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Terminal 1 (Frontend):" -ForegroundColor Yellow
Write-Host "    npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "  Terminal 2 (Backend):" -ForegroundColor Yellow
Write-Host "    cd backend" -ForegroundColor White
Write-Host "    python main.py" -ForegroundColor White
Write-Host ""
Write-Host "Then open http://localhost:5173 in your browser" -ForegroundColor Cyan
Write-Host ""
Write-Host "For more information, see:" -ForegroundColor Cyan
Write-Host "  - README.md" -ForegroundColor White
Write-Host "  - docs/user-guide/quick-start.md" -ForegroundColor White
Write-Host "  - CONTRIBUTING.md" -ForegroundColor White
