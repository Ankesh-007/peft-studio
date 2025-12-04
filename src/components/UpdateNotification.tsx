import React, { useState, useEffect } from 'react';
import { Download, X, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

interface UpdateInfo {
  version: string;
  releaseNotes?: string;
  releaseDate?: string;
  checksumVerified?: boolean;
}

interface DownloadProgress {
  percent: number;
  bytesPerSecond: number;
  transferred: number;
  total: number;
}

type UpdateState = 
  | 'checking'
  | 'available'
  | 'downloading'
  | 'downloaded'
  | 'not-available'
  | 'error'
  | null;

export const UpdateNotification: React.FC = () => {
  const [updateState, setUpdateState] = useState<UpdateState>(null);
  const [updateInfo, setUpdateInfo] = useState<UpdateInfo | null>(null);
  const [downloadProgress, setDownloadProgress] = useState<DownloadProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<string | null>(null);
  const [showReleaseNotes, setShowReleaseNotes] = useState(false);
  const [currentVersion, setCurrentVersion] = useState<string>('');

  useEffect(() => {
    // Get current app version
    if (window.api?.getAppVersion) {
      window.api.getAppVersion().then((result: { version: string }) => {
        setCurrentVersion(result.version);
      });
    }

    // Listen for update events
    if (window.api?.onUpdateAvailable) {
      window.api.onUpdateAvailable((info: UpdateInfo) => {
        setUpdateState('available');
        setUpdateInfo(info);
      });
    }

    if (window.api?.onUpdateDownloadProgress) {
      window.api.onUpdateDownloadProgress((progress: DownloadProgress) => {
        setUpdateState('downloading');
        setDownloadProgress(progress);
      });
    }

    if (window.api?.onUpdateDownloaded) {
      window.api.onUpdateDownloaded((info: UpdateInfo) => {
        setUpdateState('downloaded');
        setUpdateInfo(info);
      });
    }

    if (window.api?.onUpdateStatus) {
      window.api.onUpdateStatus((data: { status: string; message?: string; type?: string }) => {
        if (data.status === 'error') {
          setUpdateState('error');
          setError(data.message || 'An error occurred while checking for updates');
          setErrorType(data.type || null);
        } else if (data.status === 'not-available') {
          setUpdateState('not-available');
          // Auto-hide after 3 seconds
          setTimeout(() => setUpdateState(null), 3000);
        }
      });
    }

    // Listen for checksum verification failures
    if (window.api?.onUpdateChecksumFailed) {
      window.api.onUpdateChecksumFailed((data: { message: string; severity: string }) => {
        setUpdateState('error');
        setError(data.message);
        setErrorType('checksum-mismatch');
      });
    }
  }, []);

  const handleDownload = async () => {
    if (!window.api?.downloadUpdate) return;
    
    try {
      setUpdateState('downloading');
      await window.api.downloadUpdate();
    } catch (err) {
      setError('Failed to download update');
      setUpdateState('error');
    }
  };

  const handleInstall = async () => {
    if (!window.api?.installUpdate) return;
    
    try {
      await window.api.installUpdate();
    } catch (err) {
      setError('Failed to install update');
      setUpdateState('error');
    }
  };

  const handleCheckForUpdates = async () => {
    if (!window.api?.checkForUpdates) return;
    
    try {
      setUpdateState('checking');
      setError(null);
      await window.api.checkForUpdates();
    } catch (err) {
      setError('Failed to check for updates');
      setUpdateState('error');
    }
  };

  const handleDismiss = () => {
    setUpdateState(null);
    setError(null);
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatSpeed = (bytesPerSecond: number): string => {
    return formatBytes(bytesPerSecond) + '/s';
  };

  if (!updateState) {
    return (
      <button
        onClick={handleCheckForUpdates}
        className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
      >
        Check for Updates
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-md">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            {updateState === 'checking' && (
              <>
                <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  Checking for Updates
                </h3>
              </>
            )}
            {updateState === 'available' && (
              <>
                <Download className="w-5 h-5 text-blue-500" />
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  Update Available
                </h3>
              </>
            )}
            {updateState === 'downloading' && (
              <>
                <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  Downloading Update
                </h3>
              </>
            )}
            {updateState === 'downloaded' && (
              <>
                <CheckCircle className="w-5 h-5 text-green-500" />
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  Update Ready
                </h3>
              </>
            )}
            {updateState === 'not-available' && (
              <>
                <CheckCircle className="w-5 h-5 text-green-500" />
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  Up to Date
                </h3>
              </>
            )}
            {updateState === 'error' && (
              <>
                <AlertCircle className="w-5 h-5 text-red-500" />
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  Update Error
                </h3>
              </>
            )}
          </div>
          <button
            onClick={handleDismiss}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="space-y-3">
          {updateState === 'checking' && (
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Checking for new versions...
            </p>
          )}

          {updateState === 'available' && updateInfo && (
            <>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                <p>Version {updateInfo.version} is available</p>
                {currentVersion && (
                  <p className="text-xs mt-1">Current version: {currentVersion}</p>
                )}
              </div>
              
              {updateInfo.releaseNotes && (
                <button
                  onClick={() => setShowReleaseNotes(!showReleaseNotes)}
                  className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  {showReleaseNotes ? 'Hide' : 'Show'} Release Notes
                </button>
              )}
              
              {showReleaseNotes && updateInfo.releaseNotes && (
                <div className="bg-gray-50 dark:bg-gray-900 rounded p-3 text-sm text-gray-700 dark:text-gray-300 max-h-48 overflow-y-auto">
                  <pre className="whitespace-pre-wrap font-sans">
                    {updateInfo.releaseNotes}
                  </pre>
                </div>
              )}
              
              <button
                onClick={handleDownload}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded transition-colors"
              >
                Download Update
              </button>
            </>
          )}

          {updateState === 'downloading' && downloadProgress && (
            <>
              <div className="space-y-2">
                <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                  <span>{Math.round(downloadProgress.percent)}%</span>
                  <span>{formatSpeed(downloadProgress.bytesPerSecond)}</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${downloadProgress.percent}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-500 dark:text-gray-500">
                  <span>{formatBytes(downloadProgress.transferred)}</span>
                  <span>{formatBytes(downloadProgress.total)}</span>
                </div>
              </div>
            </>
          )}

          {updateState === 'downloaded' && updateInfo && (
            <>
              <div className="space-y-2">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Version {updateInfo.version} has been downloaded and is ready to install.
                </p>
                {updateInfo.checksumVerified && (
                  <div className="flex items-center gap-2 text-xs text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 rounded p-2">
                    <CheckCircle className="w-4 h-4" />
                    <span>Update integrity verified via checksum</span>
                  </div>
                )}
              </div>
              <button
                onClick={handleInstall}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded transition-colors"
              >
                Install and Restart
              </button>
            </>
          )}

          {updateState === 'not-available' && (
            <p className="text-sm text-gray-600 dark:text-gray-400">
              You're running the latest version ({currentVersion})
            </p>
          )}

          {updateState === 'error' && (
            <>
              <div className={`text-sm rounded p-3 ${
                errorType === 'checksum-mismatch' 
                  ? 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800' 
                  : ''
              }`}>
                <p className={`${
                  errorType === 'checksum-mismatch' 
                    ? 'text-red-700 dark:text-red-300 font-medium' 
                    : 'text-red-600 dark:text-red-400'
                }`}>
                  {error || 'An error occurred'}
                </p>
                {errorType === 'checksum-mismatch' && (
                  <p className="text-xs text-red-600 dark:text-red-400 mt-2">
                    For your security, this update will not be installed. You can download manually from{' '}
                    <a 
                      href="https://github.com/Ankesh-007/peft-studio/releases" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="underline hover:text-red-700 dark:hover:text-red-300"
                    >
                      GitHub Releases
                    </a>.
                  </p>
                )}
              </div>
              {errorType !== 'checksum-mismatch' && (
                <button
                  onClick={handleCheckForUpdates}
                  className="w-full bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded transition-colors"
                >
                  Try Again
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
