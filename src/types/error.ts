export enum ErrorCategory {
  USER_INPUT = "user_input",
  RESOURCE = "resource",
  TRAINING = "training",
  SYSTEM = "system",
  NETWORK = "network",
  DATASET = "dataset",
}

export enum ErrorSeverity {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  CRITICAL = "critical",
}

export interface ErrorAction {
  description: string;
  automatic: boolean;
  action_type: "auto_fix" | "manual_step" | "help_link";
  action_data?: Record<string, unknown>;
}

export interface FormattedError {
  title: string;
  what_happened: string;
  why_it_happened: string;
  actions: ErrorAction[];
  category: ErrorCategory;
  severity: ErrorSeverity;
  help_link?: string;
  original_error?: string;
  auto_recoverable: boolean;
}

export interface ErrorState {
  error: FormattedError | null;
  isRecovering: boolean;
  recoveryAttempts: number;
}
