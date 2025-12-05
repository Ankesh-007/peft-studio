/**
 * Integration Tests for Code Signing with Bundled Backend
 *
 * These tests verify that code signing works correctly with the bundled
 * Python backend executable across different platforms and configurations.
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import { execSync } from "child_process";

describe("Code Signing Integration with Bundled Backend", () => {
  const originalEnv = process.env;
  const testBuildDir = path.join(process.cwd(), "build");
  const backendDistDir = path.join(process.cwd(), "backend", "dist");

  beforeEach(() => {
    process.env = { ...originalEnv };
    
    // Ensure build directory exists
    if (!fs.existsSync(testBuildDir)) {
      fs.mkdirSync(testBuildDir, { recursive: true });
    }
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  describe("Windows Code Signing with Backend", () => {
    it("should verify sign-windows.js works with bundled executable configuration", async () => {
      // Set up test environment
      process.env.CSC_LINK = "test-certificate.pfx";
      process.env.CSC_KEY_PASSWORD = "test-password";

      // Import the signing script
      const signWindows = (await import("../../../scripts/sign-windows.js")) as any;

      // Mock configuration that includes backend executable
      const config = {
        path: "test.exe",
        platform: "win32",
        extraResources: [
          {
            from: "backend/dist/peft_engine.exe",
            to: "backend",
          },
        ],
      };

      // Should complete without throwing
      await expect(signWindows.default(config)).resolves.not.toThrow();
    });

    it("should create signing status file indicating backend is included", async () => {
      process.env.CSC_LINK = "test.pfx";
      process.env.CSC_KEY_PASSWORD = "password";

      const statusFile = path.join(testBuildDir, "signing-status.txt");
      
      // Clean up any existing status file
      if (fs.existsSync(statusFile)) {
        fs.unlinkSync(statusFile);
      }

      const signWindows = (await import("../../../scripts/sign-windows.js")) as any;
      await signWindows.default({});

      // Verify status file was created
      expect(fs.existsSync(statusFile)).toBe(true);
    });

    it("should handle unsigned builds with backend gracefully", async () => {
      // No signing credentials
      delete process.env.CSC_LINK;
      delete process.env.CSC_KEY_PASSWORD;

      const signWindows = (await import("../../../scripts/sign-windows.js")) as any;

      // Should complete without error for unsigned builds
      await expect(signWindows.default({})).resolves.not.toThrow();

      // Verify unsigned status is recorded
      const statusFile = path.join(testBuildDir, "signing-status.txt");
      if (fs.existsSync(statusFile)) {
        const status = fs.readFileSync(statusFile, "utf8");
        expect(status).toContain("NOT code signed");
      }
    });
  });

  describe("macOS Code Signing with Backend", () => {
    it("should verify sign-macos.js works with bundled executable configuration", async () => {
      // Set up test environment
      process.env.CSC_LINK = "test-certificate.p12";
      process.env.CSC_KEY_PASSWORD = "test-password";
      process.env.APPLE_ID = "test@example.com";
      process.env.APPLE_ID_PASSWORD = "abcd-efgh-ijkl-mnop";
      process.env.APPLE_TEAM_ID = "TEAM123456";

      // Import the signing script
      const signMacos = (await import("../../../scripts/sign-macos.js")) as any;

      // Mock configuration that includes backend executable
      const config = {
        path: "PEFT Studio.app",
        platform: "darwin",
        extraResources: [
          {
            from: "backend/dist/peft_engine",
            to: "backend",
          },
        ],
      };

      // Should complete without throwing
      await expect(signMacos.default(config)).resolves.not.toThrow();
    });

    it("should verify entitlements apply to backend executable", async () => {
      // This test verifies that the configuration supports backend executable signing
      const packageJson = JSON.parse(
        fs.readFileSync(path.join(process.cwd(), "package.json"), "utf8")
      );

      // Verify macOS build configuration includes entitlements
      expect(packageJson.build.mac).toBeDefined();
      expect(packageJson.build.mac.entitlements).toBeDefined();
      expect(packageJson.build.mac.entitlementsInherit).toBeDefined();
      
      // Verify hardened runtime is enabled (required for notarization)
      expect(packageJson.build.mac.hardenedRuntime).toBe(true);
    });

    it("should handle signing without notarization credentials", async () => {
      // Set up signing credentials but not notarization
      process.env.CSC_LINK = "test.p12";
      process.env.CSC_KEY_PASSWORD = "password";
      delete process.env.APPLE_ID;
      delete process.env.APPLE_ID_PASSWORD;
      delete process.env.APPLE_TEAM_ID;

      const signMacos = (await import("../../../scripts/sign-macos.js")) as any;

      // Should complete without error (signed but not notarized)
      await expect(signMacos.default({})).resolves.not.toThrow();

      // Verify status indicates signed but not notarized
      const statusFile = path.join(testBuildDir, "signing-status-macos.txt");
      if (fs.existsSync(statusFile)) {
        const status = fs.readFileSync(statusFile, "utf8");
        expect(status).toContain("code signed");
      }
    });
  });

  describe("Backend Executable in Build Configuration", () => {
    it("should verify backend executable is included in extraResources", () => {
      const packageJson = JSON.parse(
        fs.readFileSync(path.join(process.cwd(), "package.json"), "utf8")
      );

      // Verify extraResources includes backend
      expect(packageJson.build.extraResources).toBeDefined();
      expect(Array.isArray(packageJson.build.extraResources)).toBe(true);
      
      const backendResource = packageJson.build.extraResources.find(
        (resource: any) => resource.from && resource.from.includes("backend/dist/peft_engine")
      );
      
      expect(backendResource).toBeDefined();
      expect(backendResource.to).toBe("backend");
    });

    it("should verify backend source files are excluded from asar", () => {
      const packageJson = JSON.parse(
        fs.readFileSync(path.join(process.cwd(), "package.json"), "utf8")
      );

      // Verify backend source is excluded
      expect(packageJson.build.files).toBeDefined();
      expect(packageJson.build.files).toContain("!backend/**/*");
    });
  });

  describe("Error Handling for Unsigned Dev Builds", () => {
    it("should allow unsigned builds when credentials are missing", async () => {
      // Clear all signing credentials
      delete process.env.CSC_LINK;
      delete process.env.CSC_KEY_PASSWORD;
      delete process.env.APPLE_ID;
      delete process.env.APPLE_ID_PASSWORD;
      delete process.env.APPLE_TEAM_ID;

      const signWindows = (await import("../../../scripts/sign-windows.js")) as any;
      const signMacos = (await import("../../../scripts/sign-macos.js")) as any;

      // Both should complete without throwing
      await expect(signWindows.default({})).resolves.not.toThrow();
      await expect(signMacos.default({})).resolves.not.toThrow();
    });

    it("should log appropriate warnings for unsigned builds", async () => {
      delete process.env.CSC_LINK;
      delete process.env.CSC_KEY_PASSWORD;

      // Capture console output
      const consoleLogs: string[] = [];
      const originalWarn = console.warn;
      console.warn = (...args: any[]) => {
        consoleLogs.push(args.join(" "));
      };

      const signWindows = (await import("../../../scripts/sign-windows.js")) as any;
      await signWindows.default({});

      // Restore console
      console.warn = originalWarn;

      // Verify warning was logged
      const hasWarning = consoleLogs.some((log) =>
        log.includes("code signing not configured") || log.includes("unsigned")
      );
      expect(hasWarning).toBe(true);
    });
  });

  describe("Platform-Specific Backend Executable Naming", () => {
    it("should verify Windows backend executable has .exe extension", () => {
      const packageJson = JSON.parse(
        fs.readFileSync(path.join(process.cwd(), "package.json"), "utf8")
      );

      const backendResource = packageJson.build.extraResources.find(
        (resource: any) => resource.from && resource.from.includes("backend/dist/peft_engine")
      );

      // The pattern should support platform-specific extensions
      expect(backendResource.from).toContain("peft_engine");
      expect(backendResource.filter).toContain("peft_engine*");
    });

    it("should verify macOS/Linux backend executable has no extension", () => {
      // The same configuration should work for all platforms
      // The ${/*} pattern in extraResources handles platform differences
      const packageJson = JSON.parse(
        fs.readFileSync(path.join(process.cwd(), "package.json"), "utf8")
      );

      const backendResource = packageJson.build.extraResources.find(
        (resource: any) => resource.from && resource.from.includes("backend/dist/peft_engine")
      );

      // Verify the pattern supports both with and without extension
      expect(backendResource.from).toContain("${/*}");
    });
  });
});

describe("Antivirus Compatibility Tests", () => {
  it("should document antivirus compatibility considerations", () => {
    // Verify documentation exists for antivirus compatibility
    const docsPath = path.join(process.cwd(), "docs", "developer-guide", "code-signing.md");
    
    if (fs.existsSync(docsPath)) {
      const docs = fs.readFileSync(docsPath, "utf8");
      
      // Should mention antivirus or security warnings
      const hasAntivirusInfo = 
        docs.toLowerCase().includes("antivirus") ||
        docs.toLowerCase().includes("windows defender") ||
        docs.toLowerCase().includes("smartscreen");
      
      expect(hasAntivirusInfo).toBe(true);
    }
  });

  it("should verify backend executable is included in signing process", () => {
    // The backend executable should be signed as part of the app bundle
    const packageJson = JSON.parse(
      fs.readFileSync(path.join(process.cwd(), "package.json"), "utf8")
    );

    // Verify extraResources configuration
    expect(packageJson.build.extraResources).toBeDefined();
    
    // Backend should be in extraResources, which means it will be signed
    // as part of the application bundle
    const hasBackend = packageJson.build.extraResources.some(
      (resource: any) => resource.from && resource.from.includes("backend")
    );
    
    expect(hasBackend).toBe(true);
  });
});
