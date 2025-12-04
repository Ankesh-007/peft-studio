#!/usr/bin/env node

/**
 * Release Validation Script
 * 
 * Validates repository readiness for release by checking:
 * - Repository structure and documentation
 * - package.json metadata completeness
 * - Semantic versioning compliance
 * - CHANGELOG version verification
 * - Test execution and verification
 * - Working directory cleanliness
 * 
 * Requirements: 6.1, 6.2, 6.3, 6.4, 10.1, 10.2, 10.3, 10.4, 10.5
 * 
 * Usage:
 *   node scripts/validate-release.js [--skip-tests]
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
};

function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

/**
 * Validate repository structure
 * @param {string} rootDir - Root directory of repository
 * @returns {Object} - Validation result
 */
function validateStructure(rootDir = process.cwd()) {
  log('\n=== Validating Repository Structure ===', colors.bright);
  
  const result = {
    valid: true,
    gitignoreCorrect: false,
    docsWellFormatted: false,
    licenseExists: false,
    errors: [],
  };
  
  // Check for LICENSE file
  const licensePath = path.join(rootDir, 'LICENSE');
  if (fs.existsSync(licensePath)) {
    log('  ✓ LICENSE file exists', colors.green);
    result.licenseExists = true;
  } else {
    log('  ✗ LICENSE file not found', colors.red);
    result.errors.push('LICENSE file is missing');
    result.valid = false;
  }
  
  // Check for .gitignore
  const gitignorePath = path.join(rootDir, '.gitignore');
  if (fs.existsSync(gitignorePath)) {
    const gitignoreContent = fs.readFileSync(gitignorePath, 'utf8');
    
    // Check for essential patterns
    const essentialPatterns = [
      'node_modules',
      'dist',
      '*.log',
    ];
    
    const missingPatterns = essentialPatterns.filter(
      pattern => !gitignoreContent.includes(pattern)
    );
    
    if (missingPatterns.length === 0) {
      log('  ✓ .gitignore contains essential patterns', colors.green);
      result.gitignoreCorrect = true;
    } else {
      log(`  ⚠ .gitignore missing patterns: ${missingPatterns.join(', ')}`, colors.yellow);
      result.errors.push(`Missing .gitignore patterns: ${missingPatterns.join(', ')}`);
    }
  } else {
    log('  ✗ .gitignore not found', colors.red);
    result.errors.push('.gitignore file is missing');
    result.valid = false;
  }
  
  // Check for essential documentation files
  const requiredDocs = ['README.md', 'CONTRIBUTING.md', 'CHANGELOG.md'];
  const missingDocs = [];
  
  for (const doc of requiredDocs) {
    const docPath = path.join(rootDir, doc);
    if (fs.existsSync(docPath)) {
      // Check if file is not empty
      const content = fs.readFileSync(docPath, 'utf8').trim();
      if (content.length > 0) {
        log(`  ✓ ${doc} exists and is not empty`, colors.green);
      } else {
        log(`  ⚠ ${doc} exists but is empty`, colors.yellow);
        result.errors.push(`${doc} is empty`);
      }
    } else {
      log(`  ✗ ${doc} not found`, colors.red);
      missingDocs.push(doc);
      result.valid = false;
    }
  }
  
  if (missingDocs.length > 0) {
    result.errors.push(`Missing documentation files: ${missingDocs.join(', ')}`);
  }
  
  result.docsWellFormatted = missingDocs.length === 0;
  
  return result;
}

/**
 * Validate package.json metadata
 * @param {string} rootDir - Root directory of repository
 * @returns {Object} - Validation result
 */
function validateMetadata(rootDir = process.cwd()) {
  log('\n=== Validating package.json Metadata ===', colors.bright);
  
  const result = {
    valid: true,
    packageJsonComplete: false,
    versionValid: false,
    repositoryUrlCorrect: false,
    errors: [],
  };
  
  const packageJsonPath = path.join(rootDir, 'package.json');
  
  if (!fs.existsSync(packageJsonPath)) {
    log('  ✗ package.json not found', colors.red);
    result.errors.push('package.json file is missing');
    result.valid = false;
    return result;
  }
  
  try {
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    
    // Check required fields
    const requiredFields = ['name', 'version', 'description', 'author', 'license'];
    const missingFields = requiredFields.filter(field => !packageJson[field]);
    
    if (missingFields.length === 0) {
      log('  ✓ All required fields present', colors.green);
      result.packageJsonComplete = true;
    } else {
      log(`  ✗ Missing required fields: ${missingFields.join(', ')}`, colors.red);
      result.errors.push(`Missing package.json fields: ${missingFields.join(', ')}`);
      result.valid = false;
    }
    
    // Validate version format (semantic versioning)
    if (packageJson.version) {
      const versionValid = validateSemanticVersion(packageJson.version);
      if (versionValid) {
        log(`  ✓ Version follows semantic versioning: ${packageJson.version}`, colors.green);
        result.versionValid = true;
      } else {
        log(`  ✗ Version does not follow semantic versioning: ${packageJson.version}`, colors.red);
        result.errors.push(`Invalid version format: ${packageJson.version}`);
        result.valid = false;
      }
    }
    
    // Check repository URL
    if (packageJson.repository) {
      const repoUrl = typeof packageJson.repository === 'string' 
        ? packageJson.repository 
        : packageJson.repository.url;
      
      if (repoUrl && repoUrl.includes('github.com')) {
        log(`  ✓ Repository URL is valid: ${repoUrl}`, colors.green);
        result.repositoryUrlCorrect = true;
      } else {
        log(`  ⚠ Repository URL may be incorrect: ${repoUrl}`, colors.yellow);
        result.errors.push('Repository URL may be incorrect');
      }
    } else {
      log('  ⚠ Repository URL not specified', colors.yellow);
      result.errors.push('Repository URL is missing');
    }
    
    // Check for keywords
    if (!packageJson.keywords || packageJson.keywords.length === 0) {
      log('  ⚠ No keywords specified for discoverability', colors.yellow);
      result.errors.push('No keywords specified');
    } else {
      log(`  ✓ Keywords specified: ${packageJson.keywords.length}`, colors.green);
    }
    
  } catch (err) {
    log(`  ✗ Error reading package.json: ${err.message}`, colors.red);
    result.errors.push(`Error reading package.json: ${err.message}`);
    result.valid = false;
  }
  
  return result;
}

/**
 * Validate semantic versioning format
 * @param {string} version - Version string
 * @returns {boolean} - True if valid semantic version
 */
function validateSemanticVersion(version) {
  // Semantic versioning regex: MAJOR.MINOR.PATCH with optional pre-release and build metadata
  const semverRegex = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$/;
  return semverRegex.test(version);
}

/**
 * Verify CHANGELOG version
 * @param {string} rootDir - Root directory of repository
 * @returns {Object} - Validation result
 */
function verifyChangelogVersion(rootDir = process.cwd()) {
  log('\n=== Verifying CHANGELOG Version ===', colors.bright);
  
  const result = {
    valid: true,
    changelogUpdated: false,
    versionMatches: false,
    errors: [],
  };
  
  const changelogPath = path.join(rootDir, 'CHANGELOG.md');
  const packageJsonPath = path.join(rootDir, 'package.json');
  
  if (!fs.existsSync(changelogPath)) {
    log('  ✗ CHANGELOG.md not found', colors.red);
    result.errors.push('CHANGELOG.md is missing');
    result.valid = false;
    return result;
  }
  
  if (!fs.existsSync(packageJsonPath)) {
    log('  ✗ package.json not found', colors.red);
    result.errors.push('package.json is missing');
    result.valid = false;
    return result;
  }
  
  try {
    const changelogContent = fs.readFileSync(changelogPath, 'utf8');
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    const currentVersion = packageJson.version;
    
    // Check if current version is mentioned in CHANGELOG
    const versionPattern = new RegExp(`##?\\s*\\[?${currentVersion.replace(/\./g, '\\.')}\\]?`, 'i');
    
    if (versionPattern.test(changelogContent)) {
      log(`  ✓ CHANGELOG contains entry for version ${currentVersion}`, colors.green);
      result.changelogUpdated = true;
      result.versionMatches = true;
    } else {
      log(`  ✗ CHANGELOG does not contain entry for version ${currentVersion}`, colors.red);
      result.errors.push(`CHANGELOG missing entry for version ${currentVersion}`);
      result.valid = false;
    }
    
  } catch (err) {
    log(`  ✗ Error verifying CHANGELOG: ${err.message}`, colors.red);
    result.errors.push(`Error verifying CHANGELOG: ${err.message}`);
    result.valid = false;
  }
  
  return result;
}

/**
 * Execute and verify tests
 * @param {boolean} skipTests - Whether to skip test execution
 * @returns {Object} - Validation result
 */
function executeTests(skipTests = false) {
  log('\n=== Executing Tests ===', colors.bright);
  
  const result = {
    valid: true,
    testsPass: false,
    errors: [],
  };
  
  if (skipTests) {
    log('  ⚠ Tests skipped (--skip-tests flag)', colors.yellow);
    result.testsPass = true; // Don't fail validation if tests are skipped
    return result;
  }
  
  try {
    log('  Running tests...', colors.cyan);
    execSync('npm run test:run', { stdio: 'inherit' });
    log('  ✓ All tests passed', colors.green);
    result.testsPass = true;
  } catch (err) {
    log('  ✗ Tests failed', colors.red);
    result.errors.push('Test execution failed');
    result.valid = false;
  }
  
  return result;
}

/**
 * Check working directory cleanliness
 * @param {string} rootDir - Root directory of repository
 * @returns {Object} - Validation result
 */
function checkWorkingDirectory(rootDir = process.cwd()) {
  log('\n=== Checking Working Directory ===', colors.bright);
  
  const result = {
    valid: true,
    workingDirectoryClean: false,
    errors: [],
  };
  
  try {
    // Check if git is available
    execSync('git --version', { stdio: 'ignore' });
    
    // Check for uncommitted changes
    const status = execSync('git status --porcelain', { 
      cwd: rootDir,
      encoding: 'utf8' 
    });
    
    if (status.trim().length === 0) {
      log('  ✓ Working directory is clean', colors.green);
      result.workingDirectoryClean = true;
    } else {
      log('  ✗ Working directory has uncommitted changes:', colors.red);
      const lines = status.trim().split('\n');
      lines.slice(0, 10).forEach(line => {
        log(`    ${line}`, colors.yellow);
      });
      if (lines.length > 10) {
        log(`    ... and ${lines.length - 10} more`, colors.yellow);
      }
      result.errors.push('Working directory has uncommitted changes');
      result.valid = false;
    }
    
  } catch (err) {
    log('  ⚠ Git not available or not a git repository', colors.yellow);
    result.errors.push('Cannot verify working directory (git not available)');
    // Don't fail validation if git is not available
  }
  
  return result;
}

/**
 * Validate release readiness
 * @param {string} rootDir - Root directory of repository
 * @param {boolean} skipTests - Whether to skip test execution
 * @returns {Object} - Complete validation result
 */
function validateReadiness(rootDir = process.cwd(), skipTests = false) {
  log('\n' + '='.repeat(60), colors.bright);
  log('Release Readiness Validation', colors.bright);
  log('='.repeat(60), colors.bright);
  
  const startTime = Date.now();
  
  // Run all validations
  const structureResult = validateStructure(rootDir);
  const metadataResult = validateMetadata(rootDir);
  const changelogResult = verifyChangelogVersion(rootDir);
  const testResult = executeTests(skipTests);
  const workingDirResult = checkWorkingDirectory(rootDir);
  
  // Aggregate results
  const allResults = {
    ready: true,
    testsPass: testResult.testsPass,
    changelogUpdated: changelogResult.changelogUpdated,
    workingDirectoryClean: workingDirResult.workingDirectoryClean,
    issues: [],
  };
  
  // Collect all errors
  const allErrors = [
    ...structureResult.errors,
    ...metadataResult.errors,
    ...changelogResult.errors,
    ...testResult.errors,
    ...workingDirResult.errors,
  ];
  
  allResults.issues = allErrors;
  allResults.ready = 
    structureResult.valid &&
    metadataResult.valid &&
    changelogResult.valid &&
    testResult.valid &&
    workingDirResult.valid;
  
  // Generate report
  const duration = ((Date.now() - startTime) / 1000).toFixed(2);
  
  log('\n' + '='.repeat(60), colors.bright);
  log('Validation Summary', colors.bright);
  log('='.repeat(60), colors.bright);
  
  log(`\nStructure:        ${structureResult.valid ? '✓ PASS' : '✗ FAIL'}`, 
      structureResult.valid ? colors.green : colors.red);
  log(`Metadata:         ${metadataResult.valid ? '✓ PASS' : '✗ FAIL'}`, 
      metadataResult.valid ? colors.green : colors.red);
  log(`CHANGELOG:        ${changelogResult.valid ? '✓ PASS' : '✗ FAIL'}`, 
      changelogResult.valid ? colors.green : colors.red);
  log(`Tests:            ${testResult.valid ? '✓ PASS' : '✗ FAIL'}`, 
      testResult.valid ? colors.green : colors.red);
  log(`Working Dir:      ${workingDirResult.valid ? '✓ PASS' : '✗ FAIL'}`, 
      workingDirResult.valid ? colors.green : colors.red);
  
  log(`\nDuration:         ${duration}s`, colors.cyan);
  
  if (allResults.ready) {
    log('\n✅ Repository is ready for release!', colors.green);
  } else {
    log('\n❌ Repository is NOT ready for release', colors.red);
    log('\nIssues to address:', colors.yellow);
    allResults.issues.forEach((issue, index) => {
      log(`  ${index + 1}. ${issue}`, colors.yellow);
    });
  }
  
  return allResults;
}

/**
 * Main function
 */
function main() {
  const args = process.argv.slice(2);
  const skipTests = args.includes('--skip-tests');
  
  try {
    const result = validateReadiness(process.cwd(), skipTests);
    process.exit(result.ready ? 0 : 1);
  } catch (err) {
    log(`\n❌ Validation failed: ${err.message}`, colors.red);
    process.exit(1);
  }
}

// Run main function if script is executed directly
if (require.main === module) {
  main();
}

// Export functions for testing
module.exports = {
  validateStructure,
  validateMetadata,
  validateSemanticVersion,
  verifyChangelogVersion,
  executeTests,
  checkWorkingDirectory,
  validateReadiness,
};
