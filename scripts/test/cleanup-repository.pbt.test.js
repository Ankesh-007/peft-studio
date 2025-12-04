/**
 * Property-Based Tests for Repository Cleanup Module
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
  identifyUnnecessaryFiles,
  removeUnnecessaryFiles,
  cleanupRepository,
  shouldPreserve,
  matchesPattern,
  CLEANUP_CONFIG,
} = require('../cleanup-repository');

/**
 * Helper: Create a temporary test directory structure
 */
function createTestDirectory() {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'cleanup-test-'));
  return tempDir;
}

/**
 * Helper: Create a file in a directory
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

/**
 * Helper: Get all files in a directory recursively
 */
function getAllFiles(dirPath) {
  const files = [];
  
  if (!fs.existsSync(dirPath)) {
    return files;
  }
  
  const items = fs.readdirSync(dirPath);
  
  for (const item of items) {
    const fullPath = path.join(dirPath, item);
    const stats = fs.statSync(fullPath);
    
    if (stats.isDirectory()) {
      files.push(...getAllFiles(fullPath));
    } else {
      files.push(fullPath);
    }
  }
  
  return files;
}

/**
 * Helper: Check if a file exists
 */
function fileExists(filePath) {
  return fs.existsSync(filePath);
}

describe('Repository Cleanup - Property-Based Tests', () => {
  /**
   * Feature: repository-professionalization, Property 1: Cleanup Idempotence
   * Validates: Requirements 4.1, 4.2, 4.3
   * 
   * For any repository state, running cleanup multiple times must produce 
   * the same result as running it once.
   */
  describe('Property 1: Cleanup Idempotence', () => {
    it('should produce the same result when run multiple times', () => {
      fc.assert(
        fc.property(
          fc.record({
            buildArtifacts: fc.array(fc.constantFrom('dist', 'build', '.pytest_cache'), { minLength: 0, maxLength: 3 }),
            tempFiles: fc.array(fc.constantFrom('test.log', 'temp.tmp', 'STATUS.md'), { minLength: 0, maxLength: 5 }),
          }),
          (testData) => {
            // Create test directory
            const testDir = createTestDirectory();
            
            try {
              // Create test structure
              for (const dir of testData.buildArtifacts) {
                createDirectory(testDir, dir);
                createFile(testDir, path.join(dir, 'test.txt'), 'content');
              }
              
              for (const file of testData.tempFiles) {
                createFile(testDir, file, 'temp content');
              }
              
              // Run cleanup first time
              const result1 = cleanupRepository(testDir, false);
              const filesAfterFirst = getAllFiles(testDir);
              
              // Run cleanup second time
              const result2 = cleanupRepository(testDir, false);
              const filesAfterSecond = getAllFiles(testDir);
              
              // Property: Files after first cleanup should equal files after second cleanup
              // This proves idempotence - running cleanup again doesn't change anything
              expect(filesAfterFirst.sort()).toEqual(filesAfterSecond.sort());
              
              // Additional check: Second cleanup should remove nothing
              expect(result2.results.removed.length).toBe(0);
              
            } finally {
              cleanupTestDirectory(testDir);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
    
    it('should identify the same files on repeated identification', () => {
      fc.assert(
        fc.property(
          fc.record({
            dirs: fc.array(fc.constantFrom('dist', 'build', '__pycache__'), { minLength: 1, maxLength: 3 }),
          }),
          (testData) => {
            const testDir = createTestDirectory();
            
            try {
              // Create test structure
              for (const dir of testData.dirs) {
                createDirectory(testDir, dir);
                createFile(testDir, path.join(dir, 'file.txt'), 'content');
              }
              
              // Identify files twice
              const identified1 = identifyUnnecessaryFiles(testDir);
              const identified2 = identifyUnnecessaryFiles(testDir);
              
              // Property: Identification should be deterministic
              expect(identified1.buildArtifacts.sort()).toEqual(identified2.buildArtifacts.sort());
              expect(identified1.testCaches.sort()).toEqual(identified2.testCaches.sort());
              expect(identified1.pythonBytecode.sort()).toEqual(identified2.pythonBytecode.sort());
              expect(identified1.temporaryFiles.sort()).toEqual(identified2.temporaryFiles.sort());
              
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
   * Feature: repository-professionalization, Property 5: Essential File Preservation
   * Validates: Requirements 4.3
   * 
   * For any cleanup operation, all files matching essential patterns 
   * (source code, documentation, configuration) must be preserved.
   */
  describe('Property 5: Essential File Preservation', () => {
    it('should preserve all essential files during cleanup', () => {
      fc.assert(
        fc.property(
          fc.record({
            essentialFiles: fc.array(
              fc.constantFrom(
                'src/main.ts',
                'backend/app.py',
                'README.md',
                'LICENSE',
                'package.json',
                'tsconfig.json',
                '.gitignore'
              ),
              { minLength: 1, maxLength: 7 }
            ),
            unnecessaryFiles: fc.array(
              fc.constantFrom(
                'dist/bundle.js',
                'build/output.txt',
                'test.log',
                'temp.tmp'
              ),
              { minLength: 0, maxLength: 4 }
            ),
          }),
          (testData) => {
            const testDir = createTestDirectory();
            
            try {
              // Create essential files
              const createdEssentialFiles = [];
              for (const file of testData.essentialFiles) {
                const filePath = createFile(testDir, file, 'essential content');
                createdEssentialFiles.push(filePath);
              }
              
              // Create unnecessary files
              for (const file of testData.unnecessaryFiles) {
                createFile(testDir, file, 'unnecessary content');
              }
              
              // Run cleanup
              cleanupRepository(testDir, false);
              
              // Property: All essential files must still exist
              for (const essentialFile of createdEssentialFiles) {
                expect(fileExists(essentialFile)).toBe(true);
              }
              
            } finally {
              cleanupTestDirectory(testDir);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
    
    it('should preserve files matching preserve patterns', () => {
      fc.assert(
        fc.property(
          fc.record({
            sourceFiles: fc.array(
              fc.tuple(
                fc.constantFrom('src', 'backend', 'docs'),
                fc.constantFrom('file1.ts', 'file2.py', 'doc.md')
              ),
              { minLength: 1, maxLength: 5 }
            ),
          }),
          (testData) => {
            const testDir = createTestDirectory();
            
            try {
              // Create source files
              const createdFiles = [];
              for (const [dir, file] of testData.sourceFiles) {
                const filePath = createFile(testDir, path.join(dir, file), 'source content');
                createdFiles.push(filePath);
              }
              
              // Create some unnecessary files
              createDirectory(testDir, 'dist');
              createFile(testDir, 'dist/bundle.js', 'build output');
              
              // Run cleanup
              cleanupRepository(testDir, false);
              
              // Property: All source files must be preserved
              for (const sourceFile of createdFiles) {
                expect(fileExists(sourceFile)).toBe(true);
              }
              
            } finally {
              cleanupTestDirectory(testDir);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
    
    it('should never delete files in preserve patterns', () => {
      fc.assert(
        fc.property(
          fc.constantFrom(
            'src/component.tsx',
            'backend/service.py',
            'docs/guide.md',
            'scripts/build.js',
            'README.md',
            'LICENSE',
            'package.json'
          ),
          (essentialFile) => {
            const testDir = createTestDirectory();
            
            try {
              // Create the essential file
              const filePath = createFile(testDir, essentialFile, 'important content');
              
              // Create unnecessary files
              createDirectory(testDir, 'dist');
              createFile(testDir, 'dist/output.js', 'build');
              createFile(testDir, 'test.log', 'log');
              
              // Run cleanup
              cleanupRepository(testDir, false);
              
              // Property: Essential file must still exist
              expect(fileExists(filePath)).toBe(true);
              
            } finally {
              cleanupTestDirectory(testDir);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
    
    it('should preserve configuration files', () => {
      fc.assert(
        fc.property(
          fc.array(
            fc.constantFrom(
              'tsconfig.json',
              'vite.config.ts',
              'vitest.config.ts',
              'tailwind.config.js',
              '.eslintrc.json'
            ),
            { minLength: 1, maxLength: 5 }
          ),
          (configFiles) => {
            const testDir = createTestDirectory();
            
            try {
              // Create config files
              const createdConfigs = [];
              for (const config of configFiles) {
                const filePath = createFile(testDir, config, '{}');
                createdConfigs.push(filePath);
              }
              
              // Create unnecessary files
              createFile(testDir, 'test.log', 'log');
              
              // Run cleanup
              cleanupRepository(testDir, false);
              
              // Property: All config files must be preserved
              for (const configFile of createdConfigs) {
                expect(fileExists(configFile)).toBe(true);
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
   * Additional property: Pattern matching should be consistent
   */
  describe('Pattern Matching Consistency', () => {
    it('should consistently match patterns', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 1, maxLength: 50 }),
          fc.constantFrom('*.log', '*.tmp', '*_SUMMARY.md', '*.pyc'),
          (filename, pattern) => {
            // Run pattern matching multiple times
            const result1 = matchesPattern(filename, pattern);
            const result2 = matchesPattern(filename, pattern);
            const result3 = matchesPattern(filename, pattern);
            
            // Property: Pattern matching should be deterministic
            expect(result1).toBe(result2);
            expect(result2).toBe(result3);
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});
