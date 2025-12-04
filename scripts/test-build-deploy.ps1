# Comprehensive Test, Build, and Deploy Script for PEFT Studio
# This script runs all tests, builds installers, and prepares for GitHub deployment

param(
    [switch]$SkipTests = $false,
    [switch]$SkipBuild = $false,
    [string]$Platform = "windows,linux",
    [switch]$PushToGitHub = $false,
    [string]$CommitMessage = "Build: Create installers for Windows and Linux"
)

# Colors
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Step { Write-Host "`n=== $args ===" -ForegroundColor Magenta }

$ErrorActionPreference = "Stop"
$script:TestsFailed = $false
$script:BuildFailed = $false

# Trap errors
trap {
    Write-Error "An error occurred: $_"
    Write-Error $_.ScriptStackTrace
    exit 1
}

function Test-Prerequisites {
    Write-Step "Checking Prerequisites"
    
    $missing = @()
    
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        $missing += "Node.js"
    }
    
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        $missing += "npm"
    }
    
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        $missing += "Python"
    }
    
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        $missing += "Git"
    }
    
    if ($missing.Count -gt 0) {
        Write-Error "Missing prerequisites: $($missing -join ', ')"
        Write-Info "Please install the missing tools and try again"
        exit 1
    }
    
    Write-Success "✓ All prerequisites found"
}

function Install-Dependencies {
    Write-Step "Installing Dependencies"
    
    try {
        Write-Info "Installing Node.js dependencies..."
        npm ci
        if ($LASTEXITCODE -ne 0) { throw "npm ci failed" }
        
        Write-Info "Installing Python dependencies..."
        Push-Location backend
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov hypothesis
        Pop-Location
        
        Write-Success "✓ Dependencies installed"
    }
    catch {
        Write-Error "Failed to install dependencies: $_"
        exit 1
    }
}

function Run-FrontendTests {
    Write-Step "Running Frontend Tests"
    
    try {
        Write-Info "Running unit tests..."
        npm run test:run
        
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "⚠ Some frontend tests failed"
            $script:TestsFailed = $true
            return $false
        }
        
        Write-Success "✓ Frontend tests passed"
        return $true
    }
    catch {
        Write-Error "Frontend tests encountered an error: $_"
        $script:TestsFailed = $true
        return $false
    }
}

function Run-BackendTests {
    Write-Step "Running Backend Tests"
    
    try {
        Push-Location backend
        
        Write-Info "Running Python tests..."
        python -m pytest tests/ -v --tb=short --maxfail=5
        
        $testResult = $LASTEXITCODE
        Pop-Location
        
        if ($testResult -ne 0) {
            Write-Warning "⚠ Some backend tests failed"
            $script:TestsFailed = $true
            return $false
        }
        
        Write-Success "✓ Backend tests passed"
        return $true
    }
    catch {
        Pop-Location
        Write-Error "Backend tests encountered an error: $_"
        $script:TestsFailed = $true
        return $false
    }
}

function Run-Linting {
    Write-Step "Running Code Quality Checks"
    
    try {
        Write-Info "Running ESLint..."
        npm run lint
        
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "⚠ Linting issues found (continuing anyway)"
        } else {
            Write-Success "✓ Linting passed"
        }
        
        Write-Info "Running TypeScript type check..."
        npm run type-check
        
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "⚠ Type check issues found (continuing anyway)"
        } else {
            Write-Success "✓ Type check passed"
        }
    }
    catch {
        Write-Warning "Code quality checks encountered issues (continuing anyway)"
    }
}

function Build-Frontend {
    Write-Step "Building Frontend"
    
    try {
        npm run build
        
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend build failed"
        }
        
        if (-not (Test-Path "dist")) {
            throw "Build output directory 'dist' not found"
        }
        
        Write-Success "✓ Frontend built successfully"
        return $true
    }
    catch {
        Write-Error "Frontend build failed: $_"
        $script:BuildFailed = $true
        return $false
    }
}

function Build-Installers {
    param([string]$Platforms)
    
    Write-Step "Building Installers"
    
    $platformList = $Platforms -split ','
    $success = $true
    
    foreach ($platform in $platformList) {
        $platform = $platform.Trim()
        
        try {
            Write-Info "Building $platform installer..."
            
            switch ($platform.ToLower()) {
                "windows" {
                    npx electron-builder --win --config
                }
                "linux" {
                    npx electron-builder --linux --config
                }
                "mac" {
                    npx electron-builder --mac --config
                }
                default {
                    Write-Warning "Unknown platform: $platform (skipping)"
                    continue
                }
            }
            
            if ($LASTEXITCODE -ne 0) {
                throw "$platform build failed"
            }
            
            Write-Success "✓ $platform installer built"
        }
        catch {
            Write-Error "$platform installer build failed: $_"
            $success = $false
            $script:BuildFailed = $true
        }
    }
    
    return $success
}

function Show-BuildArtifacts {
    Write-Step "Build Artifacts"
    
    if (Test-Path "release") {
        $files = Get-ChildItem "release" -File
        
        if ($files.Count -eq 0) {
            Write-Warning "No build artifacts found in release directory"
            return
        }
        
        Write-Info "`nGenerated installers:"
        foreach ($file in $files) {
            $sizeMB = [math]::Round($file.Length / 1MB, 2)
            Write-Success "  ✓ $($file.Name) ($sizeMB MB)"
        }
        
        # Calculate total size
        $totalSize = ($files | Measure-Object -Property Length -Sum).Sum
        $totalSizeMB = [math]::Round($totalSize / 1MB, 2)
        Write-Info "`nTotal size: $totalSizeMB MB"
    }
    else {
        Write-Warning "Release directory not found"
    }
}

function Push-ToGitHub {
    Write-Step "Pushing to GitHub"
    
    try {
        # Check if there are changes
        $status = git status --porcelain
        
        if ([string]::IsNullOrWhiteSpace($status)) {
            Write-Info "No changes to commit"
        }
        else {
            Write-Info "Staging changes..."
            git add .
            
            Write-Info "Committing changes..."
            git commit -m $CommitMessage
            
            Write-Info "Pushing to GitHub..."
            git push
            
            if ($LASTEXITCODE -ne 0) {
                throw "Git push failed"
            }
            
            Write-Success "✓ Changes pushed to GitHub"
        }
        
        # Check if we should create a release
        $currentBranch = git rev-parse --abbrev-ref HEAD
        Write-Info "`nCurrent branch: $currentBranch"
        Write-Info "To create a release, push a tag:"
        Write-Info "  git tag v1.0.0"
        Write-Info "  git push origin v1.0.0"
        Write-Info "`nThis will trigger the GitHub Actions workflow to build and publish installers"
    }
    catch {
        Write-Error "Failed to push to GitHub: $_"
        exit 1
    }
}

function Show-Summary {
    Write-Step "Summary"
    
    $allPassed = -not $script:TestsFailed -and -not $script:BuildFailed
    
    if ($allPassed) {
        Write-Success "`n✓ All operations completed successfully!"
    }
    else {
        Write-Warning "`n⚠ Some operations had issues:"
        if ($script:TestsFailed) {
            Write-Warning "  - Tests failed or had warnings"
        }
        if ($script:BuildFailed) {
            Write-Warning "  - Build failed or had errors"
        }
    }
    
    Write-Info "`nNext steps:"
    if (Test-Path "release") {
        Write-Info "  1. Test the installers in the 'release' directory"
        Write-Info "  2. Review the build artifacts"
    }
    if ($PushToGitHub) {
        Write-Info "  3. Create a release tag to trigger automated builds"
        Write-Info "     git tag v1.0.0 && git push origin v1.0.0"
    }
    else {
        Write-Info "  3. Run with -PushToGitHub to push changes"
    }
}

# Main execution
Write-Success "======================================================================"
Write-Success "PEFT Studio - Test, Build, and Deploy"
Write-Success "======================================================================"

Test-Prerequisites
Install-Dependencies

# Run tests
if (-not $SkipTests) {
    Run-Linting
    $frontendPassed = Run-FrontendTests
    $backendPassed = Run-BackendTests
    
    if (-not $frontendPassed -or -not $backendPassed) {
        Write-Warning "`n⚠ Tests failed. Continue with build? (Y/N)"
        $response = Read-Host
        if ($response -ne 'Y' -and $response -ne 'y') {
            Write-Info "Build cancelled by user"
            exit 1
        }
    }
}
else {
    Write-Warning "Skipping tests (as requested)"
}

# Build
if (-not $SkipBuild) {
    $buildSuccess = Build-Frontend
    
    if ($buildSuccess) {
        Build-Installers -Platforms $Platform
        Show-BuildArtifacts
    }
    else {
        Write-Error "Cannot build installers - frontend build failed"
        exit 1
    }
}
else {
    Write-Warning "Skipping build (as requested)"
}

# Push to GitHub
if ($PushToGitHub) {
    Push-ToGitHub
}

Show-Summary

Write-Success "`n======================================================================"
Write-Success "Process Complete"
Write-Success "======================================================================"
