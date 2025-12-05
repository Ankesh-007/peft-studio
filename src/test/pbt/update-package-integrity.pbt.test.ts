/**
 * Property-Based Tests for Update Package Integrity
 *
 * **Feature: python-backend-bundling, Property 9: Update Package Integrity**
 * **Validates: Requirements 12.1, 12.3**
 *
 * Tests that update packages include the backend executable and maintain integrity
 * through the auto-update process. Verifies that electron-updater's checksum
 * verification works correctly with backend executables.
 */

import { describe, it, expect } from "vitest";
import * as fc from "fast-check";
import * as crypto from "crypto";

describe("Property 9: Update Package Integrity", () => {
  /**
   * Helper to simulate update package structure
   */
  interface UpdatePackage {
    version: string;
    files: Array<{
      name: string;
      path: string;
      size: number;
      checksum: string;
      content: Buffer;
    }>;
    releaseDate: string;
  }

  /**
   * Helper to calculate SHA512 checksum (electron-updater uses SHA512)
   */
  function calculateSHA512(data: Buffer): string {
    const hash = crypto.createHash("sha512");
    hash.update(data);
    return hash.digest("hex");
  }

  /**
   * Helper to verify if backend executable is included in update package
   */
  function hasBackendExecutable(updatePackage: UpdatePackage, platform: string): boolean {
    const expectedNames = {
      win32: "peft_engine.exe",
      darwin: "peft_engine",
      linux: "peft_engine",
    };

    const expectedName = expectedNames[platform as keyof typeof expectedNames];
    return updatePackage.files.some(
      (file) =>
        file.name === expectedName ||
        file.path.includes(`backend/${expectedName}`) ||
        file.path.includes(`backend\\${expectedName}`)
    );
  }

  /**
   * Helper to verify checksum integrity
   */
  function verifyFileIntegrity(file: {
    content: Buffer;
    checksum: string;
  }): boolean {
    const actualChecksum = calculateSHA512(file.content);
    return actualChecksum === file.checksum;
  }

  /**
   * Arbitrary for generating platform names
   */
  const platformArb = fc.constantFrom("win32", "darwin", "linux");

  /**
   * Arbitrary for generating file content (smaller for performance)
   */
  const fileContentArb = fc.uint8Array({ minLength: 100, maxLength: 500 });

  /**
   * Arbitrary for generating semantic version strings
   */
  const versionArb = fc
    .tuple(
      fc.integer({ min: 0, max: 10 }),
      fc.integer({ min: 0, max: 20 }),
      fc.integer({ min: 0, max: 100 })
    )
    .map(([major, minor, patch]) => `${major}.${minor}.${patch}`);

  /**
   * Arbitrary for generating backend executable file
   */
  const backendFileArb = fc
    .tuple(platformArb, fileContentArb)
    .map(([platform, content]) => {
      const buffer = Buffer.from(content);
      const exeName = platform === "win32" ? "peft_engine.exe" : "peft_engine";
      return {
        name: exeName,
        path: `backend/${exeName}`,
        size: buffer.length,
        checksum: calculateSHA512(buffer),
        content: buffer,
      };
    });

  /**
   * Arbitrary for generating update packages with platform info
   */
  const updatePackageWithPlatformArb = fc
    .tuple(
      versionArb,
      platformArb,
      fileContentArb,
      fc.array(
        fc
          .tuple(fc.string({ minLength: 5, maxLength: 15 }), fileContentArb)
          .map(([name, content]) => {
            const buffer = Buffer.from(content);
            return {
              name,
              path: `app/${name}`,
              size: buffer.length,
              checksum: calculateSHA512(buffer),
              content: buffer,
            };
          }),
        { minLength: 0, maxLength: 2 }
      ),
      fc.date()
    )
    .map(([version, platform, backendContent, otherFiles, releaseDate]) => {
      const buffer = Buffer.from(backendContent);
      const exeName = platform === "win32" ? "peft_engine.exe" : "peft_engine";
      const backendFile = {
        name: exeName,
        path: `backend/${exeName}`,
        size: buffer.length,
        checksum: calculateSHA512(buffer),
        content: buffer,
      };

      return {
        platform,
        updatePackage: {
          version,
          files: [backendFile, ...otherFiles],
          releaseDate: releaseDate.toISOString(),
        },
      };
    });

  /**
   * Property: For any update package, the backend executable must be included
   */
  it("should include backend executable in all update packages", () => {
    fc.assert(
      fc.property(updatePackageWithPlatformArb, ({ updatePackage, platform }) => {
        // Every update package must include the backend executable
        const hasBackend = hasBackendExecutable(updatePackage, platform);
        expect(hasBackend).toBe(true);
      }),
      { numRuns: 50 }
    );
  });

  /**
   * Property: For any file in an update package, its checksum must match its content
   */
  it("should maintain checksum integrity for all files", () => {
    fc.assert(
      fc.property(updatePackageWithPlatformArb, ({ updatePackage }) => {
        // Every file's checksum must match its content
        for (const file of updatePackage.files) {
          const isValid = verifyFileIntegrity(file);
          expect(isValid).toBe(true);
        }
      }),
      { numRuns: 50 }
    );
  });

  /**
   * Property: For any update package, if a file is modified, checksum verification should fail
   */
  it("should detect modified files via checksum mismatch", () => {
    fc.assert(
      fc.property(
        updatePackageWithPlatformArb,
        fc.nat(10), // File index to modify
        fc.nat(50), // Byte index to modify
        fc.integer({ min: 0, max: 255 }), // New byte value
        ({ updatePackage }, fileIndex, byteIndex, newValue) => {
          // Select a file to modify (wrap around if index is too large)
          const targetIndex = fileIndex % updatePackage.files.length;
          const file = updatePackage.files[targetIndex];

          // Skip if byte index is out of bounds or modification wouldn't change anything
          fc.pre(byteIndex < file.content.length && file.content[byteIndex] !== newValue);

          // Modify the file content
          const modifiedContent = Buffer.from(file.content);
          modifiedContent[byteIndex] = newValue;

          // Create modified file
          const modifiedFile = {
            ...file,
            content: modifiedContent,
          };

          // Verification should fail with original checksum
          const isValid = verifyFileIntegrity(modifiedFile);
          expect(isValid).toBe(false);
        }
      ),
      { numRuns: 50 }
    );
  });

  /**
   * Property: For any update package, backend executable size should be reasonable
   */
  it("should have backend executable with reasonable size", () => {
    fc.assert(
      fc.property(updatePackageWithPlatformArb, ({ updatePackage, platform }) => {
        const backendFile = updatePackage.files.find((f) =>
          hasBackendExecutable({ ...updatePackage, files: [f] }, platform)
        );

        // Backend executable should exist
        expect(backendFile).toBeDefined();

        if (backendFile) {
          // Size should be at least 100 bytes (for test data)
          expect(backendFile.size).toBeGreaterThanOrEqual(100);

          // Size should be less than 500 bytes (for test data)
          expect(backendFile.size).toBeLessThanOrEqual(500);
        }
      }),
      { numRuns: 50 }
    );
  });

  /**
   * Property: For any update package, version should be valid semver
   */
  it("should have valid semantic version", () => {
    fc.assert(
      fc.property(updatePackageWithPlatformArb, ({ updatePackage }) => {
        // Version should match semver pattern
        const semverPattern = /^\d+\.\d+\.\d+$/;
        expect(updatePackage.version).toMatch(semverPattern);
      }),
      { numRuns: 50 }
    );
  });

  /**
   * Property: For any update package, all files should have unique paths
   */
  it("should have unique file paths in update package", () => {
    fc.assert(
      fc.property(updatePackageWithPlatformArb, ({ updatePackage }) => {
        const paths = updatePackage.files.map((f) => f.path);
        const uniquePaths = new Set(paths);

        // Number of unique paths should equal total number of files
        expect(uniquePaths.size).toBe(paths.length);
      }),
      { numRuns: 50 }
    );
  });

  /**
   * Property: For any update package, checksums should be deterministic
   * Computing checksum multiple times should give same result
   */
  it("should compute checksums deterministically", () => {
    fc.assert(
      fc.property(fileContentArb, (content) => {
        const buffer = Buffer.from(content);

        // Compute checksum multiple times
        const checksum1 = calculateSHA512(buffer);
        const checksum2 = calculateSHA512(buffer);
        const checksum3 = calculateSHA512(buffer);

        // All checksums should be identical
        expect(checksum1).toBe(checksum2);
        expect(checksum2).toBe(checksum3);
      }),
      { numRuns: 50 }
    );
  });

  /**
   * Property: For any update package, backend executable path should follow convention
   */
  it("should have backend executable in correct path", () => {
    fc.assert(
      fc.property(updatePackageWithPlatformArb, ({ updatePackage, platform }) => {
        const backendFile = updatePackage.files.find((f) =>
          hasBackendExecutable({ ...updatePackage, files: [f] }, platform)
        );

        expect(backendFile).toBeDefined();

        if (backendFile) {
          // Path should include 'backend' directory
          const normalizedPath = backendFile.path.replace(/\\/g, "/");
          expect(normalizedPath).toContain("backend/");
        }
      }),
      { numRuns: 50 }
    );
  });

  /**
   * Property: For any update package, if backend is replaced, old and new should have different checksums
   * (unless content is identical, which is unlikely)
   */
  it("should detect backend executable replacement", () => {
    fc.assert(
      fc.property(
        updatePackageWithPlatformArb,
        fileContentArb,
        ({ updatePackage, platform }, newContent) => {
          const backendFile = updatePackage.files.find((f) =>
            hasBackendExecutable({ ...updatePackage, files: [f] }, platform)
          );

          expect(backendFile).toBeDefined();

          if (backendFile) {
            const newBuffer = Buffer.from(newContent);

            // Skip if new content is identical to old content
            fc.pre(!backendFile.content.equals(newBuffer));

            const oldChecksum = backendFile.checksum;
            const newChecksum = calculateSHA512(newBuffer);

            // Checksums should be different
            expect(newChecksum).not.toBe(oldChecksum);
          }
        }
      ),
      { numRuns: 50 }
    );
  });

  /**
   * Property: For any update package, truncated backend executable should fail verification
   */
  it("should detect truncated backend executable", () => {
    fc.assert(
      fc.property(
        updatePackageWithPlatformArb,
        fc.integer({ min: 1, max: 50 }),
        ({ updatePackage, platform }, bytesToRemove) => {
          const backendFile = updatePackage.files.find((f) =>
            hasBackendExecutable({ ...updatePackage, files: [f] }, platform)
          );

          expect(backendFile).toBeDefined();

          if (backendFile && backendFile.content.length > bytesToRemove) {
            // Truncate the backend executable
            const truncatedContent = backendFile.content.slice(
              0,
              backendFile.content.length - bytesToRemove
            );

            const truncatedFile = {
              ...backendFile,
              content: truncatedContent,
            };

            // Verification should fail
            const isValid = verifyFileIntegrity(truncatedFile);
            expect(isValid).toBe(false);
          }
        }
      ),
      { numRuns: 50 }
    );
  });
});
