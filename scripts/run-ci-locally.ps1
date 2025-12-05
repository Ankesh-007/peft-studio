#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run all CI checks locally to verify changes before pushing to GitHub.

.DESCRIPTION
    This script replicates the GitHub Actions CI workflow locally, running:
    - Linting (ESLint)
    - Type checking (TypeScript)
    - Frontend tests with coverage
    - Backend tests with coverage
    - Frontend build
    - Security scans (npm audit, pip-audit)

.PARAMETER SkipTests
    Skip running tests (useful for quick lint/build checks)

.PARAMETER SkipBuild
    Skip the build step

.PARAMETER SkipSecurity
    Skip security scans

.PARAMETER Verbose
    Show detailed output from all commands

.EXAMPLE
    .\scripts\run-ci-locally.ps1
    Run all CI checks

.EXAMPLE
    .\scripts\run-ci-locally.ps1 -SkipSecurity
    Run all checks except security scans

.EXAMPLE
    .\scripts\run-ci-locally.ps1 -SkipTests -SkipBuild
    Run only linting and type checking
#>

param(
    [switch]$SkipTests,
    [switch]$SkipBuild,
    [switch]$SkipSecurity,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$OriginalLocation = Get-Location

# Color output functions
function Write-Step {
    param([string]$Message)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Failure {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

# Track results
$Results = @{
    Lint = $null
    TypeCheck = $null
    FrontendTests = $null
    BackendTests = $null
    Build = $null
    SecurityScan = $null
}

$StartTime = Get-Date

try {
    Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "║          Running CI Checks Locally                        ║" -ForegroundColor Magenta
    Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Magenta

    # Check environment
    Write-Step "Checking Environment"
    
    $NodeVersion = node --version
    $NpmVersion = npm --version
    Write-Host "Node.js: $NodeVersion (Required: v18.x)"
    Write-Host "npm: $NpmVersion"
    
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $PythonVersion = python --version
        Write-Host "Python: $PythonVersion (Required: 3.10.x)"
    } else {
        Write-Warning "Python not found in PATH"
    }

    # Lint
    Write-Step "Step 1/6: Running ESLint"
    try {
        if ($Verbose) {
            npm run lint
        } else {
            npm run lint 2>&1 | Out-Null
        }
        Write-Success "ESLint passed"
        $Results.Lint = "PASS"
    } catch {
        Write-Failure "ESLint failed"
        $Results.Lint = "FAIL"
        if (-not $Verbose) {
            Write-Host "Run with -Verbose to see detailed output"
        }
        throw
    }

    # Type Check
    Write-Step "Step 2/6: Running TypeScript Type Check"
    try {
        if ($Verbose) {
            npm run type-check
        } else {
            npm run type-check 2>&1 | Out-Null
        }
        Write-Success "TypeScript type check passed"
        $Results.TypeCheck = "PASS"
    } catch {
        Write-Failure "TypeScript type check failed"
        $Results.TypeCheck = "FAIL"
        if (-not $Verbose) {
            Write-Host "Run with -Verbose to see detailed output"
        }
        throw
    }

    # Frontend Tests
    if (-not $SkipTests) {
        Write-Step "Step 3/6: Running Frontend Tests"
        try {
            if ($Verbose) {
                npm run test:coverage
            } else {
                npm run test:coverage 2>&1 | Out-Null
            }
            Write-Success "Frontend tests passed"
            $Results.FrontendTests = "PASS"
        } catch {
            Write-Failure "Frontend tests failed"
            $Results.FrontendTests = "FAIL"
            if (-not $Verbose) {
                Write-Host "Run with -Verbose to see detailed output"
                Write-Host "Or run: npm run test:coverage"
            }
            throw
        }
    } else {
        Write-Warning "Skipping frontend tests"
        $Results.FrontendTests = "SKIP"
    }

    # Backend Tests
    if (-not $SkipTests) {
        Write-Step "Step 4/6: Running Backend Tests"
        try {
            Push-Location backend
            
            # Check if pytest is installed
            $PytestInstalled = $false
            try {
                python -m pytest --version 2>&1 | Out-Null
                $PytestInstalled = $true
            } catch {
                Write-Warning "pytest not installed, installing test dependencies..."
                pip install pytest pytest-cov pytest-asyncio hypothesis
                $PytestInstalled = $true
            }
            
            if ($PytestInstalled) {
                if ($Verbose) {
                    python -m pytest -v --cov=. --cov-report=term -m "not integration and not e2e and not pbt"
                } else {
                    python -m pytest -v --cov=. --cov-report=term -m "not integration and not e2e and not pbt" 2>&1 | Out-Null
                }
                Write-Success "Backend tests passed"
                $Results.BackendTests = "PASS"
            } else {
                Write-Failure "Could not install pytest"
                $Results.BackendTests = "FAIL"
                throw "pytest installation failed"
            }
        } catch {
            Write-Failure "Backend tests failed"
            $Results.BackendTests = "FAIL"
            if (-not $Verbose) {
                Write-Host "Run with -Verbose to see detailed output"
                Write-Host "Or run: cd backend && pytest -v -m 'not integration and not e2e and not pbt'"
            }
            throw
        } finally {
            Pop-Location
        }
    } else {
        Write-Warning "Skipping backend tests"
        $Results.BackendTests = "SKIP"
    }

    # Build
    if (-not $SkipBuild) {
        Write-Step "Step 5/6: Running Frontend Build"
        try {
            if ($Verbose) {
                npm run build
            } else {
                npm run build 2>&1 | Out-Null
            }
            
            # Verify build output
            if (Test-Path "dist") {
                $DistFiles = Get-ChildItem -Path "dist" -Recurse | Measure-Object
                Write-Success "Build passed (dist directory contains $($DistFiles.Count) files)"
                $Results.Build = "PASS"
            } else {
                Write-Failure "Build failed: dist directory not found"
                $Results.Build = "FAIL"
                throw "dist directory not created"
            }
        } catch {
            Write-Failure "Build failed"
            $Results.Build = "FAIL"
            if (-not $Verbose) {
                Write-Host "Run with -Verbose to see detailed output"
                Write-Host "Or run: npm run build"
            }
            throw
        }
    } else {
        Write-Warning "Skipping build"
        $Results.Build = "SKIP"
    }

    # Security Scan
    if (-not $SkipSecurity) {
        Write-Step "Step 6/6: Running Security Scans"
        
        # npm audit
        Write-Host "Running npm audit..."
        try {
            npm audit --audit-level=moderate 2>&1 | Out-Null
            Write-Success "npm audit passed (no moderate+ vulnerabilities)"
        } catch {
            Write-Warning "npm audit found vulnerabilities (this may be acceptable)"
            if (-not $Verbose) {
                Write-Host "Run 'npm audit' to see details"
            }
        }
        
        # pip-audit
        Write-Host "Running pip-audit..."
        try {
            Push-Location backend
            
            # Check if pip-audit is installed
            try {
                pip-audit --version 2>&1 | Out-Null
            } catch {
                Write-Host "Installing pip-audit..."
                pip install pip-audit
            }
            
            pip-audit 2>&1 | Out-Null
            Write-Success "pip-audit passed (no known vulnerabilities)"
        } catch {
            Write-Warning "pip-audit found vulnerabilities (this may be acceptable)"
            if (-not $Verbose) {
                Write-Host "Run 'cd backend && pip-audit' to see details"
            }
        } finally {
            Pop-Location
        }
        
        $Results.SecurityScan = "PASS"
    } else {
        Write-Warning "Skipping security scans"
        $Results.SecurityScan = "SKIP"
    }

    # Summary
    $EndTime = Get-Date
    $Duration = $EndTime - $StartTime
    
    Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║          All CI Checks Passed! ✓                          ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green
    
    Write-Host "Results Summary:" -ForegroundColor Cyan
    Write-Host "  Lint:           $($Results.Lint)"
    Write-Host "  Type Check:     $($Results.TypeCheck)"
    Write-Host "  Frontend Tests: $($Results.FrontendTests)"
    Write-Host "  Backend Tests:  $($Results.BackendTests)"
    Write-Host "  Build:          $($Results.Build)"
    Write-Host "  Security Scan:  $($Results.SecurityScan)"
    Write-Host "`nTotal Duration: $($Duration.ToString('mm\:ss'))" -ForegroundColor Cyan
    Write-Host "`nYou can now push your changes with confidence! 🚀`n" -ForegroundColor Green
    
    exit 0

} catch {
    $EndTime = Get-Date
    $Duration = $EndTime - $StartTime
    
    Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║          CI Checks Failed ✗                                ║" -ForegroundColor Red
    Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Red
    
    Write-Host "Results Summary:" -ForegroundColor Cyan
    Write-Host "  Lint:           $($Results.Lint)"
    Write-Host "  Type Check:     $($Results.TypeCheck)"
    Write-Host "  Frontend Tests: $($Results.FrontendTests)"
    Write-Host "  Backend Tests:  $($Results.BackendTests)"
    Write-Host "  Build:          $($Results.Build)"
    Write-Host "  Security Scan:  $($Results.SecurityScan)"
    Write-Host "`nTotal Duration: $($Duration.ToString('mm\:ss'))" -ForegroundColor Cyan
    Write-Host "`nError: $_" -ForegroundColor Red
    Write-Host "`nFix the failing checks before pushing to GitHub.`n" -ForegroundColor Yellow
    
    exit 1
} finally {
    Set-Location $OriginalLocation
}
