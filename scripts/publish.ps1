#!/usr/bin/env pwsh
# Publish Verification Script for Windows (PowerShell)
# Runs all pre-publication checks and generates a verification report

param(
    [switch]$Verbose = $false,
    [switch]$SkipTests = $false,
    [switch]$SkipBuild = $false
)

$ErrorActionPreference = "Stop"
$script:ChecksPassed = 0
$script:ChecksFailed = 0
$script:ChecksWarning = 0
$script:StartTime = Get-Date

# Color output functions
function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
    $script:ChecksPassed++
}

function Write-Failure {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
    $script:ChecksFailed++
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
    $script:ChecksWarning++
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Cyan
}

function Write-Section {
    param([string]$Title)
    Write-Host "`n========================================" -ForegroundColor Magenta
    Write-Host " $Title" -ForegroundColor Magenta
    Write-Host "========================================`n" -ForegroundColor Magenta
}

function Run-Check {
    param(
        [string]$Name,
        [scriptblock]$Check
    )
    
    Write-Host "`nRunning: $Name" -ForegroundColor White
    try {
        $result = & $Check
        if ($result) {
            Write-Success $Name
            return $true
        }
        else {
            Write-Failure $Name
            return $false
        }
    }
    catch {
        Write-Failure "$Name - Error: $_"
        return $false
    }
}

Write-Section "PEFT Studio Publish Verification"
Write-Info "Starting comprehensive pre-publication checks..."
Write-Info "Started at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# Check 1: Security Scan
Write-Section "1. Security Verification"

$securityCheck = Run-Check "Security Scan" {
    if (Test-Path "scripts/security-scan.ps1") {
        $result = & "scripts/security-scan.ps1" -Verbose:$Verbose
        return $LASTEXITCODE -eq 0
    }
    else {
        Write-Warning-Custom "Security scan script not found"
        return $true
    }
}

# Check 2: Required Files
Write-Section "2. Required Files Check"

$requiredFiles = @(
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "CHANGELOG.md",
    ".gitignore",
    "package.json",
    "package-lock.json"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Success "Found: $file"
    }
    else {
        Write-Failure "Missing: $file"
    }
}

# Check 3: GitHub Templates
Write-Section "3. GitHub Templates Check"

$githubTemplates = @(
    ".github/ISSUE_TEMPLATE/bug_report.md",
    ".github/ISSUE_TEMPLATE/feature_request.md",
    ".github/ISSUE_TEMPLATE/question.md",
    ".github/pull_request_template.md",
    ".github/workflows/ci.yml",
    ".github/workflows/security.yml"
)

foreach ($template in $githubTemplates) {
    if (Test-Path $template) {
        Write-Success "Found: $template"
    }
    else {
        Write-Failure "Missing: $template"
    }
}

# Check 4: Package.json Metadata
Write-Section "4. Package.json Metadata Check"

if (Test-Path "package.json") {
    $packageJson = Get-Content "package.json" -Raw | ConvertFrom-Json
    
    $requiredFields = @{
        "name" = $packageJson.name
        "version" = $packageJson.version
        "description" = $packageJson.description
        "author" = $packageJson.author
        "license" = $packageJson.license
        "repository" = $packageJson.repository.url
        "homepage" = $packageJson.homepage
        "bugs" = $packageJson.bugs.url
    }
    
    foreach ($field in $requiredFields.Keys) {
        $value = $requiredFields[$field]
        if ($value -and $value -ne "" -and $value -notmatch "placeholder") {
            Write-Success "package.json has valid '$field': $value"
        }
        else {
            Write-Failure "package.json missing or invalid '$field'"
        }
    }
    
    # Check keywords
    if ($packageJson.keywords -and $packageJson.keywords.Count -gt 0) {
        Write-Success "package.json has $(($packageJson.keywords).Count) keywords"
    }
    else {
        Write-Warning-Custom "package.json has no keywords (affects discoverability)"
    }
}
else {
    Write-Failure "package.json not found"
}

# Check 5: Dependencies Security
Write-Section "5. Dependencies Security Check"

Write-Info "Running npm audit..."
$auditResult = npm audit --json 2>&1 | ConvertFrom-Json

if ($auditResult.metadata.vulnerabilities.total -eq 0) {
    Write-Success "No npm vulnerabilities found"
}
else {
    $critical = $auditResult.metadata.vulnerabilities.critical
    $high = $auditResult.metadata.vulnerabilities.high
    $moderate = $auditResult.metadata.vulnerabilities.moderate
    $low = $auditResult.metadata.vulnerabilities.low
    
    if ($critical -gt 0 -or $high -gt 0) {
        Write-Failure "Found $critical critical and $high high severity vulnerabilities"
    }
    elseif ($moderate -gt 0) {
        Write-Warning-Custom "Found $moderate moderate severity vulnerabilities"
    }
    else {
        Write-Success "Only $low low severity vulnerabilities found"
    }
}

# Check 6: Linting
Write-Section "6. Code Quality Check"

if (-not $SkipTests) {
    Write-Info "Running linting..."
    try {
        npm run lint 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Linting passed"
        }
        else {
            Write-Failure "Linting failed"
        }
    }
    catch {
        Write-Failure "Linting error: $_"
    }
}
else {
    Write-Info "Skipping linting (--SkipTests flag)"
}

# Check 7: Tests
Write-Section "7. Test Suite Check"

if (-not $SkipTests) {
    Write-Info "Running frontend tests..."
    try {
        npm test -- --run 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Frontend tests passed"
        }
        else {
            Write-Failure "Frontend tests failed"
        }
    }
    catch {
        Write-Failure "Frontend test error: $_"
    }
    
    Write-Info "Running backend tests..."
    if (Test-Path "backend/requirements.txt") {
        try {
            Push-Location backend
            pytest 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Backend tests passed"
            }
            else {
                Write-Failure "Backend tests failed"
            }
            Pop-Location
        }
        catch {
            Pop-Location
            Write-Failure "Backend test error: $_"
        }
    }
    else {
        Write-Info "No backend tests found"
    }
}
else {
    Write-Info "Skipping tests (--SkipTests flag)"
}

# Check 8: Build
Write-Section "8. Build Verification"

if (-not $SkipBuild) {
    Write-Info "Running build..."
    try {
        npm run build 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0 -and (Test-Path "dist")) {
            Write-Success "Build completed successfully"
        }
        else {
            Write-Failure "Build failed or dist directory not created"
        }
    }
    catch {
        Write-Failure "Build error: $_"
    }
}
else {
    Write-Info "Skipping build (--SkipBuild flag)"
}

# Check 9: Git Status
Write-Section "9. Git Repository Check"

$gitStatus = git status --porcelain
if (-not $gitStatus) {
    Write-Success "Working directory is clean"
}
else {
    Write-Warning-Custom "Working directory has uncommitted changes"
    if ($Verbose) {
        Write-Host $gitStatus
    }
}

# Check for version tag
$currentVersion = (Get-Content "package.json" -Raw | ConvertFrom-Json).version
$tagExists = git tag -l "v$currentVersion"
if ($tagExists) {
    Write-Success "Version tag v$currentVersion exists"
}
else {
    Write-Warning-Custom "Version tag v$currentVersion does not exist"
}

# Check 10: Documentation Links
Write-Section "10. Documentation Check"

Write-Info "Checking README.md links..."
if (Test-Path "README.md") {
    $readmeContent = Get-Content "README.md" -Raw
    
    # Check for placeholder URLs
    if ($readmeContent -match "placeholder|example\.com|your-username") {
        Write-Failure "README.md contains placeholder URLs"
    }
    else {
        Write-Success "README.md has no obvious placeholder URLs"
    }
    
    # Check for badges
    if ($readmeContent -match "!\[.*\]\(https://img\.shields\.io") {
        Write-Success "README.md contains badges"
    }
    else {
        Write-Warning-Custom "README.md has no badges"
    }
}
else {
    Write-Failure "README.md not found"
}

# Generate Report
Write-Section "Verification Report"

$duration = (Get-Date) - $script:StartTime
$totalChecks = $script:ChecksPassed + $script:ChecksFailed + $script:ChecksWarning

Write-Host "Verification completed at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "Duration: $($duration.TotalSeconds) seconds" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total checks: $totalChecks" -ForegroundColor Cyan
Write-Host "Passed: $($script:ChecksPassed)" -ForegroundColor Green
Write-Host "Failed: $($script:ChecksFailed)" -ForegroundColor Red
Write-Host "Warnings: $($script:ChecksWarning)" -ForegroundColor Yellow
Write-Host ""

# Save report to file
$reportPath = "publish-verification-report.txt"
$report = @"
PEFT Studio Publish Verification Report
========================================
Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Duration: $($duration.TotalSeconds) seconds

Summary:
--------
Total checks: $totalChecks
Passed: $($script:ChecksPassed)
Failed: $($script:ChecksFailed)
Warnings: $($script:ChecksWarning)

Status: $(if ($script:ChecksFailed -eq 0) { "READY FOR PUBLICATION" } else { "NOT READY - FIX ISSUES ABOVE" })
"@

$report | Out-File -FilePath $reportPath -Encoding UTF8
Write-Info "Report saved to: $reportPath"

# Final verdict
Write-Host ""
if ($script:ChecksFailed -eq 0) {
    Write-Host "✓ Repository is READY for publication!" -ForegroundColor Green
    Write-Host "✓ All critical checks passed" -ForegroundColor Green
    if ($script:ChecksWarning -gt 0) {
        Write-Host "⚠ Consider addressing $($script:ChecksWarning) warning(s) before publishing" -ForegroundColor Yellow
    }
    exit 0
}
else {
    Write-Host "✗ Repository is NOT READY for publication" -ForegroundColor Red
    Write-Host "✗ Please fix $($script:ChecksFailed) failed check(s)" -ForegroundColor Red
    exit 1
}
