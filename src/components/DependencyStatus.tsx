import React, { useEffect, useState, useCallback } from 'react';
import { CheckCircle, XCircle, AlertCircle, RefreshCw, Info } from 'lucide-react';

interface DependencyCheck {
  name: string;
  required: boolean;
  installed: boolean;
  version?: string;
  expected_version?: string;
  error?: string;
  fix_instructions?: string;
}

interface DependencyReport {
  all_passed: boolean;
  checks: DependencyCheck[];
  recommendations: string[];
  timestamp: string;
}

interface DependencyStatusProps {
  onComplete: () => void;
  onError?: (error: string) => void;
}

export const DependencyStatus: React.FC<DependencyStatusProps> = ({
  onComplete,
  onError,
}) => {
  const [report, setReport] = useState<DependencyReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkDependencies = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/dependencies/check', {
        signal: AbortSignal.timeout(10000),
      });

      if (!response.ok) {
        throw new Error(`Failed to check dependencies: ${response.statusText}`);
      }

      const data: DependencyReport = await response.json();
      setReport(data);

      // If all required dependencies passed, complete after a short delay
      if (data.all_passed) {
        setTimeout(() => {
          onComplete();
        }, 1500);
      } else {
        // Notify parent of error
        const failedRequired = data.checks.filter(
          (check) => check.required && (!check.installed || check.error)
        );
        if (failedRequired.length > 0 && onError) {
          onError(
            `Missing required dependencies: ${failedRequired.map((c) => c.name).join(', ')}`
          );
        }
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to check dependencies';
      setError(errorMessage);
      if (onError) {
        onError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  }, [onComplete, onError]);

  useEffect(() => {
    checkDependencies();
  }, [checkDependencies]);

  const getStatusIcon = (check: DependencyCheck) => {
    if (!check.installed) {
      return <XCircle className="w-5 h-5 text-red-500" />;
    }
    if (check.error) {
      return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    }
    return <CheckCircle className="w-5 h-5 text-green-500" />;
  };

  const getStatusColor = (check: DependencyCheck) => {
    if (!check.installed) return 'border-red-500 bg-red-500/10';
    if (check.error) return 'border-yellow-500 bg-yellow-500/10';
    return 'border-green-500 bg-green-500/10';
  };

  if (loading && !report) {
    return (
      <div className="fixed inset-0 bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center z-50">
        <div className="text-center">
          <div className="mb-8">
            <div className="w-24 h-24 mx-auto bg-white rounded-2xl flex items-center justify-center shadow-2xl">
              <span className="text-4xl font-bold text-blue-600">PS</span>
            </div>
          </div>
          <h2 className="text-2xl font-bold text-white mb-4">
            Checking Dependencies
          </h2>
          <div className="flex justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error && !report) {
    return (
      <div className="fixed inset-0 bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center z-50">
        <div className="max-w-2xl mx-auto p-6">
          <div className="bg-red-500/20 border-2 border-red-500 rounded-lg p-6">
            <div className="flex items-start gap-4">
              <XCircle className="w-8 h-8 text-red-400 flex-shrink-0 mt-1" />
              <div className="flex-1">
                <h2 className="text-xl font-bold text-white mb-2">
                  Connection Error
                </h2>
                <p className="text-red-200 mb-4">{error}</p>
                <button
                  onClick={checkDependencies}
                  className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors flex items-center gap-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  Retry
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!report) return null;

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center z-50 overflow-y-auto">
      <div className="max-w-4xl w-full mx-auto p-6 my-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="mb-4">
            <div className="w-20 h-20 mx-auto bg-white rounded-2xl flex items-center justify-center shadow-2xl">
              <span className="text-3xl font-bold text-blue-600">PS</span>
            </div>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">
            Dependency Verification
          </h1>
          <p className="text-blue-200">
            Checking system requirements for PEFT Studio
          </p>
        </div>

        {/* Overall Status */}
        <div
          className={`mb-6 p-4 rounded-lg border-2 ${
            report.all_passed
              ? 'bg-green-500/20 border-green-500'
              : 'bg-yellow-500/20 border-yellow-500'
          }`}
        >
          <div className="flex items-center gap-3">
            {report.all_passed ? (
              <CheckCircle className="w-6 h-6 text-green-400" />
            ) : (
              <AlertCircle className="w-6 h-6 text-yellow-400" />
            )}
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-white">
                {report.all_passed
                  ? 'All Required Dependencies Met'
                  : 'Some Dependencies Need Attention'}
              </h3>
              {!report.all_passed && (
                <p className="text-sm text-gray-200 mt-1">
                  Please resolve the issues below before continuing
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Dependency Checks */}
        <div className="bg-white/10 rounded-lg p-6 mb-6 backdrop-blur-sm">
          <h3 className="text-lg font-semibold text-white mb-4">
            Dependency Status
          </h3>
          <div className="space-y-3">
            {report.checks.map((check, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border-2 ${getStatusColor(check)}`}
              >
                <div className="flex items-start gap-3">
                  {getStatusIcon(check)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold text-white">{check.name}</h4>
                      {check.required && (
                        <span className="px-2 py-0.5 bg-red-500/30 text-red-200 text-xs rounded">
                          Required
                        </span>
                      )}
                      {!check.required && (
                        <span className="px-2 py-0.5 bg-blue-500/30 text-blue-200 text-xs rounded">
                          Optional
                        </span>
                      )}
                    </div>

                    {check.installed && check.version && (
                      <p className="text-sm text-gray-300 mb-1">
                        Version: {check.version}
                        {check.expected_version && (
                          <span className="text-gray-400">
                            {' '}
                            (expected: {check.expected_version})
                          </span>
                        )}
                      </p>
                    )}

                    {check.error && (
                      <p className="text-sm text-yellow-200 mb-2">
                        ⚠️ {check.error}
                      </p>
                    )}

                    {check.fix_instructions && (
                      <div className="mt-2 p-3 bg-black/20 rounded border border-white/10">
                        <div className="flex items-start gap-2">
                          <Info className="w-4 h-4 text-blue-300 flex-shrink-0 mt-0.5" />
                          <div className="flex-1">
                            <p className="text-xs font-semibold text-blue-200 mb-1">
                              How to fix:
                            </p>
                            <p className="text-xs text-gray-300 whitespace-pre-line">
                              {check.fix_instructions}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recommendations */}
        {report.recommendations.length > 0 && (
          <div className="bg-blue-500/20 border-2 border-blue-500 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
              <Info className="w-5 h-5" />
              Recommendations
            </h3>
            <ul className="space-y-2">
              {report.recommendations.map((rec, index) => (
                <li key={index} className="text-sm text-blue-100 flex gap-2">
                  <span className="text-blue-300">•</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-4 justify-center">
          <button
            onClick={checkDependencies}
            disabled={loading}
            className="px-6 py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500 text-white rounded-lg transition-colors flex items-center gap-2 font-semibold"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Checking...' : 'Retry Check'}
          </button>

          {report.all_passed && (
            <button
              onClick={onComplete}
              className="px-6 py-3 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors font-semibold"
            >
              Continue to Application
            </button>
          )}
        </div>

        {/* Timestamp */}
        <div className="text-center mt-6">
          <p className="text-xs text-blue-300">
            Last checked: {new Date(report.timestamp).toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
};

export default DependencyStatus;
