# Build script for PEFT Studio (Windows PowerShell)
# Usage: .\scripts\build.ps1 [windows|mac|linux|all]

param(
    [string]$Platform = "all"
)

# Colors
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }
function Write-Info { Write-Host $args -ForegroundColor Cyan }

function Check-Prerequisites {
    Write-Success "`n=== Checking Prerequisites ==="
    
    # Check Node.js
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        Write-Error "Node.js is not installed"
        exit 1
    }
    
    # Check npm
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        Write-Error "npm is not installed"
        exit 1
    }
    
    # Check if node_modules exists
    if (-not (Test-Path "node_modules")) {
        Write-Warning "node_modules not found. Running npm install..."
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to install dependencies"
            exit 1
        }
    }
    
    Write-Success "Prerequisites check complete"
}

function Build-Frontend {
    Write-Success "`n=== Building Frontend ==="
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Frontend build failed"
        exit 1
    }
    Write-Success "Frontend build complete"
}

function Build-Installer {
    param([string]$Platform)
    
    Write-Success "`n=== Building $Platform Installer ==="
    
    switch ($Platform) {
        "windows" {
            npx electron-builder --win
        }
        "mac" {
            npx electron-builder --mac
        }
        "linux" {
            npx electron-builder --linux
        }
        "all" {
            npx electron-builder --win --mac --linux
        }
        default {
            Write-Error "Unknown platform: $Platform"
            Write-Warning "Valid platforms: windows, mac, linux, all"
            exit 1
        }
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "$Platform installer build failed"
        exit 1
    }
    
    Write-Success "$Platform installer build complete"
}

function Show-Outputs {
    Write-Success "`n=== Build Outputs ==="
    
    if (Test-Path "release") {
        Write-Info "`nGenerated installers:"
        Get-ChildItem "release" -File | ForEach-Object {
            $sizeMB = [math]::Round($_.Length / 1MB, 2)
            Write-Info "  - $($_.Name) ($sizeMB MB)"
        }
    } else {
        Write-Warning "No release directory found"
    }
}

# Main
Write-Success "======================================================================"
Write-Success "PEFT Studio Build Script"
Write-Success "======================================================================"

Check-Prerequisites
Build-Frontend
Build-Installer -Platform $Platform
Show-Outputs

Write-Success "`n=== Build Complete ==="
Write-Success "Installers are in the release\ directory"
