/**
 * Property-Based Tests for Checksum Generation
 *
 * **Feature: github-releases-installer, Property 43: Checksums generated for all installers**
 * **Validates: Requirements 10.1**
 *
 * Tests that SHA256 checksums are correctly generated for all installer files.
 */

import { describe, it, expect, beforeAll, afterAll } from "vitest";
import * as fc from "fast-check";
import * as fs from "fs";
import * as path from "path";
import * as crypto from "crypto";

const {
  calculateChecksum,
  shouldIncludeFile,
  generateChecksums,
  writeChecksumsFile,
} = require("../../../scripts/generate-checksums");

describe("Property 43: Checksums generated for all installers", () => {
  const testDir = path.join(__dirname, "../../..", "test-artifacts");

  beforeAll(() => {
    // Create test directory
    if (!fs.existsSync(testDir)) {
      fs.mkdirSync(testDir, { recursive: true });
    }
  });

  afterAll(() => {
    // Clean up test directory
    if (fs.existsSync(testDir)) {
      fs.rmSync(testDir, { recursive: true, force: true });
    }
  });

  /**
   * Property: For any installer file, a SHA256 checksum should be generated
   */
  it("should generate SHA256 checksum for any installer file", async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate random file content
        fc.uint8Array({ minLength: 100, maxLength: 10000 }),
        // Generate random installer filename (alphanumeric only to avoid filesystem issues)
        fc
          .constantFrom(".exe", ".dmg", ".zip", ".AppImage", ".deb")
          .chain((ext) =>
            fc.stringMatching(/^[a-zA-Z0-9_-]{5,20}$/).map((name) => `test-installer-${name}${ext}`)
          ),
        async (content, filename) => {
          // Create test file
          const filePath = path.join(testDir, filename);
          fs.writeFileSync(filePath, Buffer.from(content));

          try {
            // Generate checksum using our function
            const checksum = await calculateChecksum(filePath);

            // Verify checksum is a valid SHA256 hash (64 hex characters)
            expect(checksum).toMatch(/^[a-f0-9]{64}$/);

            // Verify checksum matches independently calculated hash
            const hash = crypto.createHash("sha256");
            hash.update(Buffer.from(content));
            const expectedChecksum = hash.digest("hex");

            expect(checksum).toBe(expectedChecksum);
          } finally {
            // Clean up
            if (fs.existsSync(filePath)) {
              fs.unlinkSync(filePath);
            }
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: For any set of installer files, checksums should be generated for all of them
   */
  it("should generate checksums for all installer files in a directory", async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate array of installer files (alphanumeric filenames only)
        fc.array(
          fc.record({
            name: fc
              .constantFrom(".exe", ".dmg", ".zip", ".AppImage", ".deb")
              .chain((ext) =>
                fc.stringMatching(/^[a-zA-Z0-9_-]{5,15}$/).map((name) => `installer-${name}${ext}`)
              ),
            content: fc.uint8Array({ minLength: 100, maxLength: 5000 }),
          }),
          { minLength: 1, maxLength: 10 }
        ),
        async (files) => {
          // Create unique filenames to avoid collisions
          const uniqueFiles = files.map((file, index) => ({
            ...file,
            name: `${index}-${file.name}`,
          }));

          // Create test files
          for (const file of uniqueFiles) {
            const filePath = path.join(testDir, file.name);
            fs.writeFileSync(filePath, Buffer.from(file.content));
          }

          try {
            // Generate checksums
            const checksums = await generateChecksums(testDir);

            // Verify we got checksums for all installer files
            const installerFiles = uniqueFiles.filter((f) => shouldIncludeFile(f.name));
            expect(checksums.length).toBe(installerFiles.length);

            // Verify each checksum is valid
            for (const { file, checksum } of checksums) {
              expect(checksum).toMatch(/^[a-f0-9]{64}$/);

              // Verify checksum is correct
              const fileData = uniqueFiles.find((f) => f.name === file);
              if (fileData) {
                const hash = crypto.createHash("sha256");
                hash.update(Buffer.from(fileData.content));
                const expectedChecksum = hash.digest("hex");
                expect(checksum).toBe(expectedChecksum);
              }
            }
          } finally {
            // Clean up
            for (const file of uniqueFiles) {
              const filePath = path.join(testDir, file.name);
              if (fs.existsSync(filePath)) {
                fs.unlinkSync(filePath);
              }
            }
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Checksum generation should be deterministic
   * For any file content, generating the checksum multiple times should produce the same result
   */
  it("should generate the same checksum for the same file content", async () => {
    await fc.assert(
      fc.asyncProperty(fc.uint8Array({ minLength: 100, maxLength: 5000 }), async (content) => {
        const filename = "test-deterministic.exe";
        const filePath = path.join(testDir, filename);
        fs.writeFileSync(filePath, Buffer.from(content));

        try {
          // Generate checksum multiple times
          const checksum1 = await calculateChecksum(filePath);
          const checksum2 = await calculateChecksum(filePath);
          const checksum3 = await calculateChecksum(filePath);

          // All checksums should be identical
          expect(checksum1).toBe(checksum2);
          expect(checksum2).toBe(checksum3);
        } finally {
          if (fs.existsSync(filePath)) {
            fs.unlinkSync(filePath);
          }
        }
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Only installer files should be included in checksum generation
   */
  it("should only include installer files and exclude other files", () => {
    fc.assert(
      fc.property(fc.string({ minLength: 1, maxLength: 50 }), (filename) => {
        const isInstaller = shouldIncludeFile(filename);
        const hasInstallerExtension = [".exe", ".dmg", ".zip", ".AppImage", ".deb"].some((ext) =>
          filename.endsWith(ext)
        );
        const isExcluded = [".blockmap", "SHA256SUMS.txt"].some((pattern) =>
          filename.includes(pattern)
        );

        // Should include if it has installer extension and is not excluded
        const expectedResult = hasInstallerExtension && !isExcluded;
        expect(isInstaller).toBe(expectedResult);
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: SHA256SUMS.txt file should contain all installer checksums
   */
  it("should write all checksums to SHA256SUMS.txt in correct format", async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.array(
          fc.record({
            name: fc
              .constantFrom(".exe", ".dmg", ".AppImage")
              .chain((ext) =>
                fc.stringMatching(/^[a-zA-Z0-9_-]{5,15}$/).map((name) => `file-${name}${ext}`)
              ),
            content: fc.uint8Array({ minLength: 100, maxLength: 1000 }),
          }),
          { minLength: 1, maxLength: 5 }
        ),
        async (files) => {
          // Create unique filenames
          const uniqueFiles = files.map((file, index) => ({
            ...file,
            name: `${index}-${file.name}`,
          }));

          // Create test files and calculate expected checksums
          const expectedChecksums = [];
          for (const file of uniqueFiles) {
            const filePath = path.join(testDir, file.name);
            fs.writeFileSync(filePath, Buffer.from(file.content));

            const hash = crypto.createHash("sha256");
            hash.update(Buffer.from(file.content));
            expectedChecksums.push({
              file: file.name,
              checksum: hash.digest("hex"),
            });
          }

          try {
            // Write checksums file
            const outputPath = path.join(testDir, "SHA256SUMS.txt");
            writeChecksumsFile(expectedChecksums, outputPath);

            // Read and verify the file
            const content = fs.readFileSync(outputPath, "utf8");
            const lines = content.trim().split("\n");

            // Should have one line per file
            expect(lines.length).toBe(expectedChecksums.length);

            // Each line should be in format: <hash>  <filename>
            for (let i = 0; i < lines.length; i++) {
              const line = lines[i];
              const [hash, ...filenameParts] = line.split(/\s+/);
              const filename = filenameParts.join(" ");

              // Verify format
              expect(hash).toMatch(/^[a-f0-9]{64}$/);
              expect(filename).toBeTruthy();

              // Verify checksum matches
              const expected = expectedChecksums.find((c) => c.file === filename);
              expect(expected).toBeTruthy();
              expect(hash).toBe(expected?.checksum);
            }
          } finally {
            // Clean up
            for (const file of uniqueFiles) {
              const filePath = path.join(testDir, file.name);
              if (fs.existsSync(filePath)) {
                fs.unlinkSync(filePath);
              }
            }
            const outputPath = path.join(testDir, "SHA256SUMS.txt");
            if (fs.existsSync(outputPath)) {
              fs.unlinkSync(outputPath);
            }
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Checksum should change if file content changes
   */
  it("should generate different checksums for different file contents", async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.uint8Array({ minLength: 100, maxLength: 5000 }),
        fc.uint8Array({ minLength: 100, maxLength: 5000 }),
        async (content1, content2) => {
          // Skip if contents are identical
          fc.pre(!Buffer.from(content1).equals(Buffer.from(content2)));

          const filename = "test-different.exe";
          const filePath = path.join(testDir, filename);

          try {
            // Generate checksum for first content
            fs.writeFileSync(filePath, Buffer.from(content1));
            const checksum1 = await calculateChecksum(filePath);

            // Generate checksum for second content
            fs.writeFileSync(filePath, Buffer.from(content2));
            const checksum2 = await calculateChecksum(filePath);

            // Checksums should be different
            expect(checksum1).not.toBe(checksum2);
          } finally {
            if (fs.existsSync(filePath)) {
              fs.unlinkSync(filePath);
            }
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});
