# Platform Connections

Learn how to connect and manage multiple cloud platform accounts.

## Overview

PEFT Studio integrates with various platforms for:
- **Compute Providers**: RunPod, Lambda Labs, Vast.ai
- **Model Registries**: HuggingFace, Civitai, Ollama
- **Experiment Trackers**: Weights & Biases, Comet ML, Arize Phoenix
- **Deployment Platforms**: Predibase, Together AI, Modal, Replicate
- **Evaluation Tools**: DeepEval, HoneyHive

## Connecting a Platform

### Step 1: Navigate to Platforms
Click **Platforms** in the sidebar to view all available platforms.

### Step 2: Select Platform
Click **Connect** on the platform card you want to add.

### Step 3: Enter Credentials
Each platform requires different credentials:

#### HuggingFace
- **API Token**: Get from [HuggingFace Settings](https://huggingface.co/settings/tokens)
- **Permissions**: Read and Write access

#### RunPod
- **API Key**: Get from [RunPod API Keys](https://www.runpod.io/console/user/settings)
- **Permissions**: Full access

#### Weights & Biases
- **API Key**: Get from [W&B Settings](https://wandb.ai/settings)
- **Entity**: Your username or team name

### Step 4: Verify Connection
Click **Verify Connection** to test the credentials. PEFT Studio will:
- Make a test API call
- Verify permissions
- Display connection status

## Managing Connections

### View Connection Status
- **Green**: Connected and verified
- **Yellow**: Connected but not recently verified
- **Red**: Connection failed or credentials invalid

### Edit Connection
1. Click the **Edit** button on the platform card
2. Update credentials
3. Click **Save & Verify**

### Disconnect Platform
1. Click the **Disconnect** button
2. Confirm the action
3. Credentials are removed from secure storage

## Credential Security

PEFT Studio stores credentials securely:
- **Windows**: Windows Credential Manager
- **macOS**: Keychain
- **Linux**: Secret Service API

Credentials are:
- Encrypted at rest using AES-256
- Never logged or displayed in plain text
- Only transmitted over HTTPS
- Automatically cleared on disconnect

## Connection Testing

Test your connection anytime:
1. Click **Test Connection** on the platform card
2. PEFT Studio will verify:
   - API endpoint accessibility
   - Credential validity
   - Required permissions
   - Rate limit status

## Troubleshooting

### Connection Failed
**Problem**: "Connection failed" error

**Solutions**:
1. Verify credentials are correct
2. Check internet connection
3. Ensure API key has required permissions
4. Check platform status page

### Invalid Credentials
**Problem**: "Invalid credentials" error

**Solutions**:
1. Regenerate API key on platform
2. Copy key carefully (no extra spaces)
3. Verify key hasn't expired
4. Check account is active

### Rate Limited
**Problem**: "Rate limit exceeded" error

**Solutions**:
1. Wait for rate limit to reset
2. Upgrade platform plan if needed
3. Reduce API call frequency

## Best Practices

1. **Use Read-Only Keys**: When possible, use read-only API keys for browsing
2. **Rotate Keys Regularly**: Update API keys every 90 days
3. **Monitor Usage**: Track API usage in platform dashboards
4. **Disconnect Unused**: Remove platforms you're not actively using
5. **Verify Regularly**: Test connections monthly

## Platform-Specific Guides

### RunPod Setup
1. Create account at [runpod.io](https://runpod.io)
2. Add payment method
3. Generate API key
4. Connect in PEFT Studio

### Lambda Labs Setup
1. Apply for access at [lambdalabs.com](https://lambdalabs.com)
2. Wait for approval (can take days)
3. Generate API key
4. Connect in PEFT Studio

### Vast.ai Setup
1. Create account at [vast.ai](https://vast.ai)
2. Add payment method
3. Generate API key
4. Connect in PEFT Studio

## Next Steps

- [Browse models](model-browser.md)
- [Select compute providers](compute-providers.md)
- [Start training](training-configuration.md)
