#!/usr/bin/env pwsh
# Verify Troubleshooting Documentation
# This script verifies that troubleshooting documentation is complete and comprehensive

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Troubleshooting Documentation Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$passed = 0
$failed = 0

function Test-Step {
    param(
        [string]$Description,
        [scriptblock]$Test
    )
    
    Write-Host "Testing: $Description" -ForegroundColor Yellow
    try {
        $result = & $Test
        if ($result) {
            Write-Host "  [OK] $Description" -ForegroundColor Green
            $script:passed++
        } else {
            Write-Host "  [FAIL] $Description" -ForegroundColor Red
            $script:failed++
        }
    } catch {
        Write-Host "  [FAIL] $Description - $($_.Exception.Message)" -ForegroundColor Red
        $script:failed++
    }
    Write-Host ""
}

# Test 1: Check if troubleshooting guide exists
Test-Step "Troubleshooting guide exists" {
    return Test-Path "docs/reference/troubleshooting.md"
}

# Test 2: Verify guide has installation issues section
Test-Step "Installation issues section exists" {
    if (-not (Test-Path "docs/reference/troubleshooting.md")) {
        return $false
    }
    
    $content = Get-Content "docs/reference/troubleshooting.md" -Raw
    return $content -match "## Installation Issues"
}

# Test 3: Check for platform-specific sections
Test-Step "Platform-specific sections exist" {
    if (-not (Test-Path "docs/reference/troubleshooting.md")) {
        return $false
    }
    
    $content = Get-Content "docs/reference/troubleshooting.md" -Raw
    
    $platforms = @("Windows", "macOS", "Linux")
    
    foreach ($platform in $platforms) {
        if ($content -notmatch "$platform-Specific Issues") {
            Write-Host "    Missing platform: $platform" -ForegroundColor Red
            return $false
        }
    }
    
    return $true
}

# Test 4: Verify common installation problems are covered
Test-Step "Common installation problems documented" {
    if (-not (Test-Path "docs/reference/troubleshooting.md")) {
        return $false
    }
    
    $content = Get-Content "docs/reference/troubleshooting.md" -Raw
    
    $commonIssues = @(
        "Dependencies",
        "Virtual Environment",
        "Build",
        "Application Won't Start"
    )
    
    foreach ($issue in $commonIssues) {
        if ($content -notmatch $issue) {
            Write-Host "    Missing issue: $issue" -ForegroundColor Red
            return $false
        }
    }
    
    return $true
}

# Test 5: Check for Windows-specific quirks
Test-Step "Windows-specific quirks documented" {
    if (-not (Test-Path "docs/reference/troubleshooting.md")) {
        return $false
    }
    
    $content = Get-Content "docs/reference/troubleshooting.md" -Raw
    
    $windowsIssues = @(
        "Windows Defender",
        "Administrator",
        "PATH"
    )
    
    foreach ($issue in $windowsIssues) {
        if ($content -notmatch $issue) {
            Write-Host "    Missing Windows issue: $issue" -ForegroundColor Red
            return $false
        }
    }
    
    return $true
}

# Test 6: Check for macOS-specific quirks
Test-Step "macOS-specific quirks documented" {
    if (-not (Test-Path "docs/reference/troubleshooting.md")) {
        return $false
    }
    
    $content = Get-Content "docs/reference/troubleshooting.md" -Raw
    
    $macIssues = @(
        "Gatekeeper",
        "Code Signing",
        "Rosetta"
    )
    
    foreach ($issue in $macIssues) {
        if ($content -notmatch $issue) {
            Write-Host "    Missing macOS issue: $issue" -ForegroundColor Red
            return $false
        }
    }
    
    return $true
}

# Test 7: Check for Linux-specific quirks
Test-Step "Linux-specific quirks documented" {
    if (-not (Test-Path "docs/reference/troubleshooting.md")) {
        return $false
    }
    
    $content = Get-Content "docs/reference/troubleshooting.md" -Raw
    
    $linuxIssues = @(
        "AppImage",
        "FUSE",
        "System Libraries"
    )
    
    foreach ($issue in $linuxIssues) {
        if ($content -notmatch $issue) {
            Write-Host "    Missing Linux issue: $issue" -ForegroundColor Red
            return $false
        }
    }
    
    return $true
}

# Test 8: Verify solutions are provided
Test-Step "Solutions provided for issues" {
    if (-not (Test-Path "docs/reference/troubleshooting.md")) {
        return $false
    }
    
    $content = Get-Content "docs/reference/troubleshooting.md" -Raw
    
    # Check for solution keywords
    $solutionKeywords = @("Solutions:", "Solution:", "Fix:")
    
    $hasSolutions = $false
    foreach ($keyword in $solutionKeywords) {
        if ($content -match $keyword) {
            $hasSolutions = $true
            break
        }
    }
    
    return $hasSolutions
}

# Test 9: Check for code examples
Test-Step "Code examples provided" {
    if (-not (Test-Path "docs/reference/troubleshooting.md")) {
        return $false
    }
    
    $content = Get-Content "docs/reference/troubleshooting.md" -Raw
    
    # Check for code blocks (triple backticks)
    return $content -match '```'
}

# Test 10: Verify contact/support information
Test-Step "Support contact information provided" {
    if (-not (Test-Path "docs/reference/troubleshooting.md")) {
        return $false
    }
    
    $content = Get-Content "docs/reference/troubleshooting.md" -Raw
    
    return (($content -match "Getting More Help") -or ($content -match "Contact Support"))
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verification Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host ""

if ($failed -eq 0) {
    Write-Host "All troubleshooting documentation checks passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Troubleshooting guide is comprehensive and includes:" -ForegroundColor Cyan
    Write-Host "  - Installation issues and solutions" -ForegroundColor White
    Write-Host "  - Platform-specific quirks (Windows, macOS, Linux)" -ForegroundColor White
    Write-Host "  - Common problems with detailed solutions" -ForegroundColor White
    Write-Host "  - Code examples and commands" -ForegroundColor White
    Write-Host "  - Support contact information" -ForegroundColor White
    Write-Host ""
    Write-Host "Documentation: docs/reference/troubleshooting.md" -ForegroundColor Cyan
    Write-Host ""
    exit 0
} else {
    Write-Host "Some troubleshooting documentation checks failed." -ForegroundColor Red
    Write-Host "Please fix the issues before proceeding." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
