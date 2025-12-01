# Gradio Demo Generator

## Overview

The Gradio Demo Generator enables you to create, manage, and deploy interactive web demos for your fine-tuned models. Build shareable demos with custom interfaces, launch local servers, generate public URLs, and get embeddable code—all within PEFT Studio.

## Features

### Demo Configuration

Create demos with comprehensive configuration options:

- **Model Selection**: Choose your fine-tuned model or base model
- **Interface Customization**: Select input/output types:
  - Textbox (text input/output)
  - Chatbot (conversational interface)
  - Audio (speech input/output)
  - Image (image input/output)
- **Generation Parameters**: Configure:
  - Temperature
  - Top P
  - Top K
  - Max Tokens
- **Server Configuration**: Set port and sharing options
- **Model Source**: Use local models or API endpoints

### Demo Preview

Monitor and manage your demos:

- **Real-Time Status**: View demo status (created, running, stopped, error)
- **Demo List**: See all created demos with status indicators
- **Demo Selection**: Click to view details and controls
- **Visual Indicators**: Color-coded status badges

### Local Server Management

Control demo servers with ease:

- **Launch Demo**: Start the Gradio server
- **Stop Demo**: Gracefully stop the server
- **Refresh Status**: Update demo status
- **Delete Demo**: Remove demos you no longer need
- **Status Indicators**: Clear visual feedback on server state

### Public Sharing

Share your demos with the world:

- **Enable Sharing**: Toggle public sharing in configuration
- **Public URL**: Get a shareable public URL when enabled
- **Open in Browser**: Launch demo in your default browser
- **Persistent Links**: URLs remain active while server is running

### Embeddable Code

Integrate demos into websites:

- **Generated Python Code**: View the complete Gradio code
- **HTML/iframe Code**: Get embeddable code for websites
- **Copy to Clipboard**: One-click copy functionality
- **Syntax Highlighting**: Easy-to-read code display

## User Workflows

### Workflow 1: Create and Launch a Demo

1. Navigate to **Gradio Demos** in the main menu
2. Click **New Demo** button
3. Fill out the configuration form:
   - Enter demo name
   - Enter model path or ID
   - Select interface type (e.g., "textbox")
   - Configure generation parameters
   - Set server port (default: 7860)
   - Enable sharing if desired
4. Click **Create Demo**
5. Demo appears in the list with status "created"
6. Click **Launch** button
7. Wait for status to change to "running"
8. Click **Open in Browser** to test the demo

### Workflow 2: Generate and Use Embeddable Code

1. Create and launch a demo (see Workflow 1)
2. Select the running demo from the list
3. View the generated Python code in the code display
4. If sharing is enabled, view the HTML/iframe code
5. Click **Copy** button to copy code to clipboard
6. Paste code into your website or documentation
7. Users can now interact with your model through the embedded demo

### Workflow 3: Share a Demo Publicly

1. Create a demo with **Enable Sharing** checked
2. Launch the demo
3. Wait for the public URL to appear
4. Copy the public URL
5. Share the URL with colleagues or on social media
6. Users can access the demo without any setup
7. Stop the demo when you're done sharing

### Workflow 4: Manage Multiple Demos

1. Create multiple demos for different models or use cases
2. View all demos in the demo list
3. Launch demos as needed
4. Stop demos when not in use to free resources
5. Delete old demos to keep the list clean
6. Use descriptive names to identify demos easily

## Components

### GradioDemoGenerator

Main component for creating and managing Gradio demos:

**Location**: `src/components/GradioDemoGenerator.tsx`

**Features**:
- Demo configuration form
- Demo list with status indicators
- Demo controls (launch, stop, delete)
- Code display with syntax highlighting
- Copy to clipboard functionality

## Backend Integration

### API Endpoints

The UI integrates with the following backend endpoints:

- `POST /api/gradio-demos/create` - Create a new demo
- `POST /api/gradio-demos/{demo_id}/launch` - Launch a demo server
- `POST /api/gradio-demos/{demo_id}/stop` - Stop a demo server
- `GET /api/gradio-demos/{demo_id}/code` - Get generated Python code
- `GET /api/gradio-demos/{demo_id}/embed` - Get embeddable HTML/iframe code
- `DELETE /api/gradio-demos/{demo_id}` - Delete a demo
- `GET /api/gradio-demos/` - List all demos
- `GET /api/gradio-demos/{demo_id}/status` - Get demo status

### Backend Services

- **GradioDemoService**: Core service for demo operations
- **GradioDemoAPI**: FastAPI endpoints for REST API

## Interface Types

### Textbox Interface

Simple text input and output:

**Use Cases**:
- Text generation
- Summarization
- Translation
- Question answering

**Features**:
- Single text input field
- Text output display
- Suitable for most text-to-text tasks

### Chatbot Interface

Conversational interface with message history:

**Use Cases**:
- Chatbots
- Conversational AI
- Multi-turn dialogue

**Features**:
- Message history display
- User/assistant message distinction
- Context preservation across turns

### Audio Interface

Speech input and/or output:

**Use Cases**:
- Speech-to-text
- Text-to-speech
- Audio generation

**Features**:
- Microphone input
- Audio file upload
- Audio playback

### Image Interface

Image input and/or output:

**Use Cases**:
- Image captioning
- Image generation
- Visual question answering

**Features**:
- Image upload
- Image display
- Drawing canvas (optional)

## Generation Parameters

### Temperature

Controls randomness in generation:

- **Low (0.1-0.5)**: Deterministic, focused responses
- **Medium (0.6-0.9)**: Balanced creativity
- **High (1.0-2.0)**: Creative, diverse responses

### Top P

Nucleus sampling threshold:

- **Low (0.1-0.5)**: Conservative token selection
- **Medium (0.6-0.9)**: Balanced diversity
- **High (0.95-1.0)**: Maximum diversity

### Top K

Vocabulary limitation:

- **Low (10-30)**: Focused vocabulary
- **Medium (40-60)**: Balanced selection
- **High (100+)**: Diverse vocabulary

### Max Tokens

Maximum response length:

- **Short (50-200)**: Brief responses
- **Medium (200-500)**: Paragraph-length
- **Long (500+)**: Extended content

## Server Configuration

### Port Selection

Choose the port for your Gradio server:

- **Default**: 7860
- **Custom**: Any available port (1024-65535)
- **Tip**: Use different ports for multiple simultaneous demos

### Sharing Options

Control demo accessibility:

- **Local Only**: Demo accessible only on your machine
- **Public Sharing**: Demo accessible via public URL
- **Network Sharing**: Demo accessible on local network

## Demo Status States

### Created

Demo configuration saved but server not started:

- **Actions Available**: Launch, Delete
- **Next Step**: Launch the demo

### Running

Demo server is active and accessible:

- **Actions Available**: Stop, Open in Browser, Delete
- **URL Available**: Local and public (if sharing enabled)
- **Next Step**: Test the demo or share the URL

### Stopped

Demo server was running but has been stopped:

- **Actions Available**: Launch, Delete
- **Next Step**: Re-launch or delete the demo

### Error

Demo encountered an error:

- **Actions Available**: Delete, View Error
- **Next Step**: Check error message and recreate demo

## Code Generation

### Python Code

Complete Gradio application code:

```python
import gradio as gr
from transformers import pipeline

# Load model
generator = pipeline("text-generation", model="your-model-path")

# Define generation function
def generate(prompt, temperature, top_p, max_tokens):
    result = generator(
        prompt,
        max_length=max_tokens,
        temperature=temperature,
        top_p=top_p
    )
    return result[0]['generated_text']

# Create Gradio interface
demo = gr.Interface(
    fn=generate,
    inputs=[
        gr.Textbox(label="Prompt"),
        gr.Slider(0, 2, value=0.7, label="Temperature"),
        gr.Slider(0, 1, value=0.9, label="Top P"),
        gr.Slider(1, 2048, value=512, label="Max Tokens")
    ],
    outputs=gr.Textbox(label="Generated Text"),
    title="Your Model Demo",
    description="Test your fine-tuned model"
)

# Launch
demo.launch(server_port=7860, share=True)
```

### HTML/iframe Code

Embeddable code for websites:

```html
<iframe
  src="https://your-public-url.gradio.app"
  frameborder="0"
  width="850"
  height="450"
></iframe>
```

## Best Practices

### Demo Configuration

- Use descriptive names for easy identification
- Set appropriate generation parameters for your use case
- Test locally before enabling public sharing
- Choose the right interface type for your model

### Server Management

- Stop demos when not in use to free resources
- Use different ports for multiple simultaneous demos
- Monitor server logs for errors
- Restart demos if they become unresponsive

### Sharing

- Only share demos you're comfortable making public
- Test demos thoroughly before sharing
- Provide clear instructions for users
- Monitor usage if possible

### Code Customization

- Copy generated code as a starting point
- Customize interface elements as needed
- Add additional inputs or outputs
- Enhance with custom CSS or JavaScript

### Resource Management

- Limit the number of running demos
- Delete old or unused demos
- Monitor system resources (CPU, memory, GPU)
- Use quantization for large models

## Troubleshooting

### Demo Won't Launch

**Problem**: Demo fails to start

**Solutions**:
- Check if port is already in use
- Verify model path is correct
- Ensure sufficient system resources
- Check server logs for errors
- Try a different port

### Public URL Not Generated

**Problem**: Sharing enabled but no public URL

**Solutions**:
- Verify internet connectivity
- Check firewall settings
- Ensure Gradio version supports sharing
- Try restarting the demo
- Check backend logs

### Demo Crashes or Freezes

**Problem**: Demo becomes unresponsive

**Solutions**:
- Stop and restart the demo
- Check system resources
- Reduce max_tokens if generating long text
- Enable quantization for large models
- Review error logs

### Code Copy Issues

**Problem**: Copy to clipboard doesn't work

**Solutions**:
- Check browser permissions
- Try manual copy (Ctrl+C / Cmd+C)
- Refresh the page
- Try a different browser

### Model Loading Errors

**Problem**: Model fails to load in demo

**Solutions**:
- Verify model path is correct
- Check model format is compatible
- Ensure sufficient memory
- Try using a smaller model
- Check model dependencies

## Advanced Features

### Custom Interfaces

Customize beyond the standard interface types:

1. Copy the generated Python code
2. Modify the Gradio interface definition
3. Add custom components
4. Enhance with CSS styling
5. Deploy independently

### API Integration

Use API endpoints instead of local models:

1. Select "API Endpoint" in configuration
2. Enter your API URL
3. Configure authentication if needed
4. Test the connection
5. Launch the demo

### Multi-Model Demos

Create demos that compare multiple models:

1. Create separate demos for each model
2. Or customize code to load multiple models
3. Add comparison interface
4. Display results side-by-side

### Analytics Integration

Track demo usage:

1. Add analytics code to generated Python
2. Track user interactions
3. Monitor performance metrics
4. Analyze usage patterns

## Security Considerations

### Public Sharing

- Be cautious with sensitive models
- Consider rate limiting
- Monitor for abuse
- Use authentication if needed

### Model Access

- Protect proprietary models
- Use API endpoints for sensitive models
- Implement access controls
- Monitor usage logs

### Resource Limits

- Set max_tokens limits
- Implement request throttling
- Monitor resource usage
- Set up alerts for high usage

## Related Documentation

- [Inference Playground](inference-playground.md)
- [Deployment Guide](deployment.md)
- [Model Browser](model-browser.md)
- [Training Configuration](training-configuration.md)

## Support

For issues or questions about Gradio demos:

1. Check the [Troubleshooting Guide](../reference/troubleshooting.md)
2. Review the [FAQ](../reference/faq.md)
3. Visit [Gradio Documentation](https://gradio.app/docs)
4. Open an issue on GitHub
5. Contact support

---

**Status**: ✅ Complete  
**Version**: 1.0  
**Last Updated**: 2024
