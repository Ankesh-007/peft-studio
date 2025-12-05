/**
 * Property-Based Tests for CI Failure Categorization
 *
 * Feature: ci-infrastructure-fix, Property 2: Failure Categorization Consistency
 * Validates: Requirements 1.2
 *
 * These tests verify that the CI log analyzer consistently categorizes failures
 * by type, with the same failure always receiving the same category.
 */

import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import { CILogAnalyzer, Failure, FailureCategory } from '../../lib/ci-diagnostics';

/**
 * Arbitrary generator for Failure with specific characteristics
 */
const failureArbitrary = () =>
  fc.record({
    job: fc.string({ minLength: 1, maxLength: 50 }),
    step: fc.string({ minLength: 1, maxLength: 50 }),
    errorMessage: fc.string({ minLength: 5, maxLength: 200 }),
    stackTrace: fc.option(fc.string({ minLength: 10, maxLength: 100 }), { nil: undefined }),
    exitCode: fc.integer({ min: 0, max: 255 }),
  });

/**
 * Arbitrary generator for lint-related failures
 * Note: Job names must contain 'lint' or error messages must contain 'eslint'/'prettier'
 * to be categorized as 'lint' by the implementation
 */
const lintFailureArbitrary = () =>
  fc.record({
    job: fc.constantFrom('lint', 'Lint', 'ESLint Check', 'lint-check', 'code-lint'),
    step: fc.constantFrom('Run ESLint', 'Check formatting', 'Lint code'),
    errorMessage: fc.constantFrom(
      'ESLint found 5 errors',
      'prettier formatting issues detected',
      'Linting failed with errors',
      'eslint: command failed'
    ),
    stackTrace: fc.constant(undefined),
    exitCode: fc.constantFrom(1, 2),
  });

/**
 * Arbitrary generator for test-related failures
 */
const testFailureArbitrary = () =>
  fc.record({
    job: fc.constantFrom('test', 'Test Frontend', 'Test Backend', 'Unit Tests'),
    step: fc.constantFrom('Run tests', 'Execute test suite', 'Run Vitest'),
    errorMessage: fc.constantFrom(
      'Test suite failed with 3 failures',
      'spec: assertion failed',
      'test timeout exceeded',
      'Expected true but got false'
    ),
    stackTrace: fc.option(fc.string({ minLength: 10, maxLength: 100 }), { nil: undefined }),
    exitCode: fc.constantFrom(1, 2),
  });

/**
 * Arbitrary generator for build-related failures
 * Note: Job names must contain 'build' or error messages must contain 'build'/'compile'
 * to be categorized as 'build' by the implementation
 */
const buildFailureArbitrary = () =>
  fc.record({
    job: fc.constantFrom('build', 'Build Check', 'build-app', 'Build Frontend', 'frontend-build'),
    step: fc.constantFrom('Run build', 'Compile TypeScript', 'Build application'),
    errorMessage: fc.constantFrom(
      'Build failed with compilation errors',
      'compile error: type mismatch',
      'Vite build failed',
      'TypeScript compilation failed'
    ),
    stackTrace: fc.constant(undefined),
    exitCode: fc.constantFrom(1, 2),
  });

/**
 * Arbitrary generator for dependency-related failures
 */
const dependencyFailureArbitrary = () =>
  fc.record({
    job: fc.string({ minLength: 1, maxLength: 50 }),
    step: fc.constantFrom('Install dependencies', 'npm ci', 'pip install'),
    errorMessage: fc.constantFrom(
      'Module not found: cannot resolve package',
      'dependency conflict detected',
      'Package installation failed',
      'Cannot find module "react"'
    ),
    stackTrace: fc.constant(undefined),
    exitCode: fc.constantFrom(1, 2),
  });

/**
 * Arbitrary generator for environment-related failures
 */
const environmentFailureArbitrary = () =>
  fc.record({
    job: fc.string({ minLength: 1, maxLength: 50 }),
    step: fc.string({ minLength: 1, maxLength: 50 }),
    errorMessage: fc.constantFrom(
      'Node version mismatch',
      'Python version incompatible',
      'System configuration error',
      'Platform not supported'
    ),
    stackTrace: fc.constant(undefined),
    exitCode: fc.constantFrom(1, 2),
  });

/**
 * Helper: Normalize failure for comparison (exclude non-deterministic fields)
 */
function normalizeFailure(failure: Failure): string {
  return JSON.stringify({
    job: failure.job,
    step: failure.step,
    errorMessage: failure.errorMessage,
  });
}

describe('CI Failure Categorization - Property-Based Tests', () => {
  const analyzer = new CILogAnalyzer();

  /**
   * Feature: ci-infrastructure-fix, Property 2: Failure Categorization Consistency
   * Validates: Requirements 1.2
   *
   * For any set of failure messages, the categorization system should consistently
   * group them by type (linting, test, build, dependency) with the same failure
   * always receiving the same category.
   */
  describe('Property 2: Failure Categorization Consistency', () => {
    it('should consistently categorize the same failure to the same type', () => {
      fc.assert(
        fc.property(failureArbitrary(), (failure) => {
          // Categorize the same failure multiple times
          const categories1 = analyzer.categorizeFailures([failure]);
          const categories2 = analyzer.categorizeFailures([failure]);
          const categories3 = analyzer.categorizeFailures([failure]);

          // Property: Same failure should always produce the same category type
          expect(categories1.length).toBe(1);
          expect(categories2.length).toBe(1);
          expect(categories3.length).toBe(1);

          expect(categories1[0].type).toBe(categories2[0].type);
          expect(categories2[0].type).toBe(categories3[0].type);
        }),
        { numRuns: 100 }
      );
    });

    it('should consistently categorize identical failures in different orders', () => {
      fc.assert(
        fc.property(
          fc.array(failureArbitrary(), { minLength: 2, maxLength: 10 }),
          (failures) => {
            // Categorize failures in original order
            const categories1 = analyzer.categorizeFailures(failures);

            // Categorize failures in reversed order
            const reversedFailures = [...failures].reverse();
            const categories2 = analyzer.categorizeFailures(reversedFailures);

            // Property: Same failures should produce same category types regardless of order
            // (though the order of categories may differ)
            const types1 = categories1.map((c) => c.type).sort();
            const types2 = categories2.map((c) => c.type).sort();

            expect(types1).toEqual(types2);

            // Property: Each category should contain the same number of failures
            for (const cat1 of categories1) {
              const matchingCat2 = categories2.find((c) => c.type === cat1.type);
              expect(matchingCat2).toBeDefined();
              expect(cat1.failures.length).toBe(matchingCat2!.failures.length);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should categorize lint failures consistently as "lint" type', () => {
      fc.assert(
        fc.property(
          fc.array(lintFailureArbitrary(), { minLength: 1, maxLength: 5 }),
          (failures) => {
            // Categorize lint failures
            const categories = analyzer.categorizeFailures(failures);

            // Property: All lint-related failures should be categorized as "lint"
            expect(categories.length).toBeGreaterThan(0);
            const lintCategory = categories.find((c) => c.type === 'lint');
            expect(lintCategory).toBeDefined();
            expect(lintCategory!.failures.length).toBe(failures.length);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should categorize test failures consistently as "test" type', () => {
      fc.assert(
        fc.property(
          fc.array(testFailureArbitrary(), { minLength: 1, maxLength: 5 }),
          (failures) => {
            // Categorize test failures
            const categories = analyzer.categorizeFailures(failures);

            // Property: All test-related failures should be categorized as "test"
            expect(categories.length).toBeGreaterThan(0);
            const testCategory = categories.find((c) => c.type === 'test');
            expect(testCategory).toBeDefined();
            expect(testCategory!.failures.length).toBe(failures.length);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should categorize build failures consistently as "build" type', () => {
      fc.assert(
        fc.property(
          fc.array(buildFailureArbitrary(), { minLength: 1, maxLength: 5 }),
          (failures) => {
            // Categorize build failures
            const categories = analyzer.categorizeFailures(failures);

            // Property: All build-related failures should be categorized as "build"
            expect(categories.length).toBeGreaterThan(0);
            const buildCategory = categories.find((c) => c.type === 'build');
            expect(buildCategory).toBeDefined();
            expect(buildCategory!.failures.length).toBe(failures.length);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should categorize dependency failures consistently as "dependency" type', () => {
      fc.assert(
        fc.property(
          fc.array(dependencyFailureArbitrary(), { minLength: 1, maxLength: 5 }),
          (failures) => {
            // Categorize dependency failures
            const categories = analyzer.categorizeFailures(failures);

            // Property: All dependency-related failures should be categorized as "dependency"
            expect(categories.length).toBeGreaterThan(0);
            const depCategory = categories.find((c) => c.type === 'dependency');
            expect(depCategory).toBeDefined();
            expect(depCategory!.failures.length).toBe(failures.length);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should maintain consistency when categorizing mixed failure types', () => {
      fc.assert(
        fc.property(
          fc.tuple(
            fc.array(lintFailureArbitrary(), { minLength: 1, maxLength: 3 }),
            fc.array(testFailureArbitrary(), { minLength: 1, maxLength: 3 }),
            fc.array(buildFailureArbitrary(), { minLength: 1, maxLength: 3 })
          ),
          ([lintFailures, testFailures, buildFailures]) => {
            const allFailures = [...lintFailures, ...testFailures, ...buildFailures];

            // Categorize mixed failures
            const categories = analyzer.categorizeFailures(allFailures);

            // Property: Should have separate categories for each type
            const types = categories.map((c) => c.type);
            expect(types).toContain('lint');
            expect(types).toContain('test');
            expect(types).toContain('build');

            // Property: Total failures across categories should equal input
            const totalCategorized = categories.reduce(
              (sum, cat) => sum + cat.failures.length,
              0
            );
            expect(totalCategorized).toBe(allFailures.length);

            // Property: Each failure should appear in exactly one category
            const categorizedFailures = categories.flatMap((cat) => cat.failures);
            expect(categorizedFailures.length).toBe(allFailures.length);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should produce deterministic categories when called multiple times with same input', () => {
      fc.assert(
        fc.property(
          fc.array(
            fc.oneof(
              lintFailureArbitrary(),
              testFailureArbitrary(),
              buildFailureArbitrary(),
              dependencyFailureArbitrary()
            ),
            { minLength: 3, maxLength: 10 }
          ),
          (failures) => {
            // Categorize the same set of failures multiple times
            const categories1 = analyzer.categorizeFailures(failures);
            const categories2 = analyzer.categorizeFailures(failures);
            const categories3 = analyzer.categorizeFailures(failures);

            // Property: Should produce identical results each time
            expect(categories1.length).toBe(categories2.length);
            expect(categories2.length).toBe(categories3.length);

            // Property: Each category type should appear the same number of times
            const types1 = categories1.map((c) => c.type).sort();
            const types2 = categories2.map((c) => c.type).sort();
            const types3 = categories3.map((c) => c.type).sort();

            expect(types1).toEqual(types2);
            expect(types2).toEqual(types3);

            // Property: Each category should contain the same failures
            for (let i = 0; i < categories1.length; i++) {
              const cat1 = categories1.find((c) => c.type === types1[i]);
              const cat2 = categories2.find((c) => c.type === types2[i]);
              const cat3 = categories3.find((c) => c.type === types3[i]);

              expect(cat1!.failures.length).toBe(cat2!.failures.length);
              expect(cat2!.failures.length).toBe(cat3!.failures.length);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should not lose or duplicate failures during categorization', () => {
      fc.assert(
        fc.property(
          fc.array(failureArbitrary(), { minLength: 1, maxLength: 20 }),
          (failures) => {
            // Categorize failures
            const categories = analyzer.categorizeFailures(failures);

            // Property: Total failures in categories should equal input count
            const totalCategorized = categories.reduce(
              (sum, cat) => sum + cat.failures.length,
              0
            );
            expect(totalCategorized).toBe(failures.length);

            // Property: Each input failure should appear exactly once in categories
            const categorizedFailures = categories.flatMap((cat) => cat.failures);
            const normalizedInput = failures.map(normalizeFailure).sort();
            const normalizedOutput = categorizedFailures.map(normalizeFailure).sort();

            expect(normalizedOutput).toEqual(normalizedInput);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle empty failure array consistently', () => {
      // Categorize empty array multiple times
      const categories1 = analyzer.categorizeFailures([]);
      const categories2 = analyzer.categorizeFailures([]);
      const categories3 = analyzer.categorizeFailures([]);

      // Property: Empty input should always produce empty categories
      expect(categories1).toEqual([]);
      expect(categories2).toEqual([]);
      expect(categories3).toEqual([]);
    });

    it('should assign each failure to exactly one category', () => {
      fc.assert(
        fc.property(
          fc.array(failureArbitrary(), { minLength: 1, maxLength: 15 }),
          (failures) => {
            // Categorize failures
            const categories = analyzer.categorizeFailures(failures);

            // Property: No failure should appear in multiple categories
            const seenFailures = new Set<string>();
            for (const category of categories) {
              for (const failure of category.failures) {
                const key = normalizeFailure(failure);
                expect(seenFailures.has(key)).toBe(false);
                seenFailures.add(key);
              }
            }

            // Property: All input failures should be accounted for
            expect(seenFailures.size).toBe(failures.length);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should maintain category consistency with duplicate failures', () => {
      fc.assert(
        fc.property(failureArbitrary(), fc.integer({ min: 2, max: 5 }), (failure, count) => {
          // Create array with duplicate failures
          const failures = Array(count).fill(failure);

          // Categorize duplicates
          const categories = analyzer.categorizeFailures(failures);

          // Property: All duplicates should be in the same category
          expect(categories.length).toBe(1);
          expect(categories[0].failures.length).toBe(count);

          // Property: All failures in the category should have the same type
          const firstType = categories[0].type;
          for (const cat of categories) {
            expect(cat.type).toBe(firstType);
          }
        }),
        { numRuns: 100 }
      );
    });

    it('should provide consistent suggested fixes for each category type', () => {
      fc.assert(
        fc.property(
          fc.array(
            fc.oneof(
              lintFailureArbitrary(),
              testFailureArbitrary(),
              buildFailureArbitrary(),
              dependencyFailureArbitrary()
            ),
            { minLength: 1, maxLength: 10 }
          ),
          (failures) => {
            // Categorize failures multiple times
            const categories1 = analyzer.categorizeFailures(failures);
            const categories2 = analyzer.categorizeFailures(failures);

            // Property: Same category types should have same suggested fixes
            for (const cat1 of categories1) {
              const cat2 = categories2.find((c) => c.type === cat1.type);
              expect(cat2).toBeDefined();
              expect(cat1.suggestedFix).toBe(cat2!.suggestedFix);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});
