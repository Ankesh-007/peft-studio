# Configuration Management

## Overview

PEFT Studio provides comprehensive configuration management capabilities, enabling you to export, import, share, and reuse training configurations. This feature helps you maintain consistency across training runs, share successful configurations with team members, and build a library of proven configurations for different use cases.

## Features

### Export Configuration

Export your current training configuration with metadata for future use or sharing:

- **Metadata Input**: Add name, description, author, and tags to your configuration
- **Export Options**: 
  - Save to local library for quick access
  - Download as JSON file for sharing or backup
- **Configuration Preview**: Review all settings before exporting
- **Validation**: Ensures all required fields are filled

### Import Configuration

Import configurations from files or JSON text with comprehensive validation:

- **Multiple Input Methods**:
  - File upload with drag & drop support
  - Paste JSON text directly
- **Real-time Validation**: Immediate feedback on configuration validity
- **Preview Before Import**: Review configuration details before applying
- **Error Handling**: Detailed validation errors with helpful suggestions

### Configuration Library

Browse and manage your saved configurations:

- **Browse**: View all saved configurations in an organized list
- **Search**: Find configurations by name or description
- **Filter**: Filter by tags for quick access
- **Actions**: Share or delete configurations
- **Metadata Display**: View author, dates, tags, and training results

### Configuration Preview

View comprehensive configuration details:

- **Metadata**: Name, description, author, tags, creation and modification dates
- **Training Settings**: Organized display of:
  - Model settings
  - PEFT parameters
  - Training parameters
  - Compute settings
- **Hardware Requirements**: View required resources
- **Training Results**: See results from previous runs (if available)

### Sharing Functionality

Share configurations with team members or the community:

- **Download**: Export configuration as a standard JSON file
- **Shareable Format**: Uses standard JSON format for easy sharing
- **Import**: Import shared configurations from others

## User Workflows

### Workflow 1: Export Configuration

1. Complete your training configuration in the wizard
2. Click the **Export Configuration** button
3. Enter a configuration name (required)
4. Optionally add:
   - Description explaining the configuration's purpose
   - Author name
   - Tags for categorization
5. Choose export options:
   - ☑ Save to library
   - ☑ Download as file
6. Review the configuration preview
7. Click **Export** to complete

### Workflow 2: Import Configuration

1. Click the **Import Configuration** button
2. Choose your import method:
   - **File Upload**: Drag and drop or click to select a JSON file
   - **Paste JSON**: Copy and paste JSON text directly
3. View validation results:
   - ✅ Valid configurations show a success message
   - ❌ Invalid configurations show detailed error messages
4. Preview the configuration if valid
5. Click **Import Configuration** to apply the settings

### Workflow 3: Browse Library

1. Click the **Browse Library** button
2. View all saved configurations in the list
3. Use the search box to find specific configurations
4. Click on a configuration to view full details
5. Use action buttons to:
   - **Share**: Download the configuration as a file
   - **Delete**: Remove the configuration from your library

## Components

### ConfigurationManagement

Main component that orchestrates all configuration management functionality:

**Location**: `src/components/ConfigurationManagement.tsx`

**Features**:
- Unified interface for all configuration operations
- Real-time library updates
- Search functionality
- Tag-based filtering
- Empty state handling
- Error handling and loading states

### ExportConfigurationDialog

Dialog for exporting training configurations:

**Location**: `src/components/configuration/ExportConfigurationDialog.tsx`

**Features**:
- Configuration metadata input
- Export options (library and/or file)
- Configuration preview
- Validation before export

### ImportConfigurationDialog

Dialog for importing configurations with validation:

**Location**: `src/components/configuration/ImportConfigurationDialog.tsx`

**Features**:
- Two import modes (file upload or paste JSON)
- Real-time validation
- Configuration preview before import
- Detailed error messages

### ConfigurationPreview

Component for previewing configuration details:

**Location**: `src/components/configuration/ConfigurationPreview.tsx`

**Features**:
- Metadata display
- Training configuration sections
- Hardware requirements display
- Training results display
- Compact mode for dialogs

### ConfigurationLibraryBrowser

Component for browsing saved configurations:

**Location**: `src/components/configuration/ConfigurationLibraryBrowser.tsx`

**Features**:
- List view of saved configurations
- Configuration cards with metadata
- Quick actions (share, delete)
- Empty state handling
- Relative date formatting

## Backend Integration

### API Endpoints

The UI integrates with the following backend endpoints:

- `POST /api/configurations/export` - Export configuration
- `POST /api/configurations/import` - Import configuration
- `POST /api/configurations/library/save` - Save to library
- `GET /api/configurations/library/{id}` - Load from library
- `POST /api/configurations/library/list` - List configurations
- `DELETE /api/configurations/library/{id}` - Delete configuration
- `POST /api/configurations/export-file` - Download configuration file
- `POST /api/configurations/import-file` - Upload configuration file

### Backend Services

- **ConfigurationManagementService**: Core service for configuration operations
- **ConfigurationManagementAPI**: FastAPI endpoints for REST API

## Configuration Format

Configurations are stored in JSON format with the following structure:

```json
{
  "metadata": {
    "name": "Configuration Name",
    "description": "Description of the configuration",
    "author": "Author Name",
    "tags": ["tag1", "tag2"],
    "created_at": "2024-01-01T00:00:00Z",
    "modified_at": "2024-01-01T00:00:00Z"
  },
  "model": {
    "model_id": "meta-llama/Llama-2-7b-hf",
    "use_case": "chatbot"
  },
  "peft": {
    "method": "lora",
    "r": 8,
    "lora_alpha": 16,
    "lora_dropout": 0.1
  },
  "training": {
    "learning_rate": 2e-4,
    "batch_size": 4,
    "num_epochs": 3,
    "gradient_accumulation_steps": 4
  },
  "compute": {
    "platform": "local",
    "gpu_type": "nvidia-rtx-3090"
  }
}
```

## Data Validation

The system validates configurations to ensure:

- **Required Fields**: All mandatory fields are present
- **JSON Format**: Valid JSON structure
- **Configuration Structure**: Correct schema and field types
- **Enum Values**: Valid values for enumerated fields
- **Numeric Ranges**: Values within acceptable ranges

## Best Practices

### Naming Conventions

- Use descriptive names that indicate the configuration's purpose
- Include the model name or use case in the name
- Example: "Llama-2-7B-Chatbot-LoRA-r8"

### Descriptions

- Explain what makes this configuration unique
- Note any special considerations or requirements
- Document expected results or performance

### Tags

- Use consistent tags across configurations
- Common tags: model-name, use-case, peft-method, performance-level
- Example tags: "llama-2", "chatbot", "lora", "production"

### Library Organization

- Regularly review and clean up unused configurations
- Use search and filters to find configurations quickly
- Delete outdated or superseded configurations

### Sharing

- Always include comprehensive metadata when sharing
- Test imported configurations before using in production
- Document any environment-specific requirements

## Troubleshooting

### Import Validation Errors

**Problem**: Configuration fails validation on import

**Solutions**:
- Check that all required fields are present
- Verify JSON syntax is correct
- Ensure enum values match expected options
- Review error messages for specific issues

### Missing Configurations

**Problem**: Saved configuration doesn't appear in library

**Solutions**:
- Refresh the library view
- Check that the configuration was saved (not just downloaded)
- Verify the configuration wasn't accidentally deleted

### Export Issues

**Problem**: Export doesn't download or save

**Solutions**:
- Check browser download settings
- Ensure sufficient disk space
- Verify write permissions for library directory
- Check browser console for errors

## Future Enhancements

Potential improvements planned for future releases:

1. **Configuration Versioning**: Track changes and maintain version history
2. **Configuration Comparison**: Compare two configurations side-by-side
3. **Configuration Templates**: Pre-built templates for common use cases
4. **Community Sharing**: Share configurations with the PEFT Studio community
5. **Hardware Validation**: Validate configurations against available hardware
6. **Bulk Operations**: Import/export multiple configurations at once
7. **Configuration Categories**: Organize configurations by category
8. **Advanced Search**: Filter by multiple criteria simultaneously
9. **Ratings and Reviews**: Rate and review shared configurations
10. **Smart Recommendations**: Suggest configurations based on your use case

## Related Documentation

- [Training Configuration Guide](training-configuration.md)
- [Quick Start Guide](quick-start.md)
- [Platform Connections](platform-connections.md)

## Support

For issues or questions about configuration management:

1. Check the [Troubleshooting Guide](../reference/troubleshooting.md)
2. Review the [FAQ](../reference/faq.md)
3. Open an issue on GitHub
4. Contact support

---

**Status**: ✅ Complete  
**Version**: 1.0  
**Last Updated**: 2024
