# Verify Branch Protection Script for PEFT Studio (PowerShell)
# This script checks if branch protection rules are properly configured

param(
    [string]$RepoOwner = $env:GITHUB_REPOSITORY_OWNER,
    [string]$RepoName = "peft-studio",
    [string]$Branch = "main"
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Repository details
if ([string]::IsNullOrEmpty($RepoOwner)) {
    $RepoOwner = "Ankesh-007"
}
$RepoFull = "$RepoOwner/$RepoName"

# Colors for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "Branch Protection Verification" "Cyan"
Write-ColorOutput "========================================" "Cyan"
Write-Host ""

# Check if gh is installed
try {
    $null = Get-Command gh -ErrorAction Stop
    Write-ColorOutput "✓ GitHub CLI is installed" "Green"
} catch {
    Write-ColorOutput "Error: GitHub CLI (gh) is not installed" "Red"
    Write-Host "Please install it from: https://cli.github.com/"
    exit 1
}

# Check if authenticated
try {
    gh auth status 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Not authenticated"
    }
    Write-ColorOutput "✓ Authenticated with GitHub CLI" "Green"
} catch {
    Write-ColorOutput "Error: Not authenticated with GitHub CLI" "Red"
    Write-Host "Please run: gh auth login"
    exit 1
}

Write-Host ""

# Check if repository exists
Write-ColorOutput "Checking repository: $RepoFull" "Yellow"
try {
    gh repo view $RepoFull 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Repository not found"
    }
    Write-ColorOutput "✓ Repository exists" "Green"
} catch {
    Write-ColorOutput "✗ Repository not found: $RepoFull" "Red"
    Write-Host "Please update RepoOwner parameter or set GITHUB_REPOSITORY_OWNER environment variable"
    exit 1
}

Write-Host ""

# Check branch protection
Write-ColorOutput "Checking branch protection for '$Branch'..." "Yellow"

try {
    $protectionJson = gh api "repos/$RepoFull/branches/$Branch/protection" 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        throw "Branch protection not configured"
    }
    
    Write-ColorOutput "✓ Branch protection is configured" "Green"
    Write-Host ""
    
    # Parse protection details
    $protection = $protectionJson | ConvertFrom-Json
    
    Write-ColorOutput "Protection Details:" "Cyan"
    
    # Check required pull request reviews
    if ($protection.required_pull_request_reviews) {
        Write-ColorOutput "✓ Required pull request reviews enabled" "Green"
        Write-Host "  - Required approvals: $($protection.required_pull_request_reviews.required_approving_review_count)"
        
        if ($protection.required_pull_request_reviews.dismiss_stale_reviews) {
            Write-ColorOutput "  - ✓ Dismiss stale reviews enabled" "Green"
        } else {
            Write-ColorOutput "  - ⚠ Dismiss stale reviews not enabled" "Yellow"
        }
    } else {
        Write-ColorOutput "⚠ Required pull request reviews not configured" "Yellow"
    }
    
    # Check required status checks
    if ($protection.required_status_checks) {
        Write-ColorOutput "✓ Required status checks enabled" "Green"
        
        if ($protection.required_status_checks.strict) {
            Write-ColorOutput "  - ✓ Require branches to be up to date" "Green"
        } else {
            Write-ColorOutput "  - ⚠ Branches not required to be up to date" "Yellow"
        }
        
        if ($protection.required_status_checks.contexts) {
            Write-Host "  - Required checks: $($protection.required_status_checks.contexts -join ', ')"
        }
    } else {
        Write-ColorOutput "⚠ Required status checks not configured" "Yellow"
    }
    
    # Check enforce admins
    if ($protection.enforce_admins -and $protection.enforce_admins.enabled) {
        Write-ColorOutput "✓ Enforce admins enabled" "Green"
    } else {
        Write-ColorOutput "⚠ Enforce admins not enabled" "Yellow"
    }
    
    # Check required conversation resolution
    if ($protection.required_conversation_resolution -and $protection.required_conversation_resolution.enabled) {
        Write-ColorOutput "✓ Required conversation resolution enabled" "Green"
    } else {
        Write-ColorOutput "⚠ Required conversation resolution not configured" "Yellow"
    }
    
} catch {
    Write-ColorOutput "✗ Branch protection is NOT configured for '$Branch'" "Red"
    Write-Host ""
    Write-ColorOutput "To configure branch protection:" "Yellow"
    Write-Host "1. Go to: https://github.com/$RepoFull/settings/branches"
    Write-Host "2. Click 'Add branch protection rule'"
    Write-Host "3. Branch name pattern: $Branch"
    Write-Host "4. Enable the following:"
    Write-Host "   - Require a pull request before merging"
    Write-Host "   - Require approvals (at least 1)"
    Write-Host "   - Require status checks to pass before merging"
    Write-Host "   - Require branches to be up to date before merging"
    Write-Host "   - Require conversation resolution before merging"
    Write-Host "   - Include administrators"
    Write-Host ""
    Write-Host "See .github/REPOSITORY_CONFIGURATION_GUIDE.md for detailed instructions"
    exit 1
}

Write-Host ""

# Check for required workflows
Write-ColorOutput "Checking required workflow files..." "Yellow"

$requiredWorkflows = @(
    ".github/workflows/ci.yml",
    ".github/workflows/test.yml",
    ".github/workflows/build.yml",
    ".github/workflows/code-quality.yml"
)

$missingWorkflows = 0
foreach ($workflow in $requiredWorkflows) {
    if (Test-Path $workflow) {
        Write-ColorOutput "✓ Found: $workflow" "Green"
    } else {
        Write-ColorOutput "✗ Missing: $workflow" "Red"
        $missingWorkflows++
    }
}

if ($missingWorkflows -gt 0) {
    Write-Host ""
    Write-ColorOutput "⚠ $missingWorkflows required workflow(s) missing" "Yellow"
    Write-Host "These workflows should be present and added as required status checks"
}

Write-Host ""

# Summary
Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "Verification Summary" "Cyan"
Write-ColorOutput "========================================" "Cyan"
Write-Host ""

if ($LASTEXITCODE -eq 0 -and $missingWorkflows -eq 0) {
    Write-ColorOutput "✓ Branch protection is properly configured" "Green"
    Write-ColorOutput "✓ All required workflows are present" "Green"
    Write-Host ""
    Write-Host "Repository: https://github.com/$RepoFull"
    Write-Host "Branch protection: https://github.com/$RepoFull/settings/branch_protection_rules"
    Write-Host ""
    Write-ColorOutput "Branch protection verification passed!" "Green"
} else {
    Write-ColorOutput "⚠ Some configuration issues detected" "Yellow"
    Write-Host ""
    Write-Host "Please review the details above and:"
    Write-Host "1. Configure missing branch protection rules"
    Write-Host "2. Add missing workflow files"
    Write-Host "3. Re-run this script to verify"
    Write-Host ""
    Write-Host "See .github/REPOSITORY_CONFIGURATION_GUIDE.md for detailed instructions"
}

Write-Host ""
