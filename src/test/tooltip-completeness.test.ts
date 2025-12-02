import fc from "fast-check";
import { describe, it, expect } from "vitest";

import { getTooltip, hasTooltip, getAllTooltipKeys } from "../config/tooltips";

// **Feature: simplified-llm-optimization, Property 2: Configuration tooltips completeness**

describe("Tooltip Completeness Property Tests", () => {
  // All configuration keys that should have tooltips
  const requiredConfigKeys = [
    // Profile Settings
    "profile.use_case",

    // LoRA Settings
    "lora_r",
    "lora_alpha",
    "lora_dropout",
    "target_modules",

    // Training Hyperparameters
    "learning_rate",
    "num_epochs",
    "warmup_ratio",
    "max_seq_length",
    "weight_decay",
    "max_grad_norm",
    "scheduler",

    // Batch and Memory Settings
    "batch_size",
    "gradient_accumulation",

    // Precision Settings
    "precision",
    "quantization",

    // Hardware Requirements
    "min_gpu_memory",
    "recommended_gpu_memory",
    "min_dataset_size",
    "recommended_dataset_size",
    "estimated_time",

    // Dataset Settings
    "dataset_format",
    "dataset_validation",

    // Model Selection
    "model_selection",
    "model_size",
    "model_architecture",

    // Training Estimates
    "training_estimates",
    "training_duration",
    "gpu_hours",
    "electricity_cost",
    "carbon_footprint",
    "memory_usage",
    "epochs",

    // Advanced Settings
    "optimizer",
    "save_steps",
    "eval_steps",
  ];

  it("should have tooltips for all required configuration keys", () => {
    // **Validates: Requirements 1.3**
    const missingTooltips: string[] = [];

    for (const key of requiredConfigKeys) {
      if (!hasTooltip(key)) {
        missingTooltips.push(key);
      }
    }

    expect(missingTooltips).toEqual([]);
  });

  it("property: for any configuration key with a tooltip, it should have all required fields", () => {
    // **Validates: Requirements 1.3, 1.4**
    fc.assert(
      fc.property(fc.constantFrom(...getAllTooltipKeys()), (configKey) => {
        const tooltip = getTooltip(configKey);

        // Tooltip should exist
        expect(tooltip).toBeDefined();
        expect(tooltip).not.toBeNull();

        if (tooltip) {
          // Should have a title
          expect(tooltip.title).toBeDefined();
          expect(typeof tooltip.title).toBe("string");
          expect(tooltip.title.length).toBeGreaterThan(0);

          // Should have a description
          expect(tooltip.description).toBeDefined();
          expect(typeof tooltip.description).toBe("string");
          expect(tooltip.description.length).toBeGreaterThan(0);

          // Description should be plain language (no technical jargon without explanation)
          // Should not contain raw code or stack traces
          expect(tooltip.description).not.toMatch(/Error:/);
          expect(tooltip.description).not.toMatch(/at \w+\.\w+/);
          expect(tooltip.description).not.toMatch(/\w+Error/);

          // If example exists, it should be a string
          if (tooltip.example !== undefined) {
            expect(typeof tooltip.example).toBe("string");
            expect(tooltip.example.length).toBeGreaterThan(0);
          }
        }
      }),
      { numRuns: 100 },
    );
  });

  it("property: tooltip descriptions should be plain language without technical jargon", () => {
    // **Validates: Requirements 1.3**
    fc.assert(
      fc.property(fc.constantFrom(...getAllTooltipKeys()), (configKey) => {
        const tooltip = getTooltip(configKey);

        if (tooltip) {
          const description = tooltip.description.toLowerCase();

          // Should not contain error messages or stack traces
          expect(description).not.toContain("error:");
          expect(description).not.toContain("exception");
          expect(description).not.toContain("traceback");

          // Should not contain raw code syntax
          expect(description).not.toMatch(/\w+\(\)/); // function calls
          expect(description).not.toMatch(/\w+\.\w+\.\w+/); // deep object paths

          // Should be reasonably long (at least 20 characters)
          expect(description.length).toBeGreaterThan(20);

          // Should end with proper punctuation
          expect(description).toMatch(/[.!?]$/);
        }
      }),
      { numRuns: 100 },
    );
  });

  it("property: tooltip titles should be concise and descriptive", () => {
    // **Validates: Requirements 1.3**
    fc.assert(
      fc.property(fc.constantFrom(...getAllTooltipKeys()), (configKey) => {
        const tooltip = getTooltip(configKey);

        if (tooltip) {
          // Title should be concise (less than 50 characters)
          expect(tooltip.title.length).toBeLessThan(50);

          // Title should be descriptive (at least 3 characters)
          expect(tooltip.title.length).toBeGreaterThan(3);

          // Title should not be all caps (unless it's an acronym)
          const words = tooltip.title.split(" ");
          const allCapsWords = words.filter(
            (word) => word === word.toUpperCase() && word.length > 1,
          );
          // Allow some acronyms, but not all words
          expect(allCapsWords.length).toBeLessThan(words.length);
        }
      }),
      { numRuns: 100 },
    );
  });

  it("property: examples should provide concrete, actionable guidance", () => {
    // **Validates: Requirements 1.4**
    fc.assert(
      fc.property(fc.constantFrom(...getAllTooltipKeys()), (configKey) => {
        const tooltip = getTooltip(configKey);

        if (tooltip && tooltip.example) {
          // Example should be reasonably long
          expect(tooltip.example.length).toBeGreaterThan(10);

          // Example should not be the same as the description
          expect(tooltip.example.toLowerCase()).not.toBe(
            tooltip.description.toLowerCase(),
          );

          // Example should provide specific values or guidance
          const hasSpecificGuidance =
            /\d+/.test(tooltip.example) || // Contains numbers
            /["']/.test(tooltip.example) || // Contains quotes (string examples)
            /typical|common|usually|generally/i.test(tooltip.example); // Contains guidance words

          expect(hasSpecificGuidance).toBe(true);
        }
      }),
      { numRuns: 100 },
    );
  });

  it("should have contextual help for all wizard steps", () => {
    // **Validates: Requirements 1.3, 1.4**
    const wizardStepKeys = [
      "profile.use_case",
      "dataset_format",
      "dataset_validation",
      "model_selection",
      "training_estimates",
    ];

    for (const key of wizardStepKeys) {
      expect(hasTooltip(key)).toBe(true);
      const tooltip = getTooltip(key);
      expect(tooltip).toBeDefined();
      expect(tooltip?.title).toBeDefined();
      expect(tooltip?.description).toBeDefined();
    }
  });

  it("should have tooltips for all LoRA parameters", () => {
    // **Validates: Requirements 1.3**
    const loraKeys = ["lora_r", "lora_alpha", "lora_dropout", "target_modules"];

    for (const key of loraKeys) {
      expect(hasTooltip(key)).toBe(true);
      const tooltip = getTooltip(key);
      expect(tooltip).toBeDefined();
      expect(tooltip?.description).toContain("LoRA");
    }
  });

  it("should have tooltips for all training hyperparameters", () => {
    // **Validates: Requirements 1.3**
    const hyperparamKeys = [
      "learning_rate",
      "num_epochs",
      "batch_size",
      "gradient_accumulation",
      "warmup_ratio",
      "max_seq_length",
    ];

    for (const key of hyperparamKeys) {
      expect(hasTooltip(key)).toBe(true);
      const tooltip = getTooltip(key);
      expect(tooltip).toBeDefined();
      expect(tooltip?.example).toBeDefined();
    }
  });

  it("should have tooltips for hardware and resource settings", () => {
    // **Validates: Requirements 1.3**
    const resourceKeys = [
      "min_gpu_memory",
      "recommended_gpu_memory",
      "precision",
      "quantization",
      "memory_usage",
    ];

    for (const key of resourceKeys) {
      expect(hasTooltip(key)).toBe(true);
      const tooltip = getTooltip(key);
      expect(tooltip).toBeDefined();
    }
  });

  it("property: all tooltips should be accessible and complete", () => {
    // **Validates: Requirements 1.3, 1.4**
    // This is a comprehensive property that checks all tooltips at once
    fc.assert(
      fc.property(fc.constantFrom(...requiredConfigKeys), (configKey) => {
        // Tooltip must exist
        expect(hasTooltip(configKey)).toBe(true);

        const tooltip = getTooltip(configKey);
        expect(tooltip).not.toBeNull();

        if (tooltip) {
          // Must have all required fields
          expect(tooltip.title).toBeDefined();
          expect(tooltip.description).toBeDefined();

          // Fields must be non-empty strings
          expect(typeof tooltip.title).toBe("string");
          expect(typeof tooltip.description).toBe("string");
          expect(tooltip.title.length).toBeGreaterThan(0);
          expect(tooltip.description.length).toBeGreaterThan(0);

          // Description should be plain language
          expect(tooltip.description).not.toMatch(/Error:/);
          expect(tooltip.description).not.toMatch(/Exception/);

          // Should provide actionable information
          const isActionable =
            tooltip.description.length > 20 &&
            (tooltip.example !== undefined ||
              tooltip.description.includes("typical") ||
              tooltip.description.includes("common") ||
              tooltip.description.includes("usually"));

          expect(isActionable).toBe(true);
        }
      }),
      { numRuns: 100 },
    );
  });
});
