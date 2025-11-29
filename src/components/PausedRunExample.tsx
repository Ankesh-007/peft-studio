/**
 * Example usage of PausedRunDisplay component
 * This demonstrates how to integrate the paused run display into the application
 */

import React, { useState, useEffect } from 'react';
import PausedRunDisplay from './PausedRunDisplay';
import apiClient from '../api/client';

interface PausedRunExampleProps {
  jobId?: string;
}

const PausedRunExample: React.FC<PausedRunExampleProps> = ({ jobId }) => {
  const [pausedRun, setPausedRun] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (jobId) {
      fetchPausedRunInfo(jobId);
    } else {
      // If no jobId provided, fetch list of paused runs
      fetchPausedRuns();
    }
  }, [jobId]);

  const fetchPausedRunInfo = async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`http://localhost:8000/api/training/paused/${id}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch paused run: ${response.statusText}`);
      }
      
      const data = await response.json();
      setPausedRun(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch paused run');
      console.error('Error fetching paused run:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchPausedRuns = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('http://localhost:8000/api/training/paused');
      
      if (!response.ok) {
        throw new Error(`Failed to fetch paused runs: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.paused_runs && data.paused_runs.length > 0) {
        // Fetch details for the first paused run
        await fetchPausedRunInfo(data.paused_runs[0].job_id);
      } else {
        setError('No paused runs found');
        setLoading(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch paused runs');
      console.error('Error fetching paused runs:', err);
      setLoading(false);
    }
  };

  const handleResume = async (jobId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/training/resume/${jobId}`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error(`Failed to resume training: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Training resumed:', data);
      
      // Show success message
      alert(`Training resumed successfully for job ${jobId}`);
      
      // Optionally redirect to training monitor
      // window.location.href = `/training/${jobId}`;
    } catch (err) {
      console.error('Error resuming training:', err);
      alert(`Failed to resume training: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleStop = async (jobId: string) => {
    if (!confirm('Are you sure you want to stop this training run? Progress will be saved.')) {
      return;
    }
    
    try {
      const response = await fetch(`http://localhost:8000/api/training/stop/${jobId}`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error(`Failed to stop training: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Training stopped:', data);
      
      alert(`Training stopped successfully for job ${jobId}`);
      
      // Refresh the paused runs list
      if (!jobId) {
        fetchPausedRuns();
      }
    } catch (err) {
      console.error('Error stopping training:', err);
      alert(`Failed to stop training: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0a0a0a] to-[#0f0f0f] p-24 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-accent-primary mx-auto mb-16"></div>
          <p className="text-body text-dark-text-secondary">Loading paused run information...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0a0a0a] to-[#0f0f0f] p-24 flex items-center justify-center">
        <div className="card max-w-[600px]">
          <div className="text-center">
            <div className="text-h1 mb-16">⚠️</div>
            <h2 className="text-h2 mb-12">Error Loading Paused Run</h2>
            <p className="text-body text-dark-text-secondary mb-24">{error}</p>
            <button
              onClick={() => jobId ? fetchPausedRunInfo(jobId) : fetchPausedRuns()}
              className="btn-primary"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!pausedRun) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0a0a0a] to-[#0f0f0f] p-24 flex items-center justify-center">
        <div className="card max-w-[600px]">
          <div className="text-center">
            <div className="text-h1 mb-16">📋</div>
            <h2 className="text-h2 mb-12">No Paused Runs</h2>
            <p className="text-body text-dark-text-secondary">
              There are no paused training runs at the moment.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0a] to-[#0f0f0f] p-24">
      <PausedRunDisplay
        pausedRun={pausedRun}
        onResume={handleResume}
        onStop={handleStop}
      />
    </div>
  );
};

export default PausedRunExample;
