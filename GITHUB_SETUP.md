# GitHub Setup Guide

## Repository Information

**Repository**: https://github.com/Ankesh-007/peft-studio  
**Branch**: main

## Future Updates

To push changes after making edits:

```bash
# Stage changes
git add .

# Commit with message
git commit -m "Your commit message"

# Push to GitHub
git push
```

## Common Git Commands

```bash
# Check status
git status

# View commit history
git log --oneline

# Create new branch
git checkout -b feature-name

# Switch branches
git checkout main

# Pull latest changes
git pull

# View remote URL
git remote -v
```

## Authentication

If prompted for credentials:
- **Username**: Your GitHub username
- **Password**: Use a Personal Access Token (not your password)
- Generate token at: https://github.com/settings/tokens

## Troubleshooting

### Push rejected
```bash
git pull --rebase
git push
```

### Merge conflicts
```bash
# Resolve conflicts in your editor
git add .
git commit -m "Resolve conflicts"
git push
```

### Reset to last commit
```bash
git reset --hard HEAD
```
