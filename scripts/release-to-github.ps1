# PEFT Studio - Complete Release to GitHub Script
# This script handles the entire release process

param(
    [Parameter(Mandatory=$false)]
    [string]$Version = "1.0.1",
    
    [switch]$SkipBuild = $false,
    [switch]$SkipTests = $false,
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"

Write-Host "=== PEFT Studio Release to GitHub ===" -ForegroundColor Cyan
Write-Host "Version: $Version" -ForegroundColor Yellow
Write-Host ""

# Step 1: Clean up unnecessary files
Write-Host "[1/8] Cleaning up unnecessary files..." -ForegroundColor Cyan
if ($DryRun) {
    & "$PSScriptRoot/prepare-release.ps1" -DryRun
} else {
    & "$PSScriptRoot/prepare-release.ps1"
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Cleanup failed!" -ForegroundColor Red
    exit 1
}

# Step 2: Run tests (unless skipped)
if (-not $SkipTests) {
    Write-Host ""
    Write-Host "[2/8] Running tests..." -ForegroundColor Cyan
    npm run test:run
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Tests failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "[2/8] Skipping tests..." -ForegroundColor Yellow
}

# Step 3: Build the application (unless skipped)
if (-not $SkipBuild) {
    Write-Host ""
    Write-Host "[3/8] Building application..." -ForegroundColor Cyan
    npm run build
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Build failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "[3/8] Skipping build..." -ForegroundColor Yellow
}

# Step 4: Package installers
Write-Host ""
Write-Host "[4/8] Packaging installers..." -ForegroundColor Cyan
if (-not $DryRun) {
    npm run package:all
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Packaging failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  [DRY RUN] Would run: npm run package:all" -ForegroundColor Yellow
}

# Step 5: Generate checksums
Write-Host ""
Write-Host "[5/8] Generating checksums..." -ForegroundColor Cyan
if (-not $DryRun) {
    npm run generate:checksums
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Checksum generation failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  [DRY RUN] Would run: npm run generate:checksums" -ForegroundColor Yellow
}

# Step 6: Commit changes
Write-Host ""
Write-Host "[6/8] Committing changes..." -ForegroundColor Cyan
if (-not $DryRun) {
    git add .
    git commit -m "chore: prepare v$Version release"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: Commit failed (maybe no changes?)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [DRY RUN] Would run: git add . && git commit -m 'chore: prepare v$Version release'" -ForegroundColor Yellow
}

# Step 7: Create and push tag
Write-Host ""
Write-Host "[7/8] Creating and pushing tag..." -ForegroundColor Cyan
if (-not $DryRun) {
    git tag -a "v$Version" -m "Release v$Version"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Tag creation failed!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "  Pushing to origin..." -ForegroundColor Cyan
    git push origin main --tags
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Push failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  [DRY RUN] Would run: git tag -a v$Version -m 'Release v$Version'" -ForegroundColor Yellow
    Write-Host "  [DRY RUN] Would run: git push origin main --tags" -ForegroundColor Yellow
}

# Step 8: Summary
Write-Host ""
Write-Host "[8/8] Release Summary" -ForegroundColor Cyan
Write-Host "  Version: v$Version" -ForegroundColor Green
Write-Host "  Status: " -NoNewline
if ($DryRun) {
    Write-Host "DRY RUN COMPLETE" -ForegroundColor Yellow
} else {
    Write-Host "RELEASED" -ForegroundColor Green
}
Write-Host ""

if (-not $DryRun) {
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Go to: https://github.com/Ankesh-007/peft-studio/releases" -ForegroundColor White
    Write-Host "  2. Find the v$Version tag" -ForegroundColor White
    Write-Host "  3. Click 'Create release from tag'" -ForegroundColor White
    Write-Host "  4. Upload installers from the 'release/' directory" -ForegroundColor White
    Write-Host "  5. Upload checksums file" -ForegroundColor White
    Write-Host "  6. Publish the release" -ForegroundColor White
} else {
    Write-Host "Run without -DryRun to actually perform the release." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Release process complete!" -ForegroundColor Green
