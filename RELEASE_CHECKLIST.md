# PEFT Studio v1.0.1 Release Checklist

Use this checklist to ensure a smooth release process.

## Pre-Release Verification

### Code & Tests
- [ ] All code changes committed
- [ ] Version updated to 1.0.1 in `package.json`
- [ ] `CHANGELOG.md` updated with release notes
- [ ] All tests passing: `npm run test:run`
- [ ] No TypeScript errors: `npm run type-check`
- [ ] No linting errors: `npm run lint`

### Documentation
- [ ] README.md up to date
- [ ] Installation guides reviewed
- [ ] API documentation current
- [ ] Troubleshooting guide updated

### Dependencies
- [ ] All dependencies installed: `npm install`
- [ ] Backend dependencies listed in `requirements.txt`
- [ ] No security vulnerabilities: `npm audit`

## Release Preparation

### Dry Run
- [ ] Run cleanup dry run: `npm run prepare:release:dry`
- [ ] Review files to be removed
- [ ] Verify no critical files will be deleted
- [ ] Run full release dry run: `npm run release:dry`
- [ ] Review all steps that will be executed

### Backup
- [ ] Git status clean: `git status`
- [ ] All changes committed
- [ ] Branch up to date with remote
- [ ] Create backup branch (optional): `git branch backup-pre-release`

## Execute Release

### Automated Release
- [ ] Run: `npm run release`
- [ ] Verify cleanup completed successfully
- [ ] Verify tests passed
- [ ] Verify build completed
- [ ] Verify installers created in `release/` directory
- [ ] Verify checksums generated
- [ ] Verify Git commit created
- [ ] Verify Git tag created
- [ ] Verify push to GitHub successful

### Verify Installers Created
Check that these files exist in `release/` directory:

**Windows:**
- [ ] `PEFT-Studio-Setup-1.0.1.exe`
- [ ] `PEFT-Studio-Portable-1.0.1.exe`

**macOS:**
- [ ] `PEFT-Studio-1.0.1-x64.dmg`
- [ ] `PEFT-Studio-1.0.1-arm64.dmg`
- [ ] `PEFT-Studio-1.0.1-x64.zip`
- [ ] `PEFT-Studio-1.0.1-arm64.zip`

**Linux:**
- [ ] `PEFT-Studio-1.0.1-x64.AppImage`
- [ ] `PEFT-Studio-1.0.1-x64.deb`

**Checksums:**
- [ ] `checksums.txt`

## GitHub Release

### Create Release
- [ ] Go to: https://github.com/Ankesh-007/peft-studio/releases
- [ ] Click "Draft a new release"
- [ ] Select tag: `v1.0.1`
- [ ] Release title: `PEFT Studio v1.0.1`
- [ ] Copy release notes from `CHANGELOG.md`

### Upload Assets
- [ ] Upload all Windows installers (.exe files)
- [ ] Upload all macOS installers (.dmg and .zip files)
- [ ] Upload all Linux installers (.AppImage and .deb files)
- [ ] Upload `checksums.txt`
- [ ] Verify all files uploaded successfully

### Publish
- [ ] Review release notes
- [ ] Review uploaded files
- [ ] Click "Publish release"
- [ ] Verify release is visible on GitHub

## Post-Release Verification

### GitHub
- [ ] Release visible at: https://github.com/Ankesh-007/peft-studio/releases
- [ ] Tag visible at: https://github.com/Ankesh-007/peft-studio/tags
- [ ] All installers downloadable
- [ ] Checksums file downloadable

### Installers
- [ ] Download Windows installer
- [ ] Download macOS installer
- [ ] Download Linux installer
- [ ] Verify checksums match: `sha256sum -c checksums.txt`

### Testing (Optional but Recommended)
- [ ] Test Windows installer on Windows machine
- [ ] Test macOS installer on macOS machine
- [ ] Test Linux installer on Linux machine
- [ ] Verify application launches
- [ ] Verify basic functionality works

### Auto-Update (Optional)
- [ ] Test auto-update from previous version
- [ ] Verify update notification appears
- [ ] Verify update downloads and installs

## Communication

### Internal
- [ ] Notify team of release
- [ ] Update project status
- [ ] Document any issues encountered

### External (if applicable)
- [ ] Announce on social media
- [ ] Update website
- [ ] Notify users via email
- [ ] Post in community forums

## Monitoring

### First 24 Hours
- [ ] Monitor GitHub issues for problems
- [ ] Check download statistics
- [ ] Review error reports (if telemetry enabled)
- [ ] Respond to user feedback

### First Week
- [ ] Review crash reports
- [ ] Monitor for critical bugs
- [ ] Plan hotfix if needed
- [ ] Gather user feedback

## Rollback (If Needed)

If critical issues are found:

### Delete Release
- [ ] Go to GitHub release page
- [ ] Click "Delete release"
- [ ] Confirm deletion

### Delete Tag
- [ ] Locally: `git tag -d v1.0.1`
- [ ] Remotely: `git push origin :refs/tags/v1.0.1`

### Revert Commit
- [ ] `git reset --soft HEAD~1`
- [ ] `git push origin main --force`

### Communicate
- [ ] Notify users of issue
- [ ] Explain rollback reason
- [ ] Provide timeline for fix

## Success Criteria

Release is successful when:
- [ ] All installers built and uploaded
- [ ] GitHub release published
- [ ] No critical bugs reported in first 24 hours
- [ ] Auto-update working (if tested)
- [ ] Users can download and install successfully

## Notes

### Issues Encountered
```
[Record any issues here]
```

### Time Taken
```
Start time: ___________
End time: ___________
Total: ___________
```

### Lessons Learned
```
[Record lessons learned for next release]
```

## Next Release

### Improvements for Next Time
- [ ] [Add improvements here]

### Version Planning
- [ ] Plan next version number
- [ ] Identify features for next release
- [ ] Update roadmap

---

## Quick Reference

**Dry Run:** `npm run release:dry`

**Release:** `npm run release`

**Rollback:** See "Rollback (If Needed)" section above

**Support:** See `RELEASE_GUIDE.md` or `docs/reference/troubleshooting.md`

---

**Date:** ___________

**Released by:** ___________

**Status:** ⬜ Not Started | ⬜ In Progress | ⬜ Complete | ⬜ Rolled Back
