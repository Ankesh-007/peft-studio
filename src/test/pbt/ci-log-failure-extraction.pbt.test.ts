/**
 * Property-Based Tests for CI Log Failure Extraction
 *
 * Feature: ci-infrastructure-fix, Property 1: CI Log Failure Extraction Completeness
 * Validates: Requirements 1.1
 *
 * These tests verify that the CI log analyzer correctly identifies all failing
 * jobs and steps without missing any failures.
 */

import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import { CILogAnalyzer, WorkflowRun, Job, Step, Failure } from '../../lib/ci-diagnostics';

/**
 * Arbitrary generator for Step
 */
const stepArbitrary = (status: 'success' | 'failure' | 'cancelled' | 'skipped') =>
  fc.record({
    name: fc.string({ minLength: 1, maxLength: 50 }),
    status: fc.constant(status),
    conclusion: fc.oneof(fc.constant(null), fc.constant(status)),
    output: fc.option(
      fc.string({ minLength: 10, maxLength: 200 }),
      { nil: undefined }
    ),
  });

/**
 * Arbitrary generator for successful Step
 */
const successStepArbitrary = () => stepArbitrary('success');

/**
 * Arbitrary generator for failed Step with error output
 */
const failedStepArbitrary = () =>
  fc.record({
    name: fc.string({ minLength: 1, maxLength: 50 }),
    status: fc.constant('failure' as const),
    conclusion: fc.constant('failure' as const),
    output: fc.oneof(
      fc.constant('Error: Test failed'),
      fc.constant('ERROR: Build failed with exit code 1'),
      fc.constant('error: Command failed'),
      fc.constant('Failed: Linting errors found'),
      fc.constant('✖ 5 problems (5 errors, 0 warnings)'),
      fc.string({ minLength: 10, maxLength: 200 })
    ),
  });

/**
 * Arbitrary generator for Job
 */
const jobArbitrary = (status: 'success' | 'failure' | 'cancelled' | 'skipped') =>
  fc.record({
    id: fc.uuid(),
    name: fc.string({ minLength: 1, maxLength: 50 }),
    status: fc.constant(status),
    steps: fc.array(
      status === 'failure'
        ? fc.oneof(successStepArbitrary(), failedStepArbitrary())
        : successStepArbitrary(),
      { minLength: 1, maxLength: 10 }
    ),
  });

/**
 * Arbitrary generator for successful Job
 */
const successJobArbitrary = () => jobArbitrary('success');

/**
 * Arbitrary generator for failed Job (must have at least one failed step)
 */
const failedJobArbitrary = () =>
  fc
    .record({
      id: fc.uuid(),
      name: fc.string({ minLength: 1, maxLength: 50 }),
      status: fc.constant('failure' as const),
      steps: fc.tuple(
        fc.array(successStepArbitrary(), { maxLength: 5 }),
        failedStepArbitrary(),
        fc.array(fc.oneof(successStepArbitrary(), failedStepArbitrary()), { maxLength: 5 })
      ),
    })
    .map(({ id, name, status, steps }) => ({
      id,
      name,
      status,
      steps: [...steps[0], steps[1], ...steps[2]],
    }));

/**
 * Arbitrary generator for WorkflowRun
 */
const workflowRunArbitrary = () =>
  fc.record({
    id: fc.uuid(),
    name: fc.string({ minLength: 1, maxLength: 50 }),
    status: fc.constantFrom('success', 'failure', 'cancelled', 'in_progress') as fc.Arbitrary<
      'success' | 'failure' | 'cancelled' | 'in_progress'
    >,
    conclusion: fc.oneof(fc.constant(null), fc.string()),
    jobs: fc.array(fc.oneof(successJobArbitrary(), failedJobArbitrary()), {
      minLength: 1,
      maxLength: 10,
    }),
  });

/**
 * Arbitrary generator for WorkflowRun with at least one failure
 */
const workflowRunWithFailuresArbitrary = () =>
  fc
    .record({
      id: fc.uuid(),
      name: fc.string({ minLength: 1, maxLength: 50 }),
      status: fc.constant('failure' as const),
      conclusion: fc.constant('failure'),
      jobs: fc.tuple(
        fc.array(successJobArbitrary(), { maxLength: 5 }),
        failedJobArbitrary(),
        fc.array(fc.oneof(successJobArbitrary(), failedJobArbitrary()), { maxLength: 5 })
      ),
    })
    .map(({ id, name, status, conclusion, jobs }) => ({
      id,
      name,
      status,
      conclusion,
      jobs: [...jobs[0], jobs[1], ...jobs[2]],
    }));

/**
 * Helper: Count all failed steps in a workflow run
 */
function countFailedSteps(run: WorkflowRun): number {
  let count = 0;
  for (const job of run.jobs) {
    if (job.status === 'failure') {
      for (const step of job.steps) {
        if (step.status === 'failure') {
          count++;
        }
      }
    }
  }
  return count;
}

/**
 * Helper: Get all failed steps from a workflow run
 */
function getAllFailedSteps(run: WorkflowRun): Array<{ job: string; step: string }> {
  const failedSteps: Array<{ job: string; step: string }> = [];
  for (const job of run.jobs) {
    if (job.status === 'failure') {
      for (const step of job.steps) {
        if (step.status === 'failure') {
          failedSteps.push({ job: job.name, step: step.name });
        }
      }
    }
  }
  return failedSteps;
}

describe('CI Log Failure Extraction - Property-Based Tests', () => {
  const analyzer = new CILogAnalyzer();

  /**
   * Feature: ci-infrastructure-fix, Property 1: CI Log Failure Extraction Completeness
   * Validates: Requirements 1.1
   *
   * For any workflow run with failures, the diagnostic system should identify all
   * failing jobs and extract their specific error messages without missing any failures.
   */
  describe('Property 1: CI Log Failure Extraction Completeness', () => {
    it('should extract all failures from a workflow run without missing any', () => {
      fc.assert(
        fc.property(workflowRunWithFailuresArbitrary(), (run) => {
          // Extract failures using the analyzer
          const extractedFailures = analyzer.extractFailures(run);

          // Count expected failures
          const expectedFailureCount = countFailedSteps(run);

          // Property: The number of extracted failures should equal the number of failed steps
          expect(extractedFailures.length).toBe(expectedFailureCount);

          // Property: Each extracted failure should correspond to a failed step
          const allFailedSteps = getAllFailedSteps(run);
          for (const failure of extractedFailures) {
            const matchingStep = allFailedSteps.find(
              (step) => step.job === failure.job && step.step === failure.step
            );
            expect(matchingStep).toBeDefined();
          }

          // Property: All failed steps should be represented in extracted failures
          for (const failedStep of allFailedSteps) {
            const matchingFailure = extractedFailures.find(
              (failure) => failure.job === failedStep.job && failure.step === failedStep.step
            );
            expect(matchingFailure).toBeDefined();
          }
        }),
        { numRuns: 100 }
      );
    });

    it('should extract zero failures from successful workflow runs', () => {
      fc.assert(
        fc.property(
          fc.record({
            id: fc.uuid(),
            name: fc.string({ minLength: 1, maxLength: 50 }),
            status: fc.constant('success' as const),
            conclusion: fc.constant('success'),
            jobs: fc.array(successJobArbitrary(), { minLength: 1, maxLength: 10 }),
          }),
          (run) => {
            // Extract failures using the analyzer
            const extractedFailures = analyzer.extractFailures(run);

            // Property: Successful runs should have zero failures
            expect(extractedFailures.length).toBe(0);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should include error messages for all extracted failures', () => {
      fc.assert(
        fc.property(workflowRunWithFailuresArbitrary(), (run) => {
          // Extract failures using the analyzer
          const extractedFailures = analyzer.extractFailures(run);

          // Property: Every failure should have a non-empty error message
          for (const failure of extractedFailures) {
            expect(failure.errorMessage).toBeTruthy();
            expect(failure.errorMessage.length).toBeGreaterThan(0);
          }

          // Property: Every failure should have a valid exit code
          for (const failure of extractedFailures) {
            expect(failure.exitCode).toBeGreaterThanOrEqual(0);
            expect(Number.isInteger(failure.exitCode)).toBe(true);
          }
        }),
        { numRuns: 100 }
      );
    });

    it('should correctly identify job and step names for each failure', () => {
      fc.assert(
        fc.property(workflowRunWithFailuresArbitrary(), (run) => {
          // Extract failures using the analyzer
          const extractedFailures = analyzer.extractFailures(run);

          // Property: Each failure's job name should match a job in the workflow run
          for (const failure of extractedFailures) {
            const matchingJob = run.jobs.find((job) => job.name === failure.job);
            expect(matchingJob).toBeDefined();
            expect(matchingJob!.status).toBe('failure');
          }

          // Property: Each failure's step name should match a step in the corresponding job
          for (const failure of extractedFailures) {
            const matchingJob = run.jobs.find((job) => job.name === failure.job);
            const matchingStep = matchingJob!.steps.find((step) => step.name === failure.step);
            expect(matchingStep).toBeDefined();
            expect(matchingStep!.status).toBe('failure');
          }
        }),
        { numRuns: 100 }
      );
    });

    it('should not extract failures from successful steps in failed jobs', () => {
      fc.assert(
        fc.property(workflowRunWithFailuresArbitrary(), (run) => {
          // Extract failures using the analyzer
          const extractedFailures = analyzer.extractFailures(run);

          // Property: No extracted failure should correspond to a successful step
          for (const failure of extractedFailures) {
            const matchingJob = run.jobs.find((job) => job.name === failure.job);
            const matchingStep = matchingJob!.steps.find((step) => step.name === failure.step);
            expect(matchingStep!.status).not.toBe('success');
          }
        }),
        { numRuns: 100 }
      );
    });

    it('should handle workflow runs with multiple failed jobs', () => {
      fc.assert(
        fc.property(
          fc
            .record({
              id: fc.uuid(),
              name: fc.string({ minLength: 1, maxLength: 50 }),
              status: fc.constant('failure' as const),
              conclusion: fc.constant('failure'),
              jobs: fc.array(failedJobArbitrary(), { minLength: 2, maxLength: 5 }),
            })
            .map((run) => run as WorkflowRun),
          (run) => {
            // Extract failures using the analyzer
            const extractedFailures = analyzer.extractFailures(run);

            // Property: Should extract failures from all failed jobs
            const failedJobNames = new Set(run.jobs.map((job) => job.name));
            const extractedJobNames = new Set(extractedFailures.map((failure) => failure.job));

            for (const jobName of failedJobNames) {
              expect(extractedJobNames.has(jobName)).toBe(true);
            }

            // Property: Total failures should equal sum of failed steps across all jobs
            const expectedCount = countFailedSteps(run);
            expect(extractedFailures.length).toBe(expectedCount);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should maintain completeness regardless of job order', () => {
      fc.assert(
        fc.property(workflowRunWithFailuresArbitrary(), (run) => {
          // Extract failures from original order
          const failures1 = analyzer.extractFailures(run);

          // Shuffle jobs and extract again
          const shuffledRun = {
            ...run,
            jobs: [...run.jobs].sort(() => Math.random() - 0.5),
          };
          const failures2 = analyzer.extractFailures(shuffledRun);

          // Property: Number of failures should be the same regardless of job order
          expect(failures1.length).toBe(failures2.length);

          // Property: Same failures should be extracted (order may differ)
          for (const failure of failures1) {
            const matchingFailure = failures2.find(
              (f) => f.job === failure.job && f.step === failure.step
            );
            expect(matchingFailure).toBeDefined();
          }
        }),
        { numRuns: 100 }
      );
    });

    it('should handle edge case of single failed step', () => {
      fc.assert(
        fc.property(
          fc.record({
            id: fc.uuid(),
            name: fc.string({ minLength: 1, maxLength: 50 }),
            status: fc.constant('failure' as const),
            conclusion: fc.constant('failure'),
            jobs: fc.constant([
              {
                id: 'job-1',
                name: 'test-job',
                status: 'failure' as const,
                steps: [
                  {
                    name: 'failing-step',
                    status: 'failure' as const,
                    conclusion: 'failure' as const,
                    output: 'Error: Test failed',
                  },
                ],
              },
            ]),
          }),
          (run) => {
            // Extract failures using the analyzer
            const extractedFailures = analyzer.extractFailures(run);

            // Property: Should extract exactly one failure
            expect(extractedFailures.length).toBe(1);
            expect(extractedFailures[0].job).toBe('test-job');
            expect(extractedFailures[0].step).toBe('failing-step');
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});
