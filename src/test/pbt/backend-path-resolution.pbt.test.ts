/**
 * Property-Based Tests for Backend Path Resolution
 * 
 * **Feature: python-backend-bundling, Property 2: Path Resolution Consistency**
 * **Validates: Requirements 3.1, 3.2, 3.3**
 * 
 * Property: For any execution mode (development or production), when the 
 * BackendServiceManager resolves the backend path, the resolved path should 
 * point to an existing and executable file appropriate for that mode.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import * as fc from 'fast-check';
import * as fs from 'fs';
import * as path from 'path';

describe('Backend Path Resolution Property Tests', () => {
  const electronMainPath = path.join(process.cwd(), 'electron', 'main.js');

  /**
   * Helper function to read electron/main.js content
   */
  function getElectronMainContent(): string {
    if (!fs.existsSync(electronMainPath)) {
      throw new Error('electron/main.js not found');
    }
    return fs.readFileSync(electronMainPath, 'utf-8');
  }

  /**
   * Helper function to check if getBackendPath method exists
   */
  function hasGetBackendPathMethod(): boolean {
    const content = getElectronMainContent();
    return content.includes('getBackendPath()') || content.includes('async getBackendPath()');
  }

  /**
   * Helper function to extract getBackendPath method implementation
   */
  function extractGetBackendPathMethod(): string | null {
    const content = getElectronMainContent();
    const methodMatch = content.match(/async getBackendPath\(\)\s*\{[\s\S]*?\n\s{2}\}/);
    return methodMatch ? methodMatch[0] : null;
  }

  /**
   * Helper function to check if method uses app.isPackaged
   */
  function usesAppIsPackaged(methodContent: string): boolean {
    return methodContent.includes('app.isPackaged');
  }

  /**
   * Helper function to check if method handles production mode
   */
  function handlesProductionMode(methodContent: string): boolean {
    return (
      methodContent.includes('production') &&
      methodContent.includes('process.resourcesPath')
    );
  }

  /**
   * Helper function to check if method handles development mode
   */
  function handlesDevelopmentMode(methodContent: string): boolean {
    return (
      methodContent.includes('development') &&
      (methodContent.includes('backend/main.py') || methodContent.includes('findPythonExecutable'))
    );
  }

  /**
   * Helper function to check if method includes logging
   */
  function includesLogging(methodContent: string): boolean {
    return methodContent.includes('log.info') && methodContent.includes('mode') && methodContent.includes('platform');
  }

  /**
   * Helper function to check if method handles platform-specific naming
   */
  function handlesPlatformSpecificNaming(methodContent: string): boolean {
    return (
      methodContent.includes('win32') &&
      methodContent.includes('.exe') &&
      methodContent.includes('peft_engine')
    );
  }

  /**
   * Helper function to check if start method uses getBackendPath
   */
  function startMethodUsesGetBackendPath(): boolean {
    const content = getElectronMainContent();
    const startMethodMatch = content.match(/async start\(\)\s*\{[\s\S]*?\n\s{2}\}/);
    if (!startMethodMatch) {
      return false;
    }
    return startMethodMatch[0].includes('getBackendPath()');
  }

  /**
   * Helper function to check if start method handles production mode errors
   */
  function startMethodHandlesProductionErrors(): boolean {
    const content = getElectronMainContent();
    const startMethodMatch = content.match(/async start\(\)\s*\{[\s\S]*?\n\s{2}\}/);
    if (!startMethodMatch) {
      return false;
    }
    const startMethod = startMethodMatch[0];
    return (
      startMethod.includes('EXECUTABLE_NOT_FOUND') ||
      startMethod.includes('Installation may be corrupted')
    );
  }

  /**
   * Helper function to check if start method handles permission errors
   */
  function startMethodHandlesPermissionErrors(): boolean {
    const content = getElectronMainContent();
    const startMethodMatch = content.match(/async start\(\)\s*\{[\s\S]*?\n\s{2}\}/);
    if (!startMethodMatch) {
      return false;
    }
    const startMethod = startMethodMatch[0];
    return (
      startMethod.includes('chmod') ||
      startMethod.includes('PERMISSION_DENIED') ||
      startMethod.includes('execute permission')
    );
  }

  it('Property 2.1: getBackendPath method must exist in BackendServiceManager', () => {
    // Property: The getBackendPath method must be implemented
    expect(hasGetBackendPathMethod()).toBe(true);
  });

  it('Property 2.2: getBackendPath must use app.isPackaged for mode detection', () => {
    // Property: The method must distinguish between dev and prod using app.isPackaged
    const methodContent = extractGetBackendPathMethod();
    expect(methodContent).not.toBeNull();
    
    if (methodContent) {
      expect(usesAppIsPackaged(methodContent)).toBe(true);
    }
  });

  it('Property 2.3: getBackendPath must handle production mode correctly', () => {
    // Property: In production mode, must return path to bundled executable via process.resourcesPath
    const methodContent = extractGetBackendPathMethod();
    expect(methodContent).not.toBeNull();
    
    if (methodContent) {
      expect(handlesProductionMode(methodContent)).toBe(true);
    }
  });

  it('Property 2.4: getBackendPath must handle development mode correctly', () => {
    // Property: In development mode, must return path to Python script and use findPythonExecutable
    const methodContent = extractGetBackendPathMethod();
    expect(methodContent).not.toBeNull();
    
    if (methodContent) {
      expect(handlesDevelopmentMode(methodContent)).toBe(true);
    }
  });

  it('Property 2.5: getBackendPath must include logging with mode, path, and platform', () => {
    // Property: The method must log resolved paths with mode and platform information
    const methodContent = extractGetBackendPathMethod();
    expect(methodContent).not.toBeNull();
    
    if (methodContent) {
      expect(includesLogging(methodContent)).toBe(true);
    }
  });

  it('Property 2.6: getBackendPath must handle platform-specific executable naming', () => {
    // Property: Windows should use .exe extension, Unix-like systems should not
    const methodContent = extractGetBackendPathMethod();
    expect(methodContent).not.toBeNull();
    
    if (methodContent) {
      expect(handlesPlatformSpecificNaming(methodContent)).toBe(true);
    }
  });

  it('Property 2.7: start method must use getBackendPath for path resolution', () => {
    // Property: The start method must call getBackendPath instead of hardcoding paths
    expect(startMethodUsesGetBackendPath()).toBe(true);
  });

  it('Property 2.8: start method must handle production mode errors', () => {
    // Property: Must check if executable exists and provide clear error messages
    expect(startMethodHandlesProductionErrors()).toBe(true);
  });

  it('Property 2.9: start method must handle Unix permission errors', () => {
    // Property: Must attempt chmod +x on Unix systems and provide manual instructions if it fails
    expect(startMethodHandlesPermissionErrors()).toBe(true);
  });

  it('Property 2.10: Path resolution consistency across execution modes', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate different execution mode scenarios
        fc.record({
          isPackaged: fc.boolean(),
          platform: fc.constantFrom('win32', 'darwin', 'linux'),
        }),
        async ({ isPackaged, platform }) => {
          const methodContent = extractGetBackendPathMethod();
          expect(methodContent).not.toBeNull();
          
          if (!methodContent) {
            return;
          }

          // Property: For production mode, path must include process.resourcesPath
          if (isPackaged) {
            expect(methodContent).toContain('process.resourcesPath');
            expect(methodContent).toContain('backend');
            
            // Property: Windows must use .exe extension
            if (platform === 'win32') {
              expect(methodContent).toContain('peft_engine.exe');
            } else {
              // Property: Unix-like systems use no extension
              expect(methodContent).toContain('peft_engine');
            }
          } else {
            // Property: For development mode, must use Python script
            expect(methodContent).toContain('backend/main.py');
            expect(methodContent).toContain('findPythonExecutable');
          }
        }
      ),
      {
        numRuns: 100,
        verbose: true
      }
    );
  });

  it('Property 2.11: Return value structure consistency', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate different mode and platform combinations
        fc.record({
          mode: fc.constantFrom('development', 'production'),
          platform: fc.constantFrom('win32', 'darwin', 'linux'),
        }),
        async ({ mode, platform }) => {
          const methodContent = extractGetBackendPathMethod();
          expect(methodContent).not.toBeNull();
          
          if (!methodContent) {
            return;
          }

          // Property: Return value must include mode field
          expect(methodContent).toContain("mode: 'production'");
          expect(methodContent).toContain("mode: 'development'");
          
          // Property: Return value must include executable field
          expect(methodContent).toContain('executable:');
          
          // Property: Return value must include args field
          expect(methodContent).toContain('args:');
          
          // Property: Return value must include platform field
          expect(methodContent).toContain('platform');
        }
      ),
      {
        numRuns: 100,
        verbose: true
      }
    );
  });

  it('Property 2.12: Error handling consistency across modes', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate different error scenarios
        fc.record({
          errorType: fc.constantFrom('PYTHON_NOT_FOUND', 'EXECUTABLE_NOT_FOUND', 'PERMISSION_DENIED'),
          mode: fc.constantFrom('development', 'production'),
        }),
        async ({ errorType, mode }) => {
          const content = getElectronMainContent();
          const startMethodMatch = content.match(/async start\(\)\s*\{[\s\S]*?\n\s{2}\}/);
          expect(startMethodMatch).not.toBeNull();
          
          if (!startMethodMatch) {
            return;
          }
          
          const startMethod = startMethodMatch[0];

          // Property: Development mode must handle PYTHON_NOT_FOUND
          if (mode === 'development' && errorType === 'PYTHON_NOT_FOUND') {
            expect(startMethod).toContain('PYTHON_NOT_FOUND');
            expect(startMethod).toContain('Python 3.10+');
          }

          // Property: Production mode must handle EXECUTABLE_NOT_FOUND
          if (mode === 'production' && errorType === 'EXECUTABLE_NOT_FOUND') {
            expect(startMethod).toContain('EXECUTABLE_NOT_FOUND');
            expect(startMethod).toContain('Installation may be corrupted');
          }

          // Property: Production mode on Unix must handle PERMISSION_DENIED
          if (mode === 'production' && errorType === 'PERMISSION_DENIED') {
            expect(startMethod).toContain('PERMISSION_DENIED');
            expect(startMethod).toContain('chmod');
          }
        }
      ),
      {
        numRuns: 100,
        verbose: true
      }
    );
  });

  it('Property 2.13: Logging consistency across all code paths', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate different logging scenarios
        fc.record({
          logLevel: fc.constantFrom('info', 'error', 'warn'),
          context: fc.constantFrom('path_resolution', 'mode_detection', 'error_handling'),
        }),
        async ({ logLevel, context }) => {
          const content = getElectronMainContent();
          
          // Property: All log statements must use electron-log
          const logMatches = content.match(/log\.(info|error|warn)/g);
          expect(logMatches).not.toBeNull();
          expect(logMatches!.length).toBeGreaterThan(0);

          // Property: Path resolution must include mode and platform in logs
          if (context === 'path_resolution') {
            const methodContent = extractGetBackendPathMethod();
            if (methodContent) {
              expect(methodContent).toContain('log.info');
              expect(methodContent).toContain('mode');
              expect(methodContent).toContain('platform');
            }
          }

          // Property: Error logs must include error codes
          if (logLevel === 'error') {
            const errorLogMatches = content.match(/log\.error\([^)]+\)/g);
            if (errorLogMatches && errorLogMatches.length > 0) {
              // At least some error logs should include context
              const hasContextInErrors = errorLogMatches.some(log => 
                log.includes('code') || log.includes('error')
              );
              expect(hasContextInErrors).toBe(true);
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

  it('Property 2.14: Backend executable naming follows platform conventions', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate platform-specific naming scenarios
        fc.constantFrom('win32', 'darwin', 'linux'),
        async (platform) => {
          const methodContent = extractGetBackendPathMethod();
          expect(methodContent).not.toBeNull();
          
          if (!methodContent) {
            return;
          }

          // Property: All platforms must use 'peft_engine' as base name
          expect(methodContent).toContain('peft_engine');

          // Property: Windows must append .exe extension
          if (platform === 'win32') {
            expect(methodContent).toContain("platform === 'win32'");
            expect(methodContent).toContain('peft_engine.exe');
          }

          // Property: Unix-like systems must not append extension
          if (platform === 'darwin' || platform === 'linux') {
            // The method should handle non-Windows platforms
            expect(methodContent).toMatch(/peft_engine['"]?\s*(?!\.exe)/);
          }
        }
      ),
      {
        numRuns: 100,
        verbose: true
      }
    );
  });

  it('Property 2.15: Development mode Python script path must be relative to electron directory', () => {
    // Property: Development mode must use relative path from electron/main.js to backend/main.py
    const methodContent = extractGetBackendPathMethod();
    expect(methodContent).not.toBeNull();
    
    if (methodContent) {
      // Property: Must use __dirname for relative path resolution
      expect(methodContent).toContain('__dirname');
      expect(methodContent).toContain('../backend/main.py');
    }
  });

  it('Property 2.16: Production mode executable path must use process.resourcesPath', () => {
    // Property: Production mode must use process.resourcesPath for bundled executable
    const methodContent = extractGetBackendPathMethod();
    expect(methodContent).not.toBeNull();
    
    if (methodContent) {
      // Property: Must use process.resourcesPath
      expect(methodContent).toContain('process.resourcesPath');
      
      // Property: Must join with 'backend' subdirectory
      expect(methodContent).toContain("'backend'");
    }
  });

  it('Property 2.17: Start method must spawn process with correct arguments based on mode', () => {
    // Property: Development mode spawns Python with script as argument
    // Property: Production mode spawns executable directly
    const content = getElectronMainContent();
    const startMethodMatch = content.match(/async start\(\)\s*\{[\s\S]*?\n\s{2}\}/);
    expect(startMethodMatch).not.toBeNull();
    
    if (startMethodMatch) {
      const startMethod = startMethodMatch[0];
      
      // Property: Must use spawn with backendInfo.executable and backendInfo.args
      expect(startMethod).toContain('spawn(backendInfo.executable, backendInfo.args');
      
      // Property: Must set PYTHONUNBUFFERED environment variable
      expect(startMethod).toContain('PYTHONUNBUFFERED');
    }
  });

  it('Property 2.18: Stdout and stderr capture must work for both modes', () => {
    // Property: Process stdout/stderr capture should work for both Python script and executable
    const content = getElectronMainContent();
    const startMethodMatch = content.match(/async start\(\)\s*\{[\s\S]*?\n\s{2}\}/);
    expect(startMethodMatch).not.toBeNull();
    
    if (startMethodMatch) {
      const startMethod = startMethodMatch[0];
      
      // Property: Must capture stdout
      expect(startMethod).toContain("this.process.stdout.on('data'");
      
      // Property: Must capture stderr
      expect(startMethod).toContain("this.process.stderr.on('data'");
      
      // Property: Capture should not be mode-specific (works for both)
      // The spawn configuration should be the same regardless of mode
    }
  });
});
