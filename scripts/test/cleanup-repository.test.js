/**
 * Unit Tests for Repository Cleanup Module
 * 
 * Tests file identification logic, selective removal, .gitignore updates,
 * and cleanup report generation.
 * 
 * Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const {
  identifyUnnecessaryFiles,
  removeUnnecessaryFiles,
  updateGitignore,
  generateCleanupReport,
  cleanupRepository,
  shouldPreserve,
  matchesPattern,
  matchesFilePattern,
  cleanReleaseDirectory,
  CLEANUP_CONFIG,
} = require('../cleanup-repository');

/**
 * Helper: Create a temporary test directory
 */
function createTestDirectory() {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'cleanup-test-'));
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

describe('Repository Cleanup Module - Unit Tests', () => {
  describe('Pattern Matching', () => {
    describe('matchesPattern', () => {
      it('should match simple wildcard patterns', () => {
        expect(matchesPattern('test.log', '*.log')).toBe(true);
        expect(matchesPattern('test.tmp', '*.tmp')).toBe(true);
        expect(matchesPattern('test.txt', '*.log')).toBe(false);
      });
      
      it('should match patterns with multiple wildcards', () => {
        expect(matchesPattern('BUILD_SUMMARY.md', '*_SUMMARY.md')).toBe(true);
        expect(matchesPattern('TEST_STATUS.md', '*_STATUS.md')).toBe(true);
        expect(matchesPattern('README.md', '*_SUMMARY.md')).toBe(false);
      });
      
      it('should match recursive patterns', () => {
        expect(matchesPattern('src/components/Button.tsx', 'src/**/*')).toBe(true);
        expect(matchesPattern('src/lib/utils.ts', 'src/**/*')).toBe(true);
        expect(matchesPattern('backend/app.py', 'src/**/*')).toBe(false);
      });
      
      it('should match exact filenames', () => {
        expect(matchesPattern('README.md', 'README.md')).toBe(true);
        expect(matchesPattern('LICENSE', 'LICENSE')).toBe(true);
        expect(matchesPattern('README.txt', 'README.md')).toBe(false);
      });
    });
    
    describe('matchesFilePattern', () => {
      it('should match configured file patterns', () => {
        expect(matchesFilePattern('test.log')).toBe(true);
        expect(matchesFilePattern('temp.tmp')).toBe(true);
        expect(matchesFilePattern('BUILD_SUMMARY.md')).toBe(true);
        expect(matchesFilePattern('TEST_STATUS.md')).toBe(true);
        expect(matchesFilePattern('test.pyc')).toBe(true);
      });
      
      it('should not match files outside patterns', () => {
        expect(matchesFilePattern('README.md')).toBe(false);
        expect(matchesFilePattern('package.json')).toBe(false);
        expect(matchesFilePattern('main.ts')).toBe(false);
      });
    });
    
    describe('shouldPreserve', () => {
      let testDir;
      
      beforeEach(() => {
        testDir = createTestDirectory();
      });
      
      afterEach(() => {
        cleanupTestDirectory(testDir);
      });
      
      it('should preserve source files', () => {
        const srcFile = path.join(testDir, 'src', 'main.ts');
        expect(shouldPreserve(srcFile, testDir)).toBe(true);
        
        const backendFile = path.join(testDir, 'backend', 'app.py');
        expect(shouldPreserve(backendFile, testDir)).toBe(true);
      });
      
      it('should preserve documentation files', () => {
        const readme = path.join(testDir, 'README.md');
        expect(shouldPreserve(readme, testDir)).toBe(true);
        
        const license = path.join(testDir, 'LICENSE');
        expect(shouldPreserve(license, testDir)).toBe(true);
        
        const docs = path.join(testDir, 'docs', 'guide.md');
        expect(shouldPreserve(docs, testDir)).toBe(true);
      });
      
      it('should preserve configuration files', () => {
        const packageJson = path.join(testDir, 'package.json');
        expect(shouldPreserve(packageJson, testDir)).toBe(true);
        
        const tsconfig = path.join(testDir, 'tsconfig.json');
        expect(shouldPreserve(tsconfig, testDir)).toBe(true);
        
        const viteConfig = path.join(testDir, 'vite.config.js');
        expect(shouldPreserve(viteConfig, testDir)).toBe(true);
      });
      
      it('should not preserve build artifacts', () => {
        const distFile = path.join(testDir, 'dist', 'bundle.js');
        expect(shouldPreserve(distFile, testDir)).toBe(false);
        
        const buildFile = path.join(testDir, 'build', 'output.txt');
        expect(shouldPreserve(buildFile, testDir)).toBe(false);
      });
    });
  });
  
  describe('File Identification', () => {
    let testDir;
    
    beforeEach(() => {
      testDir = createTestDirectory();
    });
    
    afterEach(() => {
      cleanupTestDirectory(testDir);
    });
    
    it('should identify build artifacts', () => {
      createDirectory(testDir, 'dist');
      createFile(testDir, 'dist/bundle.js', 'content');
      
      createDirectory(testDir, 'build');
      createFile(testDir, 'build/output.txt', 'content');
      
      const fileList = identifyUnnecessaryFiles(testDir);
      
      expect(fileList.buildArtifacts).toContain(path.join(testDir, 'dist'));
      expect(fileList.buildArtifacts).toContain(path.join(testDir, 'build'));
    });
    
    it('should identify test caches', () => {
      createDirectory(testDir, '.pytest_cache');
      createFile(testDir, '.pytest_cache/test.txt', 'content');
      
      createDirectory(testDir, '.hypothesis');
      createFile(testDir, '.hypothesis/data.txt', 'content');
      
      const fileList = identifyUnnecessaryFiles(testDir);
      
      expect(fileList.testCaches).toContain(path.join(testDir, '.pytest_cache'));
      expect(fileList.testCaches).toContain(path.join(testDir, '.hypothesis'));
    });
    
    it('should identify Python bytecode', () => {
      createDirectory(testDir, 'backend/__pycache__');
      createFile(testDir, 'backend/__pycache__/app.pyc', 'content');
      
      createDirectory(testDir, 'backend/services/__pycache__');
      createFile(testDir, 'backend/services/__pycache__/service.pyc', 'content');
      
      const fileList = identifyUnnecessaryFiles(testDir);
      
      expect(fileList.pythonBytecode.length).toBeGreaterThan(0);
      expect(fileList.pythonBytecode).toContain(path.join(testDir, 'backend', '__pycache__'));
    });
    
    it('should identify temporary files', () => {
      createFile(testDir, 'test.log', 'log content');
      createFile(testDir, 'temp.tmp', 'temp content');
      createFile(testDir, 'BUILD_SUMMARY.md', 'summary');
      
      const fileList = identifyUnnecessaryFiles(testDir);
      
      expect(fileList.temporaryFiles).toContain(path.join(testDir, 'test.log'));
      expect(fileList.temporaryFiles).toContain(path.join(testDir, 'temp.tmp'));
      expect(fileList.temporaryFiles).toContain(path.join(testDir, 'BUILD_SUMMARY.md'));
    });
    
    it('should not identify essential files', () => {
      createFile(testDir, 'README.md', 'readme');
      createFile(testDir, 'package.json', '{}');
      createDirectory(testDir, 'src');
      createFile(testDir, 'src/main.ts', 'code');
      
      const fileList = identifyUnnecessaryFiles(testDir);
      
      // Essential files should not appear in any category
      const allFiles = [
        ...fileList.buildArtifacts,
        ...fileList.temporaryFiles,
        ...fileList.testCaches,
        ...fileList.pythonBytecode,
      ];
      
      expect(allFiles).not.toContain(path.join(testDir, 'README.md'));
      expect(allFiles).not.toContain(path.join(testDir, 'package.json'));
      expect(allFiles).not.toContain(path.join(testDir, 'src', 'main.ts'));
    });
  });
  
  describe('Selective Removal', () => {
    let testDir;
    
    beforeEach(() => {
      testDir = createTestDirectory();
    });
    
    afterEach(() => {
      cleanupTestDirectory(testDir);
    });
    
    it('should remove identified files', () => {
      createDirectory(testDir, 'dist');
      createFile(testDir, 'dist/bundle.js', 'content');
      createFile(testDir, 'test.log', 'log');
      
      const fileList = identifyUnnecessaryFiles(testDir);
      const results = removeUnnecessaryFiles(fileList, false);
      
      expect(results.removed.length).toBeGreaterThan(0);
      expect(fs.existsSync(path.join(testDir, 'dist'))).toBe(false);
      expect(fs.existsSync(path.join(testDir, 'test.log'))).toBe(false);
    });
    
    it('should not remove files in dry-run mode', () => {
      createDirectory(testDir, 'dist');
      createFile(testDir, 'dist/bundle.js', 'content');
      
      const fileList = identifyUnnecessaryFiles(testDir);
      const results = removeUnnecessaryFiles(fileList, true);
      
      expect(results.removed.length).toBeGreaterThan(0);
      expect(fs.existsSync(path.join(testDir, 'dist'))).toBe(true);
    });
    
    it('should track size freed', () => {
      createDirectory(testDir, 'dist');
      createFile(testDir, 'dist/bundle.js', 'x'.repeat(1000));
      
      const fileList = identifyUnnecessaryFiles(testDir);
      const results = removeUnnecessaryFiles(fileList, false);
      
      expect(results.totalSizeFreed).toBeGreaterThan(0);
    });
  });
  
  describe('Release Directory Cleanup', () => {
    let testDir;
    
    beforeEach(() => {
      testDir = createTestDirectory();
    });
    
    afterEach(() => {
      cleanupTestDirectory(testDir);
    });
    
    it('should remove subdirectories from release', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createDirectory(releaseDir, 'win-unpacked');
      createFile(releaseDir, 'win-unpacked/app.exe', 'content');
      
      const results = cleanReleaseDirectory(releaseDir, false);
      
      expect(results.removed.length).toBeGreaterThan(0);
      expect(fs.existsSync(path.join(releaseDir, 'win-unpacked'))).toBe(false);
    });
    
    it('should preserve specific files in release', () => {
      const releaseDir = createDirectory(testDir, 'release');
      createFile(releaseDir, 'SHA256SUMS.txt', 'checksums');
      createFile(releaseDir, 'latest.yml', 'metadata');
      createDirectory(releaseDir, 'win-unpacked');
      
      const results = cleanReleaseDirectory(releaseDir, false);
      
      expect(fs.existsSync(path.join(releaseDir, 'SHA256SUMS.txt'))).toBe(true);
      expect(fs.existsSync(path.join(releaseDir, 'latest.yml'))).toBe(true);
      expect(results.preserved.length).toBeGreaterThan(0);
    });
  });
  
  describe('Gitignore Updates', () => {
    let testDir;
    
    beforeEach(() => {
      testDir = createTestDirectory();
    });
    
    afterEach(() => {
      cleanupTestDirectory(testDir);
    });
    
    it('should create .gitignore if it does not exist', () => {
      const result = updateGitignore(testDir, false);
      
      expect(result).toBe(true);
      expect(fs.existsSync(path.join(testDir, '.gitignore'))).toBe(true);
    });
    
    it('should add missing patterns to .gitignore', () => {
      createFile(testDir, '.gitignore', 'node_modules/\n');
      
      updateGitignore(testDir, false);
      
      const content = fs.readFileSync(path.join(testDir, '.gitignore'), 'utf8');
      expect(content).toContain('release/*');
      expect(content).toContain('dist/');
      expect(content).toContain('.pytest_cache/');
    });
    
    it('should not duplicate existing patterns', () => {
      const existingContent = CLEANUP_CONFIG.gitignorePatterns.join('\n');
      createFile(testDir, '.gitignore', existingContent);
      
      updateGitignore(testDir, false);
      
      const content = fs.readFileSync(path.join(testDir, '.gitignore'), 'utf8');
      const distCount = (content.match(/dist\//g) || []).length;
      expect(distCount).toBe(1);
    });
    
    it('should not modify .gitignore in dry-run mode', () => {
      createFile(testDir, '.gitignore', 'node_modules/\n');
      const originalContent = fs.readFileSync(path.join(testDir, '.gitignore'), 'utf8');
      
      updateGitignore(testDir, true);
      
      const newContent = fs.readFileSync(path.join(testDir, '.gitignore'), 'utf8');
      expect(newContent).toBe(originalContent);
    });
  });
  
  describe('Cleanup Report Generation', () => {
    it('should generate a complete report', () => {
      const results = {
        removed: ['file1', 'file2', 'file3'],
        preserved: [],
        errors: [],
        totalSizeFreed: 1024 * 1024 * 5, // 5 MB
      };
      
      const startTime = Date.now() - 1000; // 1 second ago
      const report = generateCleanupReport(results, startTime);
      
      expect(report.filesRemoved).toBe(3);
      expect(report.sizeFreed).toContain('MB');
      expect(report.categoriesCleared).toBeInstanceOf(Array);
      expect(report.timestamp).toBeDefined();
      expect(report.duration).toBeDefined();
    });
    
    it('should format size correctly', () => {
      const results = {
        removed: ['file1'],
        preserved: [],
        errors: [],
        totalSizeFreed: 1024, // 1 KB
      };
      
      const report = generateCleanupReport(results, Date.now());
      
      expect(report.sizeFreed).toContain('KB');
    });
  });
  
  describe('Complete Cleanup', () => {
    let testDir;
    
    beforeEach(() => {
      testDir = createTestDirectory();
    });
    
    afterEach(() => {
      cleanupTestDirectory(testDir);
    });
    
    it('should perform complete cleanup workflow', () => {
      // Create test structure
      createDirectory(testDir, 'dist');
      createFile(testDir, 'dist/bundle.js', 'content');
      createFile(testDir, 'test.log', 'log');
      createFile(testDir, 'README.md', 'readme');
      
      const { results, report } = cleanupRepository(testDir, false);
      
      expect(results.removed.length).toBeGreaterThan(0);
      expect(report.filesRemoved).toBeGreaterThan(0);
      expect(fs.existsSync(path.join(testDir, 'README.md'))).toBe(true);
      expect(fs.existsSync(path.join(testDir, 'dist'))).toBe(false);
    });
    
    it('should not modify files in dry-run mode', () => {
      createDirectory(testDir, 'dist');
      createFile(testDir, 'dist/bundle.js', 'content');
      
      const { results } = cleanupRepository(testDir, true);
      
      expect(results.removed.length).toBeGreaterThan(0);
      expect(fs.existsSync(path.join(testDir, 'dist'))).toBe(true);
    });
  });
});
