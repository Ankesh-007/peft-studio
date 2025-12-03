import React, { useEffect, useState } from 'react';

interface SplashScreenProps {
  onComplete: () => void;
}

interface StartupProgress {
  stage: string;
  progress: number;
  message: string;
}

export const SplashScreen: React.FC<SplashScreenProps> = ({ onComplete }) => {
  const [progress, setProgress] = useState<StartupProgress>({
    stage: 'initializing',
    progress: 0,
    message: 'Initializing PEFT Studio...',
  });

  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Stage 1: Check backend health (0-30%)
        setProgress({
          stage: 'backend',
          progress: 10,
          message: 'Connecting to backend...',
        });

        const healthCheck = await fetch('http://localhost:8000/api/health', {
          signal: AbortSignal.timeout(5000),
        });

        if (!healthCheck.ok) {
          throw new Error('Backend health check failed');
        }

        setProgress({
          stage: 'backend',
          progress: 30,
          message: 'Backend connected',
        });

        // Stage 2: Load critical resources (30-60%)
        setProgress({
          stage: 'resources',
          progress: 40,
          message: 'Loading resources...',
        });

        // Simulate loading critical resources
        await new Promise((resolve) => setTimeout(resolve, 300));

        setProgress({
          stage: 'resources',
          progress: 60,
          message: 'Resources loaded',
        });

        // Stage 3: Initialize UI (60-90%)
        setProgress({
          stage: 'ui',
          progress: 70,
          message: 'Initializing interface...',
        });

        await new Promise((resolve) => setTimeout(resolve, 200));

        setProgress({
          stage: 'ui',
          progress: 90,
          message: 'Interface ready',
        });

        // Stage 4: Complete (90-100%)
        setProgress({
          stage: 'complete',
          progress: 100,
          message: 'Ready!',
        });

        // Small delay before transitioning
        await new Promise((resolve) => setTimeout(resolve, 300));

        onComplete();
      } catch (error) {
        console.error('Startup error:', error);
        setProgress({
          stage: 'error',
          progress: 0,
          message: 'Failed to start. Please check if the backend is running.',
        });
      }
    };

    initializeApp();
  }, [onComplete]);

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center z-50">
      <div className="text-center">
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
        <div className="w-80 mx-auto">
          <div className="bg-white/10 rounded-full h-2 mb-4 overflow-hidden">
            <div
              className="bg-gradient-to-r from-blue-400 to-purple-400 h-full transition-all duration-300 ease-out"
              style={{ width: `${progress.progress}%` }}
            />
          </div>

          {/* Status Message */}
          <p className="text-blue-100 text-sm animate-pulse">
            {progress.message}
          </p>

          {/* Progress Percentage */}
          <p className="text-blue-300 text-xs mt-2">{progress.progress}%</p>
        </div>

        {/* Error State */}
        {progress.stage === 'error' && (
          <div className="mt-6 p-4 bg-red-500/20 border border-red-500/50 rounded-lg max-w-md mx-auto">
            <p className="text-red-200 text-sm">{progress.message}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-3 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm transition-colors"
            >
              Retry
            </button>
          </div>
        )}

        {/* Loading Spinner */}
        {progress.stage !== 'error' && progress.stage !== 'complete' && (
          <div className="mt-8 flex justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
          </div>
        )}
      </div>

      {/* Version Info */}
      <div className="absolute bottom-4 left-0 right-0 text-center">
        <p className="text-blue-300 text-xs">Version 1.0.0</p>
      </div>
    </div>
  );
};

export default SplashScreen;
