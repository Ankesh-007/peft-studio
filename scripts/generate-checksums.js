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
 * Main function
 */
async function main() {
  try {
    // Get directory from command line argument or use default
    const directory = process.argv[2] || './release';
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
  writeChecksumsFile
};
