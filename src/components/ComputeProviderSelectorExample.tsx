/**
 * Example usage of ComputeProviderSelector
 * 
 * This demonstrates how to integrate the compute provider selection UI
 * into a training configuration workflow.
 */

import React, { useState } from 'react';
import { ComputeProviderSelector } from './ComputeProviderSelector';

interface GPUInstance {
  platform: string;
  gpu_type: string;
  gpu_count: number;
  memory_gb: number;
  vcpus: number;
  ram_gb: number;
  storage_gb: number;
  hourly_rate_usd: number;
  availability: 'high' | 'medium' | 'low' | 'unavailable';
  region: string;
  instance_id?: string;
}

export const ComputeProviderSelectorExample: React.FC = () => {
  const [showSelector, setShowSelector] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [selectedInstance, setSelectedInstance] = useState<GPUInstance | null>(null);
  
  // Example training configuration
  const [trainingHours, setTrainingHours] = useState(2.5);
  const [minMemoryGb, setMinMemoryGb] = useState(24);
  const [localGpuType, setLocalGpuType] = useState<string>('RTX 4090');
  const [localElectricityCost, setLocalElectricityCost] = useState<number>(3.50);

  const handleProviderSelect = (platform: string, instance: GPUInstance) => {
    setSelectedProvider(platform);
    setSelectedInstance(instance);
    setShowSelector(false);
    
    console.log('Selected provider:', platform);
    console.log('Selected instance:', instance);
    
    // Here you would typically proceed to the next step in your workflow
    // For example, starting the training job with the selected provider
  };

  const handleCancel = () => {
    setShowSelector(false);
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Compute Provider Selection Demo</h1>
      
      {!showSelector ? (
        <div className="space-y-6">
          {/* Configuration Panel */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Training Configuration</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Estimated Training Time (hours)
                </label>
                <input
                  type="number"
                  value={trainingHours}
                  onChange={(e) => setTrainingHours(parseFloat(e.target.value))}
                  step="0.1"
                  min="0.1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Minimum GPU Memory (GB)
                </label>
                <input
                  type="number"
                  value={minMemoryGb}
                  onChange={(e) => setMinMemoryGb(parseInt(e.target.value))}
                  step="1"
                  min="1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Local GPU Type (optional)
                </label>
                <select
                  value={localGpuType}
                  onChange={(e) => setLocalGpuType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">None</option>
                  <option value="RTX 4090">RTX 4090</option>
                  <option value="RTX 3090">RTX 3090</option>
                  <option value="A100 40GB">A100 40GB</option>
                  <option value="A100 80GB">A100 80GB</option>
                  <option value="H100">H100</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Local Electricity Cost (USD, optional)
                </label>
                <input
                  type="number"
                  value={localElectricityCost}
                  onChange={(e) => setLocalElectricityCost(parseFloat(e.target.value))}
                  step="0.1"
                  min="0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
            
            <button
              onClick={() => setShowSelector(true)}
              className="mt-6 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
            >
              Select Compute Provider
            </button>
          </div>
          
          {/* Selected Provider Display */}
          {selectedProvider && selectedInstance && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-green-900 mb-4">
                ✓ Provider Selected
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-green-700 mb-1">Platform</p>
                  <p className="text-lg font-semibold text-green-900 capitalize">
                    {selectedProvider.replace('_', ' ')}
                  </p>
                </div>
                
                <div>
                  <p className="text-sm text-green-700 mb-1">GPU</p>
                  <p className="text-lg font-semibold text-green-900">
                    {selectedInstance.gpu_type}
                  </p>
                </div>
                
                <div>
                  <p className="text-sm text-green-700 mb-1">Cost</p>
                  <p className="text-lg font-semibold text-green-900">
                    ${(selectedInstance.hourly_rate_usd * trainingHours).toFixed(2)}
                  </p>
                </div>
                
                <div>
                  <p className="text-sm text-green-700 mb-1">Availability</p>
                  <p className="text-lg font-semibold text-green-900 capitalize">
                    {selectedInstance.availability}
                  </p>
                </div>
              </div>
              
              <div className="mt-4 flex gap-3">
                <button
                  onClick={() => setShowSelector(true)}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
                >
                  Change Provider
                </button>
                
                <button
                  onClick={() => {
                    // Proceed to next step
                    alert('Proceeding to training configuration...');
                  }}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                  Continue to Training
                </button>
              </div>
            </div>
          )}
          
          {/* Info Panel */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-2">
              About Compute Provider Selection
            </h3>
            <p className="text-blue-800 mb-3">
              The compute provider selector helps you choose the best GPU platform for your training job by comparing:
            </p>
            <ul className="space-y-2 text-blue-800">
              <li className="flex items-start">
                <span className="text-blue-500 mr-2">•</span>
                <span><strong>Cost:</strong> Real-time pricing across RunPod, Lambda Labs, and Together AI</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-500 mr-2">•</span>
                <span><strong>Availability:</strong> Current GPU availability status</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-500 mr-2">•</span>
                <span><strong>Performance:</strong> Setup time and estimated start time</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-500 mr-2">•</span>
                <span><strong>Specifications:</strong> GPU memory, vCPUs, RAM, and storage</span>
              </li>
            </ul>
          </div>
        </div>
      ) : (
        <ComputeProviderSelector
          trainingHours={trainingHours}
          minMemoryGb={minMemoryGb}
          localGpuType={localGpuType || undefined}
          localElectricityCost={localElectricityCost || undefined}
          onProviderSelect={handleProviderSelect}
          onCancel={handleCancel}
        />
      )}
    </div>
  );
};

export default ComputeProviderSelectorExample;
