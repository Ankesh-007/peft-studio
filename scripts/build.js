#!/usr/bin/env node

/**
 * Build script for PEFT Studio
 * Handles building installers for Windows, macOS, and Linux
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
};

function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function exec(command, options = {}) {
  log(`\n> ${command}`, colors.cyan);
  try {
    execSync(command, { stdio: 'inherit', ...options });
    return true;
  } catch (error) {
    log(`Error executing: ${command}`, colors.red);
    return false;
  }
}

function checkPrerequisites() {
  log('\n=== Checking Prerequisites ===', colors.bright);
  
  // Check if node_modules exists
  if (!fs.existsSync('node_modules')) {
    log('node_modules not found. Running npm install...', colors.yellow);
    if (!exec('npm install')) {
      log('Failed to install dependencies', colors.red);
      process.exit(1);
    }
  }
  
  // Check if build assets exist
  const buildDir = path.join(__dirname, '..', 'build');
  const requiredIcons = ['icon.png'];
  const missingIcons = requiredIcons.filter(icon => 
    !fs.existsSync(path.join(buildDir, icon))
  );
  
  if (missingIcons.length > 0) {
    log('\nWarning: Missing icon files:', colors.yellow);
    missingIcons.forEach(icon => log(`  - ${icon}`, colors.yellow));
    log('Using placeholder icons. Add proper icons to build/ directory.', colors.yellow);
  }
  
  log('Prerequisites check complete', colors.green);
}

function buildFrontend() {
  log('\n=== Building Frontend ===', colors.bright);
  
  if (!exec('npm run build')) {
    log('Frontend build failed', colors.red);
    process.exit(1);
  }
  
  log('Frontend build complete', colors.green);
}

function buildInstaller(platform) {
  log(`\n=== Building ${platform} Installer ===`, colors.bright);
  
  const targets = {
    windows: 'win',
    mac: 'mac',
    linux: 'linux',
    all: ''
  };
  
  const target = targets[platform];
  if (target === undefined) {
    log(`Unknown platform: ${platform}`, colors.red);
    log('Valid platforms: windows, mac, linux, all', colors.yellow);
    process.exit(1);
  }
  
  const command = target 
    ? `electron-builder --${target}` 
    : 'electron-builder --win --mac --linux';
  
  if (!exec(command)) {
    log(`${platform} installer build failed`, colors.red);
    process.exit(1);
  }
  
  log(`${platform} installer build complete`, colors.green);
}

function showOutputs() {
  log('\n=== Build Outputs ===', colors.bright);
  
  const releaseDir = path.join(__dirname, '..', 'release');
  if (!fs.existsSync(releaseDir)) {
    log('No release directory found', colors.yellow);
    return;
  }
  
  const files = fs.readdirSync(releaseDir);
  if (files.length === 0) {
    log('No build outputs found', colors.yellow);
    return;
  }
  
  log('\nGenerated installers:', colors.green);
  files.forEach(file => {
    const filePath = path.join(releaseDir, file);
    const stats = fs.statSync(filePath);
    if (stats.isFile()) {
      const sizeMB = (stats.size / (1024 * 1024)).toFixed(2);
      log(`  - ${file} (${sizeMB} MB)`, colors.cyan);
    }
  });
}

function main() {
  const args = process.argv.slice(2);
  const platform = args[0] || 'all';
  
  log('='.repeat(60), colors.bright);
  log('PEFT Studio Build Script', colors.bright);
  log('='.repeat(60), colors.bright);
  
  checkPrerequisites();
  buildFrontend();
  buildInstaller(platform);
  showOutputs();
  
  log('\n=== Build Complete ===', colors.bright);
  log('Installers are in the release/ directory', colors.green);
}

main();
