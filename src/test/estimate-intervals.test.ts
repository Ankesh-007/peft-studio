import { describe, test, expect } from 'vitest';
import fc from 'fast-check';

// **Feature: simplified-llm-optimization, Property 10: Training estimates include confidence intervals**

export interface TrainingEstimate {
  duration: {
    min: number; // seconds
    expected: number;
    max: number;
  };
  confidence: number; // 0-1
}

export interface TrainingConfig {
  batchSize: number;
  epochs: number;
  datasetSize: number;
  stepsPerEpoch: number;
  throughputStepsPerSec: number;
}

/**
 * Calculate training time estimates with confidence intervals
 * Based on:
 * - Batch size and dataset size determine steps per epoch
 * - Throughput (steps/sec) determines base time
 * - Confidence intervals account for variability (±20% typical)
 */
export function calculateTrainingEstimate(config: TrainingConfig): TrainingEstimate {
  // Validate inputs
  if (
    config.batchSize <= 0 ||
    config.epochs <= 0 ||
    config.datasetSize <= 0 ||
    config.stepsPerEpoch <= 0 ||
    config.throughputStepsPerSec <= 0
  ) {
    throw new Error('Invalid training configuration: all values must be positive');
  }

  // Calculate total steps
  const totalSteps = config.stepsPerEpoch * config.epochs;

  // Calculate expected duration (in seconds)
  const expectedDuration = totalSteps / config.throughputStepsPerSec;

  // Add confidence intervals (±20% for typical variability)
  // Min: optimistic case (20% faster)
  // Max: pessimistic case (20% slower)
  const variabilityFactor = 0.2;
  const minDuration = expectedDuration * (1 - variabilityFactor);
  const maxDuration = expectedDuration * (1 + variabilityFactor);

  // Confidence decreases with longer training times (more uncertainty)
  // Base confidence of 0.8, decreasing for very long runs
  const hoursExpected = expectedDuration / 3600;
  let confidence = 0.8;
  if (hoursExpected > 24) {
    confidence = 0.6; // Lower confidence for multi-day runs
  } else if (hoursExpected > 8) {
    confidence = 0.7; // Medium confidence for long runs
  }

  return {
    duration: {
      min: Math.max(0, minDuration),
      expected: expectedDuration,
      max: maxDuration,
    },
    confidence,
  };
}

describe('Property 10: Training estimates include confidence intervals', () => {
  test('for any training configuration, estimate should include min, expected, and max duration', () => {
    fc.assert(
      fc.property(
        fc.record({
          batchSize: fc.integer({ min: 1, max: 128 }),
          epochs: fc.integer({ min: 1, max: 100 }),
          datasetSize: fc.integer({ min: 100, max: 1000000 }),
          stepsPerEpoch: fc.integer({ min: 10, max: 10000 }),
          throughputStepsPerSec: fc.double({ min: 0.1, max: 100, noNaN: true }),
        }),
        (config) => {
          const estimate = calculateTrainingEstimate(config);

          // Property: All duration fields must exist and be numbers
          expect(estimate.duration.min).toBeTypeOf('number');
          expect(estimate.duration.expected).toBeTypeOf('number');
          expect(estimate.duration.max).toBeTypeOf('number');

          // Property: All durations must be non-negative
          expect(estimate.duration.min).toBeGreaterThanOrEqual(0);
          expect(estimate.duration.expected).toBeGreaterThanOrEqual(0);
          expect(estimate.duration.max).toBeGreaterThanOrEqual(0);

          // Property: Confidence must exist and be between 0 and 1
          expect(estimate.confidence).toBeTypeOf('number');
          expect(estimate.confidence).toBeGreaterThanOrEqual(0);
          expect(estimate.confidence).toBeLessThanOrEqual(1);
        }
      ),
      { numRuns: 100 }
    );
  });

  test('for any training configuration, min <= expected <= max', () => {
    fc.assert(
      fc.property(
        fc.record({
          batchSize: fc.integer({ min: 1, max: 128 }),
          epochs: fc.integer({ min: 1, max: 100 }),
          datasetSize: fc.integer({ min: 100, max: 1000000 }),
          stepsPerEpoch: fc.integer({ min: 10, max: 10000 }),
          throughputStepsPerSec: fc.double({ min: 0.1, max: 100, noNaN: true }),
        }),
        (config) => {
          const estimate = calculateTrainingEstimate(config);

          // Property: Duration bounds must be ordered correctly
          expect(estimate.duration.min).toBeLessThanOrEqual(estimate.duration.expected);
          expect(estimate.duration.expected).toBeLessThanOrEqual(estimate.duration.max);
        }
      ),
      { numRuns: 100 }
    );
  });

  test('for any training configuration, expected duration should be proportional to total steps', () => {
    fc.assert(
      fc.property(
        fc.record({
          batchSize: fc.integer({ min: 1, max: 128 }),
          epochs: fc.integer({ min: 1, max: 100 }),
          datasetSize: fc.integer({ min: 100, max: 1000000 }),
          stepsPerEpoch: fc.integer({ min: 10, max: 10000 }),
          throughputStepsPerSec: fc.double({ min: 0.1, max: 100, noNaN: true }),
        }),
        (config) => {
          const estimate = calculateTrainingEstimate(config);

          // Property: Expected duration should equal total steps / throughput
          const totalSteps = config.stepsPerEpoch * config.epochs;
          const expectedDuration = totalSteps / config.throughputStepsPerSec;

          // Allow small floating point differences
          expect(Math.abs(estimate.duration.expected - expectedDuration)).toBeLessThan(0.01);
        }
      ),
      { numRuns: 100 }
    );
  });

  test('for any training configuration, confidence intervals should be reasonable', () => {
    fc.assert(
      fc.property(
        fc.record({
          batchSize: fc.integer({ min: 1, max: 128 }),
          epochs: fc.integer({ min: 1, max: 100 }),
          datasetSize: fc.integer({ min: 100, max: 1000000 }),
          stepsPerEpoch: fc.integer({ min: 10, max: 10000 }),
          throughputStepsPerSec: fc.double({ min: 0.1, max: 100, noNaN: true }),
        }),
        (config) => {
          const estimate = calculateTrainingEstimate(config);

          // Property: Confidence interval width should be reasonable (not too wide or too narrow)
          const intervalWidth = estimate.duration.max - estimate.duration.min;
          const expectedDuration = estimate.duration.expected;

          // Interval should be at least 10% of expected (not too narrow)
          expect(intervalWidth).toBeGreaterThanOrEqual(expectedDuration * 0.1);

          // Interval should be at most 100% of expected (not too wide)
          expect(intervalWidth).toBeLessThanOrEqual(expectedDuration * 1.0);
        }
      ),
      { numRuns: 100 }
    );
  });

  test('for any training configuration, longer runs should have lower confidence', () => {
    fc.assert(
      fc.property(
        fc.record({
          batchSize: fc.integer({ min: 1, max: 128 }),
          epochs: fc.integer({ min: 1, max: 100 }),
          datasetSize: fc.integer({ min: 100, max: 1000000 }),
          stepsPerEpoch: fc.integer({ min: 10, max: 10000 }),
          throughputStepsPerSec: fc.double({ min: 0.1, max: 100, noNaN: true }),
        }),
        (config) => {
          const estimate = calculateTrainingEstimate(config);

          const hoursExpected = estimate.duration.expected / 3600;

          // Property: Very long runs (>24 hours) should have lower confidence
          if (hoursExpected > 24) {
            expect(estimate.confidence).toBeLessThanOrEqual(0.7);
          }

          // Property: Short runs (<8 hours) should have higher confidence
          if (hoursExpected < 8) {
            expect(estimate.confidence).toBeGreaterThanOrEqual(0.7);
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  test('for any invalid configuration, should throw error', () => {
    fc.assert(
      fc.property(
        fc.record({
          batchSize: fc.integer({ min: -100, max: 0 }),
          epochs: fc.integer({ min: 1, max: 100 }),
          datasetSize: fc.integer({ min: 100, max: 1000000 }),
          stepsPerEpoch: fc.integer({ min: 10, max: 10000 }),
          throughputStepsPerSec: fc.double({ min: 0.1, max: 100, noNaN: true }),
        }),
        (config) => {
          // Property: Invalid configurations should throw errors
          expect(() => calculateTrainingEstimate(config)).toThrow();
        }
      ),
      { numRuns: 100 }
    );
  });

  test('estimate calculation should be deterministic', () => {
    fc.assert(
      fc.property(
        fc.record({
          batchSize: fc.integer({ min: 1, max: 128 }),
          epochs: fc.integer({ min: 1, max: 100 }),
          datasetSize: fc.integer({ min: 100, max: 1000000 }),
          stepsPerEpoch: fc.integer({ min: 10, max: 10000 }),
          throughputStepsPerSec: fc.double({ min: 0.1, max: 100, noNaN: true }),
        }),
        (config) => {
          const estimate1 = calculateTrainingEstimate(config);
          const estimate2 = calculateTrainingEstimate(config);

          // Property: Same inputs should produce same outputs
          expect(estimate1.duration.min).toBe(estimate2.duration.min);
          expect(estimate1.duration.expected).toBe(estimate2.duration.expected);
          expect(estimate1.duration.max).toBe(estimate2.duration.max);
          expect(estimate1.confidence).toBe(estimate2.confidence);
        }
      ),
      { numRuns: 100 }
    );
  });
});
