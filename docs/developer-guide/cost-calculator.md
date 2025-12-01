# Cost and Carbon Footprint Calculator

## Overview

The Cost Calculator Service provides comprehensive cost and environmental impact estimates for LLM training runs. It calculates electricity costs, GPU hours, energy consumption, and carbon footprint based on hardware specifications and training duration.

## Features

### 1. Electricity Cost Calculator (Requirement 9.4)
- User-input electricity rate support
- Default rates for major regions
- Real-time cost updates when rate changes

### 2. GPU Hours Estimator (Requirement 9.2)
- Accurate GPU hour calculation
- Multi-GPU support
- Scales linearly with training time and GPU count

### 3. Carbon Footprint Calculator (Requirement 9.2)
- Regional carbon intensity data
- CO₂ emissions in kg
- Based on actual grid carbon intensity

### 4. Real-Time Estimate Updates (Requirement 9.3)
- Automatic recalculation on configuration changes
- Sub-second response times
- WebSocket support for live updates

## API Endpoints

### POST /api/cost/estimate
Calculate complete cost and carbon footprint estimates.

**Request:**
```json
{
  "training_time_hours": 2.5,
  "gpu_name": "RTX 4090",
  "num_gpus": 1,
  "electricity_rate_per_kwh": 0.15,
  "region": "US",
  "utilization": 0.85
}
```

**Response:**
```json
{
  "gpu_hours": 2.5,
  "electricity_cost_usd": 0.35,
  "electricity_rate_per_kwh": 0.15,
  "carbon_footprint_kg": 0.96,
  "carbon_intensity_g_per_kwh": 386,
  "total_energy_kwh": 2.5,
  "confidence": 0.7,
  "formatted": {
    "gpu_hours": "2.5 GPU hours",
    "electricity_cost": "$0.35",
    "carbon_footprint": "0.96 kg CO₂",
    "energy_consumption": "2.50 kWh",
    "electricity_rate": "$0.150/kWh",
    "carbon_intensity": "386g CO₂/kWh",
    "confidence": "70%"
  }
}
```

### GET /api/cost/electricity-rate/{region}
Get default electricity rate for a region.

**Response:**
```json
{
  "region": "US",
  "electricity_rate_per_kwh": 0.14
}
```

### GET /api/cost/carbon-intensity/{region}
Get carbon intensity for a region.

**Response:**
```json
{
  "region": "US",
  "carbon_intensity_g_per_kwh": 386
}
```

### GET /api/cost/gpu-power/{gpu_name}
Get power consumption profile for a GPU model.

**Response:**
```json
{
  "model_name": "RTX 4090",
  "tdp_watts": 450,
  "avg_power_watts": 400,
  "idle_power_watts": 50
}
```

## GPU Power Profiles

The service includes power profiles for common GPUs:

### Consumer GPUs
- RTX 4090: 450W TDP, 400W avg training
- RTX 4080: 320W TDP, 280W avg training
- RTX 4070: 200W TDP, 180W avg training
- RTX 3090: 350W TDP, 320W avg training
- RTX 3080: 320W TDP, 290W avg training
- RTX 3070: 220W TDP, 200W avg training

### Data Center GPUs
- H100: 700W TDP, 600W avg training
- A100: 400W TDP, 350W avg training
- A100-80GB: 400W TDP, 350W avg training
- V100: 300W TDP, 270W avg training
- A10: 150W TDP, 130W avg training
- T4: 70W TDP, 60W avg training

## Regional Carbon Intensity

Carbon intensity values (grams CO₂ per kWh):

- **France (FR):** 57g/kWh - Nuclear heavy grid
- **Canada (CA):** 120g/kWh - Hydro heavy grid
- **California (US-CA):** 200g/kWh - Clean energy mix
- **UK:** 233g/kWh
- **EU:** 275g/kWh - European Union average
- **US:** 386g/kWh - United States average
- **Global Default:** 400g/kWh
- **Texas (US-TX):** 450g/kWh - More fossil fuels
- **Japan (JP):** 462g/kWh
- **Australia (AU):** 510g/kWh
- **China (CN):** 555g/kWh
- **India (IN):** 632g/kWh

## Default Electricity Rates

Default rates (USD per kWh):

- **US:** $0.14/kWh
- **Global Default:** $0.15/kWh
- **EU:** $0.25/kWh
- **UK:** $0.30/kWh

## Calculation Methodology

### Energy Consumption
```
Average Power = Idle Power + (Training Power - Idle Power) × Utilization
Energy (kWh) = (Average Power / 1000) × Training Hours × Number of GPUs
```

### Electricity Cost
```
Cost (USD) = Energy (kWh) × Electricity Rate ($/kWh)
```

### Carbon Footprint
```
Carbon (kg CO₂) = Energy (kWh) × Carbon Intensity (g/kWh) / 1000
```

### GPU Hours
```
GPU Hours = Training Time (hours) × Number of GPUs
```

## Usage Examples

### Python Backend
```python
from services.cost_calculator_service import get_cost_calculator

calculator = get_cost_calculator()

estimates = calculator.calculate_complete_estimates(
    training_time_hours=2.5,
    gpu_name="RTX 4090",
    num_gpus=1,
    electricity_rate_per_kwh=0.15,
    region="US",
    utilization=0.85
)

print(f"Cost: ${estimates.electricity_cost_usd:.2f}")
print(f"Carbon: {estimates.carbon_footprint_kg:.2f} kg CO₂")
print(f"GPU Hours: {estimates.gpu_hours:.1f}")
```

### React Frontend
```typescript
import { CostEstimateDisplay } from './components/CostEstimateDisplay';

<CostEstimateDisplay
  trainingTimeHours={2.5}
  gpuName="RTX 4090"
  numGpus={1}
  electricityRate={0.15}
  region="US"
  onEstimatesUpdate={(estimates) => {
    console.log('Updated estimates:', estimates);
  }}
/>
```

## Testing

Run the test suite:
```bash
python -m pytest backend/tests/test_cost_calculator.py -v
```

Test coverage includes:
- GPU hours calculation (single and multi-GPU)
- Energy consumption calculation
- Electricity cost calculation (with user rate and defaults)
- Carbon footprint calculation
- Complete estimates calculation
- Scaling validation (time, GPUs, rates, regions)
- Singleton pattern validation

## Integration with Training Wizard

The cost calculator integrates with the Training Wizard to provide:

1. **Pre-training estimates** - Show costs before starting training
2. **Real-time updates** - Update estimates as configuration changes
3. **User customization** - Allow users to input their electricity rate
4. **Regional awareness** - Adjust carbon footprint based on location
5. **Confidence intervals** - Show estimate reliability

## Future Enhancements

- Cloud provider cost integration (AWS, GCP, Azure)
- Historical cost tracking
- Cost optimization suggestions
- Carbon offset recommendations
- Time-of-day pricing support
- Renewable energy percentage tracking
