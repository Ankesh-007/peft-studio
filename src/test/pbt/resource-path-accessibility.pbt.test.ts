/**
 * Property-Based Tests for Resource Path Accessibility
 * 
 * **Feature: python-backend-bundling, Property 6: Resource Path Accessibility**
 * **Validates: Requirements 5.1, 5.3**
 * 
 * Property: For any packaged application, when the application is installed 
 * and launched, the backend executable should be accessible via 
 * process.resourcesPath and should be executable with appropriate permissions.
 */

import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import * as fs from 'fs';
import * as path from 'path';

describe('Resource Path Accessibility Property Tests', () => {
  const packageJsonPath = path.join(process.cwd(), 'package.json');

  /**
   * Helper function to read package.json content
   */
  function getPackageJsonContent(): any {
    if (!fs.existsSync(packageJsonPath)) {
      throw new Error('package.json not found');
    }
    const content = fs.readFileSync(packageJsonPath, 'utf-8');
    return JSON.parse(content);
  }

  /**
   * Helper function to check if extraResources is configured
   */
  function hasExtraResourcesConfig(): boolean {
    const packageJson = getPackageJsonContent();
    return packageJson.build && packageJson.build.extraResources !== undefined;
  }

  /**
   * Helper function to get extraResources configuration
   */
  function getExtraResourcesConfig(): any[] {
    const packageJson = getPackageJsonContent();
    if (!packageJson.build || !packageJson.build.extraResources) {
      return [];
    }
    return Array.isArray(packageJson.build.extraResources) 
      ? packageJson.build.extraResources 
      : [packageJson.build.extraResources];
  }

  /**
   * Helper function to check if backend executable is included in extraResources
   */
  function backendExecutableInExtraResources(): boolean {
    const extraResources = getExtraResourcesConfig();
    return extraResources.some(resource => {
      if (typeof resource === 'string') {
        return resource.includes('backend') && resource.includes('peft_engine');
      }
      if (typeof resource === 'object' && resource.from) {
        return resource.from.includes('backend/dist') && resource.from.includes('peft_engine');
      }
      return false;
    });
  }

  /**
   * Helper function to check if backend source files are excluded from asar
   */
  function backendSourceExcludedFromAsar(): boolean {
    const packageJson = getPackageJsonContent();
    if (!packageJson.build || !packageJson.build.files) {
      return false;
    }
    
    const files = packageJson.build.files;
    // Check if backend source is excluded (either not included or explicitly excluded)
    const hasBackendExclusion = files.some((pattern: string) => 
      pattern === '!backend/**/*' || pattern === '!backend/**.py'
    );
    
    // Or check if only specific backend files are included (not source)
    const hasSelectiveInclusion = files.some((pattern: string) => 
      pattern.includes('backend/dist') || pattern.includes('backend/*.spec')
    );
    
    return hasBackendExclusion || hasSelectiveInclusion;
  }

  /**
   * Helper function to check Windows NSIS configuration
   */
  function hasCorrectWindowsConfig(): boolean {
    const packageJson = getPackageJsonContent();
    if (!packageJson.build || !packageJson.build.win) {
      return false;
    }
    
    const winConfig = packageJson.build.win;
    
    // Check if requestedExecutionLevel is set to asInvoker
    const hasCorrectExecutionLevel = 
      winConfig.requestedExecutionLevel === 'asInvoker' ||
      (packageJson.build.nsis && packageJson.build.nsis.requestedExecutionLevel === 'asInvoker');
    
    return hasCorrectExecutionLevel;
  }

  /**
   * Helper function to check if platform-specific settings are correct
   */
  function hasPlatformSpecificSettings(platform: 'win' | 'mac' | 'linux'): boolean {
    const packageJson = getPackageJsonContent();
    if (!packageJson.build) {
      return false;
    }
    
    return packageJson.build[platform] !== undefined;
  }

  /**
   * Helper function to validate extraResources path structure
   */
  function validateExtraResourcesPathStructure(resource: any): boolean {
    if (typeof resource === 'string') {
      return true; // Simple string paths are valid
    }
    
    if (typeof resource === 'object') {
      // Must have 'from' field
      if (!resource.from) {
        return false;
      }
      
      // Should have 'to' field for proper placement
      if (!resource.to) {
        return false;
      }
      
      // 'to' should be 'backend' to match process.resourcesPath/backend structure
      if (resource.to !== 'backend') {
        return false;
      }
      
      return true;
    }
    
    return false;
  }

  /**
   * Helper function to check if backend executable filter is correct
   */
  function hasCorrectBackendExecutableFilter(): boolean {
    const extraResources = getExtraResourcesConfig();
    
    for (const resource of extraResources) {
      if (typeof resource === 'object' && resource.from && resource.from.includes('backend/dist')) {
        // Should have a filter for peft_engine executables
        if (resource.filter) {
          const filters = Array.isArray(resource.filter) ? resource.filter : [resource.filter];
          return filters.some((f: string) => f.includes('peft_engine'));
        }
      }
    }
    
    return false;
  }

  it('Property 6.1: extraResources configuration must exist in package.json', () => {
    // Property: The build configuration must include extraResources
    expect(hasExtraResourcesConfig()).toBe(true);
  });

  it('Property 6.2: Backend executable must be included in extraResources', () => {
    // Property: extraResources must include backend/dist/peft_engine*
    expect(backendExecutableInExtraResources()).toBe(true);
  });

  it('Property 6.3: Backend source files must be excluded from asar', () => {
    // Property: Backend source files should not be included in the asar archive
    expect(backendSourceExcludedFromAsar()).toBe(true);
  });

  it('Property 6.4: Windows configuration must have correct execution level', () => {
    // Property: Windows builds must use asInvoker execution level
    expect(hasCorrectWindowsConfig()).toBe(true);
  });

  it('Property 6.5: Platform-specific settings must exist for all platforms', () => {
    // Property: Build configuration must include settings for Windows, macOS, and Linux
    expect(hasPlatformSpecificSettings('win')).toBe(true);
    expect(hasPlatformSpecificSettings('mac')).toBe(true);
    expect(hasPlatformSpecificSettings('linux')).toBe(true);
  });

  it('Property 6.6: extraResources path structure must be valid', () => {
    // Property: Each extraResources entry must have proper structure
    const extraResources = getExtraResourcesConfig();
    expect(extraResources.length).toBeGreaterThan(0);
    
    for (const resource of extraResources) {
      expect(validateExtraResourcesPathStructure(resource)).toBe(true);
    }
  });

  it('Property 6.7: Backend executable filter must be correct', () => {
    // Property: extraResources must filter for peft_engine executables
    expect(hasCorrectBackendExecutableFilter()).toBe(true);
  });

  it('Property 6.8: Resource path accessibility across platforms', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate different platform scenarios
        fc.constantFrom('win32', 'darwin', 'linux'),
        async (platform) => {
          const extraResources = getExtraResourcesConfig();
          
          // Property: extraResources must be configured for all platforms
          expect(extraResources.length).toBeGreaterThan(0);
          
          // Property: Backend executable must be accessible via process.resourcesPath/backend
          const backendResource = extraResources.find(resource => {
            if (typeof resource === 'object' && resource.from) {
              return resource.from.includes('backend/dist');
            }
            return false;
          });
          
          expect(backendResource).toBeDefined();
          
          if (backendResource && typeof backendResource === 'object') {
            // Property: 'to' field must be 'backend' for correct path resolution
            expect(backendResource.to).toBe('backend');
            
            // Property: 'from' field must point to backend/dist directory
            expect(backendResource.from).toContain('backend/dist');
            
            // Property: Must include peft_engine in the path or filter
            const includesPeftEngine = 
              backendResource.from.includes('peft_engine') ||
              (backendResource.filter && 
               (Array.isArray(backendResource.filter) 
                 ? backendResource.filter.some((f: string) => f.includes('peft_engine'))
                 : backendResource.filter.includes('peft_engine')));
            
            expect(includesPeftEngine).toBe(true);
          }
        }
      ),
      {
        numRuns: 100,
        verbose: true
      }
    );
  });

  it('Property 6.9: Executable naming consistency with platform conventions', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate platform-specific naming scenarios
        fc.constantFrom('win32', 'darwin', 'linux'),
        async (platform) => {
          const extraResources = getExtraResourcesConfig();
          const backendResource = extraResources.find(resource => {
            if (typeof resource === 'object' && resource.from) {
              return resource.from.includes('backend/dist');
            }
            return false;
          });
          
          expect(backendResource).toBeDefined();
          
          if (backendResource && typeof backendResource === 'object') {
            // Property: All platforms must use 'peft_engine' as base name
            expect(backendResource.from).toContain('peft_engine');
            
            // Property: Windows executable should have .exe extension in filter
            if (platform === 'win32') {
              // The from path or filter should account for .exe
              const accountsForExe = 
                backendResource.from.includes('${/*}') || // Glob pattern
                backendResource.from.includes('*') || // Wildcard
                (backendResource.filter && 
                 (Array.isArray(backendResource.filter)
                   ? backendResource.filter.some((f: string) => f.includes('peft_engine'))
                   : backendResource.filter.includes('peft_engine')));
              
              expect(accountsForExe).toBe(true);
            }
          }
        }
      ),
      {
        numRuns: 100,
        verbose: true
      }
    );
  });

  it('Property 6.10: Files configuration excludes backend source appropriately', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate different file patterns
        fc.constantFrom('*.py', '*.pyc', '__pycache__', 'services', 'connectors'),
        async (pattern) => {
          const packageJson = getPackageJsonContent();
          const files = packageJson.build?.files || [];
          
          // Property: Backend source files should not be included in the main files list
          // unless they are specifically needed (like .spec files)
          
          // Check if backend/** is included
          const includesBackend = files.some((f: string) => 
            f === 'backend/**/*' || f === 'backend/**'
          );
          
          if (includesBackend) {
            // If backend is included, there should be exclusions or it should be in extraResources
            const hasExclusions = files.some((f: string) => f.startsWith('!backend'));
            const hasExtraResources = hasExtraResourcesConfig();
            
            // Property: Either have exclusions or use extraResources (preferred)
            expect(hasExclusions || hasExtraResources).toBe(true);
          }
        }
      ),
      {
        numRuns: 100,
        verbose: true
      }
    );
  });

  it('Property 6.11: NSIS configuration must allow installation directory choice', () => {
    // Property: NSIS installer should allow users to choose installation directory
    const packageJson = getPackageJsonContent();
    
    if (packageJson.build?.nsis) {
      const nsisConfig = packageJson.build.nsis;
      
      // Property: Should not be oneClick (allows directory choice)
      if (nsisConfig.oneClick !== undefined) {
        expect(nsisConfig.oneClick).toBe(false);
      }
      
      // Property: Should allow changing installation directory
      if (nsisConfig.allowToChangeInstallationDirectory !== undefined) {
        expect(nsisConfig.allowToChangeInstallationDirectory).toBe(true);
      }
    }
  });

  it('Property 6.12: DMG configuration must be present for macOS', () => {
    // Property: macOS builds should have DMG configuration
    const packageJson = getPackageJsonContent();
    
    if (packageJson.build?.mac) {
      const macConfig = packageJson.build.mac;
      
      // Property: Should target DMG format
      if (macConfig.target) {
        const targets = Array.isArray(macConfig.target) ? macConfig.target : [macConfig.target];
        const hasDmg = targets.some((t: any) => 
          (typeof t === 'string' && t === 'dmg') ||
          (typeof t === 'object' && t.target === 'dmg')
        );
        expect(hasDmg).toBe(true);
      }
    }
  });

  it('Property 6.13: AppImage configuration must be present for Linux', () => {
    // Property: Linux builds should have AppImage configuration
    const packageJson = getPackageJsonContent();
    
    if (packageJson.build?.linux) {
      const linuxConfig = packageJson.build.linux;
      
      // Property: Should target AppImage format
      if (linuxConfig.target) {
        const targets = Array.isArray(linuxConfig.target) ? linuxConfig.target : [linuxConfig.target];
        const hasAppImage = targets.some((t: any) => 
          (typeof t === 'string' && t === 'AppImage') ||
          (typeof t === 'object' && t.target === 'AppImage')
        );
        expect(hasAppImage).toBe(true);
      }
    }
  });

  it('Property 6.14: Backend executable must be copied to correct location', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate different resource path scenarios
        fc.record({
          platform: fc.constantFrom('win32', 'darwin', 'linux'),
          resourcesPath: fc.constantFrom('/app/resources', 'C:\\Program Files\\App\\resources', '/Applications/App.app/Contents/Resources'),
        }),
        async ({ platform, resourcesPath }) => {
          const extraResources = getExtraResourcesConfig();
          const backendResource = extraResources.find(resource => {
            if (typeof resource === 'object' && resource.from) {
              return resource.from.includes('backend/dist');
            }
            return false;
          });
          
          expect(backendResource).toBeDefined();
          
          if (backendResource && typeof backendResource === 'object') {
            // Property: Backend executable should be placed in resources/backend directory
            expect(backendResource.to).toBe('backend');
            
            // Property: This allows access via process.resourcesPath + '/backend/peft_engine'
            const expectedPath = path.join(resourcesPath, 'backend', 'peft_engine');
            
            // Property: Path should be constructible from resourcesPath and 'to' field
            const constructedPath = path.join(resourcesPath, backendResource.to, 'peft_engine');
            expect(constructedPath).toContain('backend');
            expect(constructedPath).toContain('peft_engine');
          }
        }
      ),
      {
        numRuns: 100,
        verbose: true
      }
    );
  });

  it('Property 6.15: Build configuration must not include unnecessary backend files', () => {
    // Property: Only the compiled executable should be included, not source files
    const packageJson = getPackageJsonContent();
    const files = packageJson.build?.files || [];
    
    // Property: Should not include backend source patterns that would bundle Python files
    const includesBackendSource = files.some((f: string) => 
      f === 'backend/**/*.py' || 
      f === 'backend/services/**/*' ||
      f === 'backend/connectors/**/*'
    );
    
    // If backend source is included, it should be excluded or overridden by extraResources
    if (includesBackendSource) {
      const hasExtraResources = hasExtraResourcesConfig();
      expect(hasExtraResources).toBe(true);
    }
  });

  it('Property 6.16: extraResources configuration must handle platform-specific executables', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate platform and architecture combinations
        fc.record({
          platform: fc.constantFrom('win32', 'darwin', 'linux'),
          arch: fc.constantFrom('x64', 'arm64'),
        }),
        async ({ platform, arch }) => {
          const extraResources = getExtraResourcesConfig();
          const backendResource = extraResources.find(resource => {
            if (typeof resource === 'object' && resource.from) {
              return resource.from.includes('backend/dist');
            }
            return false;
          });
          
          expect(backendResource).toBeDefined();
          
          if (backendResource && typeof backendResource === 'object') {
            // Property: Must use glob pattern or wildcard to handle platform-specific names
            const usesGlobPattern = 
              backendResource.from.includes('${/*}') ||
              backendResource.from.includes('*') ||
              backendResource.from.includes('peft_engine*');
            
            expect(usesGlobPattern).toBe(true);
            
            // Property: Filter should match peft_engine with or without extension
            if (backendResource.filter) {
              const filters = Array.isArray(backendResource.filter) 
                ? backendResource.filter 
                : [backendResource.filter];
              
              const matchesPeftEngine = filters.some((f: string) => 
                f.includes('peft_engine') || f === 'peft_engine*'
              );
              
              expect(matchesPeftEngine).toBe(true);
            }
          }
        }
      ),
      {
        numRuns: 100,
        verbose: true
      }
    );
  });

  it('Property 6.17: Windows requestedExecutionLevel must not require admin', () => {
    // Property: Application should run without requiring administrator privileges
    const packageJson = getPackageJsonContent();
    
    // Check in win config
    if (packageJson.build?.win?.requestedExecutionLevel) {
      expect(packageJson.build.win.requestedExecutionLevel).toBe('asInvoker');
    }
    
    // Check in nsis config
    if (packageJson.build?.nsis?.requestedExecutionLevel) {
      expect(packageJson.build.nsis.requestedExecutionLevel).toBe('asInvoker');
    }
    
    // Property: At least one of them should be set to asInvoker
    const hasCorrectLevel = 
      packageJson.build?.win?.requestedExecutionLevel === 'asInvoker' ||
      packageJson.build?.nsis?.requestedExecutionLevel === 'asInvoker';
    
    expect(hasCorrectLevel).toBe(true);
  });
});
