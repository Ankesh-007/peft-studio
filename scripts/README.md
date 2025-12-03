# Build Scripts

This directory contains scripts for building PEFT Studio installers.

## Available Scripts

### build.js
**Cross-platform Node.js build script**

```bash
node scripts/build.js [windows|mac|linux|all]
```

**Features:**
- Works on all platforms
- Color-coded output
- Prerequisite checking
- Build output summary
- Error handling

**Examples:**
```bash
node scripts/build.js all        # Build all platforms
node scripts/build.js windows    # Build Windows only
node scripts/build.js mac        # Build macOS only
node scripts/build.js linux      # Build Linux only
```

### build.sh
**Unix/Linux/macOS shell script**

```bash
chmod +x scripts/build.sh
./scripts/build.sh [windows|mac|linux|all]
```

**Features:**
- Bash-based automation
- Dependency verification
- Build orchestration
- Error handling

**Examples:**
```bash
./scripts/build.sh all        # Build all platforms
./scripts/build.sh windows    # Build Windows only
./scripts/build.sh mac        # Build macOS only
./scripts/build.sh linux      # Build Linux only
```

### build.ps1
**Windows PowerShell script**

```powershell
.\scripts\build.ps1 [windows|mac|linux|all]
```

**Features:**
- PowerShell-native
- Windows-optimized
- Color-coded output
- Error handling

**Examples:**
```powershell
.\scripts\build.ps1 all        # Build all platforms
.\scripts\build.ps1 windows    # Build Windows only
.\scripts\build.ps1 mac        # Build macOS only
.\scripts\build.ps1 linux      # Build Linux only
```

### verify-build-config.js
**Build configuration verification**

```bash
node scripts/verify-build-config.js
# or
npm run verify:build
```

**Checks:**
- package.json build configuration
- Build scripts presence
- Build assets (icons, entitlements)
- CI/CD workflows
- Required dependencies

**Output:**
```
✓ Build configuration found
✓ All platform targets configured
✓ All build scripts present
✓ Build assets directory exists
✓ macOS entitlements configured
✓ CI/CD workflows configured
✓ All dependencies installed
```

## NPM Scripts

Alternatively, use npm scripts from the project root:

```bash
# Build all platforms
npm run package:all

# Build single platform
npm run package:win
npm run package:mac
npm run package:linux

# Using build scripts
npm run dist           # All platforms
npm run dist:win       # Windows only
npm run dist:mac       # macOS only
npm run dist:linux     # Linux only

# Verify configuration
npm run verify:build
```

## Build Process

All scripts follow the same process:

1. **Check Prerequisites**
   - Verify Node.js and npm are installed
   - Check if node_modules exists
   - Verify build assets

2. **Build Frontend**
   - Run `npm run build`
   - Compile TypeScript
   - Bundle with Vite
   - Optimize assets

3. **Build Installer**
   - Run electron-builder for target platform(s)
   - Apply code signing if configured
   - Generate installers

4. **Show Output**
   - List generated installers
   - Display file sizes
   - Show output location

## Output Location

All installers are created in the `release/` directory:

```
release/
├── PEFT-Studio-Setup-1.0.0.exe          # Windows installer
├── PEFT-Studio-1.0.0-portable.exe       # Windows portable
├── PEFT-Studio-1.0.0.dmg                # macOS installer
├── PEFT-Studio-1.0.0-mac.zip            # macOS archive
├── PEFT-Studio-1.0.0.AppImage           # Linux universal
└── peft-studio_1.0.0_amd64.deb          # Linux Debian/Ubuntu
```

## Code Signing

To enable code signing, set environment variables before running build scripts:

### Windows
```bash
# PowerShell
$env:CSC_LINK = "C:\path\to\certificate.pfx"
$env:CSC_KEY_PASSWORD = "your_password"

# Command Prompt
set CSC_LINK=C:\path\to\certificate.pfx
set CSC_KEY_PASSWORD=your_password
```

### macOS
```bash
export CSC_LINK=/path/to/certificate.p12
export CSC_KEY_PASSWORD=your_password
export APPLE_ID=your@email.com
export APPLE_ID_PASSWORD=app-specific-password
```

## Troubleshooting

### Build fails with "Cannot find module"
```bash
rm -rf node_modules package-lock.json
npm install
```

### Permission denied (Unix/Linux/macOS)
```bash
chmod +x scripts/build.sh
```

### PowerShell execution policy error (Windows)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Missing icons warning
Add icon files to `build/` directory:
- `icon.ico` (Windows)
- `icon.icns` (macOS)
- `icon.png` (Linux)

See `build/README.md` for icon generation instructions.

## Documentation

- **Build and Installer Guide:** `../docs/developer-guide/build-and-installers.md` - Comprehensive guide covering all aspects of building and distributing installers

## Support

For issues or questions:
- Review documentation in project root
- Check GitHub Actions logs for CI failures
- Consult electron-builder documentation


---

## Repository Configuration Scripts

### configure-repository.sh / configure-repository.ps1
**Automates GitHub repository configuration for public release**

```bash
# Unix/Linux/macOS
./scripts/configure-repository.sh

# Windows
./scripts/configure-repository.ps1
```

**Configures:**
- Repository description and metadata
- Topics and tags for discoverability
- Issues, Projects, and Discussions
- Basic repository settings

**Requirements:**
- GitHub CLI (gh) installed: https://cli.github.com/
- GitHub authentication: `gh auth login`
- Admin access to repository

### verify-branch-protection.sh / verify-branch-protection.ps1
**Verifies GitHub branch protection rules**

```bash
# Unix/Linux/macOS
./scripts/verify-branch-protection.sh

# Windows
./scripts/verify-branch-protection.ps1
```

**Checks:**
- Branch protection enabled for main
- Required pull request reviews
- Required status checks
- Enforce admins setting
- Required conversation resolution

### verify-workflows.sh / verify-workflows.ps1
**Validates GitHub Actions workflow files**

```bash
# Unix/Linux/macOS
./scripts/verify-workflows.sh

# Windows
./scripts/verify-workflows.ps1
```

**Checks:**
- All required workflow files present
- YAML syntax validity
- Workflow triggers configured
- Required jobs present
- GitHub Actions directory structure

## Security Scripts

### security-scan.sh / security-scan.ps1
**Comprehensive security scanning**

```bash
# Unix/Linux/macOS
./scripts/security-scan.sh

# Windows
./scripts/security-scan.ps1
```

**Scans:**
- npm dependencies for vulnerabilities
- Python dependencies for vulnerabilities
- Git history for secrets
- Environment files for credentials
- Database files for sensitive data

## Publishing Scripts

### publish.ps1
**Pre-publication verification and checklist**

```powershell
./scripts/publish.ps1
```

**Verifies:**
- Security scans pass
- All tests pass
- Build succeeds
- Documentation complete
- Community standards met

### quick-start.ps1
**Quick start script for new developers**

```powershell
./scripts/quick-start.ps1
```

**Features:**
- Checks prerequisites
- Installs dependencies
- Sets up development environment
- Runs initial build

---

## Repository Configuration Workflow

For preparing the repository for public release:

1. **Run security scan** to ensure no sensitive data
   ```bash
   ./scripts/security-scan.sh  # or .ps1
   ```

2. **Configure repository** with automated script
   ```bash
   ./scripts/configure-repository.sh  # or .ps1
   ```

3. **Complete manual steps** from script output

4. **Verify configuration**
   ```bash
   ./scripts/verify-branch-protection.sh  # or .ps1
   ./scripts/verify-workflows.sh  # or .ps1
   ```

5. **Run pre-publication checks**
   ```powershell
   ./scripts/publish.ps1
   ```

See `.github/REPOSITORY_CONFIGURATION_GUIDE.md` for detailed instructions.

---

## Related Documentation

- `.github/REPOSITORY_CONFIGURATION_GUIDE.md` - Comprehensive repository setup guide
- `.github/REPOSITORY_CONFIGURATION_CHECKLIST.md` - Configuration checklist
- `.github/REPOSITORY_CONFIGURATION_SUMMARY.md` - Configuration summary
- `CONTRIBUTING.md` - Contribution guidelines
- `SECURITY.md` - Security policy
- `docs/developer-guide/build-and-installers.md` - Build and installer guide

---

**For public release preparation:** Follow the workflow in `.github/REPOSITORY_CONFIGURATION_GUIDE.md`
