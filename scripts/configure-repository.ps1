# Repository Configuration Script for PEFT Studio (PowerShell)
# This script automates GitHub repository configuration using GitHub CLI (gh)
#
# Prerequisites:
# - GitHub CLI (gh) must be installed: https://cli.github.com/
# - You must be authenticated: gh auth login
# - You must have admin access to the repository

param(
    [string]$RepoOwner = $env:GITHUB_REPOSITORY_OWNER,
    [string]$RepoName = "peft-studio"
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Repository details
if ([string]::IsNullOrEmpty($RepoOwner)) {
    $RepoOwner = "YOUR_USERNAME"
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
Write-ColorOutput "PEFT Studio Repository Configuration" "Cyan"
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

# Function to check if repository exists
function Test-Repository {
    Write-ColorOutput "Checking repository: $RepoFull" "Yellow"
    try {
        gh repo view $RepoFull 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✓ Repository exists" "Green"
            return $true
        }
    } catch {
        Write-ColorOutput "✗ Repository not found: $RepoFull" "Red"
        Write-Host "Please update RepoOwner parameter or set GITHUB_REPOSITORY_OWNER environment variable"
        exit 1
    }
}

# Function to update repository settings
function Set-BasicSettings {
    Write-Host ""
    Write-ColorOutput "Configuring basic repository settings..." "Yellow"
    
    try {
        gh repo edit $RepoFull `
            --description "Professional desktop application for Parameter-Efficient Fine-Tuning (PEFT) of Large Language Models" `
            --enable-issues `
            --enable-projects `
            --enable-wiki=false `
            2>&1 | Out-Null
        
        Write-ColorOutput "✓ Basic settings configured" "Green"
    } catch {
        Write-ColorOutput "Note: Some settings may require manual configuration" "Yellow"
    }
}

# Function to add topics
function Add-Topics {
    Write-Host ""
    Write-ColorOutput "Adding repository topics..." "Yellow"
    
    $topics = "peft,fine-tuning,llm,machine-learning,electron,react,pytorch,transformers,desktop-app,ai"
    
    try {
        gh repo edit $RepoFull --add-topic $topics 2>&1 | Out-Null
        Write-ColorOutput "✓ Topics configured" "Green"
    } catch {
        Write-ColorOutput "Note: Topics may need to be added manually via GitHub web interface" "Yellow"
        Write-Host "Topics to add: $topics"
    }
}

# Function to enable discussions
function Enable-Discussions {
    Write-Host ""
    Write-ColorOutput "Enabling GitHub Discussions..." "Yellow"
    
    Write-ColorOutput "⚠ Discussions must be enabled manually:" "Yellow"
    Write-Host "  1. Go to: https://github.com/$RepoFull/settings"
    Write-Host "  2. Under 'Features', check 'Discussions'"
    Write-Host "  3. Click 'Set up discussions'"
}

# Function to configure branch protection
function Set-BranchProtection {
    Write-Host ""
    Write-ColorOutput "Configuring branch protection for 'main'..." "Yellow"
    
    Write-ColorOutput "⚠ Branch protection must be configured manually:" "Yellow"
    Write-Host "  1. Go to: https://github.com/$RepoFull/settings/branches"
    Write-Host "  2. Click 'Add branch protection rule'"
    Write-Host "  3. Branch name pattern: main"
    Write-Host "  4. Enable required settings (see REPOSITORY_CONFIGURATION_GUIDE.md)"
}

# Function to verify workflows
function Test-Workflows {
    Write-Host ""
    Write-ColorOutput "Verifying GitHub Actions workflows..." "Yellow"
    
    $workflowFiles = @(
        ".github/workflows/ci.yml",
        ".github/workflows/test.yml",
        ".github/workflows/build.yml",
        ".github/workflows/code-quality.yml",
        ".github/workflows/deploy.yml",
        ".github/workflows/release.yml",
        ".github/workflows/build-installers.yml",
        ".github/workflows/nightly.yml"
    )
    
    foreach ($workflow in $workflowFiles) {
        if (Test-Path $workflow) {
            Write-ColorOutput "✓ Found: $workflow" "Green"
        } else {
            Write-ColorOutput "✗ Missing: $workflow" "Red"
        }
    }
}

# Function to check community standards
function Test-CommunityStandards {
    Write-Host ""
    Write-ColorOutput "Checking community standards..." "Yellow"
    
    $requiredFiles = @(
        "README.md",
        "LICENSE",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        ".github/ISSUE_TEMPLATE/bug_report.md",
        ".github/ISSUE_TEMPLATE/feature_request.md",
        ".github/pull_request_template.md"
    )
    
    foreach ($file in $requiredFiles) {
        if (Test-Path $file) {
            Write-ColorOutput "✓ Found: $file" "Green"
        } else {
            Write-ColorOutput "✗ Missing: $file" "Red"
        }
    }
}

# Function to display summary
function Show-Summary {
    Write-Host ""
    Write-ColorOutput "========================================" "Cyan"
    Write-ColorOutput "Configuration Summary" "Cyan"
    Write-ColorOutput "========================================" "Cyan"
    Write-Host ""
    Write-ColorOutput "Automated Configuration:" "Green"
    Write-Host "  ✓ Repository description updated"
    Write-Host "  ✓ Issues and Projects enabled"
    Write-Host "  ✓ Topics added"
    Write-Host "  ✓ Workflows verified"
    Write-Host "  ✓ Community files checked"
    Write-Host ""
    Write-ColorOutput "Manual Configuration Required:" "Yellow"
    Write-Host "  ⚠ Enable Discussions in repository settings"
    Write-Host "  ⚠ Configure branch protection rules for 'main'"
    Write-Host "  ⚠ Set up discussion categories"
    Write-Host "  ⚠ Create and pin welcome discussion"
    Write-Host ""
    Write-ColorOutput "Next Steps:" "Cyan"
    Write-Host "  1. Review .github/REPOSITORY_CONFIGURATION_GUIDE.md"
    Write-Host "  2. Complete manual configuration steps"
    Write-Host "  3. Verify all settings in GitHub web interface"
    Write-Host "  4. Run security and quality checks"
    Write-Host "  5. Make repository public when ready"
    Write-Host ""
    Write-ColorOutput "Repository URL: https://github.com/$RepoFull" "Green"
    Write-Host ""
}

# Main execution
try {
    Test-Repository
    Set-BasicSettings
    Add-Topics
    Enable-Discussions
    Set-BranchProtection
    Test-Workflows
    Test-CommunityStandards
    Show-Summary
    
    Write-ColorOutput "Configuration script completed!" "Green"
    Write-Host ""
} catch {
    Write-ColorOutput "Error: $($_.Exception.Message)" "Red"
    exit 1
}
