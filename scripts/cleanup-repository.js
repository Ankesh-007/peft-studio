#!/usr/bin/env node

/**
 * Repository Cleanup Script
 * 
 * Removes unnecessary files from the repository including:
 * - Build artifacts (release/*, dist/*, build/*)
 * - Test caches (.pytest_cache/, .hypothesis/)
 * - Temporary files (*.tmp, *.log, *_SUMMARY.md, *_STATUS.md)
 * - Python bytecode (__pycache__/, *.pyc)
 * 
 * Preserves essential files:
 * - Source code (src/, backend/)
 * - Documentation (docs/, *.md)
 * - Configuration files
 * 
 * Usage:
 *   node scripts/cleanup-repository.js [--dry-run]
 */

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
};

function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

/**
 * Configuration for cleanup operations
 */
const CLEANUP_CONFIG = {
  // Directories to remove entirely
  removeDirectories: [
    'dist',
    'build',
    '.pytest_cache',
    '.hypothesis',
  ],
  
  // Directory patterns to search and clean
  searchPatterns: {
    '__pycache__': { recursive: true, type: 'directory' },
    'release': { recursive: false, type: 'directory', selective: true },
  },
  
  // File patterns to remove
  filePatterns: [
    '*.pyc',
    '*.pyo',
    '*.tmp',
    '*.log',
    '*_SUMMARY.md',
    '*_STATUS.md',
    '*_COMPLETE.md',
  ],
  
  // Essential patterns to preserve (never delete)
  preservePatterns: [
    'src',
    'src/**/*',
    'backend',
    'backend/**/*',
    'docs',
    'docs/**/*',
    'scripts',
    'scripts/**/*',
    'README.md',
    'LICENSE',
    'CHANGELOG.md',
    'CONTRIBUTING.md',
    'package.json',
    'tsconfig.json',
    '*.config.js',
    '*.config.ts',
    '.gitignore',
    '.git',
    '.git/**/*',
  ],
  
  // Gitignore patterns to add
  gitignorePatterns: [
    '# Build artifacts',
    'release/*',
    'dist/',
    'build/',
    '',
    '# Test caches',
    '.pytest_cache/',
    '.hypothesis/',
    '',
    '# Python bytecode',
    '__pycache__/',
    '*.pyc',
    '*.pyo',
    '',
    '# Temporary files',
    '*.tmp',
    '*.log',
    '*_SUMMARY.md',
    '*_STATUS.md',
    '*_COMPLETE.md',
  ],
};

/**
 * Check if a path matches any of the preserve patterns
 * @param {string} filePath - Path to check
 * @param {string} rootDir - Root directory
 * @returns {boolean} - True if path should be preserved
 */
function shouldPreserve(filePath, rootDir) {
  const relativePath = path.relative(rootDir, filePath).replace(/\\/g, '/');
  
  // Never preserve __pycache__ directories or .pyc files
  if (relativePath.includes('__pycache__') || relativePath.endsWith('.pyc') || relativePath.endsWith('.pyo')) {
    return false;
  }
  
  // Never preserve test caches
  if (relativePath.includes('.pytest_cache') || relativePath.includes('.hypothesis')) {
    return false;
  }
  
  // Never preserve build artifacts
  if (relativePath.startsWith('dist/') || relativePath.startsWith('build/') || relativePath.startsWith('release/')) {
    return false;
  }
  
  // Check against preserve patterns
  for (const pattern of CLEANUP_CONFIG.preservePatterns) {
    if (matchesPattern(relativePath, pattern)) {
      return true;
    }
  }
  
  return false;
}

/**
 * Simple pattern matching (supports * wildcard and ** for recursive)
 * @param {string} filePath - Path to check
 * @param {string} pattern - Pattern to match against
 * @returns {boolean} - True if path matches pattern
 */
function matchesPattern(filePath, pattern) {
  // Normalize path separators to forward slashes for consistent matching
  const normalizedPath = filePath.replace(/\\/g, '/');
  const normalizedPattern = pattern.replace(/\\/g, '/');
  
  // Escape special regex characters except * and ?
  let regexPattern = normalizedPattern.replace(/[.+^${}()|[\]\\]/g, '\\$&');
  
  // Use placeholders to avoid conflicts during replacement
  // Replace **/* with a pattern that matches any path depth
  regexPattern = regexPattern.replace(/\*\*\/\*/g, '___GLOBSTAR_SLASH_STAR___');
  
  // Replace **/ with a pattern that matches zero or more path segments
  regexPattern = regexPattern.replace(/\*\*\//g, '___GLOBSTAR_SLASH___');
  
  // Replace /** with a pattern that matches zero or more path segments at the end
  regexPattern = regexPattern.replace(/\/\*\*/g, '___SLASH_GLOBSTAR___');
  
  // Replace remaining ** with pattern that matches anything
  regexPattern = regexPattern.replace(/\*\*/g, '___GLOBSTAR___');
  
  // Replace single * with pattern that matches anything except /
  regexPattern = regexPattern.replace(/\*/g, '[^/]*');
  
  // Replace ? with single character match
  regexPattern = regexPattern.replace(/\?/g, '.');
  
  // Now replace placeholders with actual regex patterns
  regexPattern = regexPattern.replace(/___GLOBSTAR_SLASH_STAR___/g, '.*');
  regexPattern = regexPattern.replace(/___GLOBSTAR_SLASH___/g, '(?:.*/)?' );
  regexPattern = regexPattern.replace(/___SLASH_GLOBSTAR___/g, '(?:/.*)?');
  regexPattern = regexPattern.replace(/___GLOBSTAR___/g, '.*');
  
  const regex = new RegExp(`^${regexPattern}$`);
  return regex.test(normalizedPath);
}

/**
 * Check if a file matches any of the file patterns
 * @param {string} filename - Filename to check
 * @returns {boolean} - True if file matches a removal pattern
 */
function matchesFilePattern(filename) {
  return CLEANUP_CONFIG.filePatterns.some(pattern => 
    matchesPattern(filename, pattern)
  );
}

/**
 * Get directory size recursively
 * @param {string} dirPath - Directory path
 * @returns {number} - Size in bytes
 */
function getDirectorySize(dirPath) {
  let totalSize = 0;
  
  try {
    if (!fs.existsSync(dirPath)) {
      return 0;
    }
    
    const stats = fs.statSync(dirPath);
    if (!stats.isDirectory()) {
      return stats.size;
    }
    
    const files = fs.readdirSync(dirPath);
    for (const file of files) {
      const filePath = path.join(dirPath, file);
      const fileStats = fs.statSync(filePath);
      
      if (fileStats.isDirectory()) {
        totalSize += getDirectorySize(filePath);
      } else {
        totalSize += fileStats.size;
      }
    }
  } catch (err) {
    // Ignore errors for inaccessible files
  }
  
  return totalSize;
}

/**
 * Format bytes to human-readable string
 * @param {number} bytes - Size in bytes
 * @returns {string} - Formatted string
 */
function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Remove a directory recursively
 * @param {string} dirPath - Directory path
 * @param {boolean} dryRun - If true, don't actually delete
 * @returns {number} - Size freed in bytes
 */
function removeDirectory(dirPath, dryRun = false) {
  let sizeFreed = 0;
  
  try {
    if (!fs.existsSync(dirPath)) {
      return 0;
    }
    
    sizeFreed = getDirectorySize(dirPath);
    
    if (!dryRun) {
      fs.rmSync(dirPath, { recursive: true, force: true });
    }
    
    return sizeFreed;
  } catch (err) {
    log(`  ✗ Error removing ${dirPath}: ${err.message}`, colors.red);
    return 0;
  }
}

/**
 * Remove a file
 * @param {string} filePath - File path
 * @param {boolean} dryRun - If true, don't actually delete
 * @returns {number} - Size freed in bytes
 */
function removeFile(filePath, dryRun = false) {
  try {
    if (!fs.existsSync(filePath)) {
      return 0;
    }
    
    const stats = fs.statSync(filePath);
    const size = stats.size;
    
    if (!dryRun) {
      fs.unlinkSync(filePath);
    }
    
    return size;
  } catch (err) {
    log(`  ✗ Error removing ${filePath}: ${err.message}`, colors.red);
    return 0;
  }
}

/**
 * Find all files matching patterns recursively
 * @param {string} dirPath - Directory to search
 * @param {Array<string>} patterns - File patterns to match
 * @param {string} rootDir - Root directory for preserve check
 * @returns {Array<string>} - Array of matching file paths
 */
function findMatchingFiles(dirPath, patterns, rootDir) {
  const matchingFiles = [];
  
  try {
    if (!fs.existsSync(dirPath)) {
      return matchingFiles;
    }
    
    const files = fs.readdirSync(dirPath);
    
    for (const file of files) {
      const filePath = path.join(dirPath, file);
      
      // Skip if should be preserved
      if (shouldPreserve(filePath, rootDir)) {
        continue;
      }
      
      const stats = fs.statSync(filePath);
      
      if (stats.isDirectory()) {
        // Recursively search subdirectories
        matchingFiles.push(...findMatchingFiles(filePath, patterns, rootDir));
      } else if (matchesFilePattern(file)) {
        matchingFiles.push(filePath);
      }
    }
  } catch (err) {
    // Ignore errors for inaccessible directories
  }
  
  return matchingFiles;
}

/**
 * Find all directories matching a pattern recursively
 * @param {string} dirPath - Directory to search
 * @param {string} pattern - Directory name pattern
 * @param {string} rootDir - Root directory for preserve check
 * @returns {Array<string>} - Array of matching directory paths
 */
function findMatchingDirectories(dirPath, pattern, rootDir) {
  const matchingDirs = [];
  
  try {
    if (!fs.existsSync(dirPath)) {
      return matchingDirs;
    }
    
    const files = fs.readdirSync(dirPath);
    
    for (const file of files) {
      const filePath = path.join(dirPath, file);
      
      try {
        const stats = fs.statSync(filePath);
        
        if (stats.isDirectory()) {
          if (file === pattern) {
            // Found a matching directory - add it regardless of preserve status
            // (shouldPreserve will handle the exclusion logic)
            if (!shouldPreserve(filePath, rootDir)) {
              matchingDirs.push(filePath);
            }
          } else {
            // Recursively search subdirectories
            matchingDirs.push(...findMatchingDirectories(filePath, pattern, rootDir));
          }
        }
      } catch (err) {
        // Ignore errors for inaccessible files
      }
    }
  } catch (err) {
    // Ignore errors for inaccessible directories
  }
  
  return matchingDirs;
}

/**
 * Clean release directory selectively (keep latest release files)
 * @param {string} releaseDir - Release directory path
 * @param {boolean} dryRun - If true, don't actually delete
 * @returns {Object} - Cleanup results
 */
function cleanReleaseDirectory(releaseDir, dryRun = false) {
  const results = {
    removed: [],
    preserved: [],
    sizeFreed: 0,
  };
  
  try {
    if (!fs.existsSync(releaseDir)) {
      return results;
    }
    
    const files = fs.readdirSync(releaseDir);
    
    // Patterns to preserve in release directory
    const preserveInRelease = [
      'SHA256SUMS.txt',
      'latest.yml',
      '.gitkeep',
    ];
    
    for (const file of files) {
      const filePath = path.join(releaseDir, file);
      const stats = fs.statSync(filePath);
      
      // Preserve specific files
      if (preserveInRelease.includes(file)) {
        results.preserved.push(filePath);
        continue;
      }
      
      // Remove subdirectories (like win-unpacked)
      if (stats.isDirectory()) {
        const size = removeDirectory(filePath, dryRun);
        results.sizeFreed += size;
        results.removed.push(filePath);
      }
    }
  } catch (err) {
    log(`  ✗ Error cleaning release directory: ${err.message}`, colors.red);
  }
  
  return results;
}

/**
 * Identify all unnecessary files in the repository
 * @param {string} rootDir - Root directory of repository
 * @returns {Object} - Lists of files to remove
 */
function identifyUnnecessaryFiles(rootDir) {
  const fileList = {
    buildArtifacts: [],
    temporaryFiles: [],
    testCaches: [],
    pythonBytecode: [],
  };
  
  // Find build artifact directories
  for (const dir of CLEANUP_CONFIG.removeDirectories) {
    const dirPath = path.join(rootDir, dir);
    if (fs.existsSync(dirPath)) {
      if (dir.includes('pytest') || dir.includes('hypothesis')) {
        fileList.testCaches.push(dirPath);
      } else {
        fileList.buildArtifacts.push(dirPath);
      }
    }
  }
  
  // Find __pycache__ directories
  const pycacheDirs = findMatchingDirectories(rootDir, '__pycache__', rootDir);
  fileList.pythonBytecode.push(...pycacheDirs);
  
  // Find temporary files
  const tempFiles = findMatchingFiles(rootDir, CLEANUP_CONFIG.filePatterns, rootDir);
  fileList.temporaryFiles.push(...tempFiles);
  
  return fileList;
}

/**
 * Remove unnecessary files
 * @param {Object} fileList - Lists of files to remove
 * @param {boolean} dryRun - If true, don't actually delete
 * @returns {Object} - Cleanup results
 */
function removeUnnecessaryFiles(fileList, dryRun = false) {
  const results = {
    removed: [],
    preserved: [],
    errors: [],
    totalSizeFreed: 0,
  };
  
  // Remove build artifacts
  for (const dirPath of fileList.buildArtifacts) {
    const size = removeDirectory(dirPath, dryRun);
    results.totalSizeFreed += size;
    results.removed.push(dirPath);
  }
  
  // Remove test caches
  for (const dirPath of fileList.testCaches) {
    const size = removeDirectory(dirPath, dryRun);
    results.totalSizeFreed += size;
    results.removed.push(dirPath);
  }
  
  // Remove Python bytecode
  for (const dirPath of fileList.pythonBytecode) {
    const size = removeDirectory(dirPath, dryRun);
    results.totalSizeFreed += size;
    results.removed.push(dirPath);
  }
  
  // Remove temporary files
  for (const filePath of fileList.temporaryFiles) {
    const size = removeFile(filePath, dryRun);
    results.totalSizeFreed += size;
    results.removed.push(filePath);
  }
  
  return results;
}

/**
 * Update .gitignore with cleanup patterns
 * @param {string} rootDir - Root directory of repository
 * @param {boolean} dryRun - If true, don't actually update
 * @returns {boolean} - True if updated successfully
 */
function updateGitignore(rootDir, dryRun = false) {
  try {
    const gitignorePath = path.join(rootDir, '.gitignore');
    
    // Read existing .gitignore
    let content = '';
    if (fs.existsSync(gitignorePath)) {
      content = fs.readFileSync(gitignorePath, 'utf8');
    }
    
    // Check which patterns are missing
    const missingPatterns = [];
    for (const pattern of CLEANUP_CONFIG.gitignorePatterns) {
      if (pattern === '' || pattern.startsWith('#')) {
        continue; // Skip empty lines and comments
      }
      
      if (!content.includes(pattern)) {
        missingPatterns.push(pattern);
      }
    }
    
    if (missingPatterns.length === 0) {
      log('  ✓ .gitignore already up to date', colors.green);
      return true;
    }
    
    if (!dryRun) {
      // Add missing patterns
      const newContent = content.trim() + '\n\n' + 
        CLEANUP_CONFIG.gitignorePatterns.join('\n') + '\n';
      fs.writeFileSync(gitignorePath, newContent, 'utf8');
    }
    
    log(`  ✓ Added ${missingPatterns.length} pattern(s) to .gitignore`, colors.green);
    return true;
  } catch (err) {
    log(`  ✗ Error updating .gitignore: ${err.message}`, colors.red);
    return false;
  }
}

/**
 * Generate cleanup report
 * @param {Object} results - Cleanup results
 * @param {number} startTime - Start timestamp
 * @returns {Object} - Cleanup report
 */
function generateCleanupReport(results, startTime) {
  const duration = Date.now() - startTime;
  
  return {
    filesRemoved: results.removed.length,
    sizeFreed: formatBytes(results.totalSizeFreed),
    categoriesCleared: [
      'Build artifacts',
      'Test caches',
      'Python bytecode',
      'Temporary files',
    ],
    timestamp: new Date().toISOString(),
    duration: `${(duration / 1000).toFixed(2)}s`,
  };
}

/**
 * Main cleanup function
 * @param {string} rootDir - Root directory of repository
 * @param {boolean} dryRun - If true, simulate without making changes
 * @returns {Object} - Cleanup results and report
 */
function cleanupRepository(rootDir = process.cwd(), dryRun = false) {
  const startTime = Date.now();
  
  log('\n' + '='.repeat(60), colors.bright);
  log('Repository Cleanup', colors.bright);
  log('='.repeat(60), colors.bright);
  
  if (dryRun) {
    log('\n🔍 DRY RUN MODE - No files will be deleted\n', colors.yellow);
  }
  
  // Step 1: Identify unnecessary files
  log('\n📋 Step 1: Identifying unnecessary files...', colors.cyan);
  const fileList = identifyUnnecessaryFiles(rootDir);
  
  const totalFiles = 
    fileList.buildArtifacts.length +
    fileList.temporaryFiles.length +
    fileList.testCaches.length +
    fileList.pythonBytecode.length;
  
  log(`  Found ${totalFiles} item(s) to remove:`, colors.yellow);
  log(`    - Build artifacts: ${fileList.buildArtifacts.length}`, colors.yellow);
  log(`    - Test caches: ${fileList.testCaches.length}`, colors.yellow);
  log(`    - Python bytecode: ${fileList.pythonBytecode.length}`, colors.yellow);
  log(`    - Temporary files: ${fileList.temporaryFiles.length}`, colors.yellow);
  
  // Step 2: Remove files
  log('\n🗑️  Step 2: Removing unnecessary files...', colors.cyan);
  const results = removeUnnecessaryFiles(fileList, dryRun);
  
  // Step 3: Clean release directory selectively
  log('\n📦 Step 3: Cleaning release directory...', colors.cyan);
  const releaseDir = path.join(rootDir, 'release');
  const releaseResults = cleanReleaseDirectory(releaseDir, dryRun);
  results.removed.push(...releaseResults.removed);
  results.totalSizeFreed += releaseResults.sizeFreed;
  
  // Step 4: Update .gitignore
  log('\n📝 Step 4: Updating .gitignore...', colors.cyan);
  updateGitignore(rootDir, dryRun);
  
  // Step 5: Generate report
  log('\n📊 Step 5: Generating cleanup report...', colors.cyan);
  const report = generateCleanupReport(results, startTime);
  
  // Display summary
  log('\n' + '='.repeat(60), colors.bright);
  log('Cleanup Summary', colors.bright);
  log('='.repeat(60), colors.bright);
  log(`Files removed: ${report.filesRemoved}`, colors.green);
  log(`Space freed: ${report.sizeFreed}`, colors.green);
  log(`Duration: ${report.duration}`, colors.cyan);
  log(`Timestamp: ${report.timestamp}`, colors.cyan);
  
  if (dryRun) {
    log('\n💡 Run without --dry-run to actually remove files', colors.yellow);
  } else {
    log('\n✨ Cleanup complete!', colors.green);
  }
  
  return { results, report, fileList };
}

/**
 * Main function
 */
function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes('--dry-run');
  
  try {
    cleanupRepository(process.cwd(), dryRun);
    process.exit(0);
  } catch (err) {
    log(`\n❌ Cleanup failed: ${err.message}`, colors.red);
    process.exit(1);
  }
}

// Run main function if script is executed directly
if (require.main === module) {
  main();
}

// Export functions for testing
module.exports = {
  identifyUnnecessaryFiles,
  removeUnnecessaryFiles,
  updateGitignore,
  generateCleanupReport,
  cleanupRepository,
  shouldPreserve,
  matchesPattern,
  matchesFilePattern,
  cleanReleaseDirectory,
  CLEANUP_CONFIG,
};
