/**
 * Unit Tests for Documentation Enhancer Module
 * 
 * Tests badge generation, README updates, metadata updates,
 * and documentation verification.
 * 
 * Requirements: 5.2, 6.1, 6.2, 6.4
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const {
  generateBadges,
  updateReadmeBadges,
  verifyDocumentation,
  updatePackageMetadata,
  enhanceDocumentation,
  extractBadgesFromReadme,
  validateMarkdownFormatting,
  checkRequiredDocFiles,
  REQUIRED_DOCS,
  BADGE_TEMPLATES,
} = require('../enhance-documentation');

/**
 * Helper: Create a temporary test directory
 */
function createTestDirectory() {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'docs-test-'));
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

describe('Documentation Enhancer Module - Unit Tests', () => {
  describe('Badge Generation', () => {
    it('should generate version badge', () => {
      const badges = generateBadges({
        version: '1.0.1',
        repository: 'Ankesh-007/peft-studio',
        license: 'MIT',
      });
      
      expect(badges.version).toContain('Ankesh-007/peft-studio');
      expect(badges.version).toContain('img.shields.io');
      expect(badges.version).toContain('release');
    });
    
    it('should generate license badge', () => {
      const badges = generateBadges({
        version: '1.0.0',
        repository: 'user/repo',
        license: 'MIT',
      });
      
      expect(badges.license).toContain('MIT');
      expect(badges.license).toContain('License');
      expect(badges.license).toContain('yellow');
    });
    
    it('should generate downloads badge', () => {
      const badges = generateBadges({
        version: '1.0.0',
        repository: 'user/repo',
        license: 'MIT',
      });
      
      expect(badges.downloads).toContain('downloads');
      expect(badges.downloads).toContain('user/repo');
      expect(badges.downloads).toContain('total');
    });
    
    it('should handle different license types', () => {
      const mitBadges = generateBadges({
        version: '1.0.0',
        repository: 'user/repo',
        license: 'MIT',
      });
      
      const apacheBadges = generateBadges({
        version: '1.0.0',
        repository: 'user/repo',
        license: 'Apache-2.0',
      });
      
      expect(mitBadges.license).toContain('MIT');
      expect(apacheBadges.license).toContain('Apache-2.0');
    });
    
    it('should generate all required badges', () => {
      const badges = generateBadges({
        version: '1.0.0',
        repository: 'user/repo',
        license: 'MIT',
      });
      
      expect(badges).toHaveProperty('version');
      expect(badges).toHaveProperty('license');
      expect(badges).toHaveProperty('downloads');
      expect(Object.keys(badges).length).toBe(3);
    });
  });
  
  describe('README Badge Updates', () => {
    let testDir;
    
    beforeEach(() => {
      testDir = createTestDirectory();
    });
    
    afterEach(() => {
      cleanupTestDirectory(testDir);
    });
    
    it('should add badges to README without badges', () => {
      const readmeContent = '# My Project\n\nThis is a test project.';
      createFile(testDir, 'README.md', readmeContent);
      
      const result = updateReadmeBadges(testDir, {
        version: '1.0.0',
        repository: 'user/repo',
        license: 'MIT',
      }, false);
      
      expect(result.updated).toBe(true);
      
      const updatedContent = fs.readFileSync(path.join(testDir, 'README.md'), 'utf8');
      expect(updatedContent).toContain('License: MIT');
      expect(updatedContent).toContain('downloads');
      expect(updatedContent).toContain('release');
    });
    
    it('should update existing badges', () => {
      const readmeContent = `# My Project

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/user/repo)](https://github.com/user/repo/releases/latest)

This is a test project.`;
      
      createFile(testDir, 'README.md', readmeContent);
      
      const result = updateReadmeBadges(testDir, {
        version: '2.0.0',
        repository: 'user/newrepo',
        license: 'Apache-2.0',
      }, false);
      
      expect(result.updated).toBe(true);
      
      const updatedContent = fs.readFileSync(path.join(testDir, 'README.md'), 'utf8');
      expect(updatedContent).toContain('Apache-2.0');
      expect(updatedContent).toContain('user/newrepo');
    });
    
    it('should not modify README in dry-run mode', () => {
      const readmeContent = '# My Project\n\nThis is a test project.';
      createFile(testDir, 'README.md', readmeContent);
      
      const result = updateReadmeBadges(testDir, {
        version: '1.0.0',
        repository: 'user/repo',
        license: 'MIT',
      }, true);
      
      expect(result.updated).toBe(true);
      
      const content = fs.readFileSync(path.join(testDir, 'README.md'), 'utf8');
      expect(content).toBe(readmeContent);
    });
    
    it('should preserve README structure when adding badges', () => {
      const readmeContent = `# My Project

## Features

- Feature 1
- Feature 2`;
      
      createFile(testDir, 'README.md', readmeContent);
      
      updateReadmeBadges(testDir, {
        version: '1.0.0',
        repository: 'user/repo',
        license: 'MIT',
      }, false);
      
      const updatedContent = fs.readFileSync(path.join(testDir, 'README.md'), 'utf8');
      expect(updatedContent).toContain('## Features');
      expect(updatedContent).toContain('- Feature 1');
    });
    
    it('should extract existing badges from README', () => {
      const readmeContent = `# My Project

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Downloads](https://img.shields.io/github/downloads/user/repo/total)](https://github.com/user/repo/releases)

Description`;
      
      const badges = extractBadgesFromReadme(readmeContent);
      
      expect(badges.length).toBeGreaterThan(0);
      expect(badges.some(b => b.includes('License'))).toBe(true);
      expect(badges.some(b => b.includes('Downloads'))).toBe(true);
    });
  });
  
  describe('Documentation Verification', () => {
    let testDir;
    
    beforeEach(() => {
      testDir = createTestDirectory();
    });
    
    afterEach(() => {
      cleanupTestDirectory(testDir);
    });
    
    it('should verify all required documentation files exist', () => {
      // Create all required files
      createFile(testDir, 'README.md', '# Project');
      createFile(testDir, 'LICENSE', 'MIT License');
      createFile(testDir, 'CONTRIBUTING.md', '# Contributing');
      createFile(testDir, 'CHANGELOG.md', '# Changelog');
      
      const result = verifyDocumentation(testDir);
      
      expect(result.valid).toBe(true);
      expect(result.missingDocs).toHaveLength(0);
    });
    
    it('should detect missing documentation files', () => {
      createFile(testDir, 'README.md', '# Project');
      // Missing LICENSE, CONTRIBUTING.md, CHANGELOG.md
      
      const result = verifyDocumentation(testDir);
      
      expect(result.valid).toBe(false);
      expect(result.missingDocs.length).toBeGreaterThan(0);
      expect(result.missingDocs).toContain('LICENSE');
    });
    
    it('should validate README completeness', () => {
      const incompleteReadme = '# Project\n\nShort description.';
      createFile(testDir, 'README.md', incompleteReadme);
      createFile(testDir, 'LICENSE', 'MIT');
      createFile(testDir, 'CONTRIBUTING.md', '# Contributing');
      createFile(testDir, 'CHANGELOG.md', '# Changelog');
      
      const result = verifyDocumentation(testDir);
      
      expect(result.readmeComplete).toBe(false);
    });
    
    it('should validate README has required sections', () => {
      const completeReadme = `# Project

## Features
- Feature 1

## Installation
Install instructions

## Usage
Usage instructions

## Contributing
See CONTRIBUTING.md

## License
MIT`;
      
      createFile(testDir, 'README.md', completeReadme);
      createFile(testDir, 'LICENSE', 'MIT');
      createFile(testDir, 'CONTRIBUTING.md', '# Contributing');
      createFile(testDir, 'CHANGELOG.md', '# Changelog');
      
      const result = verifyDocumentation(testDir);
      
      expect(result.readmeComplete).toBe(true);
    });
    
    it('should check LICENSE file exists', () => {
      createFile(testDir, 'README.md', '# Project');
      createFile(testDir, 'LICENSE', 'MIT License');
      createFile(testDir, 'CONTRIBUTING.md', '# Contributing');
      createFile(testDir, 'CHANGELOG.md', '# Changelog');
      
      const result = verifyDocumentation(testDir);
      
      expect(result.licenseExists).toBe(true);
    });
    
    it('should check CONTRIBUTING.md exists', () => {
      createFile(testDir, 'README.md', '# Project');
      createFile(testDir, 'LICENSE', 'MIT');
      createFile(testDir, 'CONTRIBUTING.md', '# Contributing Guide');
      createFile(testDir, 'CHANGELOG.md', '# Changelog');
      
      const result = verifyDocumentation(testDir);
      
      expect(result.contributingExists).toBe(true);
    });
    
    it('should validate markdown formatting', () => {
      const wellFormatted = `# Title

## Section

Paragraph with proper spacing.

- List item 1
- List item 2

## Another Section

More content.`;
      
      const result = validateMarkdownFormatting(wellFormatted);
      
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });
    
    it('should detect markdown formatting issues', () => {
      const poorlyFormatted = `#Title
##Section
No spacing between sections.
-List item
-Another item`;
      
      const result = validateMarkdownFormatting(poorlyFormatted);
      
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });
  });
  
  describe('Package Metadata Updates', () => {
    let testDir;
    
    beforeEach(() => {
      testDir = createTestDirectory();
    });
    
    afterEach(() => {
      cleanupTestDirectory(testDir);
    });
    
    it('should update package.json metadata', () => {
      const packageJson = {
        name: 'test-project',
        version: '1.0.0',
        description: 'Old description',
      };
      
      createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
      
      const updates = {
        description: 'New description',
        repository: {
          type: 'git',
          url: 'https://github.com/user/repo.git',
        },
        keywords: ['test', 'project'],
        author: 'Test Author',
      };
      
      const result = updatePackageMetadata(testDir, updates, false);
      
      expect(result.updated).toBe(true);
      
      const updatedPackage = JSON.parse(
        fs.readFileSync(path.join(testDir, 'package.json'), 'utf8')
      );
      
      expect(updatedPackage.description).toBe('New description');
      expect(updatedPackage.repository.url).toBe('https://github.com/user/repo.git');
      expect(updatedPackage.keywords).toContain('test');
    });
    
    it('should preserve existing package.json fields', () => {
      const packageJson = {
        name: 'test-project',
        version: '1.0.0',
        description: 'Test',
        dependencies: {
          react: '^18.0.0',
        },
        scripts: {
          test: 'vitest',
        },
      };
      
      createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
      
      const updates = {
        description: 'Updated description',
      };
      
      updatePackageMetadata(testDir, updates, false);
      
      const updatedPackage = JSON.parse(
        fs.readFileSync(path.join(testDir, 'package.json'), 'utf8')
      );
      
      expect(updatedPackage.dependencies).toEqual({ react: '^18.0.0' });
      expect(updatedPackage.scripts).toEqual({ test: 'vitest' });
    });
    
    it('should not modify package.json in dry-run mode', () => {
      const packageJson = {
        name: 'test-project',
        version: '1.0.0',
      };
      
      const originalContent = JSON.stringify(packageJson, null, 2);
      createFile(testDir, 'package.json', originalContent);
      
      const updates = {
        description: 'New description',
      };
      
      updatePackageMetadata(testDir, updates, true);
      
      const content = fs.readFileSync(path.join(testDir, 'package.json'), 'utf8');
      expect(content).toBe(originalContent);
    });
    
    it('should add repository URLs if missing', () => {
      const packageJson = {
        name: 'test-project',
        version: '1.0.0',
      };
      
      createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
      
      const updates = {
        repository: {
          type: 'git',
          url: 'https://github.com/user/repo.git',
        },
        homepage: 'https://github.com/user/repo#readme',
        bugs: {
          url: 'https://github.com/user/repo/issues',
        },
      };
      
      updatePackageMetadata(testDir, updates, false);
      
      const updatedPackage = JSON.parse(
        fs.readFileSync(path.join(testDir, 'package.json'), 'utf8')
      );
      
      expect(updatedPackage.repository).toBeDefined();
      expect(updatedPackage.homepage).toBeDefined();
      expect(updatedPackage.bugs).toBeDefined();
    });
    
    it('should add keywords if missing', () => {
      const packageJson = {
        name: 'test-project',
        version: '1.0.0',
      };
      
      createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
      
      const updates = {
        keywords: ['machine-learning', 'ai', 'peft'],
      };
      
      updatePackageMetadata(testDir, updates, false);
      
      const updatedPackage = JSON.parse(
        fs.readFileSync(path.join(testDir, 'package.json'), 'utf8')
      );
      
      expect(updatedPackage.keywords).toEqual(['machine-learning', 'ai', 'peft']);
    });
  });
  
  describe('Complete Documentation Enhancement', () => {
    let testDir;
    
    beforeEach(() => {
      testDir = createTestDirectory();
    });
    
    afterEach(() => {
      cleanupTestDirectory(testDir);
    });
    
    it('should perform complete documentation enhancement', () => {
      // Create minimal project structure
      const packageJson = {
        name: 'test-project',
        version: '1.0.0',
        description: 'Test project',
        license: 'MIT',
      };
      
      createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
      createFile(testDir, 'README.md', '# Test Project\n\nA test project.');
      createFile(testDir, 'LICENSE', 'MIT License');
      createFile(testDir, 'CONTRIBUTING.md', '# Contributing');
      createFile(testDir, 'CHANGELOG.md', '# Changelog');
      
      const result = enhanceDocumentation(testDir, false);
      
      expect(result.success).toBe(true);
      expect(result.badgesUpdated).toBe(true);
      expect(result.metadataUpdated).toBe(true);
      expect(result.verification.valid).toBe(true);
    });
    
    it('should report missing documentation files', () => {
      const packageJson = {
        name: 'test-project',
        version: '1.0.0',
      };
      
      createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
      createFile(testDir, 'README.md', '# Test');
      
      const result = enhanceDocumentation(testDir, false);
      
      expect(result.verification.valid).toBe(false);
      expect(result.verification.missingDocs.length).toBeGreaterThan(0);
    });
    
    it('should not modify files in dry-run mode', () => {
      const packageJson = {
        name: 'test-project',
        version: '1.0.0',
      };
      
      const readmeContent = '# Test Project';
      
      createFile(testDir, 'package.json', JSON.stringify(packageJson, null, 2));
      createFile(testDir, 'README.md', readmeContent);
      createFile(testDir, 'LICENSE', 'MIT');
      createFile(testDir, 'CONTRIBUTING.md', '# Contributing');
      createFile(testDir, 'CHANGELOG.md', '# Changelog');
      
      const result = enhanceDocumentation(testDir, true);
      
      expect(result.success).toBe(true);
      
      const readme = fs.readFileSync(path.join(testDir, 'README.md'), 'utf8');
      expect(readme).toBe(readmeContent);
    });
  });
  
  describe('Required Documentation Files', () => {
    it('should have correct required documentation list', () => {
      expect(REQUIRED_DOCS).toContain('README.md');
      expect(REQUIRED_DOCS).toContain('LICENSE');
      expect(REQUIRED_DOCS).toContain('CONTRIBUTING.md');
      expect(REQUIRED_DOCS).toContain('CHANGELOG.md');
    });
    
    it('should check for all required files', () => {
      const testDir = createTestDirectory();
      
      try {
        createFile(testDir, 'README.md', '# Test');
        
        const missing = checkRequiredDocFiles(testDir);
        
        expect(missing.length).toBeGreaterThan(0);
        expect(missing).toContain('LICENSE');
        expect(missing).toContain('CONTRIBUTING.md');
      } finally {
        cleanupTestDirectory(testDir);
      }
    });
  });
  
  describe('Badge Templates', () => {
    it('should have badge templates defined', () => {
      expect(BADGE_TEMPLATES).toHaveProperty('version');
      expect(BADGE_TEMPLATES).toHaveProperty('license');
      expect(BADGE_TEMPLATES).toHaveProperty('downloads');
    });
    
    it('should generate valid badge markdown', () => {
      const badges = generateBadges({
        version: '1.0.0',
        repository: 'user/repo',
        license: 'MIT',
      });
      
      // Badges should be markdown format with URLs inside
      expect(badges.version).toContain('https://');
      expect(badges.license).toContain('https://');
      expect(badges.downloads).toContain('https://');
      
      // Should be markdown badge format
      expect(badges.version).toMatch(/^\[!\[.*\]\(.*\)\]\(.*\)$/);
      expect(badges.license).toMatch(/^\[!\[.*\]\(.*\)\]\(.*\)$/);
      expect(badges.downloads).toMatch(/^\[!\[.*\]\(.*\)\]\(.*\)$/);
    });
  });
  
  describe('Link Validation', () => {
    const {
      extractLinksFromMarkdown,
      validateDocumentationLinks,
    } = require('../enhance-documentation');
    
    let testDir;
    
    beforeEach(() => {
      testDir = createTestDirectory();
    });
    
    afterEach(() => {
      cleanupTestDirectory(testDir);
    });
    
    it('should extract markdown links from content', () => {
      const content = `# Title
      
[Link 1](https://example.com)
[Link 2](docs/guide.md)
[Link 3](#anchor)`;
      
      const links = extractLinksFromMarkdown(content);
      
      expect(links.length).toBe(3);
      expect(links[0].url).toBe('https://example.com');
      expect(links[1].url).toBe('docs/guide.md');
      expect(links[2].url).toBe('#anchor');
    });
    
    it('should extract HTML links from content', () => {
      const content = `# Title
      
<a href="https://example.com">Link 1</a>
<a href="docs/guide.md">Link 2</a>`;
      
      const links = extractLinksFromMarkdown(content);
      
      expect(links.length).toBe(2);
      expect(links[0].url).toBe('https://example.com');
      expect(links[0].type).toBe('html');
    });
    
    it('should validate all links are valid when files exist', () => {
      const readmeContent = `# Project

[Guide](docs/guide.md)
[License](LICENSE)`;
      
      createFile(testDir, 'README.md', readmeContent);
      createFile(testDir, 'docs/guide.md', '# Guide');
      createFile(testDir, 'LICENSE', 'MIT');
      
      const result = validateDocumentationLinks(testDir);
      
      expect(result.valid).toBe(true);
      expect(result.brokenLinks).toHaveLength(0);
      expect(result.totalLinks).toBe(2);
      expect(result.validLinks).toBe(2);
    });
    
    it('should detect broken local links', () => {
      const readmeContent = `# Project

[Missing Guide](docs/missing.md)
[Existing License](LICENSE)`;
      
      createFile(testDir, 'README.md', readmeContent);
      createFile(testDir, 'LICENSE', 'MIT');
      
      const result = validateDocumentationLinks(testDir);
      
      expect(result.valid).toBe(false);
      expect(result.brokenLinks.length).toBe(1);
      expect(result.brokenLinks[0].url).toBe('docs/missing.md');
      expect(result.brokenLinks[0].file).toBe('README.md');
    });
    
    it('should skip external URLs in validation', () => {
      const readmeContent = `# Project

[External](https://github.com/user/repo)
[Another External](http://example.com)`;
      
      createFile(testDir, 'README.md', readmeContent);
      
      const result = validateDocumentationLinks(testDir);
      
      expect(result.valid).toBe(true);
      expect(result.totalLinks).toBe(2);
      expect(result.validLinks).toBe(2);
    });
    
    it('should skip anchor links in validation', () => {
      const readmeContent = `# Project

[Section 1](#section-1)
[Section 2](#section-2)`;
      
      createFile(testDir, 'README.md', readmeContent);
      
      const result = validateDocumentationLinks(testDir);
      
      expect(result.valid).toBe(true);
      expect(result.totalLinks).toBe(2);
    });
    
    it('should validate links in CONTRIBUTING.md', () => {
      const contributingContent = `# Contributing

[Code of Conduct](CODE_OF_CONDUCT.md)
[Missing File](missing.md)`;
      
      createFile(testDir, 'README.md', '# Project');
      createFile(testDir, 'CONTRIBUTING.md', contributingContent);
      createFile(testDir, 'CODE_OF_CONDUCT.md', '# Code of Conduct');
      
      const result = validateDocumentationLinks(testDir);
      
      expect(result.valid).toBe(false);
      expect(result.brokenLinks.length).toBe(1);
      expect(result.brokenLinks[0].file).toBe('CONTRIBUTING.md');
      expect(result.brokenLinks[0].url).toBe('missing.md');
    });
    
    it('should handle README with no links', () => {
      const readmeContent = '# Project\n\nNo links here.';
      
      createFile(testDir, 'README.md', readmeContent);
      
      const result = validateDocumentationLinks(testDir);
      
      expect(result.valid).toBe(true);
      expect(result.totalLinks).toBe(0);
      expect(result.validLinks).toBe(0);
      expect(result.brokenLinks).toHaveLength(0);
    });
  });
  
  describe('Screenshot/Image Checking', () => {
    const { checkReadmeImages } = require('../enhance-documentation');
    
    let testDir;
    
    beforeEach(() => {
      testDir = createTestDirectory();
    });
    
    afterEach(() => {
      cleanupTestDirectory(testDir);
    });
    
    it('should detect images in README', () => {
      const readmeContent = `# Project

![Screenshot](docs/screenshot.png)
![Demo](demo.gif)`;
      
      createFile(testDir, 'README.md', readmeContent);
      
      const result = checkReadmeImages(testDir);
      
      expect(result.hasImages).toBe(true);
      expect(result.imageCount).toBe(2);
      expect(result.images.length).toBe(2);
      expect(result.images[0].alt).toBe('Screenshot');
      expect(result.images[0].url).toBe('docs/screenshot.png');
    });
    
    it('should detect missing local images', () => {
      const readmeContent = `# Project

![Existing](existing.png)
![Missing](missing.png)`;
      
      createFile(testDir, 'README.md', readmeContent);
      createFile(testDir, 'existing.png', 'fake image data');
      
      const result = checkReadmeImages(testDir);
      
      expect(result.hasImages).toBe(true);
      expect(result.imageCount).toBe(2);
      expect(result.missingImages.length).toBe(1);
      expect(result.missingImages[0].url).toBe('missing.png');
    });
    
    it('should not flag external images as missing', () => {
      const readmeContent = `# Project

![External](https://example.com/image.png)
![Another](http://example.com/demo.gif)`;
      
      createFile(testDir, 'README.md', readmeContent);
      
      const result = checkReadmeImages(testDir);
      
      expect(result.hasImages).toBe(true);
      expect(result.imageCount).toBe(2);
      expect(result.missingImages).toHaveLength(0);
    });
    
    it('should handle README with no images', () => {
      const readmeContent = '# Project\n\nNo images here.';
      
      createFile(testDir, 'README.md', readmeContent);
      
      const result = checkReadmeImages(testDir);
      
      expect(result.hasImages).toBe(false);
      expect(result.imageCount).toBe(0);
      expect(result.images).toHaveLength(0);
    });
    
    it('should handle missing README', () => {
      const result = checkReadmeImages(testDir);
      
      expect(result.hasImages).toBe(false);
      expect(result.imageCount).toBe(0);
    });
    
    it('should extract image alt text correctly', () => {
      const readmeContent = `# Project

![Application Screenshot](screenshot.png)
![](no-alt.png)`;
      
      createFile(testDir, 'README.md', readmeContent);
      
      const result = checkReadmeImages(testDir);
      
      expect(result.images[0].alt).toBe('Application Screenshot');
      expect(result.images[1].alt).toBe('');
    });
  });
  
  describe('Documentation Completeness Checks', () => {
    let testDir;
    
    beforeEach(() => {
      testDir = createTestDirectory();
    });
    
    afterEach(() => {
      cleanupTestDirectory(testDir);
    });
    
    it('should check installation instructions are complete', () => {
      const readmeWithInstall = `# Project

## Features
Great features

## Installation

\`\`\`bash
npm install
\`\`\`

## Usage

Run the app.

## Contributing

See CONTRIBUTING.md

## License

MIT`;
      
      createFile(testDir, 'README.md', readmeWithInstall);
      createFile(testDir, 'LICENSE', 'MIT');
      createFile(testDir, 'CONTRIBUTING.md', '# Contributing');
      createFile(testDir, 'CHANGELOG.md', '# Changelog');
      
      const result = verifyDocumentation(testDir);
      
      expect(result.readmeComplete).toBe(true);
    });
    
    it('should report when installation section is missing', () => {
      const readmeWithoutInstall = `# Project

## Usage

Run the app.`;
      
      createFile(testDir, 'README.md', readmeWithoutInstall);
      createFile(testDir, 'LICENSE', 'MIT');
      createFile(testDir, 'CONTRIBUTING.md', '# Contributing');
      createFile(testDir, 'CHANGELOG.md', '# Changelog');
      
      const result = verifyDocumentation(testDir);
      
      expect(result.readmeComplete).toBe(false);
      expect(result.missingSections).toContain('Installation');
    });
    
    it('should include link validation in overall verification', () => {
      const readmeContent = `# Project

## Features
Great features

## Installation
Install it

## Usage
Use it

## Contributing
See [CONTRIBUTING](CONTRIBUTING.md)

## License
MIT

[Broken Link](missing.md)`;
      
      createFile(testDir, 'README.md', readmeContent);
      createFile(testDir, 'LICENSE', 'MIT');
      createFile(testDir, 'CONTRIBUTING.md', '# Contributing');
      createFile(testDir, 'CHANGELOG.md', '# Changelog');
      
      const result = verifyDocumentation(testDir);
      
      expect(result.readmeComplete).toBe(true);
      expect(result.linksValid).toBe(false);
      expect(result.valid).toBe(false);
      expect(result.brokenLinks.length).toBe(1);
    });
    
    it('should include image info in verification', () => {
      const readmeContent = `# Project

![Screenshot](screenshot.png)

## Features
Great features

## Installation
Install it

## Usage
Use it

## Contributing
See CONTRIBUTING.md

## License
MIT`;
      
      createFile(testDir, 'README.md', readmeContent);
      createFile(testDir, 'LICENSE', 'MIT');
      createFile(testDir, 'CONTRIBUTING.md', '# Contributing');
      createFile(testDir, 'CHANGELOG.md', '# Changelog');
      
      const result = verifyDocumentation(testDir);
      
      expect(result.hasScreenshots).toBe(true);
      expect(result.imageInfo).toBeDefined();
      expect(result.imageInfo.imageCount).toBe(1);
    });
  });
});
