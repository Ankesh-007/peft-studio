# Compute Provider Selection UI

## Overview

The Compute Provider Selection UI is a comprehensive interface that helps users select the best GPU platform for their training jobs by comparing costs, availability, and specifications across multiple cloud providers.

**Validates Requirements:** 3.1, 3.2, 3.3, 3.4, 3.5

## Features

### 1. Provider Comparison Table
- Side-by-side comparison of all available providers
- Sortable by cost, performance, or availability
- Real-time pricing updates every 30 seconds
- Detailed specifications for each instance

### 2. Real-time Pricing Display
- Current hourly rates for each GPU type
- Total cost calculation based on estimated training time
- Cost comparison with local training (if applicable)
- Savings percentage display

### 3. Availability Indicators
- Color-coded availability status:
  - 🟢 High: Instances readily available
  - 🟡 Medium: Limited availability
  - 🟠 Low: Very limited availability
  - 🔴 Unavailable: No instances currently available

### 4. Resource Specification Display
- GPU type and memory
- vCPUs and RAM
- Storage capacity
- Region information

### 5. Provider Recommendation Engine
- Automatically recommends the best option based on:
  - Cost efficiency
  - Setup time
  - Availability
  - Balance of cost and convenience
- Highlights cheapest, fastest, and recommended options

## Components

### ComputeProviderSelector

Main component for provider selection.

```typescript
import { ComputeProviderSelector } from './components/ComputeProviderSelector';

<ComputeProviderSelector
  trainingHours={2.5}
  minMemoryGb={24}
  localGpuType="RTX 4090"
  localElectricityCost={3.50}
  onProviderSelect={(platform, instance) => {
    console.log('Selected:', platform, instance);
  }}
  onCancel={() => {
    console.log('Cancelled');
  }}
/>
```

#### Props

- `trainingHours` (number, required): Estimated training time in hours
- `minMemoryGb` (number, optional): Minimum GPU memory required
- `localGpuType` (string, optional): Local GPU type for comparison
- `localElectricityCost` (number, optional): Local electricity cost for comparison
- `onProviderSelect` (function, required): Callback when provider is selected
- `onCancel` (function, optional): Callback when selection is cancelled

### ComputeProviderSelectorExample

Example component demonstrating integration.

```typescript
import { ComputeProviderSelectorExample } from './components/ComputeProviderSelectorExample';

<ComputeProviderSelectorExample />
```

## API Endpoints

### POST /api/cloud/compare-costs

Compare costs across all cloud platforms.

**Request:**
```json
{
  "training_hours": 2.5,
  "local_gpu_type": "RTX 4090",
  "local_electricity_cost": 3.50,
  "min_memory_gb": 24
}
```

**Response:**
```json
{
  "summary": {
    "cheapest": {
      "platform": "lambda_labs",
      "cost": "$2.75",
      "gpu": "A100 40GB"
    },
    "fastest": {
      "platform": "together_ai",
      "setup_time": "1 min",
      "gpu": "H100"
    },
    "recommended": {
      "platform": "lambda_labs",
      "cost": "$2.75",
      "gpu": "A100 40GB",
      "reason": "Lowest cost option"
    },
    "savings_vs_local": "21.4%"
  },
  "options": [
    {
      "platform": "lambda_labs",
      "gpu": "A100 40GB",
      "cost": "$2.75",
      "hourly_rate": "$1.10/hr",
      "setup_time": "immediate",
      "availability": "high",
      "pros": [
        "Lowest prices for A100/H100",
        "Fast NVMe storage",
        "Excellent network bandwidth"
      ],
      "cons": [
        "Limited availability (high demand)",
        "Hourly billing minimum"
      ]
    }
  ]
}
```

### GET /api/cloud/instances

List available cloud GPU instances.

**Query Parameters:**
- `gpu_type` (string, optional): Filter by GPU type
- `min_memory_gb` (number, optional): Minimum GPU memory
- `platform` (string, optional): Filter by platform

**Response:**
```json
{
  "instances": [
    {
      "platform": "runpod",
      "gpu_type": "RTX 4090",
      "gpu_count": 1,
      "memory_gb": 24,
      "vcpus": 16,
      "ram_gb": 64,
      "storage_gb": 200,
      "hourly_rate_usd": 0.69,
      "availability": "high",
      "region": "US-Central"
    }
  ],
  "count": 1
}
```

### POST /api/cloud/estimate-cost

Estimate cost for a specific platform and GPU type.

**Request:**
```json
{
  "platform": "runpod",
  "gpu_type": "RTX 4090",
  "training_hours": 2.5
}
```

**Response:**
```json
{
  "platform": "runpod",
  "gpu_type": "RTX 4090",
  "training_hours": 2.5,
  "total_cost_usd": 1.73,
  "hourly_rate_usd": 0.69,
  "setup_time_minutes": 5.0,
  "estimated_start_time": "5-10 min",
  "pros": [
    "Fast deployment",
    "Good GPU availability",
    "Flexible billing (per-minute)"
  ],
  "cons": [
    "Slightly higher prices than Lambda Labs",
    "Network storage can be slower"
  ]
}
```

### GET /api/cloud/platforms/{platform}/setup

Get setup instructions for a specific platform.

**Response:**
```json
{
  "title": "RunPod Setup",
  "steps": [
    "1. Create account at runpod.io",
    "2. Add payment method and credits",
    "3. Select GPU template (PyTorch recommended)",
    "4. Deploy pod and wait for initialization",
    "5. Connect via SSH or Jupyter notebook",
    "6. Upload your dataset and training script"
  ],
  "api_docs": "https://docs.runpod.io/",
  "estimated_time": "5-10 minutes"
}
```

## View Modes

### Table View
- Compact view showing all providers in a table
- Sortable columns
- Quick comparison of key metrics
- Best for comparing many options

### Cards View
- Detailed view with expandable pros/cons
- Visual emphasis on key information
- Better for mobile devices
- Best for detailed evaluation

## Sorting Options

- **Sort by Cost**: Shows cheapest options first
- **Sort by Speed**: Shows fastest setup times first
- **Sort by Availability**: Shows most available options first

## Auto-Refresh

The component automatically refreshes pricing every 30 seconds to ensure real-time accuracy. This can be disabled by clearing the refresh interval.

## Integration Example

```typescript
import React, { useState } from 'react';
import { ComputeProviderSelector } from './components/ComputeProviderSelector';

function TrainingWizard() {
  const [step, setStep] = useState(1);
  const [selectedProvider, setSelectedProvider] = useState(null);

  const handleProviderSelect = (platform, instance) => {
    setSelectedProvider({ platform, instance });
    setStep(3); // Move to next step
  };

  return (
    <div>
      {step === 2 && (
        <ComputeProviderSelector
          trainingHours={estimatedHours}
          minMemoryGb={requiredMemory}
          onProviderSelect={handleProviderSelect}
          onCancel={() => setStep(1)}
        />
      )}
    </div>
  );
}
```

## Property-Based Testing

The cost estimation accuracy is validated using property-based testing:

**Property 5: Cost estimation accuracy**
- For any training configuration, estimated cost should be within 20% of actual cost
- Tests verify linear scaling with training time
- Tests verify multi-GPU cost scaling
- Tests verify consistency across multiple calls

See `backend/tests/test_cost_estimation_accuracy.py` for implementation.

## Supported Platforms

### RunPod
- GPU Types: RTX 4090, RTX 3090, A100 40GB, A100 80GB, H100, A10
- Pricing: $0.44 - $4.25/hr
- Availability: Generally high
- Setup Time: 5-10 minutes

### Lambda Labs
- GPU Types: RTX 3090, A100 40GB, A100 80GB, H100, V100
- Pricing: $0.50 - $2.49/hr
- Availability: Medium (high demand)
- Setup Time: Immediate (if available)

### Together AI
- GPU Types: A100 80GB, H100
- Pricing: $2.00 - $3.50/hr (serverless equivalent)
- Availability: High (serverless)
- Setup Time: 1 minute

## Future Enhancements

- [ ] Add Vast.ai support
- [ ] Add Modal support
- [ ] Add Replicate support
- [ ] Historical pricing trends
- [ ] Price alerts and notifications
- [ ] Saved provider preferences
- [ ] Multi-region support
- [ ] Spot instance pricing
- [ ] Reserved instance discounts

## Troubleshooting

### Pricing not updating
- Check network connection
- Verify backend API is running
- Check browser console for errors

### No providers showing
- Verify minimum memory requirements aren't too high
- Check if backend services are running
- Verify API endpoints are accessible

### Incorrect cost estimates
- Verify training hours are accurate
- Check if local GPU type is correctly specified
- Ensure electricity cost is in USD

## Related Documentation

- [Cloud Platform Integration](CLOUD_PLATFORM_IMPLEMENTATION.md)
- [Cost Calculator](COST_CALCULATOR_IMPLEMENTATION.md)
- [Requirements](requirements.md)
- [Design Document](design.md)
