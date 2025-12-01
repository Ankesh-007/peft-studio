# Verify GitHub Actions Workflows Script for PEFT Studio (PowerShell)
# This script validates that all required workflow files exist and are properly configured

# Set error action preference
$ErrorActionPreference = "Continue"

# Colors for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "GitHub Actions Workflow Verification" "Cyan"
Write-ColorOutput "========================================" "Cyan"
Write-Host ""

# Required workflow files
$requiredWorkflows = @(
    ".github/workflows/ci.yml",
    ".github/workflows/test.yml",
    ".github/workflows/build.yml",
    ".github/workflows/code-quality.yml",
    ".github/workflows/deploy.yml",
    ".github/workflows/release.yml",
    ".github/workflows/build-installers.yml",
    ".github/workflows/nightly.yml"
)

# Optional but recommended workflows
$optionalWorkflows = @(
    ".github/workflows/verify-branch-protection.yml"
)

# Check for required workflows
Write-ColorOutput "Checking required workflow files..." "Yellow"
$missingRequired = 0
foreach ($workflow in $requiredWorkflows) {
    if (Test-Path $workflow) {
        Write-ColorOutput "✓ Found: $workflow" "Green"
    } else {
        Write-ColorOutput "✗ Missing: $workflow" "Red"
        $missingRequired++
    }
}

Write-Host ""

# Check for optional workflows
Write-ColorOutput "Checking optional workflow files..." "Yellow"
foreach ($workflow in $optionalWorkflows) {
    if (Test-Path $workflow) {
        Write-ColorOutput "✓ Found: $workflow" "Green"
    } else {
        Write-ColorOutput "ℹ Optional: $workflow (not present)" "Yellow"
    }
}

Write-Host ""

# Validate YAML syntax (basic check)
Write-ColorOutput "Validating YAML syntax (basic)..." "Yellow"
$yamlErrors = 0
foreach ($workflow in $requiredWorkflows) {
    if (Test-Path $workflow) {
        $content = Get-Content $workflow -Raw
        
        # Basic YAML validation checks
        $hasName = $content -match "name:"
        $hasOn = $content -match "on:"
        $hasJobs = $content -match "jobs:"
        
        if ($hasName -and $hasOn -and $hasJobs) {
            Write-ColorOutput "✓ Valid structure: $workflow" "Green"
        } else {
            Write-ColorOutput "✗ Invalid structure: $workflow" "Red"
            $yamlErrors++
        }
    }
}

Write-Host ""

# Check workflow triggers
Write-ColorOutput "Checking workflow triggers..." "Yellow"
foreach ($workflow in $requiredWorkflows) {
    if (Test-Path $workflow) {
        $filename = Split-Path $workflow -Leaf
        $content = Get-Content $workflow -Raw
        
        # Check for push trigger
        if ($content -match "push:") {
            Write-ColorOutput "✓ $filename has push trigger" "Green"
        } else {
            Write-ColorOutput "⚠ $filename missing push trigger" "Yellow"
        }
        
        # Check for pull_request trigger
        if ($content -match "pull_request:") {
            Write-ColorOutput "✓ $filename has pull_request trigger" "Green"
        } else {
            Write-ColorOutput "⚠ $filename missing pull_request trigger" "Yellow"
        }
    }
}

Write-Host ""

# Check for workflow_dispatch (manual trigger)
Write-ColorOutput "Checking for manual trigger support..." "Yellow"
foreach ($workflow in $requiredWorkflows) {
    if (Test-Path $workflow) {
        $filename = Split-Path $workflow -Leaf
        $content = Get-Content $workflow -Raw
        
        if ($content -match "workflow_dispatch:") {
            Write-ColorOutput "✓ $filename supports manual trigger" "Green"
        } else {
            Write-ColorOutput "ℹ $filename does not support manual trigger" "Yellow"
        }
    }
}

Write-Host ""

# Check for required jobs in CI workflow
if (Test-Path ".github/workflows/ci.yml") {
    Write-ColorOutput "Checking CI workflow jobs..." "Yellow"
    
    $ciContent = Get-Content ".github/workflows/ci.yml" -Raw
    $requiredJobs = @("lint", "test", "build")
    
    foreach ($job in $requiredJobs) {
        $pattern = "  ${job}:"
        if ($ciContent -match $pattern) {
            Write-ColorOutput "✓ CI workflow has '$job' job" "Green"
        } else {
            Write-ColorOutput "✗ CI workflow missing '$job' job" "Red"
        }
    }
    Write-Host ""
}

# Check for GitHub Actions directory structure
Write-ColorOutput "Checking GitHub Actions directory structure..." "Yellow"

if (Test-Path ".github") {
    Write-ColorOutput "✓ .github directory exists" "Green"
} else {
    Write-ColorOutput "✗ .github directory missing" "Red"
}

if (Test-Path ".github/workflows") {
    Write-ColorOutput "✓ .github/workflows directory exists" "Green"
} else {
    Write-ColorOutput "✗ .github/workflows directory missing" "Red"
}

if (Test-Path ".github/ISSUE_TEMPLATE") {
    Write-ColorOutput "✓ .github/ISSUE_TEMPLATE directory exists" "Green"
} else {
    Write-ColorOutput "⚠ .github/ISSUE_TEMPLATE directory missing" "Yellow"
}

if (Test-Path ".github/pull_request_template.md") {
    Write-ColorOutput "✓ Pull request template exists" "Green"
} else {
    Write-ColorOutput "⚠ Pull request template missing" "Yellow"
}

Write-Host ""

# Summary
Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "Verification Summary" "Cyan"
Write-ColorOutput "========================================" "Cyan"
Write-Host ""

if ($missingRequired -eq 0) {
    Write-ColorOutput "✓ All required workflow files are present" "Green"
} else {
    Write-ColorOutput "✗ $missingRequired required workflow file(s) missing" "Red"
}

if ($yamlErrors -gt 0) {
    Write-ColorOutput "✗ $yamlErrors workflow file(s) have structure issues" "Red"
}

Write-Host ""

if ($missingRequired -eq 0 -and $yamlErrors -eq 0) {
    Write-ColorOutput "Workflow verification passed!" "Green"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "1. Push changes to trigger workflows"
    Write-Host "2. Monitor workflow runs in GitHub Actions tab"
    Write-Host "3. Add successful workflows as required status checks in branch protection"
    exit 0
} else {
    Write-ColorOutput "Workflow verification failed!" "Red"
    Write-Host ""
    Write-Host "Please:"
    Write-Host "1. Add missing workflow files"
    Write-Host "2. Fix structure issues"
    Write-Host "3. Re-run this script to verify"
    exit 1
}
