# GitHub Analytics Quick Reference

Quick links and commands for accessing PEFT Studio analytics.

---

## Quick Links

### Repository Home
https://github.com/Ankesh-007/peft-studio

### Insights Dashboard
https://github.com/Ankesh-007/peft-studio/pulse

### Traffic (Admin Only)
https://github.com/Ankesh-007/peft-studio/graphs/traffic

### Contributors
https://github.com/Ankesh-007/peft-studio/graphs/contributors

### Community Profile
https://github.com/Ankesh-007/peft-studio/community

### Releases & Downloads
https://github.com/Ankesh-007/peft-studio/releases

### Issues
https://github.com/Ankesh-007/peft-studio/issues

### Pull Requests
https://github.com/Ankesh-007/peft-studio/pulls

### Dependency Graph
https://github.com/Ankesh-007/peft-studio/network/dependencies

### Security Alerts
https://github.com/Ankesh-007/peft-studio/security

---

## GitHub CLI Commands

### Repository Statistics
```bash
gh repo view Ankesh-007/peft-studio
```

### List Issues
```bash
gh issue list --repo Ankesh-007/peft-studio
```

### List Pull Requests
```bash
gh pr list --repo Ankesh-007/peft-studio
```

### View Release Downloads
```bash
gh release list --repo Ankesh-007/peft-studio
```

### View Contributors
```bash
gh api repos/Ankesh-007/peft-studio/contributors
```

---

## GitHub API Endpoints

### Repository Info
```bash
curl https://api.github.com/repos/Ankesh-007/peft-studio
```

### Traffic Views (Requires Auth)
```bash
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/Ankesh-007/peft-studio/traffic/views
```

### Traffic Clones (Requires Auth)
```bash
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/Ankesh-007/peft-studio/traffic/clones
```

### Popular Paths (Requires Auth)
```bash
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/Ankesh-007/peft-studio/traffic/popular/paths
```

### Popular Referrers (Requires Auth)
```bash
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/Ankesh-007/peft-studio/traffic/popular/referrers
```

### Contributors
```bash
curl https://api.github.com/repos/Ankesh-007/peft-studio/contributors
```

### Releases
```bash
curl https://api.github.com/repos/Ankesh-007/peft-studio/releases
```

### Issues
```bash
curl https://api.github.com/repos/Ankesh-007/peft-studio/issues
```

### Pull Requests
```bash
curl https://api.github.com/repos/Ankesh-007/peft-studio/pulls
```

### Stargazers
```bash
curl https://api.github.com/repos/Ankesh-007/peft-studio/stargazers
```

### Forks
```bash
curl https://api.github.com/repos/Ankesh-007/peft-studio/forks
```

---

## Metrics Badges for README

### Stars
```markdown
![GitHub stars](https://img.shields.io/github/stars/Ankesh-007/peft-studio?style=social)
```

### Forks
```markdown
![GitHub forks](https://img.shields.io/github/forks/Ankesh-007/peft-studio?style=social)
```

### Issues
```markdown
![GitHub issues](https://img.shields.io/github/issues/Ankesh-007/peft-studio)
```

### Pull Requests
```markdown
![GitHub pull requests](https://img.shields.io/github/issues-pr/Ankesh-007/peft-studio)
```

### License
```markdown
![GitHub license](https://img.shields.io/github/license/Ankesh-007/peft-studio)
```

### Release
```markdown
![GitHub release](https://img.shields.io/github/v/release/Ankesh-007/peft-studio)
```

### Downloads
```markdown
![GitHub all releases](https://img.shields.io/github/downloads/Ankesh-007/peft-studio/total)
```

### Contributors
```markdown
![GitHub contributors](https://img.shields.io/github/contributors/Ankesh-007/peft-studio)
```

### Last Commit
```markdown
![GitHub last commit](https://img.shields.io/github/last-commit/Ankesh-007/peft-studio)
```

### Commit Activity
```markdown
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/Ankesh-007/peft-studio)
```

---

## Monitoring Schedule

### Daily (5 minutes)
- Check new issues: https://github.com/Ankesh-007/peft-studio/issues
- Check new PRs: https://github.com/Ankesh-007/peft-studio/pulls
- Review security alerts: https://github.com/Ankesh-007/peft-studio/security

### Weekly (15 minutes)
- Review Pulse: https://github.com/Ankesh-007/peft-studio/pulse
- Check traffic: https://github.com/Ankesh-007/peft-studio/graphs/traffic
- Review contributors: https://github.com/Ankesh-007/peft-studio/graphs/contributors
- Update metrics tracking template

### Monthly (30 minutes)
- Generate comprehensive metrics report
- Analyze trends
- Review KPIs
- Plan improvements
- Update roadmap

---

## Key Metrics to Track

### Growth Metrics
- ⭐ Stars
- 🍴 Forks
- 👀 Watchers
- 👥 Contributors

### Engagement Metrics
- 📊 Traffic (views, clones)
- 🐛 Issues (open, closed, response time)
- 🔀 Pull Requests (open, merged, review time)
- 💬 Discussions

### Quality Metrics
- ✅ Test Coverage
- 🔒 Security Alerts
- 📦 Dependency Health
- 🏗️ Build Status

### Download Metrics
- 📥 Total Downloads
- 📈 Download Growth
- 🖥️ Platform Distribution

---

## Useful GitHub Search Queries

### Recent Issues
```
is:issue is:open repo:Ankesh-007/peft-studio sort:created-desc
```

### Unresponded Issues
```
is:issue is:open repo:Ankesh-007/peft-studio no:assignee
```

### Recent PRs
```
is:pr is:open repo:Ankesh-007/peft-studio sort:created-desc
```

### Merged PRs This Month
```
is:pr is:merged repo:Ankesh-007/peft-studio merged:>2025-01-01
```

### First-time Contributors
```
is:pr repo:Ankesh-007/peft-studio author:first-time-contributor
```

---

## Export Data

### Export Issues to CSV
Use GitHub's export feature:
1. Go to Issues page
2. Click "Export" button (if available)
3. Or use GitHub API with pagination

### Export Traffic Data
```bash
# Requires authentication
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/Ankesh-007/peft-studio/traffic/views \
  > traffic_views.json
```

### Export Contributors Data
```bash
curl https://api.github.com/repos/Ankesh-007/peft-studio/contributors \
  > contributors.json
```

---

## Third-Party Analytics Tools

### Shields.io
https://shields.io/
- Create custom badges
- Display metrics in README

### Repobeats
https://repobeats.axiom.co/
- Animated repository statistics
- Embed in README

### Sourcegraph
https://sourcegraph.com/
- Code search and analytics
- Dependency analysis

### GitStats
https://gitstats.me/
- Detailed repository statistics
- Contribution graphs

---

## Support

For questions about GitHub analytics:
- [GitHub Docs - Insights](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository)
- [GitHub API Docs](https://docs.github.com/en/rest)
- [GitHub Community](https://github.community/)

For PEFT Studio specific questions:
- [Open an Issue](https://github.com/Ankesh-007/peft-studio/issues/new)
- [Start a Discussion](https://github.com/Ankesh-007/peft-studio/discussions)
