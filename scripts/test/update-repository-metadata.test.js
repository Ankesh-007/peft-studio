/**
 * Unit Tests for Repository Metadata Update Module
 * 
 * Tests core functionality for updating repository metadata.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const {
  getRepositoryUrl,
  extractGitHubUrls,
  getMarkdownFiles,
  checkUrlConsistency,
  updatePackageJsonUrls,
  updatePackageJsonKeywords,
  replaceUrlsInFile,
  updateDocumentationUrls,
  verifyDescriptionConsistency,
  updateRepositoryMetadata,
} = require('../update-repository-metadata');

/**
 * Helper: Create a temporary test directory
 */
function createTestDirectory() {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'metadata-test-'));
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
 * Helper: Clean up test directory
 */
function cleanupTestDirectory(dirPath) {
  if (fs.existsSync(dirPath)) {
    fs.rmSync(dirPath, { recursive: true, force: true });
  }
}

describe('Repository Metadata Update Module', () => {
  describe('getRepositoryUrl', () => {
    it('should extract repository URL from package.json', () => {
      const testDir = createTestDirectory();

      try {
        const packageJson = {
          name: 'test-package',
          version: '1.0.0',
          repository: {
            type: 'git',
            url: 'https://github.com/test/repo.git',
          },
        };
        createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
        
        const url = getRepositoryUrl(testDir);
        expect(url).toBe('https://github.com/test/repo.git');
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
    
    it('should throw error if package.json not found', () => {
      const testDir = createTestDirectory();
      
      try {
        expect(() => getRepositoryUrl(testDir)).toThrow('package.json not found');
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
    
    it('should throw error if repository URL not in package.json', () => {
      const testDir = createTestDirectory();
      
      try {
        const packageJson = {
          name: 'test-package',
          version: '1.0.0',
        };
        createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
        
        expect(() => getRepositoryUrl(testDir)).toThrow('Repository URL not found');
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
  });
  
  describe('extractGitHubUrls', () => {
    it('should extract GitHub URLs from markdown content', () => {
      const content = `
        Check out [our repo](https://github.com/owner/repo) for more info.
        Visit [issues](https://github.com/owner/repo/issues) to report bugs.
      `;
      
      const urls = extractGitHubUrls(content);
      
      expect(urls).toContain('https://github.com/owner/repo');
      expect(urls).toContain('https://github.com/owner/repo/issues');
    });
    
    it('should normalize URLs by removing .git suffix', () => {
      const content = 'Clone from https://github.com/owner/repo.git';
      
      const urls = extractGitHubUrls(content);
      
      expect(urls).toContain('https://github.com/owner/repo');
      expect(urls).not.toContain('https://github.com/owner/repo.git');
    });
    
    it('should normalize URLs by removing trailing slashes', () => {
      const content = 'Visit https://github.com/owner/repo/ for info';
      
      const urls = extractGitHubUrls(content);
      
      expect(urls).toContain('https://github.com/owner/repo');
    });
    
    it('should return empty array if no URLs found', () => {
      const content = 'This is just plain text with no URLs';
      
      const urls = extractGitHubUrls(content);
      
      expect(urls).toEqual([]);
    });
  });

  describe('getMarkdownFiles', () => {
    it('should find all markdown files in directory', () => {
      const testDir = createTestDirectory();
      
      try {
        createFile(testDir, 'README.md', '# README');
        createFile(testDir, 'CONTRIBUTING.md', '# Contributing');
        createFile(testDir, 'docs/guide.md', '# Guide');
        createFile(testDir, 'src/index.js', 'console.log("not markdown")');
        
        const files = getMarkdownFiles(testDir);
        
        expect(files.length).toBe(3);
        expect(files.some(f => f.endsWith('README.md'))).toBe(true);
        expect(files.some(f => f.endsWith('CONTRIBUTING.md'))).toBe(true);
        expect(files.some(f => f.endsWith('guide.md'))).toBe(true);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
    
    it('should skip node_modules and .git directories', () => {
      const testDir = createTestDirectory();
      
      try {
        createFile(testDir, 'README.md', '# README');
        createFile(testDir, 'node_modules/package/README.md', '# Package');
        createFile(testDir, '.git/config.md', '# Config');
        
        const files = getMarkdownFiles(testDir);
        
        expect(files.length).toBe(1);
        expect(files[0].endsWith('README.md')).toBe(true);
        expect(files[0]).not.toContain('node_modules');
        expect(files[0]).not.toContain('.git');
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
  });
  
  describe('updatePackageJsonUrls', () => {
    it('should update repository URL in package.json', () => {
      const testDir = createTestDirectory();
      
      try {
        const packageJson = {
          name: 'test-package',
          version: '1.0.0',
          repository: {
            type: 'git',
            url: 'https://github.com/old/repo.git',
          },
        };
        createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
        
        const result = updatePackageJsonUrls(testDir, 'https://github.com/new/repo');
        
        expect(result.repository).toBe(true);
        
        const updated = JSON.parse(fs.readFileSync(path.join(testDir, 'package.json'), 'utf8'));
        expect(updated.repository.url).toBe('https://github.com/new/repo.git');
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
    
    it('should update homepage URL in package.json', () => {
      const testDir = createTestDirectory();
      
      try {
        const packageJson = {
          name: 'test-package',
          version: '1.0.0',
          repository: {
            type: 'git',
            url: 'https://github.com/old/repo.git',
          },
          homepage: 'https://github.com/old/repo#readme',
        };
        createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
        
        const result = updatePackageJsonUrls(testDir, 'https://github.com/new/repo');
        
        expect(result.homepage).toBe(true);
        
        const updated = JSON.parse(fs.readFileSync(path.join(testDir, 'package.json'), 'utf8'));
        expect(updated.homepage).toBe('https://github.com/new/repo#readme');
      } finally {
        cleanupTestDirectory(testDir);
      }
    });

    it('should update bugs URL in package.json', () => {
      const testDir = createTestDirectory();
      
      try {
        const packageJson = {
          name: 'test-package',
          version: '1.0.0',
          repository: {
            type: 'git',
            url: 'https://github.com/old/repo.git',
          },
        };
        createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
        
        const result = updatePackageJsonUrls(testDir, 'https://github.com/new/repo');
        
        expect(result.bugs).toBe(true);
        
        const updated = JSON.parse(fs.readFileSync(path.join(testDir, 'package.json'), 'utf8'));
        expect(updated.bugs.url).toBe('https://github.com/new/repo/issues');
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
  });
  
  describe('updatePackageJsonKeywords', () => {
    it('should add new keywords to package.json', () => {
      const testDir = createTestDirectory();
      
      try {
        const packageJson = {
          name: 'test-package',
          version: '1.0.0',
          keywords: ['existing', 'old'],
        };
        createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
        
        const result = updatePackageJsonKeywords(testDir, ['new', 'fresh']);
        
        expect(result.updated).toBe(true);
        expect(result.added).toContain('new');
        expect(result.added).toContain('fresh');
        
        const updated = JSON.parse(fs.readFileSync(path.join(testDir, 'package.json'), 'utf8'));
        expect(updated.keywords).toContain('existing');
        expect(updated.keywords).toContain('old');
        expect(updated.keywords).toContain('new');
        expect(updated.keywords).toContain('fresh');
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
    
    it('should not duplicate existing keywords', () => {
      const testDir = createTestDirectory();
      
      try {
        const packageJson = {
          name: 'test-package',
          version: '1.0.0',
          keywords: ['test', 'package'],
        };
        createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
        
        const result = updatePackageJsonKeywords(testDir, ['test', 'new']);
        
        const updated = JSON.parse(fs.readFileSync(path.join(testDir, 'package.json'), 'utf8'));
        const testCount = updated.keywords.filter(k => k === 'test').length;
        expect(testCount).toBe(1);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
    
    it('should sort keywords alphabetically', () => {
      const testDir = createTestDirectory();
      
      try {
        const packageJson = {
          name: 'test-package',
          version: '1.0.0',
          keywords: ['zebra', 'apple'],
        };
        createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
        
        updatePackageJsonKeywords(testDir, ['banana']);
        
        const updated = JSON.parse(fs.readFileSync(path.join(testDir, 'package.json'), 'utf8'));
        expect(updated.keywords).toEqual(['apple', 'banana', 'zebra']);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
  });

  describe('replaceUrlsInFile', () => {
    it('should replace URLs in a file', () => {
      const testDir = createTestDirectory();
      
      try {
        const content = 'Visit https://github.com/old/repo for more info';
        const filePath = createFile(testDir, 'test.md', content);
        
        const result = replaceUrlsInFile(filePath, 'https://github.com/old/repo', 'https://github.com/new/repo');
        
        expect(result).toBe(true);
        
        const updated = fs.readFileSync(filePath, 'utf8');
        expect(updated).toContain('https://github.com/new/repo');
        expect(updated).not.toContain('https://github.com/old/repo');
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
    
    it('should handle URLs with .git suffix', () => {
      const testDir = createTestDirectory();
      
      try {
        const content = 'Clone from https://github.com/old/repo.git';
        const filePath = createFile(testDir, 'test.md', content);
        
        const result = replaceUrlsInFile(filePath, 'https://github.com/old/repo', 'https://github.com/new/repo');
        
        expect(result).toBe(true);
        
        const updated = fs.readFileSync(filePath, 'utf8');
        expect(updated).toContain('https://github.com/new/repo');
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
    
    it('should return false if no changes made', () => {
      const testDir = createTestDirectory();
      
      try {
        const content = 'No URLs here';
        const filePath = createFile(testDir, 'test.md', content);
        
        const result = replaceUrlsInFile(filePath, 'https://github.com/old/repo', 'https://github.com/new/repo');
        
        expect(result).toBe(false);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
  });
  
  describe('updateDocumentationUrls', () => {
    it('should update URLs in all markdown files', () => {
      const testDir = createTestDirectory();
      
      try {
        const packageJson = {
          name: 'test-package',
          version: '1.0.0',
          repository: {
            type: 'git',
            url: 'https://github.com/old/repo.git',
          },
        };
        createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
        
        createFile(testDir, 'README.md', 'Visit https://github.com/old/repo');
        createFile(testDir, 'docs/guide.md', 'See https://github.com/old/repo/issues');
        
        const result = updateDocumentationUrls(testDir, 'https://github.com/new/repo');
        
        expect(result.updated).toBe(true);
        expect(result.files.length).toBe(2);
        
        const readme = fs.readFileSync(path.join(testDir, 'README.md'), 'utf8');
        expect(readme).toContain('https://github.com/new/repo');
        
        const guide = fs.readFileSync(path.join(testDir, 'docs/guide.md'), 'utf8');
        expect(guide).toContain('https://github.com/new/repo');
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
  });
  
  describe('verifyDescriptionConsistency', () => {
    it('should verify description appears in README', () => {
      const testDir = createTestDirectory();
      
      try {
        const packageJson = {
          name: 'test-package',
          version: '1.0.0',
          description: 'A test package for testing',
        };
        createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
        createFile(testDir, 'README.md', '# Test Package\n\nA test package for testing purposes.');
        
        const result = verifyDescriptionConsistency(testDir);
        
        expect(result.consistent).toBe(true);
        expect(result.foundInReadme).toBe(true);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
    
    it('should detect missing description in README', () => {
      const testDir = createTestDirectory();
      
      try {
        const packageJson = {
          name: 'test-package',
          version: '1.0.0',
          description: 'A test package for testing',
        };
        createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
        createFile(testDir, 'README.md', '# Test Package\n\nSomething completely different.');
        
        const result = verifyDescriptionConsistency(testDir);
        
        expect(result.consistent).toBe(false);
        expect(result.foundInReadme).toBe(false);
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
  });
});
