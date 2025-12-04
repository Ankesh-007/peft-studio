import { useState, lazy, Suspense, useEffect } from 'react';
import Layout from './components/Layout';
import { useHelpPanel } from './hooks/useHelpPanel';
import { useOnboarding } from './hooks/useOnboarding';
import SplashScreen from './components/SplashScreen';
import StartupError, { StartupErrorInfo } from './components/StartupError';
import PerformanceProfiler from './components/PerformanceProfiler';
import { UpdateNotification } from './components/UpdateNotification';
import { BackendUnavailableBanner } from './components/BackendUnavailableBanner';

// Lazy load heavy components
const Dashboard = lazy(() => import('./components/Dashboard'));
const TrainingWizard = lazy(() => import('./components/TrainingWizard'));
const DeploymentManagement = lazy(() => import('./components/DeploymentManagement').then(m => ({ default: m.DeploymentManagement })));
const GradioDemoGenerator = lazy(() => import('./components/GradioDemoGenerator'));
const InferencePlayground = lazy(() => import('./components/InferencePlayground'));
const ConfigurationManagement = lazy(() => import('./components/ConfigurationManagement'));
const LoggingDiagnostics = lazy(() => import('./components/LoggingDiagnostics'));
const ContextualHelpPanel = lazy(() => import('./components/ContextualHelpPanel'));
const WelcomeScreen = lazy(() => import('./components/onboarding/WelcomeScreen'));
const SetupWizard = lazy(() => import('./components/onboarding/SetupWizard'));
const GuidedTour = lazy(() => import('./components/onboarding/GuidedTour'));

// Loading fallback component
const LoadingFallback = () => (
  <div className="flex items-center justify-center h-screen">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p className="text-gray-600">Loading...</p>
    </div>
  </div>
);

type View = 'dashboard' | 'training' | 'deployment' | 'gradio-demos' | 'inference' | 'configurations' | 'logging';

function App() {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const [isAppReady, setIsAppReady] = useState(false);
  const [startupError, setStartupError] = useState<StartupErrorInfo | null>(null);
  const [isBackendAvailable, setIsBackendAvailable] = useState(true);
  const { isHelpOpen, currentContext, closeHelp } = useHelpPanel();
  const {
    shouldShowOnboarding,
    shouldShowSetup,
    shouldShowTour,
    completeWelcome,
    completeSetup,
    completeTour,
    skipOnboarding,
  } = useOnboarding();

  // Check backend availability after app is ready


  const handleStartupError = (error: Error) => {
    // Parse error and create StartupErrorInfo
    const errorInfo: StartupErrorInfo = {
      type: 'unknown',
      message: error.message,
      cause: 'The application failed to start properly.',
      fixInstructions: [
        'Check that Python 3.10+ is installed',
        'Verify all dependencies are installed: pip install -r requirements.txt',
        'Ensure no other application is using port 8000',
        'Try restarting the application',
      ],
      technicalDetails: error.stack || error.message,
      timestamp: new Date(),
    };

    // Detect specific error types
    if (error.message.includes('Python') || error.message.includes('python')) {
      errorInfo.type = 'python_not_found';
      errorInfo.message = 'Python Not Found';
      errorInfo.cause = 'Python 3.10+ is required but not found on your system.';
      errorInfo.fixInstructions = [
        'Download and install Python 3.10 or later from python.org',
        'Make sure to check "Add Python to PATH" during installation',
        'Restart the application after installing Python',
      ];
    } else if (error.message.includes('port') || error.message.includes('EADDRINUSE')) {
      errorInfo.type = 'port_conflict';
      errorInfo.message = 'Port Already in Use';
      errorInfo.cause = 'Another application is using port 8000.';
      errorInfo.fixInstructions = [
        'Close any other applications using port 8000',
        'The application will automatically try alternative ports',
        'Click Retry to attempt startup again',
      ];
    } else if (error.message.includes('module') || error.message.includes('package')) {
      errorInfo.type = 'missing_packages';
      errorInfo.message = 'Missing Python Packages';
      errorInfo.cause = 'Required Python packages are not installed.';
      errorInfo.fixInstructions = [
        'Click "Install Dependencies" to install required packages',
        'Or manually run: pip install -r backend/requirements.txt',
        'Restart the application after installation',
      ];
    } else if (error.message.includes('Backend') || error.message.includes('backend')) {
      errorInfo.type = 'backend_crash';
      errorInfo.message = 'Backend Service Failed';
      errorInfo.cause = 'The backend service crashed during startup.';
      errorInfo.fixInstructions = [
        'Check the logs for detailed error information',
        'Verify all dependencies are installed correctly',
        'Try restarting the application',
        'If the problem persists, report it on GitHub',
      ];
    }

    setStartupError(errorInfo);
  };

  const handleRetry = () => {
    setStartupError(null);
    setIsAppReady(false);
    // Force reload to retry startup
    window.location.reload();
  };

  const handleViewLogs = async () => {
    try {
      if (window.electron) {
        await window.electron.invoke('open-log-file');
      }
    } catch (error) {
      console.error('Failed to open log file:', error);
    }
  };

  // Show startup error screen if there's an error
  if (startupError) {
    return (
      <StartupError
        error={startupError}
        onRetry={handleRetry}
        onViewLogs={handleViewLogs}
      />
    );
  }

  // Show splash screen during startup
  if (!isAppReady) {
    return (
      <SplashScreen
        onComplete={() => {
          const backendStatus = sessionStorage.getItem('backendAvailable');
          setIsBackendAvailable(backendStatus === 'true');
          setIsAppReady(true);
        }}
        onError={handleStartupError}
      />
    );
  }

  // Show onboarding screens
  if (shouldShowOnboarding) {
    return (
      <Suspense fallback={<LoadingFallback />}>
        <WelcomeScreen
          onGetStarted={completeWelcome}
          onSkip={skipOnboarding}
        />
      </Suspense>
    );
  }

  if (shouldShowSetup) {
    return (
      <Suspense fallback={<LoadingFallback />}>
        <SetupWizard
          onComplete={completeSetup}
          onSkip={skipOnboarding}
        />
      </Suspense>
    );
  }

  return (
    <Layout>
      <Suspense fallback={<LoadingFallback />}>
        {/* Show backend unavailable banner if needed */}
        {!isBackendAvailable && <BackendUnavailableBanner />}

        {/* Navigation */}
        <div className="bg-white border-b px-6 py-3">
          <div className="flex gap-4">
            <button
              onClick={() => setCurrentView('dashboard')}
              className={`px-4 py-2 rounded-lg transition-colors ${currentView === 'dashboard'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setCurrentView('training')}
              className={`px-4 py-2 rounded-lg transition-colors ${currentView === 'training'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
            >
              Training
            </button>
            <button
              onClick={() => setCurrentView('deployment')}
              className={`px-4 py-2 rounded-lg transition-colors ${currentView === 'deployment'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
            >
              Deployments
            </button>
            <button
              onClick={() => setCurrentView('gradio-demos')}
              className={`px-4 py-2 rounded-lg transition-colors ${currentView === 'gradio-demos'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
            >
              Gradio Demos
            </button>
            <button
              onClick={() => setCurrentView('inference')}
              className={`px-4 py-2 rounded-lg transition-colors ${currentView === 'inference'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
            >
              Inference
            </button>
            <button
              onClick={() => setCurrentView('configurations')}
              className={`px-4 py-2 rounded-lg transition-colors ${currentView === 'configurations'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
            >
              Configurations
            </button>
            <button
              onClick={() => setCurrentView('logging')}
              className={`px-4 py-2 rounded-lg transition-colors ${currentView === 'logging'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
            >
              Logging
            </button>
          </div>
        </div>

        {/* Main Content */}
        {currentView === 'dashboard' && <Dashboard />}

        {currentView === 'training' && (
          <TrainingWizard
            onComplete={(state) => {
              console.log('Training wizard completed:', state);
              setCurrentView('dashboard');
            }}
            onCancel={() => setCurrentView('dashboard')}
          />
        )}

        {currentView === 'deployment' && <DeploymentManagement />}

        {currentView === 'gradio-demos' && <GradioDemoGenerator />}

        {currentView === 'inference' && <InferencePlayground />}

        {currentView === 'configurations' && <ConfigurationManagement />}

        {currentView === 'logging' && <LoggingDiagnostics />}

        {/* Global Help Panel */}
        {isHelpOpen && (
          <ContextualHelpPanel
            isOpen={isHelpOpen}
            onClose={closeHelp}
            currentContext={currentContext}
          />
        )}

        {/* Guided Tour */}
        {shouldShowTour && (
          <GuidedTour
            isActive={shouldShowTour}
            onComplete={completeTour}
            onSkip={skipOnboarding}
          />
        )}
      </Suspense>

      {/* Performance Profiler (development only) */}
      <PerformanceProfiler enabled={process.env.NODE_ENV === 'development'} />

      {/* Auto-update notification */}
      <UpdateNotification />
    </Layout>
  );
}

export default App;
