import React, { Component } from "react";

import { formatError } from "../api/errors";

import ErrorDisplay from "./ErrorDisplay";

import type { FormattedError } from "../types/error";
import type { ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: (error: FormattedError, reset: () => void) => ReactNode;
}

interface State {
  hasError: boolean;
  formattedError: FormattedError | null;
  isFormatting: boolean;
}

/**
 * Error Boundary component that catches React errors and displays them
 * in a user-friendly format with recovery options.
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      formattedError: null,
      isFormatting: false,
    };
  }

  static getDerivedStateFromError(_: Error): Partial<State> {
    return { hasError: true };
  }

  async componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Error caught by boundary:", error, errorInfo);

    this.setState({ isFormatting: true });

    try {
      const formatted = await formatError(error, {
        componentStack: errorInfo.componentStack,
      });
      this.setState({ formattedError: formatted, isFormatting: false });
    } catch (e) {
      console.error("Failed to format error:", e);
      // Fallback error format
      this.setState({
        formattedError: {
          title: "Application Error",
          what_happened:
            error.message || "An unexpected error occurred in the application.",
          why_it_happened:
            "The application encountered an issue it wasn't prepared for.",
          actions: [
            {
              description: "Reload the page to try again",
              automatic: false,
              action_type: "manual_step",
            },
            {
              description: "Clear your browser cache and reload",
              automatic: false,
              action_type: "manual_step",
            },
          ],
          category: "system" as any,
          severity: "high" as any,
          help_link: "https://docs.peftstudio.ai/troubleshooting",
          auto_recoverable: false,
        },
        isFormatting: false,
      });
    }
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      formattedError: null,
      isFormatting: false,
    });
  };

  handleRetry = () => {
    // Reload the page to retry
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.state.isFormatting) {
        return (
          <div className="flex items-center justify-center min-h-screen bg-gray-50">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Processing error...</p>
            </div>
          </div>
        );
      }

      if (this.state.formattedError) {
        if (this.props.fallback) {
          return this.props.fallback(
            this.state.formattedError,
            this.handleReset,
          );
        }

        return (
          <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
            <div className="max-w-2xl w-full">
              <ErrorDisplay
                error={this.state.formattedError}
                onDismiss={this.handleReset}
                onRetry={this.handleRetry}
              />
              <div className="mt-4 text-center">
                <button
                  onClick={this.handleReset}
                  className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
                >
                  Try Again
                </button>
              </div>
            </div>
          </div>
        );
      }
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
