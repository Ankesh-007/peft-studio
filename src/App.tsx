import React, { useState } from "react";

import ContextualHelpPanel from "./components/ContextualHelpPanel";
import Dashboard from "./components/Dashboard";
import Layout from "./components/Layout";
import GuidedTour from "./components/onboarding/GuidedTour";
import SetupWizard from "./components/onboarding/SetupWizard";
import WelcomeScreen from "./components/onboarding/WelcomeScreen";
import TrainingWizard from "./components/TrainingWizard";
import { useHelpPanel } from "./hooks/useHelpPanel";
import { useOnboarding } from "./hooks/useOnboarding";

function App() {
  const [showWizard, setShowWizard] = useState(false);
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

  // Show onboarding screens
  if (shouldShowOnboarding) {
    return (
      <WelcomeScreen onGetStarted={completeWelcome} onSkip={skipOnboarding} />
    );
  }

  if (shouldShowSetup) {
    return <SetupWizard onComplete={completeSetup} onSkip={skipOnboarding} />;
  }

  return (
    <Layout>
      {showWizard ? (
        <TrainingWizard
          onComplete={(state) => {
            console.log("Training wizard completed:", state);
            setShowWizard(false);
          }}
          onCancel={() => setShowWizard(false)}
        />
      ) : (
        <>
          <Dashboard />
          <button
            onClick={() => setShowWizard(true)}
            data-tour="start-training"
            className="fixed bottom-6 right-6 px-6 py-3 bg-blue-600 text-white rounded-lg shadow-lg hover:bg-blue-700 transition-colors"
          >
            Start Training Wizard
          </button>
        </>
      )}

      {/* Global Help Panel */}
      <ContextualHelpPanel
        isOpen={isHelpOpen}
        onClose={closeHelp}
        currentContext={currentContext}
      />

      {/* Guided Tour */}
      <GuidedTour
        isActive={shouldShowTour}
        onComplete={completeTour}
        onSkip={skipOnboarding}
      />
    </Layout>
  );
}

export default App;
