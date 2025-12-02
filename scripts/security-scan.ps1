#!/usr/bin/env pwsh
# Security Scanning Script for Windows (PowerShell)
# Scans the repository for sensitive data, credentials, and security issues

param(
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"
$script:IssuesFound = 0
$script:WarningsFound = 0

# Color output functions
function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
    $script:IssuesFound++
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
    $script:WarningsFound++
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

# Patterns to search for
$SensitivePatterns = @{
    "API Keys" = @(
        "api[_-]?key\s*[:=]\s*['\`"][a-zA-Z0-9_\-]{20,}['\`"]",
        "apikey\s*[:=]\s*['\`"][a-zA-Z0-9_\-]{20,}['\`"]"
    )
    "AWS Credentials" = @(
        "AKIA[0-9A-Z]{16}",
        "aws[_-]?secret[_-]?access[_-]?key",
        "aws[_-]?access[_-]?key[_-]?id"
    )
    "Private Keys" = @(
        "-----BEGIN (RSA |DSA |EC )?PRIVATE KEY-----",
        "-----BEGIN OPENSSH PRIVATE KEY-----"
    )
    "Tokens" = @(
        "token\s*[:=]\s*['\`"][a-zA-Z0-9_\-\.]{20,}['\`"]",
        "bearer\s+[a-zA-Z0-9_\-\.]{20,}",
        "github[_-]?token",
        "gh[ps]_[a-zA-Z0-9]{36,}"
    )
    "Passwords" = @(
        "password\s*[:=]\s*['\`"][^'\`"]{8,}['\`"]",
        "passwd\s*[:=]\s*['\`"][^'\`"]{8,}['\`"]",
        "pwd\s*[:=]\s*['\`"][^'\`"]{8,}['\`"]"
    )
    "Database URLs" = @(
        "mongodb(\+srv)?://[^\s]+",
        "postgres(ql)?://[^\s]+",
        "mysql://[^\s]+"
    )
    "Email Addresses" = @(
        "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    )
    "IP Addresses" = @(
        "\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
    )
}

# Files and directories to exclude
$ExcludePatterns = @(
    "node_modules",
    ".git",
    "dist",
    "build",
    ".hypothesis",
    "__pycache__",
    "*.min.js",
    "*.map",
    "package-lock.json",
    "*.log",
    ".pytest_cache",
    "artifacts",
    "checkpoints"
)

Write-Section "PEFT Studio Security Scanner"
Write-Info "Starting security scan of repository..."
Write-Info "Scan started at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# Check 1: Scan for sensitive patterns in files
Write-Section "1. Scanning for Sensitive Data Patterns"

$FilesToScan = Get-ChildItem -Recurse -File | Where-Object {
    $file = $_
    $shouldExclude = $false
    foreach ($pattern in $ExcludePatterns) {
        if ($file.FullName -like "*$pattern*") {
            $shouldExclude = $true
            break
        }
    }
    -not $shouldExclude
}

$TotalFiles = $FilesToScan.Count
Write-Info "Scanning $TotalFiles files..."

foreach ($category in $SensitivePatterns.Keys) {
    Write-Host "`nChecking for: $category" -ForegroundColor White
    $foundIssues = $false
    
    foreach ($pattern in $SensitivePatterns[$category]) {
        foreach ($file in $FilesToScan) {
            try {
                $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
                if ($content -match $pattern) {
                    if (-not $foundIssues) {
                        $foundIssues = $true
                    }
                    Write-Error-Custom "Found in: $($file.FullName)"
                    if ($Verbose) {
                        $matches = [regex]::Matches($content, $pattern)
                        foreach ($match in $matches) {
                            Write-Host "  Match: $($match.Value)" -ForegroundColor DarkRed
                        }
                    }
                }
            }
            catch {
                # Skip binary files or files that can't be read
                continue
            }
        }
    }
    
    if (-not $foundIssues) {
        Write-Success "No $category found"
    }
}

# Check 2: Verify .gitignore coverage
Write-Section "2. Verifying .gitignore Coverage"

$RequiredGitignorePatterns = @(
    "*.env",
    ".env",
    ".env.local",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "node_modules/",
    "__pycache__/",
    "*.pyc",
    ".pytest_cache/",
    "dist/",
    "build/",
    "*.log"
)

if (Test-Path ".gitignore") {
    $gitignoreContent = Get-Content ".gitignore" -Raw
    
    foreach ($pattern in $RequiredGitignorePatterns) {
        if ($gitignoreContent -match [regex]::Escape($pattern)) {
            Write-Success "Pattern '$pattern' is in .gitignore"
        }
        else {
            Write-Warning-Custom "Pattern '$pattern' is missing from .gitignore"
        }
    }
}
else {
    Write-Error-Custom ".gitignore file not found!"
}

# Check 3: Verify no actual sensitive files exist
Write-Section "3. Checking for Sensitive Files"

$SensitiveFiles = @(
    "*.env",
    ".env",
    ".env.local",
    ".env.production",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "*.pem",
    "*.key",
    "id_rsa",
    "id_dsa"
)

$foundSensitiveFiles = $false
foreach ($pattern in $SensitiveFiles) {
    $files = Get-ChildItem -Recurse -Filter $pattern -File -ErrorAction SilentlyContinue | Where-Object {
        $file = $_
        $shouldExclude = $false
        foreach ($excludePattern in $ExcludePatterns) {
            if ($file.FullName -like "*$excludePattern*") {
                $shouldExclude = $true
                break
            }
        }
        -not $shouldExclude
    }
    
    if ($files) {
        foreach ($file in $files) {
            Write-Error-Custom "Found sensitive file: $($file.FullName)"
            $foundSensitiveFiles = $true
        }
    }
}

if (-not $foundSensitiveFiles) {
    Write-Success "No sensitive files found in repository"
}

# Check 4: Scan git history for sensitive data
Write-Section "4. Scanning Git History"

Write-Info "Checking for sensitive patterns in commit history..."

$sensitiveKeywords = @("password", "secret", "key", "token", "credential", "api_key")
$historyIssues = $false

foreach ($keyword in $sensitiveKeywords) {
    $result = git log --all --full-history --source -- "*$keyword*" 2>&1
    if ($result -and $result -notmatch "fatal") {
        Write-Warning-Custom "Found commits referencing '$keyword' in file paths"
        $historyIssues = $true
        if ($Verbose) {
            Write-Host $result -ForegroundColor DarkYellow
        }
    }
}

if (-not $historyIssues) {
    Write-Success "No obvious sensitive data patterns in git history"
}

# Check 5: Check for large files
Write-Section "5. Checking for Large Files"

Write-Info "Scanning for files larger than 1MB..."

$largeFiles = Get-ChildItem -Recurse -File | Where-Object {
    $file = $_
    $shouldExclude = $false
    foreach ($pattern in $ExcludePatterns) {
        if ($file.FullName -like "*$pattern*") {
            $shouldExclude = $true
            break
        }
    }
    -not $shouldExclude -and $_.Length -gt 1MB
}

if ($largeFiles) {
    foreach ($file in $largeFiles) {
        $sizeMB = [math]::Round($file.Length / 1MB, 2)
        Write-Warning-Custom "Large file found: $($file.FullName) ($sizeMB MB)"
    }
}
else {
    Write-Success "No files larger than 1MB found"
}

# Check 6: Verify environment variable usage
Write-Section "6. Verifying Environment Variable Usage"

Write-Info "Checking for hardcoded configuration..."

$configFiles = Get-ChildItem -Recurse -Include "*.ts", "*.tsx", "*.js", "*.jsx", "*.py" -File | Where-Object {
    $file = $_
    $shouldExclude = $false
    foreach ($pattern in $ExcludePatterns) {
        if ($file.FullName -like "*$pattern*") {
            $shouldExclude = $true
            break
        }
    }
    -not $shouldExclude
}

$hardcodedConfigFound = $false
foreach ($file in $configFiles) {
    try {
        $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
        # Look for hardcoded URLs, ports, etc. (excluding localhost/127.0.0.1)
        if ($content -match 'http://(?!localhost|127\.0\.0\.1)[a-zA-Z0-9.-]+' -or 
            $content -match 'https://(?!localhost|127\.0\.0\.1)[a-zA-Z0-9.-]+') {
            # Exclude common safe patterns
            if ($content -notmatch 'github\.com' -and 
                $content -notmatch 'example\.com' -and
                $content -notmatch 'huggingface\.co') {
                Write-Warning-Custom "Potential hardcoded URL in: $($file.FullName)"
                $hardcodedConfigFound = $true
            }
        }
    }
    catch {
        continue
    }
}

if (-not $hardcodedConfigFound) {
    Write-Success "No obvious hardcoded configuration found"
}

# Summary
Write-Section "Security Scan Summary"

Write-Host "Scan completed at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "Files scanned: $TotalFiles" -ForegroundColor Cyan
Write-Host ""

if ($script:IssuesFound -eq 0 -and $script:WarningsFound -eq 0) {
    Write-Host "✓ No security issues found!" -ForegroundColor Green
    Write-Host "✓ Repository appears safe for public release" -ForegroundColor Green
    exit 0
}
else {
    if ($script:IssuesFound -gt 0) {
        Write-Host "✗ Found $($script:IssuesFound) security issue(s)" -ForegroundColor Red
    }
    if ($script:WarningsFound -gt 0) {
        Write-Host "⚠ Found $($script:WarningsFound) warning(s)" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "Please review and fix the issues above before publishing." -ForegroundColor Yellow
    
    if ($script:IssuesFound -gt 0) {
        exit 1
    }
    else {
        exit 0
    }
}
