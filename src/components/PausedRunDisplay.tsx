import {
  Play,
  Clock,
  Zap,
  Server,
  MemoryStick,
  Cpu,
  HardDrive,
  Calendar,
  TrendingUp,
  Pause,
} from "lucide-react";
import React from "react";

import { cn, formatDuration } from "../lib/utils";

interface ResourceUsage {
  gpu_utilization: number[];
  gpu_memory_used: number[];
  cpu_utilization: number;
  ram_used: number;
}

interface PausedRunInfo {
  job_id: string;
  state: string;
  paused_at: string;
  started_at: string;
  elapsed_time: number;
  remaining_time_estimate: number;
  current_step: number;
  current_epoch: number;
  current_loss: number;
  resource_usage: ResourceUsage;
  model_name?: string;
  dataset_name?: string;
}

interface PausedRunDisplayProps {
  pausedRun: PausedRunInfo;
  onResume: (jobId: string) => void;
  onStop?: (jobId: string) => void;
}

const PausedRunDisplay: React.FC<PausedRunDisplayProps> = ({ pausedRun, onResume, onStop }) => {
  const formatTimestamp = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString();
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  const getAverageGPUUtilization = () => {
    if (!pausedRun.resource_usage.gpu_utilization.length) return 0;
    const sum = pausedRun.resource_usage.gpu_utilization.reduce((a, b) => a + b, 0);
    return sum / pausedRun.resource_usage.gpu_utilization.length;
  };

  const getAverageGPUMemory = () => {
    if (!pausedRun.resource_usage.gpu_memory_used.length) return 0;
    const sum = pausedRun.resource_usage.gpu_memory_used.reduce((a, b) => a + b, 0);
    return sum / pausedRun.resource_usage.gpu_memory_used.length;
  };

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-start justify-between mb-24">
        <div className="flex items-center gap-12">
          <div className="w-48 h-48 rounded-full bg-accent-warning/20 flex items-center justify-center">
            <Pause size={24} className="text-accent-warning" />
          </div>
          <div>
            <div className="flex items-center gap-8 mb-4">
              <h2 className="text-h2 font-semibold">Paused Training Run</h2>
              <span className="px-12 py-4 bg-accent-warning/20 text-accent-warning text-tiny font-medium rounded-full">
                PAUSED
              </span>
            </div>
            <p className="text-body text-dark-text-secondary">Job ID: {pausedRun.job_id}</p>
          </div>
        </div>

        <div className="flex items-center gap-8">
          <button
            onClick={() => onResume(pausedRun.job_id)}
            className="btn-primary flex items-center gap-8"
          >
            <Play size={16} />
            <span>Resume Training</span>
          </button>
          {onStop && (
            <button
              onClick={() => onStop(pausedRun.job_id)}
              className="btn-secondary flex items-center gap-8"
            >
              <span>Stop &amp; Save</span>
            </button>
          )}
        </div>
      </div>

      {/* Time Information */}
      <div className="grid grid-cols-3 gap-16 mb-24">
        <div className="card bg-dark-bg-tertiary">
          <div className="flex items-center gap-12 mb-12">
            <Clock size={20} className="text-accent-primary" />
            <span className="text-small text-dark-text-secondary">Elapsed Time</span>
          </div>
          <div className="text-h2 font-bold">{formatDuration(pausedRun.elapsed_time)}</div>
          <div className="text-tiny text-dark-text-tertiary mt-4">
            Since {formatTimestamp(pausedRun.started_at)}
          </div>
        </div>

        <div className="card bg-dark-bg-tertiary">
          <div className="flex items-center gap-12 mb-12">
            <Zap size={20} className="text-accent-info" />
            <span className="text-small text-dark-text-secondary">Remaining Time</span>
          </div>
          <div className="text-h2 font-bold">
            {formatDuration(pausedRun.remaining_time_estimate)}
          </div>
          <div className="text-tiny text-dark-text-tertiary mt-4">Estimated</div>
        </div>

        <div className="card bg-dark-bg-tertiary">
          <div className="flex items-center gap-12 mb-12">
            <Calendar size={20} className="text-accent-warning" />
            <span className="text-small text-dark-text-secondary">Paused At</span>
          </div>
          <div className="text-body font-medium">{formatTimestamp(pausedRun.paused_at)}</div>
          <div className="text-tiny text-dark-text-tertiary mt-4">
            {new Date(pausedRun.paused_at).toLocaleDateString()}
          </div>
        </div>
      </div>

      {/* Training Progress */}
      <div className="mb-24">
        <h3 className="text-h3 mb-16">Training Progress at Pause</h3>
        <div className="grid grid-cols-3 gap-16">
          <div className="flex items-center justify-between p-16 bg-dark-bg-tertiary rounded-lg">
            <div>
              <div className="text-small text-dark-text-secondary mb-4">Current Step</div>
              <div className="text-h2 font-bold">{pausedRun.current_step.toLocaleString()}</div>
            </div>
            <TrendingUp size={24} className="text-accent-primary opacity-50" />
          </div>

          <div className="flex items-center justify-between p-16 bg-dark-bg-tertiary rounded-lg">
            <div>
              <div className="text-small text-dark-text-secondary mb-4">Current Epoch</div>
              <div className="text-h2 font-bold">{pausedRun.current_epoch}</div>
            </div>
            <TrendingUp size={24} className="text-accent-info opacity-50" />
          </div>

          <div className="flex items-center justify-between p-16 bg-dark-bg-tertiary rounded-lg">
            <div>
              <div className="text-small text-dark-text-secondary mb-4">Current Loss</div>
              <div className="text-h2 font-bold">{pausedRun.current_loss.toFixed(4)}</div>
            </div>
            <TrendingUp size={24} className="text-accent-success opacity-50" />
          </div>
        </div>
      </div>

      {/* Resource Usage at Pause Time */}
      <div>
        <h3 className="text-h3 mb-16">Resource Usage at Pause Time</h3>
        <div className="grid grid-cols-2 gap-16">
          {/* GPU Utilization */}
          <div className="card bg-dark-bg-tertiary">
            <div className="flex items-center gap-12 mb-16">
              <Server size={20} className="text-accent-primary" />
              <span className="text-body font-medium">GPU Utilization</span>
            </div>

            {pausedRun.resource_usage.gpu_utilization.length > 0 ? (
              <div className="space-y-12">
                {pausedRun.resource_usage.gpu_utilization.map((util, index) => (
                  <div key={index}>
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-small text-dark-text-secondary">GPU {index}</span>
                      <span className="text-small font-medium">{util.toFixed(1)}%</span>
                    </div>
                    <div className="h-8 bg-dark-bg-primary rounded-full overflow-hidden">
                      <div
                        className={cn(
                          "h-full transition-all",
                          util > 90
                            ? "bg-accent-error"
                            : util > 70
                              ? "bg-accent-warning"
                              : "bg-accent-success"
                        )}
                        style={{ width: `${util}%` }}
                      />
                    </div>
                  </div>
                ))}
                <div className="pt-12 border-t border-dark-border">
                  <div className="flex items-center justify-between">
                    <span className="text-small text-dark-text-secondary">Average</span>
                    <span className="text-body font-bold">
                      {getAverageGPUUtilization().toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-small text-dark-text-tertiary">No GPU data available</div>
            )}
          </div>

          {/* GPU Memory */}
          <div className="card bg-dark-bg-tertiary">
            <div className="flex items-center gap-12 mb-16">
              <MemoryStick size={20} className="text-accent-info" />
              <span className="text-body font-medium">GPU Memory</span>
            </div>

            {pausedRun.resource_usage.gpu_memory_used.length > 0 ? (
              <div className="space-y-12">
                {pausedRun.resource_usage.gpu_memory_used.map((memory, index) => (
                  <div key={index}>
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-small text-dark-text-secondary">GPU {index}</span>
                      <span className="text-small font-medium">{formatBytes(memory)}</span>
                    </div>
                    <div className="h-8 bg-dark-bg-primary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-accent-info to-accent-primary transition-all"
                        style={{
                          width: `${Math.min((memory / (80 * 1024 * 1024 * 1024)) * 100, 100)}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
                <div className="pt-12 border-t border-dark-border">
                  <div className="flex items-center justify-between">
                    <span className="text-small text-dark-text-secondary">Average</span>
                    <span className="text-body font-bold">
                      {formatBytes(getAverageGPUMemory())}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-small text-dark-text-tertiary">No GPU memory data available</div>
            )}
          </div>

          {/* CPU Utilization */}
          <div className="card bg-dark-bg-tertiary">
            <div className="flex items-center gap-12 mb-16">
              <Cpu size={20} className="text-accent-success" />
              <span className="text-body font-medium">CPU Utilization</span>
            </div>
            <div className="flex items-center justify-between mb-8">
              <span className="text-h1 font-bold">
                {pausedRun.resource_usage.cpu_utilization.toFixed(1)}%
              </span>
            </div>
            <div className="h-12 bg-dark-bg-primary rounded-full overflow-hidden">
              <div
                className={cn(
                  "h-full transition-all",
                  pausedRun.resource_usage.cpu_utilization > 90
                    ? "bg-accent-error"
                    : pausedRun.resource_usage.cpu_utilization > 70
                      ? "bg-accent-warning"
                      : "bg-accent-success"
                )}
                style={{
                  width: `${pausedRun.resource_usage.cpu_utilization}%`,
                }}
              />
            </div>
          </div>

          {/* RAM Usage */}
          <div className="card bg-dark-bg-tertiary">
            <div className="flex items-center gap-12 mb-16">
              <HardDrive size={20} className="text-accent-warning" />
              <span className="text-body font-medium">RAM Usage</span>
            </div>
            <div className="flex items-center justify-between mb-8">
              <span className="text-h1 font-bold">
                {formatBytes(pausedRun.resource_usage.ram_used)}
              </span>
            </div>
            <div className="h-12 bg-dark-bg-primary rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-accent-warning to-accent-error transition-all"
                style={{
                  width: `${Math.min((pausedRun.resource_usage.ram_used / (64 * 1024 * 1024 * 1024)) * 100, 100)}%`,
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Configuration Info (if available) */}
      {(pausedRun.model_name || pausedRun.dataset_name) && (
        <div className="mt-24 pt-24 border-t border-dark-border">
          <h3 className="text-h3 mb-16">Configuration</h3>
          <div className="grid grid-cols-2 gap-16">
            {pausedRun.model_name && (
              <div>
                <div className="text-small text-dark-text-secondary mb-4">Model</div>
                <div className="text-body font-medium">{pausedRun.model_name}</div>
              </div>
            )}
            {pausedRun.dataset_name && (
              <div>
                <div className="text-small text-dark-text-secondary mb-4">Dataset</div>
                <div className="text-body font-medium">{pausedRun.dataset_name}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Info Banner */}
      <div className="mt-24 p-16 bg-accent-info/10 border border-accent-info/30 rounded-lg">
        <div className="flex items-start gap-12">
          <div className="text-accent-info mt-2">ℹ️</div>
          <div>
            <div className="text-body font-medium text-accent-info mb-4">Training Paused</div>
            <p className="text-small text-dark-text-secondary">
              This training run has been paused and can be resumed at any time. All progress has
              been saved, and GPU resources have been released. Click &quot;Resume Training&quot; to
              continue from where you left off.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PausedRunDisplay;
