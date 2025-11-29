import React, { useState, useEffect } from 'react';
import { Brain, Zap, Database, Clock, TrendingUp, Upload, Play, MessageSquare, Search } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { cn, formatNumber, getTimeGreeting } from '../lib/utils';
import { SkeletonCard, SkeletonTable } from './LoadingStates';
import { useIsMobile } from '../hooks/useMediaQuery';

const Dashboard: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);
  const isMobile = useIsMobile();

  // Simulate data loading
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1000);
    return () => clearTimeout(timer);
  }, []);
  // Mock data
  const stats = [
    { label: 'Models Trained', value: 24, trend: '+12%', icon: Brain, color: 'accent-primary' },
    { label: 'Active Training', value: 2, trend: '+1', icon: Zap, color: 'accent-success' },
    { label: 'Datasets', value: 18, trend: '+3', icon: Database, color: 'accent-info' },
    { label: 'GPU Hours', value: 156, trend: '+24h', icon: Clock, color: 'accent-warning' },
  ];

  const trainingRuns = [
    { id: 1, name: 'llama-3-finance', model: 'Llama-3-8B', dataset: 'finance-qa', status: 'running', progress: 65 },
    { id: 2, name: 'mistral-chat', model: 'Mistral-7B', dataset: 'chat-data', status: 'completed', progress: 100 },
    { id: 3, name: 'gpt-neo-code', model: 'GPT-Neo-2.7B', dataset: 'code-snippets', status: 'failed', progress: 23 },
    { id: 4, name: 'llama-2-medical', model: 'Llama-2-13B', dataset: 'medical-notes', status: 'completed', progress: 100 },
  ];

  const lossData = [
    { step: 0, loss: 2.4 },
    { step: 100, loss: 1.8 },
    { step: 200, loss: 1.4 },
    { step: 300, loss: 1.1 },
    { step: 400, loss: 0.9 },
    { step: 500, loss: 0.7 },
  ];

  const gpuData = [
    { name: 'GPU 0', usage: 85 },
    { name: 'GPU 1', usage: 45 },
    { name: 'CPU', usage: 62 },
    { name: 'RAM', usage: 71 },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-accent-info';
      case 'completed': return 'bg-accent-success';
      case 'failed': return 'bg-accent-error';
      default: return 'bg-dark-text-tertiary';
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-24" role="status" aria-label="Loading dashboard">
        <div className="bg-gradient-to-br from-[#1a1a2e] to-[#16162a] rounded-2xl p-32 border border-dark-border">
          <div className="h-12 bg-dark-bg-tertiary rounded w-1/4 mb-8 animate-pulse" />
          <div className="h-6 bg-dark-bg-tertiary rounded w-1/3 mb-24 animate-pulse" />
          <div className="grid grid-cols-4 gap-16">
            {Array.from({ length: 4 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        </div>
        <div className="grid grid-cols-3 gap-24">
          <div className="col-span-2">
            <SkeletonCard />
          </div>
          <SkeletonCard />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-24" data-tour="dashboard">
      {/* Hero Section */}
      <section 
        className="bg-gradient-to-br from-[#1a1a2e] to-[#16162a] rounded-2xl p-32 border border-dark-border animate-fade-in"
        aria-label="Dashboard overview"
      >
        <h1 className="text-display mb-8">{getTimeGreeting()}</h1>
        <p className="text-body text-dark-text-secondary mb-24">
          <time dateTime={new Date().toISOString()}>
            {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </time>
        </p>
        
        {/* Stats Grid */}
        <div className={cn(
          "grid gap-16",
          isMobile ? "grid-cols-1" : "grid-cols-2 md:grid-cols-4"
        )}>
          {stats.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <article 
                key={index} 
                className="card card-hover"
                role="article"
                aria-label={`${stat.label}: ${stat.value}`}
              >
                <div className="flex items-start justify-between mb-12">
                  <div className={cn(
                    "w-40 h-40 rounded-full flex items-center justify-center",
                    `bg-${stat.color}/10`
                  )}
                  role="img"
                  aria-label={stat.label}
                  >
                    <Icon size={20} className={`text-${stat.color}`} aria-hidden="true" />
                  </div>
                  <div className="flex items-center gap-4 text-tiny text-accent-success" role="status">
                    <TrendingUp size={12} aria-hidden="true" />
                    <span aria-label={`Trend: ${stat.trend}`}>{stat.trend}</span>
                  </div>
                </div>
                <div className="text-display mb-4">{formatNumber(stat.value)}</div>
                <div className="text-small text-dark-text-tertiary">{stat.label}</div>
              </article>
            );
          })}
        </div>
      </section>

      {/* Main Grid */}
      <div className="grid grid-cols-3 gap-24">
        {/* Recent Training Runs */}
        <div className="col-span-2 card" data-tour="training-runs">
          <div className="flex items-center justify-between mb-20">
            <h2 className="text-h2">Recent Training Runs</h2>
            <button className="text-small text-accent-primary hover:text-accent-primary/80">
              View All →
            </button>
          </div>
          
          <div className="space-y-12">
            {trainingRuns.map((run) => (
              <div
                key={run.id}
                className="p-16 bg-dark-bg-tertiary rounded-lg hover:bg-dark-bg-tertiary/80 transition-all cursor-pointer"
              >
                <div className="flex items-center justify-between mb-8">
                  <div className="flex items-center gap-12">
                    <div className={cn(
                      "w-8 h-8 rounded-full",
                      getStatusColor(run.status),
                      run.status === 'running' && "animate-pulse"
                    )}></div>
                    <span className="text-body font-medium">{run.name}</span>
                  </div>
                  <span className="text-tiny text-dark-text-tertiary capitalize">{run.status}</span>
                </div>
                
                <div className="flex items-center gap-16 text-small text-dark-text-secondary mb-12">
                  <span>{run.model}</span>
                  <span>•</span>
                  <span>{run.dataset}</span>
                </div>
                
                {run.status === 'running' && (
                  <div className="space-y-4">
                    <div className="flex justify-between text-tiny text-dark-text-tertiary">
                      <span>Progress</span>
                      <span>{run.progress}%</span>
                    </div>
                    <div className="h-4 bg-dark-bg-primary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-accent-primary to-accent-info transition-all duration-300"
                        style={{ width: `${run.progress}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="card" data-tour="quick-actions">
          <h2 className="text-h2 mb-20">Quick Actions</h2>
          
          <div className="grid grid-cols-2 gap-12">
            {[
              { label: 'Upload Dataset', icon: Upload, color: 'accent-primary' },
              { label: 'Start Training', icon: Play, color: 'accent-success' },
              { label: 'Test Model', icon: MessageSquare, color: 'accent-info' },
              { label: 'Browse Models', icon: Search, color: 'accent-warning' },
            ].map((action, index) => {
              const Icon = action.icon;
              return (
                <button
                  key={index}
                  className="p-16 bg-dark-bg-tertiary rounded-lg hover:bg-gradient-to-br hover:from-dark-bg-tertiary hover:to-dark-bg-primary transition-all group"
                >
                  <Icon size={24} className={`text-${action.color} mb-8`} />
                  <div className="text-small font-medium">{action.label}</div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-2 gap-24">
        {/* Training Loss Chart */}
        <div className="card">
          <h2 className="text-h2 mb-20">Training Loss</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={lossData}>
              <defs>
                <linearGradient id="lossGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
              <XAxis dataKey="step" stroke="#71717a" style={{ fontSize: '12px' }} />
              <YAxis stroke="#71717a" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#111111',
                  border: '1px solid #2a2a2a',
                  borderRadius: '8px',
                  fontSize: '12px'
                }}
              />
              <Line
                type="monotone"
                dataKey="loss"
                stroke="#6366f1"
                strokeWidth={2}
                fill="url(#lossGradient)"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* System Resources */}
        <div className="card" data-tour="system-resources">
          <h2 className="text-h2 mb-20">System Resources</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={gpuData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
              <XAxis type="number" stroke="#71717a" style={{ fontSize: '12px' }} />
              <YAxis dataKey="name" type="category" stroke="#71717a" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#111111',
                  border: '1px solid #2a2a2a',
                  borderRadius: '8px',
                  fontSize: '12px'
                }}
              />
              <Bar dataKey="usage" fill="#6366f1" radius={[0, 8, 8, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
