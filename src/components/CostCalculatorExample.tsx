/**
 * Cost Calculator Example Component
 *
 * Demonstrates the complete cost calculator integration with:
 * - User-input electricity rate (Requirement 9.4)
 * - GPU hours estimation (Requirement 9.2)
 * - Carbon footprint calculation (Requirement 9.2)
 * - Real-time estimate updates (Requirement 9.3)
 */

import React, { useState } from "react";

import CostEstimateDisplay from "./CostEstimateDisplay";
import ElectricityRateInput from "./ElectricityRateInput";

export const CostCalculatorExample: React.FC = () => {
  const [trainingTime, setTrainingTime] = useState<number>(2.5);
  const [gpuName, setGpuName] = useState<string>("RTX 4090");
  const [numGpus, setNumGpus] = useState<number>(1);
  const [electricityRate, setElectricityRate] = useState<number | undefined>(
    undefined,
  );
  const [region, setRegion] = useState<string>("US");

  const gpuOptions = [
    "RTX 4090",
    "RTX 4080",
    "RTX 4070",
    "RTX 3090",
    "RTX 3080",
    "A100",
    "A100-80GB",
    "H100",
    "V100",
    "T4",
  ];

  const regionOptions = [
    { value: "US", label: "United States" },
    { value: "US-CA", label: "California" },
    { value: "US-TX", label: "Texas" },
    { value: "EU", label: "European Union" },
    { value: "UK", label: "United Kingdom" },
    { value: "DE", label: "Germany" },
    { value: "FR", label: "France" },
    { value: "CN", label: "China" },
    { value: "IN", label: "India" },
    { value: "JP", label: "Japan" },
    { value: "AU", label: "Australia" },
    { value: "CA", label: "Canada" },
  ];

  return (
    <div className="cost-calculator-example">
      <h2>Training Cost & Carbon Footprint Calculator</h2>

      <div className="calculator-controls">
        <div className="control-group">
          <label htmlFor="training-time">Training Time (hours)</label>
          <input
            type="number"
            id="training-time"
            value={trainingTime}
            onChange={(e) => setTrainingTime(parseFloat(e.target.value) || 0)}
            step="0.1"
            min="0"
          />
        </div>

        <div className="control-group">
          <label htmlFor="gpu-name">GPU Model</label>
          <select
            id="gpu-name"
            value={gpuName}
            onChange={(e) => setGpuName(e.target.value)}
          >
            {gpuOptions.map((gpu) => (
              <option key={gpu} value={gpu}>
                {gpu}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="num-gpus">Number of GPUs</label>
          <input
            type="number"
            id="num-gpus"
            value={numGpus}
            onChange={(e) => setNumGpus(parseInt(e.target.value) || 1)}
            min="1"
            max="8"
          />
        </div>

        <div className="control-group">
          <label htmlFor="region">Region</label>
          <select
            id="region"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
          >
            {regionOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group full-width">
          <ElectricityRateInput
            region={region}
            onRateChange={setElectricityRate}
            initialRate={electricityRate}
          />
        </div>
      </div>

      <div className="estimates-section">
        <CostEstimateDisplay
          trainingTimeHours={trainingTime}
          gpuName={gpuName}
          numGpus={numGpus}
          electricityRate={electricityRate}
          region={region}
          onEstimatesUpdate={(estimates) => {
            console.log("Estimates updated:", estimates);
          }}
        />
      </div>

      <div className="info-section">
        <h3>About These Estimates</h3>
        <ul>
          <li>
            <strong>GPU Hours:</strong> Total GPU time = training time × number
            of GPUs
          </li>
          <li>
            <strong>Electricity Cost:</strong> Based on GPU power consumption
            and your electricity rate
          </li>
          <li>
            <strong>Carbon Footprint:</strong> CO₂ emissions based on regional
            grid carbon intensity
          </li>
          <li>
            <strong>Real-time Updates:</strong> Estimates update automatically
            when you change any parameter
          </li>
        </ul>
      </div>
    </div>
  );
};

export default CostCalculatorExample;
