"""
Property-based tests for Ollama export artifact generation.
**Feature: simplified-llm-optimization, Property 33: Ollama export generates required artifacts**
**Validates: Requirements 15.3**
"""

import pytest
from hypothesis import given, strategies as st, settings
from pathlib import Path
import tempfile
import json

from services.export_service import ModelExporter


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
            'temperature': draw(st.floats(min_value=0.1, max_value=1.5)),
            'max_tokens': draw(st.integers(min_value=512, max_value=4096))
        },
        'metrics': {
            'final_loss': draw(st.floats(min_value=0.1, max_value=5.0))
        }
    }


@st.composite
def model_name_strategy(draw):
    """Generate valid model names"""
    prefix = draw(st.sampled_from(['chatbot', 'code-assistant', 'summarizer', 'qa-bot']))
    version = draw(st.integers(min_value=1, max_value=10))
    return f"{prefix}-v{version}"


def create_mock_model_checkpoint(temp_dir: Path):
    """Create a mock model checkpoint"""
    checkpoint_dir = temp_dir / "checkpoint"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock model weights
    model_file = checkpoint_dir / "adapter_model.bin"
    model_file.write_bytes(b"mock_model_weights" * 100)
    
    # Create adapter config
    adapter_config = {
        "peft_type": "LORA",
        "r": 16,
        "lora_alpha": 32
    }
    config_file = checkpoint_dir / "adapter_config.json"
    config_file.write_text(json.dumps(adapter_config, indent=2))
    
    return checkpoint_dir


# **Feature: simplified-llm-optimization, Property 33: Ollama export generates required artifacts**
@given(
    model_name=model_name_strategy(),
    metadata=model_metadata_strategy()
)
@settings(max_examples=100, deadline=None)
def test_ollama_export_generates_required_artifacts(model_name, metadata):
    """
    For any model exported to Ollama format, the export should generate
    a valid Modelfile and installation instructions.
    
    This property ensures that all required Ollama artifacts are present.
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
            format='ollama',
            model_name=model_name,
            metadata=metadata,
            merge_adapters=False
        )
        
        # Property: Export should succeed
        assert result.success, f"Export failed: {result.message}"
        
        # Property: Output path should exist
        output_path = Path(result.output_path)
        assert output_path.exists(), "Export output path does not exist"
        
        # Property: Modelfile must be present
        modelfile_path = output_path / "Modelfile"
        assert modelfile_path.exists(), "Modelfile is missing"
        assert modelfile_path.stat().st_size > 0, "Modelfile is empty"
        
        # Property: Installation instructions must be present
        install_path = output_path / "INSTALL.md"
        assert install_path.exists(), "Installation instructions (INSTALL.md) are missing"
        assert install_path.stat().st_size > 0, "Installation instructions are empty"
        
        # Property: Model directory must exist
        model_dir = output_path / "model"
        assert model_dir.exists(), "Model directory is missing"
        assert model_dir.is_dir(), "Model path is not a directory"
        
        # Property: Model directory should contain model files
        model_files = list(model_dir.glob('*'))
        assert len(model_files) > 0, "Model directory is empty"
        
        # Property: Artifacts list should contain all required files
        assert len(result.artifacts) >= 2, "Not enough artifacts generated"
        
        # Property: All artifacts should exist
        for artifact_path in result.artifacts:
            artifact = Path(artifact_path)
            assert artifact.exists(), f"Artifact does not exist: {artifact_path}"
        
        # Property: Size should be greater than zero
        assert result.size_bytes > 0, "Export size is zero"
        
        # Property: Verification should pass
        assert result.verification_passed, f"Verification failed: {result.verification_details}"


@given(
    model_name=model_name_strategy(),
    metadata=model_metadata_strategy()
)
@settings(max_examples=50, deadline=None)
def test_ollama_modelfile_content(model_name, metadata):
    """
    For any Ollama export, the Modelfile should contain valid Ollama syntax
    and reference the model correctly.
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
            format='ollama',
            model_name=model_name,
            metadata=metadata,
            merge_adapters=False
        )
        
        assert result.success, "Export failed"
        
        # Read Modelfile
        modelfile_path = Path(result.output_path) / "Modelfile"
        modelfile_content = modelfile_path.read_text()
        
        # Property: Modelfile should contain FROM directive
        assert "FROM" in modelfile_content, "Modelfile missing FROM directive"
        
        # Property: Modelfile should reference the model directory
        assert "./model" in modelfile_content, "Modelfile does not reference model directory"
        
        # Property: Modelfile should contain PARAMETER directives
        assert "PARAMETER" in modelfile_content, "Modelfile missing PARAMETER directives"
        
        # Property: Modelfile should contain essential parameters
        essential_params = ["temperature", "top_p", "top_k"]
        for param in essential_params:
            assert param in modelfile_content, f"Modelfile missing parameter: {param}"
        
        # Property: Modelfile should contain SYSTEM directive
        assert "SYSTEM" in modelfile_content, "Modelfile missing SYSTEM directive"
        
        # Property: Modelfile should contain TEMPLATE directive
        assert "TEMPLATE" in modelfile_content, "Modelfile missing TEMPLATE directive"


@given(
    model_name=model_name_strategy(),
    metadata=model_metadata_strategy()
)
@settings(max_examples=50, deadline=None)
def test_ollama_installation_instructions_content(model_name, metadata):
    """
    For any Ollama export, the installation instructions should contain
    all necessary steps and commands.
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
            format='ollama',
            model_name=model_name,
            metadata=metadata,
            merge_adapters=False
        )
        
        assert result.success, "Export failed"
        
        # Read installation instructions
        install_path = Path(result.output_path) / "INSTALL.md"
        install_content = install_path.read_text()
        
        # Property: Instructions should mention model name
        assert model_name in install_content, "Instructions do not mention model name"
        
        # Property: Instructions should contain ollama create command
        assert "ollama create" in install_content, "Instructions missing 'ollama create' command"
        
        # Property: Instructions should contain ollama run command
        assert "ollama run" in install_content, "Instructions missing 'ollama run' command"
        
        # Property: Instructions should reference the Modelfile
        assert "Modelfile" in install_content, "Instructions do not reference Modelfile"
        
        # Property: Instructions should contain usage examples
        usage_indicators = ["Usage", "API", "CLI", "Python"]
        has_usage = any(indicator in install_content for indicator in usage_indicators)
        assert has_usage, "Instructions missing usage examples"
        
        # Property: Instructions should contain troubleshooting section
        assert "Troubleshooting" in install_content or "troubleshoot" in install_content.lower(), \
            "Instructions missing troubleshooting section"


@given(model_name=model_name_strategy())
@settings(max_examples=50, deadline=None)
def test_ollama_export_without_metadata(model_name):
    """
    For any model exported without metadata, the Ollama export should still
    succeed and generate all required artifacts with default values.
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
            format='ollama',
            model_name=model_name,
            metadata=None,  # No metadata
            merge_adapters=False
        )
        
        # Property: Export should succeed without metadata
        assert result.success, "Export failed without metadata"
        
        # Property: Modelfile should still be created
        modelfile_path = Path(result.output_path) / "Modelfile"
        assert modelfile_path.exists(), "Modelfile not created without metadata"
        
        # Property: Modelfile should contain default parameters
        modelfile_content = modelfile_path.read_text()
        assert "PARAMETER temperature" in modelfile_content, "Default temperature parameter missing"
        
        # Property: Installation instructions should still be created
        install_path = Path(result.output_path) / "INSTALL.md"
        assert install_path.exists(), "Installation instructions not created without metadata"


@given(
    model_name=model_name_strategy(),
    metadata=model_metadata_strategy()
)
@settings(max_examples=50, deadline=None)
def test_ollama_export_verification(model_name, metadata):
    """
    For any Ollama export, the verification should correctly identify
    the presence of all required components.
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
            format='ollama',
            model_name=model_name,
            metadata=metadata,
            merge_adapters=False
        )
        
        assert result.success, "Export failed"
        
        # Property: Verification details should be present
        assert result.verification_details is not None, "No verification details"
        
        # Property: Verification should report found files
        assert 'found_files' in result.verification_details, "Verification missing found_files"
        found_files = result.verification_details['found_files']
        assert len(found_files) > 0, "No files found in verification"
        
        # Property: Verification should confirm Modelfile presence
        assert 'Modelfile' in found_files, "Verification did not detect Modelfile"
        
        # Property: Verification should confirm instructions presence
        assert 'INSTALL.md' in found_files, "Verification did not detect installation instructions"
        
        # Property: Verification should confirm model directory
        assert result.verification_details.get('has_model_directory', False), \
            "Verification did not detect model directory"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
