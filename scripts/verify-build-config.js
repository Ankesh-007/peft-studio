#!/usr/bin/env node

/**
 * Verification script for build configuration
 * Checks that all required files and settings are in place
 */

const fs = require('fs');
const path = require('path');

const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
};

function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function checkFile(filePath, required = true) {
  const exists = fs.existsSync(filePath);
  const status = exists ? '✓' : (required ? '✗' : '○');
  const color = exists ? colors.green : (required ? colors.red : colors.yellow);
  log(`  ${status} ${filePath}`, color);
  return exists;
}

function checkPackageJson() {
  log('\n=== Checking package.json ===', colors.cyan);
  
  const packagePath = path.join(__dirname, '..', 'package.json');
  if (!fs.existsSync(packagePath)) {
    log('✗ package.json not found', colors.red);
    return false;
  }
  
  const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
  
  // Check build configuration
  if (!pkg.build) {
    log('✗ Missing build configuration', colors.red);
    return false;
  }
  
  log('✓ Build configuration found', colors.green);
  
  // Check targets
  const targets = {
    windows: pkg.build.win?.target || [],
    mac: pkg.build.mac?.target || [],
    linux: pkg.build.linux?.target || []
  };
  
  log('\nConfigured targets:', colors.cyan);
  log(`  Windows: ${targets.windows.join(', ')}`, colors.green);
  log(`  macOS: ${targets.mac.join(', ')}`, colors.green);
  log(`  Linux: ${targets.linux.join(', ')}`, colors.green);
  
  // Check scripts
  const requiredScripts = [
    'package',
    'package:win',
    'package:mac',
    'package:linux',
    'package:all'
  ];
  
  log('\nBuild scripts:', colors.cyan);
  let allScriptsPresent = true;
  requiredScripts.forEach(script => {
    if (pkg.scripts[script]) {
      log(`  ✓ ${script}`, colors.green);
    } else {
      log(`  ✗ ${script} missing`, colors.red);
      allScriptsPresent = false;
    }
  });
  
  return allScriptsPresent;
}

function checkBuildAssets() {
  log('\n=== Checking Build Assets ===', colors.cyan);
  
  const buildDir = path.join(__dirname, '..', 'build');
  if (!fs.existsSync(buildDir)) {
    log('✗ build/ directory not found', colors.red);
    return false;
  }
  
  log('✓ build/ directory exists', colors.green);
  
  // Check for icons (optional but recommended)
  log('\nIcon files (optional):', colors.cyan);
  checkFile('build/icon.ico', false);
  checkFile('build/icon.icns', false);
  checkFile('build/icon.png', false);
  
  // Check for entitlements (required for macOS)
  log('\nmacOS entitlements:', colors.cyan);
  const hasEntitlements = checkFile('build/entitlements.mac.plist', true);
  
  return hasEntitlements;
}

function checkBuildScripts() {
  log('\n=== Checking Build Scripts ===', colors.cyan);
  
  const scripts = [
    'scripts/build.js',
    'scripts/build.sh',
    'scripts/build.ps1'
  ];
  
  let allPresent = true;
  scripts.forEach(script => {
    if (!checkFile(script, true)) {
      allPresent = false;
    }
  });
  
  return allPresent;
}

function checkCIConfig() {
  log('\n=== Checking CI/CD Configuration ===', colors.cyan);
  
  const workflows = [
    '.github/workflows/build-installers.yml',
    '.github/workflows/release.yml'
  ];
  
  let allPresent = true;
  workflows.forEach(workflow => {
    if (!checkFile(workflow, true)) {
      allPresent = false;
    }
  });
  
  return allPresent;
}

function checkDependencies() {
  log('\n=== Checking Dependencies ===', colors.cyan);
  
  const packagePath = path.join(__dirname, '..', 'package.json');
  const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
  
  const requiredDeps = [
    'electron',
    'electron-builder',
    'electron-updater'
  ];
  
  let allPresent = true;
  requiredDeps.forEach(dep => {
    if (pkg.dependencies[dep] || pkg.devDependencies[dep]) {
      log(`  ✓ ${dep}`, colors.green);
    } else {
      log(`  ✗ ${dep} missing`, colors.red);
      allPresent = false;
    }
  });
  
  return allPresent;
}

function main() {
  log('='.repeat(60), colors.cyan);
  log('PEFT Studio Build Configuration Verification', colors.cyan);
  log('='.repeat(60), colors.cyan);
  
  const checks = [
    checkPackageJson(),
    checkBuildAssets(),
    checkBuildScripts(),
    checkCIConfig(),
    checkDependencies()
  ];
  
  const allPassed = checks.every(check => check);
  
  log('\n' + '='.repeat(60), colors.cyan);
  if (allPassed) {
    log('✓ All checks passed!', colors.green);
    log('Build configuration is ready.', colors.green);
    log('\nNext steps:', colors.cyan);
    log('  1. Add icon files to build/ directory (optional)', colors.yellow);
    log('  2. Configure code signing (optional)', colors.yellow);
    log('  3. Run: npm run package', colors.green);
  } else {
    log('✗ Some checks failed', colors.red);
    log('Please fix the issues above before building.', colors.yellow);
    process.exit(1);
  }
  log('='.repeat(60), colors.cyan);
}

main();
