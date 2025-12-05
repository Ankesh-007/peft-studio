/**
 * Property-Based Tests for CI Environment Comparison
 *
 * Feature: ci-infrastructure-fix, Property 3: Environment Comparison Completeness
 * Validates: Requirements 1.3
 *
 * These tests verify that the environment comparator correctly identifies all
 * differences in Node.js version, Python version, and dependency versions between
 * local and CI environments.
 */

import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import {
  EnvironmentComparator,
  EnvironmentConfig,
  EnvironmentComparison,
} from '../../lib/ci-diagnostics';

/**
 * Arbitrary generator for semantic version strings
 */
const versionArbitrary = () =>
  fc.oneof(
    // Standard semantic versions
    fc
      .tuple(
        fc.integer({ min: 0, max: 20 }),
        fc.integer({ min: 0, max: 50 }),
        fc.integer({ min: 0, max: 100 })
      )
      .map(([major, minor, patch]) => `${major}.${minor}.${patch}`),
    // Versions with 'v' prefix
    fc
      .tuple(
        fc.integer({ min: 0, max: 20 }),
        fc.integer({ min: 0, max: 50 }),
        fc.integer({ min: 0, max: 100 })
      )
      .map(([major, minor, patch]) => `v${major}.${minor}.${patch}`),
    // Short versions (major.minor)
    fc
      .tuple(fc.integer({ min: 0, max: 20 }), fc.integer({ min: 0, max: 50 }))
      .map(([major, minor]) => `${major}.${minor}`),
    // Major version with .x
    fc.integer({ min: 0, max: 20 }).map((major) => `${major}.x`)
  );

/**
 * Arbitrary generator for dependency map
 */
const dependenciesArbitrary = () =>
  fc.dictionary(
    fc.stringMatching(/^[a-z][a-z0-9-]*$/), // Package names
    versionArbitrary(),
    { minKeys: 0, maxKeys: 20 }
  );

/**
 * Arbitrary generator for EnvironmentConfig
 */
const environmentConfigArbitrary = () =>
  fc.record({
    nodeVersion: versionArbitrary(),
    pythonVersion: versionArbitrary(),
    dependencies: dependenciesArbitrary(),
  });

/**
 * Helper: Count all differences in an environment comparison
 */
function countAllDifferences(comparison: EnvironmentComparison): number {
  let count = 0;
  
  // Count version differences
  if (comparison.nodeVersion.local !== comparison.nodeVersion.ci) {
    count++;
  }
  if (comparison.pythonVersion.local !== comparison.pythonVersion.ci) {
    count++;
  }
  
  // Count dependency differences
  count += comparison.dependencyDiffs.length;
  
  return count;
}

/**
 * Helper: Get all actual differences between two environments
 */
function getActualDifferences(local: EnvironmentConfig, ci: EnvironmentConfig): {
  nodeVersionDiff: boolean;
  pythonVersionDiff: boolean;
  dependencyDiffs: string[];
} {
  const nodeVersionDiff = local.nodeVersion !== ci.nodeVersion;
  const pythonVersionDiff = local.pythonVersion !== ci.pythonVersion;
  
  const allPackages = new Set([
    ...Object.keys(local.dependencies),
    ...Object.keys(ci.dependencies),
  ]);
  
  const dependencyDiffs: string[] = [];
  for (const pkg of allPackages) {
    const localVersion = local.dependencies[pkg] || 'not installed';
    const ciVersion = ci.dependencies[pkg] || 'not installed';
    if (localVersion !== ciVersion) {
      dependencyDiffs.push(pkg);
    }
  }
  
  return { nodeVersionDiff, pythonVersionDiff, dependencyDiffs };
}

describe('CI Environment Comparison - Property-Based Tests', () => {
  const comparator = new EnvironmentComparator();

  /**
   * Feature: ci-infrastructure-fix, Property 3: Environment Comparison Completeness
   * Validates: Requirements 1.3
   *
   * For any two environment configurations (local and CI), the comparison should
   * identify all differences in Node.js version, Python version, and dependency versions.
   */
  describe('Property 3: Environment Comparison Completeness', () => {
    it('should identify Node.js version differences', () => {
      fc.assert(
        fc.property(
          environmentConfigArbitrary(),
          environmentConfigArbitrary(),
          (local, ci) => {
            // Compare environments
            const comparison = comparator.compareEnvironments(local, ci);

            // Property: If Node versions differ, the comparison should reflect that
            if (local.nodeVersion !== ci.nodeVersion) {
              expect(comparison.nodeVersion.local).toBe(local.nodeVersion);
              expect(comparison.nodeVersion.ci).toBe(ci.nodeVersion);
              expect(comparison.nodeVersion.local).not.toBe(comparison.nodeVersion.ci);
            } else {
              // If versions are the same, they should match
              expect(comparison.nodeVersion.local).toBe(comparison.nodeVersion.ci);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should identify Python version differences', () => {
      fc.assert(
        fc.property(
          environmentConfigArbitrary(),
          environmentConfigArbitrary(),
          (local, ci) => {
            // Compare environments
            const comparison = comparator.compareEnvironments(local, ci);

            // Property: If Python versions differ, the comparison should reflect that
            if (local.pythonVersion !== ci.pythonVersion) {
              expect(comparison.pythonVersion.local).toBe(local.pythonVersion);
              expect(comparison.pythonVersion.ci).toBe(ci.pythonVersion);
              expect(comparison.pythonVersion.local).not.toBe(comparison.pythonVersion.ci);
            } else {
              // If versions are the same, they should match
              expect(comparison.pythonVersion.local).toBe(comparison.pythonVersion.ci);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should identify all dependency version differences', () => {
      fc.assert(
        fc.property(
          environmentConfigArbitrary(),
          environmentConfigArbitrary(),
          (local, ci) => {
            // Compare environments
            const comparison = comparator.compareEnvironments(local, ci);

            // Get actual differences
            const actual = getActualDifferences(local, ci);

            // Property: Number of dependency diffs should match actual differences
            expect(comparison.dependencyDiffs.length).toBe(actual.dependencyDiffs.length);

            // Property: Each actual difference should be in the comparison
            for (const pkg of actual.dependencyDiffs) {
              const diff = comparison.dependencyDiffs.find((d) => d.package === pkg);
              expect(diff).toBeDefined();
              expect(diff!.mismatch).toBe(true);
            }

            // Property: Each diff in comparison should be an actual difference
            for (const diff of comparison.dependencyDiffs) {
              expect(actual.dependencyDiffs).toContain(diff.package);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should not miss any differences between environments', () => {
      fc.assert(
        fc.property(
          environmentConfigArbitrary(),
          environmentConfigArbitrary(),
          (local, ci) => {
            // Compare environments
            const comparison = comparator.compareEnvironments(local, ci);

            // Get actual differences
            const actual = getActualDifferences(local, ci);

            // Property: All actual differences should be captured
            if (actual.nodeVersionDiff) {
              expect(comparison.nodeVersion.local).not.toBe(comparison.nodeVersion.ci);
            }

            if (actual.pythonVersionDiff) {
              expect(comparison.pythonVersion.local).not.toBe(comparison.pythonVersion.ci);
            }

            // Property: All dependency differences should be captured
            expect(comparison.dependencyDiffs.length).toBe(actual.dependencyDiffs.length);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should report zero differences for identical environments', () => {
      fc.assert(
        fc.property(environmentConfigArbitrary(), (env) => {
          // Compare environment with itself
          const comparison = comparator.compareEnvironments(env, env);

          // Property: Identical environments should have no differences
          expect(comparison.nodeVersion.local).toBe(comparison.nodeVersion.ci);
          expect(comparison.pythonVersion.local).toBe(comparison.pythonVersion.ci);
          expect(comparison.dependencyDiffs.length).toBe(0);
        }),
        { numRuns: 100 }
      );
    });

    it('should correctly identify packages present in only one environment', () => {
      fc.assert(
        fc.property(
          environmentConfigArbitrary(),
          fc.stringMatching(/^[a-z][a-z0-9-]*$/),
          versionArbitrary(),
          (baseEnv, newPackage, version) => {
            // Create local environment with an extra package
            const local = {
              ...baseEnv,
              dependencies: {
                ...baseEnv.dependencies,
                [newPackage]: version,
              },
            };

            // CI environment doesn't have the new package
            const ci = baseEnv;

            // Compare environments
            const comparison = comparator.compareEnvironments(local, ci);

            // Property: The new package should appear in dependency diffs
            const diff = comparison.dependencyDiffs.find((d) => d.package === newPackage);
            if (local.dependencies[newPackage] !== ci.dependencies[newPackage]) {
              expect(diff).toBeDefined();
              expect(diff!.localVersion).toBe(version);
              expect(diff!.ciVersion).toBe('not installed');
              expect(diff!.mismatch).toBe(true);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle packages with different versions', () => {
      fc.assert(
        fc.property(
          environmentConfigArbitrary(),
          fc.stringMatching(/^[a-z][a-z0-9-]*$/),
          versionArbitrary(),
          versionArbitrary(),
          (baseEnv, pkg, localVersion, ciVersion) => {
            fc.pre(localVersion !== ciVersion); // Only test when versions differ

            // Create environments with different versions of the same package
            const local = {
              ...baseEnv,
              dependencies: {
                ...baseEnv.dependencies,
                [pkg]: localVersion,
              },
            };

            const ci = {
              ...baseEnv,
              dependencies: {
                ...baseEnv.dependencies,
                [pkg]: ciVersion,
              },
            };

            // Compare environments
            const comparison = comparator.compareEnvironments(local, ci);

            // Property: The package should appear in dependency diffs with correct versions
            const diff = comparison.dependencyDiffs.find((d) => d.package === pkg);
            expect(diff).toBeDefined();
            expect(diff!.localVersion).toBe(localVersion);
            expect(diff!.ciVersion).toBe(ciVersion);
            expect(diff!.mismatch).toBe(true);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should maintain completeness regardless of comparison order', () => {
      fc.assert(
        fc.property(
          environmentConfigArbitrary(),
          environmentConfigArbitrary(),
          (env1, env2) => {
            // Compare in both directions
            const comparison1 = comparator.compareEnvironments(env1, env2);
            const comparison2 = comparator.compareEnvironments(env2, env1);

            // Property: Number of differences should be the same regardless of order
            expect(comparison1.dependencyDiffs.length).toBe(comparison2.dependencyDiffs.length);

            // Property: Same packages should be identified as different
            const packages1 = new Set(comparison1.dependencyDiffs.map((d) => d.package));
            const packages2 = new Set(comparison2.dependencyDiffs.map((d) => d.package));
            expect(packages1).toEqual(packages2);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should correctly report version compatibility', () => {
      fc.assert(
        fc.property(
          fc.integer({ min: 0, max: 20 }),
          fc.integer({ min: 0, max: 50 }),
          fc.integer({ min: 0, max: 50 }),
          (major, minor1, minor2) => {
            // Create environments with same major version but different minor versions
            const local: EnvironmentConfig = {
              nodeVersion: `${major}.${minor1}.0`,
              pythonVersion: '3.10.0',
              dependencies: {},
            };

            const ci: EnvironmentConfig = {
              nodeVersion: `${major}.${minor2}.0`,
              pythonVersion: '3.10.0',
              dependencies: {},
            };

            // Compare environments
            const comparison = comparator.compareEnvironments(local, ci);

            // Property: Same major version should be compatible
            expect(comparison.nodeVersion.compatible).toBe(true);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should detect incompatibility for different major versions', () => {
      fc.assert(
        fc.property(
          fc.integer({ min: 0, max: 20 }),
          fc.integer({ min: 0, max: 20 }),
          (major1, major2) => {
            fc.pre(major1 !== major2); // Only test when major versions differ

            // Create environments with different major versions
            const local: EnvironmentConfig = {
              nodeVersion: `${major1}.0.0`,
              pythonVersion: '3.10.0',
              dependencies: {},
            };

            const ci: EnvironmentConfig = {
              nodeVersion: `${major2}.0.0`,
              pythonVersion: '3.10.0',
              dependencies: {},
            };

            // Compare environments
            const comparison = comparator.compareEnvironments(local, ci);

            // Property: Different major versions should be incompatible
            expect(comparison.nodeVersion.compatible).toBe(false);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle empty dependency lists', () => {
      fc.assert(
        fc.property(versionArbitrary(), versionArbitrary(), (nodeVer, pythonVer) => {
          // Create environments with no dependencies
          const local: EnvironmentConfig = {
            nodeVersion: nodeVer,
            pythonVersion: pythonVer,
            dependencies: {},
          };

          const ci: EnvironmentConfig = {
            nodeVersion: nodeVer,
            pythonVersion: pythonVer,
            dependencies: {},
          };

          // Compare environments
          const comparison = comparator.compareEnvironments(local, ci);

          // Property: No dependencies should result in no dependency diffs
          expect(comparison.dependencyDiffs.length).toBe(0);
        }),
        { numRuns: 100 }
      );
    });

    it('should identify all differences in a complex scenario', () => {
      fc.assert(
        fc.property(
          environmentConfigArbitrary(),
          environmentConfigArbitrary(),
          (local, ci) => {
            // Compare environments
            const comparison = comparator.compareEnvironments(local, ci);

            // Count all differences
            const totalDiffs = countAllDifferences(comparison);

            // Get actual differences
            const actual = getActualDifferences(local, ci);
            const expectedDiffs =
              (actual.nodeVersionDiff ? 1 : 0) +
              (actual.pythonVersionDiff ? 1 : 0) +
              actual.dependencyDiffs.length;

            // Property: Total differences should match expected
            expect(totalDiffs).toBe(expectedDiffs);

            // Property: Comparison should be complete
            expect(comparison.nodeVersion).toBeDefined();
            expect(comparison.pythonVersion).toBeDefined();
            expect(comparison.dependencyDiffs).toBeDefined();
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle version strings with v prefix consistently', () => {
      fc.assert(
        fc.property(
          fc.integer({ min: 0, max: 20 }),
          fc.integer({ min: 0, max: 50 }),
          fc.integer({ min: 0, max: 100 }),
          (major, minor, patch) => {
            // Create environments with and without v prefix
            const local: EnvironmentConfig = {
              nodeVersion: `v${major}.${minor}.${patch}`,
              pythonVersion: '3.10.0',
              dependencies: {},
            };

            const ci: EnvironmentConfig = {
              nodeVersion: `${major}.${minor}.${patch}`,
              pythonVersion: '3.10.0',
              dependencies: {},
            };

            // Compare environments
            const comparison = comparator.compareEnvironments(local, ci);

            // Property: Same major version should be compatible regardless of v prefix
            expect(comparison.nodeVersion.compatible).toBe(true);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should not create false positives for matching dependencies', () => {
      fc.assert(
        fc.property(
          fc.dictionary(
            fc.stringMatching(/^[a-z][a-z0-9-]*$/),
            versionArbitrary(),
            { minKeys: 1, maxKeys: 10 }
          ),
          (deps) => {
            // Create identical environments
            const local: EnvironmentConfig = {
              nodeVersion: '18.0.0',
              pythonVersion: '3.10.0',
              dependencies: deps,
            };

            const ci: EnvironmentConfig = {
              nodeVersion: '18.0.0',
              pythonVersion: '3.10.0',
              dependencies: { ...deps },
            };

            // Compare environments
            const comparison = comparator.compareEnvironments(local, ci);

            // Property: Identical dependencies should produce no diffs
            expect(comparison.dependencyDiffs.length).toBe(0);
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});
