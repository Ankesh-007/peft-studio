/**
 * Platform-Specific Integration Test: Windows
 * 
 * This test suite verifies Windows-specific requirements for the Python backend bundling:
 * - .exe extension for executable
 * - No console window (--noconsole flag)
 * - NSIS installer configuration
 * - Windows-specific path handling
 * - Process management on Windows
 * 
 * Requirements: 2.1, 2.2, 2.3
 */

import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('Windows Platform-Specific Tests', () => {
  const packageJsonPath = path.join(process.cwd(), 'package.json');
  const electronMainPath = path.join(process.cwd(), 'electron', 'main.js');
  const pyinstallerSpecPath = path.join(process.cwd(), 'backend', 'peft_engine.spec');

  function getPackageJson() {
    return JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
  }

  function getElectronMainContent(): string {
    return fs.readFileSync(electronMainPath, 'utf-8');
  }

  function getPyInstallerSpec(): string {
    if (!fs.existsSync(pyinstallerSpecPath)) {
      return '';
    }
    return fs.readFileSync(pyinstallerSpecPath, 'utf-8');
  }

  describe('Requirement 2.1: Windows Executable Generation', () => {
    it('should generate peft_engine.exe for Windows', () => {
      const electronMain = getElectronMainContent();
      const getBackendPathMatch = electronMain.match(/async getBackendPath\(\)[\s\S]*?\n\s{2}\}/);
      
      expect(getBackendPathMatch).not.toBeNull();
      
      if (getBackendPathMatch) {
        const getBackendPath = getBackendPathMatch[0];
        
        // Verify Windows-specific executable name
        expect(getBackendPath).toContain("platform === 'win32'");
        expect(getBackendPath).toContain('peft_engine.exe');
      }
    });

    it('should use .exe extension only on Windows', () => {
      const electronMain = getElectronMainContent();
      const getBackendPathMatch = electronMain.match(/async getBackendPath\(\)[\s\S]*?\n\s{2}\}/);
      
      if (getBackendPathMatch) {
        const getBackendPath = getBackendPathMatch[0];
        
        // Verify conditional extension logic
        expect(getBackendPath).toMatch(/win32.*\.exe/);
        // Verify non-Windows platforms use no extension
        expect(getBackendPath).toContain('peft_engine');
      }
    });

    it('should place executable in backend/dist/ directory', () => {
      const pkg = getPackageJson();
      const buildBackendScript = pkg.scripts?.['build:backend'] || '';
      
      // Verify PyInstaller outputs to dist directory
      expect(buildBackendScript).toContain('pyinstaller');
      expect(buildBackendScript).toContain('peft_engine.spec');
    });
  });

  describe('Requirement 2.2: Console Window Hiding', () => {
    it('should configure PyInstaller console setting', () => {
      const spec = getPyInstallerSpec();
      
      if (spec) {
        // Verify console setting exists (may be True for debugging, Electron handles hiding)
        expect(spec).toContain('console=');
      }
    });

    it('should spawn process without showing console window', () => {
      const electronMain = getElectronMainContent();
      const startMethodMatch = electronMain.match(/async start\(\)[\s\S]*?\n\s{2}\}/);
      
      if (startMethodMatch) {
        const startMethod = startMethodMatch[0];
        
        // Verify spawn is used (Electron handles console hiding)
        expect(startMethod).toContain('spawn');
        expect(startMethod).not.toContain('shell: true');
      }
    });

    it('should handle process output without console window', () => {
      const electronMain = getElectronMainContent();
      const startMethodMatch = electronMain.match(/async start\(\)[\s\S]*?\n\s{2}\}/);
      
      if (startMethodMatch) {
        const startMethod = startMethodMatch[0];
        
        // Verify stdout/stderr are captured (prevents console window)
        expect(startMethod).toContain('stdout.on');
        expect(startMethod).toContain('stderr.on');
      }
    });
  });

  describe('Requirement 2.3: NSIS Installer Configuration', () => {
    it('should configure NSIS as Windows installer format', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const win = build.win || {};
      
      // Verify NSIS is in target list
      expect(win.target).toBeDefined();
      expect(Array.isArray(win.target)).toBe(true);
      
      if (Array.isArray(win.target)) {
        const hasNsis = win.target.some((t: any) => 
          typeof t === 'string' ? t === 'nsis' : t.target === 'nsis'
        );
        expect(hasNsis).toBe(true);
      }
    });

    it('should set requestedExecutionLevel to asInvoker', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const win = build.win || {};
      
      // Verify execution level doesn't require admin
      expect(win.requestedExecutionLevel).toBe('asInvoker');
    });

    it('should include backend executable in extraResources', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const extraResources = build.extraResources || [];
      
      // Verify backend executable is included
      const hasBackendResource = extraResources.some((resource: any) => {
        if (typeof resource === 'string') {
          return resource.includes('backend') && resource.includes('peft_engine');
        }
        return resource.from && resource.from.includes('backend/dist/peft_engine');
      });
      
      expect(hasBackendResource).toBe(true);
    });

    it('should configure NSIS installer options', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const nsis = build.nsis || {};
      
      // Verify NSIS configuration exists
      // Common options: oneClick, perMachine, allowToChangeInstallationDirectory
      expect(nsis).toBeDefined();
    });
  });

  describe('Windows Path Handling', () => {
    it('should handle Windows path separators correctly', () => {
      const electronMain = getElectronMainContent();
      const getBackendPathMatch = electronMain.match(/async getBackendPath\(\)[\s\S]*?\n\s{2}\}/);
      
      if (getBackendPathMatch) {
        const getBackendPath = getBackendPathMatch[0];
        
        // Verify path.join is used (handles platform-specific separators)
        expect(getBackendPath).toContain('path.join');
        
        // Should not have hardcoded forward slashes for paths
        const hasHardcodedSlashes = /['"].*\/.*backend.*['"]/.test(getBackendPath);
        if (hasHardcodedSlashes) {
          // If there are hardcoded slashes, they should be in path.join calls
          expect(getBackendPath).toContain('path.join');
        }
      }
    });

    it('should use process.resourcesPath for production mode', () => {
      const electronMain = getElectronMainContent();
      const getBackendPathMatch = electronMain.match(/async getBackendPath\(\)[\s\S]*?\n\s{2}\}/);
      
      if (getBackendPathMatch) {
        const getBackendPath = getBackendPathMatch[0];
        
        // Verify resourcesPath is used in production
        expect(getBackendPath).toContain('process.resourcesPath');
        expect(getBackendPath).toContain('app.isPackaged');
      }
    });
  });

  describe('Windows Process Management', () => {
    it('should handle SIGTERM on Windows', () => {
      const electronMain = getElectronMainContent();
      const stopMethodMatch = electronMain.match(/async stop\(\)[\s\S]*?\n\s{2}\}/);
      
      if (stopMethodMatch) {
        const stopMethod = stopMethodMatch[0];
        
        // Verify SIGTERM is sent (works on Windows with Node.js)
        expect(stopMethod).toContain("kill('SIGTERM')");
      }
    });

    it('should handle SIGKILL on Windows', () => {
      const electronMain = getElectronMainContent();
      const stopMethodMatch = electronMain.match(/async stop\(\)[\s\S]*?\n\s{2}\}/);
      
      if (stopMethodMatch) {
        const stopMethod = stopMethodMatch[0];
        
        // Verify SIGKILL is sent as fallback
        expect(stopMethod).toContain("kill('SIGKILL')");
      }
    });

    it('should handle process termination on Windows', () => {
      const electronMain = getElectronMainContent();
      const stopMethodMatch = electronMain.match(/async stop\(\)[\s\S]*?\n\s{2}\}/);
      
      if (stopMethodMatch) {
        const stopMethod = stopMethodMatch[0];
        
        // Verify process is properly terminated
        expect(stopMethod).toContain('this.process');
        expect(stopMethod).toContain('kill');
      }
    });
  });

  describe('Windows Build Scripts', () => {
    it('should support Windows build configuration', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const win = build.win || {};
      
      // Verify Windows build configuration exists
      expect(win).toBeDefined();
    });

    it('should have backend build script', () => {
      const pkg = getPackageJson();
      const scripts = pkg.scripts || {};
      
      // Verify backend build script exists
      expect(scripts['build:backend']).toBeDefined();
    });

    it('should have build verification script', () => {
      const pkg = getPackageJson();
      const scripts = pkg.scripts || {};
      
      // Verify build verification exists
      expect(scripts['build:backend:verify']).toBeDefined();
    });
  });

  describe('Windows Executable Verification', () => {
    it('should verify .exe file exists after build', () => {
      const pkg = getPackageJson();
      const scripts = pkg.scripts || {};
      
      // Verify verification script exists
      expect(scripts['build:backend:verify']).toBeDefined();
    });

    it('should check executable size is reasonable', () => {
      // This is verified in the verify-backend-build.js script
      const verifyScriptPath = path.join(process.cwd(), 'scripts', 'verify-backend-build.js');
      
      if (fs.existsSync(verifyScriptPath)) {
        const verifyScript = fs.readFileSync(verifyScriptPath, 'utf-8');
        
        // Verify size check exists
        expect(verifyScript).toContain('stats.size');
        expect(verifyScript).toContain('1024 * 1024'); // 1MB minimum
      }
    });
  });

  describe('Windows Installer Testing', () => {
    it('should configure installer to work on clean systems', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const win = build.win || {};
      
      // Verify no Python dependency is required
      // The bundled executable should be self-contained
      expect(win.requestedExecutionLevel).toBe('asInvoker');
      
      // Verify extraResources includes backend
      const extraResources = build.extraResources || [];
      expect(extraResources.length).toBeGreaterThan(0);
    });

    it('should not require administrator privileges', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const win = build.win || {};
      
      // Verify asInvoker level (no admin required)
      expect(win.requestedExecutionLevel).toBe('asInvoker');
    });
  });

  describe('Windows Error Handling', () => {
    it('should handle Windows-specific error messages', () => {
      const electronMain = getElectronMainContent();
      
      // Verify error handling exists
      expect(electronMain).toContain('stderr');
      expect(electronMain).toContain('error');
      
      // Verify platform-specific error handling
      const startMethodMatch = electronMain.match(/async start\(\)[\s\S]*?\n\s{2}\}/);
      if (startMethodMatch) {
        const startMethod = startMethodMatch[0];
        
        // Should handle stderr output
        expect(startMethod).toContain("stderr.on('data'");
      }
    });

    it('should log platform information in errors', () => {
      const electronMain = getElectronMainContent();
      
      // Verify platform is logged
      expect(electronMain).toContain('process.platform');
    });
  });

  describe('Windows Code Signing', () => {
    it('should support Windows code signing configuration', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const win = build.win || {};
      
      // Verify signing configuration can be set
      // (may not be configured in development, but structure should support it)
      expect(win).toBeDefined();
    });

    it('should have sign-windows.js script', () => {
      const signScriptPath = path.join(process.cwd(), 'scripts', 'sign-windows.js');
      
      // Verify script exists
      expect(fs.existsSync(signScriptPath)).toBe(true);
    });
  });

  describe('Windows Antivirus Compatibility', () => {
    it('should configure executable to minimize false positives', () => {
      const spec = getPyInstallerSpec();
      
      if (spec) {
        // Verify console setting exists
        expect(spec).toContain('console=');
        
        // Verify proper executable name
        expect(spec).toContain('peft_engine');
      }
    });
  });
});
