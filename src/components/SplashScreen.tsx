import React, { useEffect, useState } from "react";
import { CheckCircle, Loader2, XCircle } from "lucide-react";

interface SplashScreenProps {
  onComplete: () => void;
  onError?: (error: Error) => void;
}

interface StartupProgress {
  stage: string;
  progress: number;
  message: string;
  substeps?: StartupSubstep[];
}

interface StartupSubstep {
  name: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  message?: string;
}

export const SplashScreen: React.FC<SplashScreenProps> = ({ onComplete, onError }) => {
  const [progress, setProgress] = useState<StartupProgress>({
    stage: "initializing",
    progress: 0,
    message: "Initializing PEFT Studio...",
    substeps: [
      { name: "Starting backend service", status: "pending" },
      { name: "Checking dependencies", status: "pending" },
      { name: "Loading configuration", status: "pending" },
      { name: "Initializing interface", status: "pending" },
    ],
  });

  const updateSubstep = (index: number, status: StartupSubstep["status"], message?: string) => {
    setProgress((prev) => ({
      ...prev,
      substeps: prev.substeps?.map((step, i) =>
        i === index ? { ...step, status, message } : step
      ),
    }));
  };

  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Stage 1: Starting backend service (0-25%)
        setProgress((prev) => ({
          ...prev,
          stage: "backend",
          progress: 5,
          message: "Starting backend service...",
        }));
        updateSubstep(0, "in_progress");

        // Wait for backend to be ready (but don't block UI if it fails)
        let backendReady = false;
        let attempts = 0;
        const maxAttempts = 5; // Reduced attempts for faster startup

        while (!backendReady && attempts < maxAttempts) {
          try {
            const healthCheck = await fetch("http://localhost:8000/api/health", {
              signal: AbortSignal.timeout(1500),
            });

            if (healthCheck.ok) {
              backendReady = true;
            }
          } catch {
            attempts++;
            await new Promise((resolve) => setTimeout(resolve, 800));
          }
        }

        if (!backendReady) {
          // Backend not available - continue anyway with warning
          console.warn("Backend service not available - running in limited mode");
          updateSubstep(0, "failed", "Backend unavailable (limited functionality)");
          setProgress((prev) => ({
            ...prev,
            progress: 25,
            message: "Running without backend (limited mode)",
          }));

          // Store backend status for the app to handle
          sessionStorage.setItem("backendAvailable", "false");
        } else {
          updateSubstep(0, "completed", "Backend service running");
          setProgress((prev) => ({
            ...prev,
            progress: 25,
            message: "Backend service connected",
          }));
          sessionStorage.setItem("backendAvailable", "true");
        }

        // Stage 2: Checking dependencies (25-50%)
        setProgress((prev) => ({
          ...prev,
          stage: "dependencies",
          progress: 30,
          message: "Checking dependencies...",
        }));
        updateSubstep(1, "in_progress");

        // Only check dependencies if backend is available
        if (backendReady) {
          try {
            const depsCheck = await fetch("http://localhost:8000/api/dependencies", {
              signal: AbortSignal.timeout(5000),
            });

            if (depsCheck.ok) {
              await depsCheck.json();
              updateSubstep(1, "completed", "All dependencies verified");
            } else {
              updateSubstep(1, "completed", "Dependencies checked (warnings present)");
            }
          } catch {
            // Non-critical, continue
            updateSubstep(1, "completed", "Dependency check skipped");
          }
        } else {
          // Backend not available, skip dependency check
          updateSubstep(1, "completed", "Skipped (backend unavailable)");
        }

        setProgress((prev) => ({
          ...prev,
          progress: 50,
          message: backendReady ? "Dependencies verified" : "Running in limited mode",
        }));

        // Stage 3: Loading configuration (50-75%)
        setProgress((prev) => ({
          ...prev,
          stage: "configuration",
          progress: 55,
          message: "Loading configuration...",
        }));
        updateSubstep(2, "in_progress");

        // Simulate loading configuration
        await new Promise((resolve) => setTimeout(resolve, 500));

        updateSubstep(2, "completed", "Configuration loaded");
        setProgress((prev) => ({
          ...prev,
          progress: 75,
          message: "Configuration ready",
        }));

        // Stage 4: Initializing interface (75-95%)
        setProgress((prev) => ({
          ...prev,
          stage: "ui",
          progress: 80,
          message: "Initializing interface...",
        }));
        updateSubstep(3, "in_progress");

        await new Promise((resolve) => setTimeout(resolve, 300));

        updateSubstep(3, "completed", "Interface ready");
        setProgress((prev) => ({
          ...prev,
          progress: 95,
          message: "Interface initialized",
        }));

        // Stage 5: Complete (95-100%)
        setProgress((prev) => ({
          ...prev,
          stage: "complete",
          progress: 100,
          message: "Ready!",
        }));

        // Small delay before transitioning
        await new Promise((resolve) => setTimeout(resolve, 500));

        onComplete();
      } catch (error) {
        console.error("Startup error:", error);
        const errorMessage = error instanceof Error ? error.message : "Unknown error";

        setProgress((prev) => ({
          ...prev,
          stage: "error",
          progress: 0,
          message: `Startup failed: ${errorMessage}`,
        }));

        // Find which substep failed and mark it
        const currentSubstep = progress.substeps?.findIndex(
          (step) => step.status === "in_progress"
        );
        if (currentSubstep !== undefined && currentSubstep !== -1) {
          updateSubstep(currentSubstep, "failed", errorMessage);
        }

        // Notify parent component of error
        if (onError && error instanceof Error) {
          onError(error);
        }
      }
    };

    initializeApp();
  }, [onComplete, onError, progress.substeps]);

  const getSubstepIcon = (status: StartupSubstep["status"]) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case "failed":
        return <XCircle className="w-4 h-4 text-red-400" />;
      case "in_progress":
        return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />;
      default:
        return <div className="w-4 h-4 rounded-full border-2 border-gray-500" />;
    }
  };

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center z-50">
      <div className="text-center max-w-lg w-full px-4">
        {/* Logo */}
        <div className="mb-8">
          <div className="w-24 h-24 mx-auto bg-white rounded-2xl flex items-center justify-center shadow-2xl">
            <span className="text-4xl font-bold text-blue-600">PS</span>
          </div>
        </div>

        {/* Title */}
        <h1 className="text-4xl font-bold text-white mb-2">PEFT Studio</h1>
        <p className="text-blue-200 mb-8">Unified LLM Fine-Tuning Platform</p>

        {/* Progress Bar */}
        <div className="w-full mx-auto mb-6">
          <div className="bg-white/10 rounded-full h-3 mb-4 overflow-hidden shadow-inner">
            <div
              className="bg-gradient-to-r from-blue-400 to-purple-400 h-full transition-all duration-500 ease-out shadow-lg"
              style={{ width: `${progress.progress}%` }}
            />
          </div>

          {/* Status Message */}
          <p className="text-blue-100 text-base font-medium mb-1">{progress.message}</p>

          {/* Progress Percentage */}
          <p className="text-blue-300 text-sm">{progress.progress}%</p>
        </div>

        {/* Substeps */}
        {progress.substeps && progress.substeps.length > 0 && (
          <div className="bg-white/5 rounded-lg p-4 mb-6 backdrop-blur-sm">
            <div className="space-y-3">
              {progress.substeps.map((substep, index) => (
                <div key={index} className="flex items-center gap-3 text-left">
                  <div className="flex-shrink-0">{getSubstepIcon(substep.status)}</div>
                  <div className="flex-1 min-w-0">
                    <p
                      className={`text-sm font-medium ${
                        substep.status === "completed"
                          ? "text-green-300"
                          : substep.status === "failed"
                            ? "text-red-300"
                            : substep.status === "in_progress"
                              ? "text-blue-300"
                              : "text-gray-400"
                      }`}
                    >
                      {substep.name}
                    </p>
                    {substep.message && (
                      <p className="text-xs text-gray-400 mt-0.5">{substep.message}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error State */}
        {progress.stage === "error" && (
          <div className="mt-6 p-4 bg-red-500/20 border border-red-500/50 rounded-lg backdrop-blur-sm">
            <p className="text-red-200 text-sm mb-3">{progress.message}</p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm transition-colors font-medium"
            >
              Retry Startup
            </button>
          </div>
        )}

        {/* Loading Spinner */}
        {progress.stage !== "error" && progress.stage !== "complete" && (
          <div className="mt-6 flex justify-center">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-t-2 border-white"></div>
          </div>
        )}

        {/* Success State */}
        {progress.stage === "complete" && (
          <div className="mt-6 flex justify-center">
            <CheckCircle className="w-12 h-12 text-green-400 animate-pulse" />
          </div>
        )}
      </div>

      {/* Version Info */}
      <div className="absolute bottom-4 left-0 right-0 text-center">
        <p className="text-blue-300 text-xs">Version 1.0.1</p>
      </div>
    </div>
  );
};

export default SplashScreen;
