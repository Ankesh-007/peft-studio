#!/usr/bin/env node

/**
 * Build Environment Verification Script
 * 
 * Verifies that all required tools and dependencies are installed
 * before attempting to build the Python backend executable.
 * 
 * Requirements verified:
 * - PyInstaller installation (9.1)
 * - Python version 3.10+ (9.2)
 * - Platform-specific path handling (9.4)
 * - Installation instructions for missing dependencies (9.5)
 */

import { execSync } from 'child_process';
import path from 'path';
import os from 'os';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

/**
 * Execute a command and return the output
 * @param {string} command - Command to execute
 * @returns {string|null} - Command output or null if failed
 */
function executeCommand(command) {
  try {
    const output = execSync(command, {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 10000,
    });
    return output.trim();
  } catch (error) {
    return null;
  }
}

/**
 * Check if PyInstaller is installed
 * @returns {{installed: boolean, version: string|null}}
 */
function checkPyInstaller() {
  console.log(`${colors.cyan}Checking PyInstaller installation...${colors.reset}`);
  
  const version = executeCommand('pyinstaller --version');
  
  if (version) {
    console.log(`${colors.green}✓ PyInstaller found: ${version}${colors.reset}`);
    return { installed: true, version };
  } else {
    console.log(`${colors.red}✗ PyInstaller not found${colors.reset}`);
    return { installed: false, version: null };
  }
}

/**
 * Check Python version
 * @returns {{installed: boolean, version: string|null, meetsRequirement: boolean}}
 */
function checkPythonVersion() {
  console.log(`${colors.cyan}Checking Python version...${colors.reset}`);
  
  const versionOutput = executeCommand('python --version');
  
  if (!versionOutput) {
    console.log(`${colors.red}✗ Python not found${colors.reset}`);
    return { installed: false, version: null, meetsRequirement: false };
  }
  
  // Parse version string (e.g., "Python 3.10.5")
  const versionMatch = versionOutput.match(/Python (\d+)\.(\d+)\.(\d+)/);
  
  if (!versionMatch) {
    console.log(`${colors.red}✗ Could not parse Python version: ${versionOutput}${colors.reset}`);
    return { installed: true, version: versionOutput, meetsRequirement: false };
  }
  
  const major = parseInt(versionMatch[1], 10);
  const minor = parseInt(versionMatch[2], 10);
  const version = `${major}.${minor}.${versionMatch[3]}`;
  
  // Check if version is 3.10 or higher
  const meetsRequirement = major === 3 && minor >= 10;
  
  if (meetsRequirement) {
    console.log(`${colors.green}✓ Python ${version} found (3.10+ required)${colors.reset}`);
  } else {
    console.log(`${colors.red}✗ Python ${version} found, but 3.10+ is required${colors.reset}`);
  }
  
  return { installed: true, version, meetsRequirement };
}

/**
 * Get platform-specific installation instructions
 * @param {string} tool - Tool name ('pyinstaller' or 'python')
 * @returns {string} - Installation instructions
 */
function getInstallationInstructions(tool) {
  const platform = os.platform();
  
  if (tool === 'pyinstaller') {
    return `
${colors.yellow}PyInstaller Installation Instructions:${colors.reset}

  Using pip (recommended):
    ${colors.cyan}pip install pyinstaller${colors.reset}
  
  Or using pip3:
    ${colors.cyan}pip3 install pyinstaller${colors.reset}
  
  Verify installation:
    ${colors.cyan}pyinstaller --version${colors.reset}
`;
  }
  
  if (tool === 'python') {
    if (platform === 'win32') {
      return `
${colors.yellow}Python Installation Instructions (Windows):${colors.reset}

  1. Download Python 3.10 or later from:
     ${colors.cyan}https://www.python.org/downloads/${colors.reset}
  
  2. Run the installer and make sure to:
     - Check "Add Python to PATH"
     - Install for all users (optional)
  
  3. Verify installation:
     ${colors.cyan}python --version${colors.reset}
`;
    } else if (platform === 'darwin') {
      return `
${colors.yellow}Python Installation Instructions (macOS):${colors.reset}

  Using Homebrew (recommended):
    ${colors.cyan}brew install python@3.10${colors.reset}
  
  Or download from:
    ${colors.cyan}https://www.python.org/downloads/${colors.reset}
  
  Verify installation:
    ${colors.cyan}python3 --version${colors.reset}
`;
    } else {
      return `
${colors.yellow}Python Installation Instructions (Linux):${colors.reset}

  Using apt (Debian/Ubuntu):
    ${colors.cyan}sudo apt update${colors.reset}
    ${colors.cyan}sudo apt install python3.10 python3-pip${colors.reset}
  
  Using yum (RHEL/CentOS):
    ${colors.cyan}sudo yum install python310 python3-pip${colors.reset}
  
  Verify installation:
    ${colors.cyan}python3 --version${colors.reset}
`;
    }
  }
  
  return '';
}

/**
 * Display platform information
 */
function displayPlatformInfo() {
  const platform = os.platform();
  const arch = os.arch();
  const platformName = {
    win32: 'Windows',
    darwin: 'macOS',
    linux: 'Linux',
  }[platform] || platform;
  
  console.log(`${colors.blue}Platform: ${platformName} (${arch})${colors.reset}`);
  console.log('');
}

/**
 * Main verification function
 */
function main() {
  console.log('');
  console.log(`${colors.blue}═══════════════════════════════════════════════════════${colors.reset}`);
  console.log(`${colors.blue}  Build Environment Verification${colors.reset}`);
  console.log(`${colors.blue}═══════════════════════════════════════════════════════${colors.reset}`);
  console.log('');
  
  displayPlatformInfo();
  
  // Check Python version
  const pythonCheck = checkPythonVersion();
  console.log('');
  
  // Check PyInstaller
  const pyinstallerCheck = checkPyInstaller();
  console.log('');
  
  // Determine if build can proceed
  const canBuild = pythonCheck.installed && 
                   pythonCheck.meetsRequirement && 
                   pyinstallerCheck.installed;
  
  if (canBuild) {
    console.log(`${colors.green}═══════════════════════════════════════════════════════${colors.reset}`);
    console.log(`${colors.green}✓ Build environment is ready!${colors.reset}`);
    console.log(`${colors.green}═══════════════════════════════════════════════════════${colors.reset}`);
    console.log('');
    process.exit(0);
  } else {
    console.log(`${colors.red}═══════════════════════════════════════════════════════${colors.reset}`);
    console.log(`${colors.red}✗ Build environment verification failed${colors.reset}`);
    console.log(`${colors.red}═══════════════════════════════════════════════════════${colors.reset}`);
    console.log('');
    
    // Display installation instructions for missing components
    if (!pythonCheck.installed || !pythonCheck.meetsRequirement) {
      console.log(getInstallationInstructions('python'));
    }
    
    if (!pyinstallerCheck.installed) {
      console.log(getInstallationInstructions('pyinstaller'));
    }
    
    console.log(`${colors.yellow}After installing the required dependencies, run this script again.${colors.reset}`);
    console.log('');
    process.exit(1);
  }
}

// Run verification if executed directly
const isMainModule = import.meta.url.startsWith('file:') && 
                     process.argv[1] && 
                     fileURLToPath(import.meta.url) === process.argv[1];

if (isMainModule) {
  main();
}

// Export functions for testing
export {
  checkPyInstaller,
  checkPythonVersion,
  getInstallationInstructions,
  executeCommand,
};
