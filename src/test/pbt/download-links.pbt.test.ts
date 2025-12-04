/**
 * Property-Based Tests for Download Links
 * 
 * Feature: github-releases-installer
 * Property 39: Download link navigates to releases
 * Validates: Requirements 9.2
 * 
 * Tests that download links in documentation navigate to the GitHub releases page
 */

import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import * as fs from 'fs';
import * as path from 'path';

// Files that should contain download links
const DOCUMENTATION_FILES = [
  'README.md',
  'docs/user-guide/installation-windows.md',
  'docs/user-guide/installation-macos.md',
  'docs/user-guide/installation-linux.md',
];

// Expected GitHub releases URL pattern
const RELEASES_URL_PATTERN = /https:\/\/github\.com\/[a-zA-Z0-9-]+\/peft-studio\/releases/;
const LATEST_RELEASE_PATTERN = /https:\/\/github\.com\/[a-zA-Z0-9-]+\/peft-studio\/releases\/latest/;

describe('Download Links', () => {
  /**
   * Property 39: Download link navigates to releases
   * For any download link in the README, it should navigate to the GitHub releases page
   */
  it('should have download links pointing to GitHub releases', () => {
    fc.assert(
      fc.property(
        fc.constantFrom(...DOCUMENTATION_FILES),
        (filePath) => {
          const fullPath = path.join(process.cwd(), filePath);
          
          // Skip if file doesn't exist
          if (!fs.existsSync(fullPath)) {
            console.warn(`File not found: ${filePath}`);
            return true;
          }

          const content = fs.readFileSync(fullPath, 'utf-8');
          
          // Find PEFT Studio download/installer links (not external links like NVIDIA, badges, etc.)
          const peftDownloadPattern = /\[.*?(?:Download|download|Release|release|Installer|installer).*?PEFT.*?\]\((https?:\/\/[^\)]+)\)/g;
          const peftReleasesPattern = /\[.*?(?:releases page|Releases|releases)\]\((https?:\/\/[^\)]+)\)/g;
          
          let foundDownloadLink = false;
          let allLinksValid = true;
          
          // Check PEFT-specific download links
          let match;
          while ((match = peftDownloadPattern.exec(content)) !== null) {
            foundDownloadLink = true;
            const url = match[1];
            
            // Should point to GitHub releases
            if (!RELEASES_URL_PATTERN.test(url)) {
              console.error(`\nInvalid PEFT Studio download link in ${filePath}:`);
              console.error(`  Link text: ${match[0]}`);
              console.error(`  URL: ${url}`);
              console.error(`  Expected: GitHub releases URL`);
              allLinksValid = false;
            }
          }
          
          // Check "releases page" links
          while ((match = peftReleasesPattern.exec(content)) !== null) {
            foundDownloadLink = true;
            const url = match[1];
            
            // Should point to GitHub releases
            if (!RELEASES_URL_PATTERN.test(url)) {
              console.error(`\nInvalid releases page link in ${filePath}:`);
              console.error(`  Link text: ${match[0]}`);
              console.error(`  URL: ${url}`);
              console.error(`  Expected: GitHub releases URL`);
              allLinksValid = false;
            }
          }
          
          // If we found download links, they should all be valid
          if (foundDownloadLink && !allLinksValid) {
            return false;
          }
          
          return true;
        }
      ),
      { numRuns: DOCUMENTATION_FILES.length }
    );
  });

  it('should have prominent download link in README', () => {
    const readmePath = path.join(process.cwd(), 'README.md');
    
    if (!fs.existsSync(readmePath)) {
      console.warn('README.md not found, skipping test');
      return;
    }

    const content = fs.readFileSync(readmePath, 'utf-8');
    
    // Check for download section
    expect(content).toMatch(/##.*[Dd]ownload/);
    
    // Check for releases link
    const hasReleasesLink = RELEASES_URL_PATTERN.test(content);
    expect(hasReleasesLink).toBe(true);
    
    // Check for "latest" release link
    const hasLatestLink = LATEST_RELEASE_PATTERN.test(content);
    expect(hasLatestLink).toBe(true);
    
    // Extract all releases URLs (including /latest)
    const allReleasesUrls = content.match(/https:\/\/github\.com\/[a-zA-Z0-9-]+\/peft-studio\/releases[^\s\)"\]']*/g) || [];
    console.log(`✓ README.md contains ${allReleasesUrls.length} releases links`);
    
    // Verify at least one points to /latest
    const latestUrls = allReleasesUrls.filter(url => url.includes('/latest'));
    expect(latestUrls.length).toBeGreaterThan(0);
    console.log(`✓ ${latestUrls.length} link(s) point to latest release`);
  });

  it('should have consistent releases URLs across documentation', () => {
    const releasesUrls = new Set<string>();
    const baseUrls = new Set<string>();

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
          
          // Extract all releases URLs
          const matches = content.match(RELEASES_URL_PATTERN) || [];
          matches.forEach(url => {
            releasesUrls.add(url);
            // Extract base URL (without /latest, /tag/*, etc.)
            const baseUrl = url.match(/https:\/\/github\.com\/[a-zA-Z0-9-]+\/peft-studio\/releases/)?.[0];
            if (baseUrl) {
              baseUrls.add(baseUrl);
            }
          });
          
          return true;
        }
      ),
      { numRuns: DOCUMENTATION_FILES.length }
    );

    // All releases URLs should use the same base URL
    expect(baseUrls.size).toBeLessThanOrEqual(1);
    
    if (baseUrls.size > 0) {
      const baseUrl = Array.from(baseUrls)[0];
      console.log(`✓ Consistent releases base URL: ${baseUrl}`);
      console.log(`✓ Found ${releasesUrls.size} unique releases URLs`);
    }
  });

  it('should have download instructions in installation guides', () => {
    const installationGuides = [
      'docs/user-guide/installation-windows.md',
      'docs/user-guide/installation-macos.md',
      'docs/user-guide/installation-linux.md',
    ];

    fc.assert(
      fc.property(
        fc.constantFrom(...installationGuides),
        (filePath) => {
          const fullPath = path.join(process.cwd(), filePath);
          
          // Skip if file doesn't exist
          if (!fs.existsSync(fullPath)) {
            console.warn(`Installation guide not found: ${filePath}`);
            return true;
          }

          const content = fs.readFileSync(fullPath, 'utf-8');
          
          // Check for download section
          const hasDownloadSection = /##.*[Dd]ownload/.test(content);
          if (!hasDownloadSection) {
            console.error(`\nMissing download section in ${filePath}`);
            return false;
          }
          
          // Check for releases link
          const hasReleasesLink = RELEASES_URL_PATTERN.test(content);
          if (!hasReleasesLink) {
            console.error(`\nMissing releases link in ${filePath}`);
            return false;
          }
          
          // Check for installation instructions
          const hasInstallationSteps = /##.*[Ii]nstallation/.test(content);
          if (!hasInstallationSteps) {
            console.error(`\nMissing installation section in ${filePath}`);
            return false;
          }
          
          console.log(`✓ ${filePath} has complete download and installation instructions`);
          return true;
        }
      ),
      { numRuns: installationGuides.length }
    );
  });

  it('should have system requirements in installation guides', () => {
    const installationGuides = [
      'docs/user-guide/installation-windows.md',
      'docs/user-guide/installation-macos.md',
      'docs/user-guide/installation-linux.md',
    ];

    fc.assert(
      fc.property(
        fc.constantFrom(...installationGuides),
        (filePath) => {
          const fullPath = path.join(process.cwd(), filePath);
          
          // Skip if file doesn't exist
          if (!fs.existsSync(fullPath)) {
            return true;
          }

          const content = fs.readFileSync(fullPath, 'utf-8');
          
          // Check for system requirements section
          const hasRequirements = /##.*[Ss]ystem [Rr]equirements/.test(content);
          if (!hasRequirements) {
            console.error(`\nMissing system requirements section in ${filePath}`);
            return false;
          }
          
          // Check for minimum requirements
          const hasMinimum = /[Mm]inimum/.test(content);
          if (!hasMinimum) {
            console.error(`\nMissing minimum requirements in ${filePath}`);
            return false;
          }
          
          console.log(`✓ ${filePath} has system requirements`);
          return true;
        }
      ),
      { numRuns: installationGuides.length }
    );
  });

  it('should have troubleshooting section in installation guides', () => {
    const installationGuides = [
      'docs/user-guide/installation-windows.md',
      'docs/user-guide/installation-macos.md',
      'docs/user-guide/installation-linux.md',
    ];

    fc.assert(
      fc.property(
        fc.constantFrom(...installationGuides),
        (filePath) => {
          const fullPath = path.join(process.cwd(), filePath);
          
          // Skip if file doesn't exist
          if (!fs.existsSync(fullPath)) {
            return true;
          }

          const content = fs.readFileSync(fullPath, 'utf-8');
          
          // Check for troubleshooting section
          const hasTroubleshooting = /##.*[Tt]roubleshooting/.test(content);
          if (!hasTroubleshooting) {
            console.error(`\nMissing troubleshooting section in ${filePath}`);
            return false;
          }
          
          console.log(`✓ ${filePath} has troubleshooting section`);
          return true;
        }
      ),
      { numRuns: installationGuides.length }
    );
  });

  it('should have links to installation guides in README', () => {
    const readmePath = path.join(process.cwd(), 'README.md');
    
    if (!fs.existsSync(readmePath)) {
      console.warn('README.md not found, skipping test');
      return;
    }

    const content = fs.readFileSync(readmePath, 'utf-8');
    
    // Check for links to installation guides
    const installationGuideLinks = [
      /installation-windows\.md/,
      /installation-macos\.md/,
      /installation-linux\.md/,
    ];
    
    for (const pattern of installationGuideLinks) {
      const hasLink = pattern.test(content);
      expect(hasLink).toBe(true);
    }
    
    console.log(`✓ README.md links to all platform installation guides`);
  });

  it('should have valid download URLs format', () => {
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
          
          // Find all GitHub releases URLs
          const releasesUrls = content.match(RELEASES_URL_PATTERN) || [];
          
          for (const url of releasesUrls) {
            // Check URL format
            const isValid = 
              url.startsWith('https://github.com/') &&
              url.includes('/peft-studio/releases') &&
              !url.includes(' ') &&
              !url.includes('\n');
            
            if (!isValid) {
              console.error(`\nInvalid URL format in ${filePath}: ${url}`);
              return false;
            }
          }
          
          return true;
        }
      ),
      { numRuns: DOCUMENTATION_FILES.length }
    );
  });
});
