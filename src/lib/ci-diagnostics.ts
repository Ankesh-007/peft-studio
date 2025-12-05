/**
 * CI Diagnostics Library
 * 
 * Provides utilities for analyzing CI workflow runs and extracting failures.
 */

export interface WorkflowRun {
  id: string;
  name: string;
  status: 'success' | 'failure' | 'cancelled' | 'in_progress';
  conclusion: string | null;
  jobs: Job[];
}

export interface EnvironmentConfig {
  nodeVersion: string;
  pythonVersion: string;
  dependencies: Record<string, string>;
}

export interface VersionDiff {
  local: string;
  ci: string;
  compatible: boolean;
}

export interface DependencyDiff {
  package: string;
  localVersion: string;
  ciVersion: string;
  mismatch: boolean;
}

export interface EnvironmentComparison {
  nodeVersion: VersionDiff;
  pythonVersion: VersionDiff;
  dependencyDiffs: DependencyDiff[];
}

export interface Job {
  id: string;
  name: string;
  status: 'success' | 'failure' | 'cancelled' | 'skipped';
  steps: Step[];
}

export interface Step {
  name: string;
  status: 'success' | 'failure' | 'cancelled' | 'skipped';
  conclusion: string | null;
  output?: string;
}

export interface Failure {
  job: string;
  step: string;
  errorMessage: string;
  stackTrace?: string;
  exitCode: number;
}

export interface FailureCategory {
  type: 'lint' | 'test' | 'build' | 'dependency' | 'environment';
  failures: Failure[];
  rootCause: string;
  suggestedFix: string;
}

/**
 * CI Log Analyzer
 * 
 * Analyzes CI workflow runs and extracts failure information.
 */
export class CILogAnalyzer {
  /**
   * Extract all failures from a workflow run
   * 
   * Property: For any workflow run with failures, this should identify all failing
   * jobs and steps without missing any failures.
   */
  extractFailures(run: WorkflowRun): Failure[] {
    const failures: Failure[] = [];

    for (const job of run.jobs) {
      if (job.status === 'failure') {
        for (const step of job.steps) {
          if (step.status === 'failure') {
            const failure: Failure = {
              job: job.name,
              step: step.name,
              errorMessage: this.extractErrorMessage(step.output || ''),
              stackTrace: this.extractStackTrace(step.output || ''),
              exitCode: this.extractExitCode(step.output || ''),
            };
            failures.push(failure);
          }
        }
      }
    }

    return failures;
  }

  /**
   * Extract error message from step output
   */
  private extractErrorMessage(output: string): string {
    // Look for common error patterns
    const errorPatterns = [
      /Error: (.+)/,
      /ERROR: (.+)/,
      /error: (.+)/,
      /Failed: (.+)/,
      /FAILED: (.+)/,
      /✖ (.+)/,
      /× (.+)/,
    ];

    for (const pattern of errorPatterns) {
      const match = output.match(pattern);
      if (match) {
        return match[1].trim();
      }
    }

    // If no specific error pattern found, return first non-empty line
    const lines = output.split('\n').filter(line => line.trim().length > 0);
    return lines.length > 0 ? lines[0].trim() : 'Unknown error';
  }

  /**
   * Extract stack trace from step output
   */
  private extractStackTrace(output: string): string | undefined {
    // Look for stack trace patterns
    const stackTraceStart = output.indexOf('    at ');
    if (stackTraceStart !== -1) {
      const stackLines = output.substring(stackTraceStart).split('\n');
      const relevantLines = stackLines.filter(line => line.trim().startsWith('at '));
      return relevantLines.length > 0 ? relevantLines.join('\n') : undefined;
    }
    return undefined;
  }

  /**
   * Extract exit code from step output
   */
  private extractExitCode(output: string): number {
    const exitCodePattern = /exit code (\d+)/i;
    const match = output.match(exitCodePattern);
    return match ? parseInt(match[1], 10) : 1;
  }

  /**
   * Categorize failures by type
   */
  categorizeFailures(failures: Failure[]): FailureCategory[] {
    const categories = new Map<string, Failure[]>();

    for (const failure of failures) {
      const type = this.determineFailureType(failure);
      if (!categories.has(type)) {
        categories.set(type, []);
      }
      categories.get(type)!.push(failure);
    }

    const result: FailureCategory[] = [];
    for (const [type, categoryFailures] of categories.entries()) {
      result.push({
        type: type as FailureCategory['type'],
        failures: categoryFailures,
        rootCause: this.determineRootCause(categoryFailures),
        suggestedFix: this.suggestFix(type as FailureCategory['type']),
      });
    }

    return result;
  }

  /**
   * Determine the type of failure
   */
  private determineFailureType(failure: Failure): string {
    const message = failure.errorMessage.toLowerCase();
    const job = failure.job.toLowerCase();

    if (job.includes('lint') || message.includes('eslint') || message.includes('prettier')) {
      return 'lint';
    }
    if (job.includes('test') || message.includes('test') || message.includes('spec')) {
      return 'test';
    }
    if (job.includes('build') || message.includes('build') || message.includes('compile')) {
      return 'build';
    }
    if (message.includes('module') || message.includes('dependency') || message.includes('package')) {
      return 'dependency';
    }
    return 'environment';
  }

  /**
   * Determine root cause from failures
   */
  private determineRootCause(failures: Failure[]): string {
    if (failures.length === 0) return 'Unknown';
    
    // Use the first failure's error message as the root cause
    return failures[0].errorMessage;
  }

  /**
   * Suggest fix based on failure type
   */
  private suggestFix(type: string): string {
    const fixes: Record<string, string> = {
      lint: 'Run npm run lint:fix to auto-fix linting errors',
      test: 'Review test failures and fix failing tests',
      build: 'Check TypeScript errors with npm run type-check',
      dependency: 'Run npm ci to reinstall dependencies',
      environment: 'Check environment configuration and versions',
    };
    return fixes[type] || 'Review logs for more details';
  }
}

/**
 * Environment Comparator
 * 
 * Compares local and CI environment configurations to identify differences.
 */
export class EnvironmentComparator {
  /**
   * Compare two environment configurations
   * 
   * Property: For any two environment configurations (local and CI), the comparison
   * should identify all differences in Node.js version, Python version, and dependency versions.
   */
  compareEnvironments(local: EnvironmentConfig, ci: EnvironmentConfig): EnvironmentComparison {
    return {
      nodeVersion: this.compareVersions(local.nodeVersion, ci.nodeVersion),
      pythonVersion: this.compareVersions(local.pythonVersion, ci.pythonVersion),
      dependencyDiffs: this.compareDependencies(local.dependencies, ci.dependencies),
    };
  }

  /**
   * Compare two version strings
   */
  private compareVersions(local: string, ci: string): VersionDiff {
    return {
      local,
      ci,
      compatible: this.areVersionsCompatible(local, ci),
    };
  }

  /**
   * Check if two versions are compatible
   * Versions are compatible if they have the same major version
   */
  private areVersionsCompatible(v1: string, v2: string): boolean {
    const major1 = this.extractMajorVersion(v1);
    const major2 = this.extractMajorVersion(v2);
    return major1 === major2;
  }

  /**
   * Extract major version from version string
   */
  private extractMajorVersion(version: string): string {
    // Handle versions like "18.x", "3.10", "v18.0.0", etc.
    const cleaned = version.replace(/^v/, '');
    const parts = cleaned.split('.');
    return parts[0] || '0';
  }

  /**
   * Compare dependencies between two environments
   */
  private compareDependencies(
    local: Record<string, string>,
    ci: Record<string, string>
  ): DependencyDiff[] {
    const diffs: DependencyDiff[] = [];
    
    // Get all unique package names from both environments
    const allPackages = new Set([...Object.keys(local), ...Object.keys(ci)]);

    for (const pkg of allPackages) {
      const localVersion = local[pkg] || 'not installed';
      const ciVersion = ci[pkg] || 'not installed';
      
      if (localVersion !== ciVersion) {
        diffs.push({
          package: pkg,
          localVersion,
          ciVersion,
          mismatch: true,
        });
      }
    }

    return diffs;
  }
}
