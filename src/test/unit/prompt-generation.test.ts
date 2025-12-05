import fc from "fast-check";
import { describe, test, expect } from "vitest";

// **Feature: simplified-llm-optimization, Property 14: Use case generates relevant prompts**

/**
 * Generate example prompts for a given use case
 */
export function generateExamplePrompts(useCase: string): string[] {
  const promptMap: Record<string, string[]> = {
    chatbot: [
      "Hello! How can I help you today?",
      "What would you like to know about our services?",
      "Can you tell me more about your question?",
    ],
    "code-generation": [
      "Write a function that sorts an array in Python",
      "Create a React component for a login form",
      "Implement a binary search algorithm in JavaScript",
    ],
    summarization: [
      "Summarize the following article in 3 sentences:",
      "Provide a brief overview of this document:",
      "What are the key points from this text?",
    ],
    qa: [
      "What is the capital of France?",
      "Explain how photosynthesis works",
      'Who wrote the novel "1984"?',
    ],
    "creative-writing": [
      "Write a short story about a time traveler",
      "Compose a poem about the ocean",
      "Create a dialogue between two characters meeting for the first time",
    ],
    "domain-adaptation": [
      "Explain this concept in simple terms:",
      "Provide an example of how this applies in practice:",
      "What are the implications of this finding?",
    ],
  };

  return promptMap[useCase] || [];
}

describe("Property 14: Use case generates relevant prompts", () => {
  test("any use case should generate at least 3 example prompts", () => {
    fc.assert(
      fc.property(
        fc.constantFrom(
          "chatbot",
          "code-generation",
          "summarization",
          "qa",
          "creative-writing",
          "domain-adaptation"
        ),
        (useCase) => {
          const prompts = generateExamplePrompts(useCase);

          // Should generate at least 3 prompts
          expect(prompts.length).toBeGreaterThanOrEqual(3);

          // All prompts should be non-empty strings
          prompts.forEach((prompt) => {
            expect(prompt).toBeTruthy();
            expect(typeof prompt).toBe("string");
            expect(prompt.length).toBeGreaterThan(0);
          });

          // Prompts should be unique
          const uniquePrompts = new Set(prompts);
          expect(uniquePrompts.size).toBe(prompts.length);
        }
      ),
      { numRuns: 100 }
    );
  });

  test("generated prompts should be relevant to the use case", () => {
    fc.assert(
      fc.property(
        fc.constantFrom(
          "chatbot",
          "code-generation",
          "summarization",
          "qa",
          "creative-writing",
          "domain-adaptation"
        ),
        (useCase) => {
          const prompts = generateExamplePrompts(useCase);

          // Check for use-case specific keywords
          const relevanceChecks: Record<string, (prompt: string) => boolean> = {
            chatbot: (p) => /help|how|what|can|tell|know/i.test(p),
            "code-generation": (p) =>
              /write|create|implement|function|component|algorithm/i.test(p),
            summarization: (p) => /summarize|overview|brief|key points/i.test(p),
            qa: (p) => /what|who|how|explain|where|when/i.test(p),
            "creative-writing": (p) => /write|compose|create|story|poem|dialogue/i.test(p),
            "domain-adaptation": (p) => /explain|example|implications|concept/i.test(p),
          };

          const checker = relevanceChecks[useCase];
          if (checker) {
            // At least one prompt should contain relevant keywords
            const hasRelevant = prompts.some(checker);
            expect(hasRelevant).toBe(true);
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});
