# GitHub Analytics Setup Guide

This guide provides instructions for configuring GitHub Insights and setting up analytics monitoring for PEFT Studio.

## Overview

GitHub provides built-in analytics and insights that help track repository health, community engagement, and project metrics. This guide covers:

1. Configuring GitHub Insights
2. Monitoring download statistics
3. Tracking issue and PR metrics
4. Setting up community health metrics

---

## 1. Configure GitHub Insights

GitHub Insights provides visibility into repository activity, contributors, and traffic.

### 1.1 Enable Insights Tab

**Steps:**
1. Navigate to your repository: `https://github.com/Ankesh-007/peft-studio`
2. Click on the **Insights** tab (top navigation bar)
3. Insights is enabled by default for public repositories

### 1.2 Available Insight Categories

GitHub provides the following insight categories:

#### **Pulse**
- Shows recent activity (last week/month)
- Displays merged PRs, opened issues, closed issues
- Shows active contributors

**Access:** `Insights > Pulse`

#### **Contributors**
- Shows contribution graphs over time
- Displays commits by contributor
- Shows additions/deletions per contributor

**Access:** `Insights > Contributors`

#### **Community**
- Shows community profile completion
- Displays recommended community standards
- Tracks documentation completeness

**Access:** `Insights > Community`

#### **Traffic**
- Shows page views and unique visitors
- Displays referring sites
- Shows popular content

**Access:** `Insights > Traffic`
**Note:** Traffic data is only available to repository administrators

#### **Commits**
- Shows commit activity over time
- Displays commits by day of week and hour
- Shows commit frequency

**Access:** `Insights > Commits`

#### **Code Frequency**
- Shows additions and deletions over time
- Displays code churn metrics

**Access:** `Insights > Code frequency`

#### **Dependency Graph**
- Shows project dependencies
- Displays dependents (who uses your project)
- Tracks security alerts

**Access:** `Insights > Dependency graph`

#### **Network**
- Shows fork network
- Displays branch relationships

**Access:** `Insights > Network`

---

## 2. Monitor Download Statistics

### 2.1 Release Downloads

GitHub tracks download counts for release assets (installers, binaries).

**How to View:**
1. Go to `Releases` page
2. Each release shows download counts for attached assets
3. Click on a release to see detailed download statistics

**Metrics Available:**
- Total downloads per asset
- Downloads per release version
- Download trends over time

### 2.2 Clone Statistics

**Traffic Insights** (Admin only):
1. Go to `Insights > Traffic`
2. View **Clones** section
3. See unique cloners and total clones over 14 days

**Metrics Available:**
- Unique cloners (last 14 days)
- Total clones (last 14 days)
- Daily clone activity graph

### 2.3 Git Clone Traffic

**Note:** GitHub only retains traffic data for 14 days. For long-term tracking, consider:

**Option 1: Manual Tracking**
- Record metrics weekly in a spreadsheet
- Track: clones, views, unique visitors, downloads

**Option 2: GitHub API**
- Use GitHub API to fetch traffic data programmatically
- Store data in external database for historical analysis
- API endpoint: `GET /repos/{owner}/{repo}/traffic/clones`

**Example API Call:**
```bash
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/Ankesh-007/peft-studio/traffic/clones
```

---

## 3. Track Issue and PR Metrics

### 3.1 Issue Metrics

**Built-in Metrics:**
1. Go to `Issues` tab
2. Use filters to track:
   - Open issues
   - Closed issues
   - Issues by label
   - Issues by milestone
   - Issues by assignee

**Key Metrics to Monitor:**
- **Issue Response Time:** Time from issue creation to first response
- **Issue Resolution Time:** Time from issue creation to closure
- **Open Issue Count:** Total open issues
- **Issue Close Rate:** Percentage of issues closed vs opened

**Viewing Issue Insights:**
1. Go to `Insights > Pulse`
2. See "Issues opened" and "Issues closed" in the last week/month

### 3.2 Pull Request Metrics

**Built-in Metrics:**
1. Go to `Pull requests` tab
2. Use filters to track:
   - Open PRs
   - Closed PRs
   - Merged PRs
   - PRs by label
   - PRs by reviewer

**Key Metrics to Monitor:**
- **PR Review Time:** Time from PR creation to first review
- **PR Merge Time:** Time from PR creation to merge
- **PR Close Rate:** Percentage of PRs merged vs closed without merge
- **Review Participation:** Number of reviewers per PR

**Viewing PR Insights:**
1. Go to `Insights > Pulse`
2. See "Pull requests merged" and "Pull requests opened"

### 3.3 Advanced Tracking with GitHub Projects

**Setup GitHub Projects for Metrics:**
1. Go to `Projects` tab
2. Create a new project: "Metrics Dashboard"
3. Add custom fields:
   - Response Time (number)
   - Resolution Time (number)
   - Priority (select)
   - Status (select)

**Benefits:**
- Visual kanban board for issues/PRs
- Custom fields for tracking metrics
- Automated workflows
- Charts and insights

---

## 4. Set Up Community Health Metrics

### 4.1 Community Profile

GitHub provides a community profile checklist to ensure repository health.

**Access Community Profile:**
1. Go to `Insights > Community`
2. Review the checklist

**Community Standards Checklist:**
- ✅ Description
- ✅ README
- ✅ Code of conduct
- ✅ Contributing guidelines
- ✅ License
- ✅ Security policy
- ✅ Issue templates
- ✅ Pull request template

**Current Status for PEFT Studio:**
All items should be complete after tasks 10-13.

### 4.2 Community Health Metrics to Track

#### **Contributor Metrics**
- **Total Contributors:** Number of unique contributors
- **Active Contributors:** Contributors in last 30 days
- **First-time Contributors:** New contributors per month
- **Contributor Retention:** Percentage of returning contributors

**View:** `Insights > Contributors`

#### **Engagement Metrics**
- **Stars:** Total repository stars
- **Watchers:** Users watching the repository
- **Forks:** Total repository forks
- **Discussions:** Active discussions count

**View:** Repository homepage and `Insights > Traffic`

#### **Response Metrics**
- **Issue Response Time:** Average time to first response
- **PR Review Time:** Average time to first review
- **Issue Resolution Time:** Average time to close issues
- **PR Merge Time:** Average time to merge PRs

**Manual Tracking Required:** GitHub doesn't provide these automatically

#### **Activity Metrics**
- **Commit Frequency:** Commits per week/month
- **Release Frequency:** Releases per month
- **Issue Creation Rate:** New issues per week
- **PR Creation Rate:** New PRs per week

**View:** `Insights > Pulse` and `Insights > Commits`

### 4.3 Setting Up Automated Metrics Collection

For advanced metrics tracking, consider using GitHub Actions:

**Create Metrics Collection Workflow:**

```yaml
# .github/workflows/metrics.yml
name: Collect Metrics

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday at midnight
  workflow_dispatch:  # Manual trigger

jobs:
  collect-metrics:
    runs-on: ubuntu-latest
    steps:
      - name: Collect Repository Metrics
        uses: lowlighter/metrics@latest
        with:
          token: ${{ secrets.METRICS_TOKEN }}
          user: Ankesh-007
          repo: peft-studio
          
          # Enable plugins
          plugin_traffic: yes
          plugin_stars: yes
          plugin_followup: yes
          plugin_reactions: yes
          plugin_people: yes
          plugin_projects: yes
          
          # Output
          output_action: commit
          committer_branch: metrics
          committer_message: "Update metrics"
```

**Note:** This requires creating a personal access token with appropriate permissions.

---

## 5. Recommended Monitoring Schedule

### Daily Monitoring
- Check for new issues and PRs
- Review traffic spikes
- Monitor security alerts

### Weekly Monitoring
- Review Pulse insights
- Check contributor activity
- Analyze traffic trends
- Review issue/PR metrics

### Monthly Monitoring
- Generate comprehensive metrics report
- Analyze contributor growth
- Review community health score
- Track download statistics
- Assess project velocity

---

## 6. Key Performance Indicators (KPIs)

### Repository Health KPIs
- **Community Profile Completion:** 100% (all items checked)
- **Open Issue Count:** < 20 open issues
- **Issue Response Time:** < 24 hours average
- **PR Review Time:** < 48 hours average

### Growth KPIs
- **Stars Growth:** +10% month-over-month
- **Contributors Growth:** +5 new contributors per month
- **Fork Growth:** +5% month-over-month
- **Download Growth:** +20% month-over-month

### Engagement KPIs
- **Issue Close Rate:** > 80%
- **PR Merge Rate:** > 90%
- **Discussion Participation:** > 5 active discussions
- **Community Retention:** > 50% returning contributors

---

## 7. Tools and Resources

### GitHub Native Tools
- **GitHub Insights:** Built-in analytics dashboard
- **GitHub API:** Programmatic access to metrics
- **GitHub CLI:** Command-line access to repository data

### Third-Party Tools
- **Shields.io:** Create badges for README
- **Sourcegraph:** Code search and analytics
- **GitStats:** Generate detailed statistics
- **Repobeats:** Animated repository statistics

### Monitoring Services
- **GitHub Actions:** Automated metrics collection
- **Dependabot:** Dependency monitoring
- **CodeQL:** Security scanning
- **Codecov:** Test coverage tracking

---

## 8. Implementation Checklist

- [ ] Enable GitHub Insights (automatic for public repos)
- [ ] Review Community Profile completion
- [ ] Set up weekly metrics review schedule
- [ ] Create metrics tracking spreadsheet (optional)
- [ ] Configure GitHub Projects for advanced tracking (optional)
- [ ] Set up automated metrics collection workflow (optional)
- [ ] Add metrics badges to README
- [ ] Document KPIs and goals
- [ ] Schedule monthly metrics review meeting

---

## 9. Accessing Metrics

### For Repository Administrators
Full access to all metrics including:
- Traffic data (views, clones)
- Referrer information
- Popular content
- All Insights tabs

### For Public Users
Limited access to:
- Contributors graph
- Commit activity
- Code frequency
- Network graph
- Pulse (recent activity)

### API Access
Use GitHub API for programmatic access:
```bash
# Get repository statistics
curl https://api.github.com/repos/Ankesh-007/peft-studio

# Get traffic views (requires authentication)
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/Ankesh-007/peft-studio/traffic/views

# Get release downloads
curl https://api.github.com/repos/Ankesh-007/peft-studio/releases
```

---

## 10. Next Steps

1. **Immediate Actions:**
   - Review current Insights dashboard
   - Check Community Profile completion
   - Set up weekly monitoring schedule

2. **Short-term (1-2 weeks):**
   - Create metrics tracking system
   - Add metrics badges to README
   - Set up GitHub Projects for tracking

3. **Long-term (1-3 months):**
   - Implement automated metrics collection
   - Analyze trends and adjust KPIs
   - Create monthly metrics reports

---

## Conclusion

GitHub provides comprehensive built-in analytics for monitoring repository health and community engagement. By regularly reviewing these metrics and tracking key performance indicators, you can ensure PEFT Studio maintains a healthy, growing community and continues to meet user needs.

For questions or issues with analytics setup, refer to:
- [GitHub Insights Documentation](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository)
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [GitHub Community Forum](https://github.community/)
