"""
Gradio Demo Generator Service
Generates interactive Gradio demos for fine-tuned models.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import logging
import json
import subprocess
import threading
import time

logger = logging.getLogger(__name__)


class DemoStatus(Enum):
    """Status of a Gradio demo"""
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class DemoConfig:
    """Configuration for a Gradio demo"""
    demo_id: str
    model_id: str
    model_path: str
    title: str
    description: str
    
    # Input configuration
    input_type: str = "textbox"  # textbox, chatbot, audio, image
    input_label: str = "Input"
    input_placeholder: str = "Enter your prompt here..."
    
    # Output configuration
    output_type: str = "textbox"  # textbox, chatbot, audio, image
    output_label: str = "Output"
    
    # Generation parameters
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    
    # Server configuration
    server_name: str = "127.0.0.1"
    server_port: int = 7860
    share: bool = False
    
    # Endpoint configuration
    use_local_model: bool = True
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    
    created_at: Optional[datetime] = None


@dataclass
class DemoInfo:
    """Information about a running demo"""
    demo_id: str
    config: DemoConfig
    status: DemoStatus
    local_url: Optional[str] = None
    public_url: Optional[str] = None
    process_id: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None


class GradioDemoService:
    """Service for managing Gradio demo generation and lifecycle"""
    
    def __init__(self):
        self._demos: Dict[str, DemoInfo] = {}
        self._processes: Dict[str, subprocess.Popen] = {}
        logger.info("GradioDemoService initialized")
    
    def create_demo(self, config: DemoConfig) -> DemoInfo:
        """
        Create a new Gradio demo configuration.
        
        Args:
            config: DemoConfig with demo settings
            
        Returns:
            DemoInfo with created demo information
            
        Validates: Requirements 11.1
        """
        if config.created_at is None:
            config.created_at = datetime.now()
        
        demo_info = DemoInfo(
            demo_id=config.demo_id,
            config=config,
            status=DemoStatus.CREATED,
            created_at=config.created_at
        )
        
        self._demos[config.demo_id] = demo_info
        logger.info(f"Created demo {config.demo_id}")
        
        return demo_info
    
    def generate_gradio_code(self, config: DemoConfig) -> str:
        """
        Generate Gradio interface code based on configuration.
        
        Args:
            config: DemoConfig with demo settings
            
        Returns:
            Python code string for the Gradio interface
            
        Validates: Requirements 11.1
        """
        # Generate the inference function
        if config.use_local_model:
            inference_code = f'''
def generate_response(prompt):
    """Generate response using local model"""
    # Load model if not already loaded
    if not hasattr(generate_response, 'model'):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        generate_response.tokenizer = AutoTokenizer.from_pretrained("{config.model_path}")
        generate_response.model = AutoModelForCausalLM.from_pretrained("{config.model_path}")
    
    # Generate response
    inputs = generate_response.tokenizer(prompt, return_tensors="pt")
    outputs = generate_response.model.generate(
        **inputs,
        max_new_tokens={config.max_tokens},
        temperature={config.temperature},
        top_p={config.top_p},
        top_k={config.top_k},
        do_sample=True
    )
    response = generate_response.tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response
'''
        else:
            # Properly escape strings for Python code
            def escape_string_api(s: str) -> str:
                """Escape a string for use in Python code"""
                # Remove null bytes and other control characters except newlines/tabs
                s = ''.join(char for char in s if ord(char) >= 32 or char in '\n\r\t')
                # Escape backslashes first
                s = s.replace('\\', '\\\\')
                # Escape quotes
                s = s.replace('"', '\\"')
                # Escape newlines, carriage returns, tabs
                s = s.replace('\n', '\\n')
                s = s.replace('\r', '\\r')
                s = s.replace('\t', '\\t')
                return s
            
            api_key_escaped = escape_string_api(config.api_key) if config.api_key else ""
            api_endpoint_escaped = escape_string_api(config.api_endpoint) if config.api_endpoint else ""
            
            inference_code = f'''
def generate_response(prompt):
    """Generate response using API endpoint"""
    import requests
    
    api_key = "{api_key_escaped}"
    headers = {{"Authorization": f"Bearer {{api_key}}"}} if api_key else {{}}
    
    response = requests.post(
        "{api_endpoint_escaped}",
        headers=headers,
        json={{
            "prompt": prompt,
            "max_tokens": {config.max_tokens},
            "temperature": {config.temperature},
            "top_p": {config.top_p},
            "top_k": {config.top_k}
        }}
    )
    
    if response.status_code == 200:
        return response.json().get("response", "Error: No response")
    else:
        return f"Error: {{response.status_code}} - {{response.text}}"
'''
        
        # Escape strings for Python code - remove null bytes and escape special characters
        def escape_string(s: str) -> str:
            """Escape a string for use in Python code"""
            # Remove null bytes and other control characters
            s = ''.join(char for char in s if ord(char) >= 32 or char in '\n\r\t')
            # Escape backslashes first
            s = s.replace('\\', '\\\\')
            # Escape quotes
            s = s.replace('"', '\\"')
            # Escape newlines
            s = s.replace('\n', '\\n')
            s = s.replace('\r', '\\r')
            s = s.replace('\t', '\\t')
            return s
        
        title_escaped = escape_string(config.title)
        description_escaped = escape_string(config.description)
        input_label_escaped = escape_string(config.input_label)
        input_placeholder_escaped = escape_string(config.input_placeholder)
        output_label_escaped = escape_string(config.output_label)
        
        # Generate the Gradio interface code
        gradio_code = f'''
import gradio as gr

{inference_code}

# Create Gradio interface
demo = gr.Interface(
    fn=generate_response,
    inputs=gr.{config.input_type.capitalize()}(
        label="{input_label_escaped}",
        placeholder="{input_placeholder_escaped}"
    ),
    outputs=gr.{config.output_type.capitalize()}(
        label="{output_label_escaped}"
    ),
    title="{title_escaped}",
    description="{description_escaped}",
    examples=[
        ["Tell me about yourself"],
        ["What can you help me with?"],
        ["Give me an example"]
    ]
)

if __name__ == "__main__":
    demo.launch(
        server_name="{config.server_name}",
        server_port={config.server_port},
        share={str(config.share)}
    )
'''
        
        return gradio_code
    
    def launch_demo(self, demo_id: str) -> DemoInfo:
        """
        Launch a Gradio demo server.
        
        Args:
            demo_id: ID of the demo to launch
            
        Returns:
            Updated DemoInfo with server URLs
            
        Validates: Requirements 11.2
        """
        if demo_id not in self._demos:
            raise ValueError(f"Demo {demo_id} not found")
        
        demo_info = self._demos[demo_id]
        config = demo_info.config
        
        # Generate the Gradio code
        gradio_code = self.generate_gradio_code(config)
        
        # Save to temporary file
        import tempfile
        import os
        
        temp_dir = tempfile.mkdtemp()
        script_path = os.path.join(temp_dir, f"demo_{demo_id}.py")
        
        with open(script_path, 'w') as f:
            f.write(gradio_code)
        
        try:
            # Launch the Gradio server in a subprocess
            process = subprocess.Popen(
                ['python', script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self._processes[demo_id] = process
            
            # Wait a moment for server to start
            time.sleep(2)
            
            # Check if process is still running
            if process.poll() is not None:
                # Process terminated
                _, stderr = process.communicate()
                demo_info.status = DemoStatus.ERROR
                demo_info.error_message = stderr
                logger.error(f"Demo {demo_id} failed to start: {stderr}")
            else:
                # Process is running
                demo_info.status = DemoStatus.RUNNING
                demo_info.process_id = process.pid
                demo_info.started_at = datetime.now()
                
                # Generate URLs
                demo_info.local_url = f"http://{config.server_name}:{config.server_port}"
                
                if config.share:
                    # In a real implementation, we would parse the Gradio output for the public URL
                    demo_info.public_url = f"https://xxxxx.gradio.live"
                
                logger.info(f"Demo {demo_id} launched at {demo_info.local_url}")
        
        except Exception as e:
            demo_info.status = DemoStatus.ERROR
            demo_info.error_message = str(e)
            logger.error(f"Failed to launch demo {demo_id}: {e}")
        
        return demo_info
    
    def stop_demo(self, demo_id: str) -> DemoInfo:
        """
        Stop a running Gradio demo.
        
        Args:
            demo_id: ID of the demo to stop
            
        Returns:
            Updated DemoInfo
        """
        if demo_id not in self._demos:
            raise ValueError(f"Demo {demo_id} not found")
        
        demo_info = self._demos[demo_id]
        
        if demo_id in self._processes:
            process = self._processes[demo_id]
            process.terminate()
            process.wait(timeout=5)
            del self._processes[demo_id]
            
            demo_info.status = DemoStatus.STOPPED
            demo_info.stopped_at = datetime.now()
            logger.info(f"Demo {demo_id} stopped")
        
        return demo_info
    
    def get_demo(self, demo_id: str) -> Optional[DemoInfo]:
        """
        Get information about a demo.
        
        Args:
            demo_id: ID of the demo
            
        Returns:
            DemoInfo if found, None otherwise
        """
        return self._demos.get(demo_id)
    
    def list_demos(self, status: Optional[DemoStatus] = None) -> List[DemoInfo]:
        """
        List all demos with optional status filter.
        
        Args:
            status: Optional status filter
            
        Returns:
            List of DemoInfo objects
        """
        demos = list(self._demos.values())
        
        if status:
            demos = [d for d in demos if d.status == status]
        
        return demos
    
    def generate_embeddable_code(self, demo_id: str) -> str:
        """
        Generate embeddable HTML/JavaScript code for a demo.
        
        Args:
            demo_id: ID of the demo
            
        Returns:
            HTML/JavaScript code string
            
        Validates: Requirements 11.5
        """
        if demo_id not in self._demos:
            raise ValueError(f"Demo {demo_id} not found")
        
        demo_info = self._demos[demo_id]
        
        if not demo_info.public_url:
            raise ValueError(f"Demo {demo_id} does not have a public URL. Enable sharing to get embeddable code.")
        
        # Generate iframe embed code
        embed_code = f'''
<!-- Gradio Demo Embed -->
<iframe
    src="{demo_info.public_url}"
    frameborder="0"
    width="850"
    height="450"
    style="border: 1px solid #e0e0e0; border-radius: 4px;"
></iframe>

<!-- Alternative: JavaScript Embed -->
<script type="module" src="https://gradio.s3-us-west-2.amazonaws.com/3.50.0/gradio.js"></script>
<gradio-app src="{demo_info.public_url}"></gradio-app>
'''
        
        return embed_code
    
    def export_demo_config(self, demo_id: str) -> Dict[str, Any]:
        """
        Export demo configuration as JSON.
        
        Args:
            demo_id: ID of the demo
            
        Returns:
            Dictionary with demo configuration
        """
        if demo_id not in self._demos:
            raise ValueError(f"Demo {demo_id} not found")
        
        demo_info = self._demos[demo_id]
        config_dict = asdict(demo_info.config)
        
        # Convert datetime to ISO format
        if config_dict.get('created_at'):
            config_dict['created_at'] = config_dict['created_at'].isoformat()
        
        return config_dict
    
    def import_demo_config(self, config_dict: Dict[str, Any]) -> DemoConfig:
        """
        Import demo configuration from JSON.
        
        Args:
            config_dict: Dictionary with demo configuration
            
        Returns:
            DemoConfig object
        """
        # Convert ISO format to datetime
        if config_dict.get('created_at'):
            config_dict['created_at'] = datetime.fromisoformat(config_dict['created_at'])
        
        config = DemoConfig(**config_dict)
        return config
    
    def delete_demo(self, demo_id: str) -> bool:
        """
        Delete a demo.
        
        Args:
            demo_id: ID of the demo to delete
            
        Returns:
            True if deleted, False if not found
        """
        if demo_id not in self._demos:
            return False
        
        # Stop if running
        if demo_id in self._processes:
            self.stop_demo(demo_id)
        
        del self._demos[demo_id]
        logger.info(f"Deleted demo {demo_id}")
        return True


# Singleton instance
_gradio_demo_service_instance = None


def get_gradio_demo_service() -> GradioDemoService:
    """Get singleton instance of GradioDemoService"""
    global _gradio_demo_service_instance
    if _gradio_demo_service_instance is None:
        _gradio_demo_service_instance = GradioDemoService()
    return _gradio_demo_service_instance
