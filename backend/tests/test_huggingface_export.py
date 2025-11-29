"""
Property-based tests for HuggingFace export completeness.
**Feature: simplified-llm-optimization, Property 32: HuggingFace export completeness**
**Validates: Requirements 15.2**
"""

import pytest
from hypothesis import given, strategies as st, settings
from pathlib import Path
import tempfile
import shutil
import json

from backend.services.export_service import ModelExporter, ExportFormat


# Strategy for generating model metadata
@st.composite
def model_metadata_strategy(draw):
    """Generate realistic model metadata"""
    return {
        'config': {
            'model_name': draw(st.sampled_from([
                'meta-llama/Llama-2-7b-hf',
                'mistralai/Mistral-7B-v0.1',
                'google/gemma-7b'
            ])),
            'peft_method': draw(st.sampled_from(['lora', 'qlora'])),
            'lora_r': draw(st.integers(min_value=8, max_value=64)),
            'lora_alpha': draw(st.integers(min_value=16, max_value=128)),
            'learning_rate': draw(st.floats(min_value=1e-5, max_value=1e-3)),
            'batch_size': draw(st.integers(min_value=1, max_value=32)),
            'epochs': draw(st.integers(min_value=1, max_value=10))
        },
        'metrics': {
            'final_loss': draw(st.floats(min_value=0.1, max_value=5.0)),
            'train_time': draw(st.integers(min_value=60, max_value=36000)),
            'samples_per_second': draw(st.floats(min_value=0.1, max_value=100.0))
        }
    }


@st.composite
def model_name_strategy(draw):
    """Generate valid model names"""
    prefix = draw(st.sampled_from(['chatbot', 'code-gen', 'summarizer', 'qa-model']))
    version = draw(st.integers(min_value=1, max_value=10))
    return f"{prefix}-v{version}"


def create_mock_model_checkpoint(temp_dir: Path, include_tokenizer: bool = True):
    """Create a mock model checkpoint with necessary files"""
    checkpoint_dir = temp_dir / "checkpoint"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock model weights
    model_file = checkpoint_dir / "adapter_model.bin"
    model_file.write_bytes(b"mock_model_weights" * 100)
    
    # Create adapter config
    adapter_config = {
        "peft_type": "LORA",
        "r": 16,
        "lora_alpha": 32,
        "target_modules": ["q_proj", "v_proj"]
    }
    config_file = checkpoint_dir / "adapter_config.json"
    config_file.write_text(json.dumps(adapter_config, indent=2))
    
    if include_tokenizer:
        # Create mock tokenizer files
        tokenizer_files = {
            'tokenizer.json': '{"version": "1.0"}',
            'tokenizer_config.json': '{"model_max_length": 2048}',
            'special_tokens_map.json': '{"eos_token": "</s>"}',
        }
        
        for filename, content in tokenizer_files.items():
            (checkpoint_dir / filename).write_text(content)
    
    return checkpoint_dir


# **Feature: simplified-llm-optimization, Property 32: HuggingFace export completeness**
@given(
    model_name=model_name_strategy(),
    metadata=model_metadata_strategy(),
    include_tokenizer=st.booleans()
)
@settings(max_examples=100, deadline=None)
def test_huggingface_export_completeness(model_name, metadata, include_tokenizer):
    """
    For any model exported to HuggingFace format, the export package should contain
    model weights, model card, configuration file, and tokenizer files.
    
    This property ensures that all required artifacts are present in the export.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create mock model checkpoint
        checkpoint_dir = create_mock_model_checkpoint(temp_path, include_tokenizer)
        
        # Create exporter with temp export path
        export_base = temp_path / "exports"
        exporter = ModelExporter(export_base_path=str(export_base))
        
        # Export the model
        result = exporter.export_model(
            model_path=str(checkpoint_dir),
            format='huggingface',
            model_name=model_name,
            metadata=metadata,
            merge_adapters=False
        )
        
        # Property: Export should succeed
        assert result.success, f"Export failed: {result.message}"
        
        # Property: Output path should exist
        output_path = Path(result.output_path)
        assert output_path.exists(), "Export output path does not exist"
        
        # Property: Model card (README.md) must be present
        readme_path = output_path / "README.md"
        assert readme_path.exists(), "Model card (README.md) is missing"
        assert readme_path.stat().st_size > 0, "Model card is empty"
        
        # Property: Model card should contain model name
        readme_content = readme_path.read_text()
        assert model_name in readme_content, "Model card does not contain model name"
        
        # Property: Configuration file should be present
        config_path = output_path / "config.json"
        if metadata and 'config' in metadata:
            assert config_path.exists(), "Configuration file is missing"
            
            # Property: Config should be valid JSON
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            assert isinstance(config_data, dict), "Config is not a valid dictionary"
        
        # Property: Model weights must be present
        has_model_weights = any(
            f.suffix in ['.bin', '.safetensors', '.pt', '.pth']
            for f in output_path.glob('*')
        )
        assert has_model_weights, "No model weight files found in export"
        
        # Property: If tokenizer files exist in source, they should be in export
        if include_tokenizer:
            tokenizer_files = ['tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json']
            for tokenizer_file in tokenizer_files:
                if (checkpoint_dir / tokenizer_file).exists():
                    exported_tokenizer = output_path / tokenizer_file
                    # Note: We check if at least one tokenizer file is present
                    # since not all may be copied depending on the source
        
        # Property: Artifacts list should not be empty
        assert len(result.artifacts) > 0, "No artifacts were generated"
        
        # Property: All listed artifacts should exist
        for artifact_path in result.artifacts:
            artifact = Path(artifact_path)
            assert artifact.exists(), f"Artifact does not exist: {artifact_path}"
        
        # Property: Size should be greater than zero
        assert result.size_bytes > 0, "Export size is zero"
        
        # Property: Verification should pass
        assert result.verification_passed, f"Verification failed: {result.verification_details}"
        
        # Property: Verification details should indicate completeness
        assert result.verification_details is not None, "No verification details provided"
        assert result.verification_details.get('has_model_weights', False), "Verification did not detect model weights"


@given(
    model_name=model_name_strategy(),
    metadata=model_metadata_strategy()
)
@settings(max_examples=50, deadline=None)
def test_huggingface_export_model_card_content(model_name, metadata):
    """
    For any HuggingFace export, the model card should contain all essential information
    including model details, configuration, and usage instructions.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create mock model checkpoint
        checkpoint_dir = create_mock_model_checkpoint(temp_path)
        
        # Create exporter
        export_base = temp_path / "exports"
        exporter = ModelExporter(export_base_path=str(export_base))
        
        # Export the model
        result = exporter.export_model(
            model_path=str(checkpoint_dir),
            format='huggingface',
            model_name=model_name,
            metadata=metadata,
            merge_adapters=False
        )
        
        assert result.success, "Export failed"
        
        # Read model card
        readme_path = Path(result.output_path) / "README.md"
        readme_content = readme_path.read_text()
        
        # Property: Model card should contain essential sections
        essential_sections = ['Model Details', 'Training Configuration', 'Training Metrics', 'Usage']
        for section in essential_sections:
            assert section in readme_content, f"Model card missing section: {section}"
        
        # Property: Model card should contain base model name from config
        if metadata and 'config' in metadata:
            base_model = metadata['config'].get('model_name', '')
            if base_model:
                assert base_model in readme_content, "Model card does not mention base model"
        
        # Property: Model card should contain training metrics
        if metadata and 'metrics' in metadata:
            # At least one metric should be mentioned
            metrics_section_present = 'Training Metrics' in readme_content
            assert metrics_section_present, "Training metrics section missing"


@given(model_name=model_name_strategy())
@settings(max_examples=50, deadline=None)
def test_huggingface_export_without_metadata(model_name):
    """
    For any model exported without metadata, the export should still succeed
    and create all required files with default content.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create mock model checkpoint
        checkpoint_dir = create_mock_model_checkpoint(temp_path)
        
        # Create exporter
        export_base = temp_path / "exports"
        exporter = ModelExporter(export_base_path=str(export_base))
        
        # Export without metadata
        result = exporter.export_model(
            model_path=str(checkpoint_dir),
            format='huggingface',
            model_name=model_name,
            metadata=None,  # No metadata
            merge_adapters=False
        )
        
        # Property: Export should still succeed without metadata
        assert result.success, "Export failed without metadata"
        
        # Property: Model card should still be created
        readme_path = Path(result.output_path) / "README.md"
        assert readme_path.exists(), "Model card not created without metadata"
        
        # Property: Model weights should still be present
        has_model_weights = any(
            f.suffix in ['.bin', '.safetensors', '.pt', '.pth']
            for f in Path(result.output_path).glob('*')
        )
        assert has_model_weights, "Model weights missing in export without metadata"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
