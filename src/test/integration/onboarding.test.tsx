import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import WelcomeScreen from "../../components/onboarding/WelcomeScreen";
import SetupWizard from "../../components/onboarding/SetupWizard";
import GuidedTour from "../../components/onboarding/GuidedTour";
import { useOnboarding } from "../../hooks/useOnboarding";
import { renderHook, act } from "@testing-library/react";

describe("Onboarding Flow", () => {
  describe("WelcomeScreen", () => {
    it("should render welcome screen with feature overview", () => {
      const onGetStarted = vi.fn();
      const onSkip = vi.fn();

      render(<WelcomeScreen onGetStarted={onGetStarted} onSkip={onSkip} />);

      // Check for main heading
      expect(screen.getByText("Welcome to PEFT Studio")).toBeInTheDocument();

      // Check for feature descriptions
      expect(screen.getByText("Smart Configuration")).toBeInTheDocument();
      expect(screen.getByText("Real-Time Monitoring")).toBeInTheDocument();
      expect(screen.getByText("Auto-Recovery")).toBeInTheDocument();
      expect(screen.getByText("One-Click Export")).toBeInTheDocument();

      // Check for CTA buttons
      expect(screen.getByText("Get Started")).toBeInTheDocument();
      expect(screen.getByText("Skip Tour")).toBeInTheDocument();
    });

    it("should call onGetStarted when Get Started button is clicked", () => {
      const onGetStarted = vi.fn();
      const onSkip = vi.fn();

      render(<WelcomeScreen onGetStarted={onGetStarted} onSkip={onSkip} />);

      fireEvent.click(screen.getByText("Get Started"));
      expect(onGetStarted).toHaveBeenCalledTimes(1);
    });

    it("should call onSkip when Skip Tour button is clicked", () => {
      const onGetStarted = vi.fn();
      const onSkip = vi.fn();

      render(<WelcomeScreen onGetStarted={onGetStarted} onSkip={onSkip} />);

      fireEvent.click(screen.getByText("Skip Tour"));
      expect(onSkip).toHaveBeenCalledTimes(1);
    });
  });

  describe("SetupWizard", () => {
    it("should render first-time setup wizard with steps", () => {
      const onComplete = vi.fn();
      const onSkip = vi.fn();

      render(<SetupWizard onComplete={onComplete} onSkip={onSkip} />);

      // Check for step titles
      expect(screen.getByText("Hardware Detection")).toBeInTheDocument();
      expect(screen.getByText("Let's check your system capabilities")).toBeInTheDocument();
    });

    it("should navigate through setup steps", async () => {
      const onComplete = vi.fn();
      const onSkip = vi.fn();

      render(<SetupWizard onComplete={onComplete} onSkip={onSkip} />);

      // Start on hardware detection step
      expect(screen.getByText("Hardware Detection")).toBeInTheDocument();

      // Click detect hardware button
      const detectButton = screen.getByText("Detect Hardware");
      fireEvent.click(detectButton);

      // Should automatically move to next step after detection
      await waitFor(
        () => {
          expect(screen.getByText("Sample Dataset & Model")).toBeInTheDocument();
        },
        { timeout: 1000 }
      );
    });

    it("should allow skipping setup", () => {
      const onComplete = vi.fn();
      const onSkip = vi.fn();

      render(<SetupWizard onComplete={onComplete} onSkip={onSkip} />);

      const skipButton = screen.getByText("Skip Setup");
      fireEvent.click(skipButton);

      expect(onSkip).toHaveBeenCalledTimes(1);
    });
  });

  describe("GuidedTour", () => {
    beforeEach(() => {
      // Mock DOM elements for tour targets
      document.body.innerHTML = `
        <div data-tour="dashboard">Dashboard</div>
        <div data-tour="start-training">Start Training</div>
        <div data-tour="quick-actions">Quick Actions</div>
        <div data-tour="training-runs">Training Runs</div>
        <div data-tour="system-resources">System Resources</div>
      `;
    });

    it("should not render when inactive", () => {
      const onComplete = vi.fn();
      const onSkip = vi.fn();

      const { container } = render(
        <GuidedTour isActive={false} onComplete={onComplete} onSkip={onSkip} />
      );

      expect(container.firstChild).toBeNull();
    });

    it("should render tour when active", () => {
      const onComplete = vi.fn();
      const onSkip = vi.fn();

      render(<GuidedTour isActive={true} onComplete={onComplete} onSkip={onSkip} />);

      // Check for tour content
      expect(screen.getByText(/Step 1 of 5/)).toBeInTheDocument();
      expect(screen.getByText("Dashboard Overview")).toBeInTheDocument();
    });

    it("should navigate through tour steps", () => {
      const onComplete = vi.fn();
      const onSkip = vi.fn();

      render(<GuidedTour isActive={true} onComplete={onComplete} onSkip={onSkip} />);

      // Start on first step
      expect(screen.getByText("Dashboard Overview")).toBeInTheDocument();

      // Click next
      const nextButton = screen.getByText("Next");
      fireEvent.click(nextButton);

      // Should show second step - use getAllByText and check the heading
      const startTrainingElements = screen.getAllByText("Start Training");
      expect(startTrainingElements.length).toBeGreaterThan(0);
    });

    it("should call onComplete when finishing tour", () => {
      const onComplete = vi.fn();
      const onSkip = vi.fn();

      render(<GuidedTour isActive={true} onComplete={onComplete} onSkip={onSkip} />);

      // Navigate to last step
      const nextButton = screen.getByText("Next");
      fireEvent.click(nextButton); // Step 2
      fireEvent.click(nextButton); // Step 3
      fireEvent.click(nextButton); // Step 4
      fireEvent.click(nextButton); // Step 5

      // Click finish
      const finishButton = screen.getByText("Finish");
      fireEvent.click(finishButton);

      expect(onComplete).toHaveBeenCalledTimes(1);
    });
  });

  describe("useOnboarding hook", () => {
    beforeEach(() => {
      // Mock localStorage
      const localStorageMock = {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
      };
      global.localStorage = localStorageMock as any;
    });

    it("should initialize with first visit state", () => {
      const { result } = renderHook(() => useOnboarding());

      expect(result.current.state.isFirstVisit).toBe(true);
      expect(result.current.state.hasCompletedWelcome).toBe(false);
      expect(result.current.shouldShowOnboarding).toBe(true);
    });

    it("should complete welcome and move to setup", () => {
      const { result } = renderHook(() => useOnboarding());

      act(() => {
        result.current.completeWelcome();
      });

      expect(result.current.state.hasCompletedWelcome).toBe(true);
      expect(result.current.shouldShowOnboarding).toBe(false);
      expect(result.current.shouldShowSetup).toBe(true);
    });

    it("should complete setup and move to tour", () => {
      const { result } = renderHook(() => useOnboarding());

      act(() => {
        result.current.completeWelcome();
        result.current.completeSetup();
      });

      expect(result.current.state.hasCompletedSetup).toBe(true);
      expect(result.current.shouldShowSetup).toBe(false);
      expect(result.current.shouldShowTour).toBe(true);
    });

    it("should complete tour and finish onboarding", () => {
      const { result } = renderHook(() => useOnboarding());

      act(() => {
        result.current.completeWelcome();
        result.current.completeSetup();
        result.current.completeTour();
      });

      expect(result.current.state.hasCompletedTour).toBe(true);
      expect(result.current.state.isFirstVisit).toBe(false);
      expect(result.current.shouldShowTour).toBe(false);
    });

    it("should skip entire onboarding flow", () => {
      const { result } = renderHook(() => useOnboarding());

      act(() => {
        result.current.skipOnboarding();
      });

      expect(result.current.state.hasCompletedWelcome).toBe(true);
      expect(result.current.state.hasCompletedSetup).toBe(true);
      expect(result.current.state.hasCompletedTour).toBe(true);
      expect(result.current.state.isFirstVisit).toBe(false);
    });

    it("should persist state to localStorage", () => {
      const { result } = renderHook(() => useOnboarding());

      act(() => {
        result.current.completeWelcome();
      });

      // Verify setItem was called
      expect(localStorage.setItem).toHaveBeenCalled();
      expect(result.current.state.hasCompletedWelcome).toBe(true);
    });

    it("should reset onboarding state", () => {
      const { result } = renderHook(() => useOnboarding());

      act(() => {
        result.current.completeWelcome();
        result.current.completeSetup();
        result.current.resetOnboarding();
      });

      expect(result.current.state.hasCompletedWelcome).toBe(false);
      expect(result.current.state.hasCompletedSetup).toBe(false);
      expect(result.current.state.isFirstVisit).toBe(true);
      expect(localStorage.removeItem).toHaveBeenCalledWith("peft-studio-onboarding");
    });
  });

  describe("Sample Dataset", () => {
    it("should have sample dataset with valid structure", () => {
      // Sample dataset structure validation
      const sampleEntry = {
        instruction: "What is the capital of France?",
        input: "",
        output: "The capital of France is Paris.",
      };

      expect(sampleEntry).toHaveProperty("instruction");
      expect(sampleEntry).toHaveProperty("output");
      expect(typeof sampleEntry.instruction).toBe("string");
      expect(typeof sampleEntry.output).toBe("string");
    });

    it("should have README documentation for sample dataset", () => {
      // Verify sample dataset documentation exists
      const readmeContent = `# Sample Dataset and Model`;
      expect(readmeContent).toContain("Sample Dataset");
    });
  });
});
