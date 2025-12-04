/**
 * Unit Tests for Checksum Module
 * 
 * Tests SHA-256 calculation, file format, verification, and error handling.
 * 
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
 */

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

describe('Checksum Module - Unit Tests', () => {
  describe('SHA-256 Calculation', () => {
    let testDir;
    
    beforeEach(() => {
      testDir = createTestDirectory();
    });
    
    afterEach(() => {
      cleanupTestDirectory(testDir);
    });
    
    it('should calculate SHA-256 checksum for a file', async () => {
      const content = 'Hello, World!';
      const filePath = createFile(testDir, 'test.exe', content);
      
      const checksum = await calculateChecksum(filePath);
      
      // Verify it's a valid SHA-256 hash (64 hex characters)
      expect(checksum).toMatch(/^[a-f0-9]{64}$/);
      
      // Verify it matches expected hash
      const expectedHash = crypto.createHash('sha256').update(content).digest('hex');
      expect(checksum).toBe(expectedHash);
    });
    
    it('should calculate different checksums for different content', async () => {
      const file1 = createFile(testDir, 'file1.exe', 'content1');
      const file2 = createFile(testDir, 'file2.exe', 'content2');
      
      const checksum1 = await calculateChecksum(file1);
      const checksum2 = await calculateChecksum(file2);
      
      expect(checksum1).not.toBe(checksum2);
    });
    
    it('should calculate same checksum for same content', async () => {
      const content = 'same content';
      const file1 = createFile(testDir, 'file1.exe', content);
      const file2 = createFile(testDir, 'file2.exe', content);
      
      const checksum1 = await calculateChecksum(file1);
      const checksum2 = await calculateChecksum(file2);
      
      expect(checksum1).toBe(checksum2);
    });
    
    it('should handle empty files', async () => {
      const filePath = createFile(testDir, 'empty.exe', '');
      
      const checksum = await calculateChecksum(filePath);
      
      expect(checksum).toMatch(/^[a-f0-9]{64}$/);
      
      // SHA-256 of empty string
      const expectedHash = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855';
      expect(checksum).toBe(expectedHash);
    });
    
    it('should handle large files', async () => {
      const largeContent = 'x'.repeat(1000000); // 1MB
      const filePath = createFile(testDir, 'large.exe', largeContent);
      
      const checksum = await calculateChecksum(filePath);
      
      expect(checksum).toMatch(/^[a-f0-9]{64}$/);
    });
    
    it('should handle binary content', async () => {
      const binaryContent = Buffer.from([0x00, 0x01, 0x02, 0xFF]);
      const filePath = path.join(testDir, 'binary.exe');
      fs.writeFileSync(filePath, binaryContent);
      
      const checksum = await calculateChecksum(filePath);
      
      expect(checksum).toMatch(/^[a-f0-9]{64}$/);
    });
    
    it('should reject non-existent files', async () => {
      const nonExistentPath = path.join(testDir, 'does-not-exist.exe');
      
      await expect(calculateChecksum(nonExistentPath)).rejects.toThrow();
    });
  });
  
  describe('File Format', () => {
    let testDir;
    
    beforeEach(() => {
      testDir = createTestDirectory();
    });
    
    afterEach(() => {
      cleanupTestDirectory(testDir);
    });
    
    it('should format checksums with hash, two spaces, and filename', async () => {
      const filePath = createFile(testDir, 'test.exe', 'content');
      const checksum = await calculateChecksum(filePath);
      
      const checksums = [{ file: 'test.exe', checksum }];
      const outputPath = path.join(testDir, 'SHA256SUMS.txt');
      
      writeChecksumsFile(checksums, outputPath);
      
      const content = fs.readFileSync(outputPath, 'utf8');
      const expectedLine = `${checksum}  test.exe\n`;
      
      expect(content).toBe(expectedLine);
    });
    
    it('should format multiple checksums correctly', async () => {
      const file1 = createFile(testDir, 'file1.exe', 'content1');
      const file2 = createFile(testDir, 'file2.exe', 'content2');
      
      const checksum1 = await calculateChecksum(file1);
      const checksum2 = await calculateChecksum(file2);
      
      const checksums = [
        { file: 'file1.exe', checksum: checksum1 },
        { file: 'file2.exe', checksum: checksum2 },
      ];
      
      const outputPath = path.join(testDir, 'SHA256SUMS.txt');
      writeChecksumsFile(checksums, outputPath);
      
      const content = fs.readFileSync(outputPath, 'utf8');
      const lines = content.split('\n').filter(line => line.length > 0);
      
      expect(lines.length).toBe(2);
      expect(lines[0]).toBe(`${checksum1}  file1.exe`);
      expect(lines[1]).toBe(`${checksum2}  file2.exe`);
    });
    
    it('should end file with newline', async () => {
      const filePath = createFile(testDir, 'test.exe', 'content');
      const checksum = await calculateChecksum(filePath);
      
      const checksums = [{ file: 'test.exe', checksum }];
      const outputPath = path.join(testDir, 'SHA256SUMS.txt');
      
      writeChecksumsFile(checksums, outputPath);
      
      const content = fs.readFileSync(outputPath, 'utf8');
      
      expect(content.endsWith('\n')).toBe(true);
    });
    
    it('should handle filenames with spaces', async () => {
      const filePath = createFile(testDir, 'PEFT Studio-Setup-1.0.0.exe', 'content');
      const checksum = await calculateChecksum(filePath);
      
      const checksums = [{ file: 'PEFT Studio-Setup-1.0.0.exe', checksum }];
      const outputPath = path.join(testDir, 'SHA256SUMS.txt');
      
      writeChecksumsFile(checksums, outputPath);
      
      const content = fs.readFileSync(outputPath, 'utf8');
      
      expect(content).toContain('PEFT Studio-Setup-1.0.0.exe');
      expect(content).toMatch(/^[a-f0-9]{64}  PEFT Studio-Setup-1\.0\.0\.exe\n$/);
    });
  });
  
  describe('File Inclusion Logic', () => {
    it('should include .exe files', () => {
      expect(shouldIncludeFile('app-Setup-1.0.0.exe')).toBe(true);
      expect(shouldIncludeFile('app-Portable-1.0.0.exe')).toBe(true);
    });
    
    it('should include .dmg files', () => {
      expect(shouldIncludeFile('app-1.0.0-x64.dmg')).toBe(true);
      expect(shouldIncludeFile('app-1.0.0-arm64.dmg')).toBe(true);
    });
    
    it('should include .zip files', () => {
      expect(shouldIncludeFile('app-1.0.0-x64.zip')).toBe(true);
      expect(shouldIncludeFile('app-1.0.0-arm64.zip')).toBe(true);
    });
    
    it('should include .AppImage files', () => {
      expect(shouldIncludeFile('app-1.0.0-x64.AppImage')).toBe(true);
    });
    
    it('should include .deb files', () => {
      expect(shouldIncludeFile('app-1.0.0-amd64.deb')).toBe(true);
    });
    
    it('should exclude .blockmap files', () => {
      expect(shouldIncludeFile('app-Setup-1.0.0.exe.blockmap')).toBe(false);
    });
    
    it('should exclude SHA256SUMS.txt', () => {
      expect(shouldIncludeFile('SHA256SUMS.txt')).toBe(false);
    });
    
    it('should exclude files without valid extensions', () => {
      expect(shouldIncludeFile('README.md')).toBe(false);
      expect(shouldIncludeFile('package.json')).toBe(false);
      expect(shouldIncludeFile('app.txt')).toBe(false);
    });
  });
  
  describe('Checksum Generation', () => {
    let testDir;
    
    beforeEach(() => {
      testDir = createTestDirectory();
    });
    
    afterEach(() => {
      cleanupTestDirectory(testDir);
    });
    
    it('should generate checksums for all installer files', async () => {
      createFile(testDir, 'app-Setup-1.0.0.exe', 'content1');
      createFile(testDir, 'app-Portable-1.0.0.exe', 'content2');
      createFile(testDir, 'app-1.0.0-x64.dmg', 'content3');
      
      const checksums = await generateChecksums(testDir);
      
      expect(checksums.length).toBe(3);
      
      const filenames = checksums.map(c => c.file);
      expect(filenames).toContain('app-Setup-1.0.0.exe');
      expect(filenames).toContain('app-Portable-1.0.0.exe');
      expect(filenames).toContain('app-1.0.0-x64.dmg');
    });
    
    it('should return empty array for directory without installer files', async () => {
      createFile(testDir, 'README.md', 'content');
      createFile(testDir, 'package.json', 'content');
      
      const checksums = await generateChecksums(testDir);
      
      expect(checksums).toEqual([]);
    });
    
    it('should skip excluded files', async () => {
      createFile(testDir, 'app-Setup-1.0.0.exe', 'content1');
      createFile(testDir, 'app-Setup-1.0.0.exe.blockmap', 'content2');
      createFile(testDir, 'SHA256SUMS.txt', 'content3');
      
      const checksums = await generateChecksums(testDir);
      
      expect(checksums.length).toBe(1);
      expect(checksums[0].file).toBe('app-Setup-1.0.0.exe');
    });
    
    it('should include checksum and file properties', async () => {
      createFile(testDir, 'app-Setup-1.0.0.exe', 'content');
      
      const checksums = await generateChecksums(testDir);
      
      expect(checksums.length).toBe(1);
      expect(checksums[0]).toHaveProperty('file');
      expect(checksums[0]).toHaveProperty('checksum');
      expect(checksums[0].checksum).toMatch(/^[a-f0-9]{64}$/);
    });
  });
  
  describe('Error Handling', () => {
    let testDir;
    
    beforeEach(() => {
      testDir = createTestDirectory();
    });
    
    afterEach(() => {
      cleanupTestDirectory(testDir);
    });
    
    it('should throw error for non-existent directory', async () => {
      const nonExistentDir = path.join(testDir, 'does-not-exist');
      
      await expect(generateChecksums(nonExistentDir)).rejects.toThrow();
    });
    
    it('should throw error when calculating checksum for non-existent file', async () => {
      const nonExistentFile = path.join(testDir, 'does-not-exist.exe');
      
      await expect(calculateChecksum(nonExistentFile)).rejects.toThrow();
    });
    
    it('should throw error when writing to invalid path', () => {
      const checksums = [{ file: 'test.exe', checksum: 'a'.repeat(64) }];
      const invalidPath = path.join(testDir, 'nonexistent', 'SHA256SUMS.txt');
      
      expect(() => writeChecksumsFile(checksums, invalidPath)).toThrow();
    });
    
    it('should handle empty checksums array', () => {
      const outputPath = path.join(testDir, 'SHA256SUMS.txt');
      
      writeChecksumsFile([], outputPath);
      
      const content = fs.readFileSync(outputPath, 'utf8');
      expect(content).toBe('\n');
    });
  });
  
  describe('Verification', () => {
    let testDir;
    
    beforeEach(() => {
      testDir = createTestDirectory();
    });
    
    afterEach(() => {
      cleanupTestDirectory(testDir);
    });
    
    it('should verify checksums match file content', async () => {
      const content = 'test content';
      const filePath = createFile(testDir, 'test.exe', content);
      
      const checksum1 = await calculateChecksum(filePath);
      const checksum2 = await calculateChecksum(filePath);
      
      expect(checksum1).toBe(checksum2);
    });
    
    it('should detect when file content changes', async () => {
      const filePath = path.join(testDir, 'test.exe');
      
      fs.writeFileSync(filePath, 'original content', 'utf8');
      const checksum1 = await calculateChecksum(filePath);
      
      fs.writeFileSync(filePath, 'modified content', 'utf8');
      const checksum2 = await calculateChecksum(filePath);
      
      expect(checksum1).not.toBe(checksum2);
    });
    
    it('should verify checksums from file match actual files', async () => {
      createFile(testDir, 'app-Setup-1.0.0.exe', 'content1');
      createFile(testDir, 'app-Portable-1.0.0.exe', 'content2');
      
      const checksums = await generateChecksums(testDir);
      const outputPath = path.join(testDir, 'SHA256SUMS.txt');
      writeChecksumsFile(checksums, outputPath);
      
      // Read checksums file
      const content = fs.readFileSync(outputPath, 'utf8');
      const lines = content.trim().split('\n');
      
      // Verify each checksum
      for (const line of lines) {
        const [hash, filename] = line.split('  ');
        const filePath = path.join(testDir, filename);
        const actualHash = await calculateChecksum(filePath);
        
        expect(actualHash).toBe(hash);
      }
    });
  });
});
