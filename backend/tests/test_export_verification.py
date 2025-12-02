"""
Property-based tests for export verification.
**Feature: simplified-llm-optimization, Property 34: Export verification succeeds**
**Validates: Requirements 15.5**
"""

import pytest
from hypothesis import given, strategies as st, settings
from pathlib import Path
import tempfile
import json

from services.export_service import ModelExporter, ExportFormat


# Strategy for generating model names
@st.composite
def model_name_strategy(draw):
    """Generate valid model names"""
    prefix = draw(st.sampled_from(['chatbot', 'code-gen', 'summarizer', 'qa-model']))
    version = draw(st.integers(min_value=1, max_value=10))
    return f"{prefix}-v{version}"


# Strategy for export formats
export_format_strategy = st.sampled_from(['huggingface', 'ollama', 'lmstudio'])


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


# **Feature: simplified-llm-optimization, Property 34: Export verification succeeds**
@given(
    model_name=model_name_strategy(),
    export_format=export_format_strategy
)
@settings(max_examples=100, deadline=None)
def test_export_verification_succeeds(model_name, export_format):
    """
    For any exported model, the verification function should successfully
    validate the export and confirm all required components are present.
    
    This property ensures that verification correctly identifies complete exports.
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
            format=export_format,
            model_name=model_name,
            metadata={'config': {'model_name': 'test-model'}},
            merge_adapters=False
        )
        
        # Property: Export should succeed
        assert result.success, f"Export failed: {result.message}"
        
        # Property: Verification should be performed automatically
        assert result.verification_passed is not None, "Verification status not set"
        
        # Property: For successful exports, verification should pass
        assert result.verification_passed, \
            f"Verification failed for {export_format}: {result.verification_details}"
        
        # Property: Verification details should be provided
        assert result.verification_details is not None, "No verification details provided"
        assert isinstance(result.verification_details, dict), "Verification details not a dictionary"
        
        # Property: Verification should have a message
        assert 'message' in result.verification_details, "Verification missing message"
        
        # Property: Verification should report passed status
        assert result.verification_details.get('passed', False), \
            "Verification details do not indicate success"


@given(
    model_name=model_name_strategy(),
    export_format=export_format_strategy
)
@settings(max_examples=50, deadline=None)
def test_verification_can_be_run_separately(model_name, export_format):
    """
    For any exported model, the verification function should be callable
    separately and produce the same result as the automatic verification.
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
            format=export_format,
            model_name=model_name,
            metadata={'config': {'model_name': 'test-model'}},
            merge_adapters=False
        )
        
        assert result.success, "Export failed"
        
        # Property: Separate verification should be possible
        separate_verification = exporter.verify_export(
            export_path=result.output_path,
            format=export_format
        )
        
        # Property: Separate verification should return a dictionary
        assert isinstance(separate_verification, dict), "Verification did not return dictionary"
        
        # Property: Separate verification should have passed status
        assert 'passed' in separate_verification, "Verification missing 'passed' field"
        
        # Property: Separate verification should match automatic verification
        assert separate_verification['passed'] == result.verification_passed, \
            "Separate verification result differs from automatic verification"


@given(
    model_name=model_name_strategy()
)
@settings(max_examples=50, deadline=None)
def test_huggingface_verification_checks_required_files(model_name):
    """
    For any HuggingFace export, verification should check for the presence
    of model card, config, and model weights.
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
            metadata={'config': {'model_name': 'test-model'}},
            merge_adapters=False
        )
        
        assert result.success, "Export failed"
        
        # Property: Verification should check for model card
        assert 'found_files' in result.verification_details, "Verification missing found_files"
        found_files = result.verification_details['found_files']
        assert 'README.md' in found_files, "Verification did not check for README.md"
        
        # Property: Verification should check for model weights
        assert 'has_model_weights' in result.verification_details, \
            "Verification did not check for model weights"
        assert result.verification_details['has_model_weights'], \
            "Verification did not detect model weights"
        
        # Property: Verification should report missing files if any
        assert 'missing_required_files' in result.verification_details, \
            "Verification missing 'missing_required_files' field"


@given(
    model_name=model_name_strategy()
)
@settings(max_examples=50, deadline=None)
def test_ollama_verification_checks_required_artifacts(model_name):
    """
    For any Ollama export, verification should check for Modelfile,
    installation instructions, and model directory.
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
            metadata={'config': {'model_name': 'test-model'}},
            merge_adapters=False
        )
        
        assert result.success, "Export failed"
        
        # Property: Verification should check for Modelfile
        assert 'found_files' in result.verification_details, "Verification missing found_files"
        found_files = result.verification_details['found_files']
        assert 'Modelfile' in found_files, "Verification did not check for Modelfile"
        
        # Property: Verification should check for installation instructions
        assert 'INSTALL.md' in found_files, "Verification did not check for INSTALL.md"
        
        # Property: Verification should check for model directory
        assert 'has_model_directory' in result.verification_details, \
            "Verification did not check for model directory"
        assert result.verification_details['has_model_directory'], \
            "Verification did not detect model directory"


@given(
    model_name=model_name_strategy()
)
@settings(max_examples=50, deadline=None)
def test_lmstudio_verification_checks_required_components(model_name):
    """
    For any LM Studio export, verification should check for config file,
    setup instructions, and model directory.
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
            format='lmstudio',
            model_name=model_name,
            metadata={'config': {'model_name': 'test-model'}},
            merge_adapters=False
        )
        
        assert result.success, "Export failed"
        
        # Property: Verification should check for config file
        assert 'found_files' in result.verification_details, "Verification missing found_files"
        found_files = result.verification_details['found_files']
        assert 'lmstudio_config.json' in found_files, \
            "Verification did not check for lmstudio_config.json"
        
        # Property: Verification should check for setup instructions
        assert 'LMSTUDIO_SETUP.md' in found_files, \
            "Verification did not check for LMSTUDIO_SETUP.md"
        
        # Property: Verification should check for model directory
        assert 'has_model_directory' in result.verification_details, \
            "Verification did not check for model directory"
        assert result.verification_details['has_model_directory'], \
            "Verification did not detect model directory"


@given(
    model_name=model_name_strategy(),
    export_format=export_format_strategy
)
@settings(max_examples=50, deadline=None)
def test_verification_fails_for_nonexistent_path(model_name, export_format):
    """
    For any nonexistent export path, verification should fail gracefully
    and report the issue.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create exporter
        export_base = temp_path / "exports"
        exporter = ModelExporter(export_base_path=str(export_base))
        
        # Try to verify a nonexistent path
        nonexistent_path = temp_path / "nonexistent" / model_name
        
        # Property: Verification should handle nonexistent paths
        verification = exporter.verify_export(
            export_path=str(nonexistent_path),
            format=export_format
        )
        
        # Property: Verification should return a result
        assert isinstance(verification, dict), "Verification did not return dictionary"
        
        # Property: Verification should fail for nonexistent path
        assert not verification.get('passed', True), \
            "Verification passed for nonexistent path"
        
        # Property: Verification should provide an error message
        assert 'message' in verification, "Verification missing error message"
        assert len(verification['message']) > 0, "Verification error message is empty"


@given(
    model_name=model_name_strategy(),
    export_format=export_format_strategy
)
@settings(max_examples=50, deadline=None)
def test_verification_result_consistency(model_name, export_format):
    """
    For any exported model, running verification multiple times should
    produce consistent results.
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
            format=export_format,
            model_name=model_name,
            metadata={'config': {'model_name': 'test-model'}},
            merge_adapters=False
        )
        
        assert result.success, "Export failed"
        
        # Run verification multiple times
        verification1 = exporter.verify_export(result.output_path, export_format)
        verification2 = exporter.verify_export(result.output_path, export_format)
        verification3 = exporter.verify_export(result.output_path, export_format)
        
        # Property: All verifications should have the same passed status
        assert verification1['passed'] == verification2['passed'] == verification3['passed'], \
            "Verification results are inconsistent"
        
        # Property: All verifications should have the same message
        assert verification1['message'] == verification2['message'] == verification3['message'], \
            "Verification messages are inconsistent"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
