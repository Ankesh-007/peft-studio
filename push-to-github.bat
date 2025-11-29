@echo off
echo ========================================
echo   PEFT Studio - GitHub Setup
echo ========================================
echo.

REM Check if git is initialized
if not exist ".git" (
    echo Error: Git repository not initialized!
    echo Run: git init
    exit /b 1
)

echo Current Git Status:
git status --short
echo.

echo Enter your GitHub username:
set /p username=

if "%username%"=="" (
    echo Error: Username cannot be empty!
    exit /b 1
)

echo.
echo Enter repository name (default: peft-studio):
set /p reponame=

if "%reponame%"=="" (
    set reponame=peft-studio
)

set repourl=https://github.com/%username%/%reponame%.git

echo.
echo Repository URL: %repourl%
echo.
echo Is this correct? (Y/n)
set /p confirm=

if /i "%confirm%"=="n" (
    echo Aborted.
    exit /b 1
)

echo.
echo Adding remote 'origin'...
git remote add origin %repourl%

if errorlevel 1 (
    echo.
    echo Remote might already exist. Removing and re-adding...
    git remote remove origin
    git remote add origin %repourl%
)

echo.
echo Verifying remote...
git remote -v
echo.

echo Choose branch name:
echo   1. master (current)
echo   2. main (GitHub default)
set /p branch=

if "%branch%"=="2" (
    echo Renaming branch to 'main'...
    git branch -M main
    set branchname=main
) else (
    set branchname=master
)

echo.
echo Pushing to GitHub...
echo Branch: %branchname%
echo.

git push -u origin %branchname%

if errorlevel 1 (
    echo.
    echo ========================================
    echo   Error: Failed to push to GitHub!
    echo ========================================
    echo.
    echo Common issues:
    echo   1. Repository doesn't exist on GitHub
    echo      Create it at: https://github.com/new
    echo.
    echo   2. Authentication failed
    echo      Use a Personal Access Token as password
    echo      Generate at: https://github.com/settings/tokens
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Success! Code pushed to GitHub!
echo ========================================
echo.
echo View your repository at:
echo   https://github.com/%username%/%reponame%
echo.
echo Next steps:
echo   1. Add a description to your repository
echo   2. Add topics/tags for discoverability
echo   3. Consider adding a LICENSE file
echo.
pause
