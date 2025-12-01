/**
 * Telemetry Consent Component
 * 
 * Provides UI for users to opt-in/opt-out of telemetry collection
 * and view what data is collected.
 * 
 * Requirements: 15.5
 */

import React, { useState, useEffect } from 'react';

interface ConsentStatus {
  enabled: boolean;
  user_id: string;
  last_prompt: string | null;
  data_collected: string[];
  data_not_collected: string[];
}

export const TelemetryConsent: React.FC = () => {
  const [consentStatus, setConsentStatus] = useState<ConsentStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    fetchConsentStatus();
  }, []);

  const fetchConsentStatus = async () => {
    try {
      const response = await fetch('/api/telemetry/consent');
      const data = await response.json();
      setConsentStatus(data);
    } catch (error) {
      console.error('Failed to fetch consent status:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateConsent = async (enabled: boolean) => {
    setUpdating(true);
    try {
      const response = await fetch('/api/telemetry/consent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ enabled }),
      });

      if (response.ok) {
        await fetchConsentStatus();
      }
    } catch (error) {
      console.error('Failed to update consent:', error);
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!consentStatus) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-800">Failed to load telemetry settings</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Telemetry Settings</h2>
        <p className="mt-2 text-gray-600">
          Help us improve PEFT Studio by sharing anonymous usage data
        </p>
      </div>

      {/* Current Status */}
      <div className={`p-4 rounded-lg border-2 ${
        consentStatus.enabled 
          ? 'bg-green-50 border-green-200' 
          : 'bg-gray-50 border-gray-200'
      }`}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Telemetry is {consentStatus.enabled ? 'Enabled' : 'Disabled'}
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              {consentStatus.enabled 
                ? 'Thank you for helping us improve!' 
                : 'You can enable telemetry to help us improve the application'}
            </p>
          </div>
          <button
            onClick={() => updateConsent(!consentStatus.enabled)}
            disabled={updating}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              consentStatus.enabled
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {updating ? 'Updating...' : consentStatus.enabled ? 'Disable' : 'Enable'}
          </button>
        </div>
      </div>

      {/* What We Collect */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="w-full flex items-center justify-between text-left"
        >
          <h3 className="text-lg font-semibold text-gray-900">
            What data do we collect?
          </h3>
          <svg
            className={`w-5 h-5 text-gray-500 transition-transform ${
              showDetails ? 'transform rotate-180' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>

        {showDetails && (
          <div className="mt-4 space-y-4">
            {/* Data Collected */}
            <div>
              <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                <svg
                  className="w-5 h-5 text-green-600 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                Data We Collect (Anonymized)
              </h4>
              <ul className="space-y-2 ml-7">
                {consentStatus.data_collected.map((item, index) => (
                  <li key={index} className="text-sm text-gray-600 flex items-start">
                    <span className="text-green-600 mr-2">•</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            {/* Data NOT Collected */}
            <div>
              <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                <svg
                  className="w-5 h-5 text-red-600 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                Data We Never Collect
              </h4>
              <ul className="space-y-2 ml-7">
                {consentStatus.data_not_collected.map((item, index) => (
                  <li key={index} className="text-sm text-gray-600 flex items-start">
                    <span className="text-red-600 mr-2">•</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Privacy Information */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <svg
            className="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">Your Privacy Matters</p>
            <p>
              All telemetry data is anonymized before collection. We never collect
              personal information, API keys, or sensitive data. You can export or
              delete your data at any time.
            </p>
          </div>
        </div>
      </div>

      {/* Anonymous ID */}
      {consentStatus.enabled && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-2">
            Your Anonymous ID
          </h4>
          <code className="text-xs text-gray-600 bg-white px-2 py-1 rounded border border-gray-300">
            {consentStatus.user_id}
          </code>
          <p className="text-xs text-gray-500 mt-2">
            This ID is used to group your telemetry data and is not linked to any
            personal information.
          </p>
        </div>
      )}
    </div>
  );
};

export default TelemetryConsent;
