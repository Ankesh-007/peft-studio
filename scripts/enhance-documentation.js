#!/usr/bin/env node

/**
 * Documentation Enhancer Script
 * 
 * Enhances repository documentation by:
 * - Adding/updating README badges (version, license, downloads)
 * - Verifying all required documentation files exist
 * - Updating package.json metadata
 * - Validating markdown formatting
 * 
 * Usage:
 *   node scripts/enhance-documentation.js [--dry-run]
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
 * Required documentation files
 */
const REQUIRED_DOCS = [
  'README.md',
  'LICENSE',
  'CONTRIBUTING.md',
  'CHANGELOG.md',
];

/**
 * Required README sections
 */
const REQUIRED_README_SECTIONS = [
  'Features',
  'Installation',
  'Usage',
  'Contributing',
  'License',
];

/**
 * Badge templates
 */
const BADGE_TEMPLATES = {
  version: (repo) => 
    `[![Release](https://img.shields.io/github/v/release/${repo})](https://github.com/${repo}/releases/latest)`,
  license: (license) => 
    `[![License: ${license}](https://img.shields.io/badge/License-${license}-yellow.svg)](LICENSE)`,
  downloads: (repo) => 
    `[![Downloads](https://img.shields.io/github/downloads/${repo}/total)](https://github.com/${repo}/releases)`,
};

/**
 * Generate badges for README
 * @param {Object} config - Configuration object
 * @param {string} config.version - Package version
 * @param {string} config.repository - Repository in format 'owner/repo'
 * @param {string} config.license - License type
 * @returns {Object} - Badge strings
 */
function generateBadges(config) {
  const { repository, license } = config;
  
  return {
    version: BADGE_TEMPLATES.version(repository),
    license: BADGE_TEMPLATES.license(license),
    downloads: BADGE_TEMPLATES.downloads(repository),
  };
}

/**
 * Extract existing badges from README
 * @param {string} content - README content
 * @returns {Array<string>} - Array of badge markdown strings
 */
function extractBadgesFromReadme(content) {
  const badgeRegex = /\[!\[.*?\]\(.*?\)\]\(.*?\)/g;
  const matches = content.match(badgeRegex);
  return matches || [];
}

/**
 * Update README with badges
 * @param {string} rootDir - Root directory
 * @param {Object} config - Configuration object
 * @param {boolean} dryRun - If true, don't actually update
 * @returns {Object} - Update result
 */
function updateReadmeBadges(rootDir, config, dryRun = false) {
  try {
    const readmePath = path.join(rootDir, 'README.md');
    
    if (!fs.existsSync(readmePath)) {
      log('  ✗ README.md not found', colors.red);
      return { updated: false, error: 'README.md not found' };
    }
    
    let content = fs.readFileSync(readmePath, 'utf8');
    const badges = generateBadges(config);
    
    // Extract existing badges
    const existingBadges = extractBadgesFromReadme(content);
    
    // Create badge section
    const badgeSection = `${badges.license}\n${badges.downloads}\n${badges.version}`;
    
    // Find the title line (first # heading)
    const titleMatch = content.match(/^#\s+.+$/m);
    
    if (!titleMatch) {
      log('  ✗ Could not find title in README.md', colors.red);
      return { updated: false, error: 'No title found' };
    }
    
    const titleLine = titleMatch[0];
    const titleIndex = content.indexOf(titleLine);
    const afterTitle = titleIndex + titleLine.length;
    
    // Check if badges already exist right after title
    if (existingBadges.length > 0) {
      // Replace existing badges
      const firstBadgeIndex = content.indexOf(existingBadges[0]);
      const lastBadgeIndex = content.indexOf(existingBadges[existingBadges.length - 1]);
      const lastBadgeEnd = lastBadgeIndex + existingBadges[existingBadges.length - 1].length;
      
      // Only replace if badges are near the title
      if (firstBadgeIndex < afterTitle + 100) {
        const before = content.substring(0, firstBadgeIndex);
        const after = content.substring(lastBadgeEnd);
        content = before + badgeSection + after;
      } else {
        // Add badges after title
        const before = content.substring(0, afterTitle);
        const after = content.substring(afterTitle);
        content = before + '\n\n' + badgeSection + '\n' + after;
      }
    } else {
      // Add badges after title
      const before = content.substring(0, afterTitle);
      const after = content.substring(afterTitle);
      content = before + '\n\n' + badgeSection + '\n' + after;
    }
    
    if (!dryRun) {
      fs.writeFileSync(readmePath, content, 'utf8');
    }
    
    log('  ✓ README badges updated', colors.green);
    return { updated: true };
  } catch (err) {
    log(`  ✗ Error updating README badges: ${err.message}`, colors.red);
    return { updated: false, error: err.message };
  }
}

/**
 * Check for required documentation files
 * @param {string} rootDir - Root directory
 * @returns {Array<string>} - Array of missing files
 */
function checkRequiredDocFiles(rootDir) {
  const missing = [];
  
  for (const file of REQUIRED_DOCS) {
    const filePath = path.join(rootDir, file);
    if (!fs.existsSync(filePath)) {
      missing.push(file);
    }
  }
  
  return missing;
}

/**
 * Validate markdown formatting
 * @param {string} content - Markdown content
 * @returns {Object} - Validation result
 */
function validateMarkdownFormatting(content) {
  const errors = [];
  
  // Check for proper heading spacing (# Title, not #Title)
  const badHeadings = content.match(/^#{1,6}[^\s#]/gm);
  if (badHeadings) {
    errors.push(`Found ${badHeadings.length} heading(s) without space after #`);
  }
  
  // Check for proper list formatting (- Item, not -Item)
  const badLists = content.match(/^-[^\s-]/gm);
  if (badLists) {
    errors.push(`Found ${badLists.length} list item(s) without space after -`);
  }
  
  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Extract links from markdown content
 * @param {string} content - Markdown content
 * @returns {Array<Object>} - Array of link objects with url and text
 */
function extractLinksFromMarkdown(content) {
  const links = [];
  
  // Match markdown links [text](url)
  const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
  let match;
  
  while ((match = linkRegex.exec(content)) !== null) {
    links.push({
      text: match[1],
      url: match[2],
      type: 'markdown',
    });
  }
  
  // Match HTML links <a href="url">text</a>
  const htmlLinkRegex = /<a\s+href=["']([^"']+)["'][^>]*>([^<]*)<\/a>/gi;
  
  while ((match = htmlLinkRegex.exec(content)) !== null) {
    links.push({
      text: match[2],
      url: match[1],
      type: 'html',
    });
  }
  
  return links;
}

/**
 * Validate documentation links
 * @param {string} rootDir - Root directory
 * @returns {Object} - Validation result with broken links
 */
function validateDocumentationLinks(rootDir) {
  const result = {
    valid: true,
    totalLinks: 0,
    validLinks: 0,
    brokenLinks: [],
    warnings: [],
  };
  
  // Check README links
  const readmePath = path.join(rootDir, 'README.md');
  if (fs.existsSync(readmePath)) {
    const readmeContent = fs.readFileSync(readmePath, 'utf8');
    const links = extractLinksFromMarkdown(readmeContent);
    
    result.totalLinks += links.length;
    
    for (const link of links) {
      const { url } = link;
      
      // Skip external URLs (http/https)
      if (url.startsWith('http://') || url.startsWith('https://')) {
        result.validLinks++;
        continue;
      }
      
      // Skip anchors
      if (url.startsWith('#')) {
        result.validLinks++;
        continue;
      }
      
      // Check if local file exists
      const linkPath = path.join(rootDir, url);
      if (!fs.existsSync(linkPath)) {
        result.brokenLinks.push({
          file: 'README.md',
          url,
          text: link.text,
        });
        result.valid = false;
      } else {
        result.validLinks++;
      }
    }
  }
  
  // Check CONTRIBUTING.md links
  const contributingPath = path.join(rootDir, 'CONTRIBUTING.md');
  if (fs.existsSync(contributingPath)) {
    const contributingContent = fs.readFileSync(contributingPath, 'utf8');
    const links = extractLinksFromMarkdown(contributingContent);
    
    result.totalLinks += links.length;
    
    for (const link of links) {
      const { url } = link;
      
      // Skip external URLs and anchors
      if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('#')) {
        result.validLinks++;
        continue;
      }
      
      // Check if local file exists
      const linkPath = path.join(rootDir, url);
      if (!fs.existsSync(linkPath)) {
        result.brokenLinks.push({
          file: 'CONTRIBUTING.md',
          url,
          text: link.text,
        });
        result.valid = false;
      } else {
        result.validLinks++;
      }
    }
  }
  
  return result;
}

/**
 * Check for screenshots or images in README
 * @param {string} rootDir - Root directory
 * @returns {Object} - Result with image information
 */
function checkReadmeImages(rootDir) {
  const result = {
    hasImages: false,
    imageCount: 0,
    images: [],
    missingImages: [],
  };
  
  const readmePath = path.join(rootDir, 'README.md');
  if (!fs.existsSync(readmePath)) {
    return result;
  }
  
  const readmeContent = fs.readFileSync(readmePath, 'utf8');
  
  // Match markdown images ![alt](url)
  const imageRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
  let match;
  
  while ((match = imageRegex.exec(readmeContent)) !== null) {
    const alt = match[1];
    const url = match[2];
    
    result.imageCount++;
    result.images.push({ alt, url });
    
    // Check if local image exists
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      const imagePath = path.join(rootDir, url);
      if (!fs.existsSync(imagePath)) {
        result.missingImages.push({ alt, url });
      }
    }
  }
  
  result.hasImages = result.imageCount > 0;
  
  return result;
}

/**
 * Verify documentation completeness
 * @param {string} rootDir - Root directory
 * @returns {Object} - Verification result
 */
function verifyDocumentation(rootDir) {
  const result = {
    valid: true,
    readmeComplete: false,
    licenseExists: false,
    contributingExists: false,
    changelogCurrent: false,
    missingDocs: [],
    docsWellFormatted: true,
    formattingErrors: [],
    linksValid: true,
    brokenLinks: [],
    hasScreenshots: false,
    imageInfo: null,
  };
  
  // Check for required files
  result.missingDocs = checkRequiredDocFiles(rootDir);
  result.licenseExists = !result.missingDocs.includes('LICENSE');
  result.contributingExists = !result.missingDocs.includes('CONTRIBUTING.md');
  result.changelogCurrent = !result.missingDocs.includes('CHANGELOG.md');
  
  if (result.missingDocs.length > 0) {
    result.valid = false;
  }
  
  // Check README completeness
  const readmePath = path.join(rootDir, 'README.md');
  if (fs.existsSync(readmePath)) {
    const readmeContent = fs.readFileSync(readmePath, 'utf8');
    
    // Check for required sections
    const missingSections = REQUIRED_README_SECTIONS.filter(section => {
      const regex = new RegExp(`##?\\s+${section}`, 'i');
      return !regex.test(readmeContent);
    });
    
    result.readmeComplete = missingSections.length === 0;
    
    if (!result.readmeComplete) {
      result.missingSections = missingSections;
    }
    
    // Validate markdown formatting
    const formatting = validateMarkdownFormatting(readmeContent);
    result.docsWellFormatted = formatting.valid;
    result.formattingErrors = formatting.errors;
    
    if (!formatting.valid) {
      result.valid = false;
    }
    
    // Validate links
    const linkValidation = validateDocumentationLinks(rootDir);
    result.linksValid = linkValidation.valid;
    result.brokenLinks = linkValidation.brokenLinks;
    result.totalLinks = linkValidation.totalLinks;
    result.validLinks = linkValidation.validLinks;
    
    if (!linkValidation.valid) {
      result.valid = false;
    }
    
    // Check for images/screenshots
    const imageInfo = checkReadmeImages(rootDir);
    result.hasScreenshots = imageInfo.hasImages;
    result.imageInfo = imageInfo;
  } else {
    result.readmeComplete = false;
    result.valid = false;
  }
  
  return result;
}

/**
 * Update package.json metadata
 * @param {string} rootDir - Root directory
 * @param {Object} updates - Metadata updates
 * @param {boolean} dryRun - If true, don't actually update
 * @returns {Object} - Update result
 */
function updatePackageMetadata(rootDir, updates, dryRun = false) {
  try {
    const packagePath = path.join(rootDir, 'package.json');
    
    if (!fs.existsSync(packagePath)) {
      log('  ✗ package.json not found', colors.red);
      return { updated: false, error: 'package.json not found' };
    }
    
    const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
    
    // Apply updates
    const updatedPackage = {
      ...packageJson,
      ...updates,
    };
    
    if (!dryRun) {
      fs.writeFileSync(
        packagePath,
        JSON.stringify(updatedPackage, null, 2) + '\n',
        'utf8'
      );
    }
    
    log('  ✓ package.json metadata updated', colors.green);
    return { updated: true };
  } catch (err) {
    log(`  ✗ Error updating package.json: ${err.message}`, colors.red);
    return { updated: false, error: err.message };
  }
}

/**
 * Main documentation enhancement function
 * @param {string} rootDir - Root directory of repository
 * @param {boolean} dryRun - If true, simulate without making changes
 * @returns {Object} - Enhancement results
 */
function enhanceDocumentation(rootDir = process.cwd(), dryRun = false) {
  log('\n' + '='.repeat(60), colors.bright);
  log('Documentation Enhancement', colors.bright);
  log('='.repeat(60), colors.bright);
  
  if (dryRun) {
    log('\n🔍 DRY RUN MODE - No files will be modified\n', colors.yellow);
  }
  
  const results = {
    success: true,
    badgesUpdated: false,
    metadataUpdated: false,
    verification: null,
  };
  
  // Step 1: Read package.json for configuration
  log('\n📋 Step 1: Reading package.json...', colors.cyan);
  
  const packagePath = path.join(rootDir, 'package.json');
  if (!fs.existsSync(packagePath)) {
    log('  ✗ package.json not found', colors.red);
    results.success = false;
    return results;
  }
  
  const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
  
  // Extract repository info
  let repository = packageJson.repository;
  if (typeof repository === 'object' && repository.url) {
    // Extract owner/repo from URL
    const match = repository.url.match(/github\.com[/:]([\w-]+)\/([\w-]+)/);
    if (match) {
      repository = `${match[1]}/${match[2]}`;
    }
  }
  
  const config = {
    version: packageJson.version || '1.0.0',
    repository: repository || 'user/repo',
    license: packageJson.license || 'MIT',
  };
  
  log(`  Version: ${config.version}`, colors.cyan);
  log(`  Repository: ${config.repository}`, colors.cyan);
  log(`  License: ${config.license}`, colors.cyan);
  
  // Step 2: Update README badges
  log('\n🏷️  Step 2: Updating README badges...', colors.cyan);
  const badgeResult = updateReadmeBadges(rootDir, config, dryRun);
  results.badgesUpdated = badgeResult.updated;
  
  // Step 3: Verify documentation
  log('\n📚 Step 3: Verifying documentation...', colors.cyan);
  const verification = verifyDocumentation(rootDir);
  results.verification = verification;
  
  if (verification.valid) {
    log('  ✓ All required documentation files present', colors.green);
    log('  ✓ README is complete', colors.green);
    log('  ✓ Markdown formatting is correct', colors.green);
    log('  ✓ All documentation links are valid', colors.green);
  } else {
    if (verification.missingDocs.length > 0) {
      log(`  ✗ Missing documentation files:`, colors.red);
      verification.missingDocs.forEach(file => {
        log(`    - ${file}`, colors.red);
      });
    }
    
    if (!verification.readmeComplete && verification.missingSections) {
      log(`  ✗ README missing sections:`, colors.yellow);
      verification.missingSections.forEach(section => {
        log(`    - ${section}`, colors.yellow);
      });
    }
    
    if (!verification.docsWellFormatted) {
      log(`  ✗ Markdown formatting issues:`, colors.yellow);
      verification.formattingErrors.forEach(error => {
        log(`    - ${error}`, colors.yellow);
      });
    }
    
    if (!verification.linksValid && verification.brokenLinks.length > 0) {
      log(`  ✗ Broken documentation links:`, colors.red);
      verification.brokenLinks.forEach(link => {
        log(`    - ${link.file}: ${link.url} (${link.text})`, colors.red);
      });
    }
  }
  
  // Report on screenshots/images
  if (verification.imageInfo) {
    if (verification.hasScreenshots) {
      log(`  ✓ README includes ${verification.imageInfo.imageCount} image(s)`, colors.green);
      if (verification.imageInfo.missingImages.length > 0) {
        log(`  ⚠ Missing image files:`, colors.yellow);
        verification.imageInfo.missingImages.forEach(img => {
          log(`    - ${img.url}`, colors.yellow);
        });
      }
    } else {
      log(`  ⚠ README has no screenshots or images`, colors.yellow);
    }
  }
  
  // Step 4: Update package.json metadata (if needed)
  log('\n📦 Step 4: Checking package.json metadata...', colors.cyan);
  
  const metadataUpdates = {};
  let needsUpdate = false;
  
  // Check if repository URLs are complete
  if (!packageJson.homepage) {
    metadataUpdates.homepage = `https://github.com/${config.repository}#readme`;
    needsUpdate = true;
  }
  
  if (!packageJson.bugs) {
    metadataUpdates.bugs = {
      url: `https://github.com/${config.repository}/issues`,
    };
    needsUpdate = true;
  }
  
  if (needsUpdate) {
    const metadataResult = updatePackageMetadata(rootDir, metadataUpdates, dryRun);
    results.metadataUpdated = metadataResult.updated;
  } else {
    log('  ✓ package.json metadata is complete', colors.green);
    results.metadataUpdated = true;
  }
  
  // Display summary
  log('\n' + '='.repeat(60), colors.bright);
  log('Enhancement Summary', colors.bright);
  log('='.repeat(60), colors.bright);
  
  log(`Badges updated: ${results.badgesUpdated ? '✓' : '✗'}`, 
    results.badgesUpdated ? colors.green : colors.red);
  log(`Metadata updated: ${results.metadataUpdated ? '✓' : '✗'}`, 
    results.metadataUpdated ? colors.green : colors.red);
  log(`Documentation valid: ${verification.valid ? '✓' : '✗'}`, 
    verification.valid ? colors.green : colors.yellow);
  
  if (dryRun) {
    log('\n💡 Run without --dry-run to apply changes', colors.yellow);
  } else {
    log('\n✨ Documentation enhancement complete!', colors.green);
  }
  
  return results;
}

/**
 * Main function
 */
function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes('--dry-run');
  
  try {
    const results = enhanceDocumentation(process.cwd(), dryRun);
    
    if (results.success && results.verification.valid) {
      process.exit(0);
    } else {
      process.exit(1);
    }
  } catch (err) {
    log(`\n❌ Enhancement failed: ${err.message}`, colors.red);
    console.error(err);
    process.exit(1);
  }
}

// Run main function if script is executed directly
if (require.main === module) {
  main();
}

// Export functions for testing
module.exports = {
  generateBadges,
  updateReadmeBadges,
  verifyDocumentation,
  updatePackageMetadata,
  enhanceDocumentation,
  extractBadgesFromReadme,
  validateMarkdownFormatting,
  checkRequiredDocFiles,
  extractLinksFromMarkdown,
  validateDocumentationLinks,
  checkReadmeImages,
  REQUIRED_DOCS,
  REQUIRED_README_SECTIONS,
  BADGE_TEMPLATES,
};
