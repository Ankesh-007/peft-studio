# PEFT Studio - Prepare Release Script
# This script cleans up unnecessary files and prepares for release

param(
    [switch]$DryRun = $false
)

Write-Host "=== PEFT Studio Release Preparation ===" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Files and directories to remove
$itemsToRemove = @(
    # Build artifacts
    "release/win-unpacked",
    "release/builder-debug.yml",
    "release/builder-effective-config.yaml",
    "dist/assets",
    "dist/samples",
    "dist/index.html",
    "dist/stats.html",
    "build/signing-status-macos.txt",
    "build/signing-status.txt",
    
    # Backend cache and temporary files
    "backend/.hypothesis",
    "backend/.pytest_cache",
    "backend/__pycache__",
    "backend/data/cache",
    "backend/data/peft_studio.db",
    "backend/data/security_audit.log",
    "backend/artifacts",
    "backend/checkpoints",
    
    # Node modules cache (will be reinstalled)
    ".vite",
    
    # Spec documentation (keep only essential)
    ".kiro/specs/peft-application-fix/RELEASE_PUBLICATION_GUIDE.md",
    ".kiro/specs/peft-application-fix/RELEASE_NOTES_v1.0.1.md",
    ".kiro/specs/peft-application-fix/FINAL_CHECKPOINT_VERIFICATION.md",
    ".kiro/specs/peft-application-fix/RELEASE_1.0.1_SUMMARY.md",
    ".kiro/specs/peft-application-fix/GITHUB_RELEASE_GUIDE.md",
    ".kiro/specs/peft-application-fix/INSTALLER_TESTING_GUIDE.md"
)

# Count items
$totalItems = $itemsToRemove.Count
$removedCount = 0
$skippedCount = 0

Write-Host "Found $totalItems items to clean up" -ForegroundColor Yellow
Write-Host ""

if ($DryRun) {
    Write-Host "DRY RUN MODE - No files will be deleted" -ForegroundColor Magenta
    Write-Host ""
}

foreach ($item in $itemsToRemove) {
    if (Test-Path $item) {
        $size = if (Test-Path $item -PathType Container) {
            $folderSize = (Get-ChildItem -Path $item -Recurse -File | Measure-Object -Property Length -Sum).Sum
            if ($folderSize) { "$([math]::Round($folderSize / 1MB, 2)) MB" } else { "0 MB" }
        } else {
            $fileSize = (Get-Item $item).Length
            "$([math]::Round($fileSize / 1KB, 2)) KB"
        }
        
        Write-Host "  [REMOVE] $item ($size)" -ForegroundColor Red
        
        if (-not $DryRun) {
            try {
                Remove-Item -Path $item -Recurse -Force -ErrorAction Stop
                $removedCount++
            } catch {
                Write-Host "    [ERROR] Failed to remove: $_" -ForegroundColor DarkRed
                $skippedCount++
            }
        }
    } else {
        Write-Host "  [SKIP] $item (not found)" -ForegroundColor DarkGray
        $skippedCount++
    }
}

Write-Host ""
Write-Host "=== Cleanup Summary ===" -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "  Would remove: $removedCount items" -ForegroundColor Yellow
} else {
    Write-Host "  Removed: $removedCount items" -ForegroundColor Green
}
Write-Host "  Skipped: $skippedCount items" -ForegroundColor Gray
Write-Host ""

# Verify critical files still exist
Write-Host "=== Verifying Critical Files ===" -ForegroundColor Cyan
$criticalFiles = @(
    "package.json",
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "electron/main.js",
    "backend/main.py",
    "backend/requirements.txt",
    "build/.gitkeep",
    "build/README.md"
)

$allCriticalExist = $true
foreach ($file in $criticalFiles) {
    if (Test-Path $file) {
        Write-Host "  [OK] $file" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] $file" -ForegroundColor Red
        $allCriticalExist = $false
    }
}

Write-Host ""

if (-not $allCriticalExist) {
    Write-Host "ERROR: Some critical files are missing!" -ForegroundColor Red
    exit 1
}

if ($DryRun) {
    Write-Host "Dry run complete. Run without -DryRun to actually remove files." -ForegroundColor Yellow
} else {
    Write-Host "Cleanup complete! Ready for release." -ForegroundColor Green
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Run: npm run build" -ForegroundColor White
Write-Host "  2. Run: npm run package:all" -ForegroundColor White
Write-Host "  3. Run: npm run generate:checksums" -ForegroundColor White
Write-Host "  4. Commit changes: git add . && git commit -m 'chore: prepare v1.0.1 release'" -ForegroundColor White
Write-Host "  5. Create tag: git tag -a v1.0.1 -m 'Release v1.0.1'" -ForegroundColor White
Write-Host "  6. Push: git push origin main --tags" -ForegroundColor White
Write-Host ""
