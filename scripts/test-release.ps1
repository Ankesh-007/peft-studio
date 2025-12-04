#!/usr/bin/env pwsh
# Test Release Script
# This script helps automate parts of the release testing process

param(
    [Parameter(Mandatory=$false)]
    [string]$Version = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$CheckWorkflow,
    
    [Parameter(Mandatory=$false)]
    [switch]$VerifyAssets,
    
    [Parameter(Mandatory=$false)]
    [switch]$VerifyChecksums,
    
    [Parameter(Mandatory=$false)]
    [switch]$All
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }

# Configuration
$REPO_OWNER = "Ankesh-007"
$REPO_NAME = "peft-studio"
$GITHUB_API = "https://api.github.com"

function Get-LatestTestRelease {
    Write-Info "Fetching latest test release..."
    
    try {
        $releases = Invoke-RestMethod -Uri "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/releases" -Method Get
        $testReleases = $releases | Where-Object { $_.tag_name -like "*-test*" }
        
        if ($testReleases.Count -eq 0) {
            Write-Warning "No test releases found"
            return $null
        }
        
        $latest = $testReleases[0]
        Write-Success "Found test release: $($latest.tag_name)"
        return $latest
    }
    catch {
        Write-Error "Failed to fetch releases: $_"
        return $null
    }
}

function Test-WorkflowStatus {
    param($TagName)
    
    Write-Info "Checking workflow status for $TagName..."
    
    try {
        $workflows = Invoke-RestMethod -Uri "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/actions/runs?event=push" -Method Get
        $releaseWorkflows = $workflows.workflow_runs | Where-Object { 
            $_.name -eq "Release" -and $_.head_branch -eq $TagName 
        }
        
        if ($releaseWorkflows.Count -eq 0) {
            Write-Warning "No workflow runs found for $TagName"
            return $false
        }
        
        $workflow = $releaseWorkflows[0]
        
        Write-Info "Workflow Status: $($workflow.status)"
        Write-Info "Conclusion: $($workflow.conclusion)"
        Write-Info "URL: $($workflow.html_url)"
        
        if ($workflow.status -eq "completed" -and $workflow.conclusion -eq "success") {
            Write-Success "Workflow completed successfully"
            return $true
        }
        elseif ($workflow.status -eq "in_progress") {
            Write-Warning "Workflow is still in progress"
            return $false
        }
        else {
            Write-Error "Workflow failed or was cancelled"
            return $false
        }
    }
    catch {
        Write-Error "Failed to check workflow status: $_"
        return $false
    }
}

function Test-ReleaseAssets {
    param($Release)
    
    Write-Info "Verifying release assets..."
    
    $expectedAssets = @(
        "PEFT-Studio-Setup-*.exe",
        "PEFT-Studio-*-portable.exe",
        "PEFT-Studio-*.dmg",
        "PEFT-Studio-*-mac.zip",
        "PEFT-Studio-*.AppImage",
        "peft-studio_*_amd64.deb",
        "SHA256SUMS.txt"
    )
    
    $assets = $Release.assets
    $allFound = $true
    
    foreach ($pattern in $expectedAssets) {
        $found = $assets | Where-Object { $_.name -like $pattern }
        
        if ($found) {
            Write-Success "Found: $($found.name) ($([math]::Round($found.size / 1MB, 2)) MB)"
        }
        else {
            Write-Error "Missing: $pattern"
            $allFound = $false
        }
    }
    
    if ($allFound) {
        Write-Success "All expected assets are present"
    }
    else {
        Write-Error "Some assets are missing"
    }
    
    return $allFound
}

function Test-Checksums {
    param($Release)
    
    Write-Info "Verifying checksums..."
    
    # Find SHA256SUMS.txt asset
    $checksumsAsset = $Release.assets | Where-Object { $_.name -eq "SHA256SUMS.txt" }
    
    if (-not $checksumsAsset) {
        Write-Error "SHA256SUMS.txt not found in release assets"
        return $false
    }
    
    Write-Success "Found SHA256SUMS.txt"
    
    # Download checksums file
    $tempDir = Join-Path $env:TEMP "peft-studio-test"
    New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
    
    $checksumsPath = Join-Path $tempDir "SHA256SUMS.txt"
    
    try {
        Write-Info "Downloading SHA256SUMS.txt..."
        Invoke-WebRequest -Uri $checksumsAsset.browser_download_url -OutFile $checksumsPath
        
        # Read and display checksums
        $checksums = Get-Content $checksumsPath
        Write-Info "Checksums file contains $($checksums.Count) entries:"
        
        foreach ($line in $checksums) {
            if ($line.Trim()) {
                $parts = $line -split '\s+', 2
                if ($parts.Count -eq 2) {
                    Write-Host "  $($parts[1]): $($parts[0].Substring(0, 16))..." -ForegroundColor Gray
                }
            }
        }
        
        Write-Success "Checksums file is valid"
        return $true
    }
    catch {
        Write-Error "Failed to download or parse checksums: $_"
        return $false
    }
    finally {
        # Cleanup
        if (Test-Path $tempDir) {
            Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

function Test-ReleaseNotes {
    param($Release)
    
    Write-Info "Verifying release notes..."
    
    $body = $Release.body
    
    $requiredSections = @(
        "Downloads",
        "Installation",
        "Windows",
        "macOS",
        "Linux",
        "Checksums",
        "System Requirements"
    )
    
    $allFound = $true
    
    foreach ($section in $requiredSections) {
        if ($body -match $section) {
            Write-Success "Found section: $section"
        }
        else {
            Write-Warning "Missing section: $section"
            $allFound = $false
        }
    }
    
    if ($allFound) {
        Write-Success "All required sections are present in release notes"
    }
    else {
        Write-Warning "Some sections are missing from release notes"
    }
    
    return $allFound
}

function Show-TestChecklist {
    param($Release)
    
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  Release Testing Checklist" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Release: $($Release.tag_name)" -ForegroundColor Yellow
    Write-Host "URL: $($Release.html_url)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Manual Testing Required:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  [ ] Download Windows installer" -ForegroundColor White
    Write-Host "  [ ] Verify Windows installer checksum" -ForegroundColor White
    Write-Host "  [ ] Test Windows installation wizard" -ForegroundColor White
    Write-Host "  [ ] Verify Windows shortcuts created" -ForegroundColor White
    Write-Host "  [ ] Test Windows portable version" -ForegroundColor White
    Write-Host ""
    Write-Host "  [ ] Download macOS DMG" -ForegroundColor White
    Write-Host "  [ ] Verify macOS DMG checksum" -ForegroundColor White
    Write-Host "  [ ] Test macOS drag-and-drop installation" -ForegroundColor White
    Write-Host "  [ ] Verify macOS application signature (if signed)" -ForegroundColor White
    Write-Host "  [ ] Test macOS ZIP archive" -ForegroundColor White
    Write-Host ""
    Write-Host "  [ ] Download Linux AppImage" -ForegroundColor White
    Write-Host "  [ ] Verify Linux AppImage checksum" -ForegroundColor White
    Write-Host "  [ ] Test Linux AppImage execution" -ForegroundColor White
    Write-Host "  [ ] Verify Linux desktop integration" -ForegroundColor White
    Write-Host "  [ ] Test Linux DEB package installation" -ForegroundColor White
    Write-Host ""
    Write-Host "  [ ] Test auto-update mechanism" -ForegroundColor White
    Write-Host "  [ ] Verify update notification appears" -ForegroundColor White
    Write-Host "  [ ] Test update download and installation" -ForegroundColor White
    Write-Host "  [ ] Verify application restarts with new version" -ForegroundColor White
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Documentation:" -ForegroundColor Cyan
    Write-Host "  - Test Release Process: docs/developer-guide/test-release-process.md" -ForegroundColor Gray
    Write-Host "  - Windows Testing: docs/developer-guide/test-windows-installer.md" -ForegroundColor Gray
    Write-Host "  - macOS Testing: docs/developer-guide/test-macos-installer.md" -ForegroundColor Gray
    Write-Host "  - Linux Testing: docs/developer-guide/test-linux-installer.md" -ForegroundColor Gray
    Write-Host "  - Auto-Update Testing: docs/developer-guide/test-auto-update.md" -ForegroundColor Gray
    Write-Host ""
}

# Main execution
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  PEFT Studio Release Testing Script" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Get release to test
$release = $null

if ($Version) {
    Write-Info "Fetching release for version $Version..."
    try {
        $release = Invoke-RestMethod -Uri "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/releases/tags/$Version" -Method Get
        Write-Success "Found release: $Version"
    }
    catch {
        Write-Error "Failed to fetch release $Version: $_"
        exit 1
    }
}
else {
    $release = Get-LatestTestRelease
    if (-not $release) {
        Write-Error "No test release found. Please create a test release first."
        exit 1
    }
}

# Run tests based on parameters
$allPassed = $true

if ($All -or $CheckWorkflow) {
    Write-Host ""
    if (-not (Test-WorkflowStatus -TagName $release.tag_name)) {
        $allPassed = $false
    }
}

if ($All -or $VerifyAssets) {
    Write-Host ""
    if (-not (Test-ReleaseAssets -Release $release)) {
        $allPassed = $false
    }
}

if ($All -or $VerifyChecksums) {
    Write-Host ""
    if (-not (Test-Checksums -Release $release)) {
        $allPassed = $false
    }
}

if ($All) {
    Write-Host ""
    Test-ReleaseNotes -Release $release | Out-Null
}

# Show checklist
Write-Host ""
Show-TestChecklist -Release $release

# Summary
Write-Host ""
if ($allPassed) {
    Write-Success "Automated tests passed! Proceed with manual testing."
}
else {
    Write-Error "Some automated tests failed. Review the output above."
    exit 1
}

Write-Host ""
