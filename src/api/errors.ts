import type { FormattedError } from "../types/error";

const API_BASE_URL = "http://localhost:8000";

export async function formatError(
  error: Error,
  context?: Record<string, unknown>,
): Promise<FormattedError> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/errors/format`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        error_type: error.name,
        error_message: error.message,
        context: context || {},
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to format error: ${response.statusText}`);
    }

    return await response.json();
  } catch {
    // Fallback if the backend is unavailable
    return {
      title: "Error Occurred",
      what_happened: error.message || "An unexpected error occurred.",
      why_it_happened: "The system encountered an issue.",
      actions: [
        {
          description: "Try the operation again",
          automatic: false,
          action_type: "manual_step",
        },
        {
          description: "Check the application logs for more details",
          automatic: false,
          action_type: "manual_step",
        },
      ],
      category: "system" as const,
      severity: "medium" as const,
      help_link: "https://docs.peftstudio.ai/troubleshooting",
      auto_recoverable: false,
    };
  }
}

export async function executeAutoFix(
  actionData: Record<string, unknown>,
  context: Record<string, unknown>,
): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/errors/auto-fix`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        action_data: actionData,
        context,
      }),
    });

    if (!response.ok) {
      return false;
    }

    const result = await response.json();
    return result.success || false;
  } catch (error) {
    console.error("Failed to execute auto-fix:", error);
    return false;
  }
}
