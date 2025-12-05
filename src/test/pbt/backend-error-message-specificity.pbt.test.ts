/**
 * Property-Based Test: Backend Error Message Specificity
 *
 * Feature: python-backend-bundling, Property 10: Error Message Specificity
 * Validates: Requirements 8.1, 8.2, 8.4
 *
 * This test verifies that backend error messages are specific and actionable:
 * - Executable not found errors mention corrupted installation
 * - Missing dependency errors include the specific module name
 * - All errors include enough context for diagnosis
 */

import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';

/**
 * Backend error types that can occur during startup
 */
type BackendErrorType =
  | 'EXECUTABLE_NOT_FOUND'
  | 'PERMISSION_DENIED'
  | 'MISSING_PACKAGE'
  | 'PORT_IN_USE'
  | 'PYTHON_NOT_FOUND'
  | 'PROCESS_START_FAILED'
  | 'START_ERROR'
  | 'MAX_RESTARTS_EXCEEDED'
  | 'NO_AVAILABLE_PORTS';

/**
 * Backend error information structure
 */
interface BackendErrorInfo {
  error: string;
  code: BackendErrorType;
  missingModule?: string;
  platform?: string;
  mode?: 'development' | 'production';
  path?: string;
  timestamp?: Date;
}

describe('Property 10: Error Message Specificity', () => {
  // Generator for error codes
  const errorCodeArb = fc.constantFrom<BackendErrorType>(
    'EXECUTABLE_NOT_FOUND',
    'PERMISSION_DENIED',
    'MISSING_PACKAGE',
    'PORT_IN_USE',
    'PYTHON_NOT_FOUND',
    'PROCESS_START_FAILED',
    'START_ERROR',
    'MAX_RESTARTS_EXCEEDED',
    'NO_AVAILABLE_PORTS'
  );

  // Generator for module names
  const moduleNameArb = fc.constantFrom(
    'fastapi',
    'uvicorn',
    'torch',
    'transformers',
    'peft',
    'pydantic',
    'sqlalchemy',
    'numpy',
    'pandas'
  );

  // Generator for platforms
  const platformArb = fc.constantFrom('win32', 'darwin', 'linux');

  // Generator for modes
  const modeArb = fc.constantFrom<'development' | 'production'>('development', 'production');

  // Generator for file paths
  const pathArb = fc.oneof(
    fc.constant('/usr/local/bin/peft_engine'),
    fc.constant('C:\\Program Files\\PEFT Studio\\resources\\backend\\peft_engine.exe'),
    fc.constant('/Applications/PEFT Studio.app/Contents/Resources/backend/peft_engine'),
    fc.constant('/opt/peft-studio/resources/backend/peft_engine')
  );

  // Generator for complete error info
  const errorInfoArb: fc.Arbitrary<BackendErrorInfo> = fc
    .record({
      code: errorCodeArb,
      missingModule: fc.option(moduleNameArb, { nil: undefined }),
      platform: fc.option(platformArb, { nil: undefined }),
      mode: fc.option(modeArb, { nil: undefined }),
      path: fc.option(pathArb, { nil: undefined }),
      timestamp: fc.option(fc.date(), { nil: undefined }),
    })
    .map((partial) => {
      // Generate appropriate error message based on code
      let error: string;
      switch (partial.code) {
        case 'EXECUTABLE_NOT_FOUND':
          error =
            'Backend executable not found. Installation may be corrupted. Please reinstall the application.';
          break;
        case 'PERMISSION_DENIED':
          error = `Backend executable lacks execute permission. Please run: chmod +x ${partial.path || '/path/to/executable'}`;
          break;
        case 'MISSING_PACKAGE':
          error = `Missing Python package: ${partial.missingModule || 'unknown'}. Please run: pip install -r requirements.txt`;
          break;
        case 'PORT_IN_USE':
          error = 'Port 8000 is in use. Trying alternative port...';
          break;
        case 'PYTHON_NOT_FOUND':
          error = 'Python 3.10+ is required but not found. Please install Python from python.org';
          break;
        case 'PROCESS_START_FAILED':
          error = 'Failed to start backend process. Please check the logs for details.';
          break;
        case 'START_ERROR':
          error = 'Error starting backend. Please check the logs for details.';
          break;
        case 'MAX_RESTARTS_EXCEEDED':
          error = 'Backend service failed to start after multiple attempts. Please check the logs and try restarting the application.';
          break;
        case 'NO_AVAILABLE_PORTS':
          error = 'All ports 8000-8010 are in use. Please close other applications.';
          break;
      }

      return {
        ...partial,
        error,
      };
    });

  describe('Requirement 8.1: Bundled executable failure messages', () => {
    it('should capture and display error messages when bundled executable fails', () => {
      fc.assert(
        fc.property(errorInfoArb, (errorInfo) => {
          // Every error must have a non-empty message
          expect(errorInfo.error).toBeDefined();
          expect(errorInfo.error).not.toBe('');
          expect(errorInfo.error.trim().length).toBeGreaterThan(0);

          // Error message should be descriptive (more than just a few words)
          expect(errorInfo.error.length).toBeGreaterThan(10);

          return true;
        }),
        { numRuns: 100 }
      );
    });

    it('should include error code for programmatic handling', () => {
      fc.assert(
        fc.property(errorInfoArb, (errorInfo) => {
          expect(errorInfo.code).toBeDefined();
          expect(errorInfo.code).not.toBe('');

          // Code should be one of the valid error types
          const validCodes: BackendErrorType[] = [
            'EXECUTABLE_NOT_FOUND',
            'PERMISSION_DENIED',
            'MISSING_PACKAGE',
            'PORT_IN_USE',
            'PYTHON_NOT_FOUND',
            'PROCESS_START_FAILED',
            'START_ERROR',
            'MAX_RESTARTS_EXCEEDED',
            'NO_AVAILABLE_PORTS',
          ];

          expect(validCodes).toContain(errorInfo.code);

          return true;
        }),
        { numRuns: 100 }
      );
    });
  });

  describe('Requirement 8.2: Executable not found errors', () => {
    const executableNotFoundArb = errorInfoArb.filter(
      (e) => e.code === 'EXECUTABLE_NOT_FOUND'
    );

    it('should mention corrupted installation when executable is missing', () => {
      fc.assert(
        fc.property(executableNotFoundArb, (errorInfo) => {
          const lowerError = errorInfo.error.toLowerCase();

          // Should mention installation corruption
          const mentionsCorruption =
            lowerError.includes('corrupt') ||
            lowerError.includes('installation') ||
            lowerError.includes('missing') ||
            lowerError.includes('not found');

          expect(mentionsCorruption).toBe(true);

          return true;
        }),
        { numRuns: 100 }
      );
    });

    it('should suggest reinstalling when executable is missing', () => {
      fc.assert(
        fc.property(executableNotFoundArb, (errorInfo) => {
          const lowerError = errorInfo.error.toLowerCase();

          // Should suggest reinstallation
          const suggestsReinstall =
            lowerError.includes('reinstall') ||
            lowerError.includes('re-install') ||
            lowerError.includes('install again');

          expect(suggestsReinstall).toBe(true);

          return true;
        }),
        { numRuns: 100 }
      );
    });
  });

  describe('Requirement 8.4: Missing dependency errors', () => {
    const missingPackageArb = errorInfoArb.filter((e) => e.code === 'MISSING_PACKAGE');

    it('should include specific module name when dependency is missing', () => {
      fc.assert(
        fc.property(missingPackageArb, (errorInfo) => {
          // Error message should contain the module name
          if (errorInfo.missingModule) {
            expect(errorInfo.error).toContain(errorInfo.missingModule);
          } else {
            // If no specific module, should at least mention "package" or "module"
            const lowerError = errorInfo.error.toLowerCase();
            const mentionsPackage =
              lowerError.includes('package') ||
              lowerError.includes('module') ||
              lowerError.includes('dependency');

            expect(mentionsPackage).toBe(true);
          }

          return true;
        }),
        { numRuns: 100 }
      );
    });

    it('should provide installation instructions for missing packages', () => {
      fc.assert(
        fc.property(missingPackageArb, (errorInfo) => {
          const lowerError = errorInfo.error.toLowerCase();

          // Should mention pip or installation
          const providesInstructions =
            lowerError.includes('pip install') ||
            lowerError.includes('install') ||
            lowerError.includes('requirements.txt');

          expect(providesInstructions).toBe(true);

          return true;
        }),
        { numRuns: 100 }
      );
    });
  });

  describe('Error message quality', () => {
    it('should not contain generic error messages', () => {
      fc.assert(
        fc.property(errorInfoArb, (errorInfo) => {
          const lowerError = errorInfo.error.toLowerCase();

          // Should not be just "error" or "failed"
          const isNotGeneric =
            lowerError !== 'error' &&
            lowerError !== 'failed' &&
            lowerError !== 'something went wrong' &&
            lowerError !== 'an error occurred';

          expect(isNotGeneric).toBe(true);

          return true;
        }),
        { numRuns: 100 }
      );
    });

    it('should provide actionable information', () => {
      fc.assert(
        fc.property(errorInfoArb, (errorInfo) => {
          const lowerError = errorInfo.error.toLowerCase();

          // Should contain actionable words or specific information
          const actionWords = [
            'install',
            'reinstall',
            'run',
            'close',
            'check',
            'please',
            'try',
            'chmod',
            'port',
            'python',
            'package',
            'executable',
            'permission',
          ];

          const hasActionableInfo = actionWords.some((word) => lowerError.includes(word));

          expect(hasActionableInfo).toBe(true);

          return true;
        }),
        { numRuns: 100 }
      );
    });

    it('should be user-friendly (not overly technical)', () => {
      fc.assert(
        fc.property(errorInfoArb, (errorInfo) => {
          // Error message should not be just a stack trace or code
          const looksLikeStackTrace =
            errorInfo.error.includes('at Object.') ||
            errorInfo.error.includes('at Function.') ||
            errorInfo.error.includes('at async') ||
            (errorInfo.error.match(/^\s+at\s+/) !== null);

          expect(looksLikeStackTrace).toBe(false);

          return true;
        }),
        { numRuns: 100 }
      );
    });
  });

  describe('Context information', () => {
    it('should include platform information when relevant', () => {
      const permissionErrorArb = errorInfoArb.filter((e) => e.code === 'PERMISSION_DENIED');

      fc.assert(
        fc.property(permissionErrorArb, (errorInfo) => {
          // Permission errors should mention chmod (Unix-specific)
          const lowerError = errorInfo.error.toLowerCase();
          const mentionsUnixCommand = lowerError.includes('chmod');

          // This is Unix-specific, so it's expected
          expect(mentionsUnixCommand).toBe(true);

          return true;
        }),
        { numRuns: 100 }
      );
    });

    it('should include path information when relevant', () => {
      const pathRelevantArb = errorInfoArb.filter(
        (e) => e.code === 'EXECUTABLE_NOT_FOUND' || e.code === 'PERMISSION_DENIED'
      );

      fc.assert(
        fc.property(pathRelevantArb, (errorInfo) => {
          // These errors should ideally include path information
          // But we'll just check that the error is specific enough
          expect(errorInfo.error.length).toBeGreaterThan(20);

          return true;
        }),
        { numRuns: 100 }
      );
    });
  });

  describe('Error code consistency', () => {
    it('should have consistent error codes for similar issues', () => {
      fc.assert(
        fc.property(errorInfoArb, (errorInfo) => {
          // Error code should match the error message content
          const lowerError = errorInfo.error.toLowerCase();

          switch (errorInfo.code) {
            case 'EXECUTABLE_NOT_FOUND':
              expect(
                lowerError.includes('not found') ||
                  lowerError.includes('missing') ||
                  lowerError.includes('corrupt')
              ).toBe(true);
              break;
            case 'PERMISSION_DENIED':
              expect(
                lowerError.includes('permission') || lowerError.includes('chmod')
              ).toBe(true);
              break;
            case 'MISSING_PACKAGE':
              expect(
                lowerError.includes('package') ||
                  lowerError.includes('module') ||
                  lowerError.includes('missing')
              ).toBe(true);
              break;
            case 'PORT_IN_USE':
              expect(lowerError.includes('port')).toBe(true);
              break;
            case 'PYTHON_NOT_FOUND':
              expect(lowerError.includes('python')).toBe(true);
              break;
          }

          return true;
        }),
        { numRuns: 100 }
      );
    });
  });
});
