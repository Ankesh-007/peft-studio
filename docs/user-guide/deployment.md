# Deployment Management Guide

## Overview

PEFT Studio's deployment management system enables you to deploy fine-tuned models across multiple platforms with a comprehensive interface for configuration, monitoring, and testing. Deploy to Predibase, Together AI, Modal, or Replicate with just a few clicks.

## Supported Platforms

### 1. Predibase 🚀
- **Hot-swappable adapter serving**: Deploy multiple adapters on shared base models
- **LoRAX multi-adapter support**: Efficient serving of multiple LoRA adapters
- **Cost-effective**: Share base models across deployments
- **Enterprise-grade reliability**: Production-ready infrastructure

### 2. Together AI ⚡
- **Serverless endpoints**: No infrastructure management required
- **Pay-per-token pricing**: Only pay for what you use
- **Auto-scaling**: Automatically scales with demand
- **Global CDN**: Fast inference worldwide
- **Fast cold starts**: Minimal latency for first requests

### 3. Modal 🎯
- **Function deployment**: Deploy as serverless functions
- **Optimized cold-start times**: Fast initialization
- **Flexible configuration**: Customize compute resources
- **Python-native**: Seamless Python integration

### 4. Replicate 🔄
- **Simple deployment**: Easy setup and configuration
- **Version management**: Track and manage deployment versions
- **Public/private options**: Control access to your models
- **Docker-based**: Containerized deployments

## Getting Started

### Creating a Deployment

1. **Open Deployment Management**
   - Navigate to the "Deployments" section in PEFT Studio
   - Click "New Deployment" to start the configuration wizard

2. **Select Platform** (Step 1)
   - Choose from Predibase, Together AI, Modal, or Replicate
   - Review platform features and capabilities
   - Consider your use case:
     - **Predibase**: Best for multiple adapters on shared base models
     - **Together AI**: Best for serverless, pay-per-use scenarios
     - **Modal**: Best for Python-native function deployments
     - **Replicate**: Best for simple, version-controlled deployments

3. **Configure Model** (Step 2)
   - Enter a deployment name (e.g., "customer-support-bot")
   - Select your fine-tuned model or adapter
   - View the base model information

4. **Set Configuration** (Step 3)
   - **Scaling Settings**:
     - Minimum instances: Baseline capacity
     - Maximum instances: Peak capacity
     - Auto-scaling: Enable automatic scaling based on demand
   - **Performance Settings**:
     - Instance type: Choose compute resources
     - Batch size: Number of requests to batch together
     - Timeout: Maximum request duration
   - **Additional Settings**:
     - Description: Document your deployment
     - Environment variables: Platform-specific configuration

5. **Review & Deploy** (Step 4)
   - Review all configuration settings
   - Verify platform, model, and scaling settings
   - Click "Deploy" to start deployment
   - Monitor deployment progress on the dashboard

### Deployment Lifecycle

#### Status States

- **Pending**: Deployment created, waiting to start
- **Deploying**: Actively deploying to platform
- **Active**: Successfully deployed and serving requests
- **Failed**: Deployment encountered an error
- **Stopped**: Deployment manually stopped

#### Managing Deployments

**View All Deployments**
- The dashboard displays all deployments with real-time status
- Auto-refreshes every 5 seconds
- Shows key metrics: requests, success rate, latency, cost

**Filter Deployments**
- By status: All, Active, Deploying, Pending, Failed, Stopped
- By platform: All, Predibase, Together AI, Modal, Replicate

**Stop a Deployment**
- Click "Stop" on any active deployment
- Confirms before stopping
- Deployment status changes to "Stopped"
- Can be redeployed later

**Update Configuration**
- Modify scaling settings
- Update instance types
- Change timeout values
- Apply changes without redeployment (platform-dependent)

## Testing Endpoints

### Interactive Testing Interface

1. **Open Testing Interface**
   - Click "Test" on any active deployment
   - Testing modal opens with configuration options

2. **Configure Test Request**
   - **Prompt**: Enter the text prompt for your model
   - **Max Tokens**: Set maximum response length (default: 100)
   - **Temperature**: Control randomness (0.0-2.0, default: 0.7)
   - **Top P**: Control diversity (0.0-1.0, default: 0.9)

3. **Send Test Request**
   - Click "Send Test Request"
   - System measures latency automatically
   - Response displays with success/error indicator

4. **View Results**
   - **Response Data**: Model output (formatted JSON)
   - **Latency**: Request duration in milliseconds
   - **Status**: Success or error indicator
   - **Test History**: Last 10 tests with timestamps

### Endpoint Information

Each active deployment provides:
- **Endpoint URL**: Direct API endpoint for inference
- **Copy Button**: Quickly copy endpoint URL
- **Example Code**: Integration examples (coming soon)

### Testing Best Practices

- **Start Simple**: Test with basic prompts first
- **Vary Parameters**: Try different temperature and top_p values
- **Monitor Latency**: Track response times for performance
- **Check History**: Review past tests to identify patterns
- **Test Edge Cases**: Verify behavior with unusual inputs

## Monitoring and Metrics

### Dashboard Overview

The deployment dashboard provides real-time statistics:

**Summary Cards**
- **Total Deployments**: All deployments across platforms
- **Active Deployments**: Currently serving requests
- **Deploying**: In-progress deployments
- **Failed Deployments**: Deployments with errors

**Deployment Cards**
Each deployment shows:
- Platform and status
- Model path
- Endpoint URL
- Average latency
- Request count
- Success rate
- Estimated cost
- Error messages (if failed)

### Detailed Metrics View

Click "Metrics" on any deployment to view comprehensive usage data:

#### Request Statistics
- **Total Requests**: All requests since deployment
- **Successful Requests**: Completed successfully
- **Failed Requests**: Errors or timeouts
- **Success Rate**: Percentage of successful requests

#### Latency Metrics
- **Average Latency**: Mean response time
- **P50 (Median)**: 50th percentile latency
- **P95**: 95th percentile latency
- **P99**: 99th percentile latency
- **Visual Distribution**: Bar chart showing latency spread

#### Token Usage
- **Input Tokens**: Total tokens in requests
- **Output Tokens**: Total tokens in responses
- **Total Tokens**: Combined input and output

#### Cost Tracking
- **Total Cost**: Estimated cost since deployment
- **Cost Per Request**: Average cost per inference
- **Cost Breakdown**: Platform-specific pricing details

#### Summary Metrics
- **Average Tokens Per Request**: Typical request size
- **Requests Per Minute**: Current throughput
- **Error Rate**: Percentage of failed requests

### Auto-Refresh

- **Dashboard**: Refreshes every 5 seconds
- **Metrics View**: Refreshes every 30 seconds
- **Manual Refresh**: Click refresh button anytime

## API Integration

### Using Deployment Endpoints

Once deployed, your model is accessible via REST API:

```bash
# Example: Send inference request
curl -X POST https://your-endpoint-url/v1/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Your prompt here",
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

### Platform-Specific Details

#### Predibase
- Supports multi-adapter requests
- Specify adapter in request headers
- Hot-swap between adapters without redeployment

#### Together AI
- Standard OpenAI-compatible API
- Automatic scaling based on traffic
- Global endpoint routing

#### Modal
- Function-based invocation
- Custom request/response formats
- Python SDK available

#### Replicate
- Version-specific endpoints
- Public/private access control
- Webhook support for async requests

## Error Handling

### Common Issues

#### Deployment Failed
**Symptoms**: Status shows "Failed" with error message

**Solutions**:
- Check platform credentials in Settings
- Verify model exists and is accessible
- Review configuration for invalid settings
- Check platform status page for outages
- Contact platform support if issue persists

#### Endpoint Not Responding
**Symptoms**: Test requests timeout or fail

**Solutions**:
- Verify deployment status is "Active"
- Check endpoint URL is correct
- Ensure platform credentials are valid
- Test with simpler prompts
- Review platform-specific timeout limits

#### High Latency
**Symptoms**: Slow response times in metrics

**Solutions**:
- Increase minimum instances for faster cold starts
- Enable auto-scaling for traffic spikes
- Choose higher-performance instance types
- Optimize prompt length
- Consider different platform for your use case

#### High Costs
**Symptoms**: Unexpected cost increases

**Solutions**:
- Review token usage in metrics
- Reduce max_tokens in requests
- Optimize prompts for efficiency
- Set up cost alerts (coming soon)
- Consider switching to more cost-effective platform

### Error Messages

The system provides detailed error messages for:
- **Connection Errors**: Network or platform connectivity issues
- **Authentication Errors**: Invalid or expired credentials
- **Configuration Errors**: Invalid deployment settings
- **Resource Errors**: Insufficient quota or capacity
- **Timeout Errors**: Requests exceeding time limits

## Performance Optimization

### Scaling Configuration

**Minimum Instances**
- Set to 0 for cost savings (cold starts)
- Set to 1+ for consistent low latency
- Balance cost vs. performance

**Maximum Instances**
- Set based on expected peak traffic
- Higher values handle traffic spikes
- Monitor actual usage to optimize

**Auto-Scaling**
- Enable for variable traffic patterns
- Automatically adjusts capacity
- Reduces costs during low traffic

### Instance Types

Choose instance types based on:
- **Model Size**: Larger models need more memory
- **Latency Requirements**: Faster instances for real-time use
- **Cost Constraints**: Balance performance and budget
- **Batch Size**: Larger batches need more compute

### Request Optimization

**Prompt Engineering**
- Keep prompts concise
- Use clear, specific instructions
- Avoid unnecessary context

**Token Management**
- Set appropriate max_tokens
- Monitor actual token usage
- Adjust based on use case

**Batching**
- Enable batching for throughput
- Configure batch size appropriately
- Balance latency vs. efficiency

## Best Practices

### Deployment Strategy

1. **Start Small**: Begin with minimal instances
2. **Test Thoroughly**: Use testing interface before production
3. **Monitor Closely**: Watch metrics during initial deployment
4. **Scale Gradually**: Increase capacity based on actual usage
5. **Document Configuration**: Keep notes on settings and rationale

### Cost Management

1. **Set Baselines**: Understand expected costs before deploying
2. **Monitor Regularly**: Check metrics daily initially
3. **Optimize Prompts**: Reduce token usage where possible
4. **Use Auto-Scaling**: Avoid over-provisioning
5. **Stop Unused Deployments**: Don't pay for idle resources

### Security

1. **Protect API Keys**: Never commit credentials to code
2. **Use Environment Variables**: Store secrets securely
3. **Limit Access**: Use platform access controls
4. **Monitor Usage**: Watch for unusual patterns
5. **Rotate Keys**: Periodically update credentials

### Maintenance

1. **Regular Testing**: Verify endpoints periodically
2. **Update Models**: Deploy new versions as needed
3. **Review Metrics**: Analyze performance trends
4. **Clean Up**: Remove old deployments
5. **Stay Updated**: Follow platform announcements

## Troubleshooting

### Deployment Won't Start

**Check**:
- Platform credentials are configured
- Model exists and is accessible
- Configuration is valid
- Platform has available capacity

**Try**:
- Recreate deployment with different settings
- Test with different platform
- Contact platform support

### Inconsistent Performance

**Check**:
- Auto-scaling settings
- Instance type configuration
- Traffic patterns in metrics
- Platform status page

**Try**:
- Increase minimum instances
- Enable auto-scaling
- Choose higher-performance instances
- Distribute load across multiple deployments

### Cost Higher Than Expected

**Check**:
- Token usage in metrics
- Number of requests
- Instance configuration
- Auto-scaling behavior

**Try**:
- Reduce max_tokens
- Optimize prompts
- Lower minimum instances
- Review and adjust scaling settings

## Advanced Features

### Multi-Platform Deployments

Deploy the same model to multiple platforms:
- Compare performance across platforms
- Implement failover strategies
- Optimize costs by platform
- A/B test different configurations

### Deployment Templates (Coming Soon)

- Save configurations as templates
- Reuse settings across deployments
- Share templates with team
- Template marketplace

### Cost Alerts (Coming Soon)

- Set budget thresholds
- Receive notifications when exceeded
- Automatic deployment stopping
- Cost forecasting

### Custom Metrics (Coming Soon)

- Define custom tracking metrics
- Set up custom alerts
- Export metrics data
- Integration with monitoring tools

## Support

### Getting Help

- **Documentation**: Review this guide and other docs
- **Platform Support**: Contact platform-specific support
- **Community**: Join PEFT Studio community forums
- **Issues**: Report bugs on GitHub

### Feedback

We're constantly improving the deployment system. Share your feedback:
- Feature requests
- Bug reports
- Usability suggestions
- Platform integration requests

## Summary

PEFT Studio's deployment management system provides:

✅ **Multi-Platform Support**: Deploy to Predibase, Together AI, Modal, or Replicate
✅ **Easy Configuration**: Step-by-step wizard for setup
✅ **Real-Time Monitoring**: Live status and metrics
✅ **Interactive Testing**: Test endpoints directly in the UI
✅ **Comprehensive Metrics**: Track usage, latency, and costs
✅ **Flexible Management**: Start, stop, and update deployments
✅ **Cost Tracking**: Monitor and optimize spending

Start deploying your fine-tuned models today and bring your AI applications to production!
