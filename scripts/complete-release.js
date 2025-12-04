#!/usr/bin/env node

/**
 * Complete Release Orchestration Script
 * 
 * Master script that orchestrates the complete release process by executing
 * all steps in sequence: cleanup, validate, build, checksum, and release.
 * 
 * Features:
 * - Sequential step execution with halt on failure
 * - Comprehensive error handling
 * - Dry-run mode for testing
 * - Working directory verification
 * - Final release summary with URLs and asset list
 * 
 * Requirements: 8.1, 8.2, 8.3, 8.4
 * 
 * Usage:
 *   node scripts/complete-release.js [options]
 * 
 * Options:
 *   --dry-run          Simulate the release without making changes
 *   --skip-cleanup     Skip the cleanup step
 *   --skip-tests       Skip test execution in validation
 *   --draft            Create a draft release
 *   --help             Display help message
 * 
 * Environment Variables:
 *   GITHUB_TOKEN       GitHub personal access token (required for release)
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
  magenta: '\x1b[35m',
};

/**
 * Logging utilities
 */
function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function logStep(stepNumber, totalSteps, message) {
  log(`\n[${ stepNumber}/${totalSteps}] ${message}`, colors.bright);
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
 * Orchestration configuration
 */
const ORCHESTRATION_CONFIG = {
  steps: [
    {
      name: 'cleanup',
      description: 'Clean unnecessary files',
      command: 'node scripts/cleanup-repository.js',
      required: true,
      skipFlag: '--skip-cleanup',
    },
    {
      name: 'validate',
      description: 'Validate release readiness',
      command: 'node scripts/validate-release.js',
      required: true,
      skipFlag: null,
    },
    {
      name: 'build',
      description: 'Build installers for all platforms',
      command: 'node scripts/build.js all',
      required: true,
      skipFlag: null,
    },
    {
      name: 'checksum',
      description: 'Generate SHA256 checksums',
      command: 'node scripts/generate-checksums.js',
      required: true,
      skipFlag: null,
    },
    {
      name: 'release',
      description: 'Create GitHub release and upload assets',
      command: 'node scripts/release-to-github.js',
      required: true,
      skipFlag: null,
    },
  ],
};

/**
 * Check if working directory is clean
 * @param {string} rootDir - Root directory of repository
 * @returns {Object} - Check result
 */
function checkWorkingDirectory(rootDir = process.cwd()) {
  logInfo('Checking working directory status...');
  
  const result = {
    clean: false,
    uncommittedFiles: [],
    errors: [],
  };
  
  try {
    // Check if git is available
    execSync('git --version', { stdio: 'ignore' });
    
    // Check for uncommitted changes
    const status = execSync('git status --porcelain', {
      cwd: rootDir,
      encoding: 'utf8',
    });
    
    if (status.trim().length === 0) {
      logSuccess('Working directory is clean');
      result.clean = true;
    } else {
      logWarning('Working directory has uncommitted changes:');
      const lines = status.trim().split('\n');
      result.uncommittedFiles = lines;
      
      lines.slice(0, 10).forEach(line => {
        log(`  ${line}`, colors.yellow);
      });
      
      if (lines.length > 10) {
        log(`  ... and ${lines.length - 10} more`, colors.yellow);
      }
      
      result.errors.push('Working directory has uncommitted changes');
    }
  } catch (error) {
    logWarning('Git not available or not a git repository');
    result.errors.push(`Cannot verify working directory: ${error.message}`);
  }
  
  return result;
}

/**
 * Execute a single step
 * @param {Object} step - Step configuration
 * @param {boolean} dryRun - Whether to run in dry-run mode
 * @param {Object} options - Additional options
 * @returns {Object} - Execution result
 */
function executeStep(step, dryRun = false, options = {}) {
  const startTime = Date.now();
  
  log(`\n${step.description}...`, colors.cyan);
  
  if (dryRun) {
    logInfo(`[DRY RUN] Would execute: ${step.command}`);
    return {
      step: step.name,
      success: true,
      skipped: true,
      duration: 0,
    };
  }
  
  try {
    // Build command with options
    let command = step.command;
    
    // Add step-specific options
    if (step.name === 'validate' && options.skipTests) {
      command += ' --skip-tests';
    }
    
    if (step.name === 'release') {
      if (options.draft) {
        command += ' --draft';
      }
      if (dryRun) {
        command += ' --dry-run';
      }
    }
    
    log(`> ${command}`, colors.blue);
    
    // Execute command
    execSync(command, {
      stdio: 'inherit',
      cwd: process.cwd(),
    });
    
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    logSuccess(`${step.description} completed (${duration}s)`);
    
    return {
      step: step.name,
      success: true,
      duration: parseFloat(duration),
    };
  } catch (error) {
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    logError(`${step.description} failed (${duration}s)`);
    logError(`Error: ${error.message}`);
    
    return {
      step: step.name,
      success: false,
      duration: parseFloat(duration),
      error: error.message,
    };
  }
}

/**
 * Execute all steps in sequence
 * @param {boolean} dryRun - Whether to run in dry-run mode
 * @param {Object} options - Additional options
 * @returns {Array} - Array of step results
 */
function executeAllSteps(dryRun = false, options = {}) {
  const results = [];
  const steps = ORCHESTRATION_CONFIG.steps.filter(step => {
    // Skip steps if their skip flag is present in options
    if (step.skipFlag && options[step.skipFlag.replace('--skip-', '')]) {
      logInfo(`Skipping ${step.description} (${step.skipFlag} flag)`);
      return false;
    }
    return true;
  });
  
  const totalSteps = steps.length;
  
  for (let i = 0; i < steps.length; i++) {
    const step = steps[i];
    logStep(i + 1, totalSteps, step.description);
    
    const result = executeStep(step, dryRun, options);
    results.push(result);
    
    // Halt on failure for required steps
    if (!result.success && step.required) {
      logError(`\nRequired step '${step.name}' failed. Halting release process.`);
      break;
    }
  }
  
  return results;
}

/**
 * Extract release information from results
 * @param {Array} results - Step results
 * @returns {Object} - Release information
 */
function extractReleaseInfo(results) {
  const releaseStep = results.find(r => r.step === 'release');
  
  if (!releaseStep || !releaseStep.success) {
    return null;
  }
  
  // Try to extract release URL and assets from release step
  // This would be populated by the release script
  return {
    url: releaseStep.releaseUrl || null,
    assets: releaseStep.assets || [],
  };
}

/**
 * Generate final release summary
 * @param {Array} results - Step results
 * @param {number} startTime - Start timestamp
 * @param {boolean} dryRun - Whether this was a dry run
 * @returns {Object} - Release summary
 */
function generateFinalSummary(results, startTime, dryRun = false) {
  const totalDuration = ((Date.now() - startTime) / 1000).toFixed(2);
  
  const summary = {
    success: results.every(r => r.success),
    dryRun,
    totalSteps: results.length,
    successfulSteps: results.filter(r => r.success).length,
    failedSteps: results.filter(r => !r.success).length,
    totalDuration: parseFloat(totalDuration),
    steps: results.map(r => ({
      name: r.step,
      success: r.success,
      duration: r.duration,
      error: r.error,
      skipped: r.skipped || false,
    })),
    timestamp: new Date().toISOString(),
  };
  
  // Add failed step name if any
  const failedStep = results.find(r => !r.success);
  if (failedStep) {
    summary.failedStep = failedStep.step;
  }
  
  // Extract release information
  const releaseInfo = extractReleaseInfo(results);
  if (releaseInfo) {
    if (releaseInfo.url) {
      summary.releaseUrl = releaseInfo.url;
    }
    if (releaseInfo.assets && releaseInfo.assets.length > 0) {
      summary.assets = releaseInfo.assets;
    }
  }
  
  return summary;
}

/**
 * Display final summary
 * @param {Object} summary - Release summary
 */
function displaySummary(summary) {
  log('\n' + '='.repeat(70), colors.bright);
  log('Release Summary', colors.bright);
  log('='.repeat(70), colors.bright);
  
  if (summary.dryRun) {
    log('\n🔍 DRY RUN MODE - No changes were made', colors.yellow);
  }
  
  log(`\nStatus: ${summary.success ? '✓ SUCCESS' : '✗ FAILED'}`, 
      summary.success ? colors.green : colors.red);
  
  log(`\nSteps Executed: ${summary.totalSteps}`);
  log(`  Successful: ${summary.successfulSteps}`, colors.green);
  
  if (summary.failedSteps > 0) {
    log(`  Failed: ${summary.failedSteps}`, colors.red);
    log(`  Failed at: ${summary.failedStep}`, colors.red);
  }
  
  log(`\nTotal Duration: ${summary.totalDuration}s`, colors.cyan);
  
  // Display step details
  log('\nStep Details:', colors.bright);
  summary.steps.forEach((step, index) => {
    const symbol = step.success ? '✓' : '✗';
    const color = step.success ? colors.green : colors.red;
    const status = step.skipped ? '(skipped)' : `(${step.duration}s)`;
    
    log(`  ${index + 1}. ${symbol} ${step.name} ${status}`, color);
    
    if (step.error) {
      log(`     Error: ${step.error}`, colors.red);
    }
  });
  
  // Display release information
  if (summary.releaseUrl) {
    log('\nRelease URL:', colors.bright);
    log(`  ${summary.releaseUrl}`, colors.cyan);
  }
  
  if (summary.assets && summary.assets.length > 0) {
    log('\nRelease Assets:', colors.bright);
    summary.assets.forEach(asset => {
      const sizeMB = (asset.size / (1024 * 1024)).toFixed(2);
      log(`  - ${asset.filename} (${sizeMB} MB)`, colors.cyan);
    });
  }
  
  log('\n' + '='.repeat(70), colors.bright);
  
  if (summary.success) {
    if (summary.dryRun) {
      log('\n✨ Dry run completed successfully!', colors.green);
      log('Run without --dry-run to perform the actual release.', colors.cyan);
    } else {
      log('\n🎉 Release completed successfully!', colors.green);
    }
  } else {
    log('\n❌ Release failed. Please fix the errors and try again.', colors.red);
  }
  
  log('');
}

/**
 * Orchestrate the complete release process
 * @param {Object} options - Orchestration options
 * @returns {Object} - Orchestration result
 */
function orchestrateRelease(options = {}) {
  const {
    dryRun = false,
    skipCleanup = false,
    skipTests = false,
    draft = false,
    rootDir = process.cwd(),
  } = options;
  
  const startTime = Date.now();
  
  log('='.repeat(70), colors.bright);
  log('PEFT Studio Complete Release Orchestration', colors.bright);
  log('='.repeat(70), colors.bright);
  
  if (dryRun) {
    log('\n🔍 DRY RUN MODE - No changes will be made\n', colors.yellow);
  }
  
  // Step 0: Verify working directory
  log('\n[0] Pre-flight Checks', colors.bright);
  const workingDirCheck = checkWorkingDirectory(rootDir);
  
  if (!workingDirCheck.clean && !dryRun) {
    logWarning('\nWorking directory is not clean. Uncommitted changes detected.');
    logWarning('It is recommended to commit or stash changes before releasing.');
    logInfo('Continuing anyway...\n');
  }
  
  // Execute all steps
  const stepOptions = {
    skipCleanup,
    skipTests,
    draft,
  };
  
  const results = executeAllSteps(dryRun, stepOptions);
  
  // Generate summary
  const summary = generateFinalSummary(results, startTime, dryRun);
  
  // Display summary
  displaySummary(summary);
  
  return {
    summary,
    workingDirCheck,
    results,
  };
}

/**
 * Display help message
 */
function displayHelp() {
  log(`
🚀 Complete Release Orchestration Script

Usage:
  node scripts/complete-release.js [options]

Options:
  --dry-run          Simulate the release without making changes
  --skip-cleanup     Skip the repository cleanup step
  --skip-tests       Skip test execution in validation step
  --draft            Create a draft GitHub release
  --help             Display this help message

Environment Variables:
  GITHUB_TOKEN       GitHub personal access token (required for release step)

Steps Executed:
  1. Cleanup         Remove unnecessary files from repository
  2. Validate        Verify repository is ready for release
  3. Build           Build installers for all platforms
  4. Checksum        Generate SHA256 checksums for all artifacts
  5. Release         Create GitHub release and upload assets

Examples:
  # Dry run to test the process
  node scripts/complete-release.js --dry-run

  # Full release
  node scripts/complete-release.js

  # Release without cleanup
  node scripts/complete-release.js --skip-cleanup

  # Create draft release
  node scripts/complete-release.js --draft

Requirements:
  - Git repository with clean working directory
  - Node.js and npm installed
  - GITHUB_TOKEN environment variable set
  - All required files (package.json, CHANGELOG.md, etc.)

For more information, see the documentation in docs/
`, colors.reset);
}

/**
 * Main function
 */
function main() {
  const args = process.argv.slice(2);
  
  // Check for help flag
  if (args.includes('--help') || args.includes('-h')) {
    displayHelp();
    process.exit(0);
  }
  
  // Parse options
  const options = {
    dryRun: args.includes('--dry-run'),
    skipCleanup: args.includes('--skip-cleanup'),
    skipTests: args.includes('--skip-tests'),
    draft: args.includes('--draft'),
  };
  
  try {
    const result = orchestrateRelease(options);
    
    // Exit with appropriate code
    process.exit(result.summary.success ? 0 : 1);
  } catch (error) {
    logError(`\nFatal error: ${error.message}`);
    console.error(error);
    process.exit(1);
  }
}

// Export functions for testing
module.exports = {
  ORCHESTRATION_CONFIG,
  checkWorkingDirectory,
  executeStep,
  executeAllSteps,
  generateFinalSummary,
  displaySummary,
  orchestrateRelease,
  extractReleaseInfo,
};

// Run main function if script is executed directly
if (require.main === module) {
  main();
}
