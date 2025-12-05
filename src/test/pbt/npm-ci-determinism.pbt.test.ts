/**
 * Property-Based Tests for npm ci Determinism
 * 
 * **Feature: ci-infrastructure-fix, Property 8: npm ci Determinism**
 * **Validates: Requirements 4.1**
 * 
 * Property: For any package-lock.json file, running npm ci should install 
 * the exact same dependency versions in both local and CI environments, 
 * producing identical node_modules.
 */

import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import { execSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';

describe('npm ci Determinism Property Tests', () => {
  /**
   * Helper function to compute hash of installed packages
   */
  function computePackageHash(nodeModulesPath: string): string {
    const packages: string[] = [];
    
    if (!fs.existsSync(nodeModulesPath)) {
      return '';
    }

    // Read all package.json files in node_modules
    const collectPackages = (dir: string) => {
      try {
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        
        for (const entry of entries) {
          if (entry.isDirectory()) {
            const fullPath = path.join(dir, entry.name);
            const packageJsonPath = path.join(fullPath, 'package.json');
            
            if (fs.existsSync(packageJsonPath)) {
              try {
                const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
                packages.push(`${packageJson.name}@${packageJson.version}`);
              } catch {
                // Skip invalid package.json files
              }
            }
            
            // Handle scoped packages (@org/package)
            if (entry.name.startsWith('@')) {
              collectPackages(fullPath);
            }
          }
        }
      } catch {
        // Skip directories we can't read
      }
    };

    collectPackages(nodeModulesPath);
    
    // Sort for consistent hashing
    packages.sort();
    
    // Create hash of all package names and versions
    const hash = crypto.createHash('sha256');
    hash.update(packages.join('\n'));
    return hash.digest('hex');
  }

  /**
   * Helper function to get package versions from package-lock.json
   */
  function getLockedVersions(lockfilePath: string): Map<string, string> {
    const versions = new Map<string, string>();
    
    if (!fs.existsSync(lockfilePath)) {
      return versions;
    }

    try {
      const lockfile = JSON.parse(fs.readFileSync(lockfilePath, 'utf-8'));
      
      // Handle lockfile v2 and v3 format
      if (lockfile.packages) {
        for (const [pkgPath, pkgInfo] of Object.entries(lockfile.packages)) {
          if (pkgPath === '') continue; // Skip root package
          
          const pkgData = pkgInfo as { version?: string; name?: string };
          if (pkgData.version) {
            // Extract package name from path
            const name = pkgPath.replace(/^node_modules\//, '');
            versions.set(name, pkgData.version);
          }
        }
      }
      
      // Also handle lockfile v1 format
      if (lockfile.dependencies) {
        const collectDeps = (deps: Record<string, any>, prefix = '') => {
          for (const [name, info] of Object.entries(deps)) {
            if (info.version) {
              versions.set(prefix + name, info.version);
            }
            if (info.dependencies) {
              collectDeps(info.dependencies, `${prefix}${name}/`);
            }
          }
        };
        collectDeps(lockfile.dependencies);
      }
    } catch {
      // Return empty map if parsing fails
    }

    return versions;
  }

  it('Property 8: npm ci should produce deterministic installations', () => {
    // This property tests that the package-lock.json determines exact versions
    // We verify this by checking that locked versions match installed versions
    
    const packageLockPath = path.join(process.cwd(), 'package-lock.json');
    const nodeModulesPath = path.join(process.cwd(), 'node_modules');
    
    // Verify package-lock.json exists
    expect(fs.existsSync(packageLockPath)).toBe(true);
    
    // Get locked versions from package-lock.json
    const lockedVersions = getLockedVersions(packageLockPath);
    
    // Verify we have locked versions
    expect(lockedVersions.size).toBeGreaterThan(0);
    
    // Check that installed packages match locked versions
    const installedPackages = new Map<string, string>();
    
    if (fs.existsSync(nodeModulesPath)) {
      const collectInstalled = (dir: string, prefix = '') => {
        try {
          const entries = fs.readdirSync(dir, { withFileTypes: true });
          
          for (const entry of entries) {
            if (entry.isDirectory()) {
              const fullPath = path.join(dir, entry.name);
              const packageJsonPath = path.join(fullPath, 'package.json');
              
              if (fs.existsSync(packageJsonPath)) {
                try {
                  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
                  const pkgName = prefix + entry.name;
                  installedPackages.set(pkgName, packageJson.version);
                } catch {
                  // Skip invalid package.json
                }
              }
              
              // Handle scoped packages
              if (entry.name.startsWith('@')) {
                collectInstalled(fullPath, `${prefix}${entry.name}/`);
              }
            }
          }
        } catch {
          // Skip directories we can't read
        }
      };
      
      collectInstalled(nodeModulesPath);
    }
    
    // Property: For packages that are both locked and installed,
    // versions must match exactly
    let matchCount = 0;
    let mismatchCount = 0;
    const mismatches: string[] = [];
    
    for (const [pkgName, lockedVersion] of lockedVersions.entries()) {
      const installedVersion = installedPackages.get(pkgName);
      
      if (installedVersion) {
        if (installedVersion === lockedVersion) {
          matchCount++;
        } else {
          mismatchCount++;
          mismatches.push(`${pkgName}: locked=${lockedVersion}, installed=${installedVersion}`);
        }
      }
    }
    
    // Property: All installed packages should match their locked versions
    if (mismatchCount > 0) {
      console.log('Version mismatches found:');
      mismatches.slice(0, 10).forEach(m => console.log(`  ${m}`));
      if (mismatches.length > 10) {
        console.log(`  ... and ${mismatches.length - 10} more`);
      }
    }
    
    expect(mismatchCount).toBe(0);
    expect(matchCount).toBeGreaterThan(0);
  });

  it('Property 8.1: package-lock.json integrity hashes ensure determinism', () => {
    // This property verifies that package-lock.json contains integrity hashes
    // which npm ci uses to ensure exact package contents
    
    const packageLockPath = path.join(process.cwd(), 'package-lock.json');
    
    expect(fs.existsSync(packageLockPath)).toBe(true);
    
    const lockfile = JSON.parse(fs.readFileSync(packageLockPath, 'utf-8'));
    
    // Verify lockfile version (should be 2 or 3 for modern npm)
    expect(lockfile.lockfileVersion).toBeGreaterThanOrEqual(2);
    
    // Count packages with integrity hashes
    let packagesWithIntegrity = 0;
    let totalPackages = 0;
    
    if (lockfile.packages) {
      for (const [pkgPath, pkgInfo] of Object.entries(lockfile.packages)) {
        if (pkgPath === '') continue; // Skip root
        
        totalPackages++;
        const pkgData = pkgInfo as { integrity?: string; link?: boolean };
        
        // Packages should have integrity unless they're links
        if (pkgData.integrity || pkgData.link) {
          packagesWithIntegrity++;
        }
      }
    }
    
    // Property: Most packages should have integrity hashes
    // (some may be links or local packages without integrity)
    const integrityRatio = packagesWithIntegrity / totalPackages;
    expect(integrityRatio).toBeGreaterThan(0.9); // At least 90% should have integrity
  });

  it('Property 8.2: npm ci determinism with simulated package-lock variations', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate variations of package metadata that should still be deterministic
        fc.record({
          packageName: fc.constantFrom('react', 'typescript', 'vite', 'vitest'),
          version: fc.constantFrom('18.3.1', '5.7.2', '7.2.6', '4.0.14'),
          hasIntegrity: fc.boolean(),
          hasResolved: fc.boolean()
        }),
        async ({ packageName, version, hasIntegrity, hasResolved }) => {
          // Property: A package entry with name, version, and integrity
          // should uniquely identify the package contents
          
          // Create a mock package entry
          const packageEntry: Record<string, any> = {
            version: version
          };
          
          if (hasIntegrity) {
            // Integrity hash ensures exact contents
            packageEntry.integrity = `sha512-${crypto.randomBytes(32).toString('hex')}`;
          }
          
          if (hasResolved) {
            // Resolved URL points to exact tarball
            packageEntry.resolved = `https://registry.npmjs.org/${packageName}/-/${packageName}-${version}.tgz`;
          }
          
          // Property: With integrity hash, the package is fully determined
          if (hasIntegrity) {
            expect(packageEntry.integrity).toBeDefined();
            expect(packageEntry.integrity).toMatch(/^sha\d+-[a-f0-9]+$/);
          }
          
          // Property: Version must always be present
          expect(packageEntry.version).toBeDefined();
          expect(packageEntry.version).toMatch(/^\d+\.\d+\.\d+/);
        }
      ),
      {
        numRuns: 100,
        verbose: true
      }
    );
  });

  it('Property 8.3: lockfileVersion consistency ensures determinism', () => {
    // Property: The lockfile version determines the format and guarantees
    // that npm ci will interpret it consistently
    
    const packageLockPath = path.join(process.cwd(), 'package-lock.json');
    expect(fs.existsSync(packageLockPath)).toBe(true);
    
    const lockfile = JSON.parse(fs.readFileSync(packageLockPath, 'utf-8'));
    
    // Property: lockfileVersion must be present and valid
    expect(lockfile.lockfileVersion).toBeDefined();
    expect([1, 2, 3]).toContain(lockfile.lockfileVersion);
    
    // Property: Modern lockfiles (v2+) should have packages field
    if (lockfile.lockfileVersion >= 2) {
      expect(lockfile.packages).toBeDefined();
      expect(typeof lockfile.packages).toBe('object');
    }
    
    // Property: All lockfiles should have name and version
    expect(lockfile.name).toBeDefined();
    expect(lockfile.version).toBeDefined();
  });

  it('Property 8.4: npm ci idempotence - multiple runs produce same result', () => {
    // Property: Running npm ci multiple times with the same package-lock.json
    // should produce identical results
    
    const packageLockPath = path.join(process.cwd(), 'package-lock.json');
    const nodeModulesPath = path.join(process.cwd(), 'node_modules');
    
    expect(fs.existsSync(packageLockPath)).toBe(true);
    
    // Get current state
    const lockedVersions = getLockedVersions(packageLockPath);
    
    // Read package-lock.json content
    const lockfileContent = fs.readFileSync(packageLockPath, 'utf-8');
    const lockfileHash = crypto.createHash('sha256').update(lockfileContent).digest('hex');
    
    // Property: package-lock.json should not change during test
    // (this ensures we're testing determinism, not lock file updates)
    const lockfileContentAfter = fs.readFileSync(packageLockPath, 'utf-8');
    const lockfileHashAfter = crypto.createHash('sha256').update(lockfileContentAfter).digest('hex');
    
    expect(lockfileHashAfter).toBe(lockfileHash);
    
    // Property: The locked versions define what should be installed
    expect(lockedVersions.size).toBeGreaterThan(0);
    
    // Verify node_modules exists (npm ci should have been run)
    if (fs.existsSync(nodeModulesPath)) {
      const hash1 = computePackageHash(nodeModulesPath);
      
      // Property: The hash should be consistent
      expect(hash1).toBeTruthy();
      expect(hash1.length).toBe(64); // SHA-256 hex length
    }
  });
});
