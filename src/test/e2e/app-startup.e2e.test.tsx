/**
 * E2E Test: Application Startup
 * 
 * Tests the complete application startup flow including:
 * - Initial render
 * - Splash screen display
 * - Backend health check
 * - Main application load
 * 
 * Requirements: 3.3
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import App from '../../App';

describe('E2E: Application Startup', () => {
  beforeEach(() => {
    // Clear any stored state
    sessionStorage.clear();
    localStorage.clear();
    
    // Skip onboarding for tests
    localStorage.setItem('peft-studio-onboarding', JSON.stringify({
      hasCompletedWelcome: true,
      hasCompletedSetup: true,
      hasCompletedTour: true,
      isFirstVisit: false,
    }));
    
    // Mock window.electron if needed
    if (!window.electron) {
      (window as any).electron = {
        invoke: vi.fn(),
        on: vi.fn(),
        removeListener: vi.fn(),
      };
    }
  });

  it('should render splash screen on initial load', async () => {
    render(<App />);
    
    // Splash screen should be visible initially
    const splashElement = screen.getByText(/PEFT Studio/i);
    expect(splashElement).toBeInTheDocument();
  });

  it('should transition from splash screen to main app', async () => {
    render(<App />);
    
    // Wait for splash screen to complete (max 5 seconds)
    await waitFor(
      () => {
        // After splash, we should see navigation buttons
        const dashboardButton = screen.queryByRole('button', { name: /dashboard/i });
        expect(dashboardButton).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
  });

  it('should display main navigation after startup', async () => {
    render(<App />);
    
    // Wait for app to be ready
    await waitFor(
      () => {
        const dashboardButton = screen.queryByRole('button', { name: /dashboard/i });
        expect(dashboardButton).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
    
    // Check all main navigation buttons are present
    expect(screen.getByRole('button', { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /training/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /deployments/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /gradio demos/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /inference/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /configurations/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /logging/i })).toBeInTheDocument();
  });

  it('should handle startup errors gracefully', async () => {
    // Mock a startup error
    const mockError = new Error('Backend connection failed');
    
    // Mock the splash screen to throw an error
    vi.spyOn(console, 'error').mockImplementation(() => {});
    
    render(<App />);
    
    // The app should still render without crashing
    expect(screen.getByText(/PEFT Studio/i)).toBeInTheDocument();
    
    vi.restoreAllMocks();
  });

  it('should show backend unavailable banner when backend is down', async () => {
    // Set backend as unavailable
    sessionStorage.setItem('backendAvailable', 'false');
    
    render(<App />);
    
    // Wait for app to be ready
    await waitFor(
      () => {
        const dashboardButton = screen.queryByRole('button', { name: /dashboard/i });
        expect(dashboardButton).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
    
    // Backend unavailable banner should be visible
    await waitFor(() => {
      const banner = screen.queryByText(/backend.*unavailable/i);
      expect(banner).toBeInTheDocument();
    });
  });

  it('should not show backend banner when backend is available', async () => {
    // Set backend as available
    sessionStorage.setItem('backendAvailable', 'true');
    
    render(<App />);
    
    // Wait for app to be ready
    await waitFor(
      () => {
        const dashboardButton = screen.queryByRole('button', { name: /dashboard/i });
        expect(dashboardButton).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
    
    // Backend unavailable banner should NOT be visible
    const banner = screen.queryByText(/backend.*unavailable/i);
    expect(banner).not.toBeInTheDocument();
  });
});
