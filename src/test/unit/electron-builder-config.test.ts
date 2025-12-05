import fc from "fast-check";
import { describe, test, expect } from "vitest";
import * as fs from "fs";
import * as path from "path";

/**
 * Feature: github-releases-installer
 * Property-based tests for electron-builder configuration
 */

// Helper to load and parse package.json
function loadPackageJson(): Record<string, unknown> {
  const packagePath = path.join(process.cwd(), "package.json");
  const packageContent = fs.readFileSync(packagePath, "utf-8");
  return JSON.parse(packageContent);
}

describe("Electron Builder Configuration Properties", () => {
  /**
   * Feature: github-releases-installer, Property 3: Correct file formats per platform
   * Validates: Requirements 1.3
   * 
   * For any platform, the downloaded installer should have the correct file format 
   * (NSIS for Windows, DMG for macOS, AppImage for Linux)
   */
  test("Property 3: Correct file formats per platform", () => {
    fc.assert(
      fc.property(
        fc.constantFrom("windows", "macos", "linux"),
        (platform) => {
          const packageJson = loadPackageJson();
          const buildConfig = packageJson.build;
          
          expect(buildConfig).toBeDefined();
          
          // Define expected formats for each platform
          const expectedFormats: Record<string, string[]> = {
            windows: ["nsis", "portable"],
            macos: ["dmg", "zip"],
            linux: ["AppImage", "deb"]
          };
          
          // Map platform names to config keys
          const configKeys: Record<string, string> = {
            windows: "win",
            macos: "mac",
            linux: "linux"
          };
          
          const configKey = configKeys[platform];
          const platformConfig = buildConfig[configKey];
          
          expect(platformConfig).toBeDefined();
          expect(platformConfig.target).toBeDefined();
          
          // Extract target names (handle both string array and object array formats)
          const targets = platformConfig.target.map((t: string | { target: string }) => 
            typeof t === "string" ? t : t.target
          );
          
          // Verify all expected formats are present
          expectedFormats[platform].forEach(format => {
            expect(targets).toContain(format);
          });
          
          // Verify at least the expected number of targets
          expect(targets.length).toBeGreaterThanOrEqual(expectedFormats[platform].length);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Feature: github-releases-installer, Property 11: Windows NSIS installer provided
   * Validates: Requirements 3.1
   * 
   * For any Windows release, an NSIS-based setup executable should be provided
   */
  test("Property 11: Windows NSIS installer provided", () => {
    const packageJson = loadPackageJson();
    const buildConfig = packageJson.build;
    
    expect(buildConfig).toBeDefined();
    expect(buildConfig.win).toBeDefined();
    expect(buildConfig.win.target).toBeDefined();
    
    // Extract target names
    const targets = buildConfig.win.target.map((t: string | { target: string }) => 
      typeof t === "string" ? t : t.target
    );
    
    // Verify NSIS is in the targets
    expect(targets).toContain("nsis");
    
    // Verify NSIS configuration exists
    expect(buildConfig.nsis).toBeDefined();
    
    // Verify NSIS configuration has required properties
    const nsisConfig = buildConfig.nsis;
    expect(nsisConfig.oneClick).toBeDefined();
    expect(nsisConfig.allowToChangeInstallationDirectory).toBeDefined();
    expect(nsisConfig.createDesktopShortcut).toBeDefined();
    expect(nsisConfig.createStartMenuShortcut).toBeDefined();
    
    // Verify installer allows directory selection (Requirement 3.2)
    expect(nsisConfig.allowToChangeInstallationDirectory).toBe(true);
    
    // Verify shortcuts are created (Requirement 3.3)
    expect(nsisConfig.createDesktopShortcut).toBe(true);
    expect(nsisConfig.createStartMenuShortcut).toBe(true);
    
    // Verify portable version is also available (Requirement 3.5)
    expect(targets).toContain("portable");
  });

  /**
   * Feature: github-releases-installer, Property 16: macOS DMG provided
   * Validates: Requirements 4.1
   * 
   * For any macOS release, a DMG disk image file should be provided
   */
  test("Property 16: macOS DMG provided", () => {
    const packageJson = loadPackageJson();
    const buildConfig = packageJson.build;
    
    expect(buildConfig).toBeDefined();
    expect(buildConfig.mac).toBeDefined();
    expect(buildConfig.mac.target).toBeDefined();
    
    // Extract target names
    const targets = buildConfig.mac.target.map((t: any) => 
      typeof t === "string" ? t : t.target
    );
    
    // Verify DMG is in the targets
    expect(targets).toContain("dmg");
    
    // Verify DMG configuration exists
    expect(buildConfig.dmg).toBeDefined();
    
    // Verify DMG configuration has required properties (Requirement 4.2)
    const dmgConfig = buildConfig.dmg;
    expect(dmgConfig.contents).toBeDefined();
    
    // Verify DMG contains application icon and Applications folder link
    const contents = dmgConfig.contents;
    expect(contents).toBeInstanceOf(Array);
    expect(contents.length).toBeGreaterThanOrEqual(2);
    
    // Check for file entry (application)
    const hasFileEntry = contents.some((item: any) => item.type === "file");
    expect(hasFileEntry).toBe(true);
    
    // Check for Applications folder link
    const hasAppsLink = contents.some((item: any) => 
      item.type === "link" && item.path === "/Applications"
    );
    expect(hasAppsLink).toBe(true);
    
    // Verify ZIP archive is also available (Requirement 4.5)
    expect(targets).toContain("zip");
    
    // Verify macOS-specific metadata
    expect(buildConfig.mac.category).toBeDefined();
    expect(buildConfig.mac.hardenedRuntime).toBe(true);
  });

  /**
   * Feature: github-releases-installer, Property 20: Linux AppImage provided
   * Validates: Requirements 5.1
   * 
   * For any Linux release, an AppImage file should be provided
   */
  test("Property 20: Linux AppImage provided", () => {
    const packageJson = loadPackageJson();
    const buildConfig = packageJson.build;
    
    expect(buildConfig).toBeDefined();
    expect(buildConfig.linux).toBeDefined();
    expect(buildConfig.linux.target).toBeDefined();
    
    // Extract target names
    const targets = buildConfig.linux.target.map((t: any) => 
      typeof t === "string" ? t : t.target
    );
    
    // Verify AppImage is in the targets
    expect(targets).toContain("AppImage");
    
    // Verify AppImage configuration exists
    expect(buildConfig.appImage).toBeDefined();
    
    // Verify desktop integration configuration (Requirement 5.3)
    expect(buildConfig.linux.desktop).toBeDefined();
    const desktopConfig = buildConfig.linux.desktop;
    
    // Verify desktop file has required fields
    expect(desktopConfig.Name).toBeDefined();
    expect(desktopConfig.Comment).toBeDefined();
    expect(desktopConfig.Categories).toBeDefined();
    expect(desktopConfig.Type).toBe("Application");
    
    // Verify .deb package is also available (Requirement 5.4)
    expect(targets).toContain("deb");
    
    // Verify deb configuration exists
    expect(buildConfig.deb).toBeDefined();
    
    // Verify deb has dependencies configured
    expect(buildConfig.deb.depends).toBeDefined();
    expect(buildConfig.deb.depends).toBeInstanceOf(Array);
    expect(buildConfig.deb.depends.length).toBeGreaterThan(0);
    
    // Verify Linux category is set
    expect(buildConfig.linux.category).toBe("Development");
  });
});

describe("Auto-Update Configuration Properties", () => {
  /**
   * Verify auto-update configuration is properly set up
   */
  test("Auto-update configuration is present", () => {
    const packageJson = loadPackageJson();
    const buildConfig = packageJson.build;
    
    expect(buildConfig).toBeDefined();
    expect(buildConfig.publish).toBeDefined();
    
    // Verify publish configuration for GitHub
    const publishConfig = buildConfig.publish;
    expect(publishConfig.provider).toBe("github");
    expect(publishConfig.owner).toBeDefined();
    expect(publishConfig.repo).toBeDefined();
    
    // Verify electron-updater is in dependencies or devDependencies
    const hasElectronUpdater = packageJson.dependencies?.["electron-updater"] || packageJson.devDependencies?.["electron-updater"];
    expect(hasElectronUpdater).toBeDefined();
  });
});

describe("Code Signing Configuration Properties", () => {
  /**
   * Verify code signing configuration placeholders are present
   */
  test("Code signing configuration is present", () => {
    const packageJson = loadPackageJson();
    const buildConfig = packageJson.build;
    
    expect(buildConfig).toBeDefined();
    
    // Verify Windows code signing configuration
    expect(buildConfig.win).toBeDefined();
    expect(buildConfig.win.sign).toBeDefined();
    
    // Verify macOS code signing configuration
    expect(buildConfig.mac).toBeDefined();
    expect(buildConfig.mac.hardenedRuntime).toBe(true);
    expect(buildConfig.mac.entitlements).toBeDefined();
    expect(buildConfig.mac.entitlementsInherit).toBeDefined();
    
    // Verify entitlements file path is configured
    const entitlementsPath = path.join(process.cwd(), buildConfig.mac.entitlements);
    expect(fs.existsSync(entitlementsPath)).toBe(true);
  });
  
  /**
   * Verify Windows signing script exists
   */
  test("Windows signing script exists", () => {
    const packageJson = loadPackageJson();
    const buildConfig = packageJson.build;
    
    expect(buildConfig.win.sign).toBeDefined();
    
    // Extract script path (remove leading ./)
    const scriptPath = buildConfig.win.sign.replace(/^\.\//, "");
    const fullPath = path.join(process.cwd(), scriptPath);
    
    // Verify script file exists
    expect(fs.existsSync(fullPath)).toBe(true);
    
    // Verify script is a JavaScript file
    expect(scriptPath).toMatch(/\.js$/);
  });
});
