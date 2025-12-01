# Logging and Diagnostics

## Overview

PEFT Studio provides comprehensive logging and diagnostics tools to help you monitor, troubleshoot, and debug issues during training and inference. View detailed error logs, search and filter by severity, generate diagnostic reports, and export logs for analysis.

## Features

### Log Viewer with Filtering

View and filter error logs efficiently:

- **Stats Dashboard**: Overview of total logs and counts by severity
- **Severity Filtering**: Filter by severity level:
  - Critical (system-breaking errors)
  - High (major issues affecting functionality)
  - Medium (moderate issues with workarounds)
  - Low (minor issues or warnings)
- **Error Type Filtering**: Filter by specific error types:
  - Out of Memory (OOM) errors
  - Network errors
  - Configuration errors
  - Model loading errors
  - Training errors
  - Inference errors
- **Visual Indicators**: Color-coded severity badges and icons
- **Expandable Logs**: Click to view full details including stack traces

### Log Search

Find specific logs quickly:

- **Full-Text Search**: Search across error messages, stack traces, and context
- **Real-Time Filtering**: Instant results as you type
- **Search Highlighting**: Clear indication of matching logs
- **No Results Messaging**: Helpful feedback when no logs match

### Diagnostic Report Generator

Create comprehensive diagnostic reports:

- **One-Click Generation**: Generate reports instantly
- **Automatic Download**: Reports download automatically as JSON files
- **Complete Information**: Includes:
  - All error logs
  - System state at time of errors
  - Configuration details
  - Hardware information
  - Recent user actions
- **Unique Report IDs**: Each report has a unique identifier for tracking

### Debug Mode Toggle

Enable verbose logging for troubleshooting:

- **Visual Toggle**: Clear ON/OFF indicator
- **Backend Integration**: Enables detailed logging in backend services
- **Persistent State**: Debug mode status maintained across sessions
- **Immediate Effect**: Changes take effect immediately

### Log Export

Export logs for external analysis:

- **JSON Export**: Export all logs to a JSON file
- **Automatic Naming**: Files named with timestamps
- **Success Confirmation**: Shows export location and log count
- **Clear All Logs**: Remove all logs with confirmation dialog

## User Interface

### Stats Dashboard

At the top of the logging page, you'll see:

- **Total Logs**: Total number of error logs
- **Critical**: Count of critical severity logs (red)
- **High**: Count of high severity logs (orange)
- **Medium**: Count of medium severity logs (yellow)
- **Low**: Count of low severity logs (blue)

### Actions Bar

Quick access to common actions:

- **Search Box**: Search logs by keyword
- **Filters Button**: Toggle filter panel
- **Debug Mode Toggle**: Enable/disable debug logging
- **Refresh Button**: Reload logs and stats
- **Generate Report**: Create diagnostic report
- **Export**: Export logs to file
- **Clear**: Clear all logs (with confirmation)

### Log List

View all logs with key information:

- **Severity Icon**: Visual indicator of severity level
- **Timestamp**: When the error occurred
- **Error Type**: Category of error
- **Error Message**: Brief description
- **Expand Button**: View full details

### Expanded Log Details

Click on a log to view:

- **Full Error Message**: Complete error description
- **Stack Trace**: Full stack trace with syntax highlighting
- **System State**: CPU, memory, and disk usage at time of error
- **Context Information**: Additional context data in JSON format
- **Recent Actions**: List of recent user actions leading to the error
- **Copy Button**: Copy error message to clipboard

## User Workflows

### Workflow 1: View and Filter Logs

1. Navigate to **Logging & Diagnostics**
2. View the stats dashboard showing log counts
3. Click **Filters** to open the filter panel
4. Select a severity level (e.g., "High")
5. Optionally select an error type (e.g., "oom_error")
6. View filtered logs in the list
7. Click on any log to expand and view details

### Workflow 2: Search for Specific Errors

1. Open the Logging & Diagnostics page
2. Type a search query in the search box (e.g., "CUDA")
3. View filtered results in real-time
4. Click on matching logs to view details
5. Clear search to view all logs again

### Workflow 3: Generate Diagnostic Report

1. Navigate to Logging & Diagnostics
2. Click the **Generate Report** button
3. Wait for report generation (usually instant)
4. Report automatically downloads as a JSON file
5. Alert shows report ID and error count
6. Share report with support team if needed

### Workflow 4: Enable Debug Mode

1. Open Logging & Diagnostics
2. Click the **Debug Mode OFF** button
3. Button changes to **Debug Mode ON**
4. Backend logging level increases to verbose
5. Perform actions you want to debug
6. View detailed logs in the log list
7. Click **Debug Mode ON** to disable when done

### Workflow 5: Export and Clear Logs

1. Navigate to Logging & Diagnostics
2. Click the **Export** button
3. Logs export to a JSON file with timestamp
4. Alert shows file location and log count
5. Optionally click **Clear** to remove all logs
6. Confirm the action in the dialog
7. Logs are cleared from the system

## Log Severity Levels

### Critical

System-breaking errors that prevent core functionality:

- **Color**: Red
- **Icon**: X circle
- **Examples**:
  - Application crashes
  - Database corruption
  - Critical service failures
- **Action**: Immediate attention required

### High

Major issues affecting important functionality:

- **Color**: Orange
- **Icon**: Alert circle
- **Examples**:
  - Training failures
  - Model loading errors
  - API connection failures
- **Action**: Should be addressed soon

### Medium

Moderate issues with workarounds available:

- **Color**: Yellow
- **Icon**: Alert triangle
- **Examples**:
  - Performance degradation
  - Non-critical feature failures
  - Configuration warnings
- **Action**: Address when convenient

### Low

Minor issues or informational warnings:

- **Color**: Blue
- **Icon**: Info circle
- **Examples**:
  - Deprecation warnings
  - Minor configuration issues
  - Informational messages
- **Action**: Review periodically

## Error Types

### Out of Memory (OOM) Errors

Memory exhaustion during training or inference:

- **Causes**: Model too large, batch size too high, insufficient RAM/VRAM
- **Solutions**: Reduce batch size, enable gradient checkpointing, use quantization
- **Prevention**: Monitor memory usage, use memory profiling

### Network Errors

Connection or communication failures:

- **Causes**: Internet connectivity, firewall, API rate limits
- **Solutions**: Check network connection, verify API credentials, retry with backoff
- **Prevention**: Implement retry logic, use offline mode when possible

### Configuration Errors

Invalid or incompatible configuration:

- **Causes**: Invalid parameters, missing required fields, incompatible settings
- **Solutions**: Validate configuration, check documentation, use presets
- **Prevention**: Use configuration validation, provide helpful error messages

### Model Loading Errors

Failures when loading models:

- **Causes**: Invalid model path, corrupted files, incompatible format
- **Solutions**: Verify model path, re-download model, check format compatibility
- **Prevention**: Validate model files, use checksums, provide clear error messages

### Training Errors

Issues during model training:

- **Causes**: Invalid hyperparameters, data issues, hardware failures
- **Solutions**: Adjust hyperparameters, validate data, check hardware
- **Prevention**: Validate inputs, monitor training, implement checkpointing

### Inference Errors

Problems during model inference:

- **Causes**: Invalid input, model issues, resource constraints
- **Solutions**: Validate input, check model, ensure sufficient resources
- **Prevention**: Input validation, error handling, resource monitoring

## Diagnostic Reports

### Report Contents

Diagnostic reports include:

1. **Report Metadata**:
   - Unique report ID
   - Generation timestamp
   - PEFT Studio version
   - System information

2. **Error Logs**:
   - All error logs with full details
   - Stack traces
   - Context information

3. **System State**:
   - CPU usage
   - Memory usage
   - Disk usage
   - GPU information (if available)

4. **Configuration**:
   - Current configuration
   - Active settings
   - Enabled features

5. **Recent Actions**:
   - User actions leading to errors
   - Timestamps
   - Action details

### Report Format

Reports are exported as JSON files:

```json
{
  "report_id": "unique-report-id",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "system": {
    "os": "Windows 10",
    "cpu": "Intel Core i7",
    "memory": "16GB",
    "gpu": "NVIDIA RTX 3090"
  },
  "errors": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "severity": "high",
      "error_type": "oom_error",
      "message": "Out of memory error",
      "stack_trace": "...",
      "context": {...}
    }
  ],
  "configuration": {...},
  "recent_actions": [...]
}
```

### Using Reports

1. **Internal Analysis**: Review reports to identify patterns
2. **Support Requests**: Attach reports to support tickets
3. **Bug Reports**: Include reports in GitHub issues
4. **Team Collaboration**: Share reports with team members
5. **Documentation**: Use reports to document issues

## Debug Mode

### When to Use Debug Mode

Enable debug mode when:

- Troubleshooting specific issues
- Developing or testing new features
- Investigating performance problems
- Reproducing reported bugs
- Analyzing system behavior

### What Debug Mode Does

When enabled, debug mode:

- Increases logging verbosity
- Logs additional details about operations
- Captures more context information
- Records timing information
- Logs internal state changes

### Performance Impact

Debug mode may:

- Slightly reduce performance
- Increase disk usage for logs
- Use more memory for log buffers
- Generate larger log files

**Recommendation**: Disable debug mode during normal operation

## Best Practices

### Regular Monitoring

- Check logs periodically for issues
- Review stats dashboard for trends
- Address high and critical errors promptly
- Monitor for recurring error patterns

### Log Management

- Export logs before clearing
- Keep diagnostic reports for reference
- Clear old logs to save space
- Use search and filters effectively

### Troubleshooting

- Enable debug mode when investigating issues
- Generate diagnostic reports for complex problems
- Search logs for specific error messages
- Review stack traces for root causes

### Performance

- Disable debug mode during normal operation
- Clear logs periodically to free space
- Export logs before clearing for archival
- Monitor disk usage for log storage

### Collaboration

- Share diagnostic reports with team
- Document solutions to common errors
- Create knowledge base from error patterns
- Use reports in bug tracking systems

## Backend Integration

### API Endpoints

The UI integrates with the following backend endpoints:

- `GET /api/logging/logs` - Fetch logs with filtering
- `GET /api/logging/logs/search` - Search logs
- `POST /api/logging/diagnostic-report` - Generate diagnostic report
- `GET /api/logging/diagnostic-report/{id}/download` - Download report
- `POST /api/logging/export` - Export logs
- `DELETE /api/logging/logs` - Clear logs
- `GET /api/logging/debug-mode` - Get debug mode status
- `POST /api/logging/debug-mode` - Toggle debug mode
- `GET /api/logging/stats` - Get logging statistics

### Backend Services

- **LoggingService**: Core service for logging operations
- **LoggingAPI**: FastAPI endpoints for REST API

## Troubleshooting

### Logs Not Appearing

**Problem**: No logs displayed in the viewer

**Solutions**:
- Click the Refresh button
- Check if filters are too restrictive
- Verify backend service is running
- Check browser console for errors

### Search Not Working

**Problem**: Search doesn't return expected results

**Solutions**:
- Check search query spelling
- Try broader search terms
- Clear filters that may conflict
- Refresh the page

### Report Generation Fails

**Problem**: Diagnostic report doesn't generate

**Solutions**:
- Check backend service status
- Verify sufficient disk space
- Review backend logs for errors
- Try again after a moment

### Debug Mode Not Enabling

**Problem**: Debug mode toggle doesn't work

**Solutions**:
- Check backend connection
- Verify API endpoint is accessible
- Review browser console for errors
- Refresh the page and try again

### Export Issues

**Problem**: Log export fails or file is empty

**Solutions**:
- Check browser download settings
- Verify sufficient disk space
- Ensure write permissions
- Try exporting fewer logs

## Related Documentation

- [Quick Start Guide](quick-start.md)
- [Troubleshooting Guide](../reference/troubleshooting.md)
- [FAQ](../reference/faq.md)
- [Developer Guide](../developer-guide/api-documentation.md)

## Support

For issues or questions about logging and diagnostics:

1. Check the [Troubleshooting Guide](../reference/troubleshooting.md)
2. Review the [FAQ](../reference/faq.md)
3. Generate a diagnostic report
4. Open an issue on GitHub with the report
5. Contact support

---

**Status**: ✅ Complete  
**Version**: 1.0  
**Last Updated**: 2024
