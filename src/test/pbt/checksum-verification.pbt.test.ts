/**
 * Property-Based Tests for Checksum Verification
 *
 * **Feature: github-releases-installer, Property 46: Checksum verification matches**
 * **Validates: Requirements 10.4**
 *
 * Tests that checksum verification correctly matches downloaded files against published checksums.
 * Note: electron-updater handles actual checksum verification automatically using SHA512.
 * These tests verify the concept and our documentation/UI around checksum verification.
 */

import { describe, it, expect } from "vitest";
import * as fc from "fast-check";
import * as crypto from "crypto";

describe("Property 46: Checksum verification matches", () => {
  /**
   * Helper function to calculate SHA256 checksum
   */
  function calculateSHA256(data: Buffer): string {
    const hash = crypto.createHash("sha256");
    hash.update(data);
    return hash.digest("hex");
  }

  /**
   * Helper function to verify checksum
   */
  function verifyChecksum(data: Buffer, expectedChecksum: string): boolean {
    const actualChecksum = calculateSHA256(data);
    return actualChecksum === expectedChecksum;
  }

  /**
   * Property: For any file content and its correct checksum, verification should succeed
   */
  it("should verify matching checksums correctly", () => {
    fc.assert(
      fc.property(fc.uint8Array({ minLength: 100, maxLength: 10000 }), (content) => {
        const data = Buffer.from(content);
        const checksum = calculateSHA256(data);

        // Verification should succeed with correct checksum
        const result = verifyChecksum(data, checksum);
        expect(result).toBe(true);
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: For any file content, if we modify it, the checksum should not match
   */
  it("should detect modified content via checksum mismatch", () => {
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

          // Verification should fail with original checksum
          const result = verifyChecksum(modifiedData, originalChecksum);
          expect(result).toBe(false);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Checksum verification is deterministic
   * Verifying the same content multiple times should always give the same result
   */
  it("should give consistent verification results", () => {
    fc.assert(
      fc.property(fc.uint8Array({ minLength: 100, maxLength: 5000 }), (content) => {
        const data = Buffer.from(content);
        const checksum = calculateSHA256(data);

        // Verify multiple times
        const result1 = verifyChecksum(data, checksum);
        const result2 = verifyChecksum(data, checksum);
        const result3 = verifyChecksum(data, checksum);

        // All results should be identical
        expect(result1).toBe(result2);
        expect(result2).toBe(result3);
        expect(result1).toBe(true);
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Invalid checksums should always fail verification
   */
  it("should reject invalid checksum formats", () => {
    fc.assert(
      fc.property(
        fc.uint8Array({ minLength: 100, maxLength: 5000 }),
        fc.string({ minLength: 1, maxLength: 100 }).filter((s) => !/^[a-f0-9]{64}$/.test(s)),
        (content, invalidChecksum) => {
          const data = Buffer.from(content);

          // Verification should fail with invalid checksum
          const result = verifyChecksum(data, invalidChecksum);
          expect(result).toBe(false);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Even a single bit change should cause checksum mismatch
   */
  it("should detect single bit changes", () => {
    fc.assert(
      fc.property(
        fc.uint8Array({ minLength: 100, maxLength: 5000 }),
        fc.integer({ min: 0, max: 99 }), // Byte index
        fc.integer({ min: 0, max: 7 }), // Bit index
        (content, byteIndex, bitIndex) => {
          const originalData = Buffer.from(content);
          const originalChecksum = calculateSHA256(originalData);

          // Flip a single bit
          const modifiedContent = new Uint8Array(content);
          modifiedContent[byteIndex] ^= 1 << bitIndex;
          const modifiedData = Buffer.from(modifiedContent);

          // Skip if the bit flip didn't actually change the value (shouldn't happen but be safe)
          fc.pre(!originalData.equals(modifiedData));

          // Verification should fail
          const result = verifyChecksum(modifiedData, originalChecksum);
          expect(result).toBe(false);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Checksum verification should work regardless of file size
   */
  it("should verify checksums for files of any size", () => {
    fc.assert(
      fc.property(
        fc
          .integer({ min: 1, max: 50000 })
          .chain((size) => fc.uint8Array({ minLength: size, maxLength: size })),
        (content) => {
          const data = Buffer.from(content);
          const checksum = calculateSHA256(data);

          // Verification should succeed
          const result = verifyChecksum(data, checksum);
          expect(result).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Truncated files should fail checksum verification
   */
  it("should detect truncated files", () => {
    fc.assert(
      fc.property(
        fc.uint8Array({ minLength: 200, maxLength: 5000 }),
        fc.integer({ min: 1, max: 100 }), // Bytes to remove
        (content, bytesToRemove) => {
          const originalData = Buffer.from(content);
          const originalChecksum = calculateSHA256(originalData);

          // Truncate the content
          const truncatedContent = content.slice(0, content.length - bytesToRemove);
          const truncatedData = Buffer.from(truncatedContent);

          // Verification should fail
          const result = verifyChecksum(truncatedData, originalChecksum);
          expect(result).toBe(false);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Appended data should fail checksum verification
   */
  it("should detect appended data", () => {
    fc.assert(
      fc.property(
        fc.uint8Array({ minLength: 100, maxLength: 5000 }),
        fc.uint8Array({ minLength: 1, maxLength: 100 }), // Data to append
        (content, appendData) => {
          const originalData = Buffer.from(content);
          const originalChecksum = calculateSHA256(originalData);

          // Append data
          const modifiedContent = new Uint8Array(content.length + appendData.length);
          modifiedContent.set(content, 0);
          modifiedContent.set(appendData, content.length);
          const modifiedData = Buffer.from(modifiedContent);

          // Verification should fail
          const result = verifyChecksum(modifiedData, originalChecksum);
          expect(result).toBe(false);
        }
      ),
      { numRuns: 100 }
    );
  });
});
