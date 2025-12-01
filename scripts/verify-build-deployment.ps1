#!/usr/bin/env pwsh
# Master Build and Deployment Verification Script
# Runs all verification checks for Task 8

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Build and Deployment Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$totalPassed = 0
$totalFailed = 0
$scripts = @(
    @{
        Name = "Installation Documentation"
        Script = "scripts/verify-installation-docs.ps1"
    },
    @{
        Name = "Build Commands"
        Script = "scripts/verify-build-commands.ps1"
    },
    @{
        Name = "Installer Testing"
        Script = "scripts/verify-installer-testing.ps1"
    },
    @{
        Name = "Troubleshooting Documentation"
        Script = "scripts/verify-troubleshooting-docs.ps1"
    }
)

foreach ($item in $scripts) {
    Write-Host "Running: $($item.Name)" -ForegroundColor Yellow
    Write-Host "Script: $($item.Script)" -ForegroundColor Gray
    Write-Host ""
    
    try {
        $result = & powershell -ExecutionPolicy Bypass -File $item.Script
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            Write-Host "[OK] $($item.Name) verification passed" -ForegroundColor Green
            $totalPassed++
        } else {
            Write-Host "[FAIL] $($item.Name) verification failed" -ForegroundColor Red
            $totalFailed++
        }
    } catch {
        Write-Host "[ERROR] Failed to run $($item.Name): $($_.Exception.Message)" -ForegroundColor Red
        $totalFailed++
    }
    
    Write-Host ""
    Write-Host "----------------------------------------" -ForegroundColor Gray
    Write-Host ""
}

# Final Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Final Verification Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Verification Categories:" -ForegroundColor White
Write-Host "  Passed: $totalPassed" -ForegroundColor Green
Write-Host "  Failed: $totalFailed" -ForegroundColor Red
Write-Host ""

if ($totalFailed -eq 0) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "ALL VERIFICATIONS PASSED!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Build and Deployment Verification Complete" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Summary:" -ForegroundColor White
    Write-Host "  - Installation documentation verified" -ForegroundColor Green
    Write-Host "  - Build commands configured correctly" -ForegroundColor Green
    Write-Host "  - Installer testing procedures ready" -ForegroundColor Green
    Write-Host "  - Troubleshooting documentation complete" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Build installers: npm run package:win|mac|linux" -ForegroundColor White
    Write-Host "  2. Test on target platforms" -ForegroundColor White
    Write-Host "  3. Document test results" -ForegroundColor White
    Write-Host "  4. Prepare for public release" -ForegroundColor White
    Write-Host ""
    Write-Host "See BUILD_DEPLOYMENT_VERIFICATION_SUMMARY.md for details" -ForegroundColor Gray
    Write-Host ""
    exit 0
} else {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "SOME VERIFICATIONS FAILED" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please review the output above and fix any issues." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
