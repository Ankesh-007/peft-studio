"""
Model Export Service for converting and packaging models to various formats.
"""

from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import shutil
import logging
import subprocess
import tempfile
from datetime import datetime

logger = logging.getLogger(__name__)


ExportFormat = Literal['huggingface', 'ollama', 'gguf', 'lmstudio']


@dataclass
class ExportResult:
    """Result of a model export operation"""
    success: bool
    format: ExportFormat
    output_path: str
    artifacts: List[str]  # List of generated files
    size_bytes: int
    message: str
    verification_passed: bool = False
    verification_details: Optional[Dict[str, Any]] = None


@dataclass
class HuggingFaceExport:
    """HuggingFace export package"""
    model_path: str
    model_card: str
    config_file: str
    tokenizer_files: List[str]
    adapter_files: List[str]


@dataclass
class OllamaExport:
    """Ollama export package"""
    modelfile_path: str
    model_path: str
    instructions: str


@dataclass
class GGUFExport:
    """GGUF export package"""
    gguf_path: str
    quantization: str
    size_bytes: int


@dataclass
class LMStudioExport:
    """LM Studio export package"""
    package_path: str
    model_files: List[str]
    config_file: str


class ModelExporter:
    """Service for exporting models to various formats"""
    
    def __init__(self, export_base_path: str = "./exports"):
        self.export_base_path = Path(export_base_path)
        self.export_base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"ModelExporter initialized at {self.export_base_path}")
    
    def export_model(
        self,
        model_path: str,
        format: ExportFormat,
        model_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        quantization: Optional[str] = None,
        merge_adapters: bool = True
    ) -> ExportResult:
        """
        Export a model to the specified format.
        
        Args:
            model_path: Path to the model checkpoint
            format: Target export format
            model_name: Name for the exported model
            metadata: Optional metadata (config, metrics, etc.)
            quantization: Optional quantization level for GGUF
            merge_adapters: Whether to merge LoRA adapters with base model
            
        Returns:
            ExportResult object
        """
        try:
            logger.info(f"Starting export of {model_name} to {format}")
            
            if format == 'huggingface':
                return self._export_to_huggingface(model_path, model_name, metadata, merge_adapters)
            elif format == 'ollama':
                return self._export_to_ollama(model_path, model_name, metadata, merge_adapters)
            elif format == 'gguf':
                return self._export_to_gguf(model_path, model_name, quantization, merge_adapters)
            elif format == 'lmstudio':
                return self._export_to_lmstudio(model_path, model_name, metadata, merge_adapters)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            return ExportResult(
                success=False,
                format=format,
                output_path="",
                artifacts=[],
                size_bytes=0,
                message=f"Export failed: {str(e)}",
                verification_passed=False
            )
    
    def _export_to_huggingface(
        self,
        model_path: str,
        model_name: str,
        metadata: Optional[Dict[str, Any]],
        merge_adapters: bool
    ) -> ExportResult:
        """
        Export model to HuggingFace format with model card, config, and tokenizer.
        
        Args:
            model_path: Path to the model checkpoint
            model_name: Name for the exported model
            metadata: Model metadata
            merge_adapters: Whether to merge LoRA adapters
            
        Returns:
            ExportResult object
        """
        output_dir = self.export_base_path / "huggingface" / model_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        artifacts = []
        
        try:
            # Copy model files
            model_src = Path(model_path)
            if model_src.is_dir():
                # Copy all model files
                for file in model_src.glob("*"):
                    if file.is_file():
                        dest = output_dir / file.name
                        shutil.copy2(file, dest)
                        artifacts.append(str(dest))
            else:
                # Single file
                dest = output_dir / model_src.name
                shutil.copy2(model_src, dest)
                artifacts.append(str(dest))
            
            # Generate model card
            model_card_path = output_dir / "README.md"
            model_card_content = self._generate_model_card(model_name, metadata)
            model_card_path.write_text(model_card_content)
            artifacts.append(str(model_card_path))
            
            # Generate/copy config
            config_path = output_dir / "config.json"
            if metadata and 'config' in metadata:
                with open(config_path, 'w') as f:
                    json.dump(metadata['config'], f, indent=2)
                artifacts.append(str(config_path))
            
            # Copy tokenizer files if they exist
            tokenizer_files = ['tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'vocab.json']
            for tokenizer_file in tokenizer_files:
                src_file = model_src.parent / tokenizer_file if model_src.is_file() else model_src / tokenizer_file
                if src_file.exists():
                    dest = output_dir / tokenizer_file
                    shutil.copy2(src_file, dest)
                    artifacts.append(str(dest))
            
            # Calculate total size
            total_size = sum(Path(f).stat().st_size for f in artifacts if Path(f).exists())
            
            # Verify export
            verification = self._verify_huggingface_export(output_dir)
            
            return ExportResult(
                success=True,
                format='huggingface',
                output_path=str(output_dir),
                artifacts=artifacts,
                size_bytes=total_size,
                message=f"Successfully exported to HuggingFace format at {output_dir}",
                verification_passed=verification['passed'],
                verification_details=verification
            )
            
        except Exception as e:
            logger.error(f"HuggingFace export failed: {str(e)}")
            raise
    
    def _export_to_ollama(
        self,
        model_path: str,
        model_name: str,
        metadata: Optional[Dict[str, Any]],
        merge_adapters: bool
    ) -> ExportResult:
        """
        Export model to Ollama format with Modelfile generation.
        
        Args:
            model_path: Path to the model checkpoint
            model_name: Name for the exported model
            metadata: Model metadata
            merge_adapters: Whether to merge LoRA adapters
            
        Returns:
            ExportResult object
        """
        output_dir = self.export_base_path / "ollama" / model_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        artifacts = []
        
        try:
            # Copy model files
            model_src = Path(model_path)
            model_dest = output_dir / "model"
            
            if model_src.is_dir():
                shutil.copytree(model_src, model_dest, dirs_exist_ok=True)
            else:
                model_dest.mkdir(exist_ok=True)
                shutil.copy2(model_src, model_dest / model_src.name)
            
            artifacts.append(str(model_dest))
            
            # Generate Modelfile
            modelfile_path = output_dir / "Modelfile"
            modelfile_content = self._generate_modelfile(model_name, metadata)
            modelfile_path.write_text(modelfile_content)
            artifacts.append(str(modelfile_path))
            
            # Generate installation instructions
            instructions_path = output_dir / "INSTALL.md"
            instructions_content = self._generate_ollama_instructions(model_name)
            instructions_path.write_text(instructions_content)
            artifacts.append(str(instructions_path))
            
            # Calculate total size
            total_size = sum(
                f.stat().st_size 
                for f in output_dir.rglob('*') 
                if f.is_file()
            )
            
            # Verify export
            verification = self._verify_ollama_export(output_dir)
            
            return ExportResult(
                success=True,
                format='ollama',
                output_path=str(output_dir),
                artifacts=artifacts,
                size_bytes=total_size,
                message=f"Successfully exported to Ollama format at {output_dir}",
                verification_passed=verification['passed'],
                verification_details=verification
            )
            
        except Exception as e:
            logger.error(f"Ollama export failed: {str(e)}")
            raise
    
    def _export_to_gguf(
        self,
        model_path: str,
        model_name: str,
        quantization: Optional[str],
        merge_adapters: bool
    ) -> ExportResult:
        """
        Export model to GGUF format using llama.cpp conversion.
        
        Args:
            model_path: Path to the model checkpoint
            model_name: Name for the exported model
            quantization: Quantization level (e.g., 'Q4_K_M', 'Q5_K_S')
            merge_adapters: Whether to merge LoRA adapters
            
        Returns:
            ExportResult object
        """
        output_dir = self.export_base_path / "gguf" / model_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        artifacts = []
        
        try:
            # For now, we'll create a placeholder implementation
            # In production, this would use llama.cpp's convert.py script
            
            quant_suffix = f"-{quantization}" if quantization else ""
            gguf_filename = f"{model_name}{quant_suffix}.gguf"
            gguf_path = output_dir / gguf_filename
            
            # Placeholder: Copy model and add .gguf extension
            # In production, this would run the actual conversion
            model_src = Path(model_path)
            
            # Create a metadata file instead of actual conversion for now
            metadata_path = output_dir / "conversion_info.json"
            metadata = {
                "source_model": str(model_src),
                "quantization": quantization or "none",
                "timestamp": datetime.now().isoformat(),
                "note": "GGUF conversion requires llama.cpp to be installed"
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            artifacts.append(str(metadata_path))
            
            # Create instructions file
            instructions_path = output_dir / "CONVERSION_INSTRUCTIONS.md"
            instructions_content = self._generate_gguf_instructions(model_name, quantization)
            instructions_path.write_text(instructions_content)
            artifacts.append(str(instructions_path))
            
            # Calculate size
            total_size = sum(Path(f).stat().st_size for f in artifacts if Path(f).exists())
            
            # Verification
            verification = self._verify_gguf_export(output_dir)
            
            return ExportResult(
                success=True,
                format='gguf',
                output_path=str(output_dir),
                artifacts=artifacts,
                size_bytes=total_size,
                message=f"GGUF export prepared at {output_dir}. Manual conversion required.",
                verification_passed=verification['passed'],
                verification_details=verification
            )
            
        except Exception as e:
            logger.error(f"GGUF export failed: {str(e)}")
            raise
    
    def _export_to_lmstudio(
        self,
        model_path: str,
        model_name: str,
        metadata: Optional[Dict[str, Any]],
        merge_adapters: bool
    ) -> ExportResult:
        """
        Export model to LM Studio format.
        
        Args:
            model_path: Path to the model checkpoint
            model_name: Name for the exported model
            metadata: Model metadata
            merge_adapters: Whether to merge LoRA adapters
            
        Returns:
            ExportResult object
        """
        output_dir = self.export_base_path / "lmstudio" / model_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        artifacts = []
        
        try:
            # Copy model files
            model_src = Path(model_path)
            model_dest = output_dir / "model"
            
            if model_src.is_dir():
                shutil.copytree(model_src, model_dest, dirs_exist_ok=True)
            else:
                model_dest.mkdir(exist_ok=True)
                shutil.copy2(model_src, model_dest / model_src.name)
            
            artifacts.append(str(model_dest))
            
            # Generate config for LM Studio
            config_path = output_dir / "lmstudio_config.json"
            config = {
                "model_name": model_name,
                "model_type": "transformers",
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat()
            }
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            artifacts.append(str(config_path))
            
            # Generate instructions
            instructions_path = output_dir / "LMSTUDIO_SETUP.md"
            instructions_content = self._generate_lmstudio_instructions(model_name)
            instructions_path.write_text(instructions_content)
            artifacts.append(str(instructions_path))
            
            # Calculate total size
            total_size = sum(
                f.stat().st_size 
                for f in output_dir.rglob('*') 
                if f.is_file()
            )
            
            # Verify export
            verification = self._verify_lmstudio_export(output_dir)
            
            return ExportResult(
                success=True,
                format='lmstudio',
                output_path=str(output_dir),
                artifacts=artifacts,
                size_bytes=total_size,
                message=f"Successfully exported to LM Studio format at {output_dir}",
                verification_passed=verification['passed'],
                verification_details=verification
            )
            
        except Exception as e:
            logger.error(f"LM Studio export failed: {str(e)}")
            raise
    
    def _generate_model_card(self, model_name: str, metadata: Optional[Dict[str, Any]]) -> str:
        """Generate a HuggingFace model card"""
        config = metadata.get('config', {}) if metadata else {}
        metrics = metadata.get('metrics', {}) if metadata else {}
        
        card = f"""---
license: apache-2.0
tags:
- peft
- lora
- fine-tuned
---

# {model_name}

This model was fine-tuned using PEFT Studio.

## Model Details

- **Base Model**: {config.get('model_name', 'Unknown')}
- **Fine-tuning Method**: {config.get('peft_method', 'LoRA')}
- **Training Date**: {datetime.now().strftime('%Y-%m-%d')}

## Training Configuration

"""
        
        if config:
            card += "```json\n"
            card += json.dumps(config, indent=2)
            card += "\n```\n\n"
        
        card += "## Training Metrics\n\n"
        
        if metrics:
            for key, value in metrics.items():
                card += f"- **{key}**: {value}\n"
        
        card += """
## Usage

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Load base model
base_model = AutoModelForCausalLM.from_pretrained("base_model_name")
tokenizer = AutoTokenizer.from_pretrained("base_model_name")

# Load fine-tuned adapter
model = PeftModel.from_pretrained(base_model, "path/to/this/model")

# Generate text
inputs = tokenizer("Your prompt here", return_tensors="pt")
outputs = model.generate(**inputs)
print(tokenizer.decode(outputs[0]))
```

## Citation

If you use this model, please cite:

```
@misc{""" + model_name.replace('-', '_') + """,
  author = {PEFT Studio},
  title = {""" + model_name + """},
  year = {""" + str(datetime.now().year) + """},
  publisher = {HuggingFace},
}
```
"""
        
        return card
    
    def _generate_modelfile(self, model_name: str, metadata: Optional[Dict[str, Any]]) -> str:
        """Generate an Ollama Modelfile"""
        config = metadata.get('config', {}) if metadata else {}
        
        modelfile = f"""# Modelfile for {model_name}

FROM ./model

# Model parameters
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 2048

# System prompt
SYSTEM You are a helpful AI assistant fine-tuned for specific tasks.

# Template
TEMPLATE \"\"\"{{{{ if .System }}}}<|system|>
{{{{ .System }}}}<|end|>
{{{{ end }}}}{{{{ if .Prompt }}}}<|user|>
{{{{ .Prompt }}}}<|end|>
{{{{ end }}}}<|assistant|>
{{{{ .Response }}}}<|end|>
\"\"\"
"""
        
        return modelfile
    
    def _generate_ollama_instructions(self, model_name: str) -> str:
        """Generate Ollama installation instructions"""
        return f"""# Ollama Installation Instructions for {model_name}

## Prerequisites

- Ollama installed on your system ([Download](https://ollama.ai/download))

## Installation Steps

1. Navigate to this directory:
   ```bash
   cd {model_name}
   ```

2. Create the model in Ollama:
   ```bash
   ollama create {model_name} -f Modelfile
   ```

3. Run the model:
   ```bash
   ollama run {model_name}
   ```

## Usage

Once installed, you can use the model via:

- **CLI**: `ollama run {model_name}`
- **API**: `curl http://localhost:11434/api/generate -d '{{"model": "{model_name}", "prompt": "Your prompt here"}}'`
- **Python**: 
  ```python
  import ollama
  response = ollama.generate(model='{model_name}', prompt='Your prompt here')
  print(response['response'])
  ```

## Troubleshooting

If you encounter issues:
1. Ensure Ollama is running: `ollama serve`
2. Check model list: `ollama list`
3. View logs: `ollama logs`
"""
    
    def _generate_gguf_instructions(self, model_name: str, quantization: Optional[str]) -> str:
        """Generate GGUF conversion instructions"""
        quant_info = f" with {quantization} quantization" if quantization else ""
        
        return f"""# GGUF Conversion Instructions for {model_name}

## Prerequisites

- llama.cpp installed ([GitHub](https://github.com/ggerganov/llama.cpp))
- Python 3.8+

## Conversion Steps

1. Clone llama.cpp if not already installed:
   ```bash
   git clone https://github.com/ggerganov/llama.cpp
   cd llama.cpp
   make
   ```

2. Convert the model to GGUF format{quant_info}:
   ```bash
   python convert.py /path/to/source/model --outfile {model_name}.gguf
   ```

3. (Optional) Quantize the model:
   ```bash
   ./quantize {model_name}.gguf {model_name}-{quantization or 'Q4_K_M'}.gguf {quantization or 'Q4_K_M'}
   ```

## Quantization Options

- **Q4_K_M**: Balanced quality and size (recommended)
- **Q5_K_S**: Higher quality, larger size
- **Q8_0**: Highest quality, largest size
- **Q4_0**: Smallest size, lower quality

## Usage

Run with llama.cpp:
```bash
./main -m {model_name}.gguf -p "Your prompt here"
```

Or use with compatible applications like:
- LM Studio
- Ollama (with GGUF support)
- Text generation web UI
"""
    
    def _generate_lmstudio_instructions(self, model_name: str) -> str:
        """Generate LM Studio setup instructions"""
        return f"""# LM Studio Setup Instructions for {model_name}

## Prerequisites

- LM Studio installed ([Download](https://lmstudio.ai/))

## Installation Steps

1. Open LM Studio

2. Click on "Local Models" in the sidebar

3. Click "Import Model" button

4. Navigate to this directory and select the model folder

5. Wait for the import to complete

## Usage

1. Select {model_name} from your local models list

2. Configure generation parameters:
   - Temperature: 0.7
   - Top P: 0.9
   - Max Tokens: 2048

3. Start chatting or use the API endpoint

## API Usage

LM Studio provides a local API server:

```python
import requests

response = requests.post('http://localhost:1234/v1/chat/completions', json={{
    "model": "{model_name}",
    "messages": [
        {{"role": "user", "content": "Your prompt here"}}
    ],
    "temperature": 0.7
}})

print(response.json()['choices'][0]['message']['content'])
```

## Troubleshooting

- Ensure the model files are complete
- Check LM Studio logs for errors
- Verify sufficient disk space and RAM
"""
    
    def _verify_huggingface_export(self, export_dir: Path) -> Dict[str, Any]:
        """Verify HuggingFace export completeness"""
        required_files = ['README.md']
        optional_files = ['config.json', 'tokenizer.json', 'tokenizer_config.json']
        
        found_files = []
        missing_files = []
        
        for file in required_files:
            if (export_dir / file).exists():
                found_files.append(file)
            else:
                missing_files.append(file)
        
        for file in optional_files:
            if (export_dir / file).exists():
                found_files.append(file)
        
        # Check for model weights
        has_model_weights = any(
            f.suffix in ['.bin', '.safetensors', '.pt', '.pth']
            for f in export_dir.glob('*')
        )
        
        passed = len(missing_files) == 0 and has_model_weights
        
        return {
            'passed': passed,
            'found_files': found_files,
            'missing_required_files': missing_files,
            'has_model_weights': has_model_weights,
            'message': 'Export verification passed' if passed else f'Missing required files: {missing_files}'
        }
    
    def _verify_ollama_export(self, export_dir: Path) -> Dict[str, Any]:
        """Verify Ollama export completeness"""
        required_files = ['Modelfile', 'INSTALL.md']
        
        found_files = []
        missing_files = []
        
        for file in required_files:
            if (export_dir / file).exists():
                found_files.append(file)
            else:
                missing_files.append(file)
        
        # Check for model directory
        has_model_dir = (export_dir / 'model').exists()
        
        passed = len(missing_files) == 0 and has_model_dir
        
        return {
            'passed': passed,
            'found_files': found_files,
            'missing_required_files': missing_files,
            'has_model_directory': has_model_dir,
            'message': 'Export verification passed' if passed else f'Missing: {missing_files}'
        }
    
    def _verify_gguf_export(self, export_dir: Path) -> Dict[str, Any]:
        """Verify GGUF export completeness"""
        # For placeholder implementation, just check for instructions
        has_instructions = (export_dir / 'CONVERSION_INSTRUCTIONS.md').exists()
        has_metadata = (export_dir / 'conversion_info.json').exists()
        
        passed = has_instructions and has_metadata
        
        return {
            'passed': passed,
            'has_instructions': has_instructions,
            'has_metadata': has_metadata,
            'message': 'GGUF export prepared (manual conversion required)' if passed else 'Export incomplete'
        }
    
    def _verify_lmstudio_export(self, export_dir: Path) -> Dict[str, Any]:
        """Verify LM Studio export completeness"""
        required_files = ['lmstudio_config.json', 'LMSTUDIO_SETUP.md']
        
        found_files = []
        missing_files = []
        
        for file in required_files:
            if (export_dir / file).exists():
                found_files.append(file)
            else:
                missing_files.append(file)
        
        # Check for model directory
        has_model_dir = (export_dir / 'model').exists()
        
        passed = len(missing_files) == 0 and has_model_dir
        
        return {
            'passed': passed,
            'found_files': found_files,
            'missing_required_files': missing_files,
            'has_model_directory': has_model_dir,
            'message': 'Export verification passed' if passed else f'Missing: {missing_files}'
        }
    
    def verify_export(self, export_path: str, format: ExportFormat) -> Dict[str, Any]:
        """
        Verify an exported model.
        
        Args:
            export_path: Path to the exported model
            format: Export format
            
        Returns:
            Verification result dictionary
        """
        export_dir = Path(export_path)
        
        if not export_dir.exists():
            return {
                'passed': False,
                'message': f'Export directory does not exist: {export_path}'
            }
        
        if format == 'huggingface':
            return self._verify_huggingface_export(export_dir)
        elif format == 'ollama':
            return self._verify_ollama_export(export_dir)
        elif format == 'gguf':
            return self._verify_gguf_export(export_dir)
        elif format == 'lmstudio':
            return self._verify_lmstudio_export(export_dir)
        else:
            return {
                'passed': False,
                'message': f'Unknown format: {format}'
            }


# Singleton instance
_model_exporter_instance = None


def get_model_exporter() -> ModelExporter:
    """Get singleton instance of ModelExporter"""
    global _model_exporter_instance
    if _model_exporter_instance is None:
        _model_exporter_instance = ModelExporter()
    return _model_exporter_instance
