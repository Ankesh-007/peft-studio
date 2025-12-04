#!/usr/bin/env node

/**
 * Build Output Verification Script
 * 
 * This script verifies that the build process has produced all expected outputs
 * and that they meet quality standards.
 * 
 * Validates:
 * - Frontend build outputs (dist/ directory)
 * - Bundle sizes are reasonable
 * - Backend can start successfully
 * 
 * Requirements: 2.4, 2.5
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// ANSI color codes for output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logSection(title) {
  console.log('\n' + '='.repeat(60));
  log(title, 'cyan');
  console.log('='.repeat(60));
}

function logSuccess(message) {
  log(`✓ ${message}`, 'green');
}

function logError(message) {
  log(`✗ ${message}`, 'red');
}

function logWarning(message) {
  log(`⚠ ${message}`, 'yellow');
}

function logInfo(message) {
  log(`ℹ ${message}`, 'blue');
}

// Track verification results
const results = {
  passed: [],
  failed: [],
  warnings: []
};

/**
 * Check if a file or directory exists
 */
function checkExists(filePath, description) {
  const fullPath = path.resolve(filePath);
  if (fs.existsSync(fullPath)) {
    logSuccess(`${description} exists: ${filePath}`);
    results.passed.push(`${description} exists`);
    return true;
  } else {
    logError(`${description} missing: ${filePath}`);
    results.failed.push(`${description} missing: ${filePath}`);
    return false;
  }
}

/**
 * Get file size in KB
 */
function getFileSizeKB(filePath) {
  const stats = fs.statSync(filePath);
  return (stats.size / 1024).toFixed(2);
}

/**
 * Verify frontend build outputs
 */
function verifyFrontendBuild() {
  logSection('Frontend Build Verification');
  
  // Check dist directory exists
  if (!checkExists('dist', 'dist directory')) {
    return false;
  }
  
  // Check index.html
  if (!checkExists('dist/index.html', 'index.html')) {
    return false;
  }
  
  // Check assets directory
  if (!checkExists('dist/assets', 'assets directory')) {
    return false;
  }
  
  // Check for JavaScript bundles
  const assetsDir = path.resolve('dist/assets');
  const files = fs.readdirSync(assetsDir);
  
  const jsFiles = files.filter(f => f.endsWith('.js'));
  const cssFiles = files.filter(f => f.endsWith('.css'));
  
  logInfo(`Found ${jsFiles.length} JavaScript bundles`);
  logInfo(`Found ${cssFiles.length} CSS bundles`);
  
  if (jsFiles.length === 0) {
    logError('No JavaScript bundles found');
    results.failed.push('No JavaScript bundles found');
    return false;
  }
  
  if (cssFiles.length === 0) {
    logError('No CSS bundles found');
    results.failed.push('No CSS bundles found');
    return false;
  }
  
  logSuccess(`Found ${jsFiles.length} JavaScript bundles`);
  logSuccess(`Found ${cssFiles.length} CSS bundles`);
  results.passed.push('JavaScript bundles present');
  results.passed.push('CSS bundles present');
  
  // Check for main entry point
  const mainBundle = jsFiles.find(f => f.startsWith('index-'));
  if (mainBundle) {
    logSuccess(`Main bundle found: ${mainBundle}`);
    results.passed.push('Main bundle present');
  } else {
    logError('Main bundle (index-*.js) not found');
    results.failed.push('Main bundle missing');
    return false;
  }
  
  // Check for vendor bundles (code splitting)
  const vendorBundles = jsFiles.filter(f => f.includes('vendor'));
  if (vendorBundles.length > 0) {
    logSuccess(`Found ${vendorBundles.length} vendor bundles (code splitting enabled)`);
    results.passed.push('Code splitting enabled');
  } else {
    logWarning('No vendor bundles found - code splitting may not be enabled');
    results.warnings.push('Code splitting may not be enabled');
  }
  
  // Check samples directory
  if (checkExists('dist/samples', 'samples directory')) {
    if (checkExists('dist/samples/sample-dataset.jsonl', 'sample dataset')) {
      results.passed.push('Sample data included');
    }
  }
  
  return true;
}

/**
 * Verify bundle sizes are reasonable
 */
function verifyBundleSizes() {
  logSection('Bundle Size Verification');
  
  const assetsDir = path.resolve('dist/assets');
  if (!fs.existsSync(assetsDir)) {
    logError('Assets directory not found');
    return false;
  }
  
  const files = fs.readdirSync(assetsDir);
  const jsFiles = files.filter(f => f.endsWith('.js'));
  const cssFiles = files.filter(f => f.endsWith('.css'));
  
  let totalSizeKB = 0;
  let largeFiles = [];
  
  // Size thresholds (in KB)
  const WARN_THRESHOLD = 500; // Warn if a single file is over 500KB
  const ERROR_THRESHOLD = 1000; // Error if a single file is over 1MB
  
  console.log('\nBundle Sizes:');
  console.log('-'.repeat(60));
  
  [...jsFiles, ...cssFiles].forEach(file => {
    const filePath = path.join(assetsDir, file);
    const sizeKB = parseFloat(getFileSizeKB(filePath));
    totalSizeKB += sizeKB;
    
    let status = '✓';
    let color = 'green';
    
    if (sizeKB > ERROR_THRESHOLD) {
      status = '✗';
      color = 'red';
      largeFiles.push({ file, size: sizeKB, severity: 'error' });
    } else if (sizeKB > WARN_THRESHOLD) {
      status = '⚠';
      color = 'yellow';
      largeFiles.push({ file, size: sizeKB, severity: 'warning' });
    }
    
    log(`${status} ${file}: ${sizeKB} KB`, color);
  });
  
  console.log('-'.repeat(60));
  logInfo(`Total bundle size: ${totalSizeKB.toFixed(2)} KB (${(totalSizeKB / 1024).toFixed(2)} MB)`);
  
  // Report on large files
  if (largeFiles.length > 0) {
    console.log('\nLarge Files:');
    largeFiles.forEach(({ file, size, severity }) => {
      const message = `${file} is ${size.toFixed(2)} KB`;
      if (severity === 'error') {
        logError(message);
        results.failed.push(`Bundle too large: ${file}`);
      } else {
        logWarning(message);
        results.warnings.push(`Large bundle: ${file}`);
      }
    });
  }
  
  // Check total size
  const totalMB = totalSizeKB / 1024;
  if (totalMB > 5) {
    logWarning(`Total bundle size (${totalMB.toFixed(2)} MB) is quite large`);
    results.warnings.push('Total bundle size is large');
  } else {
    logSuccess(`Total bundle size (${totalMB.toFixed(2)} MB) is reasonable`);
    results.passed.push('Bundle sizes are reasonable');
  }
  
  return largeFiles.filter(f => f.severity === 'error').length === 0;
}

/**
 * Verify backend can start
 */
function verifyBackendStart() {
  logSection('Backend Start Verification');
  
  try {
    // Test that backend main.py can be imported
    logInfo('Testing backend import...');
    
    const result = execSync(
      'python -c "import sys; sys.path.insert(0, \'.\'); import main; print(\'SUCCESS\')"',
      {
        cwd: path.resolve('backend'),
        encoding: 'utf8',
        stdio: 'pipe'
      }
    );
    
    if (result.includes('SUCCESS')) {
      logSuccess('Backend main.py imports successfully');
      results.passed.push('Backend can import successfully');
      return true;
    } else {
      logError('Backend import did not return success');
      results.failed.push('Backend import failed');
      return false;
    }
  } catch (error) {
    logError('Backend failed to import');
    logError(`Error: ${error.message}`);
    if (error.stderr) {
      console.log('\nError output:');
      console.log(error.stderr);
    }
    results.failed.push('Backend import failed with error');
    return false;
  }
}

/**
 * Verify index.html references correct assets
 */
function verifyIndexHtml() {
  logSection('index.html Verification');
  
  const indexPath = path.resolve('dist/index.html');
  if (!fs.existsSync(indexPath)) {
    logError('index.html not found');
    return false;
  }
  
  const content = fs.readFileSync(indexPath, 'utf8');
  
  // Check for script tag
  if (content.includes('<script') && content.includes('type="module"')) {
    logSuccess('index.html contains module script tag');
    results.passed.push('Module script tag present');
  } else {
    logError('index.html missing module script tag');
    results.failed.push('Module script tag missing');
    return false;
  }
  
  // Check for CSS link
  if (content.includes('<link') && content.includes('stylesheet')) {
    logSuccess('index.html contains stylesheet link');
    results.passed.push('Stylesheet link present');
  } else {
    logWarning('index.html missing stylesheet link');
    results.warnings.push('Stylesheet link missing');
  }
  
  // Check for root div
  if (content.includes('id="root"')) {
    logSuccess('index.html contains root div');
    results.passed.push('Root div present');
  } else {
    logError('index.html missing root div');
    results.failed.push('Root div missing');
    return false;
  }
  
  // Check that referenced assets exist
  const scriptMatch = content.match(/src="([^"]+)"/);
  if (scriptMatch) {
    const scriptPath = scriptMatch[1].replace(/^\//, '');
    const fullScriptPath = path.resolve('dist', scriptPath);
    if (fs.existsSync(fullScriptPath)) {
      logSuccess(`Referenced script exists: ${scriptPath}`);
      results.passed.push('Referenced script exists');
    } else {
      logError(`Referenced script missing: ${scriptPath}`);
      results.failed.push('Referenced script missing');
      return false;
    }
  }
  
  return true;
}

/**
 * Generate summary report
 */
function generateSummary() {
  logSection('Verification Summary');
  
  console.log(`\n${colors.green}Passed: ${results.passed.length}${colors.reset}`);
  console.log(`${colors.yellow}Warnings: ${results.warnings.length}${colors.reset}`);
  console.log(`${colors.red}Failed: ${results.failed.length}${colors.reset}`);
  
  if (results.warnings.length > 0) {
    console.log('\nWarnings:');
    results.warnings.forEach(w => logWarning(w));
  }
  
  if (results.failed.length > 0) {
    console.log('\nFailures:');
    results.failed.forEach(f => logError(f));
  }
  
  console.log('\n' + '='.repeat(60));
  
  if (results.failed.length === 0) {
    logSuccess('✓ All build output verifications passed!');
    return true;
  } else {
    logError('✗ Some build output verifications failed');
    return false;
  }
}

/**
 * Main verification function
 */
function main() {
  console.log('\n');
  log('Build Output Verification', 'cyan');
  log('Validates: Requirements 2.4, 2.5', 'blue');
  
  let allPassed = true;
  
  // Run all verifications
  allPassed = verifyFrontendBuild() && allPassed;
  allPassed = verifyBundleSizes() && allPassed;
  allPassed = verifyIndexHtml() && allPassed;
  allPassed = verifyBackendStart() && allPassed;
  
  // Generate summary
  const success = generateSummary();
  
  // Exit with appropriate code
  process.exit(success ? 0 : 1);
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = {
  verifyFrontendBuild,
  verifyBundleSizes,
  verifyBackendStart,
  verifyIndexHtml
};
