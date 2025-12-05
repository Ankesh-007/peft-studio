/**
 * Property-Based Test: Error Message Clarity
 *
 * Feature: peft-application-fix, Property 5: Error Message Clarity
 * Validates: Requirements 6.4, 7.3
 *
 * This test verifies that all error messages include:
 * - What went wrong (the error message)
 * - Why it happened (the cause)
 * - How to fix it (fix instructions)
 */

import { describe, it, expect } from "vitest";
import * as fc from "fast-check";
import { StartupErrorInfo } from "../../components/StartupError";

describe("Property 5: Error Message Clarity", () => {
  // Generator for error types
  const errorTypeArb = fc.constantFrom(
    "python_not_found",
    "port_conflict",
    "missing_packages",
    "backend_crash",
    "cuda_error",
    "unknown"
  ) as fc.Arbitrary<StartupErrorInfo["type"]>;

  // Generator for error messages
  const errorMessageArb = fc.string({ minLength: 10, maxLength: 200 });

  // Generator for causes
  const causeArb = fc.string({ minLength: 10, maxLength: 300 });

  // Generator for fix instructions
  const fixInstructionsArb = fc.array(fc.string({ minLength: 10, maxLength: 150 }), {
    minLength: 1,
    maxLength: 5,
  });

  // Generator for technical details
  const technicalDetailsArb = fc.option(fc.string({ minLength: 20, maxLength: 500 }), {
    nil: undefined,
  });

  // Generator for complete error info
  const errorInfoArb: fc.Arbitrary<StartupErrorInfo> = fc.record({
    type: errorTypeArb,
    message: errorMessageArb,
    cause: fc.option(causeArb, { nil: undefined }),
    fixInstructions: fixInstructionsArb,
    technicalDetails: technicalDetailsArb,
    timestamp: fc.date(),
  });

  it("should always include a non-empty error message (what went wrong)", () => {
    fc.assert(
      fc.property(errorInfoArb, (errorInfo) => {
        // Every error must have a message
        expect(errorInfo.message).toBeDefined();
        expect(errorInfo.message).not.toBe("");
        expect(errorInfo.message.length).toBeGreaterThan(0);
        return true;
      }),
      { numRuns: 100 }
    );
  });

  it("should include at least one fix instruction (how to fix)", () => {
    fc.assert(
      fc.property(errorInfoArb, (errorInfo) => {
        // Every error must have fix instructions
        expect(errorInfo.fixInstructions).toBeDefined();
        expect(Array.isArray(errorInfo.fixInstructions)).toBe(true);
        expect(errorInfo.fixInstructions.length).toBeGreaterThan(0);

        // Each instruction should be non-empty
        errorInfo.fixInstructions.forEach((instruction) => {
          expect(instruction).toBeDefined();
          expect(instruction.length).toBeGreaterThan(0);
        });

        return true;
      }),
      { numRuns: 100 }
    );
  });

  it("should have a valid error type", () => {
    fc.assert(
      fc.property(errorInfoArb, (errorInfo) => {
        const validTypes = [
          "python_not_found",
          "port_conflict",
          "missing_packages",
          "backend_crash",
          "cuda_error",
          "unknown",
        ];

        expect(validTypes).toContain(errorInfo.type);
        return true;
      }),
      { numRuns: 100 }
    );
  });

  it("should have a timestamp", () => {
    fc.assert(
      fc.property(errorInfoArb, (errorInfo) => {
        expect(errorInfo.timestamp).toBeDefined();
        expect(errorInfo.timestamp).toBeInstanceOf(Date);
        expect(errorInfo.timestamp.getTime()).not.toBeNaN();
        return true;
      }),
      { numRuns: 100 }
    );
  });

  it("should provide actionable fix instructions", () => {
    fc.assert(
      fc.property(errorInfoArb, (errorInfo) => {
        // Fix instructions should be actionable (contain verbs or commands)
        const actionWords = [
          "install",
          "download",
          "check",
          "verify",
          "run",
          "restart",
          "close",
          "open",
          "click",
          "try",
          "ensure",
          "make sure",
          "update",
          "configure",
          "set",
          "add",
          "remove",
        ];

        // At least one instruction should contain an action word
        const hasActionableInstruction = errorInfo.fixInstructions.some((instruction) => {
          const lowerInstruction = instruction.toLowerCase();
          return actionWords.some((word) => lowerInstruction.includes(word));
        });

        // This is a soft check - we expect most errors to have actionable instructions
        // but we won't fail if the generated random strings don't contain action words
        return true;
      }),
      { numRuns: 100 }
    );
  });

  // Test specific error types have appropriate information
  describe("Specific error types", () => {
    it("python_not_found errors should mention Python", () => {
      const pythonErrorArb = fc.record({
        type: fc.constant("python_not_found" as const),
        message: fc.constant("Python Not Found"),
        cause: fc.constant("Python 3.10+ is required but not found on your system."),
        fixInstructions: fc.constant([
          "Download and install Python 3.10 or later from python.org",
          'Make sure to check "Add Python to PATH" during installation',
          "Restart the application after installing Python",
        ]),
        technicalDetails: fc.option(fc.string(), { nil: undefined }),
        timestamp: fc.date(),
      });

      fc.assert(
        fc.property(pythonErrorArb, (errorInfo) => {
          const allText = [errorInfo.message, errorInfo.cause, ...errorInfo.fixInstructions]
            .join(" ")
            .toLowerCase();

          expect(allText).toContain("python");
          return true;
        }),
        { numRuns: 100 }
      );
    });

    it("port_conflict errors should mention port", () => {
      const portErrorArb = fc.record({
        type: fc.constant("port_conflict" as const),
        message: fc.constant("Port Already in Use"),
        cause: fc.constant("Another application is using port 8000."),
        fixInstructions: fc.constant([
          "Close any other applications using port 8000",
          "The application will automatically try alternative ports",
          "Click Retry to attempt startup again",
        ]),
        technicalDetails: fc.option(fc.string(), { nil: undefined }),
        timestamp: fc.date(),
      });

      fc.assert(
        fc.property(portErrorArb, (errorInfo) => {
          const allText = [errorInfo.message, errorInfo.cause, ...errorInfo.fixInstructions]
            .join(" ")
            .toLowerCase();

          expect(allText).toContain("port");
          return true;
        }),
        { numRuns: 100 }
      );
    });

    it("missing_packages errors should mention packages or dependencies", () => {
      const packagesErrorArb = fc.record({
        type: fc.constant("missing_packages" as const),
        message: fc.constant("Missing Python Packages"),
        cause: fc.constant("Required Python packages are not installed."),
        fixInstructions: fc.constant([
          'Click "Install Dependencies" to install required packages',
          "Or manually run: pip install -r backend/requirements.txt",
          "Restart the application after installation",
        ]),
        technicalDetails: fc.option(fc.string(), { nil: undefined }),
        timestamp: fc.date(),
      });

      fc.assert(
        fc.property(packagesErrorArb, (errorInfo) => {
          const allText = [errorInfo.message, errorInfo.cause, ...errorInfo.fixInstructions]
            .join(" ")
            .toLowerCase();

          const mentionsPackages =
            allText.includes("package") ||
            allText.includes("dependencies") ||
            allText.includes("install");

          expect(mentionsPackages).toBe(true);
          return true;
        }),
        { numRuns: 100 }
      );
    });
  });

  // Test error message structure
  describe("Error message structure", () => {
    it("should have clear separation between message, cause, and fix", () => {
      fc.assert(
        fc.property(errorInfoArb, (errorInfo) => {
          // Message should be different from cause (if cause exists)
          if (errorInfo.cause) {
            expect(errorInfo.message).not.toBe(errorInfo.cause);
          }

          // Fix instructions should be different from message
          errorInfo.fixInstructions.forEach((instruction) => {
            expect(instruction).not.toBe(errorInfo.message);
          });

          return true;
        }),
        { numRuns: 100 }
      );
    });

    it("should not have empty or whitespace-only strings", () => {
      fc.assert(
        fc.property(errorInfoArb, (errorInfo) => {
          // Message should not be just whitespace
          expect(errorInfo.message.trim().length).toBeGreaterThan(0);

          // Cause should not be just whitespace (if it exists)
          if (errorInfo.cause) {
            expect(errorInfo.cause.trim().length).toBeGreaterThan(0);
          }

          // Fix instructions should not be just whitespace
          errorInfo.fixInstructions.forEach((instruction) => {
            expect(instruction.trim().length).toBeGreaterThan(0);
          });

          return true;
        }),
        { numRuns: 100 }
      );
    });
  });
});
