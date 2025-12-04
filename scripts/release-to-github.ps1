# PEFT Studio - Enhanced GitHub Release Script
# This script handles the complete release process with automated GitHub release creation
#
# Features:
# - Automated release notes extraction from CHANGELOG.md
# - Asset upload with retry logic
# - Upload verification
# - Git tag creation and push
# - Comprehensive release summary
#
# Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 8.3, 8.5

param(
    [Parameter(Mandatory=$false)]
    [string]$Version = "",
    
    [switch]$SkipBuild = $false,
    [switch]$SkipTests = $false,
    [switch]$DryRun = $false,
    [switch]$Draft = $false,
    [switch]$Prerelease = $false,
    [switch]$SkipTag = $false
)

$ErrorActionPreference = "Stop"

Write-Host "=== PEFT Studio Enhanced GitHub Release ===" -ForegroundColor Cyan
Write-Host ""

# Validate GITHUB_TOKEN is set (unless dry run)
if (-not $DryRun -and -not $env:GITHUB_TOKEN) {
    Write-Host "ERROR: GITHUB_TOKEN environment variable not set!" -ForegroundColor Red
    Write-Host "Please set GITHUB_TOKEN with a GitHub personal access token." -ForegroundColor Yellow
    Write-Host "Example: `$env:GITHUB_TOKEN = 'your_token_here'" -ForegroundColor Yellow
    exit 1
}

# Step 1: Clean up unnecessary files
Write-Host "[1/9] Cleaning up unnecessary files..." -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "  [DRY RUN] Would run cleanup" -ForegroundColor Yellow
} else {
    if (Test-Path "$PSScriptRoot/prepare-release.ps1") {
        & "$PSScriptRoot/prepare-release.ps1"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Cleanup failed!" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "  Skipping cleanup (prepare-release.ps1 not found)" -ForegroundColor Yellow
    }
}

# Step 2: Run tests (unless skipped)
if (-not $SkipTests) {
    Write-Host ""
    Write-Host "[2/9] Running tests..." -ForegroundColor Cyan
    if ($DryRun) {
        Write-Host "  [DRY RUN] Would run: npm run test:run" -ForegroundColor Yellow
    } else {
        npm run test:run
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Tests failed!" -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host ""
    Write-Host "[2/9] Skipping tests..." -ForegroundColor Yellow
}

# Step 3: Build the application (unless skipped)
if (-not $SkipBuild) {
    Write-Host ""
    Write-Host "[3/9] Building application..." -ForegroundColor Cyan
    if ($DryRun) {
        Write-Host "  [DRY RUN] Would run: npm run build" -ForegroundColor Yellow
    } else {
        npm run build
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Build failed!" -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host ""
    Write-Host "[3/9] Skipping build..." -ForegroundColor Yellow
}

# Step 4: Package installers
Write-Host ""
Write-Host "[4/9] Packaging installers..." -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "  [DRY RUN] Would run: npm run package:all" -ForegroundColor Yellow
} else {
    if (-not $SkipBuild) {
        npm run package:all
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Packaging failed!" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "  Skipping packaging (build was skipped)" -ForegroundColor Yellow
    }
}

# Step 5: Generate checksums
Write-Host ""
Write-Host "[5/9] Generating checksums..." -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "  [DRY RUN] Would run: npm run generate:checksums" -ForegroundColor Yellow
} else {
    npm run generate:checksums
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Checksum generation failed!" -ForegroundColor Red
        exit 1
    }
}

# Step 6: Commit changes (optional)
Write-Host ""
Write-Host "[6/9] Committing changes..." -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "  [DRY RUN] Would run: git add . && git commit" -ForegroundColor Yellow
} else {
    # Check if there are changes to commit
    $gitStatus = git status --porcelain
    if ($gitStatus) {
        git add .
        git commit -m "chore: prepare release"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  WARNING: Commit failed (continuing anyway)" -ForegroundColor Yellow
        } else {
            Write-Host "  ✓ Changes committed" -ForegroundColor Green
        }
    } else {
        Write-Host "  No changes to commit" -ForegroundColor Yellow
    }
}

# Step 7: Create GitHub release with automated asset upload
Write-Host ""
Write-Host "[7/9] Creating GitHub release..." -ForegroundColor Cyan

# Build arguments for the release script
$releaseArgs = @()
if ($DryRun) {
    $releaseArgs += "--dry-run"
}
if ($Draft) {
    $releaseArgs += "--draft"
}
if ($Prerelease) {
    $releaseArgs += "--prerelease"
}
if ($SkipTag) {
    $releaseArgs += "--skip-tag"
}

# Run the release script
if ($releaseArgs.Count -gt 0) {
    node "$PSScriptRoot/release-to-github.js" $releaseArgs
} else {
    node "$PSScriptRoot/release-to-github.js"
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: GitHub release creation failed!" -ForegroundColor Red
    exit 1
}

# Step 8: Push changes to remote (if not dry run and not skipped)
if (-not $DryRun -and -not $SkipTag) {
    Write-Host ""
    Write-Host "[8/9] Pushing changes to remote..." -ForegroundColor Cyan
    
    # Check if there are commits to push
    $localCommits = git log origin/main..HEAD --oneline
    if ($localCommits) {
        git push origin main
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  WARNING: Push failed (tag was already pushed)" -ForegroundColor Yellow
        } else {
            Write-Host "  ✓ Changes pushed to remote" -ForegroundColor Green
        }
    } else {
        Write-Host "  No commits to push" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "[8/9] Skipping push to remote" -ForegroundColor Yellow
}

# Step 9: Final summary
Write-Host ""
Write-Host "[9/9] Release Complete!" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "=== DRY RUN COMPLETE ===" -ForegroundColor Yellow
    Write-Host "No actual changes were made." -ForegroundColor Yellow
    Write-Host "Run without -DryRun to perform the actual release." -ForegroundColor Yellow
} else {
    Write-Host "=== RELEASE SUCCESSFUL ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "The GitHub release has been created with all assets uploaded." -ForegroundColor Green
    Write-Host "Check the release at: https://github.com/Ankesh-007/peft-studio/releases" -ForegroundColor Cyan
}

Write-Host ""
