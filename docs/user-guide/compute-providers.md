# Compute Provider Selection

## Overview

The Compute Provider Selection interface helps you choose the best GPU platform for your training jobs by comparing costs, availability, and specifications across multiple cloud providers and your local hardware.

## Supported Providers

### Local Training
- Use your own GPU hardware
- No hourly costs (only electricity)
- Full control over environment
- Best for: Development, testing, small models

### RunPod
- **Pricing**: Per-minute billing ($0.44 - $4.25/hr)
- **Availability**: Generally high
- **Setup Time**: 5-10 minutes
- **Best For**: Quick experiments, flexible workloads
- **GPUs**: RTX 4090, RTX 3090, A100, H100, A10

### Lambda Labs
- **Pricing**: Lowest prices ($0.50 - $2.49/hr)
- **Availability**: Medium (high demand)
- **Setup Time**: Immediate (if available)
- **Best For**: Long training runs, cost-sensitive projects
- **GPUs**: RTX 3090, A100, H100, V100

### Together AI
- **Pricing**: Serverless ($2.00 - $3.50/hr equivalent)
- **Availability**: High (auto-scaling)
- **Setup Time**: 1-2 minutes
- **Best For**: Instant availability, serverless workloads
- **GPUs**: A100 80GB, H100

## Using the Provider Selector

### Opening the Selector

The provider selector appears during the training configuration process:
1. Configure your training parameters
2. Proceed to the provider selection step
3. Review cost comparison and recommendations

### Understanding the Comparison

The interface shows:
- **Cheapest Option**: Lowest total cost
- **Fastest Option**: Quickest setup time
- **Recommended Option**: Best balance of cost and convenience
- **Savings vs Local**: Cost difference compared to local training

### Viewing Provider Details

Each provider card displays:
- **GPU Type**: Available GPU models
- **Total Cost**: Estimated cost for your training job
- **Hourly Rate**: Cost per hour
- **Setup Time**: Time to get started
- **Availability**: Current availability status
- **Pros & Cons**: Key advantages and limitations

### Selecting a Provider

1. Review the comparison table or cards
2. Consider your priorities (cost, speed, availability)
3. Click "Select" on your chosen provider
4. Proceed with training configuration

## View Modes

### Table View
- Compact comparison of all providers
- Sortable columns
- Quick overview of key metrics
- Best for comparing many options

### Cards View
- Detailed provider information
- Expandable pros and cons
- Visual emphasis on key details
- Best for mobile devices

## Sorting Options

Sort providers by:
- **Cost**: Show cheapest options first
- **Speed**: Show fastest setup times first
- **Availability**: Show most available options first

## Availability Indicators

- 🟢 **High**: Instances readily available
- 🟡 **Medium**: Limited availability
- 🟠 **Low**: Very limited availability
- 🔴 **Unavailable**: No instances currently available

## Cost Calculation

The system calculates costs based on:

### Training Hours
- Estimated from model size and dataset
- Adjustable based on your experience
- Includes setup and initialization time

### GPU Requirements
- Minimum VRAM needed
- Preferred GPU type
- Multi-GPU support (if needed)

### Local Comparison
- Your GPU type (if applicable)
- Electricity cost per kWh
- Power consumption estimate

## Recommendation Engine

The system recommends providers based on:

### Cost Efficiency
- Total cost for training job
- Hourly rate comparison
- Savings vs alternatives

### Setup Time
- Time to provision instance
- Configuration complexity
- Immediate vs delayed availability

### Convenience
- Ease of use
- Pre-configured environments
- Integration with existing tools

### Balance
- Prefers cloud if cost difference < 20% and setup is faster
- Otherwise recommends cheapest option
- Considers availability and reliability

## Real-time Updates

The interface automatically refreshes pricing every 30 seconds to ensure accuracy. You'll see:
- Current availability status
- Latest pricing information
- Updated recommendations

## Provider Setup Instructions

### RunPod Setup
1. Create account at runpod.io
2. Add payment method and credits
3. Select GPU template (PyTorch recommended)
4. Deploy pod and wait for initialization
5. Connect via SSH or Jupyter notebook
6. Upload your dataset and training script

**Estimated Time**: 5-10 minutes

### Lambda Labs Setup
1. Create account at lambdalabs.com
2. Add payment method
3. Select instance type
4. Launch instance (if available)
5. SSH into instance
6. Install dependencies and upload data

**Estimated Time**: Immediate (if available)

### Together AI Setup
1. Create account at together.ai
2. Get API key
3. Configure endpoint
4. Deploy via API or dashboard
5. Monitor via web interface

**Estimated Time**: 1-2 minutes

## Cost Optimization Tips

### Choose the Right GPU
- Don't overpay for more VRAM than needed
- Consider quantization for smaller GPUs
- Balance cost vs training time

### Optimize Training Time
- Use efficient training techniques
- Implement early stopping
- Monitor progress and adjust

### Use Spot Instances (Future)
- Save up to 70% on cloud costs
- Accept potential interruptions
- Best for fault-tolerant workloads

### Compare Regularly
- Prices and availability change
- New providers may offer better deals
- Re-evaluate for long-running projects

## Integration with Training Wizard

The provider selector integrates seamlessly with the training workflow:

1. **Configuration Step**: Set training parameters
2. **Provider Selection**: Compare and choose platform
3. **Review Step**: Confirm all settings
4. **Launch**: Start training on selected platform

## Troubleshooting

### No Providers Available
- Adjust minimum memory requirements
- Try different GPU types
- Check if backend services are running
- Verify API connectivity

### Pricing Not Updating
- Check network connection
- Verify backend API is running
- Clear browser cache
- Check console for errors

### Incorrect Cost Estimates
- Verify training hours are accurate
- Check local GPU type is correct
- Ensure electricity cost is in USD
- Review minimum memory requirements

### Provider Selection Fails
- Verify account credentials
- Check provider availability
- Review error messages
- Contact provider support

## Best Practices

### For Development
- Use local GPU or cheapest cloud option
- Short training runs for testing
- Iterate quickly with small datasets

### For Production
- Compare costs across providers
- Consider reliability and support
- Plan for longer training times
- Monitor costs regularly

### For Experimentation
- Use providers with good availability
- Balance cost and convenience
- Take advantage of free credits
- Try multiple providers

## API Integration

### Get Cost Comparison

```typescript
const comparison = await fetch('/api/cloud/compare-costs', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    training_hours: 10.0,
    local_gpu_type: 'RTX 4090',
    local_electricity_cost: 2.50,
    min_memory_gb: 24
  })
});

const data = await comparison.json();
console.log('Recommended:', data.summary.recommended);
```

### List Available Instances

```typescript
const instances = await fetch('/api/cloud/instances', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    gpu_type: 'A100 80GB',
    min_memory_gb: 40
  })
});

const data = await instances.json();
console.log('Available instances:', data.instances);
```

### Get Setup Instructions

```typescript
const instructions = await fetch('/api/cloud/setup-instructions/runpod');
const data = await instructions.json();

console.log('Setup time:', data.estimated_time);
data.steps.forEach(step => console.log(step));
```

## Future Enhancements

- **Additional Providers**: Vast.ai, Modal, Replicate
- **Historical Pricing**: Track price trends over time
- **Price Alerts**: Notifications when prices drop
- **Saved Preferences**: Remember your provider choices
- **Multi-Region Support**: Choose specific regions
- **Spot Instances**: Access discounted pricing
- **Reserved Instances**: Long-term discounts
- **Auto-Migration**: Switch providers automatically

## Related Documentation

- [Cloud Platforms](../developer-guide/cloud-platforms.md)
- [Training Configuration](training-configuration.md)
- [Cost Calculator](../developer-guide/cost-calculator.md)
- [Platform Connections](platform-connections.md)
