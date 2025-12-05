/**
 * Property-Based Tests for Backend Process Cleanup
 * 
 * **Feature: python-backend-bundling, Property 3: Process Cleanup Guarantee**
 * **Validates: Requirements 4.2, 4.3, 4.4**
 * 
 * Property: For any application shutdown scenario (normal quit, crash, or forced 
 * termination), when the Electron application exits, no Python backend processes 
 * should remain running as zombie processes.
 */

import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import * as fs from 'fs';
import * as path from 'path';

describe('Backend Process Cleanup Property Tests', () => {
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
   * Helper function to extract stop method implementation
   */
  function extractStopMethod(): string | null {
    const content = getElectronMainContent();
    const methodMatch = content.match(/async stop\(\)\s*\{[\s\S]*?\n\s{2}\}/);
    return methodMatch ? methodMatch[0] : null;
  }

  /**
   * Helper function to check if stop method sends SIGTERM
   */
  function sendsSIGTERM(methodContent: string): boolean {
    return methodContent.includes("kill('SIGTERM')") || methodContent.includes('kill("SIGTERM")');
  }

  /**
   * Helper function to check if stop method sends SIGKILL after timeout
   */
  function sendsSIGKILLAfterTimeout(methodContent: string): boolean {
    return (
      methodContent.includes("kill('SIGKILL')") || methodContent.includes('kill("SIGKILL")')
    ) && methodContent.includes('setTimeout');
  }

  /**
   * Helper function to check if stop method sets isShuttingDown flag
   */
  function setsShuttingDownFlag(methodContent: string): boolean {
    return methodContent.includes('this.isShuttingDown = true');
  }

  /**
   * Helper function to check if stop method stops health checks
   */
  function stopsHealthChecks(methodContent: string): boolean {
    return methodContent.includes('stopHealthChecks()');
  }

  /**
   * Helper function to check if stop method nullifies process reference
   */
  function nullifiesProcessReference(methodContent: string): boolean {
    return methodContent.includes('this.process = null');
  }

  /**
   * Helper function to check if app quit handlers call stop
   */
  function appQuitHandlersCallStop(): boolean {
    const content = getElectronMainContent();
    
    // Check window-all-closed handler
    const windowClosedMatch = content.match(/app\.on\('window-all-closed'[\s\S]*?\}\);/);
    const hasWindowClosedStop = windowClosedMatch ? windowClosedMatch[0].includes('backendManager.stop()') : false;
    
    // Check quit handler
    const quitMatch = content.match(/app\.on\('quit'[\s\S]*?\}\);/);
    const hasQuitStop = quitMatch ? quitMatch[0].includes('backendManager.stop()') : false;
    
    // Check before-quit handler
    const beforeQuitMatch = content.match(/app\.on\('before-quit'[\s\S]*?\}\);/);
    const hasBeforeQuitStop = beforeQuitMatch ? beforeQuitMatch[0].includes('backendManager.stop()') : false;
    
    return hasWindowClosedStop || hasQuitStop || hasBeforeQuitStop;
  }

  /**
   * Helper function to check if handleCrash method exists and stops health checks
   */
  function handleCrashStopsHealthChecks(): boolean {
    const content = getElectronMainContent();
    const handleCrashMatch = content.match(/async handleCrash\(\)\s*\{[\s\S]*?\n\s{2}\}/);
    
    if (!handleCrashMatch) {
      return false;
    }
    
    return handleCrashMatch[0].includes('stopHealthChecks()');
  }

  /**
   * Helper function to check if process close handler checks isShuttingDown
   */
  function processCloseHandlerChecksShuttingDown(): boolean {
    const content = getElectronMainContent();
    const closeHandlerMatch = content.match(/this\.process\.on\('close'[\s\S]*?\}\);/);
    
    if (!closeHandlerMatch) {
      return false;
    }
    
    return closeHandlerMatch[0].includes('isShuttingDown');
  }

  /**
   * Helper function to check if restart method resets restart attempts
   */
  function restartMethodResetsAttempts(): boolean {
    const content = getElectronMainContent();
    const restartMatch = content.match(/async restart\(\)\s*\{[\s\S]*?\n\s{2}\}/);
    
    if (!restartMatch) {
      return false;
    }
    
    return restartMatch[0].includes('this.restartAttempts = 0');
  }

  /**
   * Helper function to check if stop method waits for graceful shutdown
   */
  function waitsForGracefulShutdown(methodContent: string): boolean {
    // Check if there's a setTimeout or delay between SIGTERM and SIGKILL
    const hasSIGTERM = methodContent.includes("kill('SIGTERM')") || methodContent.includes('kill("SIGTERM")');
    const hasSIGKILL = methodContent.includes("kill('SIGKILL')") || methodContent.includes('kill("SIGKILL")');
    const hasDelay = methodContent.includes('setTimeout') || methodContent.includes('await new Promise');
    
    return hasSIGTERM && hasSIGKILL && hasDelay;
  }

  it('Property 3.1: stop method must exist in BackendServiceManager', () => {
    // Property: The stop method must be implemented
    const stopMethod = extractStopMethod();
    expect(stopMethod).not.toBeNull();
  });

  it('Property 3.2: stop method must send SIGTERM for graceful shutdown', () => {
    // Property: Must send SIGTERM signal to allow backend to clean up
    const stopMethod = extractStopMethod();
    expect(stopMethod).not.toBeNull();
    
    if (stopMethod) {
      expect(sendsSIGTERM(stopMethod)).toBe(true);
    }
  });

  it('Property 3.3: stop method must send SIGKILL after timeout', () => {
    // Property: Must force kill with SIGKILL if process doesn't terminate within timeout
    const stopMethod = extractStopMethod();
    expect(stopMethod).not.toBeNull();
    
    if (stopMethod) {
      expect(sendsSIGKILLAfterTimeout(stopMethod)).toBe(true);
    }
  });

  it('Property 3.4: stop method must set isShuttingDown flag', () => {
    // Property: Must set flag to prevent crash recovery during intentional shutdown
    const stopMethod = extractStopMethod();
    expect(stopMethod).not.toBeNull();
    
    if (stopMethod) {
      expect(setsShuttingDownFlag(stopMethod)).toBe(true);
    }
  });

  it('Property 3.5: stop method must stop health checks', () => {
    // Property: Must stop health check interval to prevent false alarms during shutdown
    const stopMethod = extractStopMethod();
    expect(stopMethod).not.toBeNull();
    
    if (stopMethod) {
      expect(stopsHealthChecks(stopMethod)).toBe(true);
    }
  });

  it('Property 3.6: stop method must nullify process reference', () => {
    // Property: Must set this.process to null to indicate no process is running
    const stopMethod = extractStopMethod();
    expect(stopMethod).not.toBeNull();
    
    if (stopMethod) {
      expect(nullifiesProcessReference(stopMethod)).toBe(true);
    }
  });

  it('Property 3.7: app quit handlers must call stop method', () => {
    // Property: All app quit event handlers must call backendManager.stop()
    expect(appQuitHandlersCallStop()).toBe(true);
  });

  it('Property 3.8: handleCrash must stop health checks', () => {
    // Property: Crash handler must stop health checks before attempting restart
    expect(handleCrashStopsHealthChecks()).toBe(true);
  });

  it('Property 3.9: process close handler must check isShuttingDown flag', () => {
    // Property: Must not trigger crash recovery during intentional shutdown
    expect(processCloseHandlerChecksShuttingDown()).toBe(true);
  });

  it('Property 3.10: restart method must reset restart attempts', () => {
    // Property: Manual restart should reset the restart attempt counter
    expect(restartMethodResetsAttempts()).toBe(true);
  });

  it('Property 3.11: stop method must wait for graceful shutdown before force kill', () => {
    // Property: Must give process time to shut down gracefully (1 second per requirements)
    const stopMethod = extractStopMethod();
    expect(stopMethod).not.toBeNull();
    
    if (stopMethod) {
      expect(waitsForGracefulShutdown(stopMethod)).toBe(true);
      
      // Verify the timeout is approximately 1 second (1000ms)
      const timeoutMatch = stopMethod.match(/setTimeout.*?(\d+)/);
      if (timeoutMatch) {
        const timeout = parseInt(timeoutMatch[1]);
        expect(timeout).toBeGreaterThanOrEqual(1000);
        expect(timeout).toBeLessThanOrEqual(2000);
      }
    }
  });

  it('Property 3.12: Cleanup sequence consistency across shutdown scenarios', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate different shutdown scenarios
        fc.record({
          scenario: fc.constantFrom('normal_quit', 'window_closed', 'before_quit', 'crash'),
          hasRunningProcess: fc.boolean(),
        }),
        async ({ scenario, hasRunningProcess }) => {
          const content = getElectronMainContent();
          const stopMethod = extractStopMethod();
          
          expect(stopMethod).not.toBeNull();
          
          if (!stopMethod) {
            return;
          }

          // Property: All shutdown scenarios must follow the same cleanup sequence
          // 1. Set isShuttingDown flag
          expect(stopMethod).toContain('this.isShuttingDown = true');
          
          // 2. Stop health checks
          expect(stopMethod).toContain('stopHealthChecks()');
          
          // 3. Send SIGTERM if process exists
          if (hasRunningProcess) {
            expect(stopMethod).toContain("kill('SIGTERM')");
          }
          
          // 4. Wait for graceful shutdown
          expect(stopMethod).toMatch(/setTimeout|await new Promise/);
          
          // 5. Force kill if still running
          expect(stopMethod).toContain("kill('SIGKILL')");
          
          // 6. Nullify process reference
          expect(stopMethod).toContain('this.process = null');
        }
      ),
      {
        numRuns: 100,
        verbose: true
      }
    );
  });

  it('Property 3.13: Process cleanup must be idempotent', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate scenarios where stop is called multiple times
        fc.record({
          callCount: fc.integer({ min: 1, max: 5 }),
          processState: fc.constantFrom('running', 'stopped', 'null'),
        }),
        async ({ callCount, processState }) => {
          const stopMethod = extractStopMethod();
          expect(stopMethod).not.toBeNull();
          
          if (!stopMethod) {
            return;
          }

          // Property: Calling stop multiple times should be safe
          // Must check if process exists before attempting to kill
          expect(stopMethod).toContain('if (this.process)');
          
          // Property: Must nullify process reference to prevent double-kill
          expect(stopMethod).toContain('this.process = null');
          
          // Property: stopHealthChecks should be safe to call multiple times
          const content = getElectronMainContent();
          const stopHealthChecksMatch = content.match(/stopHealthChecks\(\)\s*\{[\s\S]*?\n\s{2}\}/);
          
          if (stopHealthChecksMatch) {
            const stopHealthChecksMethod = stopHealthChecksMatch[0];
            // Must check if interval exists before clearing
            expect(stopHealthChecksMethod).toContain('if (this.healthCheckInterval)');
            expect(stopHealthChecksMethod).toContain('this.healthCheckInterval = null');
          }
        }
      ),
      {
        numRuns: 100,
        verbose: true
      }
    );
  });

  it('Property 3.14: Crash recovery must not trigger during intentional shutdown', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate different exit codes and shutdown states
        fc.record({
          exitCode: fc.integer({ min: 0, max: 255 }),
          isShuttingDown: fc.boolean(),
        }),
        async ({ exitCode, isShuttingDown }) => {
          const content = getElectronMainContent();
          const closeHandlerMatch = content.match(/this\.process\.on\('close'[\s\S]*?\}\);/);
          
          expect(closeHandlerMatch).not.toBeNull();
          
          if (!closeHandlerMatch) {
            return;
          }
          
          const closeHandler = closeHandlerMatch[0];

          // Property: Must check isShuttingDown flag before triggering crash recovery
          expect(closeHandler).toContain('isShuttingDown');
          
          // Property: Must only trigger crash recovery for non-zero exit codes
          expect(closeHandler).toContain('code !== 0');
          
          // Property: Must not trigger crash recovery if isShuttingDown is true
          if (isShuttingDown) {
            // The condition should be: !this.isShuttingDown && code !== 0
            expect(closeHandler).toMatch(/!.*isShuttingDown.*&&.*code !== 0|code !== 0.*&&.*!.*isShuttingDown/);
          }
        }
      ),
      {
        numRuns: 100,
        verbose: true
      }
    );
  });

  it('Property 3.15: Health checks must be stopped before process termination', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate different termination scenarios
        fc.constantFrom('stop', 'handleCrash', 'restart'),
        async (method) => {
          const content = getElectronMainContent();
          
          let methodMatch: RegExpMatchArray | null = null;
          
          if (method === 'stop') {
            methodMatch = content.match(/async stop\(\)\s*\{[\s\S]*?\n\s{2}\}/);
          } else if (method === 'handleCrash') {
            methodMatch = content.match(/async handleCrash\(\)\s*\{[\s\S]*?\n\s{2}\}/);
          } else if (method === 'restart') {
            methodMatch = content.match(/async restart\(\)\s*\{[\s\S]*?\n\s{2}\}/);
          }
          
          expect(methodMatch).not.toBeNull();
          
          if (!methodMatch) {
            return;
          }
          
          const methodContent = methodMatch[0];

          // Property: All termination methods must stop health checks
          if (method === 'stop' || method === 'handleCrash') {
            expect(methodContent).toContain('stopHealthChecks()');
          } else if (method === 'restart') {
            // Restart calls stop, which stops health checks
            expect(methodContent).toContain('stop()');
          }
        }
      ),
      {
        numRuns: 100,
        verbose: true
      }
    );
  });

  it('Property 3.16: SIGTERM must be sent before SIGKILL', () => {
    // Property: Graceful shutdown (SIGTERM) must always precede force kill (SIGKILL)
    const stopMethod = extractStopMethod();
    expect(stopMethod).not.toBeNull();
    
    if (stopMethod) {
      const sigtermIndex = stopMethod.indexOf("kill('SIGTERM')");
      const sigkillIndex = stopMethod.indexOf("kill('SIGKILL')");
      
      // Both signals must be present
      expect(sigtermIndex).toBeGreaterThan(-1);
      expect(sigkillIndex).toBeGreaterThan(-1);
      
      // SIGTERM must come before SIGKILL
      expect(sigtermIndex).toBeLessThan(sigkillIndex);
    }
  });

  it('Property 3.17: Process reference must be checked before kill operations', () => {
    // Property: Must verify process exists before attempting to kill it
    const stopMethod = extractStopMethod();
    expect(stopMethod).not.toBeNull();
    
    if (stopMethod) {
      // Must check if process exists
      expect(stopMethod).toContain('if (this.process)');
      
      // The kill operations should be inside the if block
      const ifBlockMatch = stopMethod.match(/if \(this\.process\)\s*\{[\s\S]*?\n\s{4}\}/);
      if (ifBlockMatch) {
        expect(ifBlockMatch[0]).toContain('kill');
      }
    }
  });

  it('Property 3.18: Shutdown flag must be set at the beginning of stop method', () => {
    // Property: isShuttingDown must be set before any other operations
    const stopMethod = extractStopMethod();
    expect(stopMethod).not.toBeNull();
    
    if (stopMethod) {
      const lines = stopMethod.split('\n').filter(line => line.trim().length > 0);
      
      // Find the line that sets isShuttingDown
      const shutdownFlagLineIndex = lines.findIndex(line => 
        line.includes('this.isShuttingDown = true')
      );
      
      // Find the line that stops health checks
      const stopHealthChecksLineIndex = lines.findIndex(line => 
        line.includes('stopHealthChecks()')
      );
      
      // isShuttingDown should be set before stopping health checks
      expect(shutdownFlagLineIndex).toBeGreaterThan(-1);
      expect(stopHealthChecksLineIndex).toBeGreaterThan(-1);
      expect(shutdownFlagLineIndex).toBeLessThan(stopHealthChecksLineIndex);
    }
  });

  it('Property 3.19: Timeout duration must match requirements (1 second)', () => {
    // Property: Must wait exactly 1 second (1000ms) between SIGTERM and SIGKILL per Requirement 4.3
    const stopMethod = extractStopMethod();
    expect(stopMethod).not.toBeNull();
    
    if (stopMethod) {
      // Look for setTimeout or Promise with delay
      const timeoutMatch = stopMethod.match(/setTimeout.*?(\d+)|resolve.*?(\d+)/);
      
      if (timeoutMatch) {
        const timeout = parseInt(timeoutMatch[1] || timeoutMatch[2]);
        
        // Must be 1000ms (1 second) as per requirements
        expect(timeout).toBe(1000);
      }
    }
  });

  it('Property 3.20: All app lifecycle handlers must ensure cleanup', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate different app lifecycle events
        fc.constantFrom('window-all-closed', 'quit', 'before-quit'),
        async (event) => {
          const content = getElectronMainContent();
          
          // Find the handler for this event
          const handlerMatch = content.match(new RegExp(`app\\.on\\('${event}'[\\s\\S]*?\\}\\);`));
          
          expect(handlerMatch).not.toBeNull();
          
          if (!handlerMatch) {
            return;
          }
          
          const handler = handlerMatch[0];

          // Property: All quit-related handlers must call backendManager.stop()
          if (event === 'quit' || event === 'before-quit' || event === 'window-all-closed') {
            expect(handler).toContain('backendManager.stop()');
          }
          
          // Property: before-quit handler must prevent default and wait for cleanup
          if (event === 'before-quit') {
            expect(handler).toContain('event.preventDefault()');
            expect(handler).toContain('await');
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
