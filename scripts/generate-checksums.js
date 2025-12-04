#!/usr/bin/env node

/**
 * Checksum Generation Script
 * 
 * Generates SHA256 checksums for all release installer files.
 * Outputs checksums in the format: <hash>  <filename>
 * 
 * Usage:
 *   node scripts/generate-checksums.js [directory]
 * 
 * If no directory is specified, defaults to './release'
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

/**
 * Calculate SHA256 checksum for a file
 * @param {string} filePath - Path to the file
 * @returns {Promise<string>} - SHA256 hash in hexadecimal format
 */
function calculateChecksum(filePath) {
  return new Promise((resolve, reject) => {
    const hash = crypto.createHash('sha256');
    const stream = fs.createReadStream(filePath);
    
    stream.on('data', (data) => {
      hash.update(data);
    });
    
    stream.on('end', () => {
      resolve(hash.digest('hex'));
    });
    
    stream.on('error', (err) => {
      reject(err);
    });
  });
}

/**
 * Check if a file should be included in checksum generation
 * @param {string} filename - Name of the file
 * @returns {boolean} - True if file should be checksummed
 */
function shouldIncludeFile(filename) {
  const extensions = ['.exe', '.dmg', '.zip', '.AppImage', '.deb'];
  const excludePatterns = ['.blockmap', 'SHA256SUMS.txt'];
  
  // Check if file has a valid extension
  const hasValidExtension = extensions.some(ext => filename.endsWith(ext));
  
  // Check if file matches exclude patterns
  const isExcluded = excludePatterns.some(pattern => filename.includes(pattern));
  
  return hasValidExtension && !isExcluded;
}

/**
 * Generate checksums for all installer files in a directory
 * @param {string} directory - Directory containing installer files
 * @returns {Promise<Array<{file: string, checksum: string}>>} - Array of file/checksum pairs
 */
async function generateChecksums(directory) {
  try {
    // Check if directory exists
    if (!fs.existsSync(directory)) {
      throw new Error(`Directory not found: ${directory}`);
    }
    
    // Read all files in directory
    const files = fs.readdirSync(directory);
    
    // Filter files that should be checksummed
    const installerFiles = files.filter(shouldIncludeFile);
    
    if (installerFiles.length === 0) {
      console.warn(`⚠️  No installer files found in ${directory}`);
      return [];
    }
    
    console.log(`📦 Found ${installerFiles.length} installer file(s) to checksum`);
    
    // Calculate checksums for all files
    const checksums = [];
    for (const file of installerFiles) {
      const filePath = path.join(directory, file);
      
      try {
        console.log(`   Calculating checksum for: ${file}`);
        const checksum = await calculateChecksum(filePath);
        checksums.push({ file, checksum });
        console.log(`   ✓ ${checksum}`);
      } catch (err) {
        console.error(`   ✗ Error calculating checksum for ${file}:`, err.message);
        throw err;
      }
    }
    
    return checksums;
  } catch (err) {
    console.error(`❌ Error generating checksums:`, err.message);
    throw err;
  }
}

/**
 * Write checksums to SHA256SUMS.txt file
 * @param {Array<{file: string, checksum: string}>} checksums - Array of file/checksum pairs
 * @param {string} outputPath - Path to output file
 */
function writeChecksumsFile(checksums, outputPath) {
  try {
    // Format: <hash>  <filename> (two spaces between hash and filename)
    const content = checksums
      .map(({ checksum, file }) => `${checksum}  ${file}`)
      .join('\n') + '\n';
    
    fs.writeFileSync(outputPath, content, 'utf8');
    console.log(`\n✅ Checksums written to: ${outputPath}`);
    console.log(`   Total files: ${checksums.length}`);
  } catch (err) {
    console.error(`❌ Error writing checksums file:`, err.message);
    throw err;
  }
}

/**
 * Verify checksums from SHA256SUMS.txt file
 * @param {string} directory - Directory containing SHA256SUMS.txt and installer files
 * @returns {Promise<{valid: boolean, verified: string[], failed: string[], missing: string[]}>}
 */
async function verifyChecksums(directory) {
  try {
    const checksumsFilePath = path.join(directory, 'SHA256SUMS.txt');
    
    // Check if checksums file exists
    if (!fs.existsSync(checksumsFilePath)) {
      throw new Error(`Checksums file not found: ${checksumsFilePath}`);
    }
    
    // Read checksums file
    const content = fs.readFileSync(checksumsFilePath, 'utf8');
    const lines = content.trim().split('\n').filter(line => line.length > 0);
    
    const verified = [];
    const failed = [];
    const missing = [];
    
    console.log(`\n🔍 Verifying ${lines.length} checksum(s)...\n`);
    
    for (const line of lines) {
      // Validate format
      if (!validateChecksumFormat(line)) {
        console.error(`   ✗ Invalid format: ${line}`);
        failed.push({ file: line, reason: 'Invalid format' });
        continue;
      }
      
      // Parse line
      const expectedHash = line.substring(0, 64);
      const filename = line.substring(66);
      const filePath = path.join(directory, filename);
      
      // Check if file exists
      if (!fs.existsSync(filePath)) {
        console.error(`   ✗ File not found: ${filename}`);
        missing.push(filename);
        continue;
      }
      
      // Recalculate checksum
      try {
        const actualHash = await calculateChecksum(filePath);
        
        if (actualHash === expectedHash) {
          console.log(`   ✓ ${filename}`);
          verified.push(filename);
        } else {
          console.error(`   ✗ Checksum mismatch: ${filename}`);
          console.error(`      Expected: ${expectedHash}`);
          console.error(`      Actual:   ${actualHash}`);
          failed.push({ file: filename, expected: expectedHash, actual: actualHash });
        }
      } catch (err) {
        console.error(`   ✗ Error verifying ${filename}:`, err.message);
        failed.push({ file: filename, reason: err.message });
      }
    }
    
    const valid = failed.length === 0 && missing.length === 0;
    
    return { valid, verified, failed, missing };
  } catch (err) {
    console.error(`❌ Error verifying checksums:`, err.message);
    throw err;
  }
}

/**
 * Validate checksum line format
 * @param {string} line - Line from SHA256SUMS.txt
 * @returns {boolean} - True if format is valid
 */
function validateChecksumFormat(line) {
  // Format: <64 hex chars>  <filename>
  const formatRegex = /^[a-f0-9]{64}  .+$/;
  return formatRegex.test(line);
}

/**
 * Display help message
 */
function displayHelp() {
  console.log(`
🔐 SHA256 Checksum Generator

Usage:
  node generate-checksums.js [directory]           Generate checksums for installer files
  node generate-checksums.js verify [directory]    Verify existing checksums
  node generate-checksums.js --help                Display this help message

Options:
  directory    Directory containing installer files (default: ./release)

Examples:
  node generate-checksums.js                       Generate checksums in ./release
  node generate-checksums.js ./dist                Generate checksums in ./dist
  node generate-checksums.js verify                Verify checksums in ./release
  node generate-checksums.js verify ./dist         Verify checksums in ./dist
`);
}

/**
 * Main function
 */
async function main() {
  try {
    // Parse command line arguments
    const args = process.argv.slice(2);
    const command = args[0];
    
    // Check for help command
    if (command === '--help' || command === '-h' || command === 'help') {
      displayHelp();
      process.exit(0);
    }
    
    // Check for verify command
    if (command === 'verify' || command === '--verify' || command === '-v') {
      const directory = args[1] || './release';
      
      console.log(`\n🔐 Verifying SHA256 checksums in: ${directory}\n`);
      
      const result = await verifyChecksums(directory);
      
      console.log(`\n📊 Verification Summary:`);
      console.log(`   ✓ Verified: ${result.verified.length}`);
      console.log(`   ✗ Failed: ${result.failed.length}`);
      console.log(`   ⚠️  Missing: ${result.missing.length}`);
      
      if (result.valid) {
        console.log('\n✅ All checksums verified successfully!\n');
        process.exit(0);
      } else {
        console.log('\n❌ Checksum verification failed!\n');
        
        if (result.failed.length > 0) {
          console.log('Failed verifications:');
          for (const item of result.failed) {
            if (item.reason) {
              console.log(`   - ${item.file}: ${item.reason}`);
            } else {
              console.log(`   - ${item.file}`);
            }
          }
        }
        
        if (result.missing.length > 0) {
          console.log('\nMissing files:');
          for (const file of result.missing) {
            console.log(`   - ${file}`);
          }
        }
        
        console.log();
        process.exit(1);
      }
    }
    
    // Default: Generate checksums
    const directory = command || './release';
    const outputPath = path.join(directory, 'SHA256SUMS.txt');
    
    console.log(`\n🔐 Generating SHA256 checksums for installers in: ${directory}\n`);
    
    // Generate checksums
    const checksums = await generateChecksums(directory);
    
    if (checksums.length === 0) {
      console.log('\n⚠️  No checksums generated. Exiting.');
      process.exit(0);
    }
    
    // Write checksums to file
    writeChecksumsFile(checksums, outputPath);
    
    // Verify checksums immediately after generation
    console.log('\n🔍 Verifying generated checksums...\n');
    const verification = await verifyChecksums(directory);
    
    if (verification.valid) {
      console.log('✅ All checksums verified successfully!');
    } else {
      console.log('⚠️  Some checksums could not be verified');
    }
    
    console.log('\n✨ Checksum generation complete!\n');
    process.exit(0);
  } catch (err) {
    console.error('\n❌ Checksum generation failed:', err.message);
    process.exit(1);
  }
}

// Run main function if script is executed directly
if (require.main === module) {
  main();
}

// Export functions for testing
module.exports = {
  calculateChecksum,
  shouldIncludeFile,
  generateChecksums,
  writeChecksumsFile,
  verifyChecksums,
  validateChecksumFormat
};
