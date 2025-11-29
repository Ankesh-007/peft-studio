# Cloud Platform Integration

This document describes the cloud platform integration feature that allows users to compare costs and deploy training jobs across multiple cloud GPU providers.

## Overview

The cloud platform integration provides:
- **RunPod API Integration**: Fast deployment with flexible per-minute billing
- **Lambda Labs Integration**: Access to H100/A100 GPUs at competitive prices
- **Together AI Integration**: Serverless endpoints with instant availability
- **Cost Comparison**: Compare costs across all platforms including local training

## Supported Platforms

### RunPod
- **Pricing**: Per-minute billing
- **Availability**: High (good GPU availability)
- **Setup Time**: 5-10 minutes
- **Best For**: Quick experiments, flexible workloads
- **GPUs Available**: RTX 4090, RTX 3090, A100 (40GB/80GB), H100, A10

### Lambda Labs
- **Pricing**: Lowest prices for A100/H100
- **Availability**: Medium (high demand, may need to wait)
- **Setup Time**: Immediate (if available)
- **Best For**: Long training runs, cost-sensitive projects
- **GPUs Available**: RTX 3090, A100 (40GB/80GB), H100, V100

### Together AI
- **Pricing**: Serverless, pay-per-use
- **Availability**: High (serverless auto-scaling)
- **Setup Time**: 1-2 minutes
- **Best For**: Serverless workloads, instant availability
- **GPUs Available**: A100 (80GB), H100

## API Endpoints

### Get Cloud Instances

```http
POST /api/cloud/instances
Content-Type: application/json

{
  "gpu_type": "A100 80GB",  // Optional
  "min_memory_gb": 40       // Optional
}
```

**Response:**
```json
{
  "instances": [
    {
      "platform": "lambda_labs",
      "gpu_type": "A100 80GB",
      "gpu_count": 1,
      "memory_gb": 80,
      "vcpus": 30,
      "ram_gb": 200,
      "storage_gb": 512,
      "hourly_rate_usd": 1.29,
      "availability": "medium",
      "region": "US-West"
    }
  ],
  "count": 15
}
```

### Get Platform-Specific Instances

```http
GET /api/cloud/platforms/runpod?gpu_type=A100%2080GB&min_memory_gb=40
```

**Response:**
```json
{
  "platform": "runpod",
  "instances": [
    {
      "gpu_type": "A100 80GB",
      "gpu_count": 1,
      "memory_gb": 80,
      "vcpus": 32,
      "ram_gb": 256,
      "storage_gb": 200,
      "hourly_rate_usd": 2.49,
      "availability": "high",
      "region": "US-Central"
    }
  ],
  "count": 1
}
```

### Compare Costs Across Platforms

```http
POST /api/cloud/compare-costs
Content-Type: application/json

{
  "training_hours": 10.0,
  "local_gpu_type": "RTX 4090",      // Optional
  "local_electricity_cost": 2.50,    // Optional
  "min_memory_gb": 24                // Optional
}
```

**Response:**
```json
{
  "summary": {
    "cheapest": {
      "platform": "lambda_labs",
      "cost": "$12.90",
      "gpu": "A100 80GB"
    },
    "fastest": {
      "platform": "together_ai",
      "setup_time": "1 min",
      "gpu": "H100"
    },
    "recommended": {
      "platform": "lambda_labs",
      "cost": "$12.90",
      "gpu": "A100 80GB",
      "reason": "Lowest cost option"
    },
    "savings_vs_local": "48.4%"
  },
  "options": [
    {
      "platform": "lambda_labs",
      "gpu": "A100 80GB",
      "cost": "$12.90",
      "hourly_rate": "$1.29/hr",
      "setup_time": "immediate",
      "availability": "medium",
      "pros": [
        "Lowest prices for A100/H100",
        "Fast NVMe storage",
        "Excellent network bandwidth",
        "Pre-configured ML environments"
      ],
      "cons": [
        "Limited availability (high demand)",
        "Hourly billing minimum",
        "May need to wait for instances"
      ]
    }
  ]
}
```

### Get Setup Instructions

```http
GET /api/cloud/setup-instructions/runpod
```

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

### List Available GPU Types

```http
GET /api/cloud/gpu-types
```

**Response:**
```json
{
  "gpu_types": [
    "RTX 4090",
    "RTX 3090",
    "A100 40GB",
    "A100 80GB",
    "H100",
    "A10",
    "V100",
    "T4"
  ]
}
```

### List Supported Platforms

```http
GET /api/cloud/platforms
```

**Response:**
```json
{
  "platforms": [
    {
      "id": "runpod",
      "name": "RunPod",
      "description": "Fast deployment with flexible billing",
      "features": [
        "Per-minute billing",
        "Good GPU availability",
        "Easy to use"
      ]
    },
    {
      "id": "lambda_labs",
      "name": "Lambda Labs",
      "description": "Lowest prices for A100/H100 GPUs",
      "features": [
        "Best prices",
        "Fast NVMe storage",
        "Pre-configured ML environments"
      ]
    },
    {
      "id": "together_ai",
      "name": "Together AI",
      "description": "Serverless endpoints with instant availability",
      "features": [
        "Instant availability",
        "Auto-scaling",
        "Pay per use"
      ]
    }
  ]
}
```

## Usage Examples

### Python Client Example

```python
import requests

# Get all cloud instances
response = requests.post(
    "http://localhost:8000/api/cloud/instances",
    json={
        "min_memory_gb": 40
    }
)
instances = response.json()["instances"]

# Compare costs
response = requests.post(
    "http://localhost:8000/api/cloud/compare-costs",
    json={
        "training_hours": 10.0,
        "local_gpu_type": "RTX 4090",
        "local_electricity_cost": 2.50,
        "min_memory_gb": 24
    }
)
comparison = response.json()

print(f"Cheapest option: {comparison['summary']['cheapest']['platform']}")
print(f"Cost: {comparison['summary']['cheapest']['cost']}")
print(f"Savings vs local: {comparison['summary'].get('savings_vs_local', 'N/A')}")

# Get setup instructions
response = requests.get(
    "http://localhost:8000/api/cloud/setup-instructions/lambda_labs"
)
instructions = response.json()
print(f"Setup time: {instructions['estimated_time']}")
for step in instructions['steps']:
    print(step)
```

### TypeScript/React Example

```typescript
import { useState, useEffect } from 'react';

interface CostComparison {
  summary: {
    cheapest: {
      platform: string;
      cost: string;
      gpu: string;
    };
    recommended: {
      platform: string;
      cost: string;
      gpu: string;
      reason: string;
    };
  };
  options: Array<{
    platform: string;
    gpu: string;
    cost: string;
    hourly_rate: string;
    pros: string[];
    cons: string[];
  }>;
}

function CloudCostComparison() {
  const [comparison, setComparison] = useState<CostComparison | null>(null);
  
  useEffect(() => {
    async function fetchComparison() {
      const response = await fetch('/api/cloud/compare-costs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          training_hours: 10.0,
          min_memory_gb: 24
        })
      });
      
      const data = await response.json();
      setComparison(data);
    }
    
    fetchComparison();
  }, []);
  
  if (!comparison) return <div>Loading...</div>;
  
  return (
    <div>
      <h2>Cost Comparison</h2>
      <div>
        <h3>Recommended: {comparison.summary.recommended.platform}</h3>
        <p>Cost: {comparison.summary.recommended.cost}</p>
        <p>GPU: {comparison.summary.recommended.gpu}</p>
        <p>Reason: {comparison.summary.recommended.reason}</p>
      </div>
      
      <h3>All Options</h3>
      {comparison.options.map((option, idx) => (
        <div key={idx}>
          <h4>{option.platform} - {option.gpu}</h4>
          <p>Cost: {option.cost} ({option.hourly_rate})</p>
          <div>
            <strong>Pros:</strong>
            <ul>
              {option.pros.map((pro, i) => <li key={i}>{pro}</li>)}
            </ul>
          </div>
          <div>
            <strong>Cons:</strong>
            <ul>
              {option.cons.map((con, i) => <li key={i}>{con}</li>)}
            </ul>
          </div>
        </div>
      ))}
    </div>
  );
}
```

## Cost Calculation

The service calculates costs based on:
1. **Hourly Rate**: Platform-specific GPU hourly rates
2. **Training Hours**: Estimated training duration
3. **Setup Time**: Time to provision and configure the instance
4. **Availability**: Current availability status

### Cost Comparison Logic

The service recommends platforms based on:
- **Cheapest**: Lowest total cost
- **Fastest**: Lowest setup time + training time
- **Recommended**: Balance of cost and convenience
  - Prefers cloud if cost difference < 20% and setup is faster
  - Otherwise recommends cheapest option

## Pricing (Approximate, as of 2024)

### RunPod
- RTX 4090: $0.69/hr
- RTX 3090: $0.44/hr
- A100 40GB: $1.89/hr
- A100 80GB: $2.49/hr
- H100: $4.25/hr
- A10: $0.79/hr

### Lambda Labs
- RTX 3090: $0.50/hr
- A100 40GB: $1.10/hr
- A100 80GB: $1.29/hr
- H100: $2.49/hr
- V100: $0.50/hr

### Together AI
- A100 80GB: ~$2.00/hr (serverless equivalent)
- H100: ~$3.50/hr (serverless equivalent)

**Note**: Prices are approximate and may vary. Check platform websites for current pricing.

## Integration with Training Wizard

The cloud platform integration is designed to work seamlessly with the Training Wizard:

1. **Step 4: Configuration** - Show cost estimates for local and cloud options
2. **Step 5: Review** - Display cost comparison and allow platform selection
3. **Launch** - Optionally deploy to selected cloud platform

## Future Enhancements

- **Direct API Integration**: Automatically provision and deploy to cloud platforms
- **Cost Tracking**: Track actual costs vs estimates
- **Auto-Migration**: Automatically migrate to cheaper platforms when available
- **Spot Instances**: Support for spot/preemptible instances for cost savings
- **Multi-GPU**: Support for multi-GPU training across platforms

## Testing

Run the test suite:

```bash
pytest backend/tests/test_cloud_platform.py -v
```

The tests verify:
- Instance retrieval from all platforms
- Filtering by GPU type and memory
- Cost calculation accuracy
- Cost comparison logic
- Pricing reasonableness
- Recommendation logic

## Requirements Validation

This implementation validates:
- **Requirement 9.2**: Cost estimates include GPU hours, electricity cost, and carbon footprint
- The cloud platform integration extends this by providing cost comparison across multiple platforms

## Notes

- Pricing data is hardcoded and should be updated periodically
- Actual availability may vary and should be checked with platform APIs
- Setup times are estimates based on typical deployment scenarios
- The service does not currently make actual API calls to cloud providers (future enhancement)
