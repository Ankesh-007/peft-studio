import { useState, useEffect } from "react";

interface OnboardingState {
  hasCompletedWelcome: boolean;
  hasCompletedSetup: boolean;
  hasCompletedTour: boolean;
  isFirstVisit: boolean;
}

const ONBOARDING_KEY = "peft-studio-onboarding";

export const useOnboarding = () => {
  const [state, setState] = useState<OnboardingState>(() => {
    const stored = localStorage.getItem(ONBOARDING_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
    return {
      hasCompletedWelcome: false,
      hasCompletedSetup: false,
      hasCompletedTour: false,
      isFirstVisit: true,
    };
  });

  useEffect(() => {
    localStorage.setItem(ONBOARDING_KEY, JSON.stringify(state));
  }, [state]);

  const completeWelcome = () => {
    setState((prev) => ({ ...prev, hasCompletedWelcome: true }));
  };

  const completeSetup = () => {
    setState((prev) => ({ ...prev, hasCompletedSetup: true }));
  };

  const completeTour = () => {
    setState((prev) => ({
      ...prev,
      hasCompletedTour: true,
      isFirstVisit: false,
    }));
  };

  const skipOnboarding = () => {
    setState({
      hasCompletedWelcome: true,
      hasCompletedSetup: true,
      hasCompletedTour: true,
      isFirstVisit: false,
    });
  };

  const resetOnboarding = () => {
    setState({
      hasCompletedWelcome: false,
      hasCompletedSetup: false,
      hasCompletedTour: false,
      isFirstVisit: true,
    });
    localStorage.removeItem(ONBOARDING_KEY);
  };

  const shouldShowOnboarding = state.isFirstVisit && !state.hasCompletedWelcome;
  const shouldShowSetup = state.hasCompletedWelcome && !state.hasCompletedSetup;
  const shouldShowTour = state.hasCompletedSetup && !state.hasCompletedTour;

  return {
    state,
    completeWelcome,
    completeSetup,
    completeTour,
    skipOnboarding,
    resetOnboarding,
    shouldShowOnboarding,
    shouldShowSetup,
    shouldShowTour,
  };
};
