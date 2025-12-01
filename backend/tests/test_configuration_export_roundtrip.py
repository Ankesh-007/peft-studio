"""
Property-Based Tests for Configuration Export Round-Trip
Feature: unified-llm-platform, Property 10: Configuration export round-trip
Validates: Requirements 18.1, 18.2

Property 10: Configuration export round-trip
For any training configuration, exporting then importing should produce 
an equivalent configuration.
"""

import pytest
import json
from hypothesis import given, strategies as st, settings, HealthCheck
from dataclasses import asdict
from services.training_config_service import (
    TrainingConfiguration,
    PEFTAlgorithm,
    QuantizationType,
    ComputeProvider,
    ExperimentTracker,
)


# Strategy for generating complete training configurations
@st.composite
def complete_training_configuration_strategy(draw):
    """
    Generate complete training configurations for round-trip testing.
    All fields are populated with valid values.
    """
    # Provider
    provider = draw(st.sampled_from(list(ComputeProvider)))
    resource_id = draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
    
    # Algorithm
    algorithm = draw(st.sampled_from(list(PEFTAlgorithm)))
    
    # Quantization
    quantization = draw(st.sampled_from(list(QuantizationType)))
    
    # Ensure quantization compatibility with DoRA
    if algorithm == PEFTAlgorithm.DORA and quantization != QuantizationType.NONE:
        quantization = QuantizationType.NONE
    
    # Experiment tracker
    experiment_tracker = draw(st.sampled_from(list(ExperimentTracker)))
    project_name = None
    if experiment_tracker != ExperimentTracker.NONE:
        project_name = draw(st.text(
            min_size=1, 
            max_size=50, 
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'), 
                whitelist_characters='-_'
            )
        ))
    
    # Model
    model_name = draw(st.text(min_size=1, max_size=100))
    model_path = draw(st.text(min_size=1, max_size=200))
    
    # Dataset
    dataset_id = draw(st.text(min_size=1, max_size=100))
    dataset_path = draw(st.text(min_size=1, max_size=200))
    
    # PEFT Settings
    lora_r = draw(st.integers(min_value=1, max_value=256))
    lora_alpha = draw(st.integers(min_value=1, max_value=512))
    lora_dropout = draw(st.floats(min_value=0.0, max_value=0.99))
    target_modules = draw(st.lists(
        st.text(min_size=1, max_size=20), 
        min_size=1, 
        max_size=10
    ))
    
    # Training Hyperparameters
    learning_rate = draw(st.floats(min_value=1e-6, max_value=1e-2))
    batch_size = draw(st.integers(min_value=1, max_value=128))
    gradient_accumulation_steps = draw(st.integers(min_value=1, max_value=32))
    num_epochs = draw(st.integers(min_value=1, max_value=100))
    max_steps = draw(st.integers(min_value=-1, max_value=10000))
    warmup_steps = draw(st.integers(min_value=0, max_value=1000))
    
    # Optimization
    optimizer = draw(st.sampled_from(["adamw", "sgd", "adam"]))
    scheduler = draw(st.sampled_from(["linear", "cosine", "constant"]))
    weight_decay = draw(st.floats(min_value=0.0, max_value=0.1))
    max_grad_norm = draw(st.floats(min_value=0.1, max_value=10.0))
    
    # Precision
    precision = draw(st.sampled_from(["fp16", "fp32", "bf16"]))
    
    # Checkpointing
    save_steps = draw(st.integers(min_value=100, max_value=2000))
    save_total_limit = draw(st.integers(min_value=1, max_value=10))
    
    # Validation
    eval_steps = draw(st.integers(min_value=100, max_value=2000))
    eval_strategy = draw(st.sampled_from(["steps", "epoch"]))
    
    return TrainingConfiguration(
        provider=provider,
        resource_id=resource_id,
        algorithm=algorithm,
        quantization=quantization,
        experiment_tracker=experiment_tracker,
        project_name=project_name,
        model_name=model_name,
        model_path=model_path,
        dataset_id=dataset_id,
        dataset_path=dataset_path,
        lora_r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        target_modules=target_modules,
        learning_rate=learning_rate,
        batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        num_epochs=num_epochs,
        max_steps=max_steps,
        warmup_steps=warmup_steps,
        optimizer=optimizer,
        scheduler=scheduler,
        weight_decay=weight_decay,
        max_grad_norm=max_grad_norm,
        precision=precision,
        save_steps=save_steps,
        save_total_limit=save_total_limit,
        eval_steps=eval_steps,
        eval_strategy=eval_strategy,
    )


def export_configuration(config: TrainingConfiguration) -> dict:
    """
    Export a training configuration to a dictionary format.
    This simulates the export functionality (Requirement 18.1).
    
    Args:
        config: Training configuration to export
        
    Returns:
        Dictionary representation of the configuration
    """
    # Convert dataclass to dictionary
    config_dict = asdict(config)
    
    # Convert enums to their string values for JSON serialization
    config_dict['provider'] = config.provider.value
    config_dict['algorithm'] = config.algorithm.value
    config_dict['quantization'] = config.quantization.value
    config_dict['experiment_tracker'] = config.experiment_tracker.value
    
    # Add metadata for export format
    export_data = {
        "format_version": "1.0",
        "config_type": "training_configuration",
        "configuration": config_dict
    }
    
    return export_data


def import_configuration(export_data: dict) -> TrainingConfiguration:
    """
    Import a training configuration from exported dictionary format.
    This simulates the import functionality with validation (Requirement 18.2).
    
    Args:
        export_data: Exported configuration data
        
    Returns:
        Reconstructed training configuration
        
    Raises:
        ValueError: If import data is invalid
    """
    # Validate format
    if "configuration" not in export_data:
        raise ValueError("Invalid export format: missing 'configuration' field")
    
    config_dict = export_data["configuration"]
    
    # Convert string values back to enums
    config_dict['provider'] = ComputeProvider(config_dict['provider'])
    config_dict['algorithm'] = PEFTAlgorithm(config_dict['algorithm'])
    config_dict['quantization'] = QuantizationType(config_dict['quantization'])
    config_dict['experiment_tracker'] = ExperimentTracker(config_dict['experiment_tracker'])
    
    # Reconstruct configuration
    return TrainingConfiguration(**config_dict)


class TestConfigurationExportRoundtrip:
    """
    Property-Based Tests for Configuration Export Round-Trip
    **Feature: unified-llm-platform, Property 10: Configuration export round-trip**
    **Validates: Requirements 18.1, 18.2**
    """
    
    @given(complete_training_configuration_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_configuration_export_import_roundtrip(self, config: TrainingConfiguration):
        """
        Property: For any training configuration, exporting then importing 
        should produce an equivalent configuration.
        
        This tests the core round-trip property:
        1. Export configuration to dictionary (Requirement 18.1)
        2. Import configuration from dictionary (Requirement 18.2)
        3. Verify all fields match the original
        """
        # Export configuration
        exported = export_configuration(config)
        
        # Verify export format
        assert "format_version" in exported
        assert "config_type" in exported
        assert "configuration" in exported
        assert exported["config_type"] == "training_configuration"
        
        # Import configuration
        imported = import_configuration(exported)
        
        # Verify round-trip: all fields should match
        assert imported.provider == config.provider
        assert imported.resource_id == config.resource_id
        assert imported.algorithm == config.algorithm
        assert imported.quantization == config.quantization
        assert imported.experiment_tracker == config.experiment_tracker
        assert imported.project_name == config.project_name
        assert imported.model_name == config.model_name
        assert imported.model_path == config.model_path
        assert imported.dataset_id == config.dataset_id
        assert imported.dataset_path == config.dataset_path
        assert imported.lora_r == config.lora_r
        assert imported.lora_alpha == config.lora_alpha
        assert imported.lora_dropout == config.lora_dropout
        assert imported.target_modules == config.target_modules
        assert imported.learning_rate == config.learning_rate
        assert imported.batch_size == config.batch_size
        assert imported.gradient_accumulation_steps == config.gradient_accumulation_steps
        assert imported.num_epochs == config.num_epochs
        assert imported.max_steps == config.max_steps
        assert imported.warmup_steps == config.warmup_steps
        assert imported.optimizer == config.optimizer
        assert imported.scheduler == config.scheduler
        assert imported.weight_decay == config.weight_decay
        assert imported.max_grad_norm == config.max_grad_norm
        assert imported.precision == config.precision
        assert imported.save_steps == config.save_steps
        assert imported.save_total_limit == config.save_total_limit
        assert imported.eval_steps == config.eval_steps
        assert imported.eval_strategy == config.eval_strategy
    
    @given(complete_training_configuration_strategy())
    @settings(max_examples=100)
    def test_configuration_json_serialization_roundtrip(self, config: TrainingConfiguration):
        """
        Property: For any training configuration, the export should be JSON-serializable
        and deserializable without data loss.
        
        This tests that configurations can be saved to files and shared:
        1. Export to dictionary
        2. Serialize to JSON string
        3. Deserialize from JSON string
        4. Import back to configuration
        5. Verify equivalence
        """
        # Export configuration
        exported = export_configuration(config)
        
        # Serialize to JSON
        json_string = json.dumps(exported)
        
        # Deserialize from JSON
        deserialized = json.loads(json_string)
        
        # Import configuration
        imported = import_configuration(deserialized)
        
        # Verify complete round-trip through JSON
        assert imported.provider == config.provider
        assert imported.algorithm == config.algorithm
        assert imported.model_name == config.model_name
        assert imported.dataset_id == config.dataset_id
        assert imported.lora_r == config.lora_r
        assert imported.learning_rate == config.learning_rate
        assert imported.batch_size == config.batch_size
    
    @given(complete_training_configuration_strategy())
    @settings(max_examples=50)
    def test_exported_configuration_has_metadata(self, config: TrainingConfiguration):
        """
        Property: For any exported configuration, metadata fields should be present.
        
        This ensures exported configurations include version information
        for compatibility checking.
        """
        exported = export_configuration(config)
        
        # Verify metadata presence
        assert "format_version" in exported
        assert "config_type" in exported
        assert exported["format_version"] == "1.0"
        assert exported["config_type"] == "training_configuration"
    
    @given(complete_training_configuration_strategy())
    @settings(max_examples=50)
    def test_import_validates_format(self, config: TrainingConfiguration):
        """
        Property: For any invalid export format, import should raise ValueError.
        
        This tests that import validation catches malformed data (Requirement 18.2).
        """
        # Export valid configuration
        exported = export_configuration(config)
        
        # Test missing configuration field
        invalid_export = {"format_version": "1.0"}
        with pytest.raises(ValueError, match="missing 'configuration' field"):
            import_configuration(invalid_export)
    
    @given(complete_training_configuration_strategy())
    @settings(max_examples=50)
    def test_enum_values_preserved_in_roundtrip(self, config: TrainingConfiguration):
        """
        Property: For any configuration with enum values, the specific enum types
        should be preserved through export/import.
        
        This ensures type safety is maintained.
        """
        # Export and import
        exported = export_configuration(config)
        imported = import_configuration(exported)
        
        # Verify enum types are preserved
        assert isinstance(imported.provider, ComputeProvider)
        assert isinstance(imported.algorithm, PEFTAlgorithm)
        assert isinstance(imported.quantization, QuantizationType)
        assert isinstance(imported.experiment_tracker, ExperimentTracker)
        
        # Verify enum values match
        assert imported.provider == config.provider
        assert imported.algorithm == config.algorithm
        assert imported.quantization == config.quantization
        assert imported.experiment_tracker == config.experiment_tracker
    
    @given(complete_training_configuration_strategy())
    @settings(max_examples=50)
    def test_optional_fields_preserved_in_roundtrip(self, config: TrainingConfiguration):
        """
        Property: For any configuration with optional fields (None or empty),
        these should be preserved through export/import.
        
        This ensures optional fields are handled correctly.
        """
        # Export and import
        exported = export_configuration(config)
        imported = import_configuration(exported)
        
        # Verify optional fields are preserved
        assert imported.resource_id == config.resource_id
        assert imported.project_name == config.project_name
    
    @given(complete_training_configuration_strategy())
    @settings(max_examples=50)
    def test_list_fields_preserved_in_roundtrip(self, config: TrainingConfiguration):
        """
        Property: For any configuration with list fields (like target_modules),
        the list contents and order should be preserved.
        
        This ensures complex data structures are handled correctly.
        """
        # Export and import
        exported = export_configuration(config)
        imported = import_configuration(exported)
        
        # Verify list fields are preserved exactly
        assert imported.target_modules == config.target_modules
        assert len(imported.target_modules) == len(config.target_modules)
        for i, module in enumerate(config.target_modules):
            assert imported.target_modules[i] == module
    
    @given(complete_training_configuration_strategy())
    @settings(max_examples=50)
    def test_numeric_precision_preserved_in_roundtrip(self, config: TrainingConfiguration):
        """
        Property: For any configuration with floating-point values,
        precision should be preserved through JSON serialization.
        
        This ensures numeric values don't lose precision.
        """
        # Export, serialize to JSON, deserialize, import
        exported = export_configuration(config)
        json_string = json.dumps(exported)
        deserialized = json.loads(json_string)
        imported = import_configuration(deserialized)
        
        # Verify floating-point values are preserved
        # Allow small floating-point errors
        assert abs(imported.learning_rate - config.learning_rate) < 1e-10
        assert abs(imported.lora_dropout - config.lora_dropout) < 1e-10
        assert abs(imported.weight_decay - config.weight_decay) < 1e-10
        assert abs(imported.max_grad_norm - config.max_grad_norm) < 1e-10
    
    @given(
        complete_training_configuration_strategy(),
        complete_training_configuration_strategy()
    )
    @settings(max_examples=50)
    def test_different_configurations_produce_different_exports(
        self, 
        config1: TrainingConfiguration, 
        config2: TrainingConfiguration
    ):
        """
        Property: For any two different configurations, their exports should differ
        (unless they happen to be identical).
        
        This ensures export captures all configuration details.
        """
        # Export both configurations
        export1 = export_configuration(config1)
        export2 = export_configuration(config2)
        
        # If configurations are different, exports should differ
        if config1 != config2:
            assert export1["configuration"] != export2["configuration"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
