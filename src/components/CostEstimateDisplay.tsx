/**
 * Cost Estimate Display Component
 * 
 * Displays cost and carbon footprint estimates with real-time updates.
 * Validates: Requirements 9.2, 9.3, 9.4
 */

import React, { useState, useEffect } from 'react';

interface CostEstimates {
  gpu_hours: number;
  electricity_cost_usd: number;
  electricity_rate_per_kwh: number;
  carbon_footprint_kg: number;
  carbon_intensity_g_per_kwh: number;
  total_energy_kwh: number;
  confidence: number;
  formatted: {
    gpu_hours: string;
    electricity_cost: string;
    carbon_footprint: string;
    energy_consumption: string;
    electricity_rate: string;
    carbon_intensity: string;
    confidence: string;
  };
}

interface CostEstimateDisplayProps {
  trainingTimeHours: number;
  gpuName: string;
  numGpus?: number;
  electricityRate?: number;
  region?: string;
  utilization?: number;
  onEstimatesUpdate?: (estimates: CostEstimates) => void;
}

export const CostEstimateDisplay: React.FC<CostEstimateDisplayProps> = ({
  trainingTimeHours,
  gpuName,
  numGpus = 1,
  electricityRate,
  region = 'default',
  utilization = 0.85,
  onEstimatesUpdate
}) => {
  const [estimates, setEstimates] = useState<CostEstimates | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Real-time estimate updates when configuration changes
  useEffect(() => {
    const fetchEstimates = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch('http://localhost:8000/api/cost/estimate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            training_time_hours: trainingTimeHours,
            gpu_name: gpuName,
            num_gpus: numGpus,
            electricity_rate_per_kwh: electricityRate,
            region: region,
            utilization: utilization
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to fetch cost estimates');
        }

        const data = await response.json();
        setEstimates(data);
        
        if (onEstimatesUpdate) {
          onEstimatesUpdate(data);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    // Only fetch if we have valid inputs
    if (trainingTimeHours > 0 && gpuName) {
      fetchEstimates();
    }
  }, [trainingTimeHours, gpuName, numGpus, electricityRate, region, utilization, onEstimatesUpdate]);

  if (loading) {
    return (
      <div className="cost-estimate-display loading">
        <div className="spinner">Calculating estimates...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="cost-estimate-display error">
        <p>Error: {error}</p>
      </div>
    );
  }

  if (!estimates) {
    return null;
  }

  return (
    <div className="cost-estimate-display">
      <h3>Cost & Environmental Impact</h3>
      
      <div className="estimate-grid">
        <div className="estimate-card">
          <div className="estimate-icon">⚡</div>
          <div className="estimate-content">
            <div className="estimate-label">GPU Hours</div>
            <div className="estimate-value">{estimates.formatted.gpu_hours}</div>
          </div>
        </div>

        <div className="estimate-card">
          <div className="estimate-icon">💰</div>
          <div className="estimate-content">
            <div className="estimate-label">Electricity Cost</div>
            <div className="estimate-value">{estimates.formatted.electricity_cost}</div>
            <div className="estimate-detail">at {estimates.formatted.electricity_rate}</div>
          </div>
        </div>

        <div className="estimate-card">
          <div className="estimate-icon">🌱</div>
          <div className="estimate-content">
            <div className="estimate-label">Carbon Footprint</div>
            <div className="estimate-value">{estimates.formatted.carbon_footprint}</div>
            <div className="estimate-detail">{estimates.formatted.carbon_intensity}</div>
          </div>
        </div>

        <div className="estimate-card">
          <div className="estimate-icon">🔋</div>
          <div className="estimate-content">
            <div className="estimate-label">Energy Consumption</div>
            <div className="estimate-value">{estimates.formatted.energy_consumption}</div>
          </div>
        </div>
      </div>

      <div className="estimate-confidence">
        <span>Confidence: {estimates.formatted.confidence}</span>
      </div>
    </div>
  );
};

export default CostEstimateDisplay;
