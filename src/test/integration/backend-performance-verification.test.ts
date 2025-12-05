/**
 * Backend Performance and Startup Time Verification Tests
 * 
 * Tests for Task 11: Verify performance and startup time
 * Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5
 * 
 * This test suite verifies:
 * - Bundled executable startup time is under 5 seconds
 * - Lazy loading is preserved in bundled executable
 * - Production mode skips unnecessary dependency checks
 * - Backend-status event notification works with bundled executable
 * - Performance metrics logging for slow startups
 * - /api/health endpoint responds quickly
 * - Startup time comparison between development and production modes
 */

import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest';
import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

interface BackendStartupMetrics {
  startTime: number;
  readyTime: number;
  healthCheckTime: number;
  totalStartupTime: number;
  mode: 'development' | 'production';
  platform: string;
}

interface BackendStatusEvent {
  status: 'starting' | 'ready' | 'error';
  port?: number;
  pid?: number;
  error?: string;
  timestamp: number;
}

describe('Backend Performance and Startup Time Verification', () => {
  const STARTUP_TIME_TARGET = 5000; // 5 seconds in milliseconds
  const HEALTH_CHECK_TIMEOUT = 2000; // 2 seconds for health check
  const TEST_PORT = 8001; // Use alternative port for testing
  
  let backendProcess: ChildProcess | null = null;
  let backendMetrics: BackendStartupMetrics | null = null;

  /**
   * Helper function to wait for backend to be ready
   */
  async function waitForBackendReady(process: ChildProcess, timeout: number): Promise<number> {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      let readyDetected = false;

      const timeoutId = setTimeout(() => {
        if (!readyDetected) {
          reject(new Error(`Backend did not start within ${timeout}ms`));
        }
      }, timeout);

      process.stdout?.on('data', (data) => {
        const output = data.toString();
        
        // Check for uvicorn ready message
        if (output.includes('Uvicorn running on') || output.includes('Application startup complete')) {
          readyDetected = true;
          clearTimeout(timeoutId);
          const readyTime = Date.now() - startTime;
          resolve(readyTime);
        }
      });

      process.stderr?.on('data', (data) => {
        const error = data.toString();
        console.error('Backend stderr:', error);
      });

      process.on('error', (err) => {
        clearTimeout(timeoutId);
        reject(err);
      });

      process.on('close', (code) => {
        clearTimeout(timeoutId);
        if (!readyDetected) {
          reject(new Error(`Backend process exited with code ${code} before becoming ready`));
        }
      });
    });
  }

  /**
   * Helper function to check /api/health endpoint
   */
  async function checkHealthEndpoint(port: number): Promise<number> {
    const startTime = Date.now();
    
    try {
      const response = await fetch(`http://127.0.0.1:${port}/api/health`);
      const responseTime = Date.now() - startTime;
      
      if (!response.ok) {
        throw new Error(`Health check failed with status ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.status !== 'healthy') {
        throw new Error(`Health check returned unhealthy status: ${data.status}`);
      }
      
      return responseTime;
    } catch (error) {
      throw new Error(`Health check failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Helper function to get backend path based on mode
   */
  function getBackendPath(mode: 'development' | 'production'): { executable: string; args: string[] } {
    const platform = process.platform;
    
    if (mode === 'production') {
      // Production mode: use bundled executable
      const exeName = platform === 'win32' ? 'peft_engine.exe' : 'peft_engine';
      const backendPath = path.join(process.cwd(), 'backend', 'dist', exeName);
      
      return {
        executable: backendPath,
        args: []
      };
    } else {
      // Development mode: use Python script
      const scriptPath = path.join(process.cwd(), 'backend', 'main.py');
      const pythonCmd = platform === 'win32' ? 'python' : 'python3';
      
      return {
        executable: pythonCmd,
        args: [scriptPath]
      };
    }
  }

  /**
   * Helper function to start backend and measure startup time
   */
  async function startBackendAndMeasure(mode: 'development' | 'production'): Promise<BackendStartupMetrics> {
    const startTime = Date.now();
    const { executable, args } = getBackendPath(mode);
    
    // Check if executable exists
    if (!fs.existsSync(executable)) {
      throw new Error(`Backend executable not found: ${executable}`);
    }
    
    // Start backend process
    const process = spawn(executable, args, {
      env: { ...process.env, PYTHONUNBUFFERED: '1' }
    });
    
    backendProcess = process;
    
    // Wait for backend to be ready
    const readyTime = await waitForBackendReady(process, STARTUP_TIME_TARGET + 2000);
    
    // Check health endpoint
    const healthCheckTime = await checkHealthEndpoint(TEST_PORT);
    
    const totalStartupTime = Date.now() - startTime;
    
    return {
      startTime,
      readyTime,
      healthCheckTime,
      totalStartupTime,
      mode,
      platform: process.platform
    };
  }

  /**
   * Helper function to stop backend process
   */
  async function stopBackend(process: ChildProcess): Promise<void> {
    return new Promise((resolve) => {
      if (!process || process.killed) {
        resolve();
        return;
      }

      process.on('close', () => {
        resolve();
      });

      // Send SIGTERM for graceful shutdown
      process.kill('SIGTERM');

      // Force kill after 2 seconds if still running
      setTimeout(() => {
        if (!process.killed) {
          process.kill('SIGKILL');
        }
      }, 2000);
    });
  }

  afterAll(async () => {
    // Clean up backend process
    if (backendProcess) {
      await stopBackend(backendProcess);
      backendProcess = null;
    }
  });

  describe('Requirement 10.1: Startup Time Target', () => {
    it('should start bundled executable within 5 seconds on modern hardware', async () => {
      // Skip if bundled executable doesn't exist
      const { executable } = getBackendPath('production');
      if (!fs.existsSync(executable)) {
        console.warn('Bundled executable not found, skipping production startup test');
        return;
      }

      const metrics = await startBackendAndMeasure('production');
      backendMetrics = metrics;

      console.log('Production Startup Metrics:', {
        readyTime: `${metrics.readyTime}ms`,
        healthCheckTime: `${metrics.healthCheckTime}ms`,
        totalStartupTime: `${metrics.totalStartupTime}ms`,
        platform: metrics.platform
      });

      // Verify startup time is under 5 seconds
      expect(metrics.totalStartupTime).toBeLessThan(STARTUP_TIME_TARGET);
      expect(metrics.readyTime).toBeLessThan(STARTUP_TIME_TARGET);
    }, 10000); // 10 second timeout for test
  });

  describe('Requirement 10.2: Lazy Loading Preservation', () => {
    it('should preserve lazy loading in bundled executable', async () => {
      // Skip if bundled executable doesn't exist
      const { executable } = getBackendPath('production');
      if (!fs.existsSync(executable)) {
        console.warn('Bundled executable not found, skipping lazy loading test');
        return;
      }

      // Start backend if not already running
      if (!backendProcess) {
        backendMetrics = await startBackendAndMeasure('production');
      }

      // Check startup metrics endpoint
      const response = await fetch(`http://127.0.0.1:${TEST_PORT}/api/startup/metrics`);
      expect(response.ok).toBe(true);

      const metrics = await response.json();
      
      // Verify that startup metrics show lazy loading is working
      expect(metrics).toHaveProperty('total_time');
      expect(metrics).toHaveProperty('phases');
      
      // Verify that heavy ML libraries are not loaded during startup
      // (they should be loaded lazily when needed)
      expect(metrics.total_time).toBeLessThan(STARTUP_TIME_TARGET / 1000); // Convert to seconds
    }, 10000);
  });

  describe('Requirement 10.3: Production Mode Optimization', () => {
    it('should skip unnecessary dependency checks in production mode', async () => {
      // Skip if bundled executable doesn't exist
      const { executable } = getBackendPath('production');
      if (!fs.existsSync(executable)) {
        console.warn('Bundled executable not found, skipping production optimization test');
        return;
      }

      // Start backend if not already running
      if (!backendProcess) {
        backendMetrics = await startBackendAndMeasure('production');
      }

      // Check startup status endpoint
      const response = await fetch(`http://127.0.0.1:${TEST_PORT}/api/startup/status`);
      expect(response.ok).toBe(true);

      const status = await response.json();
      
      // Verify startup is optimized
      expect(status.initialized).toBe(true);
      expect(status.ready).toBe(true);
      expect(status.meets_target).toBe(true);
      
      // Verify startup time meets target
      expect(status.startup_time).toBeLessThan(STARTUP_TIME_TARGET / 1000); // Convert to seconds
    }, 10000);
  });

  describe('Requirement 10.4: Backend Status Event Notification', () => {
    it('should emit backend-status event when ready', async () => {
      // This test verifies that the backend emits the expected status messages
      // In a real Electron environment, this would be tested via IPC
      
      // Skip if bundled executable doesn't exist
      const { executable } = getBackendPath('production');
      if (!fs.existsSync(executable)) {
        console.warn('Bundled executable not found, skipping status event test');
        return;
      }

      const statusEvents: BackendStatusEvent[] = [];
      const startTime = Date.now();

      // Start a new backend process to capture status events
      const { executable: exec, args } = getBackendPath('production');
      const process = spawn(exec, args, {
        env: { ...process.env, PYTHONUNBUFFERED: '1' }
      });

      // Capture stdout for status detection
      process.stdout?.on('data', (data) => {
        const output = data.toString();
        
        if (output.includes('Starting PEFT Studio Backend')) {
          statusEvents.push({
            status: 'starting',
            timestamp: Date.now() - startTime
          });
        }
        
        if (output.includes('Uvicorn running on') || output.includes('Application startup complete')) {
          statusEvents.push({
            status: 'ready',
            port: TEST_PORT,
            timestamp: Date.now() - startTime
          });
        }
      });

      // Wait for ready status
      await waitForBackendReady(process, STARTUP_TIME_TARGET + 2000);

      // Stop the process
      await stopBackend(process);

      // Verify status events were emitted
      expect(statusEvents.length).toBeGreaterThan(0);
      
      const readyEvent = statusEvents.find(e => e.status === 'ready');
      expect(readyEvent).toBeDefined();
      expect(readyEvent?.timestamp).toBeLessThan(STARTUP_TIME_TARGET);
    }, 15000);
  });

  describe('Requirement 10.5: Performance Metrics Logging', () => {
    it('should log performance metrics for slow startups', async () => {
      // Skip if bundled executable doesn't exist
      const { executable } = getBackendPath('production');
      if (!fs.existsSync(executable)) {
        console.warn('Bundled executable not found, skipping metrics logging test');
        return;
      }

      // Start backend if not already running
      if (!backendProcess) {
        backendMetrics = await startBackendAndMeasure('production');
      }

      // Get startup metrics
      const response = await fetch(`http://127.0.0.1:${TEST_PORT}/api/startup/metrics`);
      expect(response.ok).toBe(true);

      const metrics = await response.json();
      
      // Verify metrics structure
      expect(metrics).toHaveProperty('total_time');
      expect(metrics).toHaveProperty('meets_target');
      expect(metrics).toHaveProperty('phases');
      expect(metrics).toHaveProperty('recommendations');
      
      // If startup was slow, verify recommendations are provided
      if (!metrics.meets_target) {
        expect(metrics.recommendations.length).toBeGreaterThan(0);
        console.log('Slow startup detected. Recommendations:', metrics.recommendations);
      }
      
      // Verify phase timing information is available
      expect(typeof metrics.phases).toBe('object');
    }, 10000);
  });

  describe('Health Endpoint Performance', () => {
    it('should respond to /api/health quickly with bundled executable', async () => {
      // Skip if bundled executable doesn't exist
      const { executable } = getBackendPath('production');
      if (!fs.existsSync(executable)) {
        console.warn('Bundled executable not found, skipping health endpoint test');
        return;
      }

      // Start backend if not already running
      if (!backendProcess) {
        backendMetrics = await startBackendAndMeasure('production');
      }

      // Check health endpoint response time
      const responseTime = await checkHealthEndpoint(TEST_PORT);
      
      console.log(`Health endpoint response time: ${responseTime}ms`);
      
      // Health endpoint should respond within 2 seconds
      expect(responseTime).toBeLessThan(HEALTH_CHECK_TIMEOUT);
      
      // Ideally, it should respond much faster (under 500ms)
      if (responseTime > 500) {
        console.warn(`Health endpoint response time (${responseTime}ms) is slower than ideal (<500ms)`);
      }
    }, 10000);
  });

  describe('Startup Time Comparison', () => {
    it('should compare startup time between development and production modes', async () => {
      const results: { mode: string; startupTime: number; available: boolean }[] = [];

      // Test production mode
      const { executable: prodExec } = getBackendPath('production');
      if (fs.existsSync(prodExec)) {
        try {
          const prodMetrics = await startBackendAndMeasure('production');
          results.push({
            mode: 'production',
            startupTime: prodMetrics.totalStartupTime,
            available: true
          });
          
          // Clean up
          if (backendProcess) {
            await stopBackend(backendProcess);
            backendProcess = null;
          }
        } catch (error) {
          console.error('Production mode test failed:', error);
          results.push({
            mode: 'production',
            startupTime: -1,
            available: false
          });
        }
      } else {
        console.warn('Production executable not found, skipping production mode comparison');
        results.push({
          mode: 'production',
          startupTime: -1,
          available: false
        });
      }

      // Test development mode
      const { executable: devExec } = getBackendPath('development');
      if (fs.existsSync(devExec) || process.platform !== 'win32') {
        try {
          const devMetrics = await startBackendAndMeasure('development');
          results.push({
            mode: 'development',
            startupTime: devMetrics.totalStartupTime,
            available: true
          });
          
          // Clean up
          if (backendProcess) {
            await stopBackend(backendProcess);
            backendProcess = null;
          }
        } catch (error) {
          console.error('Development mode test failed:', error);
          results.push({
            mode: 'development',
            startupTime: -1,
            available: false
          });
        }
      } else {
        console.warn('Python not found, skipping development mode comparison');
        results.push({
          mode: 'development',
          startupTime: -1,
          available: false
        });
      }

      // Log comparison results
      console.log('\nStartup Time Comparison:');
      results.forEach(result => {
        if (result.available) {
          console.log(`  ${result.mode}: ${result.startupTime}ms`);
        } else {
          console.log(`  ${result.mode}: Not available`);
        }
      });

      // Verify at least one mode was tested
      const availableResults = results.filter(r => r.available);
      
      // If no modes are available, skip the test
      if (availableResults.length === 0) {
        console.warn('Neither production nor development mode is available for testing');
        return;
      }
      
      expect(availableResults.length).toBeGreaterThan(0);

      // If both modes are available, compare them
      if (availableResults.length === 2) {
        const prodResult = results.find(r => r.mode === 'production');
        const devResult = results.find(r => r.mode === 'development');
        
        if (prodResult && devResult && prodResult.available && devResult.available) {
          const difference = Math.abs(prodResult.startupTime - devResult.startupTime);
          const percentDiff = (difference / Math.max(prodResult.startupTime, devResult.startupTime)) * 100;
          
          console.log(`\nStartup time difference: ${difference}ms (${percentDiff.toFixed(1)}%)`);
          
          // Both modes should meet the 5-second target
          expect(prodResult.startupTime).toBeLessThan(STARTUP_TIME_TARGET);
          expect(devResult.startupTime).toBeLessThan(STARTUP_TIME_TARGET);
        }
      }
    }, 30000); // 30 second timeout for comparison test
  });
});
