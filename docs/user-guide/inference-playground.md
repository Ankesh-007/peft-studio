# Inference Playground

## Overview

The Inference Playground provides a comprehensive interface for testing your fine-tuned models with custom prompts and real-time streaming responses. Load models locally, experiment with generation parameters, and manage conversation history—all within PEFT Studio.

## Features

### Model Loading

Load and manage models for inference testing:

- **Model ID Input**: Specify the base model or fine-tuned model ID
- **Adapter Support**: Optionally load LoRA or other PEFT adapters
- **Use Case Selection**: Choose from predefined use cases:
  - Chatbot
  - Code Generation
  - Summarization
  - Question Answering
  - Creative Writing
  - Domain Adaptation
- **Model Management**: Load, unload, and hot-swap adapters
- **Memory Monitoring**: View memory usage for loaded models

### Quantization Support

Optimize memory usage with quantization:

- **Quantization Options**: int8, int4, or nf4 quantization
- **Automatic Quantization**: System automatically quantizes when VRAM is insufficient
- **Memory Efficiency**: Run larger models on limited hardware

### Prompt Input and Response

Interactive prompt testing with comprehensive controls:

- **Large Textarea**: Ample space for complex prompts
- **Character and Token Count**: Real-time counting as you type
- **Prompt Templates**: Quick templates for different use cases:
  - Chat template
  - Instruction template
  - Raw template
- **Generate Button**: Start inference with loading indicator
- **Reset Functionality**: Clear prompt and output quickly

### Streaming Response Support

Real-time token generation with streaming:

- **WebSocket-Based Streaming**: Token-by-token display
- **Real-Time Statistics**: Tokens per second display
- **Streaming Toggle**: Enable or disable streaming mode
- **Generation Progress**: Visual indicator during generation
- **Cursor Animation**: Animated cursor during streaming

### Generation Settings

Fine-tune generation behavior with configurable parameters:

- **Temperature** (0-2): Control randomness in generation
- **Top P** (0-1): Nucleus sampling threshold
- **Top K**: Limit vocabulary to top K tokens
- **Max Tokens**: Maximum length of generated text
- **Repetition Penalty** (1-2): Discourage repetitive text
- **Stop Sequences**: Define custom stop sequences

### Output Display

View and interact with generated responses:

- **Scrollable Output Area**: Handle long responses
- **Copy to Clipboard**: One-click copy functionality
- **Generation Statistics**: View tokens generated, time elapsed, and generation speed
- **Syntax Highlighting**: For code generation use cases

### Conversation Management

Track and manage conversation history:

- **New Conversation**: Start fresh conversations
- **Active Conversation Indicator**: See which conversation is active
- **Conversation History View**: Browse past conversations
- **Message Display**: View messages with role (user/assistant) and timestamp
- **Delete Conversations**: Remove unwanted conversation history
- **Conversation Filtering**: Filter by model and use case

## User Workflows

### Workflow 1: Load and Test a Model

1. Navigate to the **Inference Playground**
2. Enter the model ID (e.g., `meta-llama/Llama-2-7b-hf`)
3. Optionally enter an adapter path for fine-tuned models
4. Select a use case from the dropdown
5. Click **Load Model**
6. Wait for the model to load (status indicator shows progress)
7. Enter a prompt in the text area
8. Click **Generate** to test the model
9. View the response in the output area

### Workflow 2: Experiment with Generation Parameters

1. Load a model (see Workflow 1)
2. Click the **Settings** button to open the generation settings panel
3. Adjust parameters:
   - Increase temperature for more creative responses
   - Adjust top_p for nucleus sampling
   - Set max_tokens to control response length
   - Modify repetition penalty to reduce repetition
4. Enter a prompt
5. Click **Generate** to see results with new parameters
6. Iterate and refine parameters based on output quality

### Workflow 3: Use Streaming Mode

1. Load a model
2. Enable the **Streaming** toggle
3. Enter a prompt
4. Click **Generate**
5. Watch tokens appear in real-time
6. View generation speed (tokens/sec) during streaming
7. Stop generation early if needed

### Workflow 4: Manage Conversations

1. Load a model
2. Click **New Conversation** to start
3. Enter prompts and generate responses
4. View conversation history in the sidebar
5. Click on previous messages to review
6. Start a new conversation when needed
7. Delete old conversations to clean up history

### Workflow 5: Hot-Swap Adapters

1. Load a base model
2. Test with the base model
3. Enter a new adapter path
4. Click **Swap Adapter** (no need to reload base model)
5. Test with the new adapter
6. Compare results between adapters

## Components

### InferencePlayground

Main component for the inference playground interface:

**Location**: `src/components/InferencePlayground.tsx`

**Features**:
- Model loading section
- Loaded models display
- Prompt template selector
- Prompt input section
- Generation settings panel
- Output display section
- Conversation management

## Backend Integration

### API Endpoints

The UI integrates with the following backend endpoints:

**REST Endpoints**:
- `POST /api/inference/load` - Load a model for inference
- `POST /api/inference/generate` - Generate inference (non-streaming)
- `POST /api/inference/compare` - Compare fine-tuned with base model
- `POST /api/inference/conversation/save` - Save conversation message
- `GET /api/inference/conversation/{id}` - Get conversation history
- `GET /api/inference/conversations` - List all conversations
- `DELETE /api/inference/conversation/{id}` - Delete conversation
- `GET /api/inference/models/loaded` - List loaded models
- `POST /api/inference/models/{id}/unload` - Unload a model
- `POST /api/inference/models/{id}/swap-adapter` - Hot-swap adapter

**WebSocket Endpoints**:
- `WebSocket /api/inference/stream` - Stream inference generation

### Backend Services

- **InferenceService**: Core service for inference operations
- **InferenceAPI**: FastAPI endpoints for REST and WebSocket

## Use Cases

### Chatbot Testing

Test conversational AI models:

1. Load a chatbot-tuned model
2. Use the chat template
3. Enable streaming for natural conversation flow
4. Adjust temperature for personality
5. Use conversation history to maintain context

### Code Generation

Test code generation models:

1. Load a code-tuned model
2. Use the instruction template
3. Set temperature low (0.2-0.5) for deterministic code
4. Increase max_tokens for longer code snippets
5. Use stop sequences to end at function boundaries

### Summarization

Test summarization models:

1. Load a summarization-tuned model
2. Paste long text in the prompt
3. Set max_tokens to desired summary length
4. Use lower temperature for factual summaries
5. Compare outputs with different parameters

### Question Answering

Test QA models:

1. Load a QA-tuned model
2. Format prompt as question
3. Adjust top_p for answer diversity
4. Use repetition penalty to avoid redundant answers
5. Test with various question types

### Creative Writing

Test creative writing models:

1. Load a creative writing model
2. Use higher temperature (0.8-1.2) for creativity
3. Increase max_tokens for longer stories
4. Experiment with different prompts
5. Use streaming to watch the story unfold

## Generation Parameters Guide

### Temperature

Controls randomness in generation:

- **0.0-0.3**: Very deterministic, factual responses
- **0.4-0.7**: Balanced creativity and coherence
- **0.8-1.2**: Creative, diverse responses
- **1.3-2.0**: Highly random, experimental

**Use Cases**:
- Low: Code generation, factual QA, summarization
- Medium: Chatbots, general text generation
- High: Creative writing, brainstorming

### Top P (Nucleus Sampling)

Limits token selection to cumulative probability:

- **0.1-0.5**: Conservative, high-quality tokens only
- **0.6-0.9**: Balanced diversity
- **0.95-1.0**: Maximum diversity

**Use Cases**:
- Low: Formal writing, technical content
- High: Creative writing, diverse responses

### Top K

Limits vocabulary to top K most likely tokens:

- **10-20**: Very conservative
- **40-50**: Balanced
- **100+**: More diverse

**Use Cases**:
- Low: Focused, on-topic responses
- High: Exploratory, diverse vocabulary

### Max Tokens

Maximum length of generated text:

- **50-100**: Short responses, summaries
- **200-500**: Medium responses, paragraphs
- **1000+**: Long-form content, articles

**Tip**: Set based on your use case and model context window

### Repetition Penalty

Discourages repetitive text:

- **1.0**: No penalty
- **1.1-1.3**: Mild penalty, natural text
- **1.4-2.0**: Strong penalty, may affect coherence

**Use Cases**:
- Low: When repetition is acceptable
- High: When model tends to repeat phrases

## Best Practices

### Model Loading

- Start with smaller models for faster loading
- Use quantization for large models on limited hardware
- Unload models when not in use to free memory
- Monitor memory usage to avoid OOM errors

### Prompt Engineering

- Be specific and clear in your prompts
- Use examples for few-shot learning
- Format prompts according to model training
- Iterate and refine based on outputs

### Parameter Tuning

- Start with default parameters
- Adjust one parameter at a time
- Document successful parameter combinations
- Save configurations for reuse

### Conversation Management

- Start new conversations for different topics
- Review conversation history for context
- Delete old conversations to save space
- Use conversation filtering to find specific chats

### Performance Optimization

- Use streaming for better user experience
- Enable quantization for memory efficiency
- Hot-swap adapters instead of reloading base models
- Batch similar prompts when possible

## Troubleshooting

### Model Loading Issues

**Problem**: Model fails to load

**Solutions**:
- Check model ID is correct
- Verify sufficient memory available
- Try enabling quantization
- Check adapter path if using adapters
- Review error messages for specific issues

### Generation Errors

**Problem**: Generation fails or produces poor results

**Solutions**:
- Verify model is loaded successfully
- Check generation parameters are valid
- Ensure prompt is not empty
- Try adjusting temperature and top_p
- Review model's training use case

### Streaming Issues

**Problem**: Streaming doesn't work or is slow

**Solutions**:
- Check WebSocket connection
- Verify network connectivity
- Try disabling and re-enabling streaming
- Check browser console for errors
- Ensure backend service is running

### Memory Issues

**Problem**: Out of memory errors

**Solutions**:
- Enable quantization (int8 or int4)
- Unload unused models
- Reduce batch size
- Use smaller models
- Close other applications

### Conversation History Issues

**Problem**: Conversations not saving or loading

**Solutions**:
- Check backend database connection
- Verify conversation ID is valid
- Refresh the conversation list
- Check browser console for errors
- Ensure sufficient disk space

## Advanced Features

### Model Comparison

Compare fine-tuned model with base model:

1. Load your fine-tuned model
2. Click **Compare with Base**
3. Enter the same prompt for both models
4. View side-by-side results
5. Analyze differences in output quality

### Batch Testing

Test multiple prompts efficiently:

1. Prepare a list of test prompts
2. Load your model once
3. Test each prompt sequentially
4. Save results for analysis
5. Compare across different parameter settings

### Example Prompt Generation

Get started quickly with example prompts:

1. Select a use case when loading a model
2. System generates example prompts
3. Use examples as starting points
4. Modify examples for your specific needs

## Related Documentation

- [Training Configuration Guide](training-configuration.md)
- [Model Browser](model-browser.md)
- [Deployment Guide](deployment.md)
- [Quick Start Guide](quick-start.md)

## Support

For issues or questions about the Inference Playground:

1. Check the [Troubleshooting Guide](../reference/troubleshooting.md)
2. Review the [FAQ](../reference/faq.md)
3. Open an issue on GitHub
4. Contact support

---

**Status**: ✅ Complete  
**Version**: 1.0  
**Last Updated**: 2024
