# Analytics Dashboard Guide

This guide explains how to access and interpret the analytics dashboard for PEFT Studio.

---

## Overview

GitHub provides a comprehensive analytics dashboard through the **Insights** tab. This dashboard gives you visibility into:

- Repository activity and trends
- Community engagement
- Traffic and popularity
- Code contributions
- Security and dependencies

---

## Accessing the Dashboard

### Main Insights Page
**URL:** https://github.com/Ankesh-007/peft-studiopulse

The Pulse page shows recent activity including:
- Merged pull requests
- Opened issues
- Closed issues
- Active contributors
- Commits
- Releases

**Update Frequency:** Real-time

---

## Dashboard Sections

### 1. Pulse (Recent Activity)

**What it shows:**
- Activity summary for the last week or month
- Merged PRs, opened/closed issues
- Active contributors
- Commits and releases

**How to use:**
- Check daily for new activity
- Identify busy periods
- Track contributor engagement

**Interpretation:**
- High activity = healthy project
- Multiple contributors = good community
- Regular commits = active development

---

### 2. Contributors

**URL:** https://github.com/Ankesh-007/peft-studiographs/contributors

**What it shows:**
- Contribution graphs over time
- Commits by contributor
- Lines added/deleted per contributor

**How to use:**
- Identify top contributors
- Track contribution trends
- Recognize community members

**Interpretation:**
- Diverse contributors = healthy community
- Consistent contributions = sustainable project
- New contributors = growing community

---

### 3. Community Profile

**URL:** https://github.com/Ankesh-007/peft-studiocommunity

**What it shows:**
- Community standards checklist
- Recommended files (README, LICENSE, etc.)
- Completion percentage

**How to use:**
- Ensure all items are checked
- Maintain 100% completion
- Update as standards evolve

**Interpretation:**
- 100% = professional, welcoming project
- Missing items = potential barriers to contribution

---

### 4. Traffic (Admin Only)

**URL:** https://github.com/Ankesh-007/peft-studiographs/traffic

**What it shows:**
- Page views (last 14 days)
- Unique visitors
- Clones
- Referring sites
- Popular content

**How to use:**
- Monitor daily/weekly traffic
- Identify traffic sources
- Track popular pages

**Interpretation:**
- Increasing views = growing interest
- High unique visitors = broad reach
- Clones = developer interest

**Note:** Traffic data is only retained for 14 days. Export regularly for historical analysis.

---

### 5. Commits

**URL:** https://github.com/Ankesh-007/peft-studiographs/commit-activity

**What it shows:**
- Commit frequency over time
- Commits by day of week
- Commits by hour of day

**How to use:**
- Identify development patterns
- Track project velocity
- Plan release schedules

**Interpretation:**
- Consistent commits = active development
- Spikes = feature development or bug fixes
- Gaps = potential issues or planned breaks

---

### 6. Code Frequency

**URL:** https://github.com/Ankesh-007/peft-studiographs/code-frequency

**What it shows:**
- Lines added/deleted over time
- Code churn metrics

**How to use:**
- Track codebase growth
- Identify refactoring periods
- Monitor code stability

**Interpretation:**
- Balanced add/delete = healthy refactoring
- High additions = feature development
- High deletions = cleanup or simplification

---

### 7. Dependency Graph

**URL:** https://github.com/Ankesh-007/peft-studionetwork/dependencies

**What it shows:**
- Project dependencies
- Dependents (who uses your project)
- Security alerts

**How to use:**
- Monitor dependency health
- Track security vulnerabilities
- Identify dependent projects

**Interpretation:**
- Many dependents = valuable project
- Security alerts = action required
- Outdated dependencies = maintenance needed

---

### 8. Network

**URL:** https://github.com/Ankesh-007/peft-studionetwork

**What it shows:**
- Fork network
- Branch relationships
- Commit timeline across forks

**How to use:**
- Visualize project ecosystem
- Identify active forks
- Track divergence

**Interpretation:**
- Active forks = community engagement
- Merged forks = successful collaboration

---

## Key Metrics to Monitor

### Daily Metrics
- ✅ New issues
- ✅ New pull requests
- ✅ Security alerts
- ✅ Build status

### Weekly Metrics
- 📊 Traffic trends
- 👥 Active contributors
- 🔀 Merged PRs
- 🐛 Closed issues

### Monthly Metrics
- ⭐ Stars growth
- 🍴 Forks growth
- 📥 Downloads
- 👥 New contributors

---

## Interpreting Trends

### Positive Trends
- ✅ Increasing stars and forks
- ✅ Growing contributor base
- ✅ Consistent commit activity
- ✅ High PR merge rate
- ✅ Fast issue response time

### Warning Signs
- ⚠️ Declining traffic
- ⚠️ Increasing open issues
- ⚠️ Slow PR review time
- ⚠️ Security alerts
- ⚠️ Contributor churn

### Action Items
- 🔧 Address security alerts immediately
- 🔧 Respond to issues within 24 hours
- 🔧 Review PRs within 48 hours
- 🔧 Update dependencies regularly
- 🔧 Engage with community

---

## Exporting Data

### Manual Export
1. Take screenshots of key metrics
2. Copy data to spreadsheet
3. Use GitHub API for programmatic access

### Automated Export
Use GitHub Actions to collect metrics weekly:
- See `.github/workflows/metrics.yml.example`
- Requires personal access token
- Stores data as artifacts

### API Export
```bash
# Repository stats
curl https://api.github.com/repos/Ankesh-007/peft-studio > stats.json

# Traffic (requires auth)
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/Ankesh-007/peft-studio/traffic/views > traffic.json
```

---

## Visualization Tools

### Built-in GitHub Charts
- Contribution graphs
- Traffic charts
- Commit activity
- Code frequency

### Third-Party Tools
- **Shields.io**: Badges for README
- **Repobeats**: Animated statistics
- **Sourcegraph**: Code analytics
- **GitStats**: Detailed statistics

---

## Best Practices

### Regular Monitoring
- Check Pulse daily
- Review Traffic weekly
- Analyze trends monthly

### Data-Driven Decisions
- Use metrics to prioritize work
- Track impact of changes
- Identify improvement areas

### Community Engagement
- Respond to issues promptly
- Review PRs quickly
- Recognize contributors
- Share milestones

### Continuous Improvement
- Set measurable goals
- Track progress
- Adjust strategies
- Celebrate successes

---

## Troubleshooting

### Traffic Data Not Showing
- **Cause:** Only available to repository admins
- **Solution:** Ensure you're logged in as admin

### Metrics Seem Outdated
- **Cause:** GitHub caches some data
- **Solution:** Wait a few hours or refresh

### Missing Contributors
- **Cause:** Commits not properly attributed
- **Solution:** Ensure commits have correct email

### Low Traffic
- **Cause:** Limited visibility
- **Solution:** Promote project, improve SEO, add topics

---

## Resources

### GitHub Documentation
- [Insights Overview](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository)
- [Traffic Views](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-traffic-to-a-repository)
- [Dependency Graph](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-the-dependency-graph)

### API Documentation
- [GitHub REST API](https://docs.github.com/en/rest)
- [Repository Statistics](https://docs.github.com/en/rest/metrics/statistics)

### Community
- [GitHub Community Forum](https://github.community/)
- [GitHub Support](https://support.github.com/)

---

## Next Steps

1. **Explore the Dashboard**
   - Visit each Insights section
   - Familiarize yourself with available metrics
   - Bookmark important pages

2. **Set Up Monitoring**
   - Create a monitoring schedule
   - Use the metrics tracking template
   - Set up alerts for critical metrics

3. **Take Action**
   - Address any issues found
   - Engage with the community
   - Improve based on insights

4. **Share Insights**
   - Add badges to README
   - Share milestones with community
   - Celebrate achievements

---

For questions or assistance with analytics, please:
- [Open an issue](https://github.com/Ankesh-007/peft-studioissues/new)
- [Start a discussion](https://github.com/Ankesh-007/peft-studiodiscussions)
