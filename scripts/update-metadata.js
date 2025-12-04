#!/usr/bin/env node

/**
 * Update Repository Metadata Script
 * 
 * This script updates repository metadata including:
 * - Verifies and updates package.json repository URLs
 * - Adds/updates package.json keywords
 * - Updates all documentation with correct repository URLs
 * - Verifies repository description consistency
 */

const {
  checkUrlConsistency,
  updatePackageJsonUrls,
  updatePackageJsonKeywords,
  updateDocumentationUrls,
  verifyDescriptionConsistency,
  getRepositoryUrl,
} = require('./update-repository-metadata');

const fs = require('fs');
const path = require('path');

// Parse command line arguments
const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run') || args.includes('-d');
const verbose = args.includes('--verbose') || args.includes('-v');

console.log('='.repeat(60));
console.log('Repository Metadata Update');
console.log('='.repeat(60));
console.log();

if (dryRun) {
  console.log('🔍 DRY RUN MODE - No changes will be made\n');
}

// Step 1: Check URL consistency
console.log('📋 Step 1: Checking URL consistency...');
const urlCheck = checkUrlConsistency('.');

if (urlCheck.consistent) {
  console.log('✅ All documentation URLs are consistent');
} else {
  console.log(`⚠️  Found ${urlCheck.inconsistencies.length} URL inconsistencies:`);
  
  if (verbose) {
    urlCheck.inconsistencies.forEach(inc => {
      console.log(`   - ${inc.file}`);
      console.log(`     Found: ${inc.found}`);
      console.log(`     Expected: ${inc.expected}`);
    });
  } else {
    console.log(`   Use --verbose to see details`);
  }
  
  // Update documentation URLs
  if (!dryRun) {
    console.log('\n📝 Updating documentation URLs...');
    const docUpdate = updateDocumentationUrls('.', urlCheck.expectedUrl);
    
    if (docUpdate.updated) {
      console.log(`✅ Updated ${docUpdate.files.length} files:`);
      docUpdate.files.forEach(file => console.log(`   - ${file}`));
    } else {
      console.log('ℹ️  No files needed updating');
    }
  }
}

console.log();

// Step 2: Verify package.json metadata
console.log('📦 Step 2: Verifying package.json metadata...');

try {
  const packageJsonPath = path.join('.', 'package.json');
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  
  console.log(`   Repository: ${packageJson.repository?.url || 'NOT SET'}`);
  console.log(`   Homepage: ${packageJson.homepage || 'NOT SET'}`);
  console.log(`   Bugs: ${packageJson.bugs?.url || 'NOT SET'}`);
  console.log(`   Keywords: ${packageJson.keywords?.length || 0} keywords`);
  
  // Check if URLs are correct
  const repoUrl = getRepositoryUrl('.');
  const normalizedUrl = repoUrl.replace(/\.git$/, '');
  
  const urlsCorrect = 
    packageJson.repository?.url === `${normalizedUrl}.git` &&
    packageJson.homepage === `${normalizedUrl}#readme` &&
    packageJson.bugs?.url === `${normalizedUrl}/issues`;
  
  if (urlsCorrect) {
    console.log('✅ Package.json URLs are correct');
  } else {
    console.log('⚠️  Package.json URLs need updating');
    
    if (!dryRun) {
      console.log('\n📝 Updating package.json URLs...');
      const updates = updatePackageJsonUrls('.', normalizedUrl);
      
      if (updates.repository) console.log('   ✅ Updated repository URL');
      if (updates.homepage) console.log('   ✅ Updated homepage URL');
      if (updates.bugs) console.log('   ✅ Updated bugs URL');
    }
  }
} catch (error) {
  console.log(`❌ Error checking package.json: ${error.message}`);
}

console.log();

// Step 3: Verify description consistency
console.log('📄 Step 3: Verifying description consistency...');

const descCheck = verifyDescriptionConsistency('.');

if (descCheck.consistent) {
  console.log('✅ Package description appears in README');
} else {
  console.log('⚠️  Package description not found in README');
  console.log(`   Package.json: "${descCheck.packageDescription}"`);
  console.log('   Consider adding this description to README.md');
}

console.log();

// Summary
console.log('='.repeat(60));
console.log('Summary');
console.log('='.repeat(60));

if (dryRun) {
  console.log('🔍 Dry run completed - no changes were made');
  console.log('   Run without --dry-run to apply changes');
} else {
  console.log('✅ Repository metadata update completed');
}

console.log();

// Exit with appropriate code
const hasIssues = !urlCheck.consistent || !descCheck.consistent;
process.exit(hasIssues && dryRun ? 1 : 0);
