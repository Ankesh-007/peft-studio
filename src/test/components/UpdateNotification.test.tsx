import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { UpdateNotification } from '../../components/UpdateNotification';

describe('UpdateNotification', () => {
  let mockApi: any;

  beforeEach(() => {
    // Mock window.api
    mockApi = {
      getAppVersion: vi.fn().mockResolvedValue({ version: '1.0.0' }),
      checkForUpdates: vi.fn().mockResolvedValue({ success: true }),
      downloadUpdate: vi.fn().mockResolvedValue({ success: true }),
      installUpdate: vi.fn().mockResolvedValue({ success: true }),
      onUpdateAvailable: vi.fn(),
      onUpdateDownloadProgress: vi.fn(),
      onUpdateDownloaded: vi.fn(),
      onUpdateStatus: vi.fn(),
    };

    (window as any).api = mockApi;
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should render check for updates button initially', () => {
    render(<UpdateNotification />);
    expect(screen.getByText('Check for Updates')).toBeInTheDocument();
  });

  it('should call getAppVersion on mount', async () => {
    render(<UpdateNotification />);
    await waitFor(() => {
      expect(mockApi.getAppVersion).toHaveBeenCalled();
    });
  });

  it('should register update event listeners on mount', () => {
    render(<UpdateNotification />);
    expect(mockApi.onUpdateAvailable).toHaveBeenCalled();
    expect(mockApi.onUpdateDownloadProgress).toHaveBeenCalled();
    expect(mockApi.onUpdateDownloaded).toHaveBeenCalled();
    expect(mockApi.onUpdateStatus).toHaveBeenCalled();
  });

  it('should show checking state when checking for updates', async () => {
    render(<UpdateNotification />);
    
    const checkButton = screen.getByText('Check for Updates');
    fireEvent.click(checkButton);

    await waitFor(() => {
      expect(screen.getByText('Checking for Updates')).toBeInTheDocument();
    });
  });

  it('should show update available notification', async () => {
    render(<UpdateNotification />);

    // Simulate update available event
    const updateAvailableCallback = mockApi.onUpdateAvailable.mock.calls[0][0];
    updateAvailableCallback({
      version: '1.0.1',
      releaseNotes: 'Bug fixes and improvements',
      releaseDate: '2024-01-01'
    });

    await waitFor(() => {
      expect(screen.getByText('Update Available')).toBeInTheDocument();
      expect(screen.getByText('Version 1.0.1 is available')).toBeInTheDocument();
    });
  });

  it('should show release notes when button clicked', async () => {
    render(<UpdateNotification />);

    // Simulate update available event
    const updateAvailableCallback = mockApi.onUpdateAvailable.mock.calls[0][0];
    updateAvailableCallback({
      version: '1.0.1',
      releaseNotes: 'Bug fixes and improvements',
    });

    await waitFor(() => {
      expect(screen.getByText('Show Release Notes')).toBeInTheDocument();
    });

    const showNotesButton = screen.getByText('Show Release Notes');
    fireEvent.click(showNotesButton);

    await waitFor(() => {
      expect(screen.getByText('Bug fixes and improvements')).toBeInTheDocument();
      expect(screen.getByText('Hide Release Notes')).toBeInTheDocument();
    });
  });

  it('should call downloadUpdate when download button clicked', async () => {
    render(<UpdateNotification />);

    // Simulate update available event
    const updateAvailableCallback = mockApi.onUpdateAvailable.mock.calls[0][0];
    updateAvailableCallback({
      version: '1.0.1',
    });

    await waitFor(() => {
      expect(screen.getByText('Download Update')).toBeInTheDocument();
    });

    const downloadButton = screen.getByText('Download Update');
    fireEvent.click(downloadButton);

    await waitFor(() => {
      expect(mockApi.downloadUpdate).toHaveBeenCalled();
    });
  });

  it('should show download progress', async () => {
    render(<UpdateNotification />);

    // Simulate download progress event
    const progressCallback = mockApi.onUpdateDownloadProgress.mock.calls[0][0];
    progressCallback({
      percent: 45,
      bytesPerSecond: 2500000,
      transferred: 45000000,
      total: 100000000
    });

    await waitFor(() => {
      expect(screen.getByText('Downloading Update')).toBeInTheDocument();
      expect(screen.getByText('45%')).toBeInTheDocument();
    });
  });

  it('should show update downloaded notification', async () => {
    render(<UpdateNotification />);

    // Simulate update downloaded event
    const downloadedCallback = mockApi.onUpdateDownloaded.mock.calls[0][0];
    downloadedCallback({
      version: '1.0.1',
      releaseNotes: 'Bug fixes'
    });

    await waitFor(() => {
      expect(screen.getByText('Update Ready')).toBeInTheDocument();
      expect(screen.getByText(/Version 1.0.1 has been downloaded/)).toBeInTheDocument();
      expect(screen.getByText('Install and Restart')).toBeInTheDocument();
    });
  });

  it('should call installUpdate when install button clicked', async () => {
    render(<UpdateNotification />);

    // Simulate update downloaded event
    const downloadedCallback = mockApi.onUpdateDownloaded.mock.calls[0][0];
    downloadedCallback({
      version: '1.0.1',
    });

    await waitFor(() => {
      expect(screen.getByText('Install and Restart')).toBeInTheDocument();
    });

    const installButton = screen.getByText('Install and Restart');
    fireEvent.click(installButton);

    await waitFor(() => {
      expect(mockApi.installUpdate).toHaveBeenCalled();
    });
  });

  it('should show error state', async () => {
    render(<UpdateNotification />);

    // Simulate error event
    const statusCallback = mockApi.onUpdateStatus.mock.calls[0][0];
    statusCallback({
      status: 'error',
      message: 'Network error'
    });

    await waitFor(() => {
      expect(screen.getByText('Update Error')).toBeInTheDocument();
      expect(screen.getByText('Network error')).toBeInTheDocument();
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });
  });

  it('should show not available state and auto-dismiss', async () => {
    vi.useFakeTimers();
    render(<UpdateNotification />);

    // Simulate not available event
    const statusCallback = mockApi.onUpdateStatus.mock.calls[0][0];
    await vi.waitFor(() => statusCallback({
      status: 'not-available'
    }));

    await vi.waitFor(() => {
      expect(screen.getByText('Up to Date')).toBeInTheDocument();
    });

    // Fast-forward time and run pending timers
    await vi.advanceTimersByTimeAsync(3000);

    await vi.waitFor(() => {
      expect(screen.queryByText('Up to Date')).not.toBeInTheDocument();
    });

    vi.useRealTimers();
  });

  it('should dismiss notification when X button clicked', async () => {
    render(<UpdateNotification />);

    // Simulate update available event
    const updateAvailableCallback = mockApi.onUpdateAvailable.mock.calls[0][0];
    await vi.waitFor(() => updateAvailableCallback({
      version: '1.0.1',
    }));

    await waitFor(() => {
      expect(screen.getByText('Update Available')).toBeInTheDocument();
    }, { timeout: 5000 });

    // Find and click the X button - it's the last button in the notification
    const buttons = screen.getAllByRole('button');
    const dismissButton = buttons[buttons.length - 1]; // X button is the last one
    fireEvent.click(dismissButton);

    await waitFor(() => {
      expect(screen.queryByText('Update Available')).not.toBeInTheDocument();
    }, { timeout: 5000 });
  }, 15000);

  it('should format bytes correctly', async () => {
    render(<UpdateNotification />);

    // Simulate download progress with various byte sizes
    const progressCallback = mockApi.onUpdateDownloadProgress.mock.calls[0][0];
    
    // Test MB formatting
    await vi.waitFor(() => progressCallback({
      percent: 50,
      bytesPerSecond: 2500000,
      transferred: 50000000,
      total: 100000000
    }));

    await waitFor(() => {
      // Check that MB formatting is present (multiple elements expected)
      const mbElements = screen.getAllByText(/MB/);
      expect(mbElements.length).toBeGreaterThan(0);
    }, { timeout: 5000 });
  }, 15000);

  it('should handle missing window.api gracefully', () => {
    (window as any).api = undefined;
    
    expect(() => render(<UpdateNotification />)).not.toThrow();
  });

  it('should show current version in update available notification', async () => {
    render(<UpdateNotification />);

    // Wait for version to load
    await waitFor(() => {
      expect(mockApi.getAppVersion).toHaveBeenCalled();
    }, { timeout: 5000 });

    // Simulate update available event
    const updateAvailableCallback = mockApi.onUpdateAvailable.mock.calls[0][0];
    await vi.waitFor(() => updateAvailableCallback({
      version: '1.0.1',
    }));

    await waitFor(() => {
      expect(screen.getByText('Current version: 1.0.0')).toBeInTheDocument();
    }, { timeout: 5000 });
  }, 15000);
});
