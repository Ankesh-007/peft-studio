# Publish to GitHub Script
# This script helps you publish PEFT Studio to GitHub

param(
    [switch]$SkipTests,
    [switch]$SkipSecurity
)

Write-Host "🚀 PEFT Studio - Publish to GitHub" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

$errors = 0

# Step 1: Security Scan
if (-not $SkipSecurity) {
    Write-Host "Step 1: Running security scan..." -ForegroundColor Yellow
    .\scripts\security-scan.ps1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ⚠️  Security scan found issues. Review and fix before publishing." -ForegroundColor Red
        Write-Host "  Or run with -SkipSecurity to bypass (not recommended)" -ForegroundColor Yellow
        $errors++
    }
    Write-Host ""
} else {
    Write-Host "Step 1: Skipping security scan (not recommended)" -ForegroundColor Yellow
    Write-Host ""
}

# Step 2: Run Tests
if (-not $SkipTests) {
    Write-Host "Step 2: Running tests..." -ForegroundColor Yellow
    
    # Frontend tests
    Write-Host "  Running frontend tests..." -ForegroundColor Cyan
    npm test -- --run
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ❌ Frontend tests failed" -ForegroundColor Red
        $errors++
    } else {
        Write-Host "  ✅ Frontend tests passed" -ForegroundColor Green
    }
    
    # Backend tests
    Write-Host "  Running backend tests..." -ForegroundColor Cyan
    Push-Location backend
    pytest
    $testResult = $LASTEXITCODE
    Pop-Location
    
    if ($testResult -ne 0) {
        Write-Host "  ❌ Backend tests failed" -ForegroundColor Red
        $errors++
    } else {
        Write-Host "  ✅ Backend tests passed" -ForegroundColor Green
    }
    Write-Host ""
} else {
    Write-Host "Step 2: Skipping tests" -ForegroundColor Yellow
    Write-Host ""
}

# Step 3: Lint Check
Write-Host "Step 3: Running linter..." -ForegroundColor Yellow
npm run lint
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ⚠️  Linting issues found. Consider fixing before publishing." -ForegroundColor Yellow
} else {
    Write-Host "  ✅ Linting passed" -ForegroundColor Green
}
Write-Host ""

# Step 4: Build Check
Write-Host "Step 4: Testing build..." -ForegroundColor Yellow
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Build failed" -ForegroundColor Red
    $errors++
} else {
    Write-Host "  ✅ Build successful" -ForegroundColor Green
}
Write-Host ""

# Summary
Write-Host "====================================" -ForegroundColor Cyan
if ($errors -eq 0) {
    Write-Host "✅ All checks passed! Ready to publish!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Review READY_TO_PUBLISH.md" -ForegroundColor White
    Write-Host "2. Commit and push your changes:" -ForegroundColor White
    Write-Host "   git add ." -ForegroundColor Gray
    Write-Host "   git commit -m 'docs: prepare for public release'" -ForegroundColor Gray
    Write-Host "   git push origin main" -ForegroundColor Gray
    Write-Host "3. Make repository public on GitHub" -ForegroundColor White
    Write-Host "4. Create v1.0.0 release" -ForegroundColor White
    Write-Host ""
    Write-Host "See PUBLISH_TO_GITHUB.md for detailed instructions" -ForegroundColor Cyan
} else {
    Write-Host "⚠️  Found $errors issue(s) - please fix before publishing" -ForegroundColor Red
    Write-Host ""
    Write-Host "Review the errors above and fix them." -ForegroundColor Yellow
    Write-Host "Then run this script again." -ForegroundColor Yellow
    exit 1
}
