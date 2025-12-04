/**
 * Property-Based Tests for Release Validation
 * 
 * Tests correctness properties for the validation module using fast-check.
 */

const fc = require('fast-check');
const fs = require('fs');
const path = require('path');
const os = require('os');
const {
  validateSemanticVersion,
  validateStructure,
  validateMetadata,
  verifyChangelogVersion,
} = require('../validate-release');

/**
 * **Feature: repository-professionalization, Property 7: Version Consistency**
 * 
 * For any release, the version in package.json, git tag, and GitHub release must all match.
 * 
 * **Validates: Requirements 3.2, 8.5**
 */
describe('Property 7: Version Consistency', () => {
  it('should maintain version consistency across package.json and CHANGELOG', () => {
    fc.assert(
      fc.property(
        // Generate valid semantic versions
        fc.tuple(
          fc.integer({ min: 0, max: 99 }),
          fc.integer({ min: 0, max: 99 }),
          fc.integer({ min: 0, max: 99 })
        ).map(([major, minor, patch]) => `${major}.${minor}.${patch}`),
        (version) => {
          // Create temporary directory
          const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'validate-test-'));
          
          try {
            // Create package.json with version
            const packageJson = {
              name: 'test-package',
              version: version,
              description: 'Test package',
              author: 'Test Author',
              license: 'MIT',
              repository: {
                type: 'git',
                url: 'https://github.com/test/test.git'
              }
            };
            fs.writeFileSync(
              path.join(tempDir, 'package.json'),
              JSON.stringify(packageJson, null, 2)
            );
            
            // Create CHANGELOG with matching version
            const changelog = `# Changelog\n\n## [${version}] - 2024-01-01\n\n### Added\n- New feature\n`;
            fs.writeFileSync(path.join(tempDir, 'CHANGELOG.md'), changelog);
            
            // Verify that validation passes
            const result = verifyChangelogVersion(tempDir);
            
            // Property: If package.json and CHANGELOG both contain the same version,
            // verification should pass
            expect(result.valid).toBe(true);
            expect(result.versionMatches).toBe(true);
            expect(result.changelogUpdated).toBe(true);
          } finally {
            // Cleanup
            try {
              fs.rmSync(tempDir, { recursive: true, force: true });
            } catch (err) {
              // Ignore cleanup errors
            }
          }
        }
      ),
      { numRuns: 100 }
    );
  });
  
  it('should detect version mismatch between package.json and CHANGELOG', () => {
    fc.assert(
      fc.property(
        // Generate two different valid semantic versions
        fc.tuple(
          fc.tuple(
            fc.integer({ min: 0, max: 99 }),
            fc.integer({ min: 0, max: 99 }),
            fc.integer({ min: 0, max: 99 })
          ).map(([major, minor, patch]) => `${major}.${minor}.${patch}`),
          fc.tuple(
            fc.integer({ min: 0, max: 99 }),
            fc.integer({ min: 0, max: 99 }),
            fc.integer({ min: 0, max: 99 })
          ).map(([major, minor, patch]) => `${major}.${minor}.${patch}`)
        ).filter(([v1, v2]) => v1 !== v2), // Ensure versions are different
        ([packageVersion, changelogVersion]) => {
          // Create temporary directory
          const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'validate-test-'));
          
          try {
            // Create package.json with one version
            const packageJson = {
              name: 'test-package',
              version: packageVersion,
              description: 'Test package',
              author: 'Test Author',
              license: 'MIT',
            };
            fs.writeFileSync(
              path.join(tempDir, 'package.json'),
              JSON.stringify(packageJson, null, 2)
            );
            
            // Create CHANGELOG with different version
            const changelog = `# Changelog\n\n## [${changelogVersion}] - 2024-01-01\n\n### Added\n- New feature\n`;
            fs.writeFileSync(path.join(tempDir, 'CHANGELOG.md'), changelog);
            
            // Verify that validation fails
            const result = verifyChangelogVersion(tempDir);
            
            // Property: If package.json and CHANGELOG contain different versions,
            // verification should fail
            expect(result.valid).toBe(false);
            expect(result.versionMatches).toBe(false);
          } finally {
            // Cleanup
            try {
              fs.rmSync(tempDir, { recursive: true, force: true });
            } catch (err) {
              // Ignore cleanup errors
            }
          }
        }
      ),
      { numRuns: 100 }
    );
  });
  
  it('should validate semantic version format correctly', () => {
    fc.assert(
      fc.property(
        // Generate valid semantic versions
        fc.tuple(
          fc.integer({ min: 0, max: 999 }),
          fc.integer({ min: 0, max: 999 }),
          fc.integer({ min: 0, max: 999 })
        ),
        ([major, minor, patch]) => {
          const version = `${major}.${minor}.${patch}`;
          
          // Property: All versions in MAJOR.MINOR.PATCH format should be valid
          expect(validateSemanticVersion(version)).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });
  
  it('should reject invalid semantic version formats', () => {
    fc.assert(
      fc.property(
        // Generate invalid version strings
        fc.oneof(
          fc.constant('1.2'),           // Missing patch
          fc.constant('1'),             // Missing minor and patch
          fc.constant('a.b.c'),         // Non-numeric
          fc.constant('1.2.3.4'),       // Too many parts
          fc.constant(''),              // Empty
          fc.constant('v1.2.3'),        // Prefix
        ),
        (invalidVersion) => {
          // Property: Invalid version formats should be rejected
          expect(validateSemanticVersion(invalidVersion)).toBe(false);
        }
      ),
      { numRuns: 50 }
    );
  });
});

/**
 * **Feature: repository-professionalization, Property 8: Gitignore Effectiveness**
 * 
 * For any file pattern added to .gitignore, running `git status` must not show files matching that pattern.
 * 
 * **Validates: Requirements 4.4**
 */
describe('Property 8: Gitignore Effectiveness', () => {
  it('should recognize essential gitignore patterns', () => {
    fc.assert(
      fc.property(
        // Generate gitignore content with essential patterns
        fc.array(
          fc.oneof(
            fc.constant('node_modules'),
            fc.constant('dist'),
            fc.constant('*.log'),
            fc.constant('build'),
            fc.constant('.env')
          ),
          { minLength: 1, maxLength: 10 }
        ),
        (patterns) => {
          // Create temporary directory
          const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'validate-test-'));
          
          try {
            // Create .gitignore with patterns
            const gitignoreContent = patterns.join('\n');
            fs.writeFileSync(path.join(tempDir, '.gitignore'), gitignoreContent);
            
            // Create required files for validation
            fs.writeFileSync(path.join(tempDir, 'LICENSE'), 'MIT License');
            fs.writeFileSync(path.join(tempDir, 'README.md'), '# Test');
            fs.writeFileSync(path.join(tempDir, 'CONTRIBUTING.md'), '# Contributing');
            fs.writeFileSync(path.join(tempDir, 'CHANGELOG.md'), '# Changelog');
            
            // Validate structure
            const result = validateStructure(tempDir);
            
            // Property: If .gitignore contains essential patterns (node_modules, dist, *.log),
            // gitignoreCorrect should be true
            const hasEssentialPatterns = 
              gitignoreContent.includes('node_modules') &&
              gitignoreContent.includes('dist') &&
              gitignoreContent.includes('*.log');
            
            if (hasEssentialPatterns) {
              expect(result.gitignoreCorrect).toBe(true);
            }
          } finally {
            // Cleanup
            try {
              fs.rmSync(tempDir, { recursive: true, force: true });
            } catch (err) {
              // Ignore cleanup errors
            }
          }
        }
      ),
      { numRuns: 100 }
    );
  });
  
  it('should detect missing essential gitignore patterns', () => {
    fc.assert(
      fc.property(
        // Generate gitignore content without essential patterns
        fc.array(
          fc.oneof(
            fc.constant('*.tmp'),
            fc.constant('.DS_Store'),
            fc.constant('*.swp')
          ),
          { minLength: 0, maxLength: 5 }
        ),
        (patterns) => {
          // Create temporary directory
          const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'validate-test-'));
          
          try {
            // Create .gitignore without essential patterns
            const gitignoreContent = patterns.join('\n');
            fs.writeFileSync(path.join(tempDir, '.gitignore'), gitignoreContent);
            
            // Create required files for validation
            fs.writeFileSync(path.join(tempDir, 'LICENSE'), 'MIT License');
            fs.writeFileSync(path.join(tempDir, 'README.md'), '# Test');
            fs.writeFileSync(path.join(tempDir, 'CONTRIBUTING.md'), '# Contributing');
            fs.writeFileSync(path.join(tempDir, 'CHANGELOG.md'), '# Changelog');
            
            // Validate structure
            const result = validateStructure(tempDir);
            
            // Property: If .gitignore is missing essential patterns,
            // gitignoreCorrect should be false or errors should be reported
            const hasEssentialPatterns = 
              gitignoreContent.includes('node_modules') &&
              gitignoreContent.includes('dist') &&
              gitignoreContent.includes('*.log');
            
            if (!hasEssentialPatterns) {
              expect(result.gitignoreCorrect).toBe(false);
              expect(result.errors.length).toBeGreaterThan(0);
            }
          } finally {
            // Cleanup
            try {
              fs.rmSync(tempDir, { recursive: true, force: true });
            } catch (err) {
              // Ignore cleanup errors
            }
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});
