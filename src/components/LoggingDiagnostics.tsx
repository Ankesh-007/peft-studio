/**
 * Logging and Diagnostics UI
 *
 * Comprehensive logging and diagnostics interface with:
 * - Log viewer with filtering
 * - Log search functionality
 * - Diagnostic report generator
 * - Debug mode toggle
 * - Log export functionality
 *
 * Validates: Requirements 19.1, 19.2, 19.3, 19.4, 19.5
 */

import React, { useState, useEffect, useMemo, useCallback } from "react";
import {
  Search,
  Filter,
  Download,
  Trash2,
  AlertCircle,
  AlertTriangle,
  Info,
  XCircle,
  FileText,
  Settings,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
} from "lucide-react";

// Types
interface LogEntry {
  timestamp: string;
  error_message: string;
  stack_trace: string;
  error_type: string;
  severity: "low" | "medium" | "high" | "critical";
  context?: Record<string, unknown>;
  recent_actions?: string[];
  system_state: {
    timestamp: string;
    platform: string;
    python_version: string;
    cpu_usage_percent: number;
    memory_usage_percent: number;
    gpu_info?: Record<string, unknown>;
    disk_usage_percent?: number;
    network_status?: string;
  };
}

interface LogStats {
  total_logs: number;
  by_severity: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  by_error_type: Record<string, number>;
  recent_actions_count: number;
}

interface DiagnosticReport {
  report_id: string;
  generated_at: string;
  error_count: number;
  download_url: string;
  file_path?: string;
}

const LoggingDiagnostics: React.FC = () => {
  // State
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const [errorTypeFilter, setErrorTypeFilter] = useState<string>("");
  const [expandedLogs, setExpandedLogs] = useState<Set<number>>(new Set());
  const [debugMode, setDebugMode] = useState(false);
  const [stats, setStats] = useState<LogStats | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  // Fetch logs
  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (severityFilter) params.append("severity", severityFilter);
      if (errorTypeFilter) params.append("error_type", errorTypeFilter);
      params.append("limit", "100");

      const response = await fetch(`http://localhost:8000/api/logging/logs?${params}`);
      const data = await response.json();
      setLogs(data.logs || []);
      setFilteredLogs(data.logs || []);
    } catch (error) {
      console.error("Failed to fetch logs:", error);
    } finally {
      setLoading(false);
    }
  }, [severityFilter, errorTypeFilter]);

  // Fetch stats
  const fetchStats = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/logging/stats");
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  };

  // Fetch debug mode status
  const fetchDebugMode = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/logging/debug-mode");
      const data = await response.json();
      setDebugMode(data.enabled);
    } catch (error) {
      console.error("Failed to fetch debug mode:", error);
    }
  };

  // Initial load
  useEffect(() => {
    fetchLogs();
    fetchStats();
    fetchDebugMode();
  }, [fetchLogs, severityFilter, errorTypeFilter]);

  // Search functionality
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredLogs(logs);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = logs.filter(
      (log) =>
        log.error_message.toLowerCase().includes(query) ||
        log.stack_trace.toLowerCase().includes(query) ||
        log.error_type.toLowerCase().includes(query) ||
        (log.context && JSON.stringify(log.context).toLowerCase().includes(query))
    );
    setFilteredLogs(filtered);
  }, [searchQuery, logs]);

  // Toggle log expansion
  const toggleLogExpansion = (index: number) => {
    const newExpanded = new Set(expandedLogs);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedLogs(newExpanded);
  };

  // Generate diagnostic report
  const generateDiagnosticReport = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/api/logging/diagnostic-report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const report: DiagnosticReport = await response.json();

      // Download the report
      const downloadUrl = `http://localhost:8000${report.download_url}`;
      window.open(downloadUrl, "_blank");

      alert(
        `Diagnostic report generated successfully!\nReport ID: ${report.report_id}\nErrors: ${report.error_count}`
      );
    } catch (error) {
      console.error("Failed to generate diagnostic report:", error);
      alert("Failed to generate diagnostic report");
    } finally {
      setLoading(false);
    }
  };

  // Export logs
  const exportLogs = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/api/logging/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const data = await response.json();

      alert(`Logs exported successfully!\nFile: ${data.filepath}\nLogs: ${data.log_count}`);
    } catch (error) {
      console.error("Failed to export logs:", error);
      alert("Failed to export logs");
    } finally {
      setLoading(false);
    }
  };

  // Clear logs
  const clearLogs = async () => {
    if (!confirm("Are you sure you want to clear all logs? This action cannot be undone.")) {
      return;
    }

    setLoading(true);
    try {
      await fetch("http://localhost:8000/api/logging/logs", {
        method: "DELETE",
      });
      setLogs([]);
      setFilteredLogs([]);
      fetchStats();
      alert("All logs cleared successfully");
    } catch (error) {
      console.error("Failed to clear logs:", error);
      alert("Failed to clear logs");
    } finally {
      setLoading(false);
    }
  };

  // Toggle debug mode
  const toggleDebugMode = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/api/logging/debug-mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: !debugMode }),
      });
      const data = await response.json();
      setDebugMode(data.enabled);
    } catch (error) {
      console.error("Failed to toggle debug mode:", error);
      alert("Failed to toggle debug mode");
    } finally {
      setLoading(false);
    }
  };

  // Copy to clipboard
  const copyToClipboard = async (text: string, index: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch (error) {
      console.error("Failed to copy:", error);
    }
  };

  // Get severity icon and color
  const getSeverityDisplay = (severity: string) => {
    switch (severity) {
      case "critical":
        return { icon: <XCircle className="w-5 h-5" />, color: "text-red-600", bg: "bg-red-50" };
      case "high":
        return {
          icon: <AlertCircle className="w-5 h-5" />,
          color: "text-orange-600",
          bg: "bg-orange-50",
        };
      case "medium":
        return {
          icon: <AlertTriangle className="w-5 h-5" />,
          color: "text-yellow-600",
          bg: "bg-yellow-50",
        };
      case "low":
        return { icon: <Info className="w-5 h-5" />, color: "text-blue-600", bg: "bg-blue-50" };
      default:
        return { icon: <Info className="w-5 h-5" />, color: "text-gray-600", bg: "bg-gray-50" };
    }
  };

  // Get unique error types
  const errorTypes = useMemo(() => {
    const types = new Set(logs.map((log) => log.error_type));
    return Array.from(types).sort();
  }, [logs]);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Logging & Diagnostics</h1>
        <p className="text-gray-600">
          View error logs, search for issues, and generate diagnostic reports
        </p>
      </div>

      {/* Stats Cards */}
      {stats && stats.by_severity && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600 mb-1">Total Logs</div>
            <div className="text-2xl font-bold text-gray-900">{stats.total_logs}</div>
          </div>
          <div className="bg-red-50 rounded-lg shadow p-4">
            <div className="text-sm text-red-600 mb-1">Critical</div>
            <div className="text-2xl font-bold text-red-700">{stats.by_severity.critical}</div>
          </div>
          <div className="bg-orange-50 rounded-lg shadow p-4">
            <div className="text-sm text-orange-600 mb-1">High</div>
            <div className="text-2xl font-bold text-orange-700">{stats.by_severity.high}</div>
          </div>
          <div className="bg-yellow-50 rounded-lg shadow p-4">
            <div className="text-sm text-yellow-600 mb-1">Medium</div>
            <div className="text-2xl font-bold text-yellow-700">{stats.by_severity.medium}</div>
          </div>
        </div>
      )}

      {/* Actions Bar */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-wrap items-center gap-3">
          {/* Search */}
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search logs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center gap-2"
          >
            <Filter className="w-4 h-4" />
            Filters
            {showFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {/* Debug Mode Toggle */}
          <button
            onClick={toggleDebugMode}
            disabled={loading}
            className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
              debugMode
                ? "bg-green-600 text-white hover:bg-green-700"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            <Settings className="w-4 h-4" />
            Debug Mode {debugMode ? "ON" : "OFF"}
          </button>

          {/* Refresh */}
          <button
            onClick={() => {
              fetchLogs();
              fetchStats();
            }}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>

          {/* Generate Report */}
          <button
            onClick={generateDiagnosticReport}
            disabled={loading}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2"
          >
            <FileText className="w-4 h-4" />
            Generate Report
          </button>

          {/* Export */}
          <button
            onClick={exportLogs}
            disabled={loading}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Export
          </button>

          {/* Clear */}
          <button
            onClick={clearLogs}
            disabled={loading}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2"
          >
            <Trash2 className="w-4 h-4" />
            Clear
          </button>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Severity Filter */}
              <div>
                <label
                  htmlFor="severity-filter"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Severity
                </label>
                <select
                  id="severity-filter"
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">All Severities</option>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>

              {/* Error Type Filter */}
              <div>
                <label
                  htmlFor="error-type-filter"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Error Type
                </label>
                <select
                  id="error-type-filter"
                  value={errorTypeFilter}
                  onChange={(e) => setErrorTypeFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">All Types</option>
                  {errorTypes.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Logs List */}
      <div className="space-y-3">
        {loading && filteredLogs.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <RefreshCw className="w-8 h-8 text-gray-400 animate-spin mx-auto mb-2" />
            <p className="text-gray-600">Loading logs...</p>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <Info className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600 text-lg mb-2">No logs found</p>
            <p className="text-gray-500 text-sm">
              {searchQuery || severityFilter || errorTypeFilter
                ? "Try adjusting your filters or search query"
                : "Error logs will appear here when they occur"}
            </p>
          </div>
        ) : (
          filteredLogs.map((log, index) => {
            const isExpanded = expandedLogs.has(index);
            const { icon, color, bg } = getSeverityDisplay(log.severity);
            const isCopied = copiedIndex === index;

            return (
              <div key={index} className={`bg-white rounded-lg shadow overflow-hidden ${bg}`}>
                {/* Log Header */}
                <div
                  className="p-4 cursor-pointer hover:bg-opacity-80 transition-colors"
                  onClick={() => toggleLogExpansion(index)}
                >
                  <div className="flex items-start gap-3">
                    <div className={color}>{icon}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-xs font-semibold uppercase ${color}`}>
                          {log.severity}
                        </span>
                        <span className="text-xs text-gray-500">•</span>
                        <span className="text-xs text-gray-600">{log.error_type}</span>
                        <span className="text-xs text-gray-500">•</span>
                        <span className="text-xs text-gray-500">
                          {new Date(log.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-900 font-medium truncate">
                        {log.error_message}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          copyToClipboard(log.error_message, index);
                        }}
                        className="p-1 text-gray-400 hover:text-gray-600"
                        title="Copy error message"
                      >
                        {isCopied ? (
                          <Check className="w-4 h-4 text-green-600" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </button>
                      {isExpanded ? (
                        <ChevronUp className="w-5 h-5 text-gray-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-gray-400" />
                      )}
                    </div>
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="border-t border-gray-200 p-4 bg-white">
                    {/* Stack Trace */}
                    <div className="mb-4">
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">Stack Trace</h4>
                      <pre className="bg-gray-50 p-3 rounded text-xs text-gray-800 overflow-x-auto">
                        {log.stack_trace}
                      </pre>
                    </div>

                    {/* System State */}
                    <div className="mb-4">
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">System State</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <div className="bg-gray-50 p-2 rounded">
                          <div className="text-xs text-gray-600">CPU Usage</div>
                          <div className="text-sm font-medium">
                            {log.system_state.cpu_usage_percent.toFixed(1)}%
                          </div>
                        </div>
                        <div className="bg-gray-50 p-2 rounded">
                          <div className="text-xs text-gray-600">Memory Usage</div>
                          <div className="text-sm font-medium">
                            {log.system_state.memory_usage_percent.toFixed(1)}%
                          </div>
                        </div>
                        <div className="bg-gray-50 p-2 rounded">
                          <div className="text-xs text-gray-600">Platform</div>
                          <div
                            className="text-sm font-medium truncate"
                            title={log.system_state.platform}
                          >
                            {log.system_state.platform}
                          </div>
                        </div>
                        {log.system_state.disk_usage_percent && (
                          <div className="bg-gray-50 p-2 rounded">
                            <div className="text-xs text-gray-600">Disk Usage</div>
                            <div className="text-sm font-medium">
                              {log.system_state.disk_usage_percent.toFixed(1)}%
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Context */}
                    {log.context && Object.keys(log.context).length > 0 && (
                      <div className="mb-4">
                        <h4 className="text-sm font-semibold text-gray-700 mb-2">Context</h4>
                        <pre className="bg-gray-50 p-3 rounded text-xs text-gray-800 overflow-x-auto">
                          {JSON.stringify(log.context, null, 2)}
                        </pre>
                      </div>
                    )}

                    {/* Recent Actions */}
                    {log.recent_actions && log.recent_actions.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-700 mb-2">
                          Recent Actions ({log.recent_actions.length})
                        </h4>
                        <div className="bg-gray-50 p-3 rounded max-h-40 overflow-y-auto">
                          {log.recent_actions.slice(-10).map((action, i) => (
                            <div key={i} className="text-xs text-gray-700 py-1">
                              {action}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Results Count */}
      {filteredLogs.length > 0 && (
        <div className="mt-4 text-center text-sm text-gray-600">
          Showing {filteredLogs.length} of {logs.length} logs
          {(searchQuery || severityFilter || errorTypeFilter) && " (filtered)"}
        </div>
      )}
    </div>
  );
};

export default LoggingDiagnostics;
