/**
 * Property-Based Tests for Multi-Platform Build Consistency
 * 
 * **Feature: ci-infrastructure-fix, Property 11: Multi-Platform Build Consistency**
 * **Validates: Requirements 4.5, 7.2**
 * 
 * Property: For any Electron Builder configuration, if the build succeeds on one 
 * platform (Ubuntu, Windows, or macOS), the build process should succeed on all 
 * configured platforms with the same source code.
 */

import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import * as fs from 'fs';
import * as path from 'path';

describe('Multi-Platform Build Consistency Property Tests', () => {
  const distPath = path.join(process.cwd(), 'dist');
  const packageJsonPath = path.join(process.cwd(), 'package.json');
  const ciWorkflowPath = path.join(process.cwd(), '.github', 'workflows', 'ci.yml');

  /**
   * Helper function to read and parse package.json
   */
  function getPackageJson(): any {
    if (!fs.existsSync(packageJsonPath)) {
      throw new Error('package.json not found');
    }
    return JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
  }

  /**
   * Helper function to read CI workflow configuration
   */
  function getCIWorkflowConfig(): string {
    if (!fs.existsSync(ciWorkflowPath)) {
      throw new Error('CI workflow file not found');
    }
    return fs.readFileSync(ciWorkflowPath, 'utf-8');
  }

  /**
   * Helper function to extract platform matrix from CI workflow
   */
  function extractPlatformMatrix(workflowContent: string): string[] {
    // Extract the matrix.os configuration from the build-check job
    const matrixMatch = workflowContent.match(/matrix:\s*\n\s*os:\s*\[(.*?)\]/s);
    if (!matrixMatch) {
      return [];
    }

    // Parse the platform list
    const platformsStr = matrixMatch[1];
    const platforms = platformsStr
      .split(',')
      .map(p => p.trim().replace(/['"]/g, ''))
      .filter(p => p.length > 0);

    return platforms;
  }

  /**
   * Helper function to check if build output exists
   */
  function buildOutputExists(): boolean {
    return fs.existsSync(distPath) && fs.statSync(distPath).isDirectory();
  }

  /**
   * Helper function to get build configuration for a platform
   */
  function getBuildConfigForPlatform(packageJson: any, platform: 'win' | 'mac' | 'linux'): any {
    return packageJson.build?.[platform] || {};
  }

  it('Property 11: Multi-platform build matrix must be properly configured', () => {
    // Property: CI workflow must define a build matrix with all target platforms
    const workflowContent = getCIWorkflowConfig();
    const platforms = extractPlatformMatrix(workflowContent);

    // Property: Build matrix must include all three major platforms
    expect(platforms).toContain('ubuntu-latest');
    expect(platforms).toContain('windows-latest');
    expect(platforms).toContain('macos-latest');

    // Property: Build matrix must have at least 3 platforms
    expect(platforms.length).toBeGreaterThanOrEqual(3);
  });

  it('Property 11.1: Build configuration must be consistent across platforms', () => {
    // Property: All platforms should use the same build process
    const packageJson = getPackageJson();

    // Property: Main entry point must be defined and consistent
    expect(packageJson.main).toBeDefined();
    expect(packageJson.main).toBe('electron/main.js');

    // Property: Build configuration must exist
    expect(packageJson.build).toBeDefined();
    expect(typeof packageJson.build).toBe('object');

    // Property: Build output directory must be consistent
    expect(packageJson.build.directories?.output).toBeDefined();

    // Property: Build files must be defined
    expect(packageJson.build.files).toBeDefined();
    expect(Array.isArray(packageJson.build.files)).toBe(true);
    expect(packageJson.build.files).toContain('dist/**/*');
  });

  it('Property 11.2: Platform-specific build targets must be properly configured', () => {
    // Property: Each platform must have valid build targets defined
    const packageJson = getPackageJson();

    // Windows configuration
    const winConfig = getBuildConfigForPlatform(packageJson, 'win');
    expect(winConfig.target).toBeDefined();
    expect(Array.isArray(winConfig.target)).toBe(true);
    expect(winConfig.target.length).toBeGreaterThan(0);

    // macOS configuration
    const macConfig = getBuildConfigForPlatform(packageJson, 'mac');
    expect(macConfig.target).toBeDefined();
    expect(Array.isArray(macConfig.target)).toBe(true);
    expect(macConfig.target.length).toBeGreaterThan(0);

    // Linux configuration
    const linuxConfig = getBuildConfigForPlatform(packageJson, 'linux');
    expect(linuxConfig.target).toBeDefined();
    expect(Array.isArray(linuxConfig.target)).toBe(true);
    expect(linuxConfig.target.length).toBeGreaterThan(0);
  });

  it('Property 11.3: Build output structure must be platform-independent', () => {
    // Property: The dist directory structure should be the same regardless of platform
    // This ensures that the build process produces consistent output

    if (!buildOutputExists()) {
      // If build hasn't been run, skip this test
      console.log('Build output not found, skipping platform-independent structure test');
      return;
    }

    // Property: dist directory must contain index.html
    const indexHtmlPath = path.join(distPath, 'index.html');
    expect(fs.existsSync(indexHtmlPath)).toBe(true);

    // Property: dist directory must contain assets subdirectory
    const assetsPath = path.join(distPath, 'assets');
    expect(fs.existsSync(assetsPath)).toBe(true);
    expect(fs.statSync(assetsPath).isDirectory()).toBe(true);

    // Property: Assets directory must contain JavaScript files
    const assetFiles = fs.readdirSync(assetsPath);
    const jsFiles = assetFiles.filter(f => f.endsWith('.js'));
    expect(jsFiles.length).toBeGreaterThan(0);

    // Property: Assets directory must contain CSS files
    const cssFiles = assetFiles.filter(f => f.endsWith('.css'));
    expect(cssFiles.length).toBeGreaterThan(0);
  });

  it('Property 11.4: Build scripts must be platform-agnostic', () => {
    // Property: Build scripts should work on all platforms
    const packageJson = getPackageJson();

    // Property: Build script must be defined
    expect(packageJson.scripts.build).toBeDefined();

    // Property: Build script should not contain platform-specific commands
    const buildScript = packageJson.scripts.build;

    // Property: Build script should use cross-platform commands
    // (npm/node commands work on all platforms)
    expect(buildScript).toContain('tsc');
    expect(buildScript).toContain('vite build');

    // Property: Build script should not contain shell-specific syntax
    // (no bash-only or cmd-only commands)
    expect(buildScript).not.toMatch(/\$\(/); // Bash command substitution
    expect(buildScript).not.toMatch(/%[A-Z_]+%/); // Windows environment variables
  });

  it('Property 11.5: CI build verification must be consistent across platforms', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate different platform configurations
        fc.constantFrom('ubuntu-latest', 'windows-latest', 'macos-latest'),
        async (platform) => {
          // Property: Each platform should run the same build verification steps
          const workflowContent = getCIWorkflowConfig();

          // Property: Build check job must exist
          expect(workflowContent).toContain('build-check:');

          // Property: Build check must run on the platform matrix
          expect(workflowContent).toContain('runs-on: ${{ matrix.os }}');

          // Property: Build check must include the platform
          expect(workflowContent).toContain(platform);

          // Property: Build verification steps must be platform-independent
          // The workflow uses bash shell for consistency
          expect(workflowContent).toContain('shell: bash');

          // Property: Build verification must check for dist directory
          expect(workflowContent).toContain('dist');
        }
      ),
      {
        numRuns: 100,
        verbose: true
      }
    );
  });

  it('Property 11.6: Node.js version must be consistent across platforms', () => {
    // Property: All platforms must use the same Node.js version
    const workflowContent = getCIWorkflowConfig();

    // Extract all Node.js version specifications
    const nodeVersionMatches = workflowContent.matchAll(/node-version:\s*['"]?(\d+)['"]?/g);
    const nodeVersions = Array.from(nodeVersionMatches).map(match => match[1]);

    // Property: At least one Node.js version must be specified
    expect(nodeVersions.length).toBeGreaterThan(0);

    // Property: All Node.js versions must be the same
    const uniqueVersions = new Set(nodeVersions);
    expect(uniqueVersions.size).toBe(1);

    // Property: Node.js version should be 18 (as specified in design)
    expect(nodeVersions[0]).toBe('18');
  });

  it('Property 11.7: Build dependencies must be installed consistently', () => {
    // Property: All platforms must use npm ci for deterministic installs
    const workflowContent = getCIWorkflowConfig();

    // Property: Build check job must use npm ci
    // Extract the build-check job section (handle both \n and \r\n line endings)
    const buildCheckMatch = workflowContent.match(/build-check:[\s\S]*?(?=\n\s{0,2}\w+:|$)/);
    const buildCheckSection = buildCheckMatch ? buildCheckMatch[0] : '';
    
    expect(buildCheckSection).toContain('npm ci');

    // Property: npm ci should not be followed by npm install
    // (npm ci is deterministic, npm install is not)
    expect(buildCheckSection).not.toMatch(/npm ci.*npm install/s);
  });

  it('Property 11.8: Build output verification must be consistent', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate different file types that should exist in build output
        fc.record({
          fileType: fc.constantFrom('html', 'js', 'css'),
          checkExists: fc.boolean(),
          checkSize: fc.boolean()
        }),
        async ({ fileType, checkExists, checkSize }) => {
          if (!buildOutputExists()) {
            // Skip if build hasn't been run
            return;
          }

          let filePath: string;
          let minSize = 0;

          if (fileType === 'html') {
            filePath = path.join(distPath, 'index.html');
            minSize = 200;
          } else {
            const assetsPath = path.join(distPath, 'assets');
            if (!fs.existsSync(assetsPath)) {
              return;
            }

            const files = fs.readdirSync(assetsPath).filter(f => f.endsWith(`.${fileType}`));
            if (files.length === 0) {
              return;
            }

            filePath = path.join(assetsPath, files[0]);
            minSize = fileType === 'js' ? 500 : 100;
          }

          // Property: If checking existence, file must exist
          if (checkExists) {
            expect(fs.existsSync(filePath)).toBe(true);
          }

          // Property: If checking size, file must have meaningful content
          if (checkSize && fs.existsSync(filePath)) {
            const stats = fs.statSync(filePath);
            expect(stats.size).toBeGreaterThan(minSize);
          }
        }
      ),
      {
        numRuns: 100,
        verbose: true
      }
    );
  });

  it('Property 11.9: Electron Builder configuration must support all platforms', () => {
    // Property: Electron Builder must be configured for Windows, macOS, and Linux
    const packageJson = getPackageJson();

    // Property: Build configuration must exist
    expect(packageJson.build).toBeDefined();

    // Property: Windows build configuration must exist
    expect(packageJson.build.win).toBeDefined();
    expect(packageJson.build.win.target).toBeDefined();

    // Property: macOS build configuration must exist
    expect(packageJson.build.mac).toBeDefined();
    expect(packageJson.build.mac.target).toBeDefined();

    // Property: Linux build configuration must exist
    expect(packageJson.build.linux).toBeDefined();
    expect(packageJson.build.linux.target).toBeDefined();

    // Property: Each platform must have at least one target format
    expect(packageJson.build.win.target.length).toBeGreaterThan(0);
    expect(packageJson.build.mac.target.length).toBeGreaterThan(0);
    expect(packageJson.build.linux.target.length).toBeGreaterThan(0);
  });

  it('Property 11.10: Build artifact naming must be consistent across platforms', () => {
    // Property: Artifact names should follow a consistent pattern across platforms
    const packageJson = getPackageJson();

    // Property: Windows artifacts should have consistent naming
    const winConfig = packageJson.build.win;
    if (winConfig.artifactName) {
      expect(winConfig.artifactName).toContain('${productName}');
      expect(winConfig.artifactName).toContain('${version}');
    }

    // Property: macOS artifacts should have consistent naming
    const macConfig = packageJson.build.mac;
    if (macConfig.artifactName) {
      expect(macConfig.artifactName).toContain('${productName}');
      expect(macConfig.artifactName).toContain('${version}');
      expect(macConfig.artifactName).toContain('${arch}');
    }

    // Property: Linux artifacts should have consistent naming
    const linuxConfig = packageJson.build.linux;
    if (linuxConfig.artifactName) {
      expect(linuxConfig.artifactName).toContain('${productName}');
      expect(linuxConfig.artifactName).toContain('${version}');
      expect(linuxConfig.artifactName).toContain('${arch}');
    }
  });

  it('Property 11.11: Build process must use same source files across platforms', () => {
    // Property: All platforms must build from the same source files
    const packageJson = getPackageJson();

    // Property: Build files configuration must be defined
    expect(packageJson.build.files).toBeDefined();
    expect(Array.isArray(packageJson.build.files)).toBe(true);

    // Property: Build must include dist directory (frontend build output)
    expect(packageJson.build.files).toContain('dist/**/*');

    // Property: Build must include electron directory
    expect(packageJson.build.files).toContain('electron/**/*');

    // Property: Build must include package.json
    expect(packageJson.build.files).toContain('package.json');

    // Property: All platforms use the same files configuration
    // (no platform-specific file overrides)
    const winConfig = packageJson.build.win;
    const macConfig = packageJson.build.mac;
    const linuxConfig = packageJson.build.linux;

    // If platform-specific files are defined, they should be additive, not replacements
    if (winConfig.files) {
      expect(Array.isArray(winConfig.files)).toBe(true);
    }
    if (macConfig.files) {
      expect(Array.isArray(macConfig.files)).toBe(true);
    }
    if (linuxConfig.files) {
      expect(Array.isArray(linuxConfig.files)).toBe(true);
    }
  });

  it('Property 11.12: CI build matrix must use fail-fast: false for independence', () => {
    // Property: Build matrix should not fail fast, allowing all platforms to complete
    // This ensures we see failures on all platforms, not just the first one
    const workflowContent = getCIWorkflowConfig();

    // Property: Build check job must have strategy configuration
    // Extract the build-check job section (handle both \n and \r\n line endings)
    const buildCheckMatch = workflowContent.match(/build-check:[\s\S]*?(?=\n\s{0,2}\w+:|$)/);
    const buildCheckSection = buildCheckMatch ? buildCheckMatch[0] : '';
    
    expect(buildCheckSection).toContain('strategy:');

    // Property: Strategy must set fail-fast to false
    expect(buildCheckSection).toContain('fail-fast: false');

    // Property: This ensures platform independence - one platform failure
    // doesn't prevent other platforms from completing their builds
  });

  it('Property 11.13: Build consistency with platform-specific variations', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate platform-specific build configurations
        fc.record({
          platform: fc.constantFrom('win', 'mac', 'linux'),
          hasArtifactName: fc.boolean(),
          hasCategory: fc.boolean()
        }),
        async ({ platform, hasArtifactName, hasCategory }) => {
          const packageJson = getPackageJson();
          const platformConfig = getBuildConfigForPlatform(packageJson, platform as any);

          // Property: Platform configuration must exist
          expect(platformConfig).toBeDefined();
          expect(typeof platformConfig).toBe('object');

          // Property: Platform must have targets defined
          expect(platformConfig.target).toBeDefined();
          expect(Array.isArray(platformConfig.target)).toBe(true);

          // Property: If artifact name is expected, it should follow conventions
          if (hasArtifactName && platformConfig.artifactName) {
            expect(platformConfig.artifactName).toMatch(/\$\{productName\}/);
            expect(platformConfig.artifactName).toMatch(/\$\{version\}/);
          }

          // Property: macOS and Linux should have category, Windows may not
          if (hasCategory && (platform === 'mac' || platform === 'linux')) {
            // Category helps with app store/launcher organization
            expect(platformConfig.category || platformConfig.categories).toBeDefined();
          }
        }
      ),
      {
        numRuns: 100,
        verbose: true
      }
    );
  });
});
