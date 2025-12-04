/**
 * Property-Based Tests for GitHub Release Manager
 * 
 * Feature: repository-professionalization
 * 
 * These tests verify correctness properties using fast-check for property-based testing.
 */

const fc = require('fast-check');
const fs = require('fs');
const path = require('path');
const os = require('os');
const {
  verifyUploadedAssets,
  collectReleaseArtifacts,
} = require('../release-to-github');

/**
 * Helper: Create a temporary test directory
 */
function createTestDirectory() {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'release-pbt-test-'));
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
 * Helper: Clean up test directory
 */
function cleanupTestDirectory(dirPath) {
  if (fs.existsSync(dirPath)) {
    fs.rmSync(dirPath, { recursive: true, force: true });
  }
}

/**
 * Arbitrary: Generate a valid installer filename
 */
const installerFilenameArb = fc.oneof(
  fc.constant('PEFT Studio-Setup-1.0.0.exe'),
  fc.constant('PEFT Studio-Portable-1.0.0.exe'),
  fc.constant('PEFT Studio-1.0.0-x64.dmg'),
  fc.constant('PEFT Studio-1.0.0-arm64.dmg'),
  fc.constant('PEFT Studio-1.0.0-x64.zip'),
  fc.constant('PEFT Studio-1.0.0-arm64.zip'),
  fc.constant('PEFT Studio-1.0.0-x64.AppImage'),
  fc.constant('PEFT Studio-1.0.0-amd64.deb'),
  fc.constant('SHA256SUMS.txt')
);

/**
 * Arbitrary: Generate a set of installer filenames
 */
const installerSetArb = fc.uniqueArray(installerFilenameArb, { minLength: 0, maxLength: 9 });

describe('GitHub Release Manager - Property-Based Tests', () => {
  /**
   * Feature: repository-professionalization, Property 6: Release Asset Completeness
   * Validates: Requirements 3.3, 3.4
   * 
   * For any GitHub release, the number of uploaded assets must equal the number 
   * of built artifacts plus one (for checksums file).
   */
  describe('Property 6: Release Asset Completeness', () => {
    it('should verify that all expected files are uploaded', () => {
      fc.assert(
        fc.property(
          installerSetArb,
          (expectedFiles) => {
            // Create a mock release with all expected files uploaded
            const release = {
              assets: expectedFiles.map(name => ({ name })),
            };
            
            // Verify assets
            const verification = verifyUploadedAssets(release, expectedFiles);
            
            // Property: If all expected files are uploaded, verification should be valid
            expect(verification.valid).toBe(true);
            expect(verification.missing).toEqual([]);
            expect(verification.uploaded.length).toBe(expectedFiles.length);
          }
        ),
        { numRuns: 100 }
      );
    });
    
    it('should detect when assets are missing', () => {
      fc.assert(
        fc.property(
          installerSetArb,
          fc.integer({ min: 0, max: 100 }).filter(n => n < 100), // Percentage to upload
          (expectedFiles, uploadPercentage) => {
            // Skip if no files
            if (expectedFiles.length === 0) {
              return;
            }
            
            // Upload only a percentage of files
            const numToUpload = Math.floor(expectedFiles.length * uploadPercentage / 100);
            const uploadedFiles = expectedFiles.slice(0, numToUpload);
            
            const release = {
              assets: uploadedFiles.map(name => ({ name })),
            };
            
            // Verify assets
            const verification = verifyUploadedAssets(release, expectedFiles);
            
            // Property: If not all files uploaded, verification should be invalid
            if (uploadedFiles.length < expectedFiles.length) {
              expect(verification.valid).toBe(false);
              expect(verification.missing.length).toBe(expectedFiles.length - uploadedFiles.length);
            } else {
              expect(verification.valid).toBe(true);
              expect(verification.missing.length).toBe(0);
            }
            
            // Property: Uploaded count should match actual uploads
            expect(verification.uploaded.length).toBe(uploadedFiles.length);
          }
        ),
        { numRuns: 100 }
      );
    });
    
    it('should correctly identify missing files', () => {
      fc.assert(
        fc.property(
          installerSetArb,
          installerSetArb,
          (expectedFiles, uploadedFiles) => {
            const release = {
              assets: uploadedFiles.map(name => ({ name })),
            };
            
            // Verify assets
            const verification = verifyUploadedAssets(release, expectedFiles);
            
            // Property: Missing files should be exactly those in expected but not in uploaded
            const actualMissing = expectedFiles.filter(file => !uploadedFiles.includes(file));
            expect(verification.missing.sort()).toEqual(actualMissing.sort());
            
            // Property: Valid only if no missing files
            expect(verification.valid).toBe(actualMissing.length === 0);
          }
        ),
        { numRuns: 100 }
      );
    });
    
    it('should handle the case where checksums file is included', () => {
      fc.assert(
        fc.property(
          installerSetArb.filter(files => files.length > 0),
          (installerFiles) => {
            // Ensure SHA256SUMS.txt is in the list
            const filesWithChecksums = installerFiles.includes('SHA256SUMS.txt')
              ? installerFiles
              : [...installerFiles, 'SHA256SUMS.txt'];
            
            const release = {
              assets: filesWithChecksums.map(name => ({ name })),
            };
            
            // Verify assets
            const verification = verifyUploadedAssets(release, filesWithChecksums);
            
            // Property: All files including checksums should be verified
            expect(verification.valid).toBe(true);
            expect(verification.uploaded).toContain('SHA256SUMS.txt');
            expect(verification.missing).toEqual([]);
          }
        ),
        { numRuns: 100 }
      );
    });
    
    it('should verify artifact collection matches expected count', () => {
      fc.assert(
        fc.property(
          fc.uniqueArray(
            fc.record({
              filename: installerFilenameArb,
              size: fc.integer({ min: 100, max: 10000 }), // Reduced max from 100MB to 10KB for faster tests
            }),
            { minLength: 0, maxLength: 9, selector: item => item.filename }
          ),
          (artifacts) => {
            const testDir = createTestDirectory();
            
            try {
              const releaseDir = path.join(testDir, 'release');
              fs.mkdirSync(releaseDir, { recursive: true });
              
              // Create artifact files
              for (const artifact of artifacts) {
                createFile(releaseDir, artifact.filename, 'x'.repeat(artifact.size));
              }
              
              // Collect artifacts
              const collected = collectReleaseArtifacts(releaseDir);
              
              // Property: Number of collected artifacts should equal number created
              expect(collected.length).toBe(artifacts.length);
              
              // Property: Each created artifact should be collected
              for (const artifact of artifacts) {
                const found = collected.some(c => c.filename === artifact.filename);
                expect(found).toBe(true);
              }
              
              // Property: If we verify these artifacts, all should be present
              const release = {
                assets: collected.map(a => ({ name: a.filename })),
              };
              
              const expectedFiles = artifacts.map(a => a.filename);
              const verification = verifyUploadedAssets(release, expectedFiles);
              
              expect(verification.valid).toBe(true);
              expect(verification.missing).toEqual([]);
              
            } finally {
              cleanupTestDirectory(testDir);
            }
          }
        ),
        { numRuns: 25 } // Reduced from 100 for faster tests
      );
    });
    
    it('should maintain asset count consistency through collection and verification', () => {
      fc.assert(
        fc.property(
          fc.uniqueArray(
            fc.record({
              filename: installerFilenameArb,
              size: fc.integer({ min: 1000, max: 10000000 }),
            }),
            { minLength: 1, maxLength: 9, selector: item => item.filename }
          ),
          (artifacts) => {
            const testDir = createTestDirectory();
            
            try {
              const releaseDir = path.join(testDir, 'release');
              fs.mkdirSync(releaseDir, { recursive: true });
              
              // Create artifact files
              for (const artifact of artifacts) {
                createFile(releaseDir, artifact.filename, 'x'.repeat(artifact.size));
              }
              
              // Collect artifacts
              const collected = collectReleaseArtifacts(releaseDir);
              
              // Create a mock release with all collected artifacts
              const release = {
                assets: collected.map(a => ({ name: a.filename })),
              };
              
              // Verify with the collected filenames
              const verification = verifyUploadedAssets(
                release,
                collected.map(a => a.filename)
              );
              
              // Property: Verification should always be valid when all collected artifacts are uploaded
              expect(verification.valid).toBe(true);
              expect(verification.missing).toEqual([]);
              
              // Property: Number of uploaded assets should equal number of collected artifacts
              expect(verification.uploaded.length).toBe(collected.length);
              expect(verification.uploaded.length).toBe(artifacts.length);
              
            } finally {
              cleanupTestDirectory(testDir);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
    
    it('should handle partial uploads correctly', () => {
      fc.assert(
        fc.property(
          fc.uniqueArray(
            fc.record({
              filename: installerFilenameArb,
              size: fc.integer({ min: 1000, max: 10000000 }),
            }),
            { minLength: 2, maxLength: 9, selector: item => item.filename }
          ),
          fc.integer({ min: 1, max: 100 }),
          (artifacts, uploadPercentage) => {
            const testDir = createTestDirectory();
            
            try {
              const releaseDir = path.join(testDir, 'release');
              fs.mkdirSync(releaseDir, { recursive: true });
              
              // Create artifact files
              for (const artifact of artifacts) {
                createFile(releaseDir, artifact.filename, 'x'.repeat(artifact.size));
              }
              
              // Collect artifacts
              const collected = collectReleaseArtifacts(releaseDir);
              
              // Upload only a percentage
              const numToUpload = Math.max(1, Math.floor(collected.length * uploadPercentage / 100));
              const uploaded = collected.slice(0, numToUpload);
              
              // Create a mock release with partial uploads
              const release = {
                assets: uploaded.map(a => ({ name: a.filename })),
              };
              
              // Verify with all collected filenames
              const verification = verifyUploadedAssets(
                release,
                collected.map(a => a.filename)
              );
              
              // Property: If not all uploaded, verification should be invalid
              if (uploaded.length < collected.length) {
                expect(verification.valid).toBe(false);
                expect(verification.missing.length).toBe(collected.length - uploaded.length);
              } else {
                expect(verification.valid).toBe(true);
                expect(verification.missing.length).toBe(0);
              }
              
              // Property: Uploaded count should match actual uploads
              expect(verification.uploaded.length).toBe(uploaded.length);
              
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
   * Additional property: Asset verification is deterministic
   */
  describe('Asset Verification Determinism', () => {
    it('should produce consistent results for the same inputs', () => {
      fc.assert(
        fc.property(
          installerSetArb,
          installerSetArb,
          (expectedFiles, uploadedFiles) => {
            const release = {
              assets: uploadedFiles.map(name => ({ name })),
            };
            
            // Run verification multiple times
            const result1 = verifyUploadedAssets(release, expectedFiles);
            const result2 = verifyUploadedAssets(release, expectedFiles);
            const result3 = verifyUploadedAssets(release, expectedFiles);
            
            // Property: Results should be identical
            expect(result1.valid).toBe(result2.valid);
            expect(result2.valid).toBe(result3.valid);
            
            expect(result1.uploaded.sort()).toEqual(result2.uploaded.sort());
            expect(result2.uploaded.sort()).toEqual(result3.uploaded.sort());
            
            expect(result1.missing.sort()).toEqual(result2.missing.sort());
            expect(result2.missing.sort()).toEqual(result3.missing.sort());
          }
        ),
        { numRuns: 100 }
      );
    });
  });
  
  /**
   * Additional property: Artifact collection is consistent
   */
  describe('Artifact Collection Consistency', () => {
    it('should collect the same artifacts on repeated calls', () => {
      fc.assert(
        fc.property(
          fc.uniqueArray(
            fc.record({
              filename: installerFilenameArb,
              size: fc.integer({ min: 1000, max: 10000000 }),
            }),
            { minLength: 0, maxLength: 9, selector: item => item.filename }
          ),
          (artifacts) => {
            const testDir = createTestDirectory();
            
            try {
              const releaseDir = path.join(testDir, 'release');
              fs.mkdirSync(releaseDir, { recursive: true });
              
              // Create artifact files
              for (const artifact of artifacts) {
                createFile(releaseDir, artifact.filename, 'x'.repeat(artifact.size));
              }
              
              // Collect artifacts multiple times
              const collected1 = collectReleaseArtifacts(releaseDir);
              const collected2 = collectReleaseArtifacts(releaseDir);
              const collected3 = collectReleaseArtifacts(releaseDir);
              
              // Property: Collections should be identical
              expect(collected1.length).toBe(collected2.length);
              expect(collected2.length).toBe(collected3.length);
              
              const filenames1 = collected1.map(a => a.filename).sort();
              const filenames2 = collected2.map(a => a.filename).sort();
              const filenames3 = collected3.map(a => a.filename).sort();
              
              expect(filenames1).toEqual(filenames2);
              expect(filenames2).toEqual(filenames3);
              
            } finally {
              cleanupTestDirectory(testDir);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});
