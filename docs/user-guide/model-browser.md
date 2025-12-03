# Unified Model Browser

## Overview

The Unified Model Browser provides a comprehensive interface for discovering, comparing, and selecting machine learning models from multiple registries including HuggingFace, Civitai, and Ollama.

## Features

### Multi-Registry Search

Search across multiple model registries simultaneously:
- **HuggingFace**: Access thousands of pre-trained models
- **Civitai**: Browse image generation models (planned)
- **Ollama**: Explore local model library (planned)

The browser aggregates results from all selected registries and displays them in a unified interface with clear indicators showing the source of each model.

### Model Comparison

Compare up to 4 models side-by-side:
- Downloads and popularity metrics
- Model parameters and size
- Architecture details
- License information
- Hardware compatibility
- Visual indicators highlighting best values

### Model Details

View comprehensive information for each model:
- **Statistics**: Downloads, likes, parameters, size
- **Tags**: Model categories and use cases
- **Architecture**: Model type and structure
- **License**: Usage rights and restrictions
- **Compatibility**: Hardware requirements and warnings

### Advanced Filtering

Filter models by multiple criteria:
- **Registry**: Select which registries to search
- **Task Type**: Classification, generation, translation, etc.
- **Model Size**: < 1B, 1B-7B, 7B-13B, > 13B parameters
- **Architecture**: Llama, Mistral, GPT, Falcon, MPT
- **License**: Apache 2.0, MIT, GPL, etc.
- **Sort Options**: Downloads, likes, trending

### Cache Management

Efficiently manage model metadata:
- **24-hour Cache**: Reduces API calls and improves performance
- **Cache Viewer**: See all cached models with timestamps
- **Individual Removal**: Remove specific models from cache
- **Bulk Clear**: Clear entire cache when needed
- **Automatic Expiration**: Old cache entries are automatically removed

### Compatibility Checking

Get instant feedback on hardware compatibility:
- **VRAM Estimation**: Calculate required GPU memory
- **Compatibility Warnings**: Alert when hardware is insufficient
- **Quantization Recommendations**: Suggest optimization options
- **Visual Indicators**: Green for compatible, yellow for warnings

## Using the Model Browser

### Opening the Browser

Access the Model Browser from the main navigation menu or dashboard.

### Searching for Models

1. Enter search terms in the search bar
2. Select which registries to search (HuggingFace, Civitai, Ollama)
3. Apply filters to narrow results
4. Sort by downloads, likes, or trending

### Viewing Model Details

Click on any model card to open the detail modal:
- View comprehensive metadata
- Check hardware compatibility
- See download statistics
- Review license information

### Comparing Models

1. Select up to 4 models using the compare checkbox
2. Click "Compare Selected" button
3. View side-by-side comparison
4. Identify best options with visual highlights

### Managing Cache

1. Click the cache icon in the browser header
2. View all cached models with timestamps
3. Remove individual models or clear all cache
4. Cache automatically expires after 24 hours

## View Modes

### Grid View
- Visual card layout
- Model thumbnails and key info
- Best for browsing and discovery
- Registry badges show source

### List View
- Compact table format
- More models visible at once
- Sortable columns
- Best for detailed comparison

## API Integration

### Search Multi-Registry

```typescript
const results = await searchMultiRegistry({
  query: "llama",
  registries: ["huggingface", "civitai"],
  filters: {
    minDownloads: 1000,
    taskType: "text-generation"
  }
});
```

### Check Compatibility

```typescript
const compatibility = await checkModelCompatibility({
  modelId: "meta-llama/Llama-2-7b",
  availableVRAM: 24
});

if (compatibility.compatible) {
  console.log("Model is compatible!");
} else {
  console.log("Warnings:", compatibility.warnings);
  console.log("Recommendations:", compatibility.recommendations);
}
```

### Manage Cache

```typescript
// List cached models
const cached = await listCachedModels();

// Remove specific model
await removeFromCache("huggingface", "meta-llama/Llama-2-7b");

// Clear all cache
await clearCache();
```

## Model Metadata

Each model includes the following information:

- **Basic Info**: Name, description, author
- **Statistics**: Downloads, likes, creation date
- **Technical**: Parameters, size, architecture
- **Requirements**: VRAM, compute needs
- **Legal**: License, usage restrictions
- **Tags**: Categories, use cases, languages

## Hardware Compatibility

The browser automatically checks if models are compatible with your hardware:

### Compatible (Green)
- Model fits in available VRAM
- No warnings or issues
- Ready to use

### Warning (Yellow)
- Model may fit with optimizations
- Quantization recommended
- Reduced batch size suggested

### Incompatible (Red)
- Model exceeds available VRAM
- Hardware upgrade needed
- Alternative models suggested

## Best Practices

### Searching
- Use specific keywords for better results
- Apply filters to narrow down options
- Sort by downloads for popular models
- Check multiple registries for variety

### Comparing
- Compare models of similar size
- Focus on relevant metrics for your use case
- Consider license compatibility
- Check hardware requirements

### Caching
- Cache expires after 24 hours
- Clear cache if seeing stale data
- Individual removal for specific updates
- Bulk clear for fresh start

## Troubleshooting

### No Results Found
- Check spelling of search terms
- Remove or adjust filters
- Try different registries
- Use broader search terms

### Slow Loading
- Check network connection
- Clear browser cache
- Reduce number of filters
- Try fewer registries at once

### Compatibility Warnings
- Check available VRAM
- Consider quantization options
- Look for smaller model variants
- Review hardware requirements

### Cache Issues
- Clear cache and refresh
- Check cache expiration time
- Verify backend connection
- Review browser console for errors

## Keyboard Shortcuts

- `Ctrl/Cmd + K`: Focus search bar
- `Ctrl/Cmd + F`: Open filters
- `Escape`: Close modals
- `Arrow Keys`: Navigate results
- `Enter`: Open selected model

## Future Enhancements

- **Civitai Integration**: Full support for image models
- **Ollama Integration**: Local model library access
- **Download Progress**: Track model downloads
- **Offline Mode**: Browse cached models offline
- **Advanced Filters**: More filtering options
- **Model Recommendations**: AI-powered suggestions
- **Batch Operations**: Bulk model management
- **Custom Collections**: Save favorite models

## Related Documentation

- [Platform Connections](platform-connections.md)
- [Training Configuration](training-configuration.md)
- [Deployment](deployment.md)
- [API Documentation](../developer-guide/api-documentation.md)
