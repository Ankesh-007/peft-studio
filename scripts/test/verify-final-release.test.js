/**
 * Unit tests for verify-final-release.js
 * 
 * Tests the final release verification functionality including:
 * - GitHub release verification
 * - Download link testing
 * - Checksum verification
 * - Repository professionalism checks
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';

// Mock modules
vi.mock('fs');
vi.mock('child_process');

import {
  verifyRepositoryProfessionalism,
  generateVerificationReport,
} from '../verify-final-release.js';

describe('verify-final-release', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('verifyRepositoryProfessionalism', () => {
    it('should pass when all required files exist with proper content', () => {
      // Mock file system
      fs.existsSync = vi.fn((filePath) => {
        const validFiles = ['README.md', 'LICENSE', 'CONTRIBUTING.md', 'CHANGELOG.md', '.gitignore', 'package.json'];
        return validFiles.some(file => filePath.includes(file));
      });

      fs.readFileSync = vi.fn((filePath) => {
        if (filePath.includes('README.md')) {
          return '# Project Title\n\nA great description that is long enough.\n\n## Installation\n\n## Usage\n\n## License\n\n![badge](url)';
        }
        if (filePath.includes('LICENSE')) {
          return 'MIT License\n\nCopyright (c) 2024\n\nPermission is hereby granted...'.repeat(10);
        }
        if (filePath.includes('CHANGELOG.md')) {
          return '# Changelog\n\n## [1.0.1] - 2024-01-01';
        }
        if (filePath.includes('.gitignore')) {
          return 'node_modules\ndist\n*.log\nrelease';
        }
        if (filePath.includes('package.json')) {
          return JSON.stringify({
            name: 'test-app',
            version: '1.0.1',
            description: 'Test app',
            author: 'Test Author',
            license: 'MIT',
            repository: 'https://github.com/test/repo',
            keywords: ['test', 'app'],
          });
        }
        return '';
      });

      const result = verifyRepositoryProfessionalism();

      expect(result.valid).toBe(true);
      expect(result.checks.license).toBe(true);
      expect(result.checks.contributing).toBe(true);
      expect(result.checks.changelog).toBe(true);
      expect(result.checks.gitignore).toBe(true);
      expect(result.checks.packageMetadata).toBe(true);
      expect(result.checks.keywords).toBe(true);
    });

    it('should fail when README.md is missing', () => {
      fs.existsSync = vi.fn((filePath) => {
        return !filePath.includes('README.md');
      });

      fs.readFileSync = vi.fn(() => '');

      const result = verifyRepositoryProfessionalism();

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('README.md is missing');
    });

    it('should detect missing README sections', () => {
      fs.existsSync = vi.fn(() => true);

      fs.readFileSync = vi.fn((filePath) => {
        if (filePath.includes('README.md')) {
          return '# Title\n\nShort description';
        }
        if (filePath.includes('package.json')) {
          return JSON.stringify({
            name: 'test',
            version: '1.0.0',
            description: 'test',
            author: 'test',
            license: 'MIT',
            repository: 'test',
          });
        }
        return 'content';
      });

      const result = verifyRepositoryProfessionalism();

      expect(result.checks['Installation']).toBe(false);
      expect(result.checks['Usage']).toBe(false);
      expect(result.errors.some(e => e.includes('README missing sections'))).toBe(true);
    });

    it('should detect missing LICENSE file', () => {
      fs.existsSync = vi.fn((filePath) => {
        return !filePath.includes('LICENSE');
      });

      fs.readFileSync = vi.fn((filePath) => {
        if (filePath.includes('package.json')) {
          return JSON.stringify({ name: 'test', version: '1.0.0' });
        }
        return '';
      });

      const result = verifyRepositoryProfessionalism();

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('LICENSE is missing');
    });

    it('should detect missing .gitignore patterns', () => {
      fs.existsSync = vi.fn(() => true);

      fs.readFileSync = vi.fn((filePath) => {
        if (filePath.includes('.gitignore')) {
          return 'node_modules\n*.log';
        }
        if (filePath.includes('package.json')) {
          return JSON.stringify({
            name: 'test',
            version: '1.0.0',
            description: 'test',
            author: 'test',
            license: 'MIT',
            repository: 'test',
          });
        }
        return 'content';
      });

      const result = verifyRepositoryProfessionalism();

      expect(result.checks.gitignore).toBe(false);
    });

    it('should detect missing package.json metadata fields', () => {
      fs.existsSync = vi.fn(() => true);

      fs.readFileSync = vi.fn((filePath) => {
        if (filePath.includes('package.json')) {
          return JSON.stringify({
            name: 'test',
            version: '1.0.0',
            // Missing description, author, license, repository
          });
        }
        return 'content';
      });

      const result = verifyRepositoryProfessionalism();

      expect(result.checks.packageMetadata).toBe(false);
    });

    it('should detect missing keywords', () => {
      fs.existsSync = vi.fn(() => true);

      fs.readFileSync = vi.fn((filePath) => {
        if (filePath.includes('package.json')) {
          return JSON.stringify({
            name: 'test',
            version: '1.0.0',
            description: 'test',
            author: 'test',
            license: 'MIT',
            repository: 'test',
            // No keywords
          });
        }
        return 'content';
      });

      const result = verifyRepositoryProfessionalism();

      expect(result.checks.keywords).toBe(false);
    });

    it('should verify CHANGELOG contains current version', () => {
      fs.existsSync = vi.fn(() => true);

      fs.readFileSync = vi.fn((filePath) => {
        if (filePath.includes('CHANGELOG.md')) {
          return '# Changelog\n\n## [1.0.1] - 2024-01-01\n\nChanges...';
        }
        if (filePath.includes('package.json')) {
          return JSON.stringify({
            name: 'test',
            version: '1.0.1',
            description: 'test',
            author: 'test',
            license: 'MIT',
            repository: 'test',
          });
        }
        return 'content';
      });

      const result = verifyRepositoryProfessionalism();

      expect(result.checks.changelog).toBe(true);
    });

    it('should detect when CHANGELOG is missing current version', () => {
      fs.existsSync = vi.fn(() => true);

      fs.readFileSync = vi.fn((filePath) => {
        if (filePath.includes('CHANGELOG.md')) {
          return '# Changelog\n\n## [1.0.0] - 2024-01-01\n\nOld version...';
        }
        if (filePath.includes('package.json')) {
          return JSON.stringify({
            name: 'test',
            version: '1.0.1',
            description: 'test',
            author: 'test',
            license: 'MIT',
            repository: 'test',
          });
        }
        return 'content';
      });

      const result = verifyRepositoryProfessionalism();

      expect(result.checks.changelog).toBe(false);
    });
  });

  describe('generateVerificationReport', () => {
    it('should generate a complete report with all sections', () => {
      const results = {
        version: '1.0.1',
        release: {
          releaseExists: true,
          valid: true,
          errors: [],
          release: {
            html_url: 'https://github.com/test/repo/releases/tag/v1.0.1',
            assets: [
              { name: 'installer.exe', size: 1024 },
              { name: 'app.dmg', size: 2048 },
            ],
            draft: false,
            prerelease: false,
          },
        },
        downloads: {
          tested: 2,
          accessible: 2,
          valid: true,
          errors: [],
        },
        checksums: {
          checksumFileExists: true,
          formatValid: true,
          valid: true,
          checksums: [
            { hash: 'abc123', filename: 'installer.exe' },
            { hash: 'def456', filename: 'app.dmg' },
          ],
          errors: [],
        },
        professionalism: {
          valid: true,
          checks: {
            license: true,
            contributing: true,
            changelog: true,
            gitignore: true,
            packageMetadata: true,
            keywords: true,
          },
          errors: [],
        },
      };

      const report = generateVerificationReport(results);

      expect(report).toContain('# Final Release Verification Report');
      expect(report).toContain('Version: 1.0.1');
      expect(report).toContain('## GitHub Release');
      expect(report).toContain('## Download Links');
      expect(report).toContain('## Checksums');
      expect(report).toContain('## Repository Professionalism');
      expect(report).toContain('## Summary');
      expect(report).toContain('✅ **All verifications passed!**');
    });

    it('should include errors in report when verifications fail', () => {
      const results = {
        version: '1.0.1',
        release: {
          releaseExists: false,
          valid: false,
          errors: ['Release not found'],
          release: null,
        },
        downloads: {
          tested: 0,
          accessible: 0,
          valid: true,
          errors: [],
        },
        checksums: {
          checksumFileExists: false,
          formatValid: false,
          valid: false,
          checksums: [],
          errors: ['Checksum file not found'],
        },
        professionalism: {
          valid: false,
          checks: {
            license: false,
          },
          errors: ['LICENSE is missing'],
        },
      };

      const report = generateVerificationReport(results);

      expect(report).toContain('❌ **Some verifications failed**');
      expect(report).toContain('### Issues:');
      expect(report).toContain('Release not found');
      expect(report).toContain('Checksum file not found');
      expect(report).toContain('LICENSE is missing');
    });

    it('should handle skipped download tests', () => {
      const results = {
        version: '1.0.1',
        release: {
          releaseExists: true,
          valid: true,
          errors: [],
          release: {
            html_url: 'https://github.com/test/repo/releases/tag/v1.0.1',
            assets: [],
            draft: false,
            prerelease: false,
          },
        },
        downloads: {
          tested: 0,
          accessible: 0,
          valid: true,
          errors: [],
        },
        checksums: {
          checksumFileExists: true,
          formatValid: true,
          valid: true,
          checksums: [],
          errors: [],
        },
        professionalism: {
          valid: true,
          checks: {},
          errors: [],
        },
      };

      const report = generateVerificationReport(results);

      expect(report).toContain('## Download Links');
      expect(report).toContain('- Skipped');
    });

    it('should show failed download counts', () => {
      const results = {
        version: '1.0.1',
        release: {
          releaseExists: true,
          valid: true,
          errors: [],
          release: {
            html_url: 'https://github.com/test/repo/releases/tag/v1.0.1',
            assets: [],
            draft: false,
            prerelease: false,
          },
        },
        downloads: {
          tested: 5,
          accessible: 3,
          valid: false,
          errors: ['Download 1 failed', 'Download 2 failed'],
        },
        checksums: {
          checksumFileExists: true,
          formatValid: true,
          valid: true,
          checksums: [],
          errors: [],
        },
        professionalism: {
          valid: true,
          checks: {},
          errors: [],
        },
      };

      const report = generateVerificationReport(results);

      expect(report).toContain('- Tested: 5');
      expect(report).toContain('- Accessible: 3');
      expect(report).toContain('- Failed: 2');
    });
  });
});
