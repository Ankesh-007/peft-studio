# PEFT Studio - GitHub Push Script
# This script helps you push your code to GitHub

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PEFT Studio - GitHub Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "Error: Git repository not initialized!" -ForegroundColor Red
    Write-Host "Run: git init" -ForegroundColor Yellow
    exit 1
}

# Check if there are any commits
$commits = git rev-list --all --count 2>$null
if ($commits -eq 0) {
    Write-Host "Error: No commits found!" -ForegroundColor Red
    Write-Host "Run: git add . && git commit -m 'Initial commit'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Current commits: $commits" -ForegroundColor Green
Write-Host ""

# Check if remote already exists
$remoteUrl = git remote get-url origin 2>$null
if ($remoteUrl) {
    Write-Host "Remote 'origin' already exists:" -ForegroundColor Yellow
    Write-Host "  $remoteUrl" -ForegroundColor White
    Write-Host ""
    $response = Read-Host "Do you want to change it? (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        git remote remove origin
        Write-Host "Remote removed." -ForegroundColor Green
    } else {
        Write-Host "Keeping existing remote." -ForegroundColor Green
        Write-Host ""
        Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
        git push -u origin master
        exit 0
    }
}

# Prompt for GitHub username
Write-Host "Enter your GitHub username:" -ForegroundColor Cyan
$username = Read-Host

if ([string]::IsNullOrWhiteSpace($username)) {
    Write-Host "Error: Username cannot be empty!" -ForegroundColor Red
    exit 1
}

# Prompt for repository name
Write-Host ""
Write-Host "Enter repository name (default: peft-studio):" -ForegroundColor Cyan
$repoName = Read-Host
if ([string]::IsNullOrWhiteSpace($repoName)) {
    $repoName = "peft-studio"
}

# Construct repository URL
$repoUrl = "https://github.com/$username/$repoName.git"

Write-Host ""
Write-Host "Repository URL: $repoUrl" -ForegroundColor Yellow
Write-Host ""

# Ask for confirmation
$response = Read-Host "Is this correct? (Y/n)"
if ($response -eq "n" -or $response -eq "N") {
    Write-Host "Aborted." -ForegroundColor Red
    exit 1
}

# Add remote
Write-Host ""
Write-Host "Adding remote 'origin'..." -ForegroundColor Cyan
git remote add origin $repoUrl

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to add remote!" -ForegroundColor Red
    exit 1
}

Write-Host "Remote added successfully!" -ForegroundColor Green
Write-Host ""

# Verify remote
Write-Host "Verifying remote..." -ForegroundColor Cyan
git remote -v
Write-Host ""

# Ask about branch name
Write-Host "Choose default branch name:" -ForegroundColor Cyan
Write-Host "  1. master (current)" -ForegroundColor White
Write-Host "  2. main (GitHub default)" -ForegroundColor White
$branchChoice = Read-Host "Enter choice (1/2)"

$branchName = "master"
if ($branchChoice -eq "2") {
    Write-Host "Renaming branch to 'main'..." -ForegroundColor Cyan
    git branch -M main
    $branchName = "main"
    Write-Host "Branch renamed to 'main'" -ForegroundColor Green
}

Write-Host ""
Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
Write-Host "Branch: $branchName" -ForegroundColor Yellow
Write-Host ""

# Push to GitHub
git push -u origin $branchName

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Success! Code pushed to GitHub!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "View your repository at:" -ForegroundColor Cyan
    Write-Host "  https://github.com/$username/$repoName" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Add a description to your repository" -ForegroundColor White
    Write-Host "  2. Add topics/tags for discoverability" -ForegroundColor White
    Write-Host "  3. Consider adding a LICENSE file" -ForegroundColor White
    Write-Host "  4. Star your own repo! ⭐" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  Error: Failed to push to GitHub!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  1. Repository doesn't exist on GitHub" -ForegroundColor White
    Write-Host "     → Create it at: https://github.com/new" -ForegroundColor White
    Write-Host ""
    Write-Host "  2. Authentication failed" -ForegroundColor White
    Write-Host "     → Use a Personal Access Token as password" -ForegroundColor White
    Write-Host "     → Generate at: https://github.com/settings/tokens" -ForegroundColor White
    Write-Host ""
    Write-Host "  3. Permission denied" -ForegroundColor White
    Write-Host "     → Check repository permissions" -ForegroundColor White
    Write-Host ""
    exit 1
}
