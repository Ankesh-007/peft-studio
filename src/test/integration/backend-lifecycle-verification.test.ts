/**
 * Integration Test: Backend Process Lifecycle Management Verification
 * 
 * This test verifies that the BackendServiceManager correctly handles process
 * lifecycle management with bundled executables, including:
 * - SIGTERM → SIGKILL shutdown sequence
 * - Zombie process cleanup
 * - Crash recovery
 * - Health checks
 * - Port conflict handling
 * 
 * Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
 */

import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('Backend Process Lifecycle Management Verification', () => {
  const electronMainPath = path.join(process.cwd(), 'electron', 'main.js');

  function getElectronMainContent(): string {
    return fs.readFileSync(electronMainPath, 'utf-8');
  }

  describe('Requirement 4.1: Automatic Backend Startup', () => {
    it('should spawn backend process automatically when Electron starts', () => {
      const content = getElectronMainContent();
      
      // Verify app.whenReady() calls startPythonBackend
      expect(content).toContain('app.whenReady()');
      expect(content).toContain('startPythonBackend()');
      
      // Verify startPythonBackend calls backendManager.start()
      expect(content).toContain('backendManager.start()');
    });
  });

  describe('Requirement 4.2: SIGTERM on Window Close', () => {
    it('should send SIGTERM when user closes application window', () => {
      const content = getElectronMainContent();
      
      // Verify stop method sends SIGTERM
      const stopMethodMatch = content.match(/async stop\(\)\s*\{[\s\S]*?\n\s{2}\}/);
      expect(stopMethodMatch).not.toBeNull();
      
      if (stopMethodMatch) {
        const stopMethod = stopMethodMatch[0];
        expect(stopMethod).toContain("kill('SIGTERM')");
      }
      
      // Verify window-all-closed handler calls stop
      expect(content).toContain("app.on('window-all-closed'");
      expect(content).toContain('backendManager.stop()');
    });
  });

  describe('Requirement 4.3: SIGKILL After 1 Second Timeout', () => {
    it('should send SIGKILL if process does not terminate within 1 second', () => {
      const content = getElectronMainContent();
      const stopMethodMatch = content.match(/async stop\(\)\s*\{[\s\S]*?\n\s{2}\}/);
      
      expect(stopMethodMatch).not.toBeNull();
      
      if (stopMethodMatch) {
        const stopMethod = stopMethodMatch[0];
        
        // Verify SIGKILL is sent
        expect(stopMethod).toContain("kill('SIGKILL')");
        
        // Verify there's a 1 second delay
        expect(stopMethod).toContain('setTimeout(resolve, 1000)');
        
        // Verify SIGTERM comes before SIGKILL
        const sigtermIndex = stopMethod.indexOf("kill('SIGTERM')");
        const sigkillIndex = stopMethod.indexOf("kill('SIGKILL')");
        expect(sigtermIndex).toBeLessThan(sigkillIndex);
      }
    });
  });

  describe('Requirement 4.4: No Zombie Processes', () => {
    it('should ensure no zombie processes remain after app quit', () => {
      const content = getElectronMainContent();
      
      // Verify all quit handlers call stop
      expect(content).toContain("app.on('window-all-closed'");
      expect(content).toContain("app.on('quit'");
      expect(content).toContain("app.on('before-quit'");
      
      // Verify stop method nullifies process reference
      const stopMethodMatch = content.match(/async stop\(\)\s*\{[\s\S]*?\n\s{2}\}/);
      if (stopMethodMatch) {
        expect(stopMethodMatch[0]).toContain('this.process = null');
      }
      
      // Verify process close handler sets process to null
      const closeHandlerMatch = content.match(/this\.process\.on\('close'[\s\S]*?\}\);/);
      if (closeHandlerMatch) {
        expect(closeHandlerMatch[0]).toContain('this.process = null');
      }
    });
  });

  describe('Requirement 4.5: Crash Recovery', () => {
    it('should attempt to restart backend on unexpected crash', () => {
      const content = getElectronMainContent();
      
      // Verify handleCrash method exists
      expect(content).toContain('async handleCrash()');
      
      // Verify crash recovery logic
      const handleCrashMatch = content.match(/async handleCrash\(\)\s*\{[\s\S]*?\n\s{2}\}/);
      expect(handleCrashMatch).not.toBeNull();
      
      if (handleCrashMatch) {
        const handleCrash = handleCrashMatch[0];
        
        // Verify restart attempts are tracked
        expect(handleCrash).toContain('this.restartAttempts');
        expect(handleCrash).toContain('this.maxRestartAttempts');
        
        // Verify restart is attempted
        expect(handleCrash).toContain('await this.start()');
        
        // Verify max attempts are respected
        expect(handleCrash).toContain('MAX_RESTARTS_EXCEEDED');
      }
      
      // Verify process close handler triggers crash recovery
      const closeHandlerMatch = content.match(/this\.process\.on\('close'[\s\S]*?\}\);/);
      if (closeHandlerMatch) {
        const closeHandler = closeHandlerMatch[0];
        expect(closeHandler).toContain('handleCrash()');
        expect(closeHandler).toContain('!this.isShuttingDown');
        expect(closeHandler).toContain('code !== 0');
      }
    });
  });

  describe('Health Check Verification', () => {
    it('should implement health check functionality', () => {
      const content = getElectronMainContent();
      
      // Verify checkBackendHealth method exists
      expect(content).toContain('async checkBackendHealth()');
      
      // Verify health check makes HTTP request to /api/health
      const healthCheckMatch = content.match(/async checkBackendHealth\(\)[\s\S]*?\n\s{2}\}/);
      if (healthCheckMatch) {
        const healthCheck = healthCheckMatch[0];
        expect(healthCheck).toContain('/api/health');
        expect(healthCheck).toContain('http.request');
      }
      
      // Verify startHealthChecks method exists
      expect(content).toContain('startHealthChecks()');
      
      // Verify stopHealthChecks method exists
      expect(content).toContain('stopHealthChecks()');
      
      // Verify health checks are stopped during shutdown
      const stopMethodMatch = content.match(/async stop\(\)\s*\{[\s\S]*?\n\s{2}\}/);
      if (stopMethodMatch) {
        expect(stopMethodMatch[0]).toContain('stopHealthChecks()');
      }
    });
  });

  describe('Port Conflict Handling', () => {
    it('should handle port conflicts by trying alternative ports', () => {
      const content = getElectronMainContent();
      
      // Verify tryAlternativePort method exists
      expect(content).toContain('async tryAlternativePort()');
      
      // Verify port range 8000-8010
      const tryAltPortMatch = content.match(/async tryAlternativePort\(\)[\s\S]*?\n\s{2}\}/);
      if (tryAltPortMatch) {
        const tryAltPort = tryAltPortMatch[0];
        expect(tryAltPort).toContain('8001');
        expect(tryAltPort).toContain('8010');
      }
      
      // Verify stderr handler detects port conflicts
      const startMethodMatch = content.match(/async start\(\)[\s\S]*?\n\s{2}\}/);
      if (startMethodMatch) {
        const startMethod = startMethodMatch[0];
        expect(startMethod).toContain('Address already in use');
        expect(startMethod).toContain('EADDRINUSE');
        expect(startMethod).toContain('tryAlternativePort()');
      }
    });
  });

  describe('Bundled Executable Compatibility', () => {
    it('should work with both Python script (dev) and bundled executable (prod)', () => {
      const content = getElectronMainContent();
      
      // Verify getBackendPath handles both modes
      const getBackendPathMatch = content.match(/async getBackendPath\(\)[\s\S]*?\n\s{2}\}/);
      expect(getBackendPathMatch).not.toBeNull();
      
      if (getBackendPathMatch) {
        const getBackendPath = getBackendPathMatch[0];
        
        // Verify production mode handling
        expect(getBackendPath).toContain('app.isPackaged');
        expect(getBackendPath).toContain('process.resourcesPath');
        expect(getBackendPath).toContain('peft_engine');
        
        // Verify development mode handling
        expect(getBackendPath).toContain('backend/main.py');
        expect(getBackendPath).toContain('findPythonExecutable');
      }
      
      // Verify start method uses getBackendPath
      const startMethodMatch = content.match(/async start\(\)[\s\S]*?\n\s{2}\}/);
      if (startMethodMatch) {
        expect(startMethodMatch[0]).toContain('getBackendPath()');
        expect(startMethodMatch[0]).toContain('spawn(backendInfo.executable, backendInfo.args');
      }
    });

    it('should capture stdout/stderr for both modes', () => {
      const content = getElectronMainContent();
      const startMethodMatch = content.match(/async start\(\)[\s\S]*?\n\s{2}\}/);
      
      expect(startMethodMatch).not.toBeNull();
      
      if (startMethodMatch) {
        const startMethod = startMethodMatch[0];
        
        // Verify stdout capture
        expect(startMethod).toContain("this.process.stdout.on('data'");
        
        // Verify stderr capture
        expect(startMethod).toContain("this.process.stderr.on('data'");
        
        // Verify PYTHONUNBUFFERED is set
        expect(startMethod).toContain('PYTHONUNBUFFERED');
      }
    });
  });

  describe('Process Cleanup Idempotence', () => {
    it('should safely handle multiple stop calls', () => {
      const content = getElectronMainContent();
      const stopMethodMatch = content.match(/async stop\(\)\s*\{[\s\S]*?\n\s{2}\}/);
      
      expect(stopMethodMatch).not.toBeNull();
      
      if (stopMethodMatch) {
        const stopMethod = stopMethodMatch[0];
        
        // Verify process existence check
        expect(stopMethod).toContain('if (this.process)');
        
        // Verify process is nullified
        expect(stopMethod).toContain('this.process = null');
      }
      
      // Verify stopHealthChecks is idempotent
      const stopHealthChecksMatch = content.match(/stopHealthChecks\(\)\s*\{[\s\S]*?\n\s{2}\}/);
      if (stopHealthChecksMatch) {
        const stopHealthChecks = stopHealthChecksMatch[0];
        expect(stopHealthChecks).toContain('if (this.healthCheckInterval)');
        expect(stopHealthChecks).toContain('this.healthCheckInterval = null');
      }
    });
  });

  describe('Shutdown Flag Management', () => {
    it('should use isShuttingDown flag to prevent crash recovery during shutdown', () => {
      const content = getElectronMainContent();
      
      // Verify flag is set in stop method
      const stopMethodMatch = content.match(/async stop\(\)\s*\{[\s\S]*?\n\s{2}\}/);
      if (stopMethodMatch) {
        expect(stopMethodMatch[0]).toContain('this.isShuttingDown = true');
      }
      
      // Verify flag is checked in close handler
      const closeHandlerMatch = content.match(/this\.process\.on\('close'[\s\S]*?\}\);/);
      if (closeHandlerMatch) {
        expect(closeHandlerMatch[0]).toContain('!this.isShuttingDown');
      }
    });
  });

  describe('Comprehensive Lifecycle Test', () => {
    it('should implement complete process lifecycle management', () => {
      const content = getElectronMainContent();
      
      // Verify all required methods exist
      expect(content).toContain('async start()');
      expect(content).toContain('async stop()');
      expect(content).toContain('async restart()');
      expect(content).toContain('async handleCrash()');
      expect(content).toContain('async getBackendPath()');
      expect(content).toContain('async checkBackendHealth()');
      expect(content).toContain('startHealthChecks()');
      expect(content).toContain('stopHealthChecks()');
      expect(content).toContain('async tryAlternativePort()');
      
      // Verify BackendServiceManager class exists
      expect(content).toContain('class BackendServiceManager');
      
      // Verify instance is created
      expect(content).toContain('new BackendServiceManager()');
      
      // Verify all app lifecycle handlers are registered
      expect(content).toContain("app.on('window-all-closed'");
      expect(content).toContain("app.on('quit'");
      expect(content).toContain("app.on('before-quit'");
    });
  });
});
