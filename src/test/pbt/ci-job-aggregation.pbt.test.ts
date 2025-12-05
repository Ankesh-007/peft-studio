/**
 * Property-Based Tests for CI Job Aggregation
 * Feature: ci-infrastructure-fix, Property 12: CI Job Dependency Correctness
 * Validates: Requirements 9.1
 */

import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';

type JobStatus = 'success' | 'failure' | 'cancelled' | 'skipped';

interface CIJob {
  name: string;
  status: JobStatus;
  required: boolean;
}

interface CIWorkflowRun {
  jobs: CIJob[];
}

/**
 * Determines if all checks should pass based on individual job results
 * This mimics the logic in the CI workflow's all-checks-passed job
 */
function shouldAllCheckPass(jobs: CIJob[]): boolean {
  // All required jobs must have 'success' status
  const requiredJobs = jobs.filter(job => job.required);
  return requiredJobs.every(job => job.status === 'success');
}

/**
 * Simulates the CI aggregation logic
 */
function aggregateCIResults(run: CIWorkflowRun): JobStatus {
  if (shouldAllCheckPass(run.jobs)) {
    return 'success';
  }
  return 'failure';
}

describe('CI Job Aggregation Property Tests', () => {
  /**
   * Property 12: CI Job Dependency Correctness
   * For any set of CI job results, the all-checks-passed job should correctly
   * aggregate the results, passing only when all required jobs pass
   */
  it('Property 12: all-checks-passed aggregates correctly', () => {
    // Arbitrary for generating job status
    const jobStatusArb = fc.constantFrom<JobStatus>(
      'success',
      'failure',
      'cancelled',
      'skipped'
    );

    // Arbitrary for generating a CI job
    const ciJobArb = fc.record({
      name: fc.constantFrom('lint', 'test-frontend', 'test-backend', 'build-check', 'security-scan'),
      status: jobStatusArb,
      required: fc.boolean(),
    });

    // Arbitrary for generating a workflow run with multiple jobs
    const workflowRunArb = fc.record({
      jobs: fc.array(ciJobArb, { minLength: 1, maxLength: 10 }),
    });

    fc.assert(
      fc.property(workflowRunArb, (run) => {
        const aggregatedStatus = aggregateCIResults(run);
        const requiredJobs = run.jobs.filter(job => job.required);
        const allRequiredPass = requiredJobs.every(job => job.status === 'success');

        // The aggregated status should be 'success' if and only if all required jobs pass
        if (allRequiredPass) {
          expect(aggregatedStatus).toBe('success');
        } else {
          expect(aggregatedStatus).toBe('failure');
        }
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Optional jobs don't affect aggregation
   * For any workflow run, changing the status of non-required jobs should not
   * affect the aggregated result
   */
  it('Property: optional jobs do not affect aggregation', () => {
    const jobStatusArb = fc.constantFrom<JobStatus>(
      'success',
      'failure',
      'cancelled',
      'skipped'
    );

    const workflowRunArb = fc.record({
      jobs: fc.array(
        fc.record({
          name: fc.string(),
          status: jobStatusArb,
          required: fc.boolean(),
        }),
        { minLength: 2, maxLength: 10 }
      ),
    });

    fc.assert(
      fc.property(workflowRunArb, jobStatusArb, (run, newStatus) => {
        const originalResult = aggregateCIResults(run);

        // Change status of all optional jobs
        const modifiedRun = {
          ...run,
          jobs: run.jobs.map(job =>
            job.required ? job : { ...job, status: newStatus }
          ),
        };

        const modifiedResult = aggregateCIResults(modifiedRun);

        // Result should be the same since we only changed optional jobs
        expect(modifiedResult).toBe(originalResult);
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Single required failure causes overall failure
   * For any workflow run where all required jobs pass except one,
   * the aggregated result should be failure
   */
  it('Property: single required failure causes overall failure', () => {
    const requiredJobNames = ['lint', 'test-frontend', 'test-backend', 'build-check'];

    fc.assert(
      fc.property(fc.integer({ min: 0, max: requiredJobNames.length - 1 }), (failingIndex) => {
        const jobs: CIJob[] = requiredJobNames.map((name, index) => ({
          name,
          status: index === failingIndex ? 'failure' : 'success',
          required: true,
        }));

        const run: CIWorkflowRun = { jobs };
        const result = aggregateCIResults(run);

        expect(result).toBe('failure');
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: All required jobs passing means success
   * For any workflow run where all required jobs have 'success' status,
   * the aggregated result should be success regardless of optional job status
   */
  it('Property: all required passing means success', () => {
    const jobStatusArb = fc.constantFrom<JobStatus>(
      'success',
      'failure',
      'cancelled',
      'skipped'
    );

    fc.assert(
      fc.property(
        fc.array(jobStatusArb, { minLength: 0, maxLength: 5 }),
        (optionalStatuses) => {
          const requiredJobs: CIJob[] = [
            { name: 'lint', status: 'success', required: true },
            { name: 'test-frontend', status: 'success', required: true },
            { name: 'test-backend', status: 'success', required: true },
            { name: 'build-check', status: 'success', required: true },
          ];

          const optionalJobs: CIJob[] = optionalStatuses.map((status, index) => ({
            name: `optional-${index}`,
            status,
            required: false,
          }));

          const run: CIWorkflowRun = {
            jobs: [...requiredJobs, ...optionalJobs],
          };

          const result = aggregateCIResults(run);
          expect(result).toBe('success');
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Idempotence of aggregation
   * For any workflow run, running aggregation multiple times should
   * produce the same result
   */
  it('Property: aggregation is idempotent', () => {
    const jobStatusArb = fc.constantFrom<JobStatus>(
      'success',
      'failure',
      'cancelled',
      'skipped'
    );

    const workflowRunArb = fc.record({
      jobs: fc.array(
        fc.record({
          name: fc.string(),
          status: jobStatusArb,
          required: fc.boolean(),
        }),
        { minLength: 1, maxLength: 10 }
      ),
    });

    fc.assert(
      fc.property(workflowRunArb, (run) => {
        const result1 = aggregateCIResults(run);
        const result2 = aggregateCIResults(run);
        const result3 = aggregateCIResults(run);

        expect(result1).toBe(result2);
        expect(result2).toBe(result3);
      }),
      { numRuns: 100 }
    );
  });
});
