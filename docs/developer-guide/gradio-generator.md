# Gradio Demo Generator Implementation

## Overview

The Gradio Demo Generator service enables users to create interactive demos for their fine-tuned models with customizable interfaces and deployment options.

## Features Implemented

### 1. Demo Configuration and Creation (Requirement 11.1)
- **DemoConfig**: Comprehensive configuration for Gradio demos
  - Model selection (local or API endpoint)
  - Customizable input/output components (textbox, chatbot, audio, image)
  - Generation parameters (temperature, top_p, top_k, max_tokens)
  - Server configuration (port, sharing options)
- **Demo Creation**: Create and manage multiple demo configurations

### 2. Code Generation (Requirement 11.1)
- **Automatic Code Generation**: Generate complete Gradio interface code
  - Local model inference using transformers library
  - API endpoint integration with authentication
  - Proper string escaping for Python code generation
  - Handles special characters, quotes, and control characters
- **Syntactically Valid**: All generated code is valid Python

### 3. Server Management (Requirement 11.2)
- **Launch Demos**: Start Gradio servers with configured settings
- **Local URLs**: Provide local access URLs (http://127.0.0.1:port)
- **Public Sharing**: Optional public URL generation via Gradio sharing
- **Process Management**: Track and manage demo server processes
- **Stop Demos**: Gracefully terminate running demo servers

### 4. Customizable Parameters (Requirement 11.3)
- **Input Configuration**: Custom labels, placeholders, and types
- **Output Configuration**: Custom labels and types
- **Generation Parameters**: Temperature, top_p, top_k, max_tokens
- **Example Prompts**: Pre-configured example inputs

### 5. Dual Endpoint Support (Requirement 11.4)
- **Local Models**: Load and run models locally using transformers
- **API Endpoints**: Connect to deployed model APIs
- **Authentication**: Support for API key authentication
- **Flexible Switching**: Easy switching between local and remote inference

### 6. Embeddable Code Generation (Requirement 11.5)
- **iframe Embed**: Generate HTML iframe code for websites
- **JavaScript Embed**: Generate Gradio web component code
- **Public URL Required**: Validates public URL availability
- **Copy-Paste Ready**: Complete embeddable code snippets

## API Endpoints

### POST /api/gradio-demos/create
Create a new Gradio demo configuration.

**Request Body:**
```json
{
  "demo_id": "my-demo",
  "model_id": "my-model",
  "model_path": "/path/to/model",
  "title": "My Demo",
  "description": "Demo description",
  "input_type": "textbox",
  "output_type": "textbox",
  "max_tokens": 512,
  "temperature": 0.7,
  "share": false,
  "use_local_model": true
}
```

### POST /api/gradio-demos/{demo_id}/launch
Launch a Gradio demo server.

**Response:**
```json
{
  "demo_id": "my-demo",
  "status": "running",
  "local_url": "http://127.0.0.1:7860",
  "public_url": null,
  "process_id": 12345
}
```

### POST /api/gradio-demos/{demo_id}/stop
Stop a running Gradio demo.

### GET /api/gradio-demos/{demo_id}
Get information about a demo.

### GET /api/gradio-demos/
List all demos with optional status filter.

### GET /api/gradio-demos/{demo_id}/code
Get the generated Gradio code for a demo.

**Response:**
```json
{
  "demo_id": "my-demo",
  "code": "import gradio as gr\n\n..."
}
```

### GET /api/gradio-demos/{demo_id}/embed
Get embeddable HTML/JavaScript code.

**Response:**
```json
{
  "demo_id": "my-demo",
  "embed_code": "<iframe src=\"...\">...</iframe>"
}
```

### DELETE /api/gradio-demos/{demo_id}
Delete a demo.

## Property-Based Tests

### Test Coverage
All 11 property-based tests passing (100 examples each):

1. **Demo Creation**: Valid DemoInfo with CREATED status
2. **Code Validity**: Generated code is syntactically valid Python
3. **Config Parameters**: All parameters included in generated code
4. **Local Model Code**: Uses transformers library correctly
5. **API Endpoint Code**: Uses requests library correctly
6. **URL Format**: Valid URL formats for local and public URLs
7. **Embed Requirements**: Requires public URL for embeddable code
8. **Embed Content**: Contains valid iframe elements
9. **Config Round-Trip**: Export/import preserves configuration
10. **Lifecycle Transitions**: Correct status transitions
11. **Demo Isolation**: Multiple demos managed independently

### Property Validation
**Property 15: Gradio demo generation**
- For any adapter, generating a Gradio demo produces a functional interface
- Generated code is syntactically valid Python
- All configuration parameters are properly included
- Supports both local and deployed model endpoints
- Validates: Requirements 11.1, 11.2

## Usage Example

```python
from services.gradio_demo_service import get_gradio_demo_service, DemoConfig

# Get service instance
service = get_gradio_demo_service()

# Create demo configuration
config = DemoConfig(
    demo_id="my-chatbot-demo",
    model_id="my-finetuned-model",
    model_path="/models/my-model",
    title="My Chatbot Demo",
    description="Try out my fine-tuned chatbot!",
    input_type="textbox",
    output_type="textbox",
    max_tokens=512,
    temperature=0.7,
    share=True  # Enable public sharing
)

# Create demo
demo_info = service.create_demo(config)

# Launch demo server
demo_info = service.launch_demo(config.demo_id)
print(f"Demo running at: {demo_info.local_url}")
print(f"Public URL: {demo_info.public_url}")

# Get embeddable code
embed_code = service.generate_embeddable_code(config.demo_id)
print(f"Embed code:\n{embed_code}")

# Stop demo when done
service.stop_demo(config.demo_id)
```

## Implementation Details

### String Escaping
The service properly escapes all user-provided strings for Python code generation:
- Removes null bytes and control characters
- Escapes backslashes, quotes, newlines, tabs
- Prevents code injection vulnerabilities

### Process Management
- Demos run in separate Python subprocesses
- Process IDs tracked for management
- Graceful termination with timeout
- Automatic cleanup on deletion

### Configuration Export/Import
- JSON serialization of demo configurations
- DateTime handling for timestamps
- Preserves all configuration parameters
- Enables sharing and reuse of demo setups

## Files Created

1. **backend/services/gradio_demo_service.py** - Core service implementation
2. **backend/services/gradio_demo_api.py** - FastAPI endpoints
3. **backend/tests/test_gradio_demo_generation.py** - Property-based tests
4. **backend/services/GRADIO_DEMO_GENERATOR.md** - This documentation

## Integration

The Gradio demo generator is integrated into the main FastAPI application:
- Router registered in `backend/main.py`
- Available at `/api/gradio-demos/*` endpoints
- Ready for frontend integration

## Next Steps

Frontend implementation should include:
1. Demo configuration wizard UI
2. Demo management dashboard
3. Live demo preview
4. Code viewer and copy functionality
5. Embed code generator UI
