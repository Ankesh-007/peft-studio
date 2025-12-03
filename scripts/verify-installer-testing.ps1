#!/usr/bin/env pwsh
# Verify Installer Testing Documentation
# This script verifies that installer testing documentation and procedures are in place

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installer Testing Verification" -ForegroundColor Cyan
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

# Test 1: Check if installer testing guide exists
Test-Step "Installer testing guide exists" {
    return Test-Path "docs/reference/installer-testing-guide.md"
}

# Test 2: Verify testing guide has required sections
Test-Step "Testing guide has required sections" {
    if (-not (Test-Path "docs/reference/installer-testing-guide.md")) {
        return $false
    }
    
    $content = Get-Content "docs/reference/installer-testing-guide.md" -Raw
    
    $requiredSections = @(
        "Prerequisites",
        "Testing Procedure",
        "Installation Testing",
        "Application Launch Testing",
        "Core Feature Testing",
        "Uninstallation Testing"
    )
    
    foreach ($section in $requiredSections) {
        if ($content -notmatch $section) {
            Write-Host "    Missing section: $section" -ForegroundColor Red
            return $false
        }
    }
    
    return $true
}

# Test 3: Check if platform-specific instructions exist
Test-Step "Platform-specific testing instructions exist" {
    if (-not (Test-Path "docs/reference/installer-testing-guide.md")) {
        return $false
    }
    
    $content = Get-Content "docs/reference/installer-testing-guide.md" -Raw
    
    $platforms = @("Windows", "macOS", "Linux")
    
    foreach ($platform in $platforms) {
        if ($content -notmatch $platform) {
            Write-Host "    Missing platform: $platform" -ForegroundColor Red
            return $false
        }
    }
    
    return $true
}

# Test 4: Verify build output directory is configured
Test-Step "Build output directory is configured" {
    $packageJson = Get-Content "package.json" | ConvertFrom-Json
    
    if (-not $packageJson.build.directories.output) {
        Write-Host "    Missing output directory configuration" -ForegroundColor Red
        return $false
    }
    
    return $true
}

# Test 5: Check if release directory exists or can be created
Test-Step "Release directory structure is ready" {
    $packageJson = Get-Content "package.json" | ConvertFrom-Json
    $outputDir = $packageJson.build.directories.output
    
    if (-not $outputDir) {
        return $false
    }
    
    # Directory doesn't need to exist yet, just verify it's configured
    return $true
}

# Test 6: Verify installer formats are configured
Test-Step "Installer formats are configured for all platforms" {
    $packageJson = Get-Content "package.json" | ConvertFrom-Json
    
    # Windows
    if (-not $packageJson.build.win.target) {
        Write-Host "    Missing Windows installer targets" -ForegroundColor Red
        return $false
    }
    
    # macOS
    if (-not $packageJson.build.mac.target) {
        Write-Host "    Missing macOS installer targets" -ForegroundColor Red
        return $false
    }
    
    # Linux
    if (-not $packageJson.build.linux.target) {
        Write-Host "    Missing Linux installer targets" -ForegroundColor Red
        return $false
    }
    
    return $true
}

# Test 7: Check if test report template exists in guide
Test-Step "Test report template exists in guide" {
    if (-not (Test-Path "docs/reference/installer-testing-guide.md")) {
        return $false
    }
    
    $content = Get-Content "docs/reference/installer-testing-guide.md" -Raw
    
    return $content -match "Test Report Template"
}

# Test 8: Verify common issues section exists
Test-Step "Common issues and solutions documented" {
    if (-not (Test-Path "docs/reference/installer-testing-guide.md")) {
        return $false
    }
    
    $content = Get-Content "docs/reference/installer-testing-guide.md" -Raw
    
    return $content -match "Common Issues and Solutions"
}

# Test 9: Check if automated testing scripts are mentioned
Test-Step "Automated testing procedures documented" {
    if (-not (Test-Path "docs/reference/installer-testing-guide.md")) {
        return $false
    }
    
    $content = Get-Content "docs/reference/installer-testing-guide.md" -Raw
    
    return $content -match "Automated Testing"
}

# Test 10: Verify release checklist exists
Test-Step "Release checklist exists in guide" {
    if (-not (Test-Path "docs/reference/installer-testing-guide.md")) {
        return $false
    }
    
    $content = Get-Content "docs/reference/installer-testing-guide.md" -Raw
    
    return $content -match "Checklist for Release"
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
    Write-Host "All installer testing checks passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Installer testing documentation is complete." -ForegroundColor Cyan
    Write-Host "See: docs/reference/installer-testing-guide.md" -ForegroundColor White
    Write-Host ""
    Write-Host "To test installers:" -ForegroundColor Cyan
    Write-Host "  1. Build installers: npm run package:win|mac|linux" -ForegroundColor White
    Write-Host "  2. Follow testing guide for each platform" -ForegroundColor White
    Write-Host "  3. Document results using test report template" -ForegroundColor White
    Write-Host ""
    exit 0
} else {
    Write-Host "Some installer testing checks failed." -ForegroundColor Red
    Write-Host "Please fix the issues before proceeding." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
