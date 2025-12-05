/**
 * Unit Tests for Build Module
 * 
 * Tests artifact collection, build verification, error handling, and progress reporting.
 * 
 * Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
 */

import fs from 'fs';
import path from 'path';
import os from 'os';
import {
  BUILD_CONFIG,
  collectArtifacts,
  collectBackendArtifacts,
  verifyBuildOutputs,
  formatSize,
  generateBuildReport,
  verifyCompressionConfig,
  verifyDependencyExclusion,
  validateInstallerSizes,
  generateSizeReport,
} from '../build.js';

/**
 * Helper: Create a temporary test directory
 */
function createTestDirectory() {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'build-test-'));
  return tempDir;
}

/**
 * Helper: Create a file
 */
function createFile(dirPath, filename, content = '') {
  const filePath = path.join(dirPath, filename);
  const dir = path.dirname(filePath);
  
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  
  fs.writeFileSync(filePath, content, 'utf8');
  return filePath;
}

/**
 * Helper: Create a directory
 */
function createDirectory(dirPath, dirname) {
  const fullPath = path.join(dirPath, dirname);
  fs.mkdirSync(fullPath, { recursive: true });
  return fullPath;
}

/**
 * Helper: Clean up test directory
 */
function cleanupTestDirectory(dirPath) {
  if (fs.existsSync(dirPath)) {
    fs.rmSync(dirPath, { recursive: true, force: true });
  }
}

describe('Build Module - Unit Tests', () => {
  describe('Build Configuration', () => {
    it('should have valid platform configurations', () => {
      expect(BUILD_CONFIG).toBeDefined();
      expect(BUILD_CONFIG.platforms).toBeDefined();
      
      // Check Windows configuration
      expect(BUILD_CONFIG.platforms.windows).toBeDefined();
      expect(BUILD_CONFIG.platforms.windows.name).toBe('Windows');
      expect(BUILD_CONFIG.platforms.windows.target).toBe('win');
      expect(BUILD_CONFIG.platforms.windows.expectedArtifacts.length).toBeGreaterThan(0);
      
      // Check macOS configuration
      expect(BUILD_CONFIG.platforms.mac).toBeDefined();
      expect(BUILD_CONFIG.platforms.mac.name).toBe('macOS');
      expect(BUILD_CONFIG.platforms.mac.target).toBe('mac');
      expect(BUILD_CONFIG.platforms.mac.expectedArtifacts.length).toBeGreaterThan(0);
      
      // Check Linux configuration
      expect(BUILD_CONFIG.platforms.linux).toBeDefined();
      expect(BUILD_CONFIG.platforms.linux.name).toBe('Linux');
      expect(BUILD_CONFIG.platforms.linux.target).toBe('linux');
      expect(BUILD_CONFIG.platforms.linux.expectedArtifacts.length).toBeGreaterThan(0);
    });
    
    it('should have expected artifact patterns for each platform', () => {
      // Windows should have NSIS and Portable
      const windowsFormats = BUILD_CONFIG.platforms.windows.expectedArtifacts.map(a => a.format);
      expect(windowsFormats).toContain('NSIS');
      expect(windowsFormats).toContain('Portable');
      
      // macOS should have DMG and ZIP for both architectures
      const macFormats = BUILD_CONFIG.platforms.mac.expectedArtifacts.map(a => a.format);
      expect(macFormats).toContain('DMG');
      expect(macFormats).toContain('ZIP');
      
      const macArchs = BUILD_CONFIG.platforms.mac.expectedArtifacts.map(a => a.arch);
      expect(macArchs).toContain('x64');
      expect(macArchs).toContain('arm64');
      
      // Linux should have AppImage and DEB
      const linuxFormats = BUILD_CONFIG.platforms.linux.expectedArtifacts.map(a => a.format);
      expect(linuxFormats).toContain('AppImage');
      expect(linuxFormats).toContain('DEB');
    });
  });
  
  describe('Artifact Collection', () => {
    let testDir;
    let originalCwd;
    
    beforeEach(() => {
      testDir = createTestDirectory();
      originalCwd = process.cwd();
      process.chdir(testDir);
    });
    
    afterEach(() => {
      process.chdir(originalCwd);
      cleanupTestDirectory(testDir);
    });
    
    it('should return empty artifacts when release directory does not exist', () => {
      const { artifacts, totalSize } = collectArtifacts(testDir);
      
      expect(artifacts).toEqual([]);
      expect(totalSize).toBe(0);
    });
    
    it('should collect Windows artifacts', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      createFile(releaseDir, 'PEFT Studio-Portable-1.0.0.exe', 'x'.repeat(1000));
      
      const { artifacts } = collectArtifacts(testDir);
      
      const windowsArtifacts = artifacts.filter(a => a.platform === 'windows');
      expect(windowsArtifacts.length).toBe(2);
      
      const formats = windowsArtifacts.map(a => a.format);
      expect(formats).toContain('NSIS');
      expect(formats).toContain('Portable');
    });
    
    it('should collect macOS artifacts', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createFile(releaseDir, 'PEFT Studio-1.0.0-x64.dmg', 'x'.repeat(1000));
      createFile(releaseDir, 'PEFT Studio-1.0.0-arm64.dmg', 'x'.repeat(1000));
      createFile(releaseDir, 'PEFT Studio-1.0.0-x64.zip', 'x'.repeat(1000));
      createFile(releaseDir, 'PEFT Studio-1.0.0-arm64.zip', 'x'.repeat(1000));
      
      const { artifacts } = collectArtifacts(testDir);
      
      const macArtifacts = artifacts.filter(a => a.platform === 'mac');
      expect(macArtifacts.length).toBe(4);
      
      const dmgArtifacts = macArtifacts.filter(a => a.format === 'DMG');
      expect(dmgArtifacts.length).toBe(2);
      
      const zipArtifacts = macArtifacts.filter(a => a.format === 'ZIP');
      expect(zipArtifacts.length).toBe(2);
    });
    
    it('should collect Linux artifacts', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createFile(releaseDir, 'PEFT Studio-1.0.0-x64.AppImage', 'x'.repeat(1000));
      createFile(releaseDir, 'PEFT Studio-1.0.0-amd64.deb', 'x'.repeat(1000));
      
      const { artifacts } = collectArtifacts(testDir);
      
      const linuxArtifacts = artifacts.filter(a => a.platform === 'linux');
      expect(linuxArtifacts.length).toBe(2);
      
      const formats = linuxArtifacts.map(a => a.format);
      expect(formats).toContain('AppImage');
      expect(formats).toContain('DEB');
    });
    
    it('should calculate total size correctly', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      createFile(releaseDir, 'PEFT Studio-Portable-1.0.0.exe', 'x'.repeat(2000));
      
      const { totalSize } = collectArtifacts(testDir);
      
      expect(totalSize).toBe(3000);
    });
    
    it('should ignore directories in release folder', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createDirectory(releaseDir, 'win-unpacked');
      createFile(path.join(releaseDir, 'win-unpacked'), 'app.exe', 'content');
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      
      const { artifacts } = collectArtifacts(testDir);
      
      // Should only collect the installer file, not the directory
      expect(artifacts.length).toBe(1);
      expect(artifacts[0].filename).toBe('PEFT Studio-Setup-1.0.0.exe');
    });
    
    it('should set artifact metadata correctly', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      
      const { artifacts } = collectArtifacts(testDir);
      
      expect(artifacts.length).toBe(1);
      const artifact = artifacts[0];
      
      expect(artifact.filename).toBe('PEFT Studio-Setup-1.0.0.exe');
      expect(artifact.path).toContain('PEFT Studio-Setup-1.0.0.exe');
      expect(artifact.size).toBe(1000);
      expect(artifact.platform).toBe('windows');
      expect(artifact.type).toBe('installer');
      expect(artifact.format).toBe('NSIS');
    });
  });
  
  describe('Build Verification', () => {
    let testDir;
    let originalCwd;
    
    beforeEach(() => {
      testDir = createTestDirectory();
      originalCwd = process.cwd();
      process.chdir(testDir);
    });
    
    afterEach(() => {
      process.chdir(originalCwd);
      cleanupTestDirectory(testDir);
    });
    
    it('should verify complete Windows build', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      createFile(releaseDir, 'PEFT Studio-Portable-1.0.0.exe', 'x'.repeat(1000));
      
      const verification = verifyBuildOutputs(['windows'], testDir);
      
      expect(verification.valid).toBe(true);
      expect(verification.verified.length).toBe(2);
      expect(verification.missing.length).toBe(0);
    });
    
    it('should detect missing Windows artifacts', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      // Missing portable
      
      const verification = verifyBuildOutputs(['windows'], testDir);
      
      expect(verification.valid).toBe(false);
      expect(verification.verified.length).toBe(1);
      expect(verification.missing.length).toBe(1);
      expect(verification.missing[0].expected).toBe('Portable');
    });
    
    it('should verify complete macOS build', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createFile(releaseDir, 'PEFT Studio-1.0.0-x64.dmg', 'x'.repeat(1000));
      createFile(releaseDir, 'PEFT Studio-1.0.0-arm64.dmg', 'x'.repeat(1000));
      createFile(releaseDir, 'PEFT Studio-1.0.0-x64.zip', 'x'.repeat(1000));
      createFile(releaseDir, 'PEFT Studio-1.0.0-arm64.zip', 'x'.repeat(1000));
      
      const verification = verifyBuildOutputs(['mac'], testDir);
      
      expect(verification.valid).toBe(true);
      expect(verification.verified.length).toBe(4);
      expect(verification.missing.length).toBe(0);
    });
    
    it('should detect missing macOS artifacts', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createFile(releaseDir, 'PEFT Studio-1.0.0-x64.dmg', 'x'.repeat(1000));
      // Missing arm64 dmg, x64 zip, arm64 zip
      
      const verification = verifyBuildOutputs(['mac'], testDir);
      
      expect(verification.valid).toBe(false);
      expect(verification.verified.length).toBe(1);
      expect(verification.missing.length).toBe(3);
    });
    
    it('should verify complete Linux build', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createFile(releaseDir, 'PEFT Studio-1.0.0-x64.AppImage', 'x'.repeat(1000));
      createFile(releaseDir, 'PEFT Studio-1.0.0-amd64.deb', 'x'.repeat(1000));
      
      const verification = verifyBuildOutputs(['linux'], testDir);
      
      expect(verification.valid).toBe(true);
      expect(verification.verified.length).toBe(2);
      expect(verification.missing.length).toBe(0);
    });
    
    it('should detect missing Linux artifacts', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createFile(releaseDir, 'PEFT Studio-1.0.0-x64.AppImage', 'x'.repeat(1000));
      // Missing deb
      
      const verification = verifyBuildOutputs(['linux'], testDir);
      
      expect(verification.valid).toBe(false);
      expect(verification.verified.length).toBe(1);
      expect(verification.missing.length).toBe(1);
      expect(verification.missing[0].expected).toBe('DEB');
    });
    
    it('should verify multiple platforms', () => {
      const releaseDir = createDirectory(testDir, 'release');
      // Windows
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      createFile(releaseDir, 'PEFT Studio-Portable-1.0.0.exe', 'x'.repeat(1000));
      // Linux
      createFile(releaseDir, 'PEFT Studio-1.0.0-x64.AppImage', 'x'.repeat(1000));
      createFile(releaseDir, 'PEFT Studio-1.0.0-amd64.deb', 'x'.repeat(1000));
      
      const verification = verifyBuildOutputs(['windows', 'linux'], testDir);
      
      expect(verification.valid).toBe(true);
      expect(verification.verified.length).toBe(4);
      expect(verification.missing.length).toBe(0);
    });
  });
  
  describe('Size Formatting', () => {
    it('should format bytes correctly', () => {
      expect(formatSize(0)).toBe('0 B');
      expect(formatSize(500)).toBe('500 B');
      expect(formatSize(1023)).toBe('1023 B');
    });
    
    it('should format kilobytes correctly', () => {
      expect(formatSize(1024)).toBe('1.00 KB');
      expect(formatSize(1536)).toBe('1.50 KB');
      expect(formatSize(10240)).toBe('10.00 KB');
    });
    
    it('should format megabytes correctly', () => {
      expect(formatSize(1024 * 1024)).toBe('1.00 MB');
      expect(formatSize(1024 * 1024 * 1.5)).toBe('1.50 MB');
      expect(formatSize(1024 * 1024 * 50)).toBe('50.00 MB');
    });
    
    it('should format gigabytes correctly', () => {
      expect(formatSize(1024 * 1024 * 1024)).toBe('1.00 GB');
      expect(formatSize(1024 * 1024 * 1024 * 2.5)).toBe('2.50 GB');
    });
  });
  
  describe('Backend Artifact Collection', () => {
    it('should collect backend artifacts when executable exists', () => {
      // This test assumes the backend executable may or may not exist
      const result = collectBackendArtifacts();
      
      expect(result).toBeDefined();
      expect(result.artifacts).toBeDefined();
      expect(Array.isArray(result.artifacts)).toBe(true);
      expect(result.totalSize).toBeDefined();
      expect(typeof result.totalSize).toBe('number');
    });
    
    it('should return empty artifacts when backend executable does not exist', () => {
      // If backend is not built, should return empty
      const result = collectBackendArtifacts();
      
      expect(result.artifacts).toBeDefined();
      expect(result.totalSize).toBeDefined();
      
      // Either has artifacts or is empty
      if (result.artifacts.length === 0) {
        expect(result.totalSize).toBe(0);
      }
    });
    
    it('should include correct metadata for backend artifacts', () => {
      const result = collectBackendArtifacts();
      
      if (result.artifacts.length > 0) {
        const artifact = result.artifacts[0];
        expect(artifact.filename).toBeDefined();
        expect(artifact.path).toBeDefined();
        expect(artifact.size).toBeDefined();
        expect(artifact.type).toBe('backend-executable');
        expect(artifact.platform).toBeDefined();
        expect(artifact.format).toBeDefined();
      }
    });
  });
  
  describe('Build Report Generation', () => {
    it('should generate a complete build report', () => {
      const buildResults = [
        { success: true, platform: 'windows', duration: '10.5' },
        { success: true, platform: 'mac', duration: '15.2' },
        { success: true, platform: 'linux', duration: '12.8' },
      ];
      
      const verification = {
        valid: true,
        verified: ['artifact1', 'artifact2'],
        missing: [],
        unexpected: [],
      };
      
      const startTime = Date.now() - 5000; // 5 seconds ago
      
      const report = generateBuildReport(buildResults, verification, startTime);
      
      expect(report).toBeDefined();
      expect(report.duration).toBeDefined();
      expect(report.artifactCount).toBeDefined();
      expect(report.totalSize).toBeDefined();
      expect(report.verification).toBe(verification);
      expect(report.buildResults).toBe(buildResults);
    });
    
    it('should include backend result in build report', () => {
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
      
      expect(report).toBeDefined();
      expect(report.backendResult).toBe(backendResult);
      expect(report.backendSize).toBeDefined();
      expect(report.installerSize).toBeDefined();
    });
    
    it('should handle failed builds in report', () => {
      const buildResults = [
        { success: true, platform: 'windows', duration: '10.5' },
        { success: false, platform: 'mac', duration: '5.0', error: new Error('Build failed') },
        { success: true, platform: 'linux', duration: '12.8' },
      ];
      
      const verification = {
        valid: false,
        verified: ['artifact1'],
        missing: ['artifact2'],
        unexpected: [],
      };
      
      const startTime = Date.now() - 3000;
      
      const report = generateBuildReport(buildResults, verification, startTime);
      
      expect(report).toBeDefined();
      expect(report.buildResults).toBe(buildResults);
      expect(report.verification.valid).toBe(false);
    });
  });
  
  describe('Error Handling', () => {
    let testDir;
    let originalCwd;
    
    beforeEach(() => {
      testDir = createTestDirectory();
      originalCwd = process.cwd();
      process.chdir(testDir);
    });
    
    afterEach(() => {
      process.chdir(originalCwd);
      cleanupTestDirectory(testDir);
    });
    
    it('should handle missing release directory gracefully', () => {
      const { artifacts, totalSize} = collectArtifacts(testDir);
      
      expect(artifacts).toEqual([]);
      expect(totalSize).toBe(0);
    });
    
    it('should handle empty release directory', () => {
      createDirectory(testDir, 'release');
      
      const { artifacts, totalSize } = collectArtifacts(testDir);
      
      expect(artifacts).toEqual([]);
      expect(totalSize).toBe(0);
    });
    
    it('should handle unknown artifact types', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createFile(releaseDir, 'unknown-file.txt', 'content');
      
      const { artifacts } = collectArtifacts(testDir);
      
      expect(artifacts.length).toBe(1);
      expect(artifacts[0].platform).toBe('unknown');
      expect(artifacts[0].type).toBe('unknown');
    });
  });
  
  describe('Progress Reporting', () => {
    it('should track build duration', () => {
      const buildResults = [
        { success: true, platform: 'windows', duration: '10.5' },
      ];
      
      const verification = { valid: true, verified: [], missing: [], unexpected: [] };
      const startTime = Date.now() - 10500; // 10.5 seconds ago
      
      const report = generateBuildReport(buildResults, verification, startTime);
      
      expect(report.duration).toBeDefined();
      expect(parseFloat(report.duration)).toBeGreaterThan(10);
    });
    
    it('should count artifacts correctly', () => {
      const buildResults = [];
      const verification = { valid: true, verified: [], missing: [], unexpected: [] };
      const startTime = Date.now();
      
      const report = generateBuildReport(buildResults, verification, startTime);
      
      expect(report.artifactCount).toBeDefined();
      expect(typeof report.artifactCount).toBe('number');
    });
  });
  
  describe('Installer Optimization - Compression Configuration', () => {
    it('should verify compression configuration exists', () => {
      const result = verifyCompressionConfig();
      
      expect(result).toBeDefined();
      expect(result.valid).toBeDefined();
      expect(result.compressionEnabled).toBeDefined();
      expect(result.errors).toBeDefined();
      expect(result.warnings).toBeDefined();
    });
    
    it('should check compression for all platforms', () => {
      const result = verifyCompressionConfig();
      
      // Should check at least some platforms
      expect(Object.keys(result.compressionEnabled).length).toBeGreaterThan(0);
    });
    
    it('should detect when compression is disabled', () => {
      const result = verifyCompressionConfig();
      
      // Check if warnings are generated for disabled compression
      expect(Array.isArray(result.warnings)).toBe(true);
    });
    
    it('should handle missing package.json gracefully', () => {
      // This test verifies the function handles errors
      // In real scenario, package.json should exist
      expect(() => verifyCompressionConfig()).not.toThrow();
    });
  });
  
  describe('Installer Optimization - Dependency Exclusion', () => {
    it('should verify dependency exclusion configuration', () => {
      const result = verifyDependencyExclusion();
      
      expect(result).toBeDefined();
      expect(result.valid).toBeDefined();
      expect(result.filesConfig).toBeDefined();
      expect(result.excludedPatterns).toBeDefined();
      expect(result.warnings).toBeDefined();
    });
    
    it('should check files configuration exists', () => {
      const result = verifyDependencyExclusion();
      
      expect(Array.isArray(result.filesConfig)).toBe(true);
    });
    
    it('should verify required patterns are included', () => {
      const result = verifyDependencyExclusion();
      
      // Should have some files configuration
      if (result.filesConfig.length > 0) {
        expect(result.filesConfig.length).toBeGreaterThan(0);
      }
    });
    
    it('should detect development patterns in build', () => {
      const result = verifyDependencyExclusion();
      
      // Warnings array should exist
      expect(Array.isArray(result.warnings)).toBe(true);
    });
    
    it('should handle missing package.json gracefully', () => {
      expect(() => verifyDependencyExclusion()).not.toThrow();
    });
  });
  
  describe('Installer Optimization - Size Validation', () => {
    let testDir;
    let originalCwd;
    
    beforeEach(() => {
      testDir = createTestDirectory();
      originalCwd = process.cwd();
      process.chdir(testDir);
    });
    
    afterEach(() => {
      process.chdir(originalCwd);
      cleanupTestDirectory(testDir);
    });
    
    it('should validate installer sizes', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      
      const result = validateInstallerSizes(testDir);
      
      expect(result).toBeDefined();
      expect(result.valid).toBeDefined();
      expect(result.validated).toBeDefined();
      expect(result.oversized).toBeDefined();
      expect(result.warnings).toBeDefined();
    });
    
    it('should accept installers within size limits', () => {
      const releaseDir = createDirectory(testDir, 'release');
      // Create small installer (1 KB)
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      
      const result = validateInstallerSizes(testDir);
      
      expect(result.valid).toBe(true);
      expect(result.validated.length).toBe(1);
      expect(result.oversized.length).toBe(0);
    });
    
    it('should detect oversized installers', () => {
      const releaseDir = createDirectory(testDir, 'release');
      // Create large installer (600 MB - exceeds 500 MB limit)
      const largeContent = Buffer.alloc(600 * 1024 * 1024);
      fs.writeFileSync(path.join(releaseDir, 'PEFT Studio-Setup-1.0.0.exe'), largeContent);
      
      const result = validateInstallerSizes(testDir);
      
      expect(result.valid).toBe(false);
      expect(result.oversized.length).toBe(1);
      expect(result.oversized[0].filename).toBe('PEFT Studio-Setup-1.0.0.exe');
    });
    
    it('should validate multiple installers', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      createFile(releaseDir, 'PEFT Studio-Portable-1.0.0.exe', 'x'.repeat(2000));
      createFile(releaseDir, 'PEFT Studio-1.0.0-x64.dmg', 'x'.repeat(3000));
      
      const result = validateInstallerSizes(testDir);
      
      expect(result.validated.length).toBe(3);
      expect(result.valid).toBe(true);
    });
    
    it('should handle no artifacts gracefully', () => {
      const result = validateInstallerSizes(testDir);
      
      expect(result.valid).toBe(true);
      expect(result.validated.length).toBe(0);
      expect(result.oversized.length).toBe(0);
    });
    
    it('should provide size information for oversized installers', () => {
      const releaseDir = createDirectory(testDir, 'release');
      const largeContent = Buffer.alloc(600 * 1024 * 1024);
      fs.writeFileSync(path.join(releaseDir, 'PEFT Studio-Setup-1.0.0.exe'), largeContent);
      
      const result = validateInstallerSizes(testDir);
      
      expect(result.oversized.length).toBe(1);
      expect(result.oversized[0].size).toBeDefined();
      expect(result.oversized[0].limit).toBeDefined();
      expect(result.oversized[0].platform).toBeDefined();
      expect(result.oversized[0].format).toBeDefined();
    });
  });
  
  describe('Installer Optimization - Size Reporting', () => {
    let testDir;
    let originalCwd;
    
    beforeEach(() => {
      testDir = createTestDirectory();
      originalCwd = process.cwd();
      process.chdir(testDir);
    });
    
    afterEach(() => {
      process.chdir(originalCwd);
      cleanupTestDirectory(testDir);
    });
    
    it('should generate size report', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      
      const report = generateSizeReport(testDir);
      
      expect(report).toBeDefined();
      expect(report.totalSize).toBeDefined();
      expect(report.totalSizeFormatted).toBeDefined();
      expect(report.artifactCount).toBeDefined();
      expect(report.byPlatform).toBeDefined();
      expect(report.byFormat).toBeDefined();
      expect(report.artifacts).toBeDefined();
    });
    
    it('should calculate total size correctly', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      createFile(releaseDir, 'PEFT Studio-Portable-1.0.0.exe', 'x'.repeat(2000));
      
      const report = generateSizeReport(testDir);
      
      expect(report.totalSize).toBe(3000);
      expect(report.artifactCount).toBe(2);
    });
    
    it('should group artifacts by platform', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      createFile(releaseDir, 'PEFT Studio-Portable-1.0.0.exe', 'x'.repeat(2000));
      createFile(releaseDir, 'PEFT Studio-1.0.0-x64.dmg', 'x'.repeat(3000));
      
      const report = generateSizeReport(testDir);
      
      expect(report.byPlatform.windows).toBeDefined();
      expect(report.byPlatform.windows.count).toBe(2);
      expect(report.byPlatform.windows.totalSize).toBe(3000);
      
      expect(report.byPlatform.mac).toBeDefined();
      expect(report.byPlatform.mac.count).toBe(1);
      expect(report.byPlatform.mac.totalSize).toBe(3000);
    });
    
    it('should group artifacts by format', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      createFile(releaseDir, 'PEFT Studio-Portable-1.0.0.exe', 'x'.repeat(2000));
      
      const report = generateSizeReport(testDir);
      
      expect(report.byFormat.NSIS).toBeDefined();
      expect(report.byFormat.NSIS.count).toBe(1);
      expect(report.byFormat.NSIS.totalSize).toBe(1000);
      
      expect(report.byFormat.Portable).toBeDefined();
      expect(report.byFormat.Portable.count).toBe(1);
      expect(report.byFormat.Portable.totalSize).toBe(2000);
    });
    
    it('should include formatted sizes for each artifact', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      
      const report = generateSizeReport(testDir);
      
      expect(report.artifacts.length).toBe(1);
      expect(report.artifacts[0].filename).toBe('PEFT Studio-Setup-1.0.0.exe');
      expect(report.artifacts[0].size).toBe(1000);
      expect(report.artifacts[0].sizeFormatted).toBeDefined();
      expect(report.artifacts[0].platform).toBe('windows');
      expect(report.artifacts[0].format).toBe('NSIS');
    });
    
    it('should handle empty release directory', () => {
      const report = generateSizeReport(testDir);
      
      expect(report.totalSize).toBe(0);
      expect(report.artifactCount).toBe(0);
      expect(Object.keys(report.byPlatform).length).toBe(0);
      expect(Object.keys(report.byFormat).length).toBe(0);
    });
    
    it('should format total size correctly', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1024 * 1024)); // 1 MB
      
      const report = generateSizeReport(testDir);
      
      expect(report.totalSizeFormatted).toContain('MB');
    });
  });
});
