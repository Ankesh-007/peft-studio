import {
  Pause,
  Play,
  Square,
  Download,
  Zap,
  Target,
  Clock,
  Gauge,
  Shield,
  Server,
  MemoryStick,
  Hourglass,
  TrendingDown,
  TrendingUp,
  AlertCircle,
} from "lucide-react";
import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

import { cn, formatDuration } from "../lib/utils";
import { useWebSocket } from "../hooks/useWebSocket";
import { ConnectionStatus } from "./ConnectionStatus";

interface TrainingMetric {
  label: string;
  value: string | number;
  trend?: string;
  color: string;
  icon: React.ElementType;
  sparkline?: number[];
}

interface TrainingUpdate {
  type: 'training_update' | 'status_change' | 'log_entry';
  data: {
    step?: number;
    epoch?: number;
    loss?: number;
    valLoss?: number;
    learningRate?: number;
    gpuUtilization?: number;
    gpuMemory?: number;
    tokensPerSecond?: number;
    timeElapsed?: number;
    timeRemaining?: number;
    status?: 'running' | 'paused' | 'completed' | 'failed';
    progress?: number;
    log?: {
      time: string;
      level: string;
      message: string;
    };
  };
}

interface LossDataPoint {
  step: number;
  trainLoss: number;
  valLoss: number;
  lr: number;
}

interface TrainingMonitorProps {
  runId: string;
  runName: string;
}

const TrainingMonitor: React.FC<TrainingMonitorProps> = ({
  runId,
  runName,
}) => {
  const [status, setStatus] = useState<
    "running" | "paused" | "completed" | "failed"
  >("running");
  const [progress, setProgress] = useState(0);
  const [currentEpoch, setCurrentEpoch] = useState(0);
  const [totalEpochs] = useState(10);
  const [timeElapsed, setTimeElapsed] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [activeTab, setActiveTab] = useState<
    "loss" | "resources" | "parameters"
  >("loss");
  const [logsExpanded, setLogsExpanded] = useState(true);
  
  // Real-time data from WebSocket
  const [lossData, setLossData] = useState<LossDataPoint[]>([]);
  const [currentMetrics, setCurrentMetrics] = useState({
    loss: 0,
    valLoss: 0,
    learningRate: 0,
    gpuUtilization: 0,
    gpuMemory: 0,
    tokensPerSecond: 0,
  });
  const [logs, setLogs] = useState<Array<{ time: string; level: string; message: string }>>([]);
  const [lossSparkline, setLossSparkline] = useState<number[]>([]);

  // WebSocket connection for real-time updates
  const wsUrl = `ws://localhost:8000/ws/training/${runId}`;
  const { isConnected, subscribe } = useWebSocket<TrainingUpdate>(wsUrl, {
    autoConnect: true,
    onConnectionChange: (connected) => {
      console.log(`Training monitor ${connected ? 'connected' : 'disconnected'}`);
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
    },
  });

  // Subscribe to training updates
  useEffect(() => {
    const unsubscribe = subscribe((update: TrainingUpdate) => {
      if (update.type === 'training_update' && update.data) {
        const data = update.data;
        
        // Update metrics
        if (data.loss !== undefined) {
          setCurrentMetrics(prev => ({ ...prev, loss: data.loss! }));
          setLossSparkline(prev => [...prev.slice(-6), data.loss!]);
        }
        if (data.valLoss !== undefined) {
          setCurrentMetrics(prev => ({ ...prev, valLoss: data.valLoss! }));
        }
        if (data.learningRate !== undefined) {
          setCurrentMetrics(prev => ({ ...prev, learningRate: data.learningRate! }));
        }
        if (data.gpuUtilization !== undefined) {
          setCurrentMetrics(prev => ({ ...prev, gpuUtilization: data.gpuUtilization! }));
        }
        if (data.gpuMemory !== undefined) {
          setCurrentMetrics(prev => ({ ...prev, gpuMemory: data.gpuMemory! }));
        }
        if (data.tokensPerSecond !== undefined) {
          setCurrentMetrics(prev => ({ ...prev, tokensPerSecond: data.tokensPerSecond! }));
        }
        
        // Update progress
        if (data.epoch !== undefined) setCurrentEpoch(data.epoch);
        if (data.progress !== undefined) setProgress(data.progress);
        if (data.timeElapsed !== undefined) setTimeElapsed(data.timeElapsed);
        if (data.timeRemaining !== undefined) setTimeRemaining(data.timeRemaining);
        
        // Update loss chart data
        if (data.step !== undefined && data.loss !== undefined) {
          setLossData(prev => [
            ...prev,
            {
              step: data.step!,
              trainLoss: data.loss!,
              valLoss: data.valLoss || 0,
              lr: data.learningRate || 0,
            }
          ].slice(-100)); // Keep last 100 points
        }
      } else if (update.type === 'status_change' && update.data.status) {
        setStatus(update.data.status);
      } else if (update.type === 'log_entry' && update.data.log) {
        setLogs(prev => [...prev, update.data.log!].slice(-100)); // Keep last 100 logs
      }
    });

    return unsubscribe;
  }, [subscribe]);

  // Build metrics from real-time data
  const metrics: TrainingMetric[] = [
    {
      label: "Current Loss",
      value: currentMetrics.loss.toFixed(4),
      trend: lossData.length > 1 ? 
        `↓ ${((lossData[lossData.length - 2].trainLoss - currentMetrics.loss) / lossData[lossData.length - 2].trainLoss * 100).toFixed(1)}%` : 
        undefined,
      color: "accent-success",
      icon: Target,
      sparkline: lossSparkline,
    },
    {
      label: "Learning Rate",
      value: currentMetrics.learningRate.toExponential(1),
      trend: lossData.length > 1 ? 
        `↓ ${(lossData[lossData.length - 2].lr - currentMetrics.learningRate).toExponential(1)}` : 
        undefined,
      color: "accent-warning",
      icon: Zap,
    },
    {
      label: "Epoch Progress",
      value: `${currentEpoch} / ${totalEpochs}`,
      trend: `${progress}%`,
      color: "accent-primary",
      icon: Clock,
    },
    {
      label: "Training Throughput",
      value: `${currentMetrics.tokensPerSecond.toFixed(1)} steps/s`,
      trend: currentMetrics.tokensPerSecond > 10 ? "↑ Fast" : "Normal",
      color: "accent-success",
      icon: Gauge,
    },
    {
      label: "Validation Loss",
      value: currentMetrics.valLoss.toFixed(4),
      trend: currentMetrics.valLoss > currentMetrics.loss ? "↑ Higher" : "↓ Lower",
      color: currentMetrics.valLoss > currentMetrics.loss ? "accent-error" : "accent-success",
      icon: Shield,
    },
    {
      label: "GPU Utilization",
      value: `${Math.round(currentMetrics.gpuUtilization)}%`,
      trend: currentMetrics.gpuUtilization > 90 ? "High" : "Normal",
      color: currentMetrics.gpuUtilization > 90 ? "accent-error" : "accent-success",
      icon: Server,
    },
    {
      label: "VRAM Usage",
      value: `${currentMetrics.gpuMemory.toFixed(1)} GB`,
      trend: `${Math.round(currentMetrics.gpuMemory / 80 * 100)}% Max`,
      color: "accent-primary",
      icon: MemoryStick,
    },
    {
      label: "Time Remaining",
      value: formatDuration(timeRemaining),
      trend: "Estimating...",
      color: "dark-text-secondary",
      icon: Hourglass,
    },
  ];

  const resourceData = [
    { name: "GPU 0", usage: Math.round(currentMetrics.gpuUtilization) },
    { name: "GPU 1", usage: Math.round(currentMetrics.gpuUtilization * 0.5) }, // Mock second GPU
    { name: "CPU", usage: 62 }, // Would come from backend
    { name: "RAM", usage: 71 }, // Would come from backend
  ];

  const getStatusColor = () => {
    switch (status) {
      case "running":
        return "bg-accent-success";
      case "paused":
        return "bg-accent-warning";
      case "completed":
        return "bg-accent-success";
      case "failed":
        return "bg-accent-error";
      default:
        return "bg-dark-text-tertiary";
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case "running":
        return "🟢";
      case "paused":
        return "🟡";
      case "completed":
        return "✅";
      case "failed":
        return "🔴";
      default:
        return "⚪";
    }
  };

  const handlePauseResume = async () => {
    try {
      const action = status === "running" ? "pause" : "resume";
      const response = await fetch(`http://localhost:8000/api/training/${runId}/${action}`, {
        method: 'POST',
      });
      
      if (response.ok) {
        setStatus(status === "running" ? "paused" : "running");
      } else {
        console.error(`Failed to ${action} training`);
      }
    } catch (error) {
      console.error('Error controlling training:', error);
    }
  };

  const handleStop = async () => {
    if (
      confirm("Are you sure you want to stop training? Progress will be saved.")
    ) {
      try {
        const response = await fetch(`http://localhost:8000/api/training/${runId}/stop`, {
          method: 'POST',
        });
        
        if (response.ok) {
          setStatus("completed");
        } else {
          console.error('Failed to stop training');
        }
      } catch (error) {
        console.error('Error stopping training:', error);
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0a] to-[#0f0f0f] p-24 space-y-24">
      {/* WebSocket Connection Status */}
      <div className="fixed top-16 right-16 z-50">
        <ConnectionStatus 
          status={isConnected ? "online" : "offline"} 
          showLabel={true}
        />
      </div>

      {/* Status Header */}
      <div className="text-center space-y-16">
        <div className="inline-flex items-center gap-12 px-24 py-12 bg-dark-bg-secondary border border-dark-border rounded-full">
          <span
            className={cn("text-h2", status === "running" && "animate-pulse")}
          >
            {getStatusIcon()}
          </span>
          <span className="text-h2 font-semibold capitalize">{status}</span>
        </div>

        <h1 className="text-display">{runName}</h1>
        <p className="text-body text-dark-text-secondary">
          Started: {new Date().toLocaleString()}
        </p>

        {/* Control Buttons */}
        <div className="flex items-center justify-center gap-12">
          <button
            onClick={handlePauseResume}
            className={cn(
              "btn-primary flex items-center gap-8",
              status === "paused" && "bg-accent-success",
            )}
          >
            {status === "running" ? (
              <>
                <Pause size={16} />
                <span>Pause</span>
              </>
            ) : (
              <>
                <Play size={16} />
                <span>Resume</span>
              </>
            )}
          </button>

          <button
            onClick={handleStop}
            className="btn-secondary flex items-center gap-8"
          >
            <Square size={16} />
            <span>Stop & Save</span>
          </button>

          <button className="btn-ghost flex items-center gap-8">
            <Download size={16} />
            <span>Snapshot</span>
          </button>
        </div>
      </div>

      {/* Progress Section */}
      <div className="card max-w-[600px] mx-auto">
        <div className="flex items-center justify-between mb-16">
          <div className="text-center flex-1">
            <div className="text-display mb-4">{progress}%</div>
            <div className="text-small text-dark-text-tertiary">Complete</div>
          </div>

          <div className="w-[200px] h-[200px] relative">
            <svg className="transform -rotate-90" viewBox="0 0 200 200">
              <circle
                cx="100"
                cy="100"
                r="90"
                fill="none"
                stroke="#1a1a1a"
                strokeWidth="12"
              />
              <circle
                cx="100"
                cy="100"
                r="90"
                fill="none"
                stroke="url(#progressGradient)"
                strokeWidth="12"
                strokeDasharray={`${progress * 5.65} 565`}
                strokeLinecap="round"
                className="transition-all duration-500"
              />
              <defs>
                <linearGradient
                  id="progressGradient"
                  x1="0%"
                  y1="0%"
                  x2="100%"
                  y2="0%"
                >
                  <stop offset="0%" stopColor="#6366f1" />
                  <stop offset="100%" stopColor="#3b82f6" />
                </linearGradient>
              </defs>
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <div className="text-h1 font-bold">{currentEpoch}</div>
              <div className="text-small text-dark-text-tertiary">
                / {totalEpochs}
              </div>
            </div>
          </div>

          <div className="text-center flex-1">
            <div className="text-h2 mb-4">{formatDuration(timeElapsed)}</div>
            <div className="text-small text-dark-text-tertiary">Elapsed</div>
            <div className="text-h3 mt-12 text-accent-info">
              {formatDuration(timeRemaining)}
            </div>
            <div className="text-tiny text-dark-text-tertiary">Remaining</div>
          </div>
        </div>

        <div className="h-8 bg-dark-bg-primary rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-accent-primary to-accent-info transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-4 gap-16">
        {metrics.map((metric, index) => {
          const Icon = metric.icon;
          const isNegativeTrend =
            metric.trend?.includes("↑") && metric.label.includes("Loss");
          const isPositiveTrend =
            metric.trend?.includes("↑") && !metric.label.includes("Loss");

          return (
            <div
              key={index}
              className="card card-hover relative overflow-hidden"
            >
              {/* Sparkline background */}
              {metric.sparkline && (
                <div className="absolute top-0 right-0 w-[100px] h-[40px] opacity-20">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={metric.sparkline.map((v, i) => ({ v, i }))}
                    >
                      <Line
                        type="monotone"
                        dataKey="v"
                        stroke={`var(--${metric.color})`}
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}

              <div className="relative z-10">
                <div className="flex items-center justify-between mb-12">
                  <Icon size={20} className={`text-${metric.color}`} />
                  {metric.trend && (
                    <div
                      className={cn(
                        "flex items-center gap-4 text-tiny",
                        isNegativeTrend && "text-accent-error",
                        isPositiveTrend && "text-accent-success",
                        !isNegativeTrend &&
                          !isPositiveTrend &&
                          "text-dark-text-tertiary",
                      )}
                    >
                      {isNegativeTrend ? (
                        <TrendingUp size={12} />
                      ) : isPositiveTrend ? (
                        <TrendingUp size={12} />
                      ) : (
                        <TrendingDown size={12} />
                      )}
                      <span>{metric.trend}</span>
                    </div>
                  )}
                </div>

                <div className="text-h1 font-bold mb-4">{metric.value}</div>
                <div className="text-small text-dark-text-tertiary">
                  {metric.label}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Visualization Area */}
      <div className="card">
        {/* Tabs */}
        <div className="flex items-center gap-8 mb-24 border-b border-dark-border">
          {[
            { id: "loss", label: "Loss Curves" },
            { id: "resources", label: "Resource Monitoring" },
            { id: "parameters", label: "Parameter Distributions" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={cn(
                "px-16 py-12 text-body font-medium transition-all relative",
                activeTab === tab.id
                  ? "text-accent-primary"
                  : "text-dark-text-secondary hover:text-dark-text-primary",
              )}
            >
              {tab.label}
              {activeTab === tab.id && (
                <div className="absolute bottom-0 left-0 right-0 h-2 bg-accent-primary rounded-t" />
              )}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === "loss" && (
          <div className="space-y-16">
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={lossData}>
                <defs>
                  <linearGradient
                    id="trainGradient"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                <XAxis
                  dataKey="step"
                  stroke="#71717a"
                  style={{ fontSize: "12px" }}
                  label={{
                    value: "Steps",
                    position: "insideBottom",
                    offset: -5,
                  }}
                />
                <YAxis
                  yAxisId="left"
                  stroke="#71717a"
                  style={{ fontSize: "12px" }}
                  label={{ value: "Loss", angle: -90, position: "insideLeft" }}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  stroke="#f59e0b"
                  style={{ fontSize: "12px" }}
                  label={{
                    value: "Learning Rate",
                    angle: 90,
                    position: "insideRight",
                  }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#111111",
                    border: "1px solid #2a2a2a",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                />
                <Legend />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="trainLoss"
                  stroke="#6366f1"
                  strokeWidth={2}
                  name="Training Loss"
                  dot={false}
                  fill="url(#trainGradient)"
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="valLoss"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  name="Validation Loss"
                  dot={false}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="lr"
                  stroke="#f59e0b"
                  strokeWidth={1.5}
                  name="Learning Rate"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {activeTab === "resources" && (
          <div className="space-y-24">
            <div>
              <h3 className="text-h3 mb-16">GPU & System Utilization</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={resourceData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                  <XAxis
                    type="number"
                    stroke="#71717a"
                    style={{ fontSize: "12px" }}
                  />
                  <YAxis
                    dataKey="name"
                    type="category"
                    stroke="#71717a"
                    style={{ fontSize: "12px" }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#111111",
                      border: "1px solid #2a2a2a",
                      borderRadius: "8px",
                    }}
                  />
                  <Bar dataKey="usage" radius={[0, 8, 8, 0]}>
                    {resourceData.map((entry, index) => (
                      <rect
                        key={index}
                        fill={
                          entry.usage > 90
                            ? "#ef4444"
                            : entry.usage > 70
                              ? "#f59e0b"
                              : "#10b981"
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {activeTab === "parameters" && (
          <div className="text-center py-64 text-dark-text-tertiary">
            <AlertCircle size={48} className="mx-auto mb-16 opacity-50" />
            <p>Parameter distribution visualization coming soon</p>
          </div>
        )}
      </div>

      {/* Configuration Sidebar & Logs */}
      <div className="grid grid-cols-3 gap-24">
        {/* Configuration Summary */}
        <div className="card">
          <h3 className="text-h3 mb-16">Configuration</h3>
          <div className="space-y-12 text-small">
            <div>
              <div className="text-dark-text-tertiary mb-4">Model</div>
              <div className="text-dark-text-primary font-medium">
                Llama-3-8B
              </div>
            </div>
            <div>
              <div className="text-dark-text-tertiary mb-4">Dataset</div>
              <div className="text-dark-text-primary font-medium">
                Finance-10k
              </div>
            </div>
            <div>
              <div className="text-dark-text-tertiary mb-4">PEFT Method</div>
              <div className="text-dark-text-primary font-medium">
                QLoRA (r=64, α=128)
              </div>
            </div>
            <div>
              <div className="text-dark-text-tertiary mb-4">Batch Size</div>
              <div className="text-dark-text-primary font-medium">8</div>
            </div>
            <div>
              <div className="text-dark-text-tertiary mb-4">Total Steps</div>
              <div className="text-dark-text-primary font-medium">1,250</div>
            </div>
            <div>
              <div className="text-dark-text-tertiary mb-4">Log Path</div>
              <div className="text-dark-text-primary font-mono text-tiny break-all">
                /path/to/run/logs
              </div>
            </div>
          </div>

          <div className="mt-20 pt-20 border-t border-dark-border">
            <button className="btn-ghost w-full justify-center">
              View Full Config
            </button>
          </div>
        </div>

        {/* Real-Time Logs */}
        <div className="col-span-2 card">
          <div className="flex items-center justify-between mb-16">
            <h3 className="text-h3">Training Logs</h3>
            <div className="flex items-center gap-8">
              <button className="btn-ghost text-tiny px-8 py-4">
                <Download size={14} />
              </button>
              <button className="btn-ghost text-tiny px-8 py-4">Clear</button>
            </div>
          </div>

          <div className="bg-black rounded-lg p-16 h-[400px] overflow-y-auto font-mono text-tiny">
            {logs.map((log, index) => (
              <div
                key={index}
                className={cn(
                  "mb-4",
                  log.level === "INFO" && "text-[#a1a1aa]",
                  log.level === "WARN" && "text-[#f59e0b]",
                  log.level === "ERROR" && "text-[#ef4444] animate-pulse",
                  log.level === "DEBUG" && "text-[#52525b]",
                )}
              >
                <span className="text-dark-text-tertiary">[{log.time}]</span>{" "}
                <span className="font-semibold">{log.level}</span> {log.message}
              </div>
            ))}
            <div className="h-4" /> {/* Auto-scroll anchor */}
          </div>

          <div className="mt-12">
            <input
              type="text"
              placeholder="Filter logs..."
              className="input w-full text-tiny"
            />
          </div>
        </div>
      </div>

      {/* Checkpoints (if completed) */}
      {status === "completed" && (
        <div className="card">
          <div className="text-center mb-32">
            <div className="text-display mb-8">✅ Training Completed!</div>
            <p className="text-body text-dark-text-secondary mb-24">
              Your model has been successfully trained and saved.
            </p>

            <div className="grid grid-cols-4 gap-16 max-w-[800px] mx-auto mb-32">
              <div className="text-center">
                <div className="text-h2 text-accent-success mb-4">0.4321</div>
                <div className="text-small text-dark-text-tertiary">
                  Best Loss
                </div>
              </div>
              <div className="text-center">
                <div className="text-h2 text-accent-primary mb-4">07:12:45</div>
                <div className="text-small text-dark-text-tertiary">
                  Total Time
                </div>
              </div>
              <div className="text-center">
                <div className="text-h2 text-accent-info mb-4">1.5 GB</div>
                <div className="text-small text-dark-text-tertiary">
                  Checkpoint Size
                </div>
              </div>
              <div className="text-center">
                <div className="text-h2 text-accent-warning mb-4">4</div>
                <div className="text-small text-dark-text-tertiary">
                  Artifacts
                </div>
              </div>
            </div>

            <div className="flex items-center justify-center gap-12">
              <button className="btn-primary">Test Model</button>
              <button className="btn-secondary">View Checkpoints</button>
              <button className="btn-ghost">Deploy Model</button>
              <button className="btn-ghost">View Report</button>
            </div>
          </div>

          <div>
            <h3 className="text-h3 mb-16">Saved Checkpoints</h3>
            <div className="space-y-8">
              {[
                {
                  name: "epoch-1_step-250",
                  step: 250,
                  loss: 0.823,
                  time: "01:15:30",
                },
                {
                  name: "epoch-5_step-625",
                  step: 625,
                  loss: 0.612,
                  time: "03:45:00",
                },
                {
                  name: "best_model",
                  step: 1250,
                  loss: 0.432,
                  time: "07:12:45",
                  isBest: true,
                },
              ].map((checkpoint, index) => (
                <div
                  key={index}
                  className={cn(
                    "flex items-center justify-between p-16 rounded-lg",
                    checkpoint.isBest
                      ? "bg-accent-success/10 border border-accent-success/30"
                      : "bg-dark-bg-tertiary",
                  )}
                >
                  <div className="flex items-center gap-16">
                    {checkpoint.isBest && <span className="text-h3">🏆</span>}
                    <div>
                      <div className="text-body font-medium">
                        {checkpoint.name}
                      </div>
                      <div className="text-small text-dark-text-tertiary">
                        Step {checkpoint.step} • Loss: {checkpoint.loss} •{" "}
                        {checkpoint.time}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-8">
                    <button className="btn-ghost text-tiny px-12 py-6">
                      Load
                    </button>
                    <button className="btn-ghost text-tiny px-12 py-6">
                      Export
                    </button>
                    <button className="btn-ghost text-tiny px-12 py-6 text-accent-error">
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TrainingMonitor;
