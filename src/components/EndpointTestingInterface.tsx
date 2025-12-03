/**
 * Endpoint Testing Interface
 * 
 * Interface for testing deployment endpoints with custom inputs.
 * Shows response, latency, and allows saving test cases.
 * 
 * Requirements: 9.4
 */

import React, { useState } from 'react';

interface TestResult {
  success: boolean;
  response?: any;
  error?: string;
  latency_ms?: number;
  timestamp: string;
}

interface EndpointTestingInterfaceProps {
  deploymentId: string;
  deploymentName: string;
  endpointUrl: string;
  onClose: () => void;
}

export const EndpointTestingInterface: React.FC<EndpointTestingInterfaceProps> = ({
  deploymentId,
  deploymentName,
  endpointUrl,
  onClose
}) => {
  const [testInput, setTestInput] = useState({
    prompt: 'Hello, how are you?',
    max_tokens: 100,
    temperature: 0.7,
    top_p: 0.9
  });
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [testing, setTesting] = useState(false);
  const [testHistory, setTestHistory] = useState<TestResult[]>([]);

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      const response = await fetch(`/api/deployments/${deploymentId}/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input_data: testInput })
      });

      const result = await response.json();
      setTestResult(result);
      setTestHistory(prev => [result, ...prev].slice(0, 10)); // Keep last 10 tests
    } catch (error) {
      setTestResult({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      });
    } finally {
      setTesting(false);
    }
  };

  const formatJson = (obj: any) => {
    try {
      return JSON.stringify(obj, null, 2);
    } catch {
      return String(obj);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">Test Endpoint</h2>
              <p className="text-gray-600 mt-1">{deploymentName}</p>
              <p className="text-sm text-blue-600 mt-1">{endpointUrl}</p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Input Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Test Input</h3>
              
              <div>
                <label className="block text-sm font-medium mb-2">Prompt</label>
                <textarea
                  value={testInput.prompt}
                  onChange={e => setTestInput({ ...testInput, prompt: e.target.value })}
                  rows={4}
                  className="w-full px-4 py-2 border rounded-lg"
                  placeholder="Enter your prompt..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Max Tokens</label>
                  <input
                    type="number"
                    value={testInput.max_tokens}
                    onChange={e => setTestInput({ ...testInput, max_tokens: parseInt(e.target.value) })}
                    min="1"
                    max="4096"
                    className="w-full px-4 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Temperature</label>
                  <input
                    type="number"
                    value={testInput.temperature}
                    onChange={e => setTestInput({ ...testInput, temperature: parseFloat(e.target.value) })}
                    min="0"
                    max="2"
                    step="0.1"
                    className="w-full px-4 py-2 border rounded-lg"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Top P</label>
                <input
                  type="number"
                  value={testInput.top_p}
                  onChange={e => setTestInput({ ...testInput, top_p: parseFloat(e.target.value) })}
                  min="0"
                  max="1"
                  step="0.1"
                  className="w-full px-4 py-2 border rounded-lg"
                />
              </div>

              <button
                onClick={handleTest}
                disabled={testing || !testInput.prompt}
                className="w-full px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {testing ? 'Testing...' : 'Send Test Request'}
              </button>
            </div>

            {/* Output Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Response</h3>
              
              {testResult ? (
                <div className="space-y-4">
                  {testResult.success ? (
                    <>
                      <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                        <div className="flex items-center gap-2 text-green-800 mb-2">
                          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span className="font-semibold">Success</span>
                        </div>
                        <div className="text-sm">
                          <strong>Latency:</strong> {testResult.latency_ms?.toFixed(2)}ms
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-2">Response Data</label>
                        <pre className="p-4 bg-gray-50 rounded-lg overflow-x-auto text-sm">
                          {formatJson(testResult.response)}
                        </pre>
                      </div>
                    </>
                  ) : (
                    <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                      <div className="flex items-center gap-2 text-red-800 mb-2">
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                        <span className="font-semibold">Error</span>
                      </div>
                      <p className="text-sm text-red-800">{testResult.error}</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-8 text-center text-gray-500 border-2 border-dashed rounded-lg">
                  <p>No test results yet</p>
                  <p className="text-sm mt-2">Send a test request to see the response</p>
                </div>
              )}
            </div>
          </div>

          {/* Test History */}
          {testHistory.length > 0 && (
            <div className="mt-8">
              <h3 className="text-lg font-semibold mb-4">Recent Tests</h3>
              <div className="space-y-2">
                {testHistory.map((test, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg border ${
                      test.success
                        ? 'bg-green-50 border-green-200'
                        : 'bg-red-50 border-red-200'
                    }`}
                  >
                    <div className="flex items-center justify-between text-sm">
                      <span className={test.success ? 'text-green-800' : 'text-red-800'}>
                        {test.success ? '✓ Success' : '✗ Failed'}
                      </span>
                      <span className="text-gray-600">
                        {test.latency_ms ? `${test.latency_ms.toFixed(2)}ms` : 'N/A'}
                      </span>
                      <span className="text-gray-600">
                        {new Date(test.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50">
          <div className="flex justify-end gap-4">
            <button
              onClick={onClose}
              className="px-6 py-2 border rounded-lg hover:bg-gray-100"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
