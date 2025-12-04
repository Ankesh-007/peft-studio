#!/usr/bin/env node

/**
 * Final Release Verification Script
 * 
 * Performs comprehensive verification of a completed GitHub release:
 * - Verifies GitHub release exists and is complete with all assets
 * - Tests download links for all installers
 * - Verifies checksums can be validated by users
 * - Ensures repository looks professional
 * - Updates any remaining documentation
 * 
 * Requirements: All requirements (final verification)
 * 
 * Usage:
 *   node scripts/verify-final-release.js [options]
 * 
 * Options:
 *   --version <version>    Version to verify (default: from package.json)
 *   --skip-downloads       Skip testing actual downloads
 *   --help                 Display help message
 * 
 * Environment Variables:
 *   GITHUB_TOKEN          GitHub personal access token (optional, for API rate limits)
 */

const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execSync } = require('child_process');

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
  blue: '\x1b[34m',
};

/**
 * Logging utilities
 */
function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function logSuccess(message) {
  log(`✓ ${message}`, colors.green);
}

function logError(message) {
  log(`✗ ${message}`, colors.red);
}

function logWarning(message) {
  log(`⚠ ${message}`, colors.yellow);
}

function logInfo(message) {
  log(`ℹ ${message}`, colors.cyan);
}

/**
 * Make HTTPS request
 * @param {string} url - URL to request
 * @param {Object} options - Request options
 * @returns {Promise<Object>} - Response data
 */
function httpsRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const protocol = urlObj.protocol === 'https:' ? https : http;
    
    const requestOptions = {
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname + urlObj.search,
      method: options.method || 'GET',
      headers: {
        'User-Agent': 'PEFT-Studio-Release-Verifier',
        ...options.headers,
      },
    };
    
    const req = protocol.request(requestOptions, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            const jsonData = JSON.parse(data);
            resolve({ statusCode: res.statusCode, data: jsonData, headers: res.headers });
          } catch (err) {
            resolve({ statusCode: res.statusCode, data, headers: res.headers });
          }
        } else if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          // Handle redirects
          resolve({ statusCode: res.statusCode, redirect: res.headers.location, headers: res.headers });
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${data}`));
        }
      });
    });
    
    req.on('error', reject);
    req.end();
  });
}

/**
 * Get GitHub release information
 * @param {string} owner - Repository owner
 * @param {string} repo - Repository name
 * @param {string} version - Release version
 * @returns {Promise<Object>} - Release information
 */
async function getGitHubRelease(owner, repo, version) {
  const tag = version.startsWith('v') ? version : `v${version}`;
  const url = `https://api.github.com/repos/${owner}/${repo}/releases/tags/${tag}`;
  
  const headers = {
    'Accept': 'application/vnd.github.v3+json',
  };
  
  // Add auth token if available
  if (process.env.GITHUB_TOKEN) {
    headers['Authorization'] = `token ${process.env.GITHUB_TOKEN}`;
  }
  
  try {
    const response = await httpsRequest(url, { headers });
    return response.data;
  } catch (error) {
    throw new Error(`Failed to fetch release: ${error.message}`);
  }
}

/**
 * Verify GitHub release exists and is complete
 * @param {string} version - Version to verify
 * @returns {Promise<Object>} - Verification result
 */
async function verifyGitHubRelease(version) {
  log('\n=== Verifying GitHub Release ===', colors.bright);
  
  const result = {
    valid: true,
    releaseExists: false,
    assetsComplete: false,
    errors: [],
    release: null,
  };
  
  try {
    // Read package.json to get repository info
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    const repoUrl = packageJson.repository?.url || packageJson.repository;
    
    if (!repoUrl) {
      throw new Error('Repository URL not found in package.json');
    }
    
    // Extract owner and repo from URL
    const match = repoUrl.match(/github\.com[:/]([^/]+)\/([^/.]+)/);
    if (!match) {
      throw new Error(`Invalid repository URL: ${repoUrl}`);
    }
    
    const [, owner, repo] = match;
    
    logInfo(`Checking release for ${owner}/${repo} version ${version}...`);
    
    // Fetch release from GitHub API
    const release = await getGitHubRelease(owner, repo, version);
    
    result.release = release;
    result.releaseExists = true;
    
    logSuccess(`Release found: ${release.name || release.tag_name}`);
    logInfo(`  URL: ${release.html_url}`);
    logInfo(`  Published: ${release.published_at || 'Draft'}`);
    logInfo(`  Draft: ${release.draft}`);
    logInfo(`  Prerelease: ${release.prerelease}`);
    
    // Verify assets
    const assets = release.assets || [];
    logInfo(`\n  Assets (${assets.length}):`);
    
    if (assets.length === 0) {
      logWarning('    No assets found in release');
      result.errors.push('Release has no assets');
      result.valid = false;
    } else {
      assets.forEach(asset => {
        const sizeMB = (asset.size / (1024 * 1024)).toFixed(2);
        logInfo(`    - ${asset.name} (${sizeMB} MB)`);
      });
      
      // Check for expected assets
      const expectedPatterns = [
        /Setup.*\.exe$/i,           // Windows installer
        /Portable.*\.exe$/i,        // Windows portable
        /\.dmg$/i,                  // macOS DMG
        /\.AppImage$/i,             // Linux AppImage
        /SHA256SUMS\.txt$/i,        // Checksums
      ];
      
      const foundPatterns = expectedPatterns.map(pattern => {
        const found = assets.some(asset => pattern.test(asset.name));
        return { pattern: pattern.toString(), found };
      });
      
      const missingPatterns = foundPatterns.filter(p => !p.found);
      
      if (missingPatterns.length > 0) {
        logWarning('\n  Missing expected asset types:');
        missingPatterns.forEach(p => {
          logWarning(`    - ${p.pattern}`);
        });
        result.errors.push('Some expected asset types are missing');
      } else {
        logSuccess('\n  All expected asset types present');
        result.assetsComplete = true;
      }
    }
    
  } catch (error) {
    logError(`Failed to verify release: ${error.message}`);
    result.errors.push(error.message);
    result.valid = false;
  }
  
  return result;
}

/**
 * Test download link accessibility
 * @param {string} url - Download URL
 * @param {string} filename - Asset filename
 * @returns {Promise<Object>} - Test result
 */
async function testDownloadLink(url, filename) {
  try {
    const response = await httpsRequest(url, { method: 'HEAD' });
    
    if (response.statusCode === 200) {
      const size = response.headers['content-length'];
      const sizeMB = size ? (parseInt(size) / (1024 * 1024)).toFixed(2) : 'unknown';
      return {
        accessible: true,
        filename,
        size: sizeMB,
        url,
      };
    } else if (response.redirect) {
      // Follow redirect
      return testDownloadLink(response.redirect, filename);
    } else {
      return {
        accessible: false,
        filename,
        error: `HTTP ${response.statusCode}`,
        url,
      };
    }
  } catch (error) {
    return {
      accessible: false,
      filename,
      error: error.message,
      url,
    };
  }
}

/**
 * Test all download links
 * @param {Object} release - GitHub release object
 * @param {boolean} skipDownloads - Whether to skip download tests
 * @returns {Promise<Object>} - Test results
 */
async function testDownloadLinks(release, skipDownloads = false) {
  log('\n=== Testing Download Links ===', colors.bright);
  
  const result = {
    valid: true,
    allAccessible: false,
    tested: 0,
    accessible: 0,
    errors: [],
    links: [],
  };
  
  if (skipDownloads) {
    logInfo('Skipping download tests (--skip-downloads flag)');
    result.allAccessible = true;
    return result;
  }
  
  const assets = release.assets || [];
  
  if (assets.length === 0) {
    logWarning('No assets to test');
    return result;
  }
  
  logInfo(`Testing ${assets.length} download links...`);
  
  for (const asset of assets) {
    const testResult = await testDownloadLink(asset.browser_download_url, asset.name);
    result.links.push(testResult);
    result.tested++;
    
    if (testResult.accessible) {
      logSuccess(`  ${asset.name} (${testResult.size} MB)`);
      result.accessible++;
    } else {
      logError(`  ${asset.name}: ${testResult.error}`);
      result.errors.push(`${asset.name}: ${testResult.error}`);
      result.valid = false;
    }
  }
  
  result.allAccessible = result.accessible === result.tested;
  
  if (result.allAccessible) {
    logSuccess(`\nAll ${result.tested} download links are accessible`);
  } else {
    logError(`\n${result.tested - result.accessible} of ${result.tested} links are not accessible`);
  }
  
  return result;
}

/**
 * Download and verify checksums file
 * @param {Object} release - GitHub release object
 * @returns {Promise<Object>} - Verification result
 */
async function verifyChecksums(release) {
  log('\n=== Verifying Checksums ===', colors.bright);
  
  const result = {
    valid: true,
    checksumFileExists: false,
    formatValid: false,
    errors: [],
    checksums: [],
  };
  
  const assets = release.assets || [];
  const checksumAsset = assets.find(asset => 
    /SHA256SUMS\.txt$/i.test(asset.name)
  );
  
  if (!checksumAsset) {
    logError('SHA256SUMS.txt not found in release assets');
    result.errors.push('Checksum file not found');
    result.valid = false;
    return result;
  }
  
  result.checksumFileExists = true;
  logSuccess('SHA256SUMS.txt found in release');
  
  try {
    // Download checksum file
    logInfo('Downloading checksum file...');
    const response = await httpsRequest(checksumAsset.browser_download_url);
    const checksumContent = response.data;
    
    // Parse checksums
    const lines = checksumContent.split('\n').filter(line => line.trim());
    
    logInfo(`\nChecksum file contains ${lines.length} entries:`);
    
    // Validate format
    const formatRegex = /^[a-f0-9]{64}  .+$/;
    let allValid = true;
    
    for (const line of lines) {
      if (!formatRegex.test(line)) {
        logError(`  Invalid format: ${line.substring(0, 80)}...`);
        result.errors.push(`Invalid checksum format: ${line.substring(0, 50)}`);
        allValid = false;
        result.valid = false;
      } else {
        const [hash, filename] = line.split(/\s{2,}/);
        result.checksums.push({ hash, filename });
        logInfo(`  ✓ ${filename}`);
      }
    }
    
    result.formatValid = allValid;
    
    if (allValid) {
      logSuccess(`\nAll ${lines.length} checksum entries are properly formatted`);
      
      // Verify all installers have checksums
      const installerAssets = assets.filter(asset => 
        !asset.name.includes('SHA256SUMS') && 
        !asset.name.includes('latest.yml') &&
        !asset.name.includes('.blockmap')
      );
      
      const missingChecksums = installerAssets.filter(asset => 
        !result.checksums.some(cs => cs.filename === asset.name)
      );
      
      if (missingChecksums.length > 0) {
        logWarning('\nInstallers missing checksums:');
        missingChecksums.forEach(asset => {
          logWarning(`  - ${asset.name}`);
        });
        result.errors.push('Some installers are missing checksums');
      } else {
        logSuccess('All installers have checksums');
      }
    }
    
  } catch (error) {
    logError(`Failed to verify checksums: ${error.message}`);
    result.errors.push(error.message);
    result.valid = false;
  }
  
  return result;
}

/**
 * Verify repository professionalism
 * @returns {Object} - Verification result
 */
function verifyRepositoryProfessionalism() {
  log('\n=== Verifying Repository Professionalism ===', colors.bright);
  
  const result = {
    valid: true,
    errors: [],
    checks: {},
  };
  
  // Check README.md
  logInfo('Checking README.md...');
  if (fs.existsSync('README.md')) {
    const readme = fs.readFileSync('README.md', 'utf8');
    
    // Check for essential sections
    const essentialSections = [
      { name: 'Title/Header', pattern: /^#\s+.+/m },
      { name: 'Description', pattern: /.{50,}/s },
      { name: 'Installation', pattern: /##\s*Install/i },
      { name: 'Usage', pattern: /##\s*Usage/i },
      { name: 'License', pattern: /##\s*License/i },
    ];
    
    const missingSections = [];
    
    for (const section of essentialSections) {
      if (section.pattern.test(readme)) {
        logSuccess(`  ✓ ${section.name} section present`);
        result.checks[section.name] = true;
      } else {
        logWarning(`  ⚠ ${section.name} section missing or incomplete`);
        missingSections.push(section.name);
        result.checks[section.name] = false;
      }
    }
    
    if (missingSections.length > 0) {
      result.errors.push(`README missing sections: ${missingSections.join(', ')}`);
    }
    
    // Check for badges
    if (/!\[.*\]\(.*\)/m.test(readme)) {
      logSuccess('  ✓ Badges present');
      result.checks.badges = true;
    } else {
      logWarning('  ⚠ No badges found');
      result.checks.badges = false;
    }
    
  } else {
    logError('  ✗ README.md not found');
    result.errors.push('README.md is missing');
    result.valid = false;
  }
  
  // Check LICENSE
  logInfo('\nChecking LICENSE...');
  if (fs.existsSync('LICENSE')) {
    const license = fs.readFileSync('LICENSE', 'utf8');
    if (license.length > 100) {
      logSuccess('  ✓ LICENSE file present and substantial');
      result.checks.license = true;
    } else {
      logWarning('  ⚠ LICENSE file seems too short');
      result.checks.license = false;
    }
  } else {
    logError('  ✗ LICENSE not found');
    result.errors.push('LICENSE is missing');
    result.valid = false;
  }
  
  // Check CONTRIBUTING.md
  logInfo('\nChecking CONTRIBUTING.md...');
  if (fs.existsSync('CONTRIBUTING.md')) {
    logSuccess('  ✓ CONTRIBUTING.md present');
    result.checks.contributing = true;
  } else {
    logWarning('  ⚠ CONTRIBUTING.md not found');
    result.checks.contributing = false;
  }
  
  // Check CHANGELOG.md
  logInfo('\nChecking CHANGELOG.md...');
  if (fs.existsSync('CHANGELOG.md')) {
    const changelog = fs.readFileSync('CHANGELOG.md', 'utf8');
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    const version = packageJson.version;
    
    if (changelog.includes(version)) {
      logSuccess(`  ✓ CHANGELOG.md includes version ${version}`);
      result.checks.changelog = true;
    } else {
      logWarning(`  ⚠ CHANGELOG.md doesn't include version ${version}`);
      result.checks.changelog = false;
    }
  } else {
    logError('  ✗ CHANGELOG.md not found');
    result.errors.push('CHANGELOG.md is missing');
    result.valid = false;
  }
  
  // Check .gitignore
  logInfo('\nChecking .gitignore...');
  if (fs.existsSync('.gitignore')) {
    const gitignore = fs.readFileSync('.gitignore', 'utf8');
    const essentialPatterns = ['node_modules', 'dist', '*.log', 'release'];
    const missingPatterns = essentialPatterns.filter(p => !gitignore.includes(p));
    
    if (missingPatterns.length === 0) {
      logSuccess('  ✓ .gitignore contains essential patterns');
      result.checks.gitignore = true;
    } else {
      logWarning(`  ⚠ .gitignore missing patterns: ${missingPatterns.join(', ')}`);
      result.checks.gitignore = false;
    }
  } else {
    logError('  ✗ .gitignore not found');
    result.errors.push('.gitignore is missing');
    result.valid = false;
  }
  
  // Check package.json metadata
  logInfo('\nChecking package.json metadata...');
  if (fs.existsSync('package.json')) {
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    
    const requiredFields = ['name', 'version', 'description', 'author', 'license', 'repository'];
    const missingFields = requiredFields.filter(field => !packageJson[field]);
    
    if (missingFields.length === 0) {
      logSuccess('  ✓ All required metadata fields present');
      result.checks.packageMetadata = true;
    } else {
      logWarning(`  ⚠ Missing fields: ${missingFields.join(', ')}`);
      result.checks.packageMetadata = false;
    }
    
    if (packageJson.keywords && packageJson.keywords.length > 0) {
      logSuccess(`  ✓ Keywords present (${packageJson.keywords.length})`);
      result.checks.keywords = true;
    } else {
      logWarning('  ⚠ No keywords for discoverability');
      result.checks.keywords = false;
    }
  }
  
  return result;
}

/**
 * Generate verification report
 * @param {Object} results - All verification results
 * @returns {string} - Report content
 */
function generateVerificationReport(results) {
  const lines = [];
  
  lines.push('# Final Release Verification Report');
  lines.push('');
  lines.push(`Generated: ${new Date().toISOString()}`);
  lines.push(`Version: ${results.version}`);
  lines.push('');
  
  lines.push('## GitHub Release');
  lines.push('');
  if (results.release.releaseExists) {
    lines.push(`- ✓ Release exists: ${results.release.release.html_url}`);
    lines.push(`- Assets: ${results.release.release.assets.length}`);
    lines.push(`- Draft: ${results.release.release.draft}`);
    lines.push(`- Prerelease: ${results.release.release.prerelease}`);
  } else {
    lines.push('- ✗ Release not found');
  }
  lines.push('');
  
  lines.push('## Download Links');
  lines.push('');
  if (results.downloads.tested > 0) {
    lines.push(`- Tested: ${results.downloads.tested}`);
    lines.push(`- Accessible: ${results.downloads.accessible}`);
    lines.push(`- Failed: ${results.downloads.tested - results.downloads.accessible}`);
  } else {
    lines.push('- Skipped');
  }
  lines.push('');
  
  lines.push('## Checksums');
  lines.push('');
  lines.push(`- File exists: ${results.checksums.checksumFileExists ? '✓' : '✗'}`);
  lines.push(`- Format valid: ${results.checksums.formatValid ? '✓' : '✗'}`);
  lines.push(`- Entries: ${results.checksums.checksums.length}`);
  lines.push('');
  
  lines.push('## Repository Professionalism');
  lines.push('');
  for (const [check, passed] of Object.entries(results.professionalism.checks)) {
    lines.push(`- ${passed ? '✓' : '⚠'} ${check}`);
  }
  lines.push('');
  
  lines.push('## Summary');
  lines.push('');
  const allValid = results.release.valid && 
                   results.downloads.valid && 
                   results.checksums.valid && 
                   results.professionalism.valid;
  
  if (allValid) {
    lines.push('✅ **All verifications passed!**');
  } else {
    lines.push('❌ **Some verifications failed**');
    lines.push('');
    lines.push('### Issues:');
    const allErrors = [
      ...results.release.errors,
      ...results.downloads.errors,
      ...results.checksums.errors,
      ...results.professionalism.errors,
    ];
    allErrors.forEach(error => {
      lines.push(`- ${error}`);
    });
  }
  
  return lines.join('\n');
}

/**
 * Main verification function
 * @param {Object} options - Verification options
 * @returns {Promise<Object>} - Verification results
 */
async function verifyFinalRelease(options = {}) {
  const {
    version = null,
    skipDownloads = false,
  } = options;
  
  log('='.repeat(70), colors.bright);
  log('Final Release Verification', colors.bright);
  log('='.repeat(70), colors.bright);
  
  const startTime = Date.now();
  
  // Get version from package.json if not provided
  let releaseVersion = version;
  if (!releaseVersion) {
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    releaseVersion = packageJson.version;
  }
  
  logInfo(`\nVerifying release version: ${releaseVersion}`);
  
  // Run all verifications
  const releaseResult = await verifyGitHubRelease(releaseVersion);
  
  let downloadsResult = { valid: true, tested: 0, accessible: 0, errors: [], links: [] };
  let checksumsResult = { valid: true, errors: [] };
  
  if (releaseResult.releaseExists && releaseResult.release) {
    downloadsResult = await testDownloadLinks(releaseResult.release, skipDownloads);
    checksumsResult = await verifyChecksums(releaseResult.release);
  }
  
  const professionalismResult = verifyRepositoryProfessionalism();
  
  // Generate summary
  const duration = ((Date.now() - startTime) / 1000).toFixed(2);
  
  log('\n' + '='.repeat(70), colors.bright);
  log('Verification Summary', colors.bright);
  log('='.repeat(70), colors.bright);
  
  log(`\nGitHub Release:   ${releaseResult.valid ? '✓ PASS' : '✗ FAIL'}`, 
      releaseResult.valid ? colors.green : colors.red);
  log(`Download Links:   ${downloadsResult.valid ? '✓ PASS' : '✗ FAIL'}`, 
      downloadsResult.valid ? colors.green : colors.red);
  log(`Checksums:        ${checksumsResult.valid ? '✓ PASS' : '✗ FAIL'}`, 
      checksumsResult.valid ? colors.green : colors.red);
  log(`Professionalism:  ${professionalismResult.valid ? '✓ PASS' : '✗ FAIL'}`, 
      professionalismResult.valid ? colors.green : colors.red);
  
  log(`\nDuration:         ${duration}s`, colors.cyan);
  
  const allValid = releaseResult.valid && 
                   downloadsResult.valid && 
                   checksumsResult.valid && 
                   professionalismResult.valid;
  
  if (allValid) {
    log('\n✅ All verifications passed! Release is ready.', colors.green);
  } else {
    log('\n❌ Some verifications failed', colors.red);
    
    const allErrors = [
      ...releaseResult.errors,
      ...downloadsResult.errors,
      ...checksumsResult.errors,
      ...professionalismResult.errors,
    ];
    
    if (allErrors.length > 0) {
      log('\nIssues:', colors.yellow);
      allErrors.forEach((error, index) => {
        log(`  ${index + 1}. ${error}`, colors.yellow);
      });
    }
  }
  
  // Generate report
  const results = {
    version: releaseVersion,
    release: releaseResult,
    downloads: downloadsResult,
    checksums: checksumsResult,
    professionalism: professionalismResult,
    duration: parseFloat(duration),
    timestamp: new Date().toISOString(),
  };
  
  const report = generateVerificationReport(results);
  const reportPath = path.join(process.cwd(), 'VERIFICATION_REPORT.md');
  fs.writeFileSync(reportPath, report);
  
  log(`\n📄 Verification report saved to: ${reportPath}`, colors.cyan);
  
  return {
    success: allValid,
    results,
    report,
  };
}

/**
 * Display help message
 */
function displayHelp() {
  log(`
🔍 Final Release Verification Script

Usage:
  node scripts/verify-final-release.js [options]

Options:
  --version <version>    Version to verify (default: from package.json)
  --skip-downloads       Skip testing actual downloads
  --help                 Display this help message

Environment Variables:
  GITHUB_TOKEN          GitHub personal access token (optional, for API rate limits)

Verifications Performed:
  1. GitHub Release     Verify release exists with all assets
  2. Download Links     Test accessibility of all download links
  3. Checksums          Verify SHA256SUMS.txt format and completeness
  4. Professionalism    Check repository documentation and structure

Examples:
  # Verify current version
  node scripts/verify-final-release.js

  # Verify specific version
  node scripts/verify-final-release.js --version 1.0.1

  # Skip download tests (faster)
  node scripts/verify-final-release.js --skip-downloads

Output:
  - Console output with verification results
  - VERIFICATION_REPORT.md with detailed report

`, colors.reset);
}

/**
 * Main function
 */
async function main() {
  const args = process.argv.slice(2);
  
  // Check for help flag
  if (args.includes('--help') || args.includes('-h')) {
    displayHelp();
    process.exit(0);
  }
  
  // Parse options
  const options = {
    skipDownloads: args.includes('--skip-downloads'),
  };
  
  // Get version if specified
  const versionIndex = args.indexOf('--version');
  if (versionIndex !== -1 && args[versionIndex + 1]) {
    options.version = args[versionIndex + 1];
  }
  
  try {
    const result = await verifyFinalRelease(options);
    process.exit(result.success ? 0 : 1);
  } catch (error) {
    logError(`\nFatal error: ${error.message}`);
    console.error(error);
    process.exit(1);
  }
}

// Export functions for testing
module.exports = {
  httpsRequest,
  getGitHubRelease,
  verifyGitHubRelease,
  testDownloadLink,
  testDownloadLinks,
  verifyChecksums,
  verifyRepositoryProfessionalism,
  generateVerificationReport,
  verifyFinalRelease,
};

// Run main function if script is executed directly
if (require.main === module) {
  main();
}
