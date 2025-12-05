/**
 * Property-Based Tests for Linting Completeness
 *
 * Feature: code-quality-and-release-automation, Property 1: Linting Completeness
 * Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5
 *
 * These tests verify that ESLint produces zero errors and zero warnings
 * for all source files in the src directory.
 */

import { describe, it, expect } from "vitest";
import fc from "fast-check";
import { ESLint } from "eslint";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Helper: Get all TypeScript/React files in src directory
 */
function getAllSourceFiles(dir: string, fileList: string[] = []): string[] {
  const files = fs.readdirSync(dir);

  for (const file of files) {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);

    if (stat.isDirectory()) {
      // Skip test directories, node_modules, and build directories
      if (!file.startsWith(".") && file !== "node_modules" && file !== "dist" && file !== "build") {
        getAllSourceFiles(filePath, fileList);
      }
    } else if (file.endsWith(".ts") || file.endsWith(".tsx")) {
      fileList.push(filePath);
    }
  }

  return fileList;
}

/**
 * Helper: Run ESLint on a file
 */
async function lintFile(filePath: string): Promise<ESLint.LintResult> {
  const eslint = new ESLint({
    overrideConfigFile: path.resolve(process.cwd(), "eslint.config.js"),
  });

  const results = await eslint.lintFiles([filePath]);
  return results[0];
}

/**
 * Helper: Run ESLint on multiple files
 */
async function lintFiles(filePaths: string[]): Promise<ESLint.LintResult[]> {
  const eslint = new ESLint({
    overrideConfigFile: path.resolve(process.cwd(), "eslint.config.js"),
  });

  return await eslint.lintFiles(filePaths);
}

describe("Linting Completeness - Property-Based Tests", () => {
  /**
   * Feature: code-quality-and-release-automation, Property 1: Linting Completeness
   * Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5
   *
   * For any source file in the src directory, running ESLint should produce
   * zero errors and zero warnings after fixes are applied.
   */
  describe("Property 1: Linting Completeness", () => {
    it("should produce zero errors and warnings for all source files", async () => {
      // Get all source files
      const srcDir = path.resolve(process.cwd(), "src");
      const allFiles = getAllSourceFiles(srcDir);

      // Filter out test files for this property test
      const sourceFiles = allFiles.filter(
        (file) =>
          !file.includes("/test/") && !file.endsWith(".test.ts") && !file.endsWith(".test.tsx")
      );

      // Property: For any subset of source files, linting should produce zero errors/warnings
      await fc.assert(
        fc.asyncProperty(
          fc.subarray(sourceFiles, { minLength: 1, maxLength: Math.min(10, sourceFiles.length) }),
          async (filesToLint) => {
            const results = await lintFiles(filesToLint);

            // Property: Each file should have zero errors
            for (const result of results) {
              expect(result.errorCount).toBe(0);
            }

            // Property: Each file should have zero warnings
            for (const result of results) {
              expect(result.warningCount).toBe(0);
            }

            // Property: Total error count should be zero
            const totalErrors = results.reduce((sum, r) => sum + r.errorCount, 0);
            expect(totalErrors).toBe(0);

            // Property: Total warning count should be zero
            const totalWarnings = results.reduce((sum, r) => sum + r.warningCount, 0);
            expect(totalWarnings).toBe(0);
          }
        ),
        { numRuns: 100 }
      );
    }, 60000); // 60 second timeout for property test

    it("should have zero errors and warnings for React components", async () => {
      // Get all React component files
      const srcDir = path.resolve(process.cwd(), "src");
      const allFiles = getAllSourceFiles(srcDir);

      const componentFiles = allFiles.filter(
        (file) => file.endsWith(".tsx") && !file.includes("/test/") && !file.endsWith(".test.tsx")
      );

      // Property: For any React component file, linting should produce zero errors/warnings
      await fc.assert(
        fc.asyncProperty(
          fc.subarray(componentFiles, {
            minLength: 1,
            maxLength: Math.min(10, componentFiles.length),
          }),
          async (filesToLint) => {
            const results = await lintFiles(filesToLint);

            // Property: Each component should have zero errors
            for (const result of results) {
              expect(result.errorCount).toBe(0);
            }

            // Property: Each component should have zero warnings
            for (const result of results) {
              expect(result.warningCount).toBe(0);
            }

            // Property: No React-specific violations (display names, hooks rules, etc.)
            for (const result of results) {
              const reactViolations = result.messages.filter(
                (msg) => msg.ruleId?.startsWith("react/") || msg.ruleId?.startsWith("react-hooks/")
              );
              expect(reactViolations.length).toBe(0);
            }
          }
        ),
        { numRuns: 100 }
      );
    }, 60000);

    it("should have zero TypeScript-specific errors", async () => {
      // Get all TypeScript files
      const srcDir = path.resolve(process.cwd(), "src");
      const allFiles = getAllSourceFiles(srcDir);

      const tsFiles = allFiles.filter(
        (file) =>
          (file.endsWith(".ts") || file.endsWith(".tsx")) &&
          !file.includes("/test/") &&
          !file.endsWith(".test.ts") &&
          !file.endsWith(".test.tsx")
      );

      // Property: For any TypeScript file, there should be no TypeScript-specific violations
      await fc.assert(
        fc.asyncProperty(
          fc.subarray(tsFiles, { minLength: 1, maxLength: Math.min(10, tsFiles.length) }),
          async (filesToLint) => {
            const results = await lintFiles(filesToLint);

            // Property: No TypeScript-specific violations (no-explicit-any, etc.)
            for (const result of results) {
              const tsViolations = result.messages.filter((msg) =>
                msg.ruleId?.startsWith("@typescript-eslint/")
              );
              expect(tsViolations.length).toBe(0);
            }

            // Property: Total error count should be zero
            const totalErrors = results.reduce((sum, r) => sum + r.errorCount, 0);
            expect(totalErrors).toBe(0);

            // Property: Total warning count should be zero
            const totalWarnings = results.reduce((sum, r) => sum + r.warningCount, 0);
            expect(totalWarnings).toBe(0);
          }
        ),
        { numRuns: 100 }
      );
    }, 60000);

    it("should maintain zero errors across random file selections", async () => {
      // Get all source files
      const srcDir = path.resolve(process.cwd(), "src");
      const allFiles = getAllSourceFiles(srcDir);

      const sourceFiles = allFiles.filter(
        (file) =>
          !file.includes("/test/") && !file.endsWith(".test.ts") && !file.endsWith(".test.tsx")
      );

      // Property: Regardless of which files we select, the total should be zero errors/warnings
      await fc.assert(
        fc.asyncProperty(
          fc.integer({ min: 1, max: Math.min(15, sourceFiles.length) }),
          async (numFiles) => {
            // Randomly select numFiles files
            const shuffled = [...sourceFiles].sort(() => Math.random() - 0.5);
            const selectedFiles = shuffled.slice(0, numFiles);

            const results = await lintFiles(selectedFiles);

            // Property: Total errors should always be zero
            const totalErrors = results.reduce((sum, r) => sum + r.errorCount, 0);
            expect(totalErrors).toBe(0);

            // Property: Total warnings should always be zero
            const totalWarnings = results.reduce((sum, r) => sum + r.warningCount, 0);
            expect(totalWarnings).toBe(0);

            // Property: Number of results should match number of files
            expect(results.length).toBe(selectedFiles.length);
          }
        ),
        { numRuns: 100 }
      );
    }, 60000);

    it("should have consistent linting results across multiple runs", async () => {
      // Get all source files
      const srcDir = path.resolve(process.cwd(), "src");
      const allFiles = getAllSourceFiles(srcDir);

      const sourceFiles = allFiles.filter(
        (file) =>
          !file.includes("/test/") && !file.endsWith(".test.ts") && !file.endsWith(".test.tsx")
      );

      // Property: Running ESLint multiple times on the same files should produce consistent results
      await fc.assert(
        fc.asyncProperty(
          fc.subarray(sourceFiles, { minLength: 1, maxLength: Math.min(5, sourceFiles.length) }),
          async (filesToLint) => {
            // Run linting three times
            const results1 = await lintFiles(filesToLint);
            const results2 = await lintFiles(filesToLint);
            const results3 = await lintFiles(filesToLint);

            // Property: Error counts should be consistent
            const errors1 = results1.reduce((sum, r) => sum + r.errorCount, 0);
            const errors2 = results2.reduce((sum, r) => sum + r.errorCount, 0);
            const errors3 = results3.reduce((sum, r) => sum + r.errorCount, 0);

            expect(errors1).toBe(errors2);
            expect(errors2).toBe(errors3);

            // Property: Warning counts should be consistent
            const warnings1 = results1.reduce((sum, r) => sum + r.warningCount, 0);
            const warnings2 = results2.reduce((sum, r) => sum + r.warningCount, 0);
            const warnings3 = results3.reduce((sum, r) => sum + r.warningCount, 0);

            expect(warnings1).toBe(warnings2);
            expect(warnings2).toBe(warnings3);

            // Property: All should be zero
            expect(errors1).toBe(0);
            expect(warnings1).toBe(0);
          }
        ),
        { numRuns: 50 } // Reduced runs since we're running linting 3x per iteration
      );
    }, 60000);
  });
});
