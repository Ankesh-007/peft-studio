/**
 * Property-Based Test: Repository Cleanup Idempotence
 * Feature: peft-application-fix, Property 4: Repository Cleanup Idempotence
 * Validates: Requirements 4.1, 4.2, 4.3, 4.4
 *
 * Tests that running cleanup operations multiple times produces the same result
 * as running it once, and that critical files are never removed.
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fc from "fast-check";
import * as fs from "fs";
import * as path from "path";

// Critical files that should never be removed
const CRITICAL_FILES = [
  "package.json",
  "README.md",
  "LICENSE",
  ".gitignore",
  "build/.gitkeep",
  "build/README.md",
  "dist/.gitkeep",
  "release/.gitkeep",
];

// Directories that should be cleaned
const CLEANUP_DIRS = [
  ".hypothesis",
  ".pytest_cache",
  "coverage",
  "backend/.hypothesis",
  "backend/.pytest_cache",
];

// Files that should be removed (patterns)
const CLEANUP_FILE_PATTERNS = [/.*_COMPLETE\.md$/, /.*_STATUS\.md$/, /.*_SUMMARY\.md$/];

interface FileSystemState {
  files: string[];
  directories: string[];
}

/**
 * Capture the current state of the file system
 */
function captureFileSystemState(rootDir: string): FileSystemState {
  const files: string[] = [];
  const directories: string[] = [];

  function traverse(dir: string) {
    if (!fs.existsSync(dir)) return;

    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });

      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        const relativePath = path.relative(rootDir, fullPath);

        if (entry.isDirectory()) {
          directories.push(relativePath);
          traverse(fullPath);
        } else {
          files.push(relativePath);
        }
      }
    } catch (error) {
      // Skip directories we can't read
    }
  }

  traverse(rootDir);
  return { files, directories };
}

/**
 * Simulate cleanup operation
 */
function simulateCleanup(rootDir: string): void {
  // Remove cleanup directories
  for (const dir of CLEANUP_DIRS) {
    const fullPath = path.join(rootDir, dir);
    if (fs.existsSync(fullPath)) {
      try {
        fs.rmSync(fullPath, { recursive: true, force: true });
      } catch (error) {
        // Ignore errors
      }
    }
  }

  // Remove files matching cleanup patterns
  function removeMatchingFiles(dir: string) {
    if (!fs.existsSync(dir)) return;

    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });

      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);

        if (entry.isDirectory()) {
          removeMatchingFiles(fullPath);
        } else {
          const shouldRemove = CLEANUP_FILE_PATTERNS.some((pattern) => pattern.test(entry.name));

          if (shouldRemove) {
            try {
              fs.unlinkSync(fullPath);
            } catch (error) {
              // Ignore errors
            }
          }
        }
      }
    } catch (error) {
      // Skip directories we can't read
    }
  }

  removeMatchingFiles(rootDir);
}

/**
 * Check if critical files exist
 */
function checkCriticalFiles(rootDir: string): boolean {
  return CRITICAL_FILES.every((file) => {
    const fullPath = path.join(rootDir, file);
    return fs.existsSync(fullPath);
  });
}

describe("Property 4: Repository Cleanup Idempotence", () => {
  const testRootDir = path.join(process.cwd(), "test-cleanup-workspace");

  beforeEach(() => {
    // Create test workspace
    if (fs.existsSync(testRootDir)) {
      fs.rmSync(testRootDir, { recursive: true, force: true });
    }
    fs.mkdirSync(testRootDir, { recursive: true });
  });

  afterEach(() => {
    // Clean up test workspace
    if (fs.existsSync(testRootDir)) {
      fs.rmSync(testRootDir, { recursive: true, force: true });
    }
  });

  it("should produce the same result when run multiple times", () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            type: fc.constantFrom("file", "directory"),
            name: fc.oneof(
              fc.constant("test_COMPLETE.md"),
              fc.constant("build_STATUS.md"),
              fc.constant("deploy_SUMMARY.md"),
              fc.constant(".hypothesis/test.txt"),
              fc.constant("coverage/index.html"),
              fc.constant("regular-file.txt"),
              fc.constant("package.json"),
              fc.constant("README.md")
            ),
          }),
          { minLength: 5, maxLength: 20 }
        ),
        (fileStructure) => {
          // Create test file structure
          for (const item of fileStructure) {
            const fullPath = path.join(testRootDir, item.name);
            const dir = path.dirname(fullPath);

            if (!fs.existsSync(dir)) {
              fs.mkdirSync(dir, { recursive: true });
            }

            if (item.type === "file") {
              // Skip if path already exists as directory
              if (!fs.existsSync(fullPath) || !fs.statSync(fullPath).isDirectory()) {
                fs.writeFileSync(fullPath, "test content");
              }
            } else {
              if (!fs.existsSync(fullPath)) {
                fs.mkdirSync(fullPath, { recursive: true });
              }
            }
          }

          // Capture state before cleanup
          const stateBefore = captureFileSystemState(testRootDir);

          // Run cleanup first time
          simulateCleanup(testRootDir);
          const stateAfterFirst = captureFileSystemState(testRootDir);

          // Run cleanup second time
          simulateCleanup(testRootDir);
          const stateAfterSecond = captureFileSystemState(testRootDir);

          // States after first and second cleanup should be identical
          expect(stateAfterFirst.files.sort()).toEqual(stateAfterSecond.files.sort());
          expect(stateAfterFirst.directories.sort()).toEqual(stateAfterSecond.directories.sort());

          // Verify idempotence: no additional files removed
          const filesRemovedFirst = stateBefore.files.length - stateAfterFirst.files.length;
          const filesRemovedSecond = stateAfterFirst.files.length - stateAfterSecond.files.length;

          expect(filesRemovedSecond).toBe(0);
        }
      ),
      { numRuns: 100 }
    );
  });

  it("should never remove critical files", () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            name: fc.oneof(
              ...CRITICAL_FILES.map((f) => fc.constant(f)),
              fc.constant("test_COMPLETE.md"),
              fc.constant(".hypothesis/test.txt")
            ),
          }),
          { minLength: 3, maxLength: 15 }
        ),
        (fileStructure) => {
          // Create test file structure including critical files
          for (const item of fileStructure) {
            const fullPath = path.join(testRootDir, item.name);
            const dir = path.dirname(fullPath);

            if (!fs.existsSync(dir)) {
              fs.mkdirSync(dir, { recursive: true });
            }

            fs.writeFileSync(fullPath, "test content");
          }

          // Track which critical files were created
          const createdCriticalFiles = fileStructure
            .map((item) => item.name)
            .filter((name) => CRITICAL_FILES.includes(name));

          // Run cleanup
          simulateCleanup(testRootDir);

          // Verify all created critical files still exist
          for (const criticalFile of createdCriticalFiles) {
            const fullPath = path.join(testRootDir, criticalFile);
            expect(fs.existsSync(fullPath)).toBe(true);
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it("should remove all files matching cleanup patterns", () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            name: fc.oneof(
              fc.constant("TEST_COMPLETE.md"),
              fc.constant("BUILD_STATUS.md"),
              fc.constant("DEPLOY_SUMMARY.md"),
              fc.constant("CLEANUP_COMPLETE.md"),
              fc.constant("RELEASE_STATUS.md"),
              fc.constant("regular-file.md")
            ),
          }),
          { minLength: 3, maxLength: 10 }
        ),
        (fileStructure) => {
          // Create test file structure
          for (const item of fileStructure) {
            const fullPath = path.join(testRootDir, item.name);
            fs.writeFileSync(fullPath, "test content");
          }

          // Run cleanup
          simulateCleanup(testRootDir);

          // Verify no files matching cleanup patterns remain
          const remainingFiles = fs.readdirSync(testRootDir);

          for (const file of remainingFiles) {
            const matchesPattern = CLEANUP_FILE_PATTERNS.some((pattern) => pattern.test(file));
            expect(matchesPattern).toBe(false);
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it("should remove all cleanup directories", () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            dir: fc.constantFrom(...CLEANUP_DIRS),
            hasFiles: fc.boolean(),
          }),
          { minLength: 1, maxLength: CLEANUP_DIRS.length }
        ),
        (dirStructure) => {
          // Create test directory structure
          for (const item of dirStructure) {
            const fullPath = path.join(testRootDir, item.dir);
            fs.mkdirSync(fullPath, { recursive: true });

            if (item.hasFiles) {
              fs.writeFileSync(path.join(fullPath, "test.txt"), "test content");
            }
          }

          // Run cleanup
          simulateCleanup(testRootDir);

          // Verify cleanup directories are removed
          for (const dir of CLEANUP_DIRS) {
            const fullPath = path.join(testRootDir, dir);
            expect(fs.existsSync(fullPath)).toBe(false);
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});
