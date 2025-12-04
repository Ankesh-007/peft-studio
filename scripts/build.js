#!/usr/bin/env node

/**
 * Enhanced Build Script for PEFT Studio
 * Handles building installers for Windows, macOS, and Linux with comprehensive
 * artifact collection, cataloging, verification, and progress reporting.
 * 
 * Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

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

// Build configuration
const BUILD_CONFIG = {
  platforms: {
    windows: {
      name: 'Windows',
      target: 'win',
      enabled: true,
      expectedArtifacts: [
        { pattern: /PEFT.*-Setup-.*\.exe$/, type: 'installer', format: 'NSIS' },
        { pattern: /PEFT.*-Portable-.*\.exe$/, type: 'portable', format: 'Portable' },
      ],
    },
    mac: {
      name: 'macOS',
      target: 'mac',
      enabled: true,
      expectedArtifacts: [
        { pattern: /PEFT.*-.*-x64\.dmg$/, type: 'installer', format: 'DMG', arch: 'x64' },
        { pattern: /PEFT.*-.*-arm64\.dmg$/, type: 'installer', format: 'DMG', arch: 'arm64' },
        { pattern: /PEFT.*-.*-x64\.zip$/, type: 'archive', format: 'ZIP', arch: 'x64' },
        { pattern: /PEFT.*-.*-arm64\.zip$/, type: 'archive', format: 'ZIP', arch: 'arm64' },
      ],
    },
    linux: {
      name: 'Linux',
      target: 'linux',
      enabled: true,
      expectedArtifacts: [
        { pattern: /PEFT.*-.*-x64\.AppImage$/, type: 'installer', format: 'AppImage' },
        { pattern: /PEFT.*-.*-amd64\.deb$/, type: 'installer', format: 'DEB' },
      ],
    },
  },
  releaseDir: 'release',
};

/**
 * Logging utilities
 */
function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function logProgress(current, total, message) {
  const percentage = Math.round((current / total) * 100);
  log(`[${current}/${total}] ${percentage}% - ${message}`, colors.blue);
}

function logError(message, error) {
  log(`ERROR: ${message}`, colors.red);
  if (error) {
    log(`  ${error.message || error}`, colors.red);
  }
}

function logSuccess(message) {
  log(`✓ ${message}`, colors.green);
}

function logWarning(message) {
  log(`⚠ ${message}`, colors.yellow);
}

/**
 * Execute command with error handling
 */
function exec(command, options = {}) {
  log(`\n> ${command}`, colors.cyan);
  try {
    execSync(command, { stdio: 'inherit', ...options });
    return { success: true };
  } catch (error) {
    return { success: false, error };
  }
}

/**
 * Check prerequisites before building
 */
function checkPrerequisites() {
  log('\n=== Checking Prerequisites ===', colors.bright);
  
  const checks = [];
  
  // Check if node_modules exists
  if (!fs.existsSync('node_modules')) {
    logWarning('node_modules not found. Running npm install...');
    const result = exec('npm install');
    if (!result.success) {
      logError('Failed to install dependencies', result.error);
      process.exit(1);
    }
  }
  checks.push({ name: 'Dependencies', status: 'ok' });
  
  // Check if build assets exist
  const buildDir = path.join(__dirname, '..', 'build');
  if (!fs.existsSync(buildDir)) {
    fs.mkdirSync(buildDir, { recursive: true });
  }
  checks.push({ name: 'Build directory', status: 'ok' });
  
  // Check for icon files
  const requiredIcons = ['icon.png'];
  const missingIcons = requiredIcons.filter(icon => 
    !fs.existsSync(path.join(buildDir, icon))
  );
  
  if (missingIcons.length > 0) {
    logWarning('Missing icon files:');
    missingIcons.forEach(icon => log(`  - ${icon}`, colors.yellow));
    logWarning('Using placeholder icons. Add proper icons to build/ directory.');
    checks.push({ name: 'Icons', status: 'warning' });
  } else {
    checks.push({ name: 'Icons', status: 'ok' });
  }
  
  // Display check results
  log('\nPrerequisite checks:', colors.bright);
  checks.forEach(check => {
    const symbol = check.status === 'ok' ? '✓' : '⚠';
    const color = check.status === 'ok' ? colors.green : colors.yellow;
    log(`  ${symbol} ${check.name}`, color);
  });
  
  logSuccess('Prerequisites check complete');
  return { success: true, checks };
}

/**
 * Build frontend
 */
function buildFrontend() {
  log('\n=== Building Frontend ===', colors.bright);
  
  const startTime = Date.now();
  const result = exec('npm run build');
  const duration = ((Date.now() - startTime) / 1000).toFixed(2);
  
  if (!result.success) {
    logError('Frontend build failed', result.error);
    return { success: false, error: result.error, duration };
  }
  
  logSuccess(`Frontend build complete (${duration}s)`);
  return { success: true, duration };
}

/**
 * Build installer for a specific platform
 */
function buildPlatform(platformKey) {
  const platform = BUILD_CONFIG.platforms[platformKey];
  
  if (!platform.enabled) {
    logWarning(`${platform.name} build is disabled`);
    return { success: true, skipped: true, platform: platformKey };
  }
  
  log(`\n=== Building ${platform.name} Installer ===`, colors.bright);
  
  const startTime = Date.now();
  const command = `electron-builder --${platform.target}`;
  const result = exec(command);
  const duration = ((Date.now() - startTime) / 1000).toFixed(2);
  
  if (!result.success) {
    logError(`${platform.name} installer build failed`, result.error);
    return { 
      success: false, 
      platform: platformKey, 
      error: result.error,
      duration 
    };
  }
  
  logSuccess(`${platform.name} installer build complete (${duration}s)`);
  return { success: true, platform: platformKey, duration };
}

/**
 * Build all platforms simultaneously
 */
function buildAllPlatforms(platforms) {
  log('\n=== Building All Platforms ===', colors.bright);
  
  const results = [];
  const enabledPlatforms = platforms.filter(p => BUILD_CONFIG.platforms[p].enabled);
  
  log(`Building for ${enabledPlatforms.length} platform(s): ${enabledPlatforms.join(', ')}\n`);
  
  let current = 0;
  for (const platformKey of enabledPlatforms) {
    current++;
    logProgress(current, enabledPlatforms.length, `Building ${BUILD_CONFIG.platforms[platformKey].name}`);
    
    const result = buildPlatform(platformKey);
    results.push(result);
    
    // Continue with other platforms even if one fails
    if (!result.success && !result.skipped) {
      logWarning(`${BUILD_CONFIG.platforms[platformKey].name} build failed, continuing with other platforms...`);
    }
  }
  
  return results;
}

/**
 * Collect and catalog artifacts
 * @param {string} baseDir - Optional base directory (for testing)
 */
function collectArtifacts(baseDir = null) {
  log('\n=== Collecting Artifacts ===', colors.bright);
  
  const releaseDir = baseDir 
    ? path.join(baseDir, BUILD_CONFIG.releaseDir)
    : path.join(__dirname, '..', BUILD_CONFIG.releaseDir);
  
  if (!fs.existsSync(releaseDir)) {
    logWarning('Release directory not found');
    return { artifacts: [], totalSize: 0 };
  }
  
  const artifacts = [];
  const files = fs.readdirSync(releaseDir);
  
  for (const file of files) {
    const filePath = path.join(releaseDir, file);
    const stats = fs.statSync(filePath);
    
    // Only process files, not directories
    if (!stats.isFile()) {
      continue;
    }
    
    // Determine artifact type and platform
    let artifactInfo = {
      filename: file,
      path: filePath,
      size: stats.size,
      type: 'unknown',
      platform: 'unknown',
      format: 'unknown',
      architecture: 'unknown',
    };
    
    // Match against expected artifacts
    for (const [platformKey, platform] of Object.entries(BUILD_CONFIG.platforms)) {
      for (const expected of platform.expectedArtifacts) {
        if (expected.pattern.test(file)) {
          artifactInfo.platform = platformKey;
          artifactInfo.type = expected.type;
          artifactInfo.format = expected.format;
          artifactInfo.architecture = expected.arch || 'x64';
          break;
        }
      }
      if (artifactInfo.platform !== 'unknown') break;
    }
    
    artifacts.push(artifactInfo);
  }
  
  const totalSize = artifacts.reduce((sum, a) => sum + a.size, 0);
  
  logSuccess(`Collected ${artifacts.length} artifact(s)`);
  return { artifacts, totalSize };
}

/**
 * Verify build outputs
 * @param {string[]} platforms - Platforms to verify
 * @param {string} baseDir - Optional base directory (for testing)
 */
function verifyBuildOutputs(platforms, baseDir = null) {
  log('\n=== Verifying Build Outputs ===', colors.bright);
  
  const { artifacts } = collectArtifacts(baseDir);
  const verification = {
    valid: true,
    verified: [],
    missing: [],
    unexpected: [],
  };
  
  // Check each enabled platform
  for (const platformKey of platforms) {
    const platform = BUILD_CONFIG.platforms[platformKey];
    
    if (!platform.enabled) {
      continue;
    }
    
    log(`\nVerifying ${platform.name} artifacts:`, colors.bright);
    
    for (const expected of platform.expectedArtifacts) {
      const found = artifacts.find(a => expected.pattern.test(a.filename));
      
      if (found) {
        logSuccess(`  Found: ${found.filename} (${formatSize(found.size)})`);
        verification.verified.push({
          platform: platformKey,
          artifact: found.filename,
          expected: expected.format,
        });
      } else {
        logWarning(`  Missing: ${expected.format} ${expected.arch || ''}`);
        verification.missing.push({
          platform: platformKey,
          expected: expected.format,
          arch: expected.arch,
        });
        verification.valid = false;
      }
    }
  }
  
  // Check for unexpected artifacts
  for (const artifact of artifacts) {
    if (artifact.platform === 'unknown') {
      logWarning(`Unexpected artifact: ${artifact.filename}`);
      verification.unexpected.push(artifact.filename);
    }
  }
  
  if (verification.valid) {
    logSuccess('\nAll expected artifacts verified');
  } else {
    logWarning('\nSome expected artifacts are missing');
  }
  
  return verification;
}

/**
 * Format file size
 */
function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

/**
 * Verify compression configuration in package.json
 * Requirements: 7.1
 */
function verifyCompressionConfig() {
  log('\n=== Verifying Compression Configuration ===', colors.bright);
  
  const packageJsonPath = path.join(__dirname, '..', 'package.json');
  
  if (!fs.existsSync(packageJsonPath)) {
    logError('package.json not found');
    return { valid: false, errors: ['package.json not found'] };
  }
  
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  const buildConfig = packageJson.build || {};
  
  const results = {
    valid: true,
    compressionEnabled: {},
    errors: [],
    warnings: [],
  };
  
  // Check compression for each platform
  const platforms = ['win', 'mac', 'linux', 'nsis', 'dmg', 'appImage', 'deb'];
  
  for (const platform of platforms) {
    const platformConfig = buildConfig[platform];
    
    if (platformConfig) {
      // Check if compression is explicitly set
      if (platformConfig.compression !== undefined) {
        results.compressionEnabled[platform] = platformConfig.compression;
        
        if (platformConfig.compression === 'store' || platformConfig.compression === null) {
          results.warnings.push(`${platform}: compression is disabled or set to 'store'`);
        } else {
          logSuccess(`  ${platform}: compression enabled (${platformConfig.compression})`);
        }
      } else {
        // Default compression is enabled for most formats
        results.compressionEnabled[platform] = 'default';
        log(`  ${platform}: using default compression`, colors.cyan);
      }
    }
  }
  
  if (results.warnings.length > 0) {
    results.warnings.forEach(w => logWarning(`  ${w}`));
  }
  
  logSuccess('Compression configuration verified');
  return results;
}

/**
 * Verify development dependencies are excluded from build
 * Requirements: 7.2
 */
function verifyDependencyExclusion() {
  log('\n=== Verifying Dependency Exclusion ===', colors.bright);
  
  const packageJsonPath = path.join(__dirname, '..', 'package.json');
  
  if (!fs.existsSync(packageJsonPath)) {
    logError('package.json not found');
    return { valid: false, errors: ['package.json not found'] };
  }
  
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  const buildConfig = packageJson.build || {};
  
  const results = {
    valid: true,
    filesConfig: buildConfig.files || [],
    excludedPatterns: [],
    warnings: [],
  };
  
  // Check if files configuration exists
  if (!buildConfig.files || buildConfig.files.length === 0) {
    results.warnings.push('No files configuration found - all files may be included');
    results.valid = false;
  } else {
    logSuccess('  Files configuration found');
    
    // Check for common patterns that should be included
    const requiredPatterns = ['dist/**/*', 'electron/**/*', 'backend/**/*', 'package.json'];
    const missingPatterns = requiredPatterns.filter(pattern => 
      !buildConfig.files.some(f => f === pattern || f.includes(pattern.split('/')[0]))
    );
    
    if (missingPatterns.length > 0) {
      results.warnings.push(`Missing recommended patterns: ${missingPatterns.join(', ')}`);
    }
    
    // Check for patterns that should NOT be included
    const devPatterns = ['node_modules', 'src', '.git', 'test', 'tests', '__tests__'];
    const includedDevPatterns = buildConfig.files.filter(f => 
      devPatterns.some(dev => f.includes(dev))
    );
    
    if (includedDevPatterns.length > 0) {
      results.warnings.push(`Development patterns included: ${includedDevPatterns.join(', ')}`);
    }
    
    logSuccess(`  ${buildConfig.files.length} file pattern(s) configured`);
  }
  
  // Check for asarUnpack configuration (files that should not be packed)
  if (buildConfig.asarUnpack) {
    results.excludedPatterns.push(...(Array.isArray(buildConfig.asarUnpack) ? buildConfig.asarUnpack : [buildConfig.asarUnpack]));
    log(`  ${results.excludedPatterns.length} pattern(s) excluded from asar`, colors.cyan);
  }
  
  if (results.warnings.length > 0) {
    results.warnings.forEach(w => logWarning(`  ${w}`));
  }
  
  logSuccess('Dependency exclusion verified');
  return results;
}

/**
 * Validate installer sizes are within reasonable limits
 * Requirements: 7.3
 * @param {string} baseDir - Optional base directory (for testing)
 */
function validateInstallerSizes(baseDir = null) {
  log('\n=== Validating Installer Sizes ===', colors.bright);
  
  const { artifacts } = collectArtifacts(baseDir);
  
  // Define reasonable size limits (in bytes)
  const SIZE_LIMITS = {
    windows: {
      installer: 500 * 1024 * 1024, // 500 MB
      portable: 500 * 1024 * 1024,  // 500 MB
    },
    mac: {
      dmg: 500 * 1024 * 1024,       // 500 MB
      zip: 500 * 1024 * 1024,       // 500 MB
    },
    linux: {
      AppImage: 500 * 1024 * 1024,  // 500 MB
      deb: 500 * 1024 * 1024,       // 500 MB
    },
  };
  
  const results = {
    valid: true,
    validated: [],
    oversized: [],
    warnings: [],
  };
  
  if (artifacts.length === 0) {
    logWarning('No artifacts found to validate');
    return results;
  }
  
  for (const artifact of artifacts) {
    const platformLimits = SIZE_LIMITS[artifact.platform];
    
    if (!platformLimits) {
      results.warnings.push(`No size limits defined for platform: ${artifact.platform}`);
      continue;
    }
    
    const limit = platformLimits[artifact.format] || platformLimits.installer;
    
    if (artifact.size > limit) {
      logWarning(`  ${artifact.filename}: ${formatSize(artifact.size)} exceeds limit of ${formatSize(limit)}`);
      results.oversized.push({
        filename: artifact.filename,
        size: artifact.size,
        limit: limit,
        platform: artifact.platform,
        format: artifact.format,
      });
      results.valid = false;
    } else {
      logSuccess(`  ${artifact.filename}: ${formatSize(artifact.size)} (within limit)`);
      results.validated.push({
        filename: artifact.filename,
        size: artifact.size,
        limit: limit,
      });
    }
  }
  
  if (results.valid) {
    logSuccess('All installer sizes are within limits');
  } else {
    logWarning(`${results.oversized.length} installer(s) exceed size limits`);
  }
  
  return results;
}

/**
 * Generate size report for release summary
 * Requirements: 7.5
 * @param {string} baseDir - Optional base directory (for testing)
 */
function generateSizeReport(baseDir = null) {
  log('\n=== Generating Size Report ===', colors.bright);
  
  const { artifacts, totalSize } = collectArtifacts(baseDir);
  
  const report = {
    totalSize,
    totalSizeFormatted: formatSize(totalSize),
    artifactCount: artifacts.length,
    byPlatform: {},
    byFormat: {},
    artifacts: [],
  };
  
  // Group by platform
  for (const artifact of artifacts) {
    if (!report.byPlatform[artifact.platform]) {
      report.byPlatform[artifact.platform] = {
        count: 0,
        totalSize: 0,
        artifacts: [],
      };
    }
    
    report.byPlatform[artifact.platform].count++;
    report.byPlatform[artifact.platform].totalSize += artifact.size;
    report.byPlatform[artifact.platform].artifacts.push(artifact.filename);
    
    // Group by format
    if (!report.byFormat[artifact.format]) {
      report.byFormat[artifact.format] = {
        count: 0,
        totalSize: 0,
      };
    }
    
    report.byFormat[artifact.format].count++;
    report.byFormat[artifact.format].totalSize += artifact.size;
    
    // Add to artifacts list
    report.artifacts.push({
      filename: artifact.filename,
      size: artifact.size,
      sizeFormatted: formatSize(artifact.size),
      platform: artifact.platform,
      format: artifact.format,
      type: artifact.type,
    });
  }
  
  // Display report
  log('\nSize Report:', colors.bright);
  log(`  Total artifacts: ${report.artifactCount}`);
  log(`  Total size: ${report.totalSizeFormatted}`, colors.cyan);
  
  log('\nBy Platform:', colors.bright);
  for (const [platform, data] of Object.entries(report.byPlatform)) {
    log(`  ${platform}: ${data.count} artifact(s), ${formatSize(data.totalSize)}`, colors.cyan);
  }
  
  log('\nBy Format:', colors.bright);
  for (const [format, data] of Object.entries(report.byFormat)) {
    log(`  ${format}: ${data.count} artifact(s), ${formatSize(data.totalSize)}`, colors.cyan);
  }
  
  logSuccess('Size report generated');
  return report;
}

/**
 * Generate build report
 * @param {Array} buildResults - Build results for each platform
 * @param {Object} verification - Verification results
 * @param {number} startTime - Build start timestamp
 * @param {string} baseDir - Optional base directory (for testing)
 */
function generateBuildReport(buildResults, verification, startTime, baseDir = null) {
  log('\n=== Build Report ===', colors.bright);
  
  const duration = ((Date.now() - startTime) / 1000).toFixed(2);
  const { artifacts, totalSize } = collectArtifacts(baseDir);
  
  // Platform results
  log('\nPlatform Build Results:', colors.bright);
  for (const result of buildResults) {
    const platform = BUILD_CONFIG.platforms[result.platform];
    const symbol = result.success ? '✓' : '✗';
    const color = result.success ? colors.green : colors.red;
    const status = result.skipped ? 'skipped' : (result.success ? 'success' : 'failed');
    log(`  ${symbol} ${platform.name}: ${status} (${result.duration || 0}s)`, color);
  }
  
  // Artifacts
  log('\nGenerated Artifacts:', colors.bright);
  if (artifacts.length === 0) {
    logWarning('  No artifacts found');
  } else {
    for (const artifact of artifacts) {
      log(`  - ${artifact.filename}`, colors.cyan);
      log(`    Platform: ${artifact.platform}, Type: ${artifact.type}, Format: ${artifact.format}`, colors.cyan);
      log(`    Size: ${formatSize(artifact.size)}`, colors.cyan);
    }
  }
  
  // Summary
  log('\nSummary:', colors.bright);
  log(`  Total artifacts: ${artifacts.length}`);
  log(`  Total size: ${formatSize(totalSize)}`);
  log(`  Build duration: ${duration}s`);
  log(`  Verification: ${verification.valid ? 'PASSED' : 'FAILED'}`, 
      verification.valid ? colors.green : colors.yellow);
  
  if (verification.missing.length > 0) {
    log(`  Missing artifacts: ${verification.missing.length}`, colors.yellow);
  }
  
  return {
    duration,
    artifactCount: artifacts.length,
    totalSize,
    verification,
    buildResults,
  };
}

/**
 * Main build function
 */
function main() {
  const args = process.argv.slice(2);
  const requestedPlatform = args[0] || 'all';
  
  log('='.repeat(60), colors.bright);
  log('PEFT Studio Enhanced Build Script', colors.bright);
  log('='.repeat(60), colors.bright);
  
  const startTime = Date.now();
  
  // Determine platforms to build
  let platforms;
  if (requestedPlatform === 'all') {
    platforms = Object.keys(BUILD_CONFIG.platforms);
  } else if (BUILD_CONFIG.platforms[requestedPlatform]) {
    platforms = [requestedPlatform];
  } else {
    logError(`Unknown platform: ${requestedPlatform}`);
    log('Valid platforms: windows, mac, linux, all', colors.yellow);
    process.exit(1);
  }
  
  // Execute build steps
  const prereqResult = checkPrerequisites();
  if (!prereqResult.success) {
    process.exit(1);
  }
  
  const frontendResult = buildFrontend();
  if (!frontendResult.success) {
    process.exit(1);
  }
  
  const buildResults = buildAllPlatforms(platforms);
  
  // Check if any builds succeeded
  const anySuccess = buildResults.some(r => r.success);
  if (!anySuccess) {
    logError('All platform builds failed');
    process.exit(1);
  }
  
  // Verify installer optimization
  const compressionCheck = verifyCompressionConfig();
  const dependencyCheck = verifyDependencyExclusion();
  
  // Collect and verify artifacts
  const verification = verifyBuildOutputs(platforms);
  
  // Validate installer sizes
  const sizeValidation = validateInstallerSizes();
  
  // Generate size report
  const sizeReport = generateSizeReport();
  
  // Generate report
  const report = generateBuildReport(buildResults, verification, startTime);
  
  // Determine exit status
  const allSuccess = buildResults.every(r => r.success || r.skipped);
  
  if (allSuccess && verification.valid) {
    log('\n=== Build Complete: SUCCESS ===', colors.green);
    log('All installers are in the release/ directory', colors.green);
    process.exit(0);
  } else if (anySuccess) {
    log('\n=== Build Complete: PARTIAL SUCCESS ===', colors.yellow);
    log('Some builds failed or artifacts are missing', colors.yellow);
    log('Check the report above for details', colors.yellow);
    process.exit(1);
  } else {
    log('\n=== Build Complete: FAILED ===', colors.red);
    process.exit(1);
  }
}

// Export functions for testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    BUILD_CONFIG,
    checkPrerequisites,
    buildFrontend,
    buildPlatform,
    buildAllPlatforms,
    collectArtifacts,
    verifyBuildOutputs,
    generateBuildReport,
    formatSize,
    verifyCompressionConfig,
    verifyDependencyExclusion,
    validateInstallerSizes,
    generateSizeReport,
  };
}

// Run main if executed directly
if (require.main === module) {
  main();
}
