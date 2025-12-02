#!/usr/bin/env pwsh
# PEFT Studio - Publication Readiness Verification Script
# This script verifies that the repository is ready for public release

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PEFT Studio Publication Readiness Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allPassed = $true

# Function to check if a file exists
function Test-FileExists {
    param($path, $description)
    if (Test-Path $path) {
        Write-Host "✓ $description" -ForegroundColor Green
        return $true
    } else {
        Write-Host "✗ $description - MISSING" -ForegroundColor Red
        return $false
    }
}

# Function to check if a command succeeds
function Test-Command {
    param($command, $description)
    try {
        $output = Invoke-Expression $command 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ $description" -ForegroundColor Green
            return $true
        } else {
            Write-Host "✗ $description - FAILED" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "✗ $description - ERROR: $_" -ForegroundColor Red
        return $false
    }
}

Write-Host "1. Checking Required Documentation Files..." -ForegroundColor Yellow
Write-Host ""

$allPassed = (Test-FileExists "README.md" "README.md exists") -and $allPassed
$allPassed = (Test-FileExists "CONTRIBUTING.md" "CONTRIBUTING.md exists") -and $allPassed
$allPassed = (Test-FileExists "CODE_OF_CONDUCT.md" "CODE_OF_CONDUCT.md exists") -and $allPassed
$allPassed = (Test-FileExists "SECURITY.md" "SECURITY.md exists") -and $allPassed
$allPassed = (Test-FileExists "LICENSE" "LICENSE exists") -and $allPassed
$allPassed = (Test-FileExists "CHANGELOG.md" "CHANGELOG.md exists") -and $allPassed

Write-Host ""
Write-Host "2. Checking GitHub Templates..." -ForegroundColor Yellow
Write-Host ""

$allPassed = (Test-FileExists ".github/ISSUE_TEMPLATE/bug_report.md" "Bug report template exists") -and $allPassed
$allPassed = (Test-FileExists ".github/ISSUE_TEMPLATE/feature_request.md" "Feature request template exists") -and $allPassed
$allPassed = (Test-FileExists ".github/ISSUE_TEMPLATE/question.md" "Question template exists") -and $allPassed
$allPassed = (Test-FileExists ".github/pull_request_template.md" "Pull request template exists") -and $allPassed

Write-Host ""
Write-Host "3. Checking CI/CD Workflows..." -ForegroundColor Yellow
Write-Host ""

$allPassed = (Test-FileExists ".github/workflows/ci.yml" "CI workflow exists") -and $allPassed
$allPassed = (Test-FileExists ".github/workflows/security.yml" "Security workflow exists") -and $allPassed

Write-Host ""
Write-Host "4. Checking Git Configuration..." -ForegroundColor Yellow
Write-Host ""

# Check if git remote is configured
$remoteUrl = git remote get-url origin 2>&1
if ($remoteUrl -match "github.com/Ankesh-007/peft-studio") {
    Write-Host "✓ Git remote configured correctly" -ForegroundColor Green
} else {
    Write-Host "✗ Git remote not configured correctly" -ForegroundColor Red
    $allPassed = $false
}

# Check if v1.0.0 tag exists
$tagExists = git tag -l "v1.0.0" 2>&1
if ($tagExists -eq "v1.0.0") {
    Write-Host "✓ Version tag v1.0.0 exists" -ForegroundColor Green
} else {
    Write-Host "✗ Version tag v1.0.0 missing" -ForegroundColor Red
    $allPassed = $false
}

# Check if on main branch
$currentBranch = git branch --show-current 2>&1
if ($currentBranch -eq "main") {
    Write-Host "✓ On main branch" -ForegroundColor Green
} else {
    Write-Host "⚠ Not on main branch (current: $currentBranch)" -ForegroundColor Yellow
}

# Check if there are uncommitted changes
$status = git status --porcelain 2>&1
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "✓ No uncommitted changes" -ForegroundColor Green
} else {
    Write-Host "⚠ Uncommitted changes detected" -ForegroundColor Yellow
    Write-Host "  Consider committing or stashing changes before publication" -ForegroundColor Gray
}

Write-Host ""
Write-Host "5. Checking Package Configuration..." -ForegroundColor Yellow
Write-Host ""

# Check package.json
if (Test-Path "package.json") {
    $packageJson = Get-Content "package.json" | ConvertFrom-Json
    
    if ($packageJson.repository.url -match "github.com/Ankesh-007/peft-studio") {
        Write-Host "✓ package.json repository URL correct" -ForegroundColor Green
    } else {
        Write-Host "✗ package.json repository URL incorrect" -ForegroundColor Red
        $allPassed = $false
    }
    
    if ($packageJson.license -eq "MIT") {
        Write-Host "✓ package.json license set to MIT" -ForegroundColor Green
    } else {
        Write-Host "✗ package.json license not set to MIT" -ForegroundColor Red
        $allPassed = $false
    }
    
    if ($packageJson.keywords -and $packageJson.keywords.Count -gt 0) {
        Write-Host "✓ package.json has keywords" -ForegroundColor Green
    } else {
        Write-Host "⚠ package.json missing keywords" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "6. Checking Security..." -ForegroundColor Yellow
Write-Host ""

# Check for .env files
$envFiles = Get-ChildItem -Path . -Filter ".env*" -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne ".env.example" }
if ($envFiles.Count -eq 0) {
    Write-Host "✓ No .env files found" -ForegroundColor Green
} else {
    Write-Host "✗ .env files found - REMOVE BEFORE PUBLICATION" -ForegroundColor Red
    $envFiles | ForEach-Object { Write-Host "  - $($_.FullName)" -ForegroundColor Red }
    $allPassed = $false
}

# Check for database files that are NOT in .gitignore
$dbFiles = @(Get-ChildItem -Path . -Filter "*.db" -Recurse -File -ErrorAction SilentlyContinue)
$sqliteFiles = @(Get-ChildItem -Path . -Filter "*.sqlite*" -Recurse -File -ErrorAction SilentlyContinue)
$allDbFiles = $dbFiles + $sqliteFiles
$trackedDbFiles = @()
foreach ($file in $allDbFiles) {
    $relativePath = $file.FullName.Replace((Get-Location).Path + "\", "").Replace("\", "/")
    $checkIgnore = git check-ignore $relativePath 2>&1
    if ($LASTEXITCODE -ne 0) {
        $trackedDbFiles += $file
    }
}
if ($trackedDbFiles.Count -eq 0) {
    Write-Host "✓ No tracked database files found" -ForegroundColor Green
} else {
    Write-Host "✗ Tracked database files found - REMOVE BEFORE PUBLICATION" -ForegroundColor Red
    $trackedDbFiles | ForEach-Object { Write-Host "  - $($_.FullName)" -ForegroundColor Red }
    $allPassed = $false
}

Write-Host ""
Write-Host "7. Checking Build System..." -ForegroundColor Yellow
Write-Host ""

# Check if node_modules exists
if (Test-Path "node_modules") {
    Write-Host "✓ node_modules directory exists" -ForegroundColor Green
} else {
    Write-Host "⚠ node_modules not found - run 'npm install'" -ForegroundColor Yellow
}

# Check if backend dependencies are installed
if ((Test-Path "backend/venv") -or (Test-Path "backend/.venv")) {
    Write-Host "✓ Python virtual environment exists" -ForegroundColor Green
} else {
    Write-Host "⚠ Python virtual environment not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

if ($allPassed) {
    Write-Host "✓ ALL CHECKS PASSED - READY FOR PUBLICATION" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Review PUBLICATION_GUIDE.md for detailed instructions" -ForegroundColor White
    Write-Host "2. Make repository public on GitHub" -ForegroundColor White
    Write-Host "3. Create release v1.0.0" -ForegroundColor White
    Write-Host "4. Verify public access" -ForegroundColor White
    Write-Host "5. Monitor initial feedback" -ForegroundColor White
    exit 0
} else {
    Write-Host "✗ SOME CHECKS FAILED - FIX ISSUES BEFORE PUBLICATION" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please address the issues above before making the repository public." -ForegroundColor Yellow
    exit 1
}
