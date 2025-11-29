# GitHub Setup Instructions

## Quick Setup

After creating your GitHub repository, run these commands:

```bash
# Add your GitHub repository as remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/peft-studio.git

# Verify the remote was added
git remote -v

# Push your code to GitHub
git push -u origin master

# Or if you prefer 'main' as the default branch:
git branch -M main
git push -u origin main
```

## Alternative: Using SSH

If you have SSH keys set up:

```bash
# Add remote using SSH
git remote add origin git@github.com:YOUR_USERNAME/peft-studio.git

# Push
git push -u origin master
```

## If You Need to Change the Remote

```bash
# Remove existing remote
git remote remove origin

# Add new remote
git remote add origin https://github.com/YOUR_USERNAME/peft-studio.git

# Push
git push -u origin master
```

## Verify Everything Worked

After pushing, you should see:

```
Enumerating objects: 45, done.
Counting objects: 100% (45/45), done.
Delta compression using up to 8 threads
Compressing objects: 100% (40/40), done.
Writing objects: 100% (45/45), 150.00 KiB | 5.00 MiB/s, done.
Total 45 (delta 2), reused 0 (delta 0), pack-reused 0
To https://github.com/YOUR_USERNAME/peft-studio.git
 * [new branch]      master -> master
Branch 'master' set up to track remote branch 'master' from 'origin'.
```

## Next Steps

1. Visit your repository: `https://github.com/YOUR_USERNAME/peft-studio`
2. You should see all your files
3. The README.md will be displayed on the main page
4. Add topics/tags to your repo for better discoverability

## Recommended Repository Settings

### Topics to Add:
- `electron`
- `react`
- `typescript`
- `machine-learning`
- `llm`
- `fine-tuning`
- `peft`
- `lora`
- `desktop-app`
- `pytorch`

### Add a License (Recommended):
- Go to your repo → Add file → Create new file
- Name it `LICENSE`
- Choose a license template (MIT is common for open source)

### Enable GitHub Pages (Optional):
- Settings → Pages
- Source: Deploy from a branch
- Branch: master / docs (if you create a docs folder)

## Troubleshooting

### Authentication Issues

If you get authentication errors:

**Option 1: Use Personal Access Token**
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` scope
3. Use the token as your password when pushing

**Option 2: Use GitHub CLI**
```bash
# Install GitHub CLI: https://cli.github.com/
gh auth login
gh repo create peft-studio --public --source=. --remote=origin --push
```

### Branch Name Issues

If GitHub uses 'main' instead of 'master':

```bash
git branch -M main
git push -u origin main
```

## Repository Description

Use this for your GitHub repository description:

```
🚀 Professional desktop application for Parameter-Efficient Fine-Tuning (PEFT) of Large Language Models. Built with Electron, React, TypeScript, and Python FastAPI. Features real-time training monitoring, model testing playground, and beautiful dark-themed UI.
```

## README Badges (Optional)

Add these to the top of your README.md:

```markdown
![License](https://img.shields.io/badge/license-ISC-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![React](https://img.shields.io/badge/React-18.3-61dafb?logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178c6?logo=typescript)
![Electron](https://img.shields.io/badge/Electron-33.2-47848f?logo=electron)
```
