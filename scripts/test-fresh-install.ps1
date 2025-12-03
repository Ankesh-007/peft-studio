#!/usr/bin/env pwsh
# Test Fresh Installation Script
# This script tests the installation process by following the documented steps

param(
    [string]$TestDir = "$env:TEMP\peft-studio-install-test",
    [switch]$KeepTestDir = $false
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PEFT Studio Fresh Installation Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to log messages
function Write-Step {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Error-Step {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Yellow
}

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Cyan
Write-Host ""

# Check Node.js
try {
    $nodeVersion = node --version
    if ($nodeVersion -match "v(\d+)\.") {
        $majorVersion = [int]$matches[1]
        if ($majorVersion -ge 18) {
            Write-Step "Node.js $nodeVersion (>= 18 required)"
        } else {
            Write-Error-Step "Node.js version $nodeVersion is too old. Version 18+ required."
            exit 1
        }
    }
} catch {
    Write-Error-Step "Node.js not found. Please install Node.js 18+ from https://nodejs.org/"
    exit 1
}

# Check Python
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $majorVersion = [int]$matches[1]
        $minorVersion = [int]$matches[2]
        if ($majorVersion -eq 3 -and $minorVersion -ge 10) {
            Write-Step "Python $pythonVersion (>= 3.10 required)"
        } else {
            Write-Error-Step "Python version $pythonVersion is too old. Version 3.10+ required."
            exit 1
        }
    }
} catch {
    Write-Error-Step "Python not found. Please install Python 3.10+ from https://www.python.org/"
    exit 1
}

# Check npm
try {
    $npmVersion = npm --version
    Write-Step "npm $npmVersion"
} catch {
    Write-Error-Step "npm not found. Please install Node.js which includes npm."
    exit 1
}

# Check pip
try {
    $pipVersion = pip --version
    Write-Step "pip installed"
} catch {
    Write-Error-Step "pip not found. Please ensure Python is installed correctly."
    exit 1
}

Write-Host ""
Write-Host "All prerequisites met!" -ForegroundColor Green
Write-Host ""

# Create test directory
Write-Host "Setting up test environment..." -ForegroundColor Cyan
Write-Host ""

if (Test-Path $TestDir) {
    Write-Info "Removing existing test directory..."
    Remove-Item -Path $TestDir -Recurse -Force
}

New-Item -ItemType Directory -Path $TestDir -Force | Out-Null
Write-Step "Created test directory: $TestDir"

# Get current repository path
$RepoPath = (Get-Location).Path
Write-Info "Current repository: $RepoPath"
Write-Host ""

# Clone repository to test location
Write-Host "Cloning repository..." -ForegroundColor Cyan
Write-Host ""

try {
    # Copy repository to test location (simulating git clone)
    Write-Info "Copying repository files to test location..."
    
    # Copy all files except node_modules, dist, build, and other generated directories
    $excludeDirs = @(
        "node_modules",
        "dist",
        "build",
        "release",
        ".git",
        "peft_env",
        "backend/__pycache__",
        "backend/.pytest_cache",
        ".hypothesis"
    )
    
    Get-ChildItem -Path $RepoPath -Exclude $excludeDirs | ForEach-Object {
        $dest = Join-Path $TestDir $_.Name
        if ($_.PSIsContainer) {
            # Skip excluded directories
            if ($excludeDirs -contains $_.Name) {
                return
            }
            Copy-Item -Path $_.FullName -Destination $dest -Recurse -Force
        } else {
            Copy-Item -Path $_.FullName -Destination $dest -Force
        }
    }
    
    Write-Step "Repository copied to test location"
} catch {
    Write-Error-Step "Failed to copy repository: $_"
    exit 1
}

# Change to test directory
Set-Location $TestDir
Write-Host ""

# Install frontend dependencies
Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
Write-Host ""

try {
    $installOutput = npm install 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Step "Frontend dependencies installed successfully"
    } else {
        Write-Error-Step "npm install failed"
        Write-Host $installOutput
        exit 1
    }
} catch {
    Write-Error-Step "Failed to install frontend dependencies: $_"
    exit 1
}

Write-Host ""

# Create Python virtual environment
Write-Host "Creating Python virtual environment..." -ForegroundColor Cyan
Write-Host ""

try {
    python -m venv peft_env
    Write-Step "Python virtual environment created"
} catch {
    Write-Error-Step "Failed to create virtual environment: $_"
    exit 1
}

# Activate virtual environment
Write-Info "Activating virtual environment..."
$venvActivate = Join-Path $TestDir "peft_env\Scripts\Activate.ps1"

if (Test-Path $venvActivate) {
    & $venvActivate
    Write-Step "Virtual environment activated"
} else {
    Write-Error-Step "Virtual environment activation script not found"
    exit 1
}

Write-Host ""

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
Write-Host ""

try {
    $pipInstall = pip install -r backend/requirements.txt 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Step "Python dependencies installed successfully"
    } else {
        Write-Error-Step "pip install failed"
        Write-Host $pipInstall
        exit 1
    }
} catch {
    Write-Error-Step "Failed to install Python dependencies: $_"
    exit 1
}

Write-Host ""

# Verify installation
Write-Host "Verifying installation..." -ForegroundColor Cyan
Write-Host ""

# Check if node_modules exists
if (Test-Path "node_modules") {
    Write-Step "node_modules directory exists"
} else {
    Write-Error-Step "node_modules directory not found"
    exit 1
}

# Check if key dependencies are installed
$keyDeps = @("react", "electron", "vite")
foreach ($dep in $keyDeps) {
    if (Test-Path "node_modules/$dep") {
        Write-Step "$dep installed"
    } else {
        Write-Error-Step "$dep not found in node_modules"
        exit 1
    }
}

# Check if Python packages are installed
Write-Info "Checking Python packages..."
$pythonPackages = @("fastapi", "torch", "transformers")
foreach ($pkg in $pythonPackages) {
    try {
        $checkPkg = pip show $pkg 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Step "$pkg installed"
        } else {
            Write-Error-Step "$pkg not installed"
            exit 1
        }
    } catch {
        Write-Error-Step "Failed to check ${pkg}: $($_.Exception.Message)"
        exit 1
    }
}

Write-Host ""

# Test build process
Write-Host "Testing build process..." -ForegroundColor Cyan
Write-Host ""

try {
    Write-Info "Running npm run build..."
    $buildOutput = npm run build 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Step "Build completed successfully"
    } else {
        Write-Error-Step "Build failed"
        Write-Host $buildOutput
        exit 1
    }
} catch {
    Write-Error-Step "Failed to run build: $_"
    exit 1
}

# Check if dist directory was created
if (Test-Path "dist") {
    Write-Step "dist directory created"
    
    # Check for key build artifacts
    if (Test-Path "dist/index.html") {
        Write-Step "index.html found in dist"
    } else {
        Write-Error-Step "index.html not found in dist"
        exit 1
    }
} else {
    Write-Error-Step "dist directory not created"
    exit 1
}

Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installation Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[OK] Prerequisites verified" -ForegroundColor Green
Write-Host "[OK] Repository cloned successfully" -ForegroundColor Green
Write-Host "[OK] Frontend dependencies installed" -ForegroundColor Green
Write-Host "[OK] Python virtual environment created" -ForegroundColor Green
Write-Host "[OK] Python dependencies installed" -ForegroundColor Green
Write-Host "[OK] Build process completed" -ForegroundColor Green
Write-Host ""
Write-Host "All installation steps completed successfully!" -ForegroundColor Green
Write-Host ""

# Cleanup
if (-not $KeepTestDir) {
    Write-Info "Cleaning up test directory..."
    Set-Location $RepoPath
    Remove-Item -Path $TestDir -Recurse -Force
    Write-Step "Test directory removed"
} else {
    Write-Info "Test directory preserved at: $TestDir"
}

Write-Host ""
Write-Host "Fresh installation test PASSED" -ForegroundColor Green
Write-Host ""

exit 0
