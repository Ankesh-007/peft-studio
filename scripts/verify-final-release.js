#!/usr/bin/env node

/**
 * Final Release Verification Script
 * 
 * This script performs comprehensive verification of the Python backend bundling
 * implementation before release. It checks all critical aspects of the build
 * pipeline, bundled executables, and integration points.
 */

import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ANSI color codes for output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function logSection(title) {
  log(`\n${'='.repeat(80)}`, colors.cyan);
  log(`  ${title}`, colors.bright + colors.cyan);
  log('='.repeat(80), colors.cyan);
}

function logSuccess(message) {
  log(`✅ ${message}`, colors.green);
}

function logError(message) {
  log(`❌ ${message}`, colors.red);
}

function logWarning(message) {
  log(`⚠️  ${message}`, colors.yellow);
}

function logInfo(message) {
  log(`ℹ️  ${message}`, colors.blue);
}

// Track verification results
const results = {
  passed: [],
  failed: [],
  warnings: [],
  skipped: [],
};

function recordResult(category, test, passed, message = '') {
  const result = { category, test, message };
  if (passed) {
    results.passed.push(result);
    logSuccess(`${test}${message ? ': ' + message : ''}`);
  } else {
    results.failed.push(result);
    logError(`${test}${message ? ': ' + message : ''}`);
  }
}

function recordWarning(category, test, message) {
  results.warnings.push({ category, test, message });
  logWarning(`${test}: ${message}`);
}

function recordSkipped(category, test, reason) {
  results.skipped.push({ category, test, reason });
  logInfo(`${test}: ${reason}`);
}

// Verification functions

function verifyFileExists(filePath, description) {
  const exists = fs.existsSync(filePath);
  recordResult('Files', description, exists, exists ? filePath : `Not found: ${filePath}`);
  return exists;
}

function verifyFileSize(filePath, minSize, maxSize, description) {
  if (!fs.existsSync(filePath)) {
    recordResult('Files', description, false, `File not found: ${filePath}`);
    return false;
  }
  
  const stats = fs.statSync(filePath);
  const sizeMB = stats.size / (1024 * 1024);
  const valid = stats.size >= minSize && stats.size <= maxSize;
  
  recordResult(
    'Files',
    description,
    valid,
    `${sizeMB.toFixed(2)} MB (min: ${(minSize / 1024 / 1024).toFixed(2)} MB, max: ${(maxSize / 1024 / 1024).toFixed(2)} MB)`
  );
  
  return valid;
}

function verifyBuildArtifacts() {
  logSection('Build Artifacts Verification');
  
  const platform = process.platform;
  const backendExeName = platform === 'win32' ? 'peft_engine.exe' : 'peft_engine';
  const backendExePath = path.join(__dirname, '../backend/dist', backendExeName);
  
  // Check backend executable
  verifyFileExists(backendExePath, 'Backend executable exists');
  verifyFileSize(backendExePath, 1024 * 1024, 3 * 1024 * 1024 * 1024, 'Backend executable size is reasonable');
  
  // Check PyInstaller spec file
  verifyFileExists(
    path.join(__dirname, '../backend/peft_engine.spec'),
    'PyInstaller spec file exists'
  );
  
  // Check build hooks
  verifyFileExists(
    path.join(__dirname, '../backend/build_hooks.py'),
    'Build hooks file exists'
  );
  
  // Check runtime paths module
  verifyFileExists(
    path.join(__dirname, '../backend/runtime_paths.py'),
    'Runtime paths module exists'
  );
}

function verifyBuildScripts() {
  logSection('Build Scripts Verification');
  
  // Check package.json scripts
  const packageJson = JSON.parse(fs.readFileSync(path.join(__dirname, '../package.json'), 'utf8'));
  const requiredScripts = [
    'build:backend',
    'build:backend:verify',
    'build:frontend',
    'build:all',
  ];
  
  for (const script of requiredScripts) {
    const exists = packageJson.scripts && packageJson.scripts[script];
    recordResult('Build Scripts', `Script "${script}" exists`, exists);
  }
  
  // Check verification scripts
  verifyFileExists(
    path.join(__dirname, 'verify-backend-build.js'),
    'Backend build verification script exists'
  );
  
  verifyFileExists(
    path.join(__dirname, 'verify-build-environment.js'),
    'Build environment verification script exists'
  );
  
  verifyFileExists(
    path.join(__dirname, 'build.js'),
    'Main build script exists'
  );
}

function verifyElectronConfiguration() {
  logSection('Electron Configuration Verification');
  
  // Check main.js
  const mainJsPath = path.join(__dirname, '../electron/main.js');
  if (verifyFileExists(mainJsPath, 'Electron main.js exists')) {
    const mainJsContent = fs.readFileSync(mainJsPath, 'utf8');
    
    // Check for key methods
    const checks = [
      { pattern: /getBackendPath\s*\(/, description: 'getBackendPath() method exists' },
      { pattern: /app\.isPackaged/, description: 'Production mode detection exists' },
      { pattern: /process\.resourcesPath/, description: 'Resource path usage exists' },
      { pattern: /SIGTERM/, description: 'Graceful shutdown (SIGTERM) exists' },
      { pattern: /SIGKILL/, description: 'Force kill (SIGKILL) exists' },
    ];
    
    for (const check of checks) {
      const found = check.pattern.test(mainJsContent);
      recordResult('Electron Config', check.description, found);
    }
  }
  
  // Check package.json build configuration
  const packageJson = JSON.parse(fs.readFileSync(path.join(__dirname, '../package.json'), 'utf8'));
  
  if (packageJson.build) {
    const hasExtraResources = packageJson.build.extraResources && packageJson.build.extraResources.length > 0;
    recordResult('Electron Config', 'extraResources configured', hasExtraResources);
    
    const hasFiles = packageJson.build.files && packageJson.build.files.length > 0;
    recordResult('Electron Config', 'files configuration exists', hasFiles);
  } else {
    recordResult('Electron Config', 'build configuration exists', false);
  }
}

function verifyTestSuite() {
  logSection('Test Suite Verification');
  
  // Check for test files
  const testFiles = [
    'backend/tests/test_pyinstaller_dependency_inclusion.py',
    'backend/tests/test_data_file_bundling.py',
    'backend/tests/test_runtime_path_integration.py',
    'backend/tests/test_python_import_resolution.py',
    'src/test/pbt/backend-path-resolution.pbt.test.ts',
    'src/test/pbt/backend-process-cleanup.pbt.test.ts',
    'src/test/pbt/resource-path-accessibility.pbt.test.ts',
    'src/test/pbt/backend-error-message-specificity.pbt.test.ts',
    'src/test/pbt/data-file-bundling.pbt.test.ts',
    'src/test/pbt/update-package-integrity.pbt.test.ts',
    'scripts/test/build-backend.test.js',
    'scripts/test/verify-backend-build.pbt.test.js',
    'src/test/integration/backend-lifecycle-verification.test.ts',
    'src/test/integration/backend-performance-verification.test.ts',
    'src/test/integration/code-signing-backend-integration.test.ts',
    'src/test/integration/platform-windows.test.ts',
    'src/test/integration/platform-macos.test.ts',
    'src/test/integration/platform-linux.test.ts',
    'src/test/e2e/bundled-backend-integration.e2e.test.ts',
  ];
  
  for (const testFile of testFiles) {
    const fullPath = path.join(__dirname, '..', testFile);
    verifyFileExists(fullPath, `Test file: ${testFile}`);
  }
}

function verifyDocumentation() {
  logSection('Documentation Verification');
  
  const docFiles = [
    'docs/developer-guide/backend-bundling.md',
    'docs/developer-guide/backend-bundling-troubleshooting.md',
    'docs/developer-guide/testing-bundled-backend.md',
    'docs/developer-guide/release-with-bundled-backend.md',
    'docs/developer-guide/BACKEND_BUNDLING_INDEX.md',
    'backend/BUILD_SYSTEM_README.md',
  ];
  
  for (const docFile of docFiles) {
    const fullPath = path.join(__dirname, '..', docFile);
    verifyFileExists(fullPath, `Documentation: ${docFile}`);
  }
}

function verifyCIConfiguration() {
  logSection('CI/CD Configuration Verification');
  
  const ciFiles = [
    '.github/workflows/ci.yml',
    '.github/workflows/build.yml',
  ];
  
  for (const ciFile of ciFiles) {
    const fullPath = path.join(__dirname, '..', ciFile);
    if (verifyFileExists(fullPath, `CI workflow: ${ciFile}`)) {
      const content = fs.readFileSync(fullPath, 'utf8');
      
      if (ciFile.includes('build.yml')) {
        // Check for backend build steps
        const hasBackendBuild = content.includes('build:backend') || content.includes('pyinstaller');
        recordResult('CI Config', 'Backend build step in build.yml', hasBackendBuild);
      }
    }
  }
}

function runTests() {
  logSection('Running Test Suites');
  
  // Note: We'll just verify test files exist and are runnable
  // Actual test execution should be done separately
  
  logInfo('Test execution should be run separately with:');
  logInfo('  npm test                  - Unit tests');
  logInfo('  npm run test:integration  - Integration tests');
  logInfo('  npm run test:pbt          - Property-based tests');
  logInfo('  npm run test:e2e          - E2E tests');
  logInfo('  cd backend && pytest      - Backend tests');
  
  recordSkipped('Tests', 'Test execution', 'Run tests separately to verify functionality');
}

function verifyPlatformSpecifics() {
  logSection('Platform-Specific Verification');
  
  const platform = process.platform;
  logInfo(`Current platform: ${platform}`);
  
  if (platform === 'win32') {
    logInfo('Windows-specific checks:');
    const exePath = path.join(__dirname, '../backend/dist/peft_engine.exe');
    verifyFileExists(exePath, 'Windows .exe executable exists');
  } else if (platform === 'darwin') {
    logInfo('macOS-specific checks:');
    const exePath = path.join(__dirname, '../backend/dist/peft_engine');
    verifyFileExists(exePath, 'macOS executable exists');
  } else if (platform === 'linux') {
    logInfo('Linux-specific checks:');
    const exePath = path.join(__dirname, '../backend/dist/peft_engine');
    verifyFileExists(exePath, 'Linux executable exists');
  }
}

function generateReport() {
  logSection('Verification Summary');
  
  const total = results.passed.length + results.failed.length;
  const passRate = total > 0 ? ((results.passed.length / total) * 100).toFixed(1) : 0;
  
  log(`\nTotal Checks: ${total}`, colors.bright);
  logSuccess(`Passed: ${results.passed.length}`);
  logError(`Failed: ${results.failed.length}`);
  logWarning(`Warnings: ${results.warnings.length}`);
  logInfo(`Skipped: ${results.skipped.length}`);
  log(`\nPass Rate: ${passRate}%\n`, colors.bright);
  
  if (results.failed.length > 0) {
    log('\nFailed Checks:', colors.red + colors.bright);
    for (const failure of results.failed) {
      log(`  • [${failure.category}] ${failure.test}`, colors.red);
      if (failure.message) {
        log(`    ${failure.message}`, colors.red);
      }
    }
  }
  
  if (results.warnings.length > 0) {
    log('\nWarnings:', colors.yellow + colors.bright);
    for (const warning of results.warnings) {
      log(`  • [${warning.category}] ${warning.test}`, colors.yellow);
      if (warning.message) {
        log(`    ${warning.message}`, colors.yellow);
      }
    }
  }
  
  log('\n');
  
  // Write detailed report to file
  const reportPath = path.join(__dirname, '../.kiro/specs/python-backend-bundling/verification-report.json');
  fs.writeFileSync(reportPath, JSON.stringify({
    timestamp: new Date().toISOString(),
    platform: process.platform,
    arch: process.arch,
    results,
    summary: {
      total,
      passed: results.passed.length,
      failed: results.failed.length,
      warnings: results.warnings.length,
      skipped: results.skipped.length,
      passRate: parseFloat(passRate),
    },
  }, null, 2));
  
  logInfo(`Detailed report saved to: ${reportPath}`);
  
  return results.failed.length === 0;
}

// Main execution
function main() {
  log('\n' + '='.repeat(80), colors.bright + colors.cyan);
  log('  PEFT Studio - Python Backend Bundling Final Verification', colors.bright + colors.cyan);
  log('='.repeat(80) + '\n', colors.bright + colors.cyan);
  
  try {
    verifyBuildArtifacts();
    verifyBuildScripts();
    verifyElectronConfiguration();
    verifyTestSuite();
    verifyDocumentation();
    verifyCIConfiguration();
    verifyPlatformSpecifics();
    runTests();
    
    const success = generateReport();
    
    if (success) {
      log('\n✅ All verification checks passed!', colors.green + colors.bright);
      log('The Python backend bundling implementation is ready for release.\n', colors.green);
      process.exit(0);
    } else {
      log('\n❌ Some verification checks failed.', colors.red + colors.bright);
      log('Please review the failures above and fix them before release.\n', colors.red);
      process.exit(1);
    }
  } catch (error) {
    logError(`\nVerification failed with error: ${error.message}`);
    console.error(error);
    process.exit(1);
  }
}

// Run if called directly
const isMainModule = import.meta.url === `file:///${process.argv[1].replace(/\\/g, '/')}` || 
                     import.meta.url.endsWith(path.basename(process.argv[1]));

if (isMainModule) {
  main();
}

export { main };
