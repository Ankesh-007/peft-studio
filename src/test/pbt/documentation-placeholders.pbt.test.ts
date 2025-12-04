/**
 * Property-Based Tests for Documentation Placeholder Replacement
 * 
 * Feature: github-releases-installer
 * Property 42: Username placeholder replacement
 * Validates: Requirements 9.5
 * 
 * Tests that all instances of "YOUR_USERNAME" are replaced with actual GitHub username
 */

import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import * as fs from 'fs';
import * as path from 'path';

// Files that should not contain YOUR_USERNAME placeholder
const DOCUMENTATION_FILES = [
  'README.md',
  'package.json',
  'electron/main.js',
  'BUILDING.md',
  'CONTRIBUTING.md',
  'CHANGELOG.md',
  'ROADMAP.md',
  'docs/developer-guide/installer-build-guide.md',
  '.github/ISSUE_TEMPLATE/question.md',
  'scripts/verify-branch-protection.sh',
  'scripts/verify-branch-protection.ps1',
  'scripts/configure-repository.sh',
  'scripts/configure-repository.ps1',
];

// Files that are allowed to contain YOUR_USERNAME (templates, specs, etc.)
const ALLOWED_FILES = [
  '.kiro/specs/github-releases-installer/design.md',
  '.kiro/specs/github-releases-installer/tasks.md',
  '.kiro/specs/github-releases-installer/requirements.md',
];

describe('Documentation Placeholder Replacement', () => {
  /**
   * Property 42: Username placeholder replacement
   * For any project publication, all instances of "YOUR_USERNAME" should be replaced 
   * with the actual GitHub username
   */
  it('should not contain YOUR_USERNAME placeholder in documentation files', () => {
    fc.assert(
      fc.property(
        fc.constantFrom(...DOCUMENTATION_FILES),
        (filePath) => {
          const fullPath = path.join(process.cwd(), filePath);

          // Skip if file doesn't exist
          if (!fs.existsSync(fullPath)) {
            return true;
          }

          const content = fs.readFileSync(fullPath, 'utf-8');

          // Check that YOUR_USERNAME is not present
          const hasPlaceholder = content.includes('YOUR_USERNAME');

          if (hasPlaceholder) {
            // Find all occurrences for better error reporting
            const lines = content.split('\n');
            const occurrences = lines
              .map((line, index) => ({ line: index + 1, content: line }))
              .filter(({ content }) => content.includes('YOUR_USERNAME'));

            console.error(`\nFound YOUR_USERNAME placeholder in ${filePath}:`);
            occurrences.forEach(({ line, content }) => {
              console.error(`  Line ${line}: ${content.trim()}`);
            });
          }

          return !hasPlaceholder;
        }
      ),
      { numRuns: DOCUMENTATION_FILES.length }
    );
  });

  it('should have consistent GitHub username across all files', () => {
    const githubUsernamePattern = /github\.com\/([a-zA-Z0-9-]+)\/peft-studio/g;
    const usernames = new Set<string>();

    fc.assert(
      fc.property(
        fc.constantFrom(...DOCUMENTATION_FILES),
        (filePath) => {
          const fullPath = path.join(process.cwd(), filePath);

          // Skip if file doesn't exist
          if (!fs.existsSync(fullPath)) {
            return true;
          }

          const content = fs.readFileSync(fullPath, 'utf-8');

          // Extract all GitHub usernames
          let match;
          while ((match = githubUsernamePattern.exec(content)) !== null) {
            usernames.add(match[1]);
          }

          return true;
        }
      ),
      { numRuns: DOCUMENTATION_FILES.length }
    );

    // After checking all files, verify we have exactly one username
    expect(usernames.size).toBeGreaterThan(0);
    expect(usernames.size).toBeLessThanOrEqual(1);

    // Verify it's not the placeholder
    const username = Array.from(usernames)[0];
    if (username) {
      expect(username).not.toBe('YOUR_USERNAME');
      console.log(`✓ Consistent GitHub username found: ${username}`);
    }
  });

  it('should have valid GitHub repository URLs', () => {
    const validUrlPattern = /https:\/\/github\.com\/[a-zA-Z0-9-]+\/peft-studio/;

    fc.assert(
      fc.property(
        fc.constantFrom(...DOCUMENTATION_FILES),
        (filePath) => {
          const fullPath = path.join(process.cwd(), filePath);

          // Skip if file doesn't exist
          if (!fs.existsSync(fullPath)) {
            return true;
          }

          const content = fs.readFileSync(fullPath, 'utf-8');

          // Find all GitHub URLs
          const githubUrls = content.match(/https:\/\/github\.com\/[^\s)"\]]+/g) || [];

          // Check each URL is valid (not containing YOUR_USERNAME)
          for (const url of githubUrls) {
            if (url.includes('YOUR_USERNAME')) {
              console.error(`\nFound invalid URL in ${filePath}: ${url}`);
              return false;
            }

            // Check it matches the valid pattern
            if (url.includes('peft-studio') && !validUrlPattern.test(url)) {
              console.error(`\nFound malformed URL in ${filePath}: ${url}`);
              return false;
            }
          }

          return true;
        }
      ),
      { numRuns: DOCUMENTATION_FILES.length }
    );
  });

  it('should have replaced placeholders in package.json', () => {
    const packageJsonPath = path.join(process.cwd(), 'package.json');

    if (!fs.existsSync(packageJsonPath)) {
      console.warn('package.json not found, skipping test');
      return;
    }

    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));

    // Check repository field
    expect(packageJson.repository?.url).toBeDefined();
    expect(packageJson.repository?.url).not.toContain('YOUR_USERNAME');

    // Check homepage field
    expect(packageJson.homepage).toBeDefined();
    expect(packageJson.homepage).not.toContain('YOUR_USERNAME');

    // Check bugs field
    expect(packageJson.bugs?.url).toBeDefined();
    expect(packageJson.bugs?.url).not.toContain('YOUR_USERNAME');

    // Check build.publish field
    expect(packageJson.build?.publish?.owner).toBeDefined();
    expect(packageJson.build?.publish?.owner).not.toBe('YOUR_USERNAME');

    console.log(`✓ package.json has valid repository configuration`);
    console.log(`  Repository: ${packageJson.repository?.url}`);
    console.log(`  Homepage: ${packageJson.homepage}`);
    console.log(`  Bugs: ${packageJson.bugs?.url}`);
    console.log(`  Publish owner: ${packageJson.build?.publish?.owner}`);
  });

  it('should have replaced placeholders in electron main.js', () => {
    const mainJsPath = path.join(process.cwd(), 'electron/main.js');

    if (!fs.existsSync(mainJsPath)) {
      console.warn('electron/main.js not found, skipping test');
      return;
    }

    const content = fs.readFileSync(mainJsPath, 'utf-8');

    // Check for YOUR_USERNAME in autoUpdater configuration
    expect(content).not.toContain("owner: 'YOUR_USERNAME'");
    expect(content).not.toContain('owner: "YOUR_USERNAME"');

    // Extract the owner value
    const ownerMatch = content.match(/owner:\s*['"]([^'"]+)['"]/);
    if (ownerMatch) {
      const owner = ownerMatch[1];
      expect(owner).not.toBe('YOUR_USERNAME');
      console.log(`✓ electron/main.js has valid auto-updater owner: ${owner}`);
    }
  });

  it('should not have placeholder warning in README', () => {
    const readmePath = path.join(process.cwd(), 'README.md');

    if (!fs.existsSync(readmePath)) {
      console.warn('README.md not found, skipping test');
      return;
    }

    const content = fs.readFileSync(readmePath, 'utf-8');

    // Check that the warning about replacing YOUR_USERNAME is removed
    const warningPatterns = [
      /replace all instances of.*YOUR_USERNAME/i,
      /Before publishing.*YOUR_USERNAME/i,
      /\*\*Note\*\*:.*YOUR_USERNAME/i,
    ];

    for (const pattern of warningPatterns) {
      const match = content.match(pattern);
      if (match) {
        console.error(`\nFound placeholder warning in README.md: ${match[0]}`);
      }
      expect(content).not.toMatch(pattern);
    }

    console.log(`✓ README.md has no placeholder warnings`);
  });
});
