import { describe, test, expect } from 'vitest';
import fc from 'fast-check';

// **Feature: simplified-llm-optimization, Property 9: Loss curve color coding**

/**
 * Loss curve color zones:
 * - Green (good): Loss is decreasing and below threshold
 * - Yellow (acceptable): Loss is stable or slightly increasing
 * - Red (problematic): Loss is diverging or significantly increasing
 */

export type LossZone = 'green' | 'yellow' | 'red';

export interface LossColorResult {
  zone: LossZone;
  color: string;
}

/**
 * Determines the color zone for a loss value based on:
 * - Current loss value
 * - Previous loss value (for trend detection)
 * - Threshold for "good" loss (typically < 1.0 for well-trained models)
 */
export function getLossColorZone(
  currentLoss: number,
  previousLoss: number | null = null,
  goodThreshold: number = 1.0,
  acceptableThreshold: number = 2.0
): LossColorResult {
  // Handle invalid inputs
  if (currentLoss < 0 || isNaN(currentLoss) || !isFinite(currentLoss)) {
    return { zone: 'red', color: '#ef4444' };
  }

  // If we have previous loss, check for trend
  if (previousLoss !== null && isFinite(previousLoss) && previousLoss > 0) {
    const lossChange = currentLoss - previousLoss;
    const percentChange = (lossChange / previousLoss) * 100;

    // Red zone: Loss is increasing significantly (>10% increase)
    if (percentChange > 10) {
      return { zone: 'red', color: '#ef4444' };
    }

    // Red zone: Loss is very high (>acceptableThreshold)
    if (currentLoss > acceptableThreshold) {
      return { zone: 'red', color: '#ef4444' };
    }

    // Yellow zone: Loss is slightly increasing (0-10% increase) or stable
    if (percentChange > 0 || Math.abs(percentChange) < 1) {
      return { zone: 'yellow', color: '#f59e0b' };
    }

    // Green zone: Loss is decreasing and below good threshold
    if (lossChange < 0 && currentLoss < goodThreshold) {
      return { zone: 'green', color: '#10b981' };
    }

    // Yellow zone: Loss is decreasing but still above good threshold
    if (lossChange < 0 && currentLoss >= goodThreshold) {
      return { zone: 'yellow', color: '#f59e0b' };
    }
  }

  // No previous loss - judge based on absolute value only
  if (currentLoss < goodThreshold) {
    return { zone: 'green', color: '#10b981' };
  } else if (currentLoss < acceptableThreshold) {
    return { zone: 'yellow', color: '#f59e0b' };
  } else {
    return { zone: 'red', color: '#ef4444' };
  }
}

describe('Property 9: Loss curve color coding', () => {
  test('for any loss value, the system should assign a valid color zone', () => {
    fc.assert(
      fc.property(
        fc.double({ min: 0, max: 10, noNaN: true }),
        (lossValue) => {
          const result = getLossColorZone(lossValue);

          // Property: Result must have a valid zone
          expect(['green', 'yellow', 'red']).toContain(result.zone);

          // Property: Result must have a valid color hex code
          expect(result.color).toMatch(/^#[0-9a-f]{6}$/i);
        }
      ),
      { numRuns: 100 }
    );
  });

  test('for any loss value with previous loss, color zone should be consistent with trend', () => {
    fc.assert(
      fc.property(
        fc.double({ min: 0.01, max: 10, noNaN: true }),
        fc.double({ min: 0.01, max: 10, noNaN: true }),
        (currentLoss, previousLoss) => {
          const result = getLossColorZone(currentLoss, previousLoss);

          // Property: Significant increase (>10%) should be red
          const percentChange = ((currentLoss - previousLoss) / previousLoss) * 100;
          if (percentChange > 10) {
            expect(result.zone).toBe('red');
          }

          // Property: Very high loss (>2.0) should be red
          if (currentLoss > 2.0) {
            expect(result.zone).toBe('red');
          }

          // Property: Low decreasing loss (<1.0 and significantly decreasing) should be green
          // Only check for green if there's a meaningful decrease (>1% decrease)
          const lossChange = currentLoss - previousLoss;
          const isSignificantDecrease = lossChange < 0 && Math.abs(percentChange) > 1;
          if (currentLoss < 1.0 && isSignificantDecrease) {
            expect(result.zone).toBe('green');
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  test('for any invalid loss value (NaN, negative, infinite), should return red zone', () => {
    fc.assert(
      fc.property(
        fc.oneof(
          fc.constant(NaN),
          fc.constant(Infinity),
          fc.constant(-Infinity),
          fc.double({ min: -100, max: -0.01 })
        ),
        (invalidLoss) => {
          const result = getLossColorZone(invalidLoss);

          // Property: Invalid values should always be red (problematic)
          expect(result.zone).toBe('red');
          expect(result.color).toBe('#ef4444');
        }
      ),
      { numRuns: 100 }
    );
  });

  test('color zone should be deterministic for same inputs', () => {
    fc.assert(
      fc.property(
        fc.double({ min: 0, max: 10, noNaN: true }),
        fc.option(fc.double({ min: 0, max: 10, noNaN: true }), { nil: null }),
        (currentLoss, previousLoss) => {
          const result1 = getLossColorZone(currentLoss, previousLoss);
          const result2 = getLossColorZone(currentLoss, previousLoss);

          // Property: Same inputs should produce same outputs
          expect(result1.zone).toBe(result2.zone);
          expect(result1.color).toBe(result2.color);
        }
      ),
      { numRuns: 100 }
    );
  });

  test('green zone should only occur for good loss values', () => {
    fc.assert(
      fc.property(
        fc.double({ min: 0, max: 10, noNaN: true }),
        fc.option(fc.double({ min: 0, max: 10, noNaN: true }), { nil: null }),
        (currentLoss, previousLoss) => {
          const result = getLossColorZone(currentLoss, previousLoss);

          // Property: Green zone implies loss is good (low and/or decreasing)
          if (result.zone === 'green') {
            expect(currentLoss).toBeLessThan(1.0);
            if (previousLoss !== null && previousLoss > 0) {
              // Green requires meaningful decrease (not just equal or tiny difference)
              const lossChange = currentLoss - previousLoss;
              expect(lossChange).toBeLessThan(0);
            }
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  test('red zone should occur for problematic loss values', () => {
    fc.assert(
      fc.property(
        fc.double({ min: 0, max: 10, noNaN: true }),
        fc.option(fc.double({ min: 0, max: 10, noNaN: true }), { nil: null }),
        (currentLoss, previousLoss) => {
          const result = getLossColorZone(currentLoss, previousLoss);

          // Property: Red zone implies loss is problematic
          if (result.zone === 'red') {
            const isHighLoss = currentLoss > 2.0;
            const isIncreasing =
              previousLoss !== null &&
              ((currentLoss - previousLoss) / previousLoss) * 100 > 10;
            const isInvalid = !isFinite(currentLoss) || currentLoss < 0;

            // At least one problematic condition should be true
            expect(isHighLoss || isIncreasing || isInvalid).toBe(true);
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});
