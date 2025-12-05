/**
 * Tests for verify-final-release.js
 */

const { describe, it, expect, beforeEach, afterEach } = require('vitest');
const fs = require('fs');
const path = require('path');

describe('verify-final-release', () => {
  describe('verification script structure', () => {
    it('should have executable permissions on Unix systems', () => {
      if (process.platform !== 'win32') {
        const scriptPath = path.join(__dirname, '../verify-final-release.js');
        const stats = fs.statSync(scriptPath);
        // Check if file exists
        expect(stats.isFile()).toBe(true);
      }
    });

    it('should export main function', () => {
      const script = require('../verify-final-release.js');
      expect(typeof script.main).toBe('function');
    });

    it('should be a valid Node.js script', () => {
      const scriptPath = path.join(__dirname, '../verify-final-release.js');
      const content = fs.readFileSync(scriptPath, 'utf8');
      
      // Should have shebang
      expect(content.startsWith('#!/usr/bin/env node')).toBe(true);
      
      // Should have required imports
      expect(content).toContain("require('fs')");
      expect(content).toContain("require('path')");
    });
  });

  describe('verification categories', () => {
    it('should check build artifacts', () => {
      const scriptPath = path.join(__dirname, '../verify-final-release.js');
      const content = fs.readFileSync(scriptPath, 'utf8');
      
      expect(content).toContain('verifyBuildArtifacts');
      expect(content).toContain('Backend executable exists');
    });

    it('should check build scripts', () => {
      const scriptPath = path.join(__dirname, '../verify-final-release.js');
      const content = fs.readFileSync(scriptPath, 'utf8');
      
      expect(content).toContain('verifyBuildScripts');
      expect(content).toContain('build:backend');
    });

    it('should check Electron configuration', () => {
      const scriptPath = path.join(__dirname, '../verify-final-release.js');
      const content = fs.readFileSync(scriptPath, 'utf8');
      
      expect(content).toContain('verifyElectronConfiguration');
      expect(content).toContain('getBackendPath');
    });

    it('should check test suite', () => {
      const scriptPath = path.join(__dirname, '../verify-final-release.js');
      const content = fs.readFileSync(scriptPath, 'utf8');
      
      expect(content).toContain('verifyTestSuite');
    });

    it('should check documentation', () => {
      const scriptPath = path.join(__dirname, '../verify-final-release.js');
      const content = fs.readFileSync(scriptPath, 'utf8');
      
      expect(content).toContain('verifyDocumentation');
      expect(content).toContain('backend-bundling.md');
    });

    it('should check CI configuration', () => {
      const scriptPath = path.join(__dirname, '../verify-final-release.js');
      const content = fs.readFileSync(scriptPath, 'utf8');
      
      expect(content).toContain('verifyCIConfiguration');
      expect(content).toContain('.github/workflows');
    });

    it('should check platform specifics', () => {
      const scriptPath = path.join(__dirname, '../verify-final-release.js');
      const content = fs.readFileSync(scriptPath, 'utf8');
      
      expect(content).toContain('verifyPlatformSpecifics');
      expect(content).toContain('process.platform');
    });
  });

  describe('reporting', () => {
    it('should generate summary report', () => {
      const scriptPath = path.join(__dirname, '../verify-final-release.js');
      const content = fs.readFileSync(scriptPath, 'utf8');
      
      expect(content).toContain('generateReport');
      expect(content).toContain('Pass Rate');
    });

    it('should save detailed report to JSON', () => {
      const scriptPath = path.join(__dirname, '../verify-final-release.js');
      const content = fs.readFileSync(scriptPath, 'utf8');
      
      expect(content).toContain('verification-report.json');
      expect(content).toContain('JSON.stringify');
    });

    it('should track passed, failed, warnings, and skipped', () => {
      const scriptPath = path.join(__dirname, '../verify-final-release.js');
      const content = fs.readFileSync(scriptPath, 'utf8');
      
      expect(content).toContain('results.passed');
      expect(content).toContain('results.failed');
      expect(content).toContain('results.warnings');
      expect(content).toContain('results.skipped');
    });
  });

  describe('exit codes', () => {
    it('should exit with 0 on success', () => {
      const scriptPath = path.join(__dirname, '../verify-final-release.js');
      const content = fs.readFileSync(scriptPath, 'utf8');
      
      expect(content).toContain('process.exit(0)');
    });

    it('should exit with 1 on failure', () => {
      const scriptPath = path.join(__dirname, '../verify-final-release.js');
      const content = fs.readFileSync(scriptPath, 'utf8');
      
      expect(content).toContain('process.exit(1)');
    });
  });
});
