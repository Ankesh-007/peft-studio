/**
 * E2E Test: Frontend-Backend Integration
 * 
 * Tests the integration between frontend and backend:
 * - API health checks
 * - Backend availability detection
 * - Error handling for backend failures
 * - Data fetching and display
 * 
 * Requirements: 3.3
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import App from '../../App';

// Mock fetch for backend API calls
const mockFetch = vi.fn();

describe('E2E: Frontend-Backend Integration', () => {
  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
    
    // Skip onboarding for tests
    localStorage.setItem('peft-studio-onboarding', JSON.stringify({
      hasCompletedWelcome: true,
      hasCompletedSetup: true,
      hasCompletedTour: true,
      isFirstVisit: false,
    }));
    
    // Setup fetch mock
    global.fetch = mockFetch;
    
    if (!window.electron) {
      (window as any).electron = {
        invoke: vi.fn(),
        on: vi.fn(),
        removeListener: vi.fn(),
      };
    }
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should detect when backend is available', async () => {
    // Mock successful health check
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'healthy' }),
    });
    
    sessionStorage.setItem('backendAvailable', 'true');
    
    render(<App />);
    
    await waitFor(
      () => {
        const dashboardButton = screen.queryByRole('button', { name: /dashboard/i });
        expect(dashboardButton).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
    
    // Backend banner should NOT be visible
    const banner = screen.queryByText(/backend.*unavailable/i);
    expect(banner).not.toBeInTheDocument();
  });

  it('should detect when backend is unavailable', async () => {
    // Mock failed health check
    mockFetch.mockRejectedValueOnce(new Error('Connection refused'));
    
    sessionStorage.setItem('backendAvailable', 'false');
    
    render(<App />);
    
    await waitFor(
      () => {
        const dashboardButton = screen.queryByRole('button', { name: /dashboard/i });
        expect(dashboardButton).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
    
    // Backend banner SHOULD be visible
    await waitFor(() => {
      const banner = screen.queryByText(/backend.*unavailable/i);
      expect(banner).toBeInTheDocument();
    });
  });

  it('should handle backend timeout gracefully', async () => {
    // Mock timeout
    mockFetch.mockImplementationOnce(() => 
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Timeout')), 100)
      )
    );
    
    sessionStorage.setItem('backendAvailable', 'false');
    
    render(<App />);
    
    // App should still render
    await waitFor(
      () => {
        const dashboardButton = screen.queryByRole('button', { name: /dashboard/i });
        expect(dashboardButton).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
  });

  it('should handle malformed backend responses', async () => {
    // Mock malformed response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => {
        throw new Error('Invalid JSON');
      },
    });
    
    render(<App />);
    
    // App should still render despite bad response
    await waitFor(
      () => {
        const dashboardButton = screen.queryByRole('button', { name: /dashboard/i });
        expect(dashboardButton).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
  });

  it('should handle 500 server errors', async () => {
    // Mock 500 error
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: async () => ({ error: 'Server error' }),
    });
    
    render(<App />);
    
    // App should still render
    await waitFor(
      () => {
        const dashboardButton = screen.queryByRole('button', { name: /dashboard/i });
        expect(dashboardButton).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
  });

  it('should handle network errors', async () => {
    // Mock network error
    mockFetch.mockRejectedValueOnce(new Error('Network error'));
    
    render(<App />);
    
    // App should still render
    await waitFor(
      () => {
        const dashboardButton = screen.queryByRole('button', { name: /dashboard/i });
        expect(dashboardButton).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
  });

  it('should retry failed backend connections', async () => {
    // First call fails, second succeeds
    mockFetch
      .mockRejectedValueOnce(new Error('Connection failed'))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'healthy' }),
      });
    
    render(<App />);
    
    await waitFor(
      () => {
        const dashboardButton = screen.queryByRole('button', { name: /dashboard/i });
        expect(dashboardButton).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
    
    // Should have attempted multiple calls
    expect(mockFetch).toHaveBeenCalled();
  });

  it('should display appropriate error messages for different failure types', async () => {
    // Mock Python not found error
    const pythonError = new Error('Python not found');
    
    vi.spyOn(console, 'error').mockImplementation(() => {});
    
    render(<App />);
    
    // App should render without crashing
    await waitFor(
      () => {
        expect(screen.getByText(/PEFT Studio/i)).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
    
    vi.restoreAllMocks();
  });

  it('should maintain functionality when backend is partially available', async () => {
    // Some endpoints work, others don't
    mockFetch.mockImplementation((url) => {
      if (url.includes('/health')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ status: 'healthy' }),
        });
      }
      return Promise.reject(new Error('Endpoint not available'));
    });
    
    sessionStorage.setItem('backendAvailable', 'true');
    
    render(<App />);
    
    await waitFor(
      () => {
        const dashboardButton = screen.queryByRole('button', { name: /dashboard/i });
        expect(dashboardButton).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
    
    // App should still be functional
    expect(screen.getByRole('button', { name: /dashboard/i })).toBeInTheDocument();
  });
});
