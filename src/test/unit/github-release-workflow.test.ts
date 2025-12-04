import fc from "fast-check";
import { describe, test, expect } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as yaml from "yaml";

/**
 * Feature: github-releases-installer
 * Property-based tests for GitHub release workflow configuration
 */

// Helper to load and parse the workflow file
function loadWorkflowConfig(): any {
  const workflowPath = path.join(process.cwd(), ".github/workflows/release.yml");
  const workflowContent = fs.readFileSync(workflowPath, "utf-8");
  return yaml.parse(workflowContent);
}

describe("GitHub Release Workflow Properties", () => {
  /**
   * Feature: github-releases-installer, Property 6: Version tags trigger workflow
   * Validates: Requirements 2.1
   * 
   * For any valid version tag pushed to the repository, the release workflow should be automatically triggered
   */
  test("Property 6: Version tags trigger workflow", () => {
    fc.assert(
      fc.property(
        fc.tuple(
          fc.integer({ min: 0, max: 99 }),
          fc.integer({ min: 0, max: 99 }),
          fc.integer({ min: 0, max: 99 })
        ),
        ([major, minor, patch]) => {
          const versionTag = `v${major}.${minor}.${patch}`;
          const workflow = loadWorkflowConfig();
          
          // Check that workflow has push trigger
          expect(workflow.on).toBeDefined();
          expect(workflow.on.push).toBeDefined();
          expect(workflow.on.push.tags).toBeDefined();
          
          // Check that the tag pattern matches version tags
          const tagPatterns = workflow.on.push.tags;
          const hasVersionPattern = tagPatterns.some((pattern: string) => {
            // Convert glob pattern to regex
            const regexPattern = pattern.replace(/\*/g, ".*");
            const regex = new RegExp(`^${regexPattern}$`);
            return regex.test(versionTag);
          });
          
          expect(hasVersionPattern).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Feature: github-releases-installer, Property 7: Parallel platform builds
   * Validates: Requirements 2.2
   * 
   * For any release workflow execution, Windows, macOS, and Linux builds should run in parallel
   */
  test("Property 7: Parallel platform builds", () => {
    const workflow = loadWorkflowConfig();
    
    // Check that we have separate build jobs for each platform
    expect(workflow.jobs).toBeDefined();
    expect(workflow.jobs["build-windows"]).toBeDefined();
    expect(workflow.jobs["build-macos"]).toBeDefined();
    expect(workflow.jobs["build-linux"]).toBeDefined();
    
    // Check that all build jobs depend on create-release (not on each other)
    const buildWindows = workflow.jobs["build-windows"];
    const buildMacos = workflow.jobs["build-macos"];
    const buildLinux = workflow.jobs["build-linux"];
    
    // All should depend on create-release
    expect(buildWindows.needs).toEqual("create-release");
    expect(buildMacos.needs).toEqual("create-release");
    expect(buildLinux.needs).toEqual("create-release");
    
    // Verify they run on different platforms
    expect(buildWindows["runs-on"]).toBe("windows-latest");
    expect(buildMacos["runs-on"]).toBe("macos-latest");
    expect(buildLinux["runs-on"]).toBe("ubuntu-latest");
  });

  /**
   * Feature: github-releases-installer, Property 8: Built installers uploaded as assets
   * Validates: Requirements 2.3
   * 
   * For any successfully built installer, it should be uploaded as a release asset to GitHub
   */
  test("Property 8: Built installers uploaded as assets", () => {
    const workflow = loadWorkflowConfig();
    
    // Check that upload-assets job exists and depends on all build jobs
    expect(workflow.jobs["upload-assets"]).toBeDefined();
    const uploadJob = workflow.jobs["upload-assets"];
    
    // Should depend on all build jobs
    expect(uploadJob.needs).toContain("build-windows");
    expect(uploadJob.needs).toContain("build-macos");
    expect(uploadJob.needs).toContain("build-linux");
    expect(uploadJob.needs).toContain("create-release");
    
    // Check that it has steps to upload assets
    const steps = uploadJob.steps;
    expect(steps).toBeDefined();
    
    // Should have steps to download artifacts from each platform
    const downloadSteps = steps.filter((step: any) => 
      step.uses && step.uses.includes("download-artifact")
    );
    expect(downloadSteps.length).toBeGreaterThanOrEqual(3); // Windows, macOS, Linux
    
    // Should have steps to upload release assets
    const uploadSteps = steps.filter((step: any) => 
      step.uses && step.uses.includes("upload-release-asset")
    );
    expect(uploadSteps.length).toBeGreaterThanOrEqual(6); // At least 2 per platform
    
    // Verify each upload step has required fields
    uploadSteps.forEach((step: any) => {
      expect(step.with).toBeDefined();
      expect(step.with.upload_url).toBeDefined();
      expect(step.with.asset_path).toBeDefined();
      expect(step.with.asset_name).toBeDefined();
      expect(step.with.asset_content_type).toBeDefined();
    });
  });
});

describe("GitHub Release Notes Template Properties", () => {
  // Helper to load the release template
  function loadReleaseTemplate(): string {
    const templatePath = path.join(process.cwd(), ".github/release-template.md");
    return fs.readFileSync(templatePath, "utf-8");
  }

  /**
   * Feature: github-releases-installer, Property 4: Release notes include installation instructions
   * Validates: Requirements 1.4
   * 
   * For any published release, the release notes should contain installation instructions
   */
  test("Property 4: Release notes include installation instructions", () => {
    fc.assert(
      fc.property(
        fc.tuple(
          fc.integer({ min: 0, max: 99 }),
          fc.integer({ min: 0, max: 99 }),
          fc.integer({ min: 0, max: 99 })
        ),
        ([major, minor, patch]) => {
          const version = `${major}.${minor}.${patch}`;
          const template = loadReleaseTemplate();
          
          // Replace template variables to simulate a real release
          const releaseNotes = template
            .replace(/\{\{VERSION\}\}/g, version)
            .replace(/\{\{RELEASE_DATE\}\}/g, new Date().toISOString())
            .replace(/\{\{CHANGELOG\}\}/g, "Test changelog")
            .replace(/\{\{CHECKSUMS\}\}/g, "test checksums");
          
          // Check that installation instructions section exists
          expect(releaseNotes).toContain("## 📋 Installation Instructions");
          
          // Check that instructions for all platforms are present
          expect(releaseNotes).toContain("### Windows Installation");
          expect(releaseNotes).toContain("### macOS Installation");
          expect(releaseNotes).toContain("### Linux Installation");
          
          // Check that instructions contain actionable steps
          expect(releaseNotes).toMatch(/1\.\s+\*\*Download\*\*/);
          expect(releaseNotes).toMatch(/2\.\s+\*\*\w+\*\*/); // Step 2 with bold action
          expect(releaseNotes).toMatch(/3\.\s+\*\*\w+\*\*/); // Step 3 with bold action
          
          // Verify installation instructions are not empty
          const installationSection = releaseNotes.split("## 📋 Installation Instructions")[1];
          expect(installationSection).toBeDefined();
          expect(installationSection.length).toBeGreaterThan(500); // Substantial content
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Feature: github-releases-installer, Property 24: Platform-specific instructions in notes
   * Validates: Requirements 6.1
   * 
   * For any release notes, they should contain platform-specific installation instructions
   */
  test("Property 24: Platform-specific instructions in notes", () => {
    fc.assert(
      fc.property(
        fc.record({
          major: fc.integer({ min: 0, max: 99 }),
          minor: fc.integer({ min: 0, max: 99 }),
          patch: fc.integer({ min: 0, max: 99 }),
          platform: fc.constantFrom("windows", "macos", "linux")
        }),
        ({ major, minor, patch, platform }) => {
          const version = `${major}.${minor}.${patch}`;
          const template = loadReleaseTemplate();
          
          // Replace template variables
          const releaseNotes = template
            .replace(/\{\{VERSION\}\}/g, version)
            .replace(/\{\{RELEASE_DATE\}\}/g, new Date().toISOString());
          
          // Define platform-specific expectations
          const platformChecks: Record<string, { header: string; specifics: string[] }> = {
            windows: {
              header: "### Windows Installation",
              specifics: [
                ".exe",
                "installation wizard",
                "Start Menu",
                "desktop shortcut",
                "SmartScreen",
                "Portable"
              ]
            },
            macos: {
              header: "### macOS Installation",
              specifics: [
                ".dmg",
                "Applications folder",
                "Spotlight",
                "Right-click",
                "macOS 10.15"
              ]
            },
            linux: {
              header: "### Linux Installation",
              specifics: [
                "AppImage",
                "chmod +x",
                ".deb",
                "dpkg",
                "Ubuntu"
              ]
            }
          };
          
          const checks = platformChecks[platform];
          
          // Verify platform-specific header exists
          expect(releaseNotes).toContain(checks.header);
          
          // Extract the platform-specific section (everything from this header to the next ## or end)
          const headerIndex = releaseNotes.indexOf(checks.header);
          expect(headerIndex).toBeGreaterThan(-1);
          
          const afterHeader = releaseNotes.substring(headerIndex);
          const nextSectionIndex = afterHeader.indexOf("\n## ", 1);
          const platformSection = nextSectionIndex > 0 
            ? afterHeader.substring(0, nextSectionIndex)
            : afterHeader;
          
          expect(platformSection).toBeDefined();
          expect(platformSection.length).toBeGreaterThan(100); // Has substantial content
          
          // Verify platform-specific details are present
          checks.specifics.forEach(specific => {
            expect(platformSection).toContain(specific);
          });
          
          // Verify the section has numbered steps
          expect(platformSection).toMatch(/1\.\s+\*\*\w+\*\*/);
          
          // Verify security/troubleshooting notes are present for each platform
          if (platform === "windows") {
            expect(platformSection).toContain("Security Warning");
          } else if (platform === "macos") {
            expect(platformSection).toContain("Security Note");
          } else if (platform === "linux") {
            expect(platformSection).toContain("Desktop Integration");
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});
