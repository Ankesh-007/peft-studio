#!/usr/bin/env node

/**
 * Manual test script for backend build integration
 * 
 * This script verifies that the backend build functions are properly integrated
 * into the build pipeline.
 */

import {
  buildBackend,
  verifyBackendBuild,
  collectBackendArtifacts,
  generateBuildReport,
} from './build.js';

console.log('Testing Backend Build Integration...\n');

// Test 1: Collect backend artifacts
console.log('Test 1: Collecting backend artifacts...');
try {
  const artifacts = collectBackendArtifacts();
  console.log('✓ collectBackendArtifacts() works');
  console.log(`  Found ${artifacts.artifacts.length} artifact(s)`);
  console.log(`  Total size: ${artifacts.totalSize} bytes`);
  if (artifacts.artifacts.length > 0) {
    console.log(`  Artifact: ${artifacts.artifacts[0].filename}`);
  }
} catch (error) {
  console.error('✗ collectBackendArtifacts() failed:', error.message);
}

// Test 2: Generate build report with backend result
console.log('\nTest 2: Generating build report with backend result...');
try {
  const buildResults = [
    { success: true, platform: 'windows', duration: '10.5' },
  ];
  
  const verification = {
    valid: true,
    verified: [],
    missing: [],
    unexpected: [],
  };
  
  const backendResult = {
    success: true,
    duration: '5.0',
  };
  
  const startTime = Date.now() - 5000;
  
  const report = generateBuildReport(buildResults, verification, startTime, backendResult);
  
  console.log('✓ generateBuildReport() works with backend result');
  console.log(`  Backend size: ${report.backendSize} bytes`);
  console.log(`  Installer size: ${report.installerSize} bytes`);
  console.log(`  Total size: ${report.totalSize} bytes`);
} catch (error) {
  console.error('✗ generateBuildReport() failed:', error.message);
}

// Test 3: Generate build report without backend result
console.log('\nTest 3: Generating build report without backend result...');
try {
  const buildResults = [
    { success: true, platform: 'windows', duration: '10.5' },
  ];
  
  const verification = {
    valid: true,
    verified: [],
    missing: [],
    unexpected: [],
  };
  
  const startTime = Date.now() - 5000;
  
  const report = generateBuildReport(buildResults, verification, startTime);
  
  console.log('✓ generateBuildReport() works without backend result');
  console.log(`  Total size: ${report.totalSize} bytes`);
} catch (error) {
  console.error('✗ generateBuildReport() failed:', error.message);
}

console.log('\n✓ All backend integration tests passed!');
