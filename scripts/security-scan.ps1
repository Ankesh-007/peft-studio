# Security Scan Script for PEFT Studio
# This script scans for potential security issues before public release

Write-Host "🔒 PEFT Studio Security Scan" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$issues = 0

# Function to search and report
function Search-Pattern {
    param(
        [string]$Pattern,
        [string]$Description,
        [string[]]$Exclude = @()
    )
    
    Write-Host "Checking for $Description..." -ForegroundColor Yellow
    
    $excludeArgs = @()
    foreach ($ex in $Exclude) {
        $excludeArgs += "--exclude-dir=$ex"
    }
    
    $results = git grep -i $Pattern $excludeArgs 2>$null
    
    if ($results) {
        Write-Host "  ⚠️  Found potential issues:" -ForegroundColor Red
        $results | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
        return 1
    } else {
        Write-Host "  ✅ No issues found" -ForegroundColor Green
        return 0
    }
}

# Scan for API keys
$issues += Search-Pattern "api[_-]key" "API keys" @("node_modules", ".git", "*.md")

# Scan for tokens
$issues += Search-Pattern "token\s*=\s*['\"]" "hardcoded tokens" @("node_modules", ".git", "*.md")

# Scan for passwords
$issues += Search-Pattern "password\s*=\s*['\"]" "hardcoded passwords" @("node_modules", ".git", "*.md")

# Scan for secrets
$issues += Search-Pattern "secret\s*=\s*['\"]" "hardcoded secrets" @("node_modules", ".git", "*.md")

# Scan for AWS keys
$issues += Search-Pattern "AKIA[0-9A-Z]{16}" "AWS access keys" @("node_modules", ".git")

# Scan for private keys
$issues += Search-Pattern "BEGIN.*PRIVATE KEY" "private keys" @("node_modules", ".git")

# Scan for email addresses (excluding documentation)
Write-Host "Checking for email addresses..." -ForegroundColor Yellow
$emails = git grep -E "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" -- ':!*.md' ':!LICENSE' ':!node_modules' 2>$null
if ($emails) {
    Write-Host "  ⚠️  Found email addresses (review if they should be public):" -ForegroundColor Yellow
    $emails | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
}

# Check .env files
Write-Host "Checking .env files..." -ForegroundColor Yellow
$envFiles = Get-ChildItem -Path . -Filter ".env*" -Recurse -File | Where-Object { $_.Name -ne ".env.example" }
if ($envFiles) {
    Write-Host "  ⚠️  Found .env files (ensure they're in .gitignore):" -ForegroundColor Yellow
    $envFiles | ForEach-Object { Write-Host "    $($_.FullName)" -ForegroundColor Yellow }
    $issues++
} else {
    Write-Host "  ✅ No .env files found" -ForegroundColor Green
}

# Check for database files
Write-Host "Checking for database files..." -ForegroundColor Yellow
$dbFiles = Get-ChildItem -Path . -Include "*.db", "*.sqlite", "*.sqlite3" -Recurse -File
if ($dbFiles) {
    Write-Host "  ⚠️  Found database files (ensure they're in .gitignore):" -ForegroundColor Yellow
    $dbFiles | ForEach-Object { Write-Host "    $($_.FullName)" -ForegroundColor Yellow }
    $issues++
} else {
    Write-Host "  ✅ No database files found" -ForegroundColor Green
}

# Check for large files
Write-Host "Checking for large files (>10MB)..." -ForegroundColor Yellow
$largeFiles = Get-ChildItem -Path . -Recurse -File | Where-Object { 
    $_.Length -gt 10MB -and 
    $_.FullName -notmatch "node_modules" -and 
    $_.FullName -notmatch ".git"
}
if ($largeFiles) {
    Write-Host "  ⚠️  Found large files:" -ForegroundColor Yellow
    $largeFiles | ForEach-Object { 
        $sizeMB = [math]::Round($_.Length / 1MB, 2)
        Write-Host "    $($_.FullName) ($sizeMB MB)" -ForegroundColor Yellow 
    }
}

# Check .gitignore
Write-Host "Checking .gitignore..." -ForegroundColor Yellow
if (Test-Path ".gitignore") {
    $gitignore = Get-Content ".gitignore"
    $requiredPatterns = @(".env", "*.db", "*.sqlite", "node_modules", "__pycache__")
    $missing = @()
    
    foreach ($pattern in $requiredPatterns) {
        if ($gitignore -notcontains $pattern) {
            $missing += $pattern
        }
    }
    
    if ($missing) {
        Write-Host "  ⚠️  Missing patterns in .gitignore:" -ForegroundColor Yellow
        $missing | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
    } else {
        Write-Host "  ✅ .gitignore looks good" -ForegroundColor Green
    }
} else {
    Write-Host "  ❌ .gitignore not found!" -ForegroundColor Red
    $issues++
}

# Summary
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
if ($issues -eq 0) {
    Write-Host "✅ Security scan complete - No critical issues found!" -ForegroundColor Green
    Write-Host "Review any warnings above before publishing." -ForegroundColor Yellow
} else {
    Write-Host "⚠️  Security scan found $issues potential issue(s)" -ForegroundColor Red
    Write-Host "Please review and fix before publishing!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Review any warnings above" -ForegroundColor White
Write-Host "2. Run: npm test && cd backend && pytest" -ForegroundColor White
Write-Host "3. Run: npm run lint" -ForegroundColor White
Write-Host "4. Review PUBLIC_RELEASE_CHECKLIST.md" -ForegroundColor White
Write-Host "5. Test fresh clone and build" -ForegroundColor White
