/**
 * Electricity Rate Input Component
 *
 * Allows users to input their electricity rate for accurate cost calculations.
 * Validates: Requirement 9.4
 */

import React, { useState, useEffect } from "react";

interface ElectricityRateInputProps {
  region?: string;
  onRateChange: (rate: number) => void;
  initialRate?: number;
}

export const ElectricityRateInput: React.FC<ElectricityRateInputProps> = ({
  region = "default",
  onRateChange,
  initialRate,
}) => {
  const [rate, setRate] = useState<number>(initialRate || 0);
  const [defaultRate, setDefaultRate] = useState<number>(0);
  const [useCustomRate, setUseCustomRate] = useState<boolean>(!!initialRate);
  const [loading, setLoading] = useState(true);

  // Fetch default rate for region
  useEffect(() => {
    const fetchDefaultRate = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/cost/electricity-rate/${region}`);

        if (response.ok) {
          const data = await response.json();
          setDefaultRate(data.electricity_rate_per_kwh);

          // If not using custom rate, use the default
          if (!useCustomRate) {
            setRate(data.electricity_rate_per_kwh);
            onRateChange(data.electricity_rate_per_kwh);
          }
        }
      } catch (err) {
        console.error("Failed to fetch default electricity rate:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchDefaultRate();
  }, [region, useCustomRate, onRateChange]);

  const handleRateChange = (value: string) => {
    const numValue = parseFloat(value);
    if (!isNaN(numValue) && numValue >= 0) {
      setRate(numValue);
      onRateChange(numValue);
    }
  };

  const handleToggleCustomRate = (checked: boolean) => {
    setUseCustomRate(checked);
    if (!checked) {
      // Revert to default rate
      setRate(defaultRate);
      onRateChange(defaultRate);
    }
  };

  if (loading) {
    return <div>Loading electricity rates...</div>;
  }

  return (
    <div className="electricity-rate-input">
      <div className="rate-header">
        <label htmlFor="electricity-rate">Electricity Rate</label>
        <div className="custom-rate-toggle">
          <input
            type="checkbox"
            id="use-custom-rate"
            checked={useCustomRate}
            onChange={(e) => handleToggleCustomRate(e.target.checked)}
          />
          <label htmlFor="use-custom-rate">Use custom rate</label>
        </div>
      </div>

      {useCustomRate ? (
        <div className="rate-input-group">
          <span className="currency-symbol">$</span>
          <input
            type="number"
            id="electricity-rate"
            value={rate}
            onChange={(e) => handleRateChange(e.target.value)}
            step="0.01"
            min="0"
            placeholder="0.15"
            className="rate-input"
          />
          <span className="rate-unit">per kWh</span>
        </div>
      ) : (
        <div className="rate-display">
          <span className="default-rate">
            ${defaultRate.toFixed(3)} per kWh (default for {region})
          </span>
        </div>
      )}

      <div className="rate-help">
        <p>
          💡 Your electricity rate affects the cost estimate. Check your utility bill for your
          actual rate.
        </p>
      </div>
    </div>
  );
};

export default ElectricityRateInput;
