/**
 * Property-Based Tests for Repository Metadata Update Module
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
  checkUrlConsistency,
  extractGitHubUrls,
  getMarkdownFiles,
  updatePackageJsonUrls,
  updatePackageJsonKeywords,
  replaceUrlsInFile,
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

/**
 * **Feature: repository-professionalization, Property 9: URL Consistency**
 * 
 * For any repository, all documentation files must reference the same repository URL.
 * 
 * **Validates: Requirements 9.3**
 */
describe('Property 9: URL Consistency', () => {
  it('should detect consistent URLs across all documentation', () => {
    fc.assert(
      fc.property(
        // Generate a valid GitHub repository URL
        fc.record({
          owner: fc.stringOf(fc.constantFrom('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'), { minLength: 3, maxLength: 20 }),
          repo: fc.stringOf(fc.constantFrom('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', '-'), { minLength: 3, maxLength: 30 }),
        }),
        ({ owner, repo }) => {
          const testDir = createTestDirectory();
          
          try {
            const repoUrl = `https://github.com/${owner}/${repo}`;
            
            // Create package.json with repository URL
            const packageJson = {
              name: 'test-package',
              version: '1.0.0',
              description: 'Test package',
              repository: {
                type: 'git',
                url: `${repoUrl}.git`,
              },
            };
            createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
            
            // Create multiple markdown files with the same URL
            const readmeContent = `# Test Project\n\nVisit [our repo](${repoUrl}) for more info.\n`;
            createFile(testDir, 'README.md', readmeContent);
            
            const contributingContent = `# Contributing\n\nSee [issues](${repoUrl}/issues) to contribute.\n`;
            createFile(testDir, 'CONTRIBUTING.md', contributingContent);
            
            const docsContent = `# Documentation\n\nCheck [releases](${repoUrl}/releases) for downloads.\n`;
            createFile(testDir, 'docs/guide.md', docsContent);
            
            // Check URL consistency
            const result = checkUrlConsistency(testDir);
            
            // Property: If all documentation files reference the same repository URL,
            // consistency check should pass
            expect(result.consistent).toBe(true);
            expect(result.inconsistencies.length).toBe(0);
            
          } finally {
            cleanupTestDirectory(testDir);
          }
        }
      ),
      { numRuns: 100 }
    );
  });
  
  it('should detect placeholder URLs that need replacement', () => {
    fc.assert(
      fc.property(
        // Generate repository URL with placeholder owner
        fc.record({
          placeholder: fc.constantFrom('your-org', 'yourusername', 'YOUR_ORG', 'your-username'),
          repo: fc.stringOf(fc.constantFrom('a', 'b', 'c', 'd', 'e'), { minLength: 3, maxLength: 10 }),
        }),
        ({ placeholder, repo }) => {
          const testDir = createTestDirectory();
          
          try {
            const actualOwner = 'actual-owner';
            const repoUrl = `https://github.com/${actualOwner}/${repo}`;
            const placeholderUrl = `https://github.com/${placeholder}/${repo}`;
            
            // Create package.json with actual repository URL
            const packageJson = {
              name: 'test-package',
              version: '1.0.0',
              repository: {
                type: 'git',
                url: `${repoUrl}.git`,
              },
            };
            createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
            
            // Create README with actual URL
            const readmeContent = `# Test\n\nVisit [repo](${repoUrl}).\n`;
            createFile(testDir, 'README.md', readmeContent);
            
            // Create CONTRIBUTING with placeholder URL (should be flagged)
            const contributingContent = `# Contributing\n\nSee [issues](${placeholderUrl}/issues).\n`;
            createFile(testDir, 'CONTRIBUTING.md', contributingContent);
            
            // Check URL consistency
            const result = checkUrlConsistency(testDir);
            
            // Property: If documentation files contain placeholder URLs,
            // consistency check should fail
            expect(result.consistent).toBe(false);
            expect(result.inconsistencies.length).toBeGreaterThan(0);
            
          } finally {
            cleanupTestDirectory(testDir);
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should extract GitHub URLs correctly from markdown content', () => {
    fc.assert(
      fc.property(
        fc.record({
          owner: fc.stringOf(fc.constantFrom('a', 'b', 'c', 'd'), { minLength: 3, maxLength: 10 }),
          repo: fc.stringOf(fc.constantFrom('a', 'b', 'c', 'd'), { minLength: 3, maxLength: 10 }),
          path: fc.option(fc.constantFrom('/issues', '/releases', '/wiki', '/blob/main/README.md'), { nil: '' }),
        }),
        ({ owner, repo, path }) => {
          const url = `https://github.com/${owner}/${repo}${path || ''}`;
          const content = `Check out [this link](${url}) for more info.`;
          
          // Extract URLs
          const urls = extractGitHubUrls(content);
          
          // Property: Extracted URLs should include the URL we embedded
          const normalizedUrl = url.replace(/\.git$/, '').replace(/\/$/, '');
          const normalizedExtracted = urls.map(u => u.replace(/\.git$/, '').replace(/\/$/, ''));
          
          expect(normalizedExtracted).toContain(normalizedUrl.split('#')[0].split('?')[0]);
        }
      ),
      { numRuns: 100 }
    );
  });
  
  it('should normalize URLs consistently', () => {
    fc.assert(
      fc.property(
        fc.record({
          owner: fc.stringOf(fc.constantFrom('a', 'b', 'c'), { minLength: 3, maxLength: 8 }),
          repo: fc.stringOf(fc.constantFrom('a', 'b', 'c'), { minLength: 3, maxLength: 8 }),
          suffix: fc.constantFrom('', '.git', '/', '/.git'),
        }),
        ({ owner, repo, suffix }) => {
          const baseUrl = `https://github.com/${owner}/${repo}`;
          const urlWithSuffix = `${baseUrl}${suffix}`;
          
          const content = `Link: ${urlWithSuffix}`;
          const urls = extractGitHubUrls(content);
          
          // Property: All variations of the same URL should normalize to the same value
          const normalized = urls.map(u => u.replace(/\.git$/, '').replace(/\/$/, ''));
          
          expect(normalized).toContain(baseUrl);
        }
      ),
      { numRuns: 100 }
    );
  });
});
