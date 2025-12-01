# Troubleshooting Guide

Common issues and solutions for PEFT Studio.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Connection Problems](#connection-problems)
- [Training Errors](#training-errors)
- [Performance Issues](#performance-issues)
- [Deployment Problems](#deployment-problems)
- [Data and Storage](#data-and-storage)
- [Platform-Specific Issues](#platform-specific-issues)

## Installation Issues

### Application Won't Start

**Symptoms:**
- Application crashes on startup
- Blank screen or loading forever
- Error message on launch

**Solutions:**

1. **Check System Requirements**
   ```bash
   # Minimum requirements:
   - OS: Windows 10+, macOS 10.15+, Ubuntu 20.04+
   - RAM: 8GB (16GB recommended)
   - Disk: 10GB free space
   ```

2. **Clear Application Data**
   ```bash
   # Windows
   del /s /q %APPDATA%\peft-studio\*
   
   # macOS
   rm -rf ~/Library/Application\ Support/peft-studio/*
   
   # Linux
   rm -rf ~/.config/peft-studio/*
   ```

3. **Reinstall Application**
   - Uninstall completely
   - Download latest version
   - Install fresh

4. **Check Logs**
   ```bash
   # Windows
   type %APPDATA%\peft-studio\logs\main.log
   
   # macOS/Linux
   cat ~/.config/peft-studio/logs/main.log
   ```

### Database Initialization Failed

**Symptoms:**
- "Database error" on startup
- Cannot save settings

**Solutions:**

1. **Delete Corrupted Database**
   ```bash
   # Windows
   del %APPDATA%\peft-studio\data\peft_studio.db
   
   # macOS/Linux
   rm ~/.config/peft-studio/data/peft_studio.db
   ```

2. **Check Permissions**
   ```bash
   # Ensure write permissions
   chmod -R 755 ~/.config/peft-studio/
   ```

## Connection Problems

### Platform Connection Failed

**Symptoms:**
- "Connection failed" error
- "Invalid credentials" message
- Timeout errors

**Solutions:**

1. **Verify Credentials**
   - Copy API key carefully (no spaces)
   - Check key hasn't expired
   - Verify account is active

2. **Test Internet Connection**
   ```bash
   # Test connectivity
   ping api.huggingface.co
   curl -I https://api.runpod.io
   ```

3. **Check Firewall**
   - Allow PEFT Studio through firewall
   - Check corporate proxy settings
   - Verify VPN isn't blocking

4. **Platform Status**
   - Check platform status page
   - Verify API endpoint is operational
   - Look for maintenance windows

### WebSocket Connection Drops

**Symptoms:**
- Log streaming stops
- Real-time updates not working
- "Connection lost" messages

**Solutions:**

1. **Check Network Stability**
   - Test with stable connection
   - Avoid WiFi if unstable
   - Use wired connection

2. **Increase Timeout**
   ```json
   // config/settings.json
   {
     "websocket": {
       "timeout": 60000,
       "reconnect_attempts": 5
     }
   }
   ```

3. **Disable Proxy**
   - WebSockets may not work through proxies
   - Try direct connection

## Training Errors

### Out of Memory (OOM)

**Symptoms:**
- "CUDA out of memory" error
- Training crashes mid-run
- System freezes

**Solutions:**

1. **Reduce Batch Size**
   ```python
   # Try smaller batch size
   batch_size = 1  # or 2
   gradient_accumulation_steps = 16  # Increase this
   ```

2. **Enable Quantization**
   ```python
   # Use 4-bit quantization
   quantization = "int4"
   ```

3. **Reduce Model Rank**
   ```python
   # Lower LoRA rank
   rank = 4  # Instead of 8 or 16
   ```

4. **Use Gradient Checkpointing**
   ```python
   # Enable in config
   gradient_checkpointing = True
   ```

5. **Switch to Smaller Model**
   - Try 7B instead of 13B
   - Use quantized base model

### Training Stuck or Slow

**Symptoms:**
- Progress bar not moving
- Very slow training speed
- High CPU usage, low GPU usage

**Solutions:**

1. **Check GPU Utilization**
   ```bash
   # Monitor GPU
   nvidia-smi -l 1
   ```

2. **Optimize Data Loading**
   ```python
   # Increase num_workers
   dataloader_num_workers = 4
   ```

3. **Check Dataset Format**
   - Verify JSON format is correct
   - Ensure no corrupted entries
   - Check file encoding (UTF-8)

4. **Disable Unnecessary Logging**
   ```python
   # Reduce logging frequency
   logging_steps = 100  # Instead of 10
   ```

### Loss is NaN or Exploding

**Symptoms:**
- Loss shows as NaN
- Loss increases rapidly
- Training diverges

**Solutions:**

1. **Reduce Learning Rate**
   ```python
   learning_rate = 1e-5  # Instead of 2e-4
   ```

2. **Add Gradient Clipping**
   ```python
   max_grad_norm = 0.3
   ```

3. **Increase Warmup Steps**
   ```python
   warmup_steps = 500  # Instead of 100
   ```

4. **Check Dataset Quality**
   - Remove outliers
   - Normalize inputs
   - Check for corrupted data

### Job Submission Failed

**Symptoms:**
- "Job submission failed" error
- "Resource unavailable" message
- Timeout on submission

**Solutions:**

1. **Check Platform Credits**
   - Verify sufficient balance
   - Add payment method

2. **Try Different Resource**
   - Select alternative GPU type
   - Choose different provider

3. **Reduce Resource Requirements**
   - Use smaller instance
   - Enable quantization

4. **Check Platform Limits**
   - Verify concurrent job limits
   - Check account restrictions

## Performance Issues

### Slow Application Startup

**Symptoms:**
- Takes >10 seconds to start
- Splash screen hangs
- UI unresponsive initially

**Solutions:**

1. **Clear Cache**
   ```bash
   # Clear model cache
   rm -rf ~/.peft-studio/data/cache/*
   ```

2. **Disable Auto-Start Features**
   ```json
   // config/settings.json
   {
     "startup": {
       "check_updates": false,
       "load_recent_jobs": false
     }
   }
   ```

3. **Optimize Database**
   ```bash
   # Vacuum database
   sqlite3 ~/.peft-studio/data/peft_studio.db "VACUUM;"
   ```

### High Memory Usage

**Symptoms:**
- Application uses >2GB RAM
- System becomes slow
- Out of memory errors

**Solutions:**

1. **Limit Cache Size**
   ```json
   // config/settings.json
   {
     "cache": {
       "max_size_mb": 500,
       "max_models": 10
     }
   }
   ```

2. **Close Unused Tabs**
   - Close model browser when not needed
   - Limit concurrent job monitoring

3. **Restart Application**
   - Restart periodically
   - Clear memory leaks

### UI Lag or Freezing

**Symptoms:**
- UI becomes unresponsive
- Clicks don't register
- Animations stutter

**Solutions:**

1. **Reduce Update Frequency**
   ```json
   // config/settings.json
   {
     "ui": {
       "refresh_interval_ms": 5000,
       "chart_max_points": 100
     }
   }
   ```

2. **Disable Animations**
   ```json
   {
     "ui": {
       "animations_enabled": false
     }
   }
   ```

3. **Close Background Jobs**
   - Stop monitoring completed jobs
   - Clear old logs

## Deployment Problems

### Deployment Failed

**Symptoms:**
- "Deployment failed" error
- Endpoint not accessible
- Timeout during deployment

**Solutions:**

1. **Verify Adapter Format**
   - Check .safetensors format
   - Verify file not corrupted
   - Ensure compatible with platform

2. **Check Platform Quotas**
   - Verify deployment limits
   - Check concurrent deployments
   - Ensure sufficient credits

3. **Try Different Platform**
   - Switch to alternative provider
   - Compare platform requirements

### Endpoint Not Responding

**Symptoms:**
- 404 or 503 errors
- Timeout on requests
- Slow response times

**Solutions:**

1. **Wait for Warmup**
   - Cold starts can take 30-60s
   - First request may be slow

2. **Check Endpoint URL**
   - Verify URL is correct
   - Check authentication headers

3. **Test with Simple Prompt**
   ```bash
   curl -X POST https://endpoint.url/v1/completions \
     -H "Authorization: Bearer TOKEN" \
     -d '{"prompt": "Hello", "max_tokens": 10}'
   ```

4. **Monitor Platform Status**
   - Check deployment logs
   - Verify instance is running

### High Inference Latency

**Symptoms:**
- Responses take >5 seconds
- Inconsistent response times
- Timeout errors

**Solutions:**

1. **Enable Auto-Scaling**
   ```json
   {
     "deployment": {
       "min_replicas": 2,
       "max_replicas": 5,
       "auto_scaling": true
     }
   }
   ```

2. **Use Faster Instance**
   - Upgrade to GPU with more VRAM
   - Use dedicated instance

3. **Optimize Generation**
   ```python
   # Reduce max_tokens
   max_tokens = 100  # Instead of 500
   
   # Adjust temperature
   temperature = 0.7  # Lower for faster
   ```

## Data and Storage

### Disk Space Full

**Symptoms:**
- "Insufficient disk space" error
- Cannot download models
- Cannot save adapters

**Solutions:**

1. **Clear Cache**
   ```bash
   # Clear model cache
   rm -rf ~/.peft-studio/data/cache/models/*
   
   # Clear old logs
   find ~/.peft-studio/logs -mtime +30 -delete
   ```

2. **Delete Old Adapters**
   - Remove unused adapters
   - Archive to external storage

3. **Clean Up Jobs**
   ```bash
   # Delete old job data
   sqlite3 ~/.peft-studio/data/peft_studio.db \
     "DELETE FROM training_jobs WHERE completed_at < date('now', '-30 days');"
   ```

### Dataset Upload Failed

**Symptoms:**
- "Upload failed" error
- Timeout during upload
- Corrupted dataset

**Solutions:**

1. **Check File Size**
   - Verify file <2GB
   - Split large datasets

2. **Verify Format**
   ```json
   // Correct format
   [
     {"text": "Example 1"},
     {"text": "Example 2"}
   ]
   ```

3. **Check Encoding**
   ```bash
   # Convert to UTF-8
   iconv -f ISO-8859-1 -t UTF-8 input.json > output.json
   ```

### Adapter Download Failed

**Symptoms:**
- "Download failed" error
- Incomplete download
- Corrupted file

**Solutions:**

1. **Retry Download**
   - Click retry button
   - Wait for network stability

2. **Check Disk Space**
   - Ensure sufficient space
   - Clear cache if needed

3. **Verify Job Completed**
   - Ensure training finished
   - Check job status

## Platform-Specific Issues

### RunPod Issues

**Problem: Pod won't start**
- Check account balance
- Verify GPU availability
- Try different region

**Problem: SSH connection failed**
- Check SSH key configuration
- Verify firewall rules
- Use RunPod web terminal

### Lambda Labs Issues

**Problem: No GPUs available**
- Lambda has limited capacity
- Try different times
- Join waitlist for access

**Problem: Instance terminated**
- Check for idle timeout
- Verify payment method
- Review usage limits

### HuggingFace Issues

**Problem: Model not found**
- Verify model ID is correct
- Check model is public
- Ensure you have access

**Problem: Rate limited**
- Wait for rate limit reset
- Upgrade to Pro account
- Use caching

### Weights & Biases Issues

**Problem: Metrics not logging**
- Verify API key is valid
- Check project exists
- Ensure internet connection

**Problem: Dashboard not updating**
- Refresh browser
- Check W&B status
- Verify run is active

## Getting More Help

### Generate Diagnostic Report

1. Go to **Settings** → **Diagnostics**
2. Click **Generate Report**
3. Save report file
4. Attach to support ticket

### Enable Debug Mode

```json
// config/settings.json
{
  "logging": {
    "level": "DEBUG",
    "console_output": true
  }
}
```

### Contact Support

- **GitHub Issues**: [Report bugs](https://github.com/your-org/peft-studio/issues)
- **Discussions**: [Ask questions](https://github.com/your-org/peft-studio/discussions)
- **Email**: support@peft-studio.com
- **Discord**: [Join community](https://discord.gg/peft-studio)

### Useful Commands

```bash
# Check version
peft-studio --version

# Reset to defaults
peft-studio --reset

# Run in safe mode
peft-studio --safe-mode

# Export logs
peft-studio --export-logs logs.zip
```

## Known Issues

### Windows Defender False Positive
- **Issue**: Windows Defender flags application
- **Status**: Known issue, working with Microsoft
- **Workaround**: Add exception in Windows Defender

### macOS Gatekeeper Warning
- **Issue**: "App from unidentified developer"
- **Solution**: Right-click → Open → Open anyway

### Linux AppImage Permissions
- **Issue**: AppImage won't execute
- **Solution**: `chmod +x PEFT-Studio.AppImage`

## Reporting Bugs

When reporting bugs, include:
1. PEFT Studio version
2. Operating system and version
3. Steps to reproduce
4. Expected vs actual behavior
5. Error messages or logs
6. Screenshots if applicable

Use the diagnostic report feature to automatically collect this information.
