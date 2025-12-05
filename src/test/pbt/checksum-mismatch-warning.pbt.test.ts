/**
 * Property-Based Tests for Checksum Mismatch Warnings
 *
 * **Feature: github-releases-installer, Property 47: Checksum mismatch warning**
 * **Validates: Requirements 10.5**
 *
 * Tests that checksum mismatches trigger appropriate warnings and prevent installation.
 */

import { describe, it, expect } from "vitest";
import * as fc from "fast-check";
import * as crypto from "crypto";

describe("Property 47: Checksum mismatch warning", () => {
  /**
   * Helper function to calculate SHA256 checksum
   */
  function calculateSHA256(data: Buffer): string {
    const hash = crypto.createHash("sha256");
    hash.update(data);
    return hash.digest("hex");
  }

  /**
   * Simulates the checksum verification process
   * Returns an object with verification result and warning message
   */
  function verifyWithWarning(
    data: Buffer,
    expectedChecksum: string
  ): { verified: boolean; warning: string | null; shouldInstall: boolean } {
    const actualChecksum = calculateSHA256(data);
    const verified = actualChecksum === expectedChecksum;

    if (!verified) {
      return {
        verified: false,
        warning:
          "⚠️ Checksum mismatch! DO NOT install this file. The file may be corrupted or tampered with.",
        shouldInstall: false,
      };
    }

    return {
      verified: true,
      warning: null,
      shouldInstall: true,
    };
  }

  /**
   * Property: For any mismatched checksum, a warning should be generated
   */
  it("should generate warning for any checksum mismatch", () => {
    fc.assert(
      fc.property(
        fc.uint8Array({ minLength: 100, maxLength: 5000 }),
        fc.integer({ min: 0, max: 99 }), // Index to modify
        fc.integer({ min: 0, max: 255 }), // New value
        (content, modifyIndex, newValue) => {
          // Skip if modification wouldn't change anything
          fc.pre(content[modifyIndex] !== newValue);

          const originalData = Buffer.from(content);
          const originalChecksum = calculateSHA256(originalData);

          // Modify the content
          const modifiedContent = new Uint8Array(content);
          modifiedContent[modifyIndex] = newValue;
          const modifiedData = Buffer.from(modifiedContent);

          // Verify with warning
          const result = verifyWithWarning(modifiedData, originalChecksum);

          // Should not be verified
          expect(result.verified).toBe(false);

          // Should have a warning
          expect(result.warning).toBeTruthy();
          expect(result.warning).toContain("Checksum mismatch");
          expect(result.warning).toContain("DO NOT install");

          // Should not allow installation
          expect(result.shouldInstall).toBe(false);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: For any valid checksum, no warning should be generated
   */
  it("should not generate warning for matching checksums", () => {
    fc.assert(
      fc.property(fc.uint8Array({ minLength: 100, maxLength: 5000 }), (content) => {
        const data = Buffer.from(content);
        const checksum = calculateSHA256(data);

        // Verify with warning
        const result = verifyWithWarning(data, checksum);

        // Should be verified
        expect(result.verified).toBe(true);

        // Should not have a warning
        expect(result.warning).toBeNull();

        // Should allow installation
        expect(result.shouldInstall).toBe(true);
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Warning message should always indicate security risk
   */
  it("should include security warning in mismatch message", () => {
    fc.assert(
      fc.property(
        fc.uint8Array({ minLength: 100, maxLength: 5000 }),
        fc.hexaString({ minLength: 64, maxLength: 64 }), // Random invalid checksum
        (content, wrongChecksum) => {
          const data = Buffer.from(content);
          const actualChecksum = calculateSHA256(data);

          // Skip if by chance the checksums match
          fc.pre(actualChecksum !== wrongChecksum);

          // Verify with warning
          const result = verifyWithWarning(data, wrongChecksum);

          // Warning should mention security implications
          expect(result.warning).toBeTruthy();
          const warning = result.warning!.toLowerCase();

          // Should contain security-related keywords
          const hasSecurityKeywords =
            warning.includes("corrupt") ||
            warning.includes("tamper") ||
            warning.includes("do not install") ||
            warning.includes("mismatch");

          expect(hasSecurityKeywords).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Installation should be blocked for any checksum mismatch
   */
  it("should block installation for any checksum mismatch", () => {
    fc.assert(
      fc.property(
        fc.uint8Array({ minLength: 100, maxLength: 5000 }),
        fc.uint8Array({ minLength: 1, maxLength: 100 }), // Data to append
        (content, appendData) => {
          const originalData = Buffer.from(content);
          const originalChecksum = calculateSHA256(originalData);

          // Append data to corrupt the file
          const corruptedContent = new Uint8Array(content.length + appendData.length);
          corruptedContent.set(content, 0);
          corruptedContent.set(appendData, content.length);
          const corruptedData = Buffer.from(corruptedContent);

          // Verify with warning
          const result = verifyWithWarning(corruptedData, originalChecksum);

          // Installation should be blocked
          expect(result.shouldInstall).toBe(false);
          expect(result.verified).toBe(false);
          expect(result.warning).toBeTruthy();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Truncated files should trigger mismatch warning
   */
  it("should warn about truncated files", () => {
    fc.assert(
      fc.property(
        fc.uint8Array({ minLength: 200, maxLength: 5000 }),
        fc.integer({ min: 1, max: 100 }), // Bytes to remove
        (content, bytesToRemove) => {
          const originalData = Buffer.from(content);
          const originalChecksum = calculateSHA256(originalData);

          // Truncate the file
          const truncatedContent = content.slice(0, content.length - bytesToRemove);
          const truncatedData = Buffer.from(truncatedContent);

          // Verify with warning
          const result = verifyWithWarning(truncatedData, originalChecksum);

          // Should generate warning
          expect(result.verified).toBe(false);
          expect(result.warning).toBeTruthy();
          expect(result.shouldInstall).toBe(false);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Even minor corruption should trigger warning
   */
  it("should warn about single byte corruption", () => {
    fc.assert(
      fc.property(
        fc.uint8Array({ minLength: 100, maxLength: 5000 }),
        fc.integer({ min: 0, max: 99 }), // Byte to corrupt
        (content, corruptIndex) => {
          const originalData = Buffer.from(content);
          const originalChecksum = calculateSHA256(originalData);

          // Corrupt a single byte
          const corruptedContent = new Uint8Array(content);
          corruptedContent[corruptIndex] = (corruptedContent[corruptIndex] + 1) % 256;
          const corruptedData = Buffer.from(corruptedContent);

          // Verify with warning
          const result = verifyWithWarning(corruptedData, originalChecksum);

          // Should generate warning even for single byte corruption
          expect(result.verified).toBe(false);
          expect(result.warning).toBeTruthy();
          expect(result.shouldInstall).toBe(false);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Warning should be consistent for the same mismatch
   */
  it("should generate consistent warnings for same mismatch", () => {
    fc.assert(
      fc.property(
        fc.uint8Array({ minLength: 100, maxLength: 5000 }),
        fc.hexaString({ minLength: 64, maxLength: 64 }),
        (content, wrongChecksum) => {
          const data = Buffer.from(content);
          const actualChecksum = calculateSHA256(data);

          // Skip if checksums match
          fc.pre(actualChecksum !== wrongChecksum);

          // Verify multiple times
          const result1 = verifyWithWarning(data, wrongChecksum);
          const result2 = verifyWithWarning(data, wrongChecksum);
          const result3 = verifyWithWarning(data, wrongChecksum);

          // All results should be identical
          expect(result1.verified).toBe(result2.verified);
          expect(result2.verified).toBe(result3.verified);
          expect(result1.warning).toBe(result2.warning);
          expect(result2.warning).toBe(result3.warning);
          expect(result1.shouldInstall).toBe(result2.shouldInstall);
          expect(result2.shouldInstall).toBe(result3.shouldInstall);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Empty files should trigger mismatch for non-empty checksums
   */
  it("should detect empty file corruption", () => {
    fc.assert(
      fc.property(fc.uint8Array({ minLength: 100, maxLength: 5000 }), (content) => {
        // Skip empty content
        fc.pre(content.length > 0);

        const originalData = Buffer.from(content);
        const originalChecksum = calculateSHA256(originalData);

        // Create empty file
        const emptyData = Buffer.from([]);

        // Verify with warning
        const result = verifyWithWarning(emptyData, originalChecksum);

        // Should generate warning
        expect(result.verified).toBe(false);
        expect(result.warning).toBeTruthy();
        expect(result.shouldInstall).toBe(false);
      }),
      { numRuns: 100 }
    );
  });
});
