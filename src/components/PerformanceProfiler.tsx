/**
 * Performance Profiler Component
 *
 * Development tool for monitoring and profiling application performance.
 * Shows FPS, memory usage, render times, and custom metrics.
 *
 * Requirements: 14.3
 */

import React, { useState, memo } from "react";
import { useFPS, useMemoryUsage, usePerformanceStats } from "../hooks/usePerformance";
import { performanceMonitor, logPerformanceMetrics } from "../lib/performance";

interface PerformanceProfilerProps {
  enabled?: boolean;
  position?: "top-left" | "top-right" | "bottom-left" | "bottom-right";
}

export const PerformanceProfiler: React.FC<PerformanceProfilerProps> = memo(
  ({ enabled = process.env.NODE_ENV === "development", position = "bottom-right" }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const fps = useFPS();
    const memory = useMemoryUsage(1000);
    const stats = usePerformanceStats();

    if (!enabled) {
      return null;
    }

    const positionClasses = {
      "top-left": "top-4 left-4",
      "top-right": "top-4 right-4",
      "bottom-left": "bottom-4 left-4",
      "bottom-right": "bottom-4 right-4",
    };

    const getFPSColor = (fps: number) => {
      if (fps >= 55) return "text-green-600";
      if (fps >= 30) return "text-yellow-600";
      return "text-red-600";
    };

    const getMemoryColor = (percent: number) => {
      if (percent < 50) return "text-green-600";
      if (percent < 75) return "text-yellow-600";
      return "text-red-600";
    };

    return (
      <div
        className={`fixed ${positionClasses[position]} z-50 bg-black/90 text-white rounded-lg shadow-2xl font-mono text-xs`}
        style={{ backdropFilter: "blur(10px)" }}
      >
        {/* Compact View */}
        {!isExpanded && (
          <div
            className="p-3 cursor-pointer hover:bg-black/95 transition-colors"
            onClick={() => setIsExpanded(true)}
          >
            <div className="flex items-center gap-4">
              <div>
                <span className="text-gray-400">FPS:</span>
                <span className={`ml-2 font-bold ${getFPSColor(fps)}`}>{fps}</span>
              </div>
              {memory && (
                <div>
                  <span className="text-gray-400">MEM:</span>
                  <span className={`ml-2 font-bold ${getMemoryColor(memory.usedPercent)}`}>
                    {memory.usedPercent.toFixed(1)}%
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Expanded View */}
        {isExpanded && (
          <div className="w-96 max-h-[600px] overflow-y-auto">
            {/* Header */}
            <div className="sticky top-0 bg-black/95 p-3 border-b border-gray-700 flex items-center justify-between">
              <h3 className="font-bold text-sm">Performance Monitor</h3>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    logPerformanceMetrics();
                    alert("Performance metrics logged to console");
                  }}
                  className="px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-xs"
                  title="Log metrics to console"
                >
                  Log
                </button>
                <button
                  onClick={() => {
                    performanceMonitor.clear();
                    alert("Performance metrics cleared");
                  }}
                  className="px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-xs"
                  title="Clear metrics"
                >
                  Clear
                </button>
                <button
                  onClick={() => setIsExpanded(false)}
                  className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* FPS */}
            <div className="p-3 border-b border-gray-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400">Frame Rate</span>
                <span className={`font-bold text-lg ${getFPSColor(fps)}`}>{fps} FPS</span>
              </div>
              <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all ${fps >= 55 ? "bg-green-600" : fps >= 30 ? "bg-yellow-600" : "bg-red-600"
                    }`}
                  style={{ width: `${(fps / 60) * 100}%` }}
                />
              </div>
            </div>

            {/* Memory */}
            {memory && (
              <div className="p-3 border-b border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-400">Memory Usage</span>
                  <span className={`font-bold ${getMemoryColor(memory.usedPercent)}`}>
                    {(memory.usedJSHeapSize / 1024 / 1024).toFixed(1)} MB
                  </span>
                </div>
                <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all ${memory.usedPercent < 50
                        ? "bg-green-600"
                        : memory.usedPercent < 75
                          ? "bg-yellow-600"
                          : "bg-red-600"
                      }`}
                    style={{ width: `${memory.usedPercent}%` }}
                  />
                </div>
                <div className="mt-2 text-xs text-gray-500">
                  Limit: {(memory.jsHeapSizeLimit / 1024 / 1024).toFixed(0)} MB
                </div>
              </div>
            )}

            {/* Custom Metrics */}
            {stats && Object.keys(stats).length > 0 && (
              <div className="p-3">
                <h4 className="text-gray-400 mb-2">Custom Metrics</h4>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {Object.entries(stats).map(
                    ([name, stat]: any) => (
                      <div key={name} className="bg-gray-800/50 p-2 rounded">
                        <div className="font-medium mb-1 truncate" title={name}>
                          {name}
                        </div>
                        <div className="grid grid-cols-3 gap-2 text-xs">
                          <div>
                            <span className="text-gray-500">Avg:</span>
                            <span className="ml-1">{stat.avg?.toFixed(2)}ms</span>
                          </div>
                          <div>
                            <span className="text-gray-500">P95:</span>
                            <span className="ml-1">{stat.p95?.toFixed(2)}ms</span>
                          </div>
                          <div>
                            <span className="text-gray-500">Max:</span>
                            <span className="ml-1">{stat.max?.toFixed(2)}ms</span>
                          </div>
                        </div>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}

            {/* Tips */}
            <div className="p-3 bg-gray-900/50 text-xs text-gray-400">
              <div className="mb-1">💡 Tips:</div>
              <ul className="list-disc list-inside space-y-1">
                <li>Target: 60 FPS for smooth UI</li>
                <li>Keep memory usage below 75%</li>
                <li>Operations should be &lt;16ms</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    );
  }
);

PerformanceProfiler.displayName = "PerformanceProfiler";

export default PerformanceProfiler;
