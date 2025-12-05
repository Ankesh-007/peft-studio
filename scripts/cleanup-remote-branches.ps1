# Script to clean up remote Dependabot branches
# Run this after reviewing and merging/closing Dependabot PRs

Write-Host "Repository Cleanup Script" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

# List all remote branches
Write-Host "Fetching latest remote branches..." -ForegroundColor Yellow
git fetch --all --prune

Write-Host ""
Write-Host "Current remote Dependabot branches:" -ForegroundColor Yellow
$dependabotBranches = git branch -r | Select-String "dependabot"
$dependabotBranches | ForEach-Object { Write-Host $_ -ForegroundColor Gray }

Write-Host ""
Write-Host "IMPORTANT: Before deleting branches, please:" -ForegroundColor Red
Write-Host "1. Visit https://github.com/Ankesh-007/peft-studio/pulls" -ForegroundColor White
Write-Host "2. Review all Dependabot pull requests" -ForegroundColor White
Write-Host "3. Merge the ones you want to keep" -ForegroundColor White
Write-Host "4. Close the ones you don't need" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "Have you reviewed all PRs? (yes/no)"

if ($confirm -eq "yes") {
    Write-Host ""
    Write-Host "Deleting remote Dependabot branches..." -ForegroundColor Yellow
    
    # GitHub Actions branches
    git push origin --delete dependabot/github_actions/actions/checkout-6
    git push origin --delete dependabot/github_actions/actions/setup-node-6
    git push origin --delete dependabot/github_actions/actions/upload-artifact-5
    git push origin --delete dependabot/github_actions/codecov/codecov-action-5
    git push origin --delete dependabot/github_actions/github/codeql-action-4
    
    # NPM branches
    git push origin --delete dependabot/npm_and_yarn/build-tools-fdce341329
    git push origin --delete dependabot/npm_and_yarn/fast-check-4.3.0
    git push origin --delete dependabot/npm_and_yarn/jsdom-27.2.0
    git push origin --delete dependabot/npm_and_yarn/prettier-3.7.4
    git push origin --delete dependabot/npm_and_yarn/react-93291292c9
    git push origin --delete dependabot/npm_and_yarn/tailwindcss-4.1.17
    git push origin --delete dependabot/npm_and_yarn/testing-286c5582ca
    git push origin --delete "dependabot/npm_and_yarn/types/node-24.10.1"
    git push origin --delete dependabot/npm_and_yarn/typescript-eslint/eslint-plugin-8.48.1
    git push origin --delete dependabot/npm_and_yarn/typescript-eslint/parser-8.48.1
    
    # Python branches
    git push origin --delete dependabot/pip/backend/aiohttp-3.13.2
    git push origin --delete dependabot/pip/backend/fastapi-31fed7a76c
    git push origin --delete dependabot/pip/backend/huggingface-hub-1.1.7
    git push origin --delete dependabot/pip/backend/keyring-25.7.0
    git push origin --delete dependabot/pip/backend/ml-libs-d04f2e788f
    git push origin --delete dependabot/pip/backend/pandas-2.3.3
    git push origin --delete dependabot/pip/backend/python-multipart-0.0.20
    git push origin --delete dependabot/pip/backend/sqlalchemy-2.0.44
    git push origin --delete dependabot/pip/backend/testing-a4b75fd499
    git push origin --delete dependabot/pip/backend/wandb-0.23.1
    
    Write-Host ""
    Write-Host "Cleanup complete!" -ForegroundColor Green
    Write-Host "Pruning local references..." -ForegroundColor Yellow
    git fetch --all --prune
    
    Write-Host ""
    Write-Host "Remaining remote branches:" -ForegroundColor Yellow
    git branch -r
} else {
    Write-Host ""
    Write-Host "Cleanup cancelled. Please review PRs first." -ForegroundColor Yellow
    Write-Host "Run this script again after reviewing." -ForegroundColor Yellow
}
