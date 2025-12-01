# Repository Configuration Checklist

Use this checklist to track progress on configuring the GitHub repository for public release.

## Pre-Configuration

- [ ] GitHub CLI (gh) installed and authenticated
- [ ] Repository created on GitHub
- [ ] Admin access to repository confirmed
- [ ] Repository is currently private

## Automated Configuration (via scripts)

Run: `./scripts/configure-repository.sh` (Unix) or `./scripts/configure-repository.ps1` (Windows)

- [ ] Script executed successfully
- [ ] Repository description updated
- [ ] Issues enabled
- [ ] Projects enabled
- [ ] Wiki disabled
- [ ] Topics added (10 topics)
- [ ] All workflow files verified present

## Manual Configuration Required

### 1. Repository Settings

Navigate to: **Settings** → **General**

- [ ] Description verified: "Professional desktop application for Parameter-Efficient Fine-Tuning (PEFT) of Large Language Models"
- [ ] Website URL added (if available)
- [ ] Issues enabled ✓
- [ ] Projects enabled ✓
- [ ] Discussions enabled
- [ ] Wiki disabled ✓
- [ ] Default branch set to `main`

### 2. Repository Topics

Navigate to: **Settings** → **General** → **Topics**

Verify all topics are present:
- [ ] peft
- [ ] fine-tuning
- [ ] llm
- [ ] machine-learning
- [ ] electron
- [ ] react
- [ ] pytorch
- [ ] transformers
- [ ] desktop-app
- [ ] ai

### 3. Branch Protection Rules

Navigate to: **Settings** → **Branches** → **Add branch protection rule**

Branch: `main`

- [ ] Require pull request before merging
- [ ] Require 1 approval
- [ ] Dismiss stale reviews when new commits pushed
- [ ] Require status checks to pass
- [ ] Require branches to be up to date
- [ ] Required status checks added:
  - [ ] test
  - [ ] build
  - [ ] lint
- [ ] Require conversation resolution
- [ ] Include administrators
- [ ] Force pushes disabled
- [ ] Deletions disabled

### 4. GitHub Actions

Navigate to: **Settings** → **Actions** → **General**

- [ ] Allow all actions and reusable workflows
- [ ] Read and write permissions enabled
- [ ] Allow GitHub Actions to create and approve PRs
- [ ] Artifact retention set to 90 days

### 5. GitHub Discussions

Navigate to: **Settings** → **General** → **Features**

- [ ] Discussions enabled
- [ ] Discussion categories configured:
  - [ ] 📣 Announcements (maintainers only)
  - [ ] 💡 Ideas
  - [ ] 🙏 Q&A
  - [ ] 🎉 Show and Tell
  - [ ] 🐛 Bug Reports
  - [ ] 📚 Documentation
- [ ] Welcome discussion created
- [ ] Welcome discussion pinned

### 6. Security Settings

Navigate to: **Settings** → **Security** → **Code security and analysis**

- [ ] Dependency graph enabled
- [ ] Dependabot alerts enabled
- [ ] Dependabot security updates enabled
- [ ] Dependabot version updates enabled (via .github/dependabot.yml)
- [ ] Code scanning configured (optional)
- [ ] Secret scanning enabled (optional)

### 7. Workflow Verification

Navigate to: **Actions** tab

Verify workflows are present and valid:
- [ ] CI Workflow (ci.yml)
- [ ] Test Workflow (test.yml)
- [ ] Build Workflow (build.yml)
- [ ] Code Quality Workflow (code-quality.yml)
- [ ] Deploy Workflow (deploy.yml)
- [ ] Release Workflow (release.yml)
- [ ] Build Installers Workflow (build-installers.yml)
- [ ] Nightly Workflow (nightly.yml)

Test workflows:
- [ ] Trigger test run (push empty commit)
- [ ] Verify workflows execute successfully
- [ ] Check for any errors in workflow runs

### 8. Community Standards

Navigate to: **Insights** → **Community**

Verify 100% completion:
- [ ] Description ✓
- [ ] README ✓
- [ ] Code of conduct ✓
- [ ] Contributing ✓
- [ ] License ✓
- [ ] Security policy ✓
- [ ] Issue templates ✓
- [ ] Pull request template ✓

### 9. Package Metadata

Verify package.json contains:
- [ ] Correct description
- [ ] All keywords/topics
- [ ] Author information
- [ ] Repository URL (update YOUR_USERNAME)
- [ ] Homepage URL (update YOUR_USERNAME)
- [ ] Bugs URL (update YOUR_USERNAME)
- [ ] MIT license specified

### 10. Documentation Review

- [ ] README.md complete and accurate
- [ ] CONTRIBUTING.md clear and helpful
- [ ] CODE_OF_CONDUCT.md present
- [ ] SECURITY.md with vulnerability reporting process
- [ ] LICENSE file with MIT license
- [ ] CHANGELOG.md with version history
- [ ] All links in documentation work

## Final Verification

Before making repository public:

- [ ] All automated checks passed
- [ ] All manual configuration completed
- [ ] Security scan passed (no sensitive data)
- [ ] All tests passing
- [ ] Build successful on all platforms
- [ ] Documentation reviewed and complete
- [ ] Community standards 100% complete
- [ ] Workflows tested and working

## Publication

- [ ] Repository made public
- [ ] Verified public access from incognito browser
- [ ] README renders correctly
- [ ] All links work
- [ ] Releases accessible (if any)
- [ ] Initial community feedback monitored

## Post-Publication

- [ ] Repository URL shared with team
- [ ] Initial announcement made (if applicable)
- [ ] Monitoring set up for issues and discussions
- [ ] Response plan in place for community feedback

---

## Notes

Date Started: _______________
Date Completed: _______________
Configured By: _______________

Issues Encountered:
- 
- 
- 

Additional Configuration:
- 
- 
- 

---

## Quick Reference

- Repository: https://github.com/YOUR_USERNAME/peft-studio
- Settings: https://github.com/YOUR_USERNAME/peft-studio/settings
- Actions: https://github.com/YOUR_USERNAME/peft-studio/actions
- Discussions: https://github.com/YOUR_USERNAME/peft-studio/discussions
- Insights: https://github.com/YOUR_USERNAME/peft-studio/pulse

---

**Remember**: Update YOUR_USERNAME with actual GitHub username before making repository public!
