# Quick Build and Test Script
# Simple wrapper for the comprehensive test-build-deploy script

Write-Host "======================================================================"  -ForegroundColor Cyan
Write-Host "PEFT Studio - Quick Build and Test" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "What would you like to do?" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Run tests only" -ForegroundColor White
Write-Host "2. Build Windows installer (with tests)" -ForegroundColor White
Write-Host "3. Build Linux installer (with tests)" -ForegroundColor White
Write-Host "4. Build both Windows and Linux (with tests)" -ForegroundColor White
Write-Host "5. Quick build (skip tests) - Windows" -ForegroundColor White
Write-Host "6. Quick build (skip tests) - Linux" -ForegroundColor White
Write-Host "7. Quick build (skip tests) - Both" -ForegroundColor White
Write-Host "8. Build and push to GitHub" -ForegroundColor White
Write-Host "9. Exit" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-9)"

switch ($choice) {
    "1" {
        Write-Host "`nRunning tests..." -ForegroundColor Green
        .\scripts\test-build-deploy.ps1 -SkipBuild
    }
    "2" {
        Write-Host "`nBuilding Windows installer with tests..." -ForegroundColor Green
        .\scripts\test-build-deploy.ps1 -Platform "windows"
    }
    "3" {
        Write-Host "`nBuilding Linux installer with tests..." -ForegroundColor Green
        .\scripts\test-build-deploy.ps1 -Platform "linux"
    }
    "4" {
        Write-Host "`nBuilding Windows and Linux installers with tests..." -ForegroundColor Green
        .\scripts\test-build-deploy.ps1 -Platform "windows,linux"
    }
    "5" {
        Write-Host "`nQuick build - Windows (skipping tests)..." -ForegroundColor Green
        .\scripts\test-build-deploy.ps1 -SkipTests -Platform "windows"
    }
    "6" {
        Write-Host "`nQuick build - Linux (skipping tests)..." -ForegroundColor Green
        .\scripts\test-build-deploy.ps1 -SkipTests -Platform "linux"
    }
    "7" {
        Write-Host "`nQuick build - Both platforms (skipping tests)..." -ForegroundColor Green
        .\scripts\test-build-deploy.ps1 -SkipTests -Platform "windows,linux"
    }
    "8" {
        Write-Host "`nBuilding and pushing to GitHub..." -ForegroundColor Green
        $message = Read-Host "Enter commit message (or press Enter for default)"
        if ([string]::IsNullOrWhiteSpace($message)) {
            .\scripts\test-build-deploy.ps1 -Platform "windows,linux" -PushToGitHub
        } else {
            .\scripts\test-build-deploy.ps1 -Platform "windows,linux" -PushToGitHub -CommitMessage $message
        }
    }
    "9" {
        Write-Host "`nExiting..." -ForegroundColor Yellow
        exit 0
    }
    default {
        Write-Host "`nInvalid choice. Please run the script again." -ForegroundColor Red
        exit 1
    }
}
