/**
 * Unit Tests for Release Validation Module
 * 
 * Tests for validate-release.js functionality
 * Requirements: 6.1, 6.2, 6.3, 6.4, 10.1, 10.2, 10.3, 10.4, 10.5
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const {
  validateStructure,
  validateMetadata,
  validateSemanticVersion,
  verifyChangelogVersion,
  checkWorkingDirectory,
  validateReadiness,
} = require('../validate-release');

/**
 * Helper: Create a temporary test directory
 */
function createTestDirectory() {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'validate-test-'));
  return tempDir;
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

describe('Release Validation Module - Unit Tests', () => {
  describe('validateStructure', () => {
    it('should pass validation when all required files exist', () => {
      const testDir = createTestDirectory();
      
      try {
        // Create required files
        createFile(testDir, 'LICENSE', 'MIT License');
        createFile(testDir, '.gitignore', 'node_modules\ndist\n*.log');
        createFile(testDir, 'README.md', '# Test Project');
        createFile(testDir, 'CONTRIBUTING.md', '# Contributing');
        createFile(testDir, 'CHANGELOG.md', '# Changelog');
        
        const result = validateStructure(testDir);
        
        expect(result.valid).toBe(true);
        expect(result.licenseExists).toBe(true);
        expect(result.gitignoreCorrect).toBe(true);
        expect(result.docsWellFormatted).toBe(true);
        expect(result.errors).toHaveLength(0);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
    
    it('should fail validation when LICENSE is missing', () => {
      const testDir = createTestDirectory();
      
      try {
        createFile(testDir, '.gitignore', 'node_modules\ndist\n*.log');
        createFile(testDir, 'README.md', '# Test');
        createFile(testDir, 'CONTRIBUTING.md', '# Contributing');
        createFile(testDir, 'CHANGELOG.md', '# Changelog');
        
        const result = validateStructure(testDir);
        
        expect(result.valid).toBe(false);
        expect(result.licenseExists).toBe(false);
        expect(result.errors.length).toBeGreaterThan(0);
        expect(result.errors.some(e => e.includes('LICENSE'))).toBe(true);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
    
    it('should detect missing documentation files', () => {
      const testDir = createTestDirectory();
      
      try {
        createFile(testDir, 'LICENSE', 'MIT');
        createFile(testDir, '.gitignore', 'node_modules\ndist\n*.log');
        // Missing README, CONTRIBUTING, CHANGELOG
        
        const result = validateStructure(testDir);
        
        expect(result.valid).toBe(false);
        expect(result.docsWellFormatted).toBe(false);
        expect(result.errors.length).toBeGreaterThan(0);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
    
    it('should detect missing gitignore patterns', () => {
      const testDir = createTestDirectory();
      
      try {
        createFile(testDir, 'LICENSE', 'MIT');
        createFile(testDir, '.gitignore', '# Empty gitignore');
        createFile(testDir, 'README.md', '# Test');
        createFile(testDir, 'CONTRIBUTING.md', '# Contributing');
        createFile(testDir, 'CHANGELOG.md', '# Changelog');
        
        const result = validateStructure(testDir);
        
        expect(result.gitignoreCorrect).toBe(false);
        expect(result.errors.some(e => e.includes('.gitignore'))).toBe(true);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
    
    it('should detect empty documentation files', () => {
      const testDir = createTestDirectory();
      
      try {
        createFile(testDir, 'LICENSE', 'MIT');
        createFile(testDir, '.gitignore', 'node_modules\ndist\n*.log');
        createFile(testDir, 'README.md', ''); // Empty file
        createFile(testDir, 'CONTRIBUTING.md', '# Contributing');
        createFile(testDir, 'CHANGELOG.md', '# Changelog');
        
        const result = validateStructure(testDir);
        
        expect(result.errors.some(e => e.includes('empty'))).toBe(true);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
  });
  
  describe('validateMetadata', () => {
    it('should pass validation with complete package.json', () => {
      const testDir = createTestDirectory();
      
      try {
        const packageJson = {
          name: 'test-package',
          version: '1.0.0',
          description: 'Test package',
          author: 'Test Author',
          license: 'MIT',
          repository: {
            type: 'git',
            url: 'https://github.com/test/test.git'
          },
          keywords: ['test', 'package']
        };
        
        createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
        
        const result = validateMetadata(testDir);
        
        expect(result.valid).toBe(true);
        expect(result.packageJsonComplete).toBe(true);
        expect(result.versionValid).toBe(true);
        expect(result.repositoryUrlCorrect).toBe(true);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
    
    it('should fail validation when package.json is missing', () => {
      const testDir = createTestDirectory();
      
      try {
        const result = validateMetadata(testDir);
        
        expect(result.valid).toBe(false);
        expect(result.errors.some(e => e.includes('package.json'))).toBe(true);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
    
    it('should detect missing required fields', () => {
      const testDir = createTestDirectory();
      
      try {
        const packageJson = {
          name: 'test-package',
          // Missing version, description, author, license
        };
        
        createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
        
        const result = validateMetadata(testDir);
        
        expect(result.valid).toBe(false);
        expect(result.packageJsonComplete).toBe(false);
        expect(result.errors.length).toBeGreaterThan(0);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
    
    it('should detect invalid version format', () => {
      const testDir = createTestDirectory();
      
      try {
        const packageJson = {
          name: 'test-package',
          version: 'invalid-version',
          description: 'Test',
          author: 'Test',
          license: 'MIT'
        };
        
        createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
        
        const result = validateMetadata(testDir);
        
        expect(result.valid).toBe(false);
        expect(result.versionValid).toBe(false);
        expect(result.errors.some(e => e.includes('version'))).toBe(true);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
    
    it('should warn about missing keywords', () => {
      const testDir = createTestDirectory();
      
      try {
        const packageJson = {
          name: 'test-package',
          version: '1.0.0',
          description: 'Test',
          author: 'Test',
          license: 'MIT',
          // No keywords
        };
        
        createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
        
        const result = validateMetadata(testDir);
        
        expect(result.errors.some(e => e.includes('keywords'))).toBe(true);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
  });
  
  describe('validateSemanticVersion', () => {
    it('should validate correct semantic versions', () => {
      expect(validateSemanticVersion('1.0.0')).toBe(true);
      expect(validateSemanticVersion('0.0.1')).toBe(true);
      expect(validateSemanticVersion('10.20.30')).toBe(true);
      expect(validateSemanticVersion('1.0.0-alpha')).toBe(true);
      expect(validateSemanticVersion('1.0.0-beta.1')).toBe(true);
      expect(validateSemanticVersion('1.0.0+build.123')).toBe(true);
    });
    
    it('should reject invalid semantic versions', () => {
      expect(validateSemanticVersion('1.0')).toBe(false);
      expect(validateSemanticVersion('1')).toBe(false);
      expect(validateSemanticVersion('a.b.c')).toBe(false);
      expect(validateSemanticVersion('1.2.3.4')).toBe(false);
      expect(validateSemanticVersion('')).toBe(false);
      expect(validateSemanticVersion('v1.0.0')).toBe(false);
    });
  });
  
  describe('verifyChangelogVersion', () => {
    it('should pass when CHANGELOG contains current version', () => {
      const testDir = createTestDirectory();
      
      try {
        const packageJson = {
          name: 'test-package',
          version: '1.2.3',
          description: 'Test',
          author: 'Test',
          license: 'MIT'
        };
        
        const changelog = `# Changelog

## [1.2.3] - 2024-01-01

### Added
- New feature

### Fixed
- Bug fix
`;
        
        createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
        createFile(testDir, 'CHANGELOG.md', changelog);
        
        const result = verifyChangelogVersion(testDir);
        
        expect(result.valid).toBe(true);
        expect(result.changelogUpdated).toBe(true);
        expect(result.versionMatches).toBe(true);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
    
    it('should fail when CHANGELOG does not contain current version', () => {
      const testDir = createTestDirectory();
      
      try {
        const packageJson = {
          name: 'test-package',
          version: '2.0.0',
          description: 'Test',
          author: 'Test',
          license: 'MIT'
        };
        
        const changelog = `# Changelog

## [1.0.0] - 2024-01-01

### Added
- Initial release
`;
        
        createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
        createFile(testDir, 'CHANGELOG.md', changelog);
        
        const result = verifyChangelogVersion(testDir);
        
        expect(result.valid).toBe(false);
        expect(result.versionMatches).toBe(false);
        expect(result.errors.some(e => e.includes('2.0.0'))).toBe(true);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
    
    it('should fail when CHANGELOG is missing', () => {
      const testDir = createTestDirectory();
      
      try {
        const packageJson = {
          name: 'test-package',
          version: '1.0.0',
          description: 'Test',
          author: 'Test',
          license: 'MIT'
        };
        
        createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
        
        const result = verifyChangelogVersion(testDir);
        
        expect(result.valid).toBe(false);
        expect(result.errors.some(e => e.includes('CHANGELOG'))).toBe(true);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
    
    it('should handle version without brackets in CHANGELOG', () => {
      const testDir = createTestDirectory();
      
      try {
        const packageJson = {
          name: 'test-package',
          version: '1.0.0',
          description: 'Test',
          author: 'Test',
          license: 'MIT'
        };
        
        const changelog = `# Changelog

## 1.0.0 - 2024-01-01

### Added
- Feature
`;
        
        createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
        createFile(testDir, 'CHANGELOG.md', changelog);
        
        const result = verifyChangelogVersion(testDir);
        
        expect(result.valid).toBe(true);
        expect(result.versionMatches).toBe(true);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
  });
  
  describe('checkWorkingDirectory', () => {
    it('should handle non-git directories gracefully', () => {
      const testDir = createTestDirectory();
      
      try {
        const result = checkWorkingDirectory(testDir);
        
        // Should not fail validation if git is not available
        expect(result.errors.some(e => e.includes('git'))).toBe(true);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
  });
  
  describe('validateReadiness', () => {
    it('should aggregate all validation results', () => {
      const testDir = createTestDirectory();
      
      try {
        // Create a complete valid repository structure
        createFile(testDir, 'LICENSE', 'MIT License');
        createFile(testDir, '.gitignore', 'node_modules\ndist\n*.log');
        createFile(testDir, 'README.md', '# Test Project');
        createFile(testDir, 'CONTRIBUTING.md', '# Contributing');
        createFile(testDir, 'CHANGELOG.md', '# Changelog\n\n## [1.0.0] - 2024-01-01\n\n### Added\n- Initial release');
        
        const packageJson = {
          name: 'test-package',
          version: '1.0.0',
          description: 'Test package',
          author: 'Test Author',
          license: 'MIT',
          repository: {
            type: 'git',
            url: 'https://github.com/test/test.git'
          },
          keywords: ['test']
        };
        createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
        
        const result = validateReadiness(testDir, true); // Skip tests
        
        expect(result).toHaveProperty('ready');
        expect(result).toHaveProperty('testsPass');
        expect(result).toHaveProperty('changelogUpdated');
        expect(result).toHaveProperty('workingDirectoryClean');
        expect(result).toHaveProperty('issues');
        expect(Array.isArray(result.issues)).toBe(true);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
    
    it('should report all issues when validation fails', () => {
      const testDir = createTestDirectory();
      
      try {
        // Create incomplete repository (missing files)
        createFile(testDir, 'LICENSE', 'MIT');
        
        const result = validateReadiness(testDir, true); // Skip tests
        
        expect(result.ready).toBe(false);
        expect(result.issues.length).toBeGreaterThan(0);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
  });
});
