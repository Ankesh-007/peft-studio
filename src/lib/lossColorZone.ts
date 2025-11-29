/**
 * Loss curve color zone utilities
 * Implements Property 9: Loss curve color coding
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

/**
 * Get a human-readable description of the loss zone
 */
export function getLossZoneDescription(zone: LossZone): string {
  switch (zone) {
    case 'green':
      return 'Training is progressing well. Loss is low and decreasing.';
    case 'yellow':
      return 'Training is acceptable. Loss is stable or slightly increasing.';
    case 'red':
      return 'Training may have issues. Loss is high or diverging.';
  }
}
