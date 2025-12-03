# Repository Configuration Guide

This guide provides step-by-step instructions for configuring the GitHub repository settings for PEFT Studio's public release.

## Prerequisites

- Repository must be created on GitHub
- You must have admin access to the repository
- Repository should be private initially (will be made public in final step)

## Configuration Checklist

### 1. Basic Repository Settings

Navigate to: **Settings** → **General**

#### Repository Details

- **Description**: `Professional desktop application for Parameter-Efficient Fine-Tuning (PEFT) of Large Language Models`
- **Website**: (Add your website URL if available, or leave blank)
- **Topics**: See section 2 below

#### Features

Enable the following features:
- ✅ **Issues** - For bug reports and feature requests
- ✅ **Projects** - For project management and roadmap
- ✅ **Discussions** - For community Q&A and engagement
- ❌ **Wiki** - Not needed (documentation is in `/docs`)
- ❌ **Sponsorships** - Optional, enable if you want to accept sponsorships

#### Pull Requests

- ✅ **Allow merge commits**
- ✅ **Allow squash merging** (recommended as default)
- ✅ **Allow rebase merging**
- ✅ **Always suggest updating pull request branches**
- ✅ **Automatically delete head branches**

#### Default Branch

- Ensure default branch is set to: **`main`**

---

### 2. Repository Topics

Navigate to: **Settings** → **General** → **Topics**

Add the following topics (in this order for best discoverability):

```
peft
fine-tuning
llm
machine-learning
electron
react
pytorch
transformers
desktop-app
ai
```

**Verification**: Topics should appear at the top of your repository page below the description.

---

### 3. Branch Protection Rules

Navigate to: **Settings** → **Branches** → **Add branch protection rule**

#### Rule for `main` branch:

**Branch name pattern**: `main`

**Protect matching branches**:
- ✅ **Require a pull request before merging**
  - ✅ **Require approvals**: 1 (or more for team projects)
  - ✅ **Dismiss stale pull request approvals when new commits are pushed**
  - ✅ **Require review from Code Owners** (if you have a CODEOWNERS file)
- ✅ **Require status checks to pass before merging**
  - ✅ **Require branches to be up to date before merging**
  - Add required status checks:
    - `test` (from test.yml workflow)
    - `build` (from build.yml workflow)
    - `lint` (from code-quality.yml workflow)
- ✅ **Require conversation resolution before merging**
- ✅ **Require signed commits** (optional but recommended)
- ✅ **Require linear history** (optional, prevents merge commits)
- ✅ **Include administrators** (ensures rules apply to everyone)
- ❌ **Allow force pushes** (keep disabled for safety)
- ❌ **Allow deletions** (keep disabled for safety)

**Save changes**

---

### 4. GitHub Actions Configuration

Navigate to: **Settings** → **Actions** → **General**

#### Actions permissions:
- ✅ **Allow all actions and reusable workflows**

#### Workflow permissions:
- ✅ **Read and write permissions**
- ✅ **Allow GitHub Actions to create and approve pull requests**

#### Artifact and log retention:
- Set to **90 days** (default)

**Verification**: Check that workflows in `.github/workflows/` are enabled and can run.

---

### 5. GitHub Discussions Setup

Navigate to: **Settings** → **General** → **Features**

1. ✅ Enable **Discussions**
2. Click **Set up discussions** button
3. GitHub will create initial discussion categories

#### Configure Discussion Categories:

Navigate to: **Discussions** tab → **Categories** (gear icon)

**Recommended categories**:

1. **📣 Announcements** (Announcement format)
   - Description: "Official announcements and updates"
   - ✅ Only maintainers can post

2. **💡 Ideas** (Open discussion)
   - Description: "Share ideas for new features or improvements"

3. **🙏 Q&A** (Question/Answer format)
   - Description: "Ask questions and get help from the community"

4. **🎉 Show and Tell** (Open discussion)
   - Description: "Share what you've built with PEFT Studio"

5. **🐛 Bug Reports** (Open discussion)
   - Description: "Report bugs (use Issues for tracking)"

6. **📚 Documentation** (Open discussion)
   - Description: "Discuss documentation improvements"

#### Create Welcome Discussion:

1. Go to **Discussions** tab
2. Click **New discussion**
3. Category: **Announcements**
4. Title: "Welcome to PEFT Studio! 🎉"
5. Body:
```markdown
# Welcome to PEFT Studio! 🎉

Thank you for your interest in PEFT Studio - a professional desktop application for Parameter-Efficient Fine-Tuning of Large Language Models.

## Getting Started

- 📖 Read the [Quick Start Guide](../docs/user-guide/quick-start.md)
- 🐛 Report bugs via [Issues](../issues)
- 💡 Share ideas in [Ideas Discussion](../discussions/categories/ideas)
- ❓ Ask questions in [Q&A](../discussions/categories/q-a)

## Contributing

We welcome contributions! Please read our [Contributing Guide](../CONTRIBUTING.md) to get started.

## Community Guidelines

Please follow our [Code of Conduct](../CODE_OF_CONDUCT.md) to keep our community welcoming and inclusive.

## Support

- 📚 [Documentation](../docs)
- 💬 [Discussions](../discussions)
- 🐛 [Issue Tracker](../issues)

Happy fine-tuning! 🚀
```
6. Click **Start discussion**
7. **Pin** the discussion (three dots menu → Pin discussion)

---

### 6. Security Settings

Navigate to: **Settings** → **Security** → **Code security and analysis**

#### Recommended settings:
- ✅ **Dependency graph** (should be enabled by default)
- ✅ **Dependabot alerts** (enable to get security alerts)
- ✅ **Dependabot security updates** (enable for automatic security patches)
- ✅ **Dependabot version updates** (already configured via `.github/dependabot.yml`)
- ✅ **Code scanning** (optional, requires GitHub Advanced Security for private repos)
- ✅ **Secret scanning** (optional, requires GitHub Advanced Security for private repos)

---

### 7. Verify GitHub Actions Workflows

Navigate to: **Actions** tab

#### Check that the following workflows exist and are valid:

1. **CI Workflow** (`.github/workflows/ci.yml`)
   - Runs on: push, pull_request
   - Jobs: lint, test, build

2. **Test Workflow** (`.github/workflows/test.yml`)
   - Runs on: push, pull_request
   - Jobs: frontend tests, backend tests

3. **Build Workflow** (`.github/workflows/build.yml`)
   - Runs on: push, pull_request
   - Jobs: build for multiple platforms

4. **Code Quality Workflow** (`.github/workflows/code-quality.yml`)
   - Runs on: push, pull_request
   - Jobs: linting, formatting checks

5. **Deploy Workflow** (`.github/workflows/deploy.yml`)
   - Runs on: release
   - Jobs: deploy to production

6. **Release Workflow** (`.github/workflows/release.yml`)
   - Runs on: tag push
   - Jobs: create release, build installers

7. **Build Installers Workflow** (`.github/workflows/build-installers.yml`)
   - Runs on: workflow_dispatch, release
   - Jobs: build installers for all platforms

8. **Nightly Workflow** (`.github/workflows/nightly.yml`)
   - Runs on: schedule (nightly)
   - Jobs: comprehensive testing

#### Verification Steps:

1. Go to **Actions** tab
2. Check that all workflows are listed
3. Click on each workflow to verify it's enabled
4. Check recent runs (if any) for errors
5. If workflows haven't run yet, they will run on next push/PR

**Trigger a test run**:
```bash
# Make a small change and push to trigger workflows
git commit --allow-empty -m "test: trigger CI workflows"
git push
```

---

### 8. Repository Insights and Analytics

Navigate to: **Insights** tab

#### Configure Community Standards:

1. Go to **Insights** → **Community**
2. Verify all items are checked:
   - ✅ Description
   - ✅ README
   - ✅ Code of conduct
   - ✅ Contributing
   - ✅ License
   - ✅ Security policy
   - ✅ Issue templates
   - ✅ Pull request template

If any are missing, add them before making the repository public.

---

### 9. Collaborators and Teams (Optional)

Navigate to: **Settings** → **Collaborators and teams**

If you have team members:
1. Click **Add people** or **Add teams**
2. Set appropriate permissions:
   - **Read**: Can view and clone
   - **Triage**: Can manage issues and PRs
   - **Write**: Can push to repository
   - **Maintain**: Can manage repository settings
   - **Admin**: Full access

---

### 10. Notifications

Navigate to: **Settings** → **Notifications**

Configure how you want to receive notifications:
- ✅ **Watching**: Automatically watch repositories you have push access to
- ✅ **Participating**: Get notified when participating in conversations
- ✅ **@mentions**: Get notified when mentioned

---

## Verification Checklist

Before making the repository public, verify:

- [ ] Repository description is set correctly
- [ ] All 10 topics are added and visible
- [ ] Issues, Projects, and Discussions are enabled
- [ ] Default branch is `main`
- [ ] Branch protection rules are configured for `main`
- [ ] GitHub Actions workflows are present and valid
- [ ] Discussions are enabled with proper categories
- [ ] Welcome discussion is created and pinned
- [ ] Security features are enabled (Dependabot, etc.)
- [ ] Community standards are 100% complete
- [ ] All documentation files are present and complete

---

## Making Repository Public

**⚠️ WARNING: This action cannot be easily undone. Ensure all security checks pass first.**

Navigate to: **Settings** → **General** → **Danger Zone**

1. Scroll to bottom of page
2. Click **Change visibility**
3. Select **Make public**
4. Type repository name to confirm
5. Click **I understand, make this repository public**

---

## Post-Publication Verification

After making the repository public:

1. **Access from incognito browser** to verify public visibility
2. **Check README renders correctly** on repository homepage
3. **Verify all links work** (documentation, issues, discussions)
4. **Test cloning** the repository as a new user
5. **Check that releases are accessible** (if any exist)
6. **Monitor initial issues and discussions** for community feedback

---

## Troubleshooting

### Workflows not running
- Check Actions are enabled in Settings → Actions
- Verify workflow files have correct YAML syntax
- Check branch protection rules aren't blocking workflow runs

### Topics not appearing
- Ensure you saved changes after adding topics
- Topics may take a few minutes to appear in search
- Maximum 20 topics allowed

### Branch protection preventing merges
- Verify required status checks are passing
- Check that branch is up to date with base branch
- Ensure all conversations are resolved

### Discussions not showing
- Verify Discussions are enabled in Settings → Features
- Check that you've created at least one discussion category
- Refresh the page or clear browser cache

---

## Additional Resources

- [GitHub Docs: Managing repository settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features)
- [GitHub Docs: Configuring branch protection rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches)
- [GitHub Docs: About discussions](https://docs.github.com/en/discussions)
- [GitHub Docs: About GitHub Actions](https://docs.github.com/en/actions)

---

## Notes

This configuration guide is designed for the initial public release of PEFT Studio. Settings can be adjusted later based on community needs and project growth.

For questions or issues with repository configuration, please refer to the GitHub documentation or contact the repository maintainers.
