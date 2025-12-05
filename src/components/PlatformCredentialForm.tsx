import React, { useState } from "react";

interface Platform {
  name: string;
  display_name: string;
  description: string;
  required_credentials: string[];
}

interface PlatformCredentialFormProps {
  platform: Platform;
  isEditing: boolean;
  onSubmit: (credentials: Record<string, string>) => void;
  onCancel: () => void;
}

/**
 * Platform Credential Form Component
 *
 * Modal form for entering platform credentials.
 * Validates: Requirements 1.2, 1.3
 */
export const PlatformCredentialForm: React.FC<PlatformCredentialFormProps> = ({
  platform,
  isEditing,
  onSubmit,
  onCancel,
}) => {
  const [credentials, setCredentials] = useState<Record<string, string>>({});
  const [showPassword, setShowPassword] = useState<Record<string, boolean>>({});
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  const handleInputChange = (key: string, value: string) => {
    setCredentials((prev) => ({ ...prev, [key]: value }));
    setTestResult(null); // Clear test result when credentials change
  };

  const togglePasswordVisibility = (key: string) => {
    setShowPassword((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      const response = await fetch("http://localhost:8000/api/platforms/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          platform_name: platform.name,
          credentials,
        }),
      });

      const result = await response.json();

      if (result.success) {
        setTestResult({
          success: true,
          message: `Connection successful! (${result.test_time_seconds.toFixed(2)}s)`,
        });
      } else {
        setTestResult({
          success: false,
          message: result.error || "Connection test failed",
        });
      }
    } catch (err) {
      setTestResult({
        success: false,
        message: err instanceof Error ? err.message : "Failed to test connection",
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Validate all required credentials are provided
    const missingCredentials = platform.required_credentials.filter(
      (key) => !credentials[key] || credentials[key].trim() === ""
    );

    if (missingCredentials.length > 0) {
      alert(`Please provide: ${missingCredentials.join(", ")}`);
      return;
    }

    onSubmit(credentials);
  };

  const formatCredentialLabel = (key: string): string => {
    return key
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const isPasswordField = (key: string): boolean => {
    const passwordKeywords = ["password", "secret", "key", "token"];
    return passwordKeywords.some((keyword) => key.toLowerCase().includes(keyword));
  };

  const allCredentialsProvided = platform.required_credentials.every(
    (key) => credentials[key] && credentials[key].trim() !== ""
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">
            {isEditing ? "Update" : "Connect to"} {platform.display_name}
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            {isEditing
              ? "Update your credentials for this platform"
              : "Enter your credentials to connect to this platform"}
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
          {platform.required_credentials.map((key) => (
            <div key={key}>
              <label htmlFor={key} className="block text-sm font-medium text-gray-700 mb-1">
                {formatCredentialLabel(key)}
                <span className="text-red-500 ml-1">*</span>
              </label>
              <div className="relative">
                <input
                  type={isPasswordField(key) && !showPassword[key] ? "password" : "text"}
                  id={key}
                  value={credentials[key] || ""}
                  onChange={(e) => handleInputChange(key, e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder={`Enter your ${formatCredentialLabel(key).toLowerCase()}`}
                  required
                />
                {isPasswordField(key) && (
                  <button
                    type="button"
                    onClick={() => togglePasswordVisibility(key)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showPassword[key] ? "👁️" : "👁️‍🗨️"}
                  </button>
                )}
              </div>
            </div>
          ))}

          {/* Test Result */}
          {testResult && (
            <div
              className={`p-3 rounded-lg ${
                testResult.success
                  ? "bg-green-50 border border-green-200"
                  : "bg-red-50 border border-red-200"
              }`}
            >
              <p className={`text-sm ${testResult.success ? "text-green-700" : "text-red-700"}`}>
                {testResult.success ? "✓" : "✗"} {testResult.message}
              </p>
            </div>
          )}

          {/* Security Notice */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-xs text-blue-700">
              <strong>🔒 Security:</strong> Your credentials are encrypted and stored securely in
              your system&apos;s keystore. They are never transmitted in plain text or logged.
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={handleTestConnection}
              disabled={!allCredentialsProvided || testing}
              className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {testing ? "Testing..." : "Test Connection"}
            </button>
            <button
              type="submit"
              disabled={!allCredentialsProvided}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isEditing ? "Update" : "Connect"}
            </button>
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
