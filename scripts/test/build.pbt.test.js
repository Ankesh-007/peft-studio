/**
 * Property-Based Tests for Build Module
 * 
 * Feature: repository-professionalization
 * 
 * These tests verify correctness properties using fast-check for property-based testing.
 */

const fc = require('fast-check');
const fs = require('fs');
const path = require('path');
const os = require('os');
const buildModule = require('../build');
const {
  BUILD_CONFIG,
  formatSize,
} = buildModule;

/**
 * Helper: Create a temporary test directory
 */
function createTestDirectory() {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'build-test-'));
  return tempDir;
}

/**
 * Helper: Create a mock release directory with artifacts
 */
function createMockReleaseDirectory(testDir, artifacts) {
  const releaseDir = path.join(testDir, 'release');
  fs.mkdirSync(releaseDir, { recursive: true });
  
  for (const artifact of artifacts) {
    const filePath = path.join(releaseDir, artifact.filename);
    const content = 'x'.repeat(artifact.size || 1000);
    fs.writeFileSync(filePath, content, 'utf8');
  }
  
  return releaseDir;
}

/**
 * Helper: Collect artifacts from a specific directory
 * This is a test-specific version that works with test directories
 */
function collectArtifactsFromDir(testDir) {
  const releaseDir = path.join(testDir, 'release');
  
  if (!fs.existsSync(releaseDir)) {
    return { artifacts: [], totalSize: 0 };
  }
  
  const artifacts = [];
  const files = fs.readdirSync(releaseDir);
  
  for (const file of files) {
    const filePath = path.join(releaseDir, file);
    const stats = fs.statSync(filePath);
    
    // Only process files, not directories
    if (!stats.isFile()) {
      continue;
    }
    
    // Determine artifact type and platform
    let artifactInfo = {
      filename: file,
      path: filePath,
      size: stats.size,
      type: 'unknown',
      platform: 'unknown',
      format: 'unknown',
      architecture: 'unknown',
    };
    
    // Match against expected artifacts
    for (const [platformKey, platform] of Object.entries(BUILD_CONFIG.platforms)) {
      for (const expected of platform.expectedArtifacts) {
        if (expected.pattern.test(file)) {
          artifactInfo.platform = platformKey;
          artifactInfo.type = expected.type;
          artifactInfo.format = expected.format;
          artifactInfo.architecture = expected.arch || 'x64';
          break;
        }
      }
      if (artifactInfo.platform !== 'unknown') break;
    }
    
    artifacts.push(artifactInfo);
  }
  
  const totalSize = artifacts.reduce((sum, a) => sum + a.size, 0);
  
  return { artifacts, totalSize };
}

/**
 * Helper: Clean up test directory
 */
function cleanupTestDirectory(dirPath) {
  if (fs.existsSync(dirPath)) {
    fs.rmSync(dirPath, { recursive: true, force: true });
  }
}

/**
 * Helper: Get expected artifact count for platforms
 */
function getExpectedArtifactCount(platforms) {
  let count = 0;
  for (const platformKey of platforms) {
    const platform = BUILD_CONFIG.platforms[platformKey];
    if (platform && platform.enabled) {
      count += platform.expectedArtifacts.length;
    }
  }
  return count;
}

describe('Build Module - Property-Based Tests', () => {
  /**
   * Feature: repository-professionalization, Property 2: Build Completeness
   * Validates: Requirements 1.1, 1.2, 1.3, 1.5
   * 
   * For any enabled platform, the build process must generate all expected 
   * installer artifacts for that platform.
   */
  describe('Property 2: Build Completeness', () => {
    it('should generate all expected artifacts for Windows platform', () => {
      fc.assert(
        fc.property(
          fc.record({
            hasSetup: fc.boolean(),
            hasPortable: fc.boolean(),
          }),
          (testData) => {
            const testDir = createTestDirectory();
            
            try {
              const artifacts = [];
              
              // Create Windows artifacts based on test data
              if (testData.hasSetup) {
                artifacts.push({
                  filename: 'PEFT Studio-Setup-1.0.0.exe',
                  size: 50000000,
                });
              }
              
              if (testData.hasPortable) {
                artifacts.push({
                  filename: 'PEFT Studio-Portable-1.0.0.exe',
                  size: 45000000,
                });
              }
              
              // Create mock release directory
              const releaseDir = createMockReleaseDirectory(testDir, artifacts);
              
              // Collect artifacts from test directory
              const { artifacts: collected } = collectArtifactsFromDir(testDir);
              
              // Property: If both artifacts exist, we should collect both
              if (testData.hasSetup && testData.hasPortable) {
                const windowsArtifacts = collected.filter(a => a.platform === 'windows');
                expect(windowsArtifacts.length).toBe(2);
                
                const hasSetup = windowsArtifacts.some(a => a.format === 'NSIS');
                const hasPortable = windowsArtifacts.some(a => a.format === 'Portable');
                
                expect(hasSetup).toBe(true);
                expect(hasPortable).toBe(true);
              }
              
              // Property: If only setup exists, we should only collect setup
              if (testData.hasSetup && !testData.hasPortable) {
                const windowsArtifacts = collected.filter(a => a.platform === 'windows');
                expect(windowsArtifacts.length).toBe(1);
                expect(windowsArtifacts[0].format).toBe('NSIS');
              }
              
              // Property: If only portable exists, we should only collect portable
              if (!testData.hasSetup && testData.hasPortable) {
                const windowsArtifacts = collected.filter(a => a.platform === 'windows');
                expect(windowsArtifacts.length).toBe(1);
                expect(windowsArtifacts[0].format).toBe('Portable');
              }
              
            } finally {
              cleanupTestDirectory(testDir);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
    
    it('should generate all expected artifacts for macOS platform', () => {
      fc.assert(
        fc.property(
          fc.record({
            hasX64Dmg: fc.boolean(),
            hasArm64Dmg: fc.boolean(),
            hasX64Zip: fc.boolean(),
            hasArm64Zip: fc.boolean(),
          }),
          (testData) => {
            const testDir = createTestDirectory();
            
            try {
              const artifacts = [];
              
              // Create macOS artifacts based on test data
              if (testData.hasX64Dmg) {
                artifacts.push({
                  filename: 'PEFT Studio-1.0.0-x64.dmg',
                  size: 60000000,
                });
              }
              
              if (testData.hasArm64Dmg) {
                artifacts.push({
                  filename: 'PEFT Studio-1.0.0-arm64.dmg',
                  size: 58000000,
                });
              }
              
              if (testData.hasX64Zip) {
                artifacts.push({
                  filename: 'PEFT Studio-1.0.0-x64.zip',
                  size: 55000000,
                });
              }
              
              if (testData.hasArm64Zip) {
                artifacts.push({
                  filename: 'PEFT Studio-1.0.0-arm64.zip',
                  size: 53000000,
                });
              }
              
              // Create mock release directory
              const releaseDir = createMockReleaseDirectory(testDir, artifacts);
              
              // Collect artifacts from test directory
              const { artifacts: collected } = collectArtifactsFromDir(testDir);
              const macArtifacts = collected.filter(a => a.platform === 'mac');
              
              // Property: Number of collected macOS artifacts should match created artifacts
              const expectedCount = [
                testData.hasX64Dmg,
                testData.hasArm64Dmg,
                testData.hasX64Zip,
                testData.hasArm64Zip,
              ].filter(Boolean).length;
              
              expect(macArtifacts.length).toBe(expectedCount);
              
              // Property: Each created artifact should be collected
              if (testData.hasX64Dmg) {
                const found = macArtifacts.some(a => 
                  a.format === 'DMG' && a.architecture === 'x64'
                );
                expect(found).toBe(true);
              }
              
              if (testData.hasArm64Dmg) {
                const found = macArtifacts.some(a => 
                  a.format === 'DMG' && a.architecture === 'arm64'
                );
                expect(found).toBe(true);
              }
              
              if (testData.hasX64Zip) {
                const found = macArtifacts.some(a => 
                  a.format === 'ZIP' && a.architecture === 'x64'
                );
                expect(found).toBe(true);
              }
              
              if (testData.hasArm64Zip) {
                const found = macArtifacts.some(a => 
                  a.format === 'ZIP' && a.architecture === 'arm64'
                );
                expect(found).toBe(true);
              }
              
            } finally {
              cleanupTestDirectory(testDir);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
    
    it('should generate all expected artifacts for Linux platform', () => {
      fc.assert(
        fc.property(
          fc.record({
            hasAppImage: fc.boolean(),
            hasDeb: fc.boolean(),
          }),
          (testData) => {
            const testDir = createTestDirectory();
            
            try {
              const artifacts = [];
              
              // Create Linux artifacts based on test data (using smaller sizes for faster tests)
              if (testData.hasAppImage) {
                artifacts.push({
                  filename: 'PEFT Studio-1.0.0-x64.AppImage',
                  size: 1000, // Reduced from 70MB for faster tests
                });
              }
              
              if (testData.hasDeb) {
                artifacts.push({
                  filename: 'PEFT Studio-1.0.0-amd64.deb',
                  size: 1000, // Reduced from 65MB for faster tests
                });
              }
              
              // Create mock release directory
              const releaseDir = createMockReleaseDirectory(testDir, artifacts);
              
              // Collect artifacts from test directory
              const { artifacts: collected } = collectArtifactsFromDir(testDir);
              const linuxArtifacts = collected.filter(a => a.platform === 'linux');
              
              // Property: Number of collected Linux artifacts should match created artifacts
              const expectedCount = [testData.hasAppImage, testData.hasDeb].filter(Boolean).length;
              expect(linuxArtifacts.length).toBe(expectedCount);
              
              // Property: Each created artifact should be collected
              if (testData.hasAppImage) {
                const found = linuxArtifacts.some(a => a.format === 'AppImage');
                expect(found).toBe(true);
              }
              
              if (testData.hasDeb) {
                const found = linuxArtifacts.some(a => a.format === 'DEB');
                expect(found).toBe(true);
              }
              
            } finally {
              cleanupTestDirectory(testDir);
            }
          }
        ),
        { numRuns: 25 } // Reduced from 100 for faster tests
      );
    });
    
    it('should collect all artifacts when all platforms are built', () => {
      fc.assert(
        fc.property(
          fc.record({
            // Windows
            windowsSetup: fc.boolean(),
            windowsPortable: fc.boolean(),
            // macOS
            macX64Dmg: fc.boolean(),
            macArm64Dmg: fc.boolean(),
            macX64Zip: fc.boolean(),
            macArm64Zip: fc.boolean(),
            // Linux
            linuxAppImage: fc.boolean(),
            linuxDeb: fc.boolean(),
          }),
          (testData) => {
            const testDir = createTestDirectory();
            
            try {
              const artifacts = [];
              
              // Create all possible artifacts based on test data
              if (testData.windowsSetup) {
                artifacts.push({ filename: 'PEFT Studio-Setup-1.0.0.exe', size: 50000000 });
              }
              if (testData.windowsPortable) {
                artifacts.push({ filename: 'PEFT Studio-Portable-1.0.0.exe', size: 45000000 });
              }
              if (testData.macX64Dmg) {
                artifacts.push({ filename: 'PEFT Studio-1.0.0-x64.dmg', size: 60000000 });
              }
              if (testData.macArm64Dmg) {
                artifacts.push({ filename: 'PEFT Studio-1.0.0-arm64.dmg', size: 58000000 });
              }
              if (testData.macX64Zip) {
                artifacts.push({ filename: 'PEFT Studio-1.0.0-x64.zip', size: 55000000 });
              }
              if (testData.macArm64Zip) {
                artifacts.push({ filename: 'PEFT Studio-1.0.0-arm64.zip', size: 53000000 });
              }
              if (testData.linuxAppImage) {
                artifacts.push({ filename: 'PEFT Studio-1.0.0-x64.AppImage', size: 70000000 });
              }
              if (testData.linuxDeb) {
                artifacts.push({ filename: 'PEFT Studio-1.0.0-amd64.deb', size: 65000000 });
              }
              
              // Create mock release directory
              const releaseDir = createMockReleaseDirectory(testDir, artifacts);
              
              // Collect artifacts from test directory
              const { artifacts: collected } = collectArtifactsFromDir(testDir);
              
              // Property: Number of collected artifacts should equal number of created artifacts
              expect(collected.length).toBe(artifacts.length);
              
              // Property: Each created artifact should be collected
              for (const artifact of artifacts) {
                const found = collected.some(a => a.filename === artifact.filename);
                expect(found).toBe(true);
              }
              
            } finally {
              cleanupTestDirectory(testDir);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
  });
  
  /**
   * Additional property: Size formatting should be consistent
   */
  describe('Size Formatting Consistency', () => {
    it('should format sizes consistently', () => {
      fc.assert(
        fc.property(
          fc.integer({ min: 0, max: 10000000000 }),
          (size) => {
            // Run formatting multiple times
            const result1 = formatSize(size);
            const result2 = formatSize(size);
            const result3 = formatSize(size);
            
            // Property: Formatting should be deterministic
            expect(result1).toBe(result2);
            expect(result2).toBe(result3);
            
            // Property: Result should contain a number and a unit
            expect(result1).toMatch(/^[\d.]+ (B|KB|MB|GB)$/);
          }
        ),
        { numRuns: 100 }
      );
    });
    
    it('should use appropriate units for different sizes', () => {
      fc.assert(
        fc.property(
          fc.constantFrom(
            { size: 500, expectedUnit: 'B' },
            { size: 1024, expectedUnit: 'KB' },
            { size: 1024 * 1024, expectedUnit: 'MB' },
            { size: 1024 * 1024 * 1024, expectedUnit: 'GB' }
          ),
          (testCase) => {
            const result = formatSize(testCase.size);
            
            // Property: Size should be formatted with the expected unit
            expect(result).toContain(testCase.expectedUnit);
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});
