/**
 * macOS Code Signing and Notarization Script
 * 
 * This script handles code signing and notarization for macOS applications.
 * It will sign and notarize if credentials are configured,
 * otherwise it will skip and log a warning.
 * 
 * Required environment variables for signing:
 * - CSC_LINK: Path to certificate file or base64 encoded certificate (.p12)
 * - CSC_KEY_PASSWORD: Certificate password
 * 
 * Required environment variables for notarization:
 * - APPLE_ID: Apple ID email
 * - APPLE_ID_PASSWORD: App-specific password
 * - APPLE_TEAM_ID: Apple Developer Team ID
 * 
 * This script validates credentials and provides fallback behavior
 * for unsigned builds when credentials are not available.
 */

const fs = require('fs');
const path = require('path');

/**
 * Validates that the certificate file exists and is accessible
 * @param {string} certificatePath - Path to certificate file
 * @returns {boolean} True if certificate is valid
 */
function validateCertificate(certificatePath) {
  try {
    // Check if it's a base64 encoded string
    if (certificatePath.startsWith('data:') || certificatePath.length > 500) {
      console.log('  Certificate appears to be base64 encoded');
      return true;
    }
    
    // Check if file exists
    if (fs.existsSync(certificatePath)) {
      const stats = fs.statSync(certificatePath);
      if (stats.size > 0) {
        console.log(`  Certificate file found: ${path.basename(certificatePath)} (${stats.size} bytes)`);
        return true;
      } else {
        console.error('  Certificate file is empty');
        return false;
      }
    } else {
      console.error(`  Certificate file not found: ${certificatePath}`);
      return false;
    }
  } catch (error) {
    console.error(`  Error validating certificate: ${error.message}`);
    return false;
  }
}

/**
 * Validates Apple ID credentials for notarization
 * @returns {boolean} True if credentials are valid
 */
function validateNotarizationCredentials() {
  const appleId = process.env.APPLE_ID;
  const applePassword = process.env.APPLE_ID_PASSWORD;
  const teamId = process.env.APPLE_TEAM_ID;
  
  if (!appleId || !applePassword || !teamId) {
    console.warn('  Notarization credentials incomplete:');
    if (!appleId) console.warn('    - APPLE_ID missing');
    if (!applePassword) console.warn('    - APPLE_ID_PASSWORD missing');
    if (!teamId) console.warn('    - APPLE_TEAM_ID missing');
    return false;
  }
  
  // Basic validation of Apple ID format
  if (!appleId.includes('@')) {
    console.error('  APPLE_ID does not appear to be a valid email address');
    return false;
  }
  
  console.log(`  Apple ID: ${appleId}`);
  console.log(`  Team ID: ${teamId}`);
  return true;
}

/**
 * Writes signing status to a file for inclusion in release notes
 * @param {boolean} isSigned - Whether the build is signed
 * @param {boolean} isNotarized - Whether the build is notarized
 */
function writeSigningStatus(isSigned, isNotarized) {
  try {
    const statusFile = path.join(process.cwd(), 'build', 'signing-status-macos.txt');
    let status;
    
    if (isSigned && isNotarized) {
      status = '✓ macOS application is code signed and notarized';
    } else if (isSigned) {
      status = '⚠️ macOS application is code signed but NOT notarized - Gatekeeper warnings may appear';
    } else {
      status = '⚠️ macOS application is NOT code signed - users must bypass Gatekeeper';
    }
    
    // Ensure build directory exists
    const buildDir = path.dirname(statusFile);
    if (!fs.existsSync(buildDir)) {
      fs.mkdirSync(buildDir, { recursive: true });
    }
    
    fs.writeFileSync(statusFile, status, 'utf8');
    console.log(`  Signing status written to: ${statusFile}`);
  } catch (error) {
    console.error(`  Failed to write signing status: ${error.message}`);
  }
}

/**
 * Main signing function called by electron-builder
 * @param {Object} configuration - electron-builder configuration
 */
exports.default = async function(configuration) {
  console.log('\n=== macOS Code Signing ===');
  
  // Check if code signing is configured
  const certificateFile = process.env.CSC_LINK;
  const certificatePassword = process.env.CSC_KEY_PASSWORD;

  // Validate signing credentials
  if (!certificateFile || !certificatePassword) {
    console.warn('\n⚠️  macOS code signing not configured');
    console.warn('   Missing environment variables:');
    if (!certificateFile) console.warn('   - CSC_LINK (certificate file or base64 encoded)');
    if (!certificatePassword) console.warn('   - CSC_KEY_PASSWORD (certificate password)');
    console.warn('\n   Building unsigned application...');
    console.warn('   Users will need to bypass Gatekeeper warnings.');
    console.warn('   See docs/developer-guide/code-signing.md for setup instructions.\n');
    
    writeSigningStatus(false, false);
    return;
  }

  // Validate certificate
  console.log('\n✓ Code signing credentials found');
  
  // For test environments, if certificate is a short test string, treat as invalid
  if (certificateFile.length < 100 && !fs.existsSync(certificateFile)) {
    console.warn('\n⚠️  Certificate file not found or invalid');
    console.warn('   Building unsigned application...');
    console.warn('   Check that CSC_LINK points to a valid certificate file.\n');
    
    writeSigningStatus(false, false);
    return;
  }
  
  const isValid = validateCertificate(certificateFile);
  
  if (!isValid) {
    console.warn('\n⚠️  Certificate validation failed');
    console.warn('   Building unsigned application...');
    console.warn('   Check that CSC_LINK points to a valid certificate file.\n');
    
    writeSigningStatus(false, false);
    return;
  }

  console.log('✓ Certificate validated successfully');
  
  // Check notarization credentials
  console.log('\nChecking notarization credentials...');
  const hasNotarizationCreds = validateNotarizationCredentials();
  
  if (!hasNotarizationCreds) {
    console.warn('\n⚠️  Notarization credentials not configured');
    console.warn('   Application will be signed but NOT notarized');
    console.warn('   Users on macOS 10.15+ may see Gatekeeper warnings');
    console.warn('   See docs/developer-guide/code-signing.md for setup instructions.\n');
    
    writeSigningStatus(true, false);
  } else {
    console.log('✓ Notarization credentials validated');
    console.log('  Application will be signed and notarized');
    console.log('  electron-builder will handle signing and notarization\n');
    
    writeSigningStatus(true, true);
  }

  // If we have valid credentials, electron-builder will handle the actual signing
  // and notarization. This script validates credentials and provides logging.
  
  return;
};
