/**
 * Training time estimation utilities
 * Implements Property 10: Training estimates include confidence intervals
 */

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
export function calculateTrainingEstimate(
  config: TrainingConfig,
): TrainingEstimate {
  // Validate inputs
  if (
    config.batchSize <= 0 ||
    config.epochs <= 0 ||
    config.datasetSize <= 0 ||
    config.stepsPerEpoch <= 0 ||
    config.throughputStepsPerSec <= 0
  ) {
    throw new Error(
      "Invalid training configuration: all values must be positive",
    );
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

/**
 * Format duration in seconds to human-readable string
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${minutes}m ${secs}s`;
  } else if (seconds < 86400) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  } else {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    return `${days}d ${hours}h`;
  }
}

/**
 * Format estimate with confidence interval
 */
export function formatEstimateWithInterval(estimate: TrainingEstimate): string {
  const min = formatDuration(estimate.duration.min);
  const expected = formatDuration(estimate.duration.expected);
  const max = formatDuration(estimate.duration.max);
  const confidencePercent = Math.round(estimate.confidence * 100);

  return `${expected} (${min} - ${max}, ${confidencePercent}% confidence)`;
}
