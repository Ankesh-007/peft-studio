/**
 * Property-Based Tests for Checksum Module
 * 
 * Feature: repository-professionalization
 * 
 * These tests verify correctness properties using fast-check for property-based testing.
 */

const fc = require('fast-check');
const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const {
  calculateChecksum,
  shouldIncludeFile,
  generateChecksums,
  writeChecksumsFile,
} = require('../generate-checksums');

/**
 * Helper: Create a temporary test directory
 */
function createTestDirectory() {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'checksum-test-'));
  return tempDir;
}

/**
 * Helper: Create a file with specific content
 */
function createFile(dirPath, filename, content) {
  const filePath = path.join(dirPath, filename);
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
 * Helper: Calculate checksum directly for verification
 */
function calculateChecksumSync(filePath) {
  const content = fs.readFileSync(filePath);
  return crypto.createHash('sha256').update(content).digest('hex');
}

describe('Checksum Module - Property-Based Tests', () => {
  /**
   * Feature: repository-professionalization, Property 3: Checksum Consistency
   * Validates: Requirements 2.1, 2.5
   * 
   * For any artifact, recalculating its checksum must produce the same hash 
   * as recorded in SHA256SUMS.txt.
   */
  describe('Property 3: Checksum Consistency', () => {
    it('should produce consistent checksums for the same file content', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.string({ minLength: 0, maxLength: 10000 }),
          async (content) => {
            const testDir = createTestDirectory();
            
            try {
              // Create a file with the generated content
              const filename = 'test-file.exe';
              const filePath = createFile(testDir, filename, content);
              
              // Calculate checksum multiple times
              const checksum1 = await calculateChecksum(filePath);
              const checksum2 = await calculateChecksum(filePath);
              const checksum3 = await calculateChecksum(filePath);
              
              // Property: All checksums should be identical
              expect(checksum1).toBe(checksum2);
              expect(checksum2).toBe(checksum3);
              
              // Property: Checksum should match direct calculation
              const expectedChecksum = calculateChecksumSync(filePath);
              expect(checksum1).toBe(expectedChecksum);
              
            } finally {
              cleanupTestDirectory(testDir);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
    
    it('should produce consistent checksums after writing and reading from file', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.array(
            fc.record({
              filename: fc.constantFrom(
                'app-Setup-1.0.0.exe',
                'app-Portable-1.0.0.exe',
                'app-1.0.0-x64.dmg',
                'app-1.0.0-arm64.dmg',
                'app-1.0.0-x64.zip',
                'app-1.0.0-x64.AppImage',
                'app-1.0.0-amd64.deb'
              ),
              content: fc.string({ minLength: 100, maxLength: 1000 }),
            }),
            { minLength: 1, maxLength: 5 }
          ),
          async (files) => {
            const testDir = createTestDirectory();
            
            try {
              // Create files and generate checksums
              const createdFiles = [];
              for (const file of files) {
                const filePath = createFile(testDir, file.filename, file.content);
                createdFiles.push(filePath);
              }
              
              // Generate checksums
              const checksums = await generateChecksums(testDir);
              
              // Write checksums to file
              const checksumsFilePath = path.join(testDir, 'SHA256SUMS.txt');
              writeChecksumsFile(checksums, checksumsFilePath);
              
              // Read checksums file
              const checksumsContent = fs.readFileSync(checksumsFilePath, 'utf8');
              const lines = checksumsContent.trim().split('\n');
              
              // Property: Each file should have a checksum entry
              expect(lines.length).toBe(checksums.length);
              
              // Property: Recalculating checksums should match recorded values
              for (const { file, checksum } of checksums) {
                const filePath = path.join(testDir, file);
                const recalculatedChecksum = await calculateChecksum(filePath);
                
                // Checksum should be consistent
                expect(recalculatedChecksum).toBe(checksum);
                
                // Checksum should be in the file
                const checksumLine = `${checksum}  ${file}`;
                expect(checksumsContent).toContain(checksumLine);
              }
              
            } finally {
              cleanupTestDirectory(testDir);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
    
    it('should produce the same checksum regardless of how file is read', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.uint8Array({ minLength: 0, maxLength: 5000 }),
          async (binaryContent) => {
            const testDir = createTestDirectory();
            
            try {
              // Create a file with binary content
              const filename = 'binary-file.exe';
              const filePath = path.join(testDir, filename);
              fs.writeFileSync(filePath, Buffer.from(binaryContent));
              
              // Calculate checksum using the module function
              const moduleChecksum = await calculateChecksum(filePath);
              
              // Calculate checksum using direct sync method
              const directChecksum = calculateChecksumSync(filePath);
              
              // Property: Both methods should produce the same checksum
              expect(moduleChecksum).toBe(directChecksum);
              
              // Property: Checksum should be a valid SHA-256 hash (64 hex characters)
              expect(moduleChecksum).toMatch(/^[a-f0-9]{64}$/);
              
            } finally {
              cleanupTestDirectory(testDir);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
    
    it('should maintain checksum consistency across file modifications', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.string({ minLength: 100, maxLength: 1000 }),
          fc.string({ minLength: 100, maxLength: 1000 }),
          async (content1, content2) => {
            const testDir = createTestDirectory();
            
            try {
              const filename = 'mutable-file.exe';
              const filePath = path.join(testDir, filename);
              
              // Write first content and calculate checksum
              fs.writeFileSync(filePath, content1, 'utf8');
              const checksum1 = await calculateChecksum(filePath);
              
              // Write second content and calculate checksum
              fs.writeFileSync(filePath, content2, 'utf8');
              const checksum2 = await calculateChecksum(filePath);
              
              // Property: If content is the same, checksums should match
              if (content1 === content2) {
                expect(checksum1).toBe(checksum2);
              }
              
              // Property: If content is different, checksums should differ
              if (content1 !== content2) {
                expect(checksum1).not.toBe(checksum2);
              }
              
              // Property: Recalculating after second write should match checksum2
              const checksum2Verify = await calculateChecksum(filePath);
              expect(checksum2Verify).toBe(checksum2);
              
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
   * Feature: repository-professionalization, Property 4: Checksum File Format
   * Validates: Requirements 2.3
   * 
   * For any line in SHA256SUMS.txt, it must match the format 
   * ^[a-f0-9]{64}  .+ (64-character hex hash, two spaces, filename).
   */
  describe('Property 4: Checksum File Format', () => {
    it('should format each line with hash, two spaces, and filename', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.array(
            fc.record({
              filename: fc.constantFrom(
                'app-Setup-1.0.0.exe',
                'app-Portable-1.0.0.exe',
                'app-1.0.0-x64.dmg',
                'app-1.0.0-arm64.dmg',
                'app-1.0.0-x64.zip',
                'app-1.0.0-x64.AppImage',
                'app-1.0.0-amd64.deb'
              ),
              content: fc.string({ minLength: 100, maxLength: 1000 }),
            }),
            { minLength: 1, maxLength: 7 }
          ),
          async (files) => {
            const testDir = createTestDirectory();
            
            try {
              // Create files
              for (const file of files) {
                createFile(testDir, file.filename, file.content);
              }
              
              // Generate checksums
              const checksums = await generateChecksums(testDir);
              
              // Write checksums to file
              const checksumsFilePath = path.join(testDir, 'SHA256SUMS.txt');
              writeChecksumsFile(checksums, checksumsFilePath);
              
              // Read checksums file
              const checksumsContent = fs.readFileSync(checksumsFilePath, 'utf8');
              const lines = checksumsContent.trim().split('\n');
              
              // Property: Each line must match the format
              const formatRegex = /^[a-f0-9]{64}  .+$/;
              
              for (const line of lines) {
                expect(line).toMatch(formatRegex);
                
                // Property: Hash should be exactly 64 hex characters
                const hash = line.substring(0, 64);
                expect(hash).toMatch(/^[a-f0-9]{64}$/);
                
                // Property: There should be exactly two spaces after the hash
                expect(line.substring(64, 66)).toBe('  ');
                
                // Property: Filename should start at position 66
                const filename = line.substring(66);
                expect(filename.length).toBeGreaterThan(0);
              }
              
            } finally {
              cleanupTestDirectory(testDir);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
    
    it('should maintain format consistency across different file types', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.string({ minLength: 100, maxLength: 1000 }),
          async (content) => {
            const testDir = createTestDirectory();
            
            try {
              // Create files of different types
              const files = [
                { filename: 'test-Setup-1.0.0.exe', content },
                { filename: 'test-1.0.0-x64.dmg', content },
                { filename: 'test-1.0.0-x64.AppImage', content },
              ];
              
              for (const file of files) {
                createFile(testDir, file.filename, file.content);
              }
              
              // Generate checksums
              const checksums = await generateChecksums(testDir);
              
              // Write checksums to file
              const checksumsFilePath = path.join(testDir, 'SHA256SUMS.txt');
              writeChecksumsFile(checksums, checksumsFilePath);
              
              // Read checksums file
              const checksumsContent = fs.readFileSync(checksumsFilePath, 'utf8');
              const lines = checksumsContent.trim().split('\n');
              
              // Property: All lines should have the same format structure
              const formatRegex = /^[a-f0-9]{64}  .+$/;
              
              for (const line of lines) {
                expect(line).toMatch(formatRegex);
              }
              
              // Property: Each line should have hash at position 0-63, 
              // two spaces at 64-65, and filename starting at 66
              for (const line of lines) {
                const parts = line.split('  ');
                expect(parts.length).toBe(2);
                expect(parts[0].length).toBe(64);
                expect(parts[1].length).toBeGreaterThan(0);
              }
              
            } finally {
              cleanupTestDirectory(testDir);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
    
    it('should handle filenames with special characters correctly', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.string({ minLength: 100, maxLength: 500 }),
          async (content) => {
            const testDir = createTestDirectory();
            
            try {
              // Create files with various naming patterns
              const files = [
                { filename: 'PEFT Studio-Setup-1.0.0.exe', content },
                { filename: 'PEFT Studio-Portable-1.0.0.exe', content },
                { filename: 'PEFT Studio-1.0.0-x64.dmg', content },
              ];
              
              for (const file of files) {
                createFile(testDir, file.filename, file.content);
              }
              
              // Generate checksums
              const checksums = await generateChecksums(testDir);
              
              // Write checksums to file
              const checksumsFilePath = path.join(testDir, 'SHA256SUMS.txt');
              writeChecksumsFile(checksums, checksumsFilePath);
              
              // Read checksums file
              const checksumsContent = fs.readFileSync(checksumsFilePath, 'utf8');
              const lines = checksumsContent.trim().split('\n');
              
              // Property: Format should be maintained even with spaces in filenames
              for (const line of lines) {
                // Should match format: hash + two spaces + filename
                expect(line).toMatch(/^[a-f0-9]{64}  .+$/);
                
                // Extract hash and filename
                const hash = line.substring(0, 64);
                const separator = line.substring(64, 66);
                const filename = line.substring(66);
                
                // Verify format components
                expect(hash).toMatch(/^[a-f0-9]{64}$/);
                expect(separator).toBe('  ');
                expect(filename).toContain('PEFT Studio');
              }
              
            } finally {
              cleanupTestDirectory(testDir);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
    
    it('should produce valid format for any number of files', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.integer({ min: 1, max: 8 }),
          fc.string({ minLength: 50, maxLength: 500 }),
          async (fileCount, content) => {
            const testDir = createTestDirectory();
            
            try {
              // Create variable number of files
              const fileTypes = [
                'app-Setup-1.0.0.exe',
                'app-Portable-1.0.0.exe',
                'app-1.0.0-x64.dmg',
                'app-1.0.0-arm64.dmg',
                'app-1.0.0-x64.zip',
                'app-1.0.0-arm64.zip',
                'app-1.0.0-x64.AppImage',
                'app-1.0.0-amd64.deb',
              ];
              
              // Create exactly fileCount files
              const filesToCreate = fileTypes.slice(0, fileCount);
              
              for (let i = 0; i < filesToCreate.length; i++) {
                createFile(testDir, filesToCreate[i], content + i);
              }
              
              // Generate checksums
              const checksums = await generateChecksums(testDir);
              
              // Write checksums to file
              const checksumsFilePath = path.join(testDir, 'SHA256SUMS.txt');
              writeChecksumsFile(checksums, checksumsFilePath);
              
              // Read checksums file
              const checksumsContent = fs.readFileSync(checksumsFilePath, 'utf8');
              const lines = checksumsContent.trim().split('\n');
              
              // Property: Number of lines should match number of files created
              expect(lines.length).toBe(filesToCreate.length);
              
              // Property: Every line should match the format
              const formatRegex = /^[a-f0-9]{64}  .+$/;
              for (const line of lines) {
                expect(line).toMatch(formatRegex);
              }
              
              // Property: File should end with newline
              expect(checksumsContent.endsWith('\n')).toBe(true);
              
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
