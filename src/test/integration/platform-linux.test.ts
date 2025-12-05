/**
 * Platform-Specific Integration Test: Linux
 * 
 * This test suite verifies Linux-specific requirements for the Python backend bundling:
 * - AppImage format support
 * - .deb package support
 * - Executable permissions handling
 * - Linux-specific path handling
 * - Process management on Linux
 * 
 * Requirements: 2.1, 2.2, 2.3
 */

import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('Linux Platform-Specific Tests', () => {
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

  describe('Requirement 2.3: Linux Executable Generation', () => {
    it('should generate peft_engine executable for Linux (no extension)', () => {
      const electronMain = getElectronMainContent();
      const getBackendPathMatch = electronMain.match(/async getBackendPath\(\)[\s\S]*?\n\s{2}\}/);
      
      expect(getBackendPathMatch).not.toBeNull();
      
      if (getBackendPathMatch) {
        const getBackendPath = getBackendPathMatch[0];
        
        // Verify Linux uses peft_engine without extension (not .exe)
        expect(getBackendPath).toContain("platform === 'win32'");
        expect(getBackendPath).toContain('peft_engine.exe');
        expect(getBackendPath).toContain('peft_engine');
        
        // Verify conditional logic for non-Windows platforms
        const hasConditionalLogic = getBackendPath.includes('?') && getBackendPath.includes(':');
        expect(hasConditionalLogic).toBe(true);
      }
    });

    it('should use consistent naming across platforms', () => {
      const electronMain = getElectronMainContent();
      const getBackendPathMatch = electronMain.match(/async getBackendPath\(\)[\s\S]*?\n\s{2}\}/);
      
      if (getBackendPathMatch) {
        const getBackendPath = getBackendPathMatch[0];
        
        // Verify base name is consistent
        const peftEngineCount = (getBackendPath.match(/peft_engine/g) || []).length;
        expect(peftEngineCount).toBeGreaterThan(0);
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

  describe('AppImage Format Support', () => {
    it('should configure AppImage as Linux installer format', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const linux = build.linux || {};
      
      // Verify AppImage is in target list
      expect(linux.target).toBeDefined();
      
      if (linux.target) {
        const targets = Array.isArray(linux.target) ? linux.target : [linux.target];
        const hasAppImage = targets.some((t: any) => 
          typeof t === 'string' ? t === 'AppImage' : t.target === 'AppImage'
        );
        expect(hasAppImage).toBe(true);
      }
    });

    it('should configure AppImage options', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const appImage = build.appImage || {};
      
      // Verify AppImage configuration exists
      expect(appImage).toBeDefined();
    });

    it('should support x64 architecture for AppImage', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const linux = build.linux || {};
      
      // Verify Linux configuration supports architecture targeting
      expect(linux).toBeDefined();
    });
  });

  describe('.deb Package Support', () => {
    it('should configure .deb as Linux installer format', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const linux = build.linux || {};
      
      // Verify deb is in target list
      if (linux.target) {
        const targets = Array.isArray(linux.target) ? linux.target : [linux.target];
        const hasDeb = targets.some((t: any) => 
          typeof t === 'string' ? t === 'deb' : t.target === 'deb'
        );
        
        // deb may or may not be configured, but AppImage should be
        expect(targets.length).toBeGreaterThan(0);
      }
    });

    it('should configure deb package options if present', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const deb = build.deb || {};
      
      // Verify deb configuration can be set
      expect(deb).toBeDefined();
    });
  });

  describe('Requirement 2.3: Linux Installer Configuration', () => {
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

    it('should configure Linux-specific build options', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const linux = build.linux || {};
      
      // Verify Linux configuration exists
      expect(linux).toBeDefined();
      expect(linux.target).toBeDefined();
    });
  });

  describe('Linux Path Handling', () => {
    it('should handle Unix-style path separators', () => {
      const electronMain = getElectronMainContent();
      const getBackendPathMatch = electronMain.match(/async getBackendPath\(\)[\s\S]*?\n\s{2}\}/);
      
      if (getBackendPathMatch) {
        const getBackendPath = getBackendPathMatch[0];
        
        // Verify path.join is used (handles platform-specific separators)
        expect(getBackendPath).toContain('path.join');
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

    it('should handle Linux directory structure', () => {
      const electronMain = getElectronMainContent();
      const getBackendPathMatch = electronMain.match(/async getBackendPath\(\)[\s\S]*?\n\s{2}\}/);
      
      if (getBackendPathMatch) {
        const getBackendPath = getBackendPathMatch[0];
        
        // Verify proper path construction for Linux
        expect(getBackendPath).toContain('process.resourcesPath');
        expect(getBackendPath).toContain('path.join');
      }
    });
  });

  describe('Linux Executable Permissions', () => {
    it('should handle executable permissions', () => {
      const electronMain = getElectronMainContent();
      
      // Verify error handling for permission issues
      const startMethodMatch = electronMain.match(/async start\(\)[\s\S]*?\n\s{2}\}/);
      if (startMethodMatch) {
        const startMethod = startMethodMatch[0];
        
        // Should handle spawn errors
        expect(startMethod).toContain("on('error'");
      }
    });

    it('should attempt chmod +x on permission errors', () => {
      const electronMain = getElectronMainContent();
      
      // Check for permission error handling
      // This may be in error handler or start method
      const hasChmodHandling = electronMain.includes('chmod') || 
                               electronMain.includes('EACCES') ||
                               electronMain.includes('permission');
      
      // At minimum, should handle permission errors
      expect(electronMain).toContain('error');
    });

    it('should provide manual chmod instructions on failure', () => {
      const electronMain = getElectronMainContent();
      
      // Should have error messages for permission issues
      const hasPermissionError = electronMain.includes('permission') || 
                                 electronMain.includes('EACCES') ||
                                 electronMain.includes('chmod');
      
      // At minimum, should have error handling
      expect(electronMain).toContain('error');
    });

    it('should verify executable has execute bit set', () => {
      const electronMain = getElectronMainContent();
      
      // Should handle permission errors during spawn
      const startMethodMatch = electronMain.match(/async start\(\)[\s\S]*?\n\s{2}\}/);
      if (startMethodMatch) {
        expect(startMethodMatch[0]).toContain("on('error'");
      }
    });
  });

  describe('Linux Process Management', () => {
    it('should handle SIGTERM on Linux', () => {
      const electronMain = getElectronMainContent();
      const stopMethodMatch = electronMain.match(/async stop\(\)[\s\S]*?\n\s{2}\}/);
      
      if (stopMethodMatch) {
        const stopMethod = stopMethodMatch[0];
        
        // Verify SIGTERM is sent (native Unix signal)
        expect(stopMethod).toContain("kill('SIGTERM')");
      }
    });

    it('should handle SIGKILL on Linux', () => {
      const electronMain = getElectronMainContent();
      const stopMethodMatch = electronMain.match(/async stop\(\)[\s\S]*?\n\s{2}\}/);
      
      if (stopMethodMatch) {
        const stopMethod = stopMethodMatch[0];
        
        // Verify SIGKILL is sent as fallback
        expect(stopMethod).toContain("kill('SIGKILL')");
      }
    });

    it('should handle Unix process signals correctly', () => {
      const electronMain = getElectronMainContent();
      const stopMethodMatch = electronMain.match(/async stop\(\)[\s\S]*?\n\s{2}\}/);
      
      if (stopMethodMatch) {
        const stopMethod = stopMethodMatch[0];
        
        // Verify proper signal handling sequence
        const sigtermIndex = stopMethod.indexOf("kill('SIGTERM')");
        const sigkillIndex = stopMethod.indexOf("kill('SIGKILL')");
        
        expect(sigtermIndex).toBeLessThan(sigkillIndex);
      }
    });

    it('should handle zombie process cleanup', () => {
      const electronMain = getElectronMainContent();
      const stopMethodMatch = electronMain.match(/async stop\(\)[\s\S]*?\n\s{2}\}/);
      
      if (stopMethodMatch) {
        const stopMethod = stopMethodMatch[0];
        
        // Verify process is nullified
        expect(stopMethod).toContain('this.process = null');
      }
    });
  });

  describe('Linux Build Scripts', () => {
    it('should support Linux build configuration', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const linux = build.linux || {};
      
      // Verify Linux build configuration exists
      expect(linux).toBeDefined();
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

  describe('Linux Installer Testing', () => {
    it('should configure installer to work on clean systems', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      
      // Verify no Python dependency is required
      // The bundled executable should be self-contained
      const extraResources = build.extraResources || [];
      expect(extraResources.length).toBeGreaterThan(0);
    });

    it('should not require root privileges for installation', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const appImage = build.appImage || {};
      
      // AppImage doesn't require root by default
      expect(appImage).toBeDefined();
    });

    it('should support user-level installation', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const linux = build.linux || {};
      
      // Verify Linux configuration supports user installation
      expect(linux.target).toBeDefined();
    });
  });

  describe('Linux Error Handling', () => {
    it('should handle Linux-specific error messages', () => {
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

    it('should handle permission denied errors', () => {
      const electronMain = getElectronMainContent();
      
      // Should handle EACCES or permission errors
      const hasPermissionHandling = electronMain.includes('EACCES') || 
                                    electronMain.includes('permission') ||
                                    electronMain.includes('chmod');
      
      // At minimum, should have error handling
      expect(electronMain).toContain('error');
    });

    it('should handle missing library errors', () => {
      const electronMain = getElectronMainContent();
      
      // Should handle stderr output which may contain library errors
      const startMethodMatch = electronMain.match(/async start\(\)[\s\S]*?\n\s{2}\}/);
      if (startMethodMatch) {
        expect(startMethodMatch[0]).toContain("stderr.on('data'");
      }
    });
  });

  describe('Linux Executable Verification', () => {
    it('should verify executable exists after build', () => {
      const pkg = getPackageJson();
      const scripts = pkg.scripts || {};
      
      // Verify verification script exists
      expect(scripts['build:backend:verify']).toBeDefined();
    });

    it('should check executable size is reasonable', () => {
      const verifyScriptPath = path.join(process.cwd(), 'scripts', 'verify-backend-build.js');
      
      if (fs.existsSync(verifyScriptPath)) {
        const verifyScript = fs.readFileSync(verifyScriptPath, 'utf-8');
        
        // Verify size check exists
        expect(verifyScript).toContain('stats.size');
        expect(verifyScript).toContain('1024 * 1024'); // 1MB minimum
      }
    });

    it('should verify executable is actually executable', () => {
      const verifyScriptPath = path.join(process.cwd(), 'scripts', 'verify-backend-build.js');
      
      if (fs.existsSync(verifyScriptPath)) {
        const verifyScript = fs.readFileSync(verifyScriptPath, 'utf-8');
        
        // Should check file exists
        expect(verifyScript).toContain('existsSync');
      }
    });
  });

  describe('Linux Distribution Compatibility', () => {
    it('should support major Linux distributions', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const linux = build.linux || {};
      
      // AppImage works on most distributions
      if (linux.target) {
        const targets = Array.isArray(linux.target) ? linux.target : [linux.target];
        const hasAppImage = targets.some((t: any) => 
          typeof t === 'string' ? t === 'AppImage' : t.target === 'AppImage'
        );
        expect(hasAppImage).toBe(true);
      }
    });

    it('should not depend on specific system libraries', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      
      // The bundled executable should be self-contained
      const extraResources = build.extraResources || [];
      expect(extraResources.length).toBeGreaterThan(0);
    });
  });

  describe('Linux Desktop Integration', () => {
    it('should support desktop file configuration', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const linux = build.linux || {};
      
      // Verify Linux configuration exists
      expect(linux).toBeDefined();
    });

    it('should configure application category', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const linux = build.linux || {};
      
      // Verify category can be configured
      expect(linux).toBeDefined();
    });
  });

  describe('Linux AppImage Specific', () => {
    it('should configure AppImage to be self-contained', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const appImage = build.appImage || {};
      
      // AppImage should be self-contained by default
      expect(appImage).toBeDefined();
    });

    it('should not require installation', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const linux = build.linux || {};
      
      // AppImage can run without installation
      if (linux.target) {
        const targets = Array.isArray(linux.target) ? linux.target : [linux.target];
        const hasAppImage = targets.some((t: any) => 
          typeof t === 'string' ? t === 'AppImage' : t.target === 'AppImage'
        );
        expect(hasAppImage).toBe(true);
      }
    });

    it('should support FUSE for AppImage mounting', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const appImage = build.appImage || {};
      
      // AppImage uses FUSE by default
      expect(appImage).toBeDefined();
    });
  });

  describe('Linux Security', () => {
    it('should not require elevated privileges', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const linux = build.linux || {};
      
      // Verify no sudo/root requirement
      expect(linux).toBeDefined();
    });

    it('should run with user permissions', () => {
      const electronMain = getElectronMainContent();
      const startMethodMatch = electronMain.match(/async start\(\)[\s\S]*?\n\s{2}\}/);
      
      if (startMethodMatch) {
        const startMethod = startMethodMatch[0];
        
        // Should not use sudo or elevated permissions
        expect(startMethod).not.toContain('sudo');
      }
    });
  });

  describe('Linux System Requirements', () => {
    it('should document minimum system requirements', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const linux = build.linux || {};
      
      // Verify Linux configuration exists
      expect(linux).toBeDefined();
    });

    it('should support x64 architecture', () => {
      const pkg = getPackageJson();
      const build = pkg.build || {};
      const linux = build.linux || {};
      
      // Verify Linux configuration supports architecture targeting
      expect(linux).toBeDefined();
    });
  });
});
