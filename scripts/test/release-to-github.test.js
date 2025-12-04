/**
 * Unit Tests for GitHub Release Manager
 * 
 * Tests release notes extraction, asset upload with retry, upload verification,
 * git tag creation, and release summary generation.
 * 
 * Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 8.3, 8.5
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const {
  RELEASE_CONFIG,
  extractReleaseNotes,
  getRepositoryInfo,
  getVersion,
  verifyUploadedAssets,
  collectReleaseArtifacts,
  generateReleaseSummary,
} = require('../release-to-github');

/**
 * Helper: Create a temporary test directory
 */
function createTestDirectory() {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'release-test-'));
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

describe('GitHub Release Manager - Unit Tests', () => {
  describe('Release Notes Extraction', () => {
    let testDir;
    
    beforeEach(() => {
      testDir = createTestDirectory();
    });
    
    afterEach(() => {
      cleanupTestDirectory(testDir);
    });
    
    it('should extract release notes for a specific version', () => {
      const changelogContent = `# Changelog

## [1.0.1] - 2024-12-04

### Fixed
- Bug fix 1
- Bug fix 2

### Added
- New feature 1

## [1.0.0] - 2024-12-01

### Initial Release
`;
      
      const changelogPath = createFile(testDir, 'CHANGELOG.md', changelogContent);
      const notes = extractReleaseNotes('1.0.1', changelogPath);
      
      expect(notes).toContain('### Fixed');
      expect(notes).toContain('Bug fix 1');
      expect(notes).toContain('### Added');
      expect(notes).toContain('New feature 1');
      expect(notes).not.toContain('### Initial Release');
    });
    
    it('should extract notes up to the next version header', () => {
      const changelogContent = `# Changelog

## [2.0.0] - 2024-12-10

### Breaking
- Breaking change

## [1.0.1] - 2024-12-04

### Fixed
- Bug fix

## [1.0.0] - 2024-12-01

### Initial Release
`;
      
      const changelogPath = createFile(testDir, 'CHANGELOG.md', changelogContent);
      const notes = extractReleaseNotes('1.0.1', changelogPath);
      
      expect(notes).toContain('### Fixed');
      expect(notes).toContain('Bug fix');
      expect(notes).not.toContain('### Breaking');
      expect(notes).not.toContain('### Initial Release');
    });
    
    it('should throw error if version not found', () => {
      const changelogContent = `# Changelog

## [1.0.0] - 2024-12-01

### Initial Release
`;
      
      const changelogPath = createFile(testDir, 'CHANGELOG.md', changelogContent);
      
      expect(() => {
        extractReleaseNotes('2.0.0', changelogPath);
      }).toThrow('Version 2.0.0 not found in CHANGELOG.md');
    });
    
    it('should throw error if CHANGELOG.md does not exist', () => {
      const nonExistentPath = path.join(testDir, 'NONEXISTENT.md');
      
      expect(() => {
        extractReleaseNotes('1.0.0', nonExistentPath);
      }).toThrow('CHANGELOG.md not found');
    });
    
    it('should throw error if no release notes found for version', () => {
      const changelogContent = `# Changelog

## [1.0.1] - 2024-12-04

## [1.0.0] - 2024-12-01
`;
      
      const changelogPath = createFile(testDir, 'CHANGELOG.md', changelogContent);
      
      expect(() => {
        extractReleaseNotes('1.0.1', changelogPath);
      }).toThrow('No release notes found for version 1.0.1');
    });
    
    it('should handle version with different formats', () => {
      const changelogContent = `# Changelog

## [1.0.1] - 2024-12-04

### Fixed
- Bug fix
`;
      
      const changelogPath = createFile(testDir, 'CHANGELOG.md', changelogContent);
      const notes = extractReleaseNotes('1.0.1', changelogPath);
      
      expect(notes).toContain('### Fixed');
      expect(notes).toContain('Bug fix');
    });
  });
  
  describe('Repository Information', () => {
    let testDir;
    let originalEnv;
    
    beforeEach(() => {
      testDir = createTestDirectory();
      originalEnv = process.env.GITHUB_REPOSITORY;
    });
    
    afterEach(() => {
      cleanupTestDirectory(testDir);
      process.env.GITHUB_REPOSITORY = originalEnv;
    });
    
    it('should get repository info from environment variable', () => {
      process.env.GITHUB_REPOSITORY = 'testowner/testrepo';
      
      const packageContent = JSON.stringify({
        name: 'test-package',
        version: '1.0.0',
      });
      
      const packagePath = createFile(testDir, 'package.json', packageContent);
      const info = getRepositoryInfo(packagePath);
      
      expect(info.owner).toBe('testowner');
      expect(info.repo).toBe('testrepo');
      expect(info.url).toBe('https://github.com/testowner/testrepo');
    });
    
    it('should get repository info from package.json string format', () => {
      delete process.env.GITHUB_REPOSITORY;
      
      const packageContent = JSON.stringify({
        name: 'test-package',
        version: '1.0.0',
        repository: 'https://github.com/testowner/testrepo',
      });
      
      const packagePath = createFile(testDir, 'package.json', packageContent);
      const info = getRepositoryInfo(packagePath);
      
      expect(info.owner).toBe('testowner');
      expect(info.repo).toBe('testrepo');
      expect(info.url).toBe('https://github.com/testowner/testrepo');
    });
    
    it('should get repository info from package.json object format', () => {
      delete process.env.GITHUB_REPOSITORY;
      
      const packageContent = JSON.stringify({
        name: 'test-package',
        version: '1.0.0',
        repository: {
          type: 'git',
          url: 'https://github.com/testowner/testrepo.git',
        },
      });
      
      const packagePath = createFile(testDir, 'package.json', packageContent);
      const info = getRepositoryInfo(packagePath);
      
      expect(info.owner).toBe('testowner');
      expect(info.repo).toBe('testrepo');
      expect(info.url).toBe('https://github.com/testowner/testrepo');
    });
    
    it('should handle git+https:// format', () => {
      delete process.env.GITHUB_REPOSITORY;
      
      const packageContent = JSON.stringify({
        name: 'test-package',
        version: '1.0.0',
        repository: 'git+https://github.com/testowner/testrepo.git',
      });
      
      const packagePath = createFile(testDir, 'package.json', packageContent);
      const info = getRepositoryInfo(packagePath);
      
      expect(info.owner).toBe('testowner');
      expect(info.repo).toBe('testrepo');
    });
    
    it('should throw error if no repository field and no env var', () => {
      delete process.env.GITHUB_REPOSITORY;
      
      const packageContent = JSON.stringify({
        name: 'test-package',
        version: '1.0.0',
      });
      
      const packagePath = createFile(testDir, 'package.json', packageContent);
      
      expect(() => {
        getRepositoryInfo(packagePath);
      }).toThrow('No repository field in package.json');
    });
    
    it('should throw error if package.json does not exist', () => {
      const nonExistentPath = path.join(testDir, 'NONEXISTENT.json');
      
      expect(() => {
        getRepositoryInfo(nonExistentPath);
      }).toThrow('package.json not found');
    });
  });
  
  describe('Version Extraction', () => {
    let testDir;
    
    beforeEach(() => {
      testDir = createTestDirectory();
    });
    
    afterEach(() => {
      cleanupTestDirectory(testDir);
    });
    
    it('should get version from package.json', () => {
      const packageContent = JSON.stringify({
        name: 'test-package',
        version: '1.2.3',
      });
      
      const packagePath = createFile(testDir, 'package.json', packageContent);
      const version = getVersion(packagePath);
      
      expect(version).toBe('1.2.3');
    });
    
    it('should throw error if no version field', () => {
      const packageContent = JSON.stringify({
        name: 'test-package',
      });
      
      const packagePath = createFile(testDir, 'package.json', packageContent);
      
      expect(() => {
        getVersion(packagePath);
      }).toThrow('No version field in package.json');
    });
    
    it('should throw error if package.json does not exist', () => {
      const nonExistentPath = path.join(testDir, 'NONEXISTENT.json');
      
      expect(() => {
        getVersion(nonExistentPath);
      }).toThrow('package.json not found');
    });
  });
  
  describe('Upload Verification', () => {
    it('should verify all assets uploaded', () => {
      const release = {
        assets: [
          { name: 'installer1.exe' },
          { name: 'installer2.dmg' },
          { name: 'SHA256SUMS.txt' },
        ],
      };
      
      const expectedFiles = ['installer1.exe', 'installer2.dmg', 'SHA256SUMS.txt'];
      const verification = verifyUploadedAssets(release, expectedFiles);
      
      expect(verification.valid).toBe(true);
      expect(verification.uploaded).toEqual(['installer1.exe', 'installer2.dmg', 'SHA256SUMS.txt']);
      expect(verification.missing).toEqual([]);
    });
    
    it('should detect missing assets', () => {
      const release = {
        assets: [
          { name: 'installer1.exe' },
        ],
      };
      
      const expectedFiles = ['installer1.exe', 'installer2.dmg', 'SHA256SUMS.txt'];
      const verification = verifyUploadedAssets(release, expectedFiles);
      
      expect(verification.valid).toBe(false);
      expect(verification.uploaded).toEqual(['installer1.exe']);
      expect(verification.missing).toEqual(['installer2.dmg', 'SHA256SUMS.txt']);
    });
    
    it('should handle empty assets', () => {
      const release = {
        assets: [],
      };
      
      const expectedFiles = ['installer1.exe'];
      const verification = verifyUploadedAssets(release, expectedFiles);
      
      expect(verification.valid).toBe(false);
      expect(verification.uploaded).toEqual([]);
      expect(verification.missing).toEqual(['installer1.exe']);
    });
    
    it('should handle no expected files', () => {
      const release = {
        assets: [
          { name: 'installer1.exe' },
        ],
      };
      
      const expectedFiles = [];
      const verification = verifyUploadedAssets(release, expectedFiles);
      
      expect(verification.valid).toBe(true);
      expect(verification.uploaded).toEqual(['installer1.exe']);
      expect(verification.missing).toEqual([]);
    });
  });
  
  describe('Artifact Collection', () => {
    let testDir;
    
    beforeEach(() => {
      testDir = createTestDirectory();
    });
    
    afterEach(() => {
      cleanupTestDirectory(testDir);
    });
    
    it('should collect installer artifacts', () => {
      const releaseDir = path.join(testDir, 'release');
      fs.mkdirSync(releaseDir, { recursive: true });
      
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      createFile(releaseDir, 'PEFT Studio-1.0.0-x64.dmg', 'x'.repeat(2000));
      createFile(releaseDir, 'PEFT Studio-1.0.0-x64.AppImage', 'x'.repeat(3000));
      
      const artifacts = collectReleaseArtifacts(releaseDir);
      
      expect(artifacts.length).toBe(3);
      expect(artifacts.map(a => a.filename)).toContain('PEFT Studio-Setup-1.0.0.exe');
      expect(artifacts.map(a => a.filename)).toContain('PEFT Studio-1.0.0-x64.dmg');
      expect(artifacts.map(a => a.filename)).toContain('PEFT Studio-1.0.0-x64.AppImage');
    });
    
    it('should include SHA256SUMS.txt', () => {
      const releaseDir = path.join(testDir, 'release');
      fs.mkdirSync(releaseDir, { recursive: true });
      
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      createFile(releaseDir, 'SHA256SUMS.txt', 'checksums');
      
      const artifacts = collectReleaseArtifacts(releaseDir);
      
      expect(artifacts.length).toBe(2);
      expect(artifacts.map(a => a.filename)).toContain('SHA256SUMS.txt');
    });
    
    it('should exclude blockmap files', () => {
      const releaseDir = path.join(testDir, 'release');
      fs.mkdirSync(releaseDir, { recursive: true });
      
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe.blockmap', 'blockmap');
      
      const artifacts = collectReleaseArtifacts(releaseDir);
      
      expect(artifacts.length).toBe(1);
      expect(artifacts[0].filename).toBe('PEFT Studio-Setup-1.0.0.exe');
    });
    
    it('should exclude builder files', () => {
      const releaseDir = path.join(testDir, 'release');
      fs.mkdirSync(releaseDir, { recursive: true });
      
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      createFile(releaseDir, 'builder-debug.yml', 'debug');
      createFile(releaseDir, 'builder-effective-config.yaml', 'config');
      
      const artifacts = collectReleaseArtifacts(releaseDir);
      
      expect(artifacts.length).toBe(1);
      expect(artifacts[0].filename).toBe('PEFT Studio-Setup-1.0.0.exe');
    });
    
    it('should exclude latest.yml', () => {
      const releaseDir = path.join(testDir, 'release');
      fs.mkdirSync(releaseDir, { recursive: true });
      
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      createFile(releaseDir, 'latest.yml', 'latest');
      
      const artifacts = collectReleaseArtifacts(releaseDir);
      
      expect(artifacts.length).toBe(1);
      expect(artifacts[0].filename).toBe('PEFT Studio-Setup-1.0.0.exe');
    });
    
    it('should ignore directories', () => {
      const releaseDir = path.join(testDir, 'release');
      fs.mkdirSync(releaseDir, { recursive: true });
      fs.mkdirSync(path.join(releaseDir, 'win-unpacked'), { recursive: true });
      
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      createFile(path.join(releaseDir, 'win-unpacked'), 'app.exe', 'content');
      
      const artifacts = collectReleaseArtifacts(releaseDir);
      
      expect(artifacts.length).toBe(1);
      expect(artifacts[0].filename).toBe('PEFT Studio-Setup-1.0.0.exe');
    });
    
    it('should throw error if release directory does not exist', () => {
      const nonExistentDir = path.join(testDir, 'nonexistent');
      
      expect(() => {
        collectReleaseArtifacts(nonExistentDir);
      }).toThrow('Release directory not found');
    });
    
    it('should set artifact metadata correctly', () => {
      const releaseDir = path.join(testDir, 'release');
      fs.mkdirSync(releaseDir, { recursive: true });
      
      createFile(releaseDir, 'PEFT Studio-Setup-1.0.0.exe', 'x'.repeat(1000));
      
      const artifacts = collectReleaseArtifacts(releaseDir);
      
      expect(artifacts.length).toBe(1);
      expect(artifacts[0].filename).toBe('PEFT Studio-Setup-1.0.0.exe');
      expect(artifacts[0].path).toContain('PEFT Studio-Setup-1.0.0.exe');
      expect(artifacts[0].size).toBe(1000);
    });
  });
  
  describe('Release Summary Generation', () => {
    it('should generate a complete summary', () => {
      const release = {
        name: 'PEFT Studio v1.0.1',
        tag_name: 'v1.0.1',
        html_url: 'https://github.com/owner/repo/releases/tag/v1.0.1',
      };
      
      const artifacts = [
        { filename: 'installer1.exe', size: 50000000 },
        { filename: 'installer2.dmg', size: 60000000 },
        { filename: 'SHA256SUMS.txt', size: 1000 },
      ];
      
      const summary = generateReleaseSummary(release, artifacts);
      
      expect(summary).toContain('GitHub Release Summary');
      expect(summary).toContain('Release: PEFT Studio v1.0.1');
      expect(summary).toContain('Tag: v1.0.1');
      expect(summary).toContain('URL: https://github.com/owner/repo/releases/tag/v1.0.1');
      expect(summary).toContain('Assets (3)');
      expect(summary).toContain('installer1.exe');
      expect(summary).toContain('installer2.dmg');
      expect(summary).toContain('SHA256SUMS.txt');
    });
    
    it('should format file sizes in MB', () => {
      const release = {
        name: 'Test Release',
        tag_name: 'v1.0.0',
        html_url: 'https://github.com/test/test',
      };
      
      const artifacts = [
        { filename: 'file1.exe', size: 1024 * 1024 * 50 }, // 50 MB
        { filename: 'file2.dmg', size: 1024 * 1024 * 100 }, // 100 MB
      ];
      
      const summary = generateReleaseSummary(release, artifacts);
      
      expect(summary).toContain('50.00 MB');
      expect(summary).toContain('100.00 MB');
    });
    
    it('should handle empty artifacts', () => {
      const release = {
        name: 'Test Release',
        tag_name: 'v1.0.0',
        html_url: 'https://github.com/test/test',
      };
      
      const artifacts = [];
      
      const summary = generateReleaseSummary(release, artifacts);
      
      expect(summary).toContain('Assets (0)');
    });
  });
  
  describe('Configuration', () => {
    it('should have valid release configuration', () => {
      expect(RELEASE_CONFIG).toBeDefined();
      expect(RELEASE_CONFIG.maxRetries).toBeGreaterThan(0);
      expect(RELEASE_CONFIG.retryDelay).toBeGreaterThan(0);
      expect(RELEASE_CONFIG.changelogFile).toBe('CHANGELOG.md');
      expect(RELEASE_CONFIG.packageFile).toBe('package.json');
      expect(RELEASE_CONFIG.releaseDir).toBe('release');
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
    
    it('should handle malformed package.json', () => {
      const packagePath = createFile(testDir, 'package.json', 'invalid json');
      
      expect(() => {
        getVersion(packagePath);
      }).toThrow();
    });
    
    it('should handle malformed CHANGELOG.md', () => {
      const changelogPath = createFile(testDir, 'CHANGELOG.md', '');
      
      expect(() => {
        extractReleaseNotes('1.0.0', changelogPath);
      }).toThrow();
    });
    
    it('should handle empty release directory', () => {
      const releaseDir = path.join(testDir, 'release');
      fs.mkdirSync(releaseDir, { recursive: true });
      
      const artifacts = collectReleaseArtifacts(releaseDir);
      
      expect(artifacts).toEqual([]);
    });
  });
});
