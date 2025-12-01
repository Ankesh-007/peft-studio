#!/usr/bin/env pwsh
# Verify Installation Documentation Script
# This script verifies that the installation instructions in README are accurate

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installation Documentation Verification" -ForegroundColor Cyan
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

# Test 1: Check if README.md exists and contains installation instructions
Test-Step "README.md exists with installation section" {
    if (-not (Test-Path "README.md")) {
        return $false
    }
    
    $readme = Get-Content "README.md" -Raw
    return ($readme -match "## 🚀 Quick Start") -and ($readme -match "### Installation")
}

# Test 2: Check if package.json exists
Test-Step "package.json exists" {
    return Test-Path "package.json"
}

# Test 3: Check if backend/requirements.txt exists
Test-Step "backend/requirements.txt exists" {
    return Test-Path "backend/requirements.txt"
}

# Test 4: Verify npm scripts mentioned in README exist
Test-Step "npm scripts in README exist in package.json" {
    $readme = Get-Content "README.md" -Raw
    $packageJson = Get-Content "package.json" | ConvertFrom-Json
    
    $scriptsToCheck = @("dev", "build", "electron:dev", "electron:build")
    
    foreach ($script in $scriptsToCheck) {
        if (-not $packageJson.scripts.$script) {
            Write-Host "    Missing script: $script" -ForegroundColor Red
            return $false
        }
    }
    
    return $true
}

# Test 5: Check if electron directory exists
Test-Step "electron directory exists" {
    return Test-Path "electron"
}

# Test 6: Check if backend directory exists
Test-Step "backend directory exists" {
    return Test-Path "backend"
}

# Test 7: Verify key dependencies in package.json
Test-Step "Key dependencies listed in package.json" {
    $packageJson = Get-Content "package.json" | ConvertFrom-Json
    
    $keyDeps = @("react", "electron")
    $keyDevDeps = @("vite")
    
    foreach ($dep in $keyDeps) {
        if (-not $packageJson.dependencies.$dep) {
            Write-Host "    Missing dependency: $dep" -ForegroundColor Red
            return $false
        }
    }
    
    foreach ($dep in $keyDevDeps) {
        if (-not $packageJson.devDependencies.$dep) {
            Write-Host "    Missing devDependency: $dep" -ForegroundColor Red
            return $false
        }
    }
    
    return $true
}

# Test 8: Check if .gitignore excludes generated directories
Test-Step ".gitignore excludes node_modules and dist" {
    if (-not (Test-Path ".gitignore")) {
        return $false
    }
    
    $gitignore = Get-Content ".gitignore" -Raw
    return ($gitignore -match "node_modules") -and ($gitignore -match "dist")
}

# Test 9: Verify documentation links in README
Test-Step "Documentation files referenced in README exist" {
    $readme = Get-Content "README.md" -Raw
    
    # Extract markdown links
    $links = [regex]::Matches($readme, '\[.*?\]\((docs/.*?\.md)\)')
    
    $allExist = $true
    foreach ($match in $links) {
        $docPath = $match.Groups[1].Value
        if (-not (Test-Path $docPath)) {
            Write-Host "    Missing doc: $docPath" -ForegroundColor Red
            $allExist = $false
        }
    }
    
    return $allExist
}

# Test 10: Check if build scripts exist
Test-Step "Build scripts exist" {
    $scriptsExist = $true
    
    $buildScripts = @("scripts/build.js", "scripts/build.ps1", "scripts/build.sh")
    
    foreach ($script in $buildScripts) {
        if (-not (Test-Path $script)) {
            Write-Host "    Missing: $script" -ForegroundColor Red
            $scriptsExist = $false
        }
    }
    
    return $scriptsExist
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
    Write-Host "All installation documentation checks passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Some installation documentation checks failed." -ForegroundColor Red
    exit 1
}
