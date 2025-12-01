#!/usr/bin/env pwsh
# Verify Build Commands Script
# This script verifies that build commands are properly configured

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Build Commands Verification" -ForegroundColor Cyan
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

# Test 1: Check if package.json has build scripts
Test-Step "package.json has build scripts" {
    $packageJson = Get-Content "package.json" | ConvertFrom-Json
    
    $requiredScripts = @(
        "build",
        "package:win",
        "package:mac",
        "package:linux"
    )
    
    foreach ($script in $requiredScripts) {
        if (-not $packageJson.scripts.$script) {
            Write-Host "    Missing script: $script" -ForegroundColor Red
            return $false
        }
    }
    
    return $true
}

# Test 2: Check if electron-builder is installed
Test-Step "electron-builder is in dependencies" {
    $packageJson = Get-Content "package.json" | ConvertFrom-Json
    
    return ($packageJson.dependencies.'electron-builder' -or 
            $packageJson.devDependencies.'electron-builder')
}

# Test 3: Check if build configuration exists in package.json
Test-Step "electron-builder configuration exists" {
    $packageJson = Get-Content "package.json" | ConvertFrom-Json
    
    if (-not $packageJson.build) {
        Write-Host "    Missing build configuration" -ForegroundColor Red
        return $false
    }
    
    # Check for platform-specific configs
    $platforms = @("win", "mac", "linux")
    foreach ($platform in $platforms) {
        if (-not $packageJson.build.$platform) {
            Write-Host "    Missing $platform configuration" -ForegroundColor Red
            return $false
        }
    }
    
    return $true
}

# Test 4: Check if build directory exists
Test-Step "build directory exists" {
    return Test-Path "build"
}

# Test 5: Check if build scripts exist
Test-Step "build scripts exist" {
    $scripts = @("scripts/build.js", "scripts/build.ps1", "scripts/build.sh")
    
    foreach ($script in $scripts) {
        if (-not (Test-Path $script)) {
            Write-Host "    Missing: $script" -ForegroundColor Red
            return $false
        }
    }
    
    return $true
}

# Test 6: Verify build.js is executable
Test-Step "build.js is a valid Node.js script" {
    if (-not (Test-Path "scripts/build.js")) {
        return $false
    }
    
    $content = Get-Content "scripts/build.js" -Raw
    return $content -match "#!/usr/bin/env node"
}

# Test 7: Check if electron is installed
Test-Step "electron is in dependencies" {
    $packageJson = Get-Content "package.json" | ConvertFrom-Json
    
    return ($packageJson.dependencies.electron -or 
            $packageJson.devDependencies.electron)
}

# Test 8: Verify build output directory configuration
Test-Step "build output directory is configured" {
    $packageJson = Get-Content "package.json" | ConvertFrom-Json
    
    if (-not $packageJson.build.directories) {
        Write-Host "    Missing directories configuration" -ForegroundColor Red
        return $false
    }
    
    if (-not $packageJson.build.directories.output) {
        Write-Host "    Missing output directory configuration" -ForegroundColor Red
        return $false
    }
    
    return $true
}

# Test 9: Check if main entry point is configured
Test-Step "electron main entry point is configured" {
    $packageJson = Get-Content "package.json" | ConvertFrom-Json
    
    if (-not $packageJson.main) {
        Write-Host "    Missing main entry point" -ForegroundColor Red
        return $false
    }
    
    $mainFile = $packageJson.main
    if (-not (Test-Path $mainFile)) {
        Write-Host "    Main file not found: $mainFile" -ForegroundColor Red
        return $false
    }
    
    return $true
}

# Test 10: Verify platform-specific targets are configured
Test-Step "platform-specific targets are configured" {
    $packageJson = Get-Content "package.json" | ConvertFrom-Json
    
    # Check Windows targets
    if (-not $packageJson.build.win.target) {
        Write-Host "    Missing Windows targets" -ForegroundColor Red
        return $false
    }
    
    # Check macOS targets
    if (-not $packageJson.build.mac.target) {
        Write-Host "    Missing macOS targets" -ForegroundColor Red
        return $false
    }
    
    # Check Linux targets
    if (-not $packageJson.build.linux.target) {
        Write-Host "    Missing Linux targets" -ForegroundColor Red
        return $false
    }
    
    return $true
}

# Test 11: Check if vite config exists for frontend build
Test-Step "vite configuration exists" {
    return Test-Path "vite.config.ts"
}

# Test 12: Verify TypeScript configuration
Test-Step "TypeScript configuration exists" {
    return Test-Path "tsconfig.json"
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
    Write-Host "All build command checks passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Build commands are properly configured:" -ForegroundColor Cyan
    Write-Host "  - npm run package:win    (Windows installer)" -ForegroundColor White
    Write-Host "  - npm run package:mac    (macOS installer)" -ForegroundColor White
    Write-Host "  - npm run package:linux  (Linux installer)" -ForegroundColor White
    Write-Host "  - npm run package:all    (All platforms)" -ForegroundColor White
    Write-Host ""
    exit 0
} else {
    Write-Host "Some build command checks failed." -ForegroundColor Red
    Write-Host "Please fix the issues before building installers." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
