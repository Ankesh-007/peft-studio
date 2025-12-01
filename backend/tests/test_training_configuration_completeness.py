"""
Property-Based Tests for Training Configuration Completeness
Feature: unified-llm-platform, Property 4: Training configuration completeness
Validates: Requirements 4.1, 4.2

Property 4: Training configuration completeness
For any training configuration, all required fields should be populated 
before submission is allowed.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from backend.services.training_config_service import (
    TrainingConfiguration,
    TrainingConfigService,
    PEFTAlgorithm,
    QuantizationType,
    ComputeProvider,
    ExperimentTracker,
)


# Strategies for generating training configurations
@st.composite
def training_configuration_strategy(draw, complete=True):
    """
    Generate training configurations for property testing.
    
    Args:
        complete: If True, generate complete configurations. If False, may omit required fields.
    """
    # Provider (Requirement 4.1)
    provider = draw(st.sampled_from(list(ComputeProvider)))
    
    # Algorithm (Requirement 4.2)
    algorithm = draw(st.sampled_from(list(PEFTAlgorithm)))
    
    # Quantization (Requirement 4.3)
    quantization = draw(st.sampled_from(list(QuantizationType)))
    
    # Experiment tracker (Requirement 4.4)
    experiment_tracker = draw(st.sampled_from(list(ExperimentTracker)))
    project_name = None
    if experiment_tracker != ExperimentTracker.NONE:
        if complete:
            project_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')))
        else:
            # Sometimes omit project name to test validation
            project_name = draw(st.one_of(st.none(), st.just(""), st.text(min_size=1, max_size=50)))
    
    # Model
    if complete:
        model_name = draw(st.text(min_size=1, max_size=100))
        model_path = draw(st.text(min_size=1, max_size=200))
    else:
        model_name = draw(st.one_of(st.none(), st.just(""), st.text(min_size=1, max_size=100)))
        model_path = draw(st.one_of(st.none(), st.just(""), st.text(min_size=1, max_size=200)))
    
    # Dataset
    if complete:
        dataset_id = draw(st.text(min_size=1, max_size=100))
        dataset_path = draw(st.text(min_size=1, max_size=200))
    else:
        dataset_id = draw(st.one_of(st.none(), st.just(""), st.text(min_size=1, max_size=100)))
        dataset_path = draw(st.one_of(st.none(), st.just(""), st.text(min_size=1, max_size=200)))
    
    # PEFT Settings (Requirement 4.5)
    if complete:
        lora_r = draw(st.integers(min_value=1, max_value=256))
        lora_alpha = draw(st.integers(min_value=1, max_value=512))
        lora_dropout = draw(st.floats(min_value=0.0, max_value=0.99))
        target_modules = draw(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10))
    else:
        lora_r = draw(st.integers(min_value=-10, max_value=256))
        lora_alpha = draw(st.integers(min_value=-10, max_value=512))
        lora_dropout = draw(st.floats(min_value=-1.0, max_value=2.0))
        target_modules = draw(st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=10))
    
    # Training Hyperparameters (Requirement 4.5)
    if complete:
        learning_rate = draw(st.floats(min_value=1e-6, max_value=1e-2))
        batch_size = draw(st.integers(min_value=1, max_value=128))
        gradient_accumulation_steps = draw(st.integers(min_value=1, max_value=32))
        num_epochs = draw(st.integers(min_value=1, max_value=100))
    else:
        learning_rate = draw(st.floats(min_value=-1.0, max_value=1.0))
        batch_size = draw(st.integers(min_value=-10, max_value=128))
        gradient_accumulation_steps = draw(st.integers(min_value=-10, max_value=32))
        num_epochs = draw(st.integers(min_value=-10, max_value=100))
    
    return TrainingConfiguration(
        provider=provider,
        algorithm=algorithm,
        quantization=quantization,
        experiment_tracker=experiment_tracker,
        project_name=project_name,
        model_name=model_name or "",
        model_path=model_path or "",
        dataset_id=dataset_id or "",
        dataset_path=dataset_path or "",
        lora_r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        target_modules=target_modules,
        learning_rate=learning_rate,
        batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        num_epochs=num_epochs,
    )


class TestTrainingConfigurationCompleteness:
    """
    Property-Based Tests for Training Configuration Completeness
    **Feature: unified-llm-platform, Property 4: Training configuration completeness**
    **Validates: Requirements 4.1, 4.2**
    """
    
    @given(training_configuration_strategy(complete=True))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_complete_configuration_is_valid(self, config: TrainingConfiguration):
        """
        Property: For any complete training configuration with all required fields,
        validation should pass.
        
        This tests that when all required fields are properly populated:
        - Provider is selected (Requirement 4.1)
        - Algorithm is selected (Requirement 4.2)
        - Model and dataset are specified
        - Hyperparameters are valid (Requirement 4.5)
        - Experiment tracker configuration is complete if enabled (Requirement 4.4)
        """
        # Ensure quantization compatibility (Requirement 4.3)
        if config.quantization != QuantizationType.NONE and config.algorithm == PEFTAlgorithm.DORA:
            # Skip incompatible combinations
            assume(False)
        
        service = TrainingConfigService()
        result = service.validate_configuration(config)
        
        # A complete configuration should be valid
        assert result.is_valid, f"Complete configuration should be valid. Errors: {result.errors}"
        assert len(result.errors) == 0, f"Complete configuration should have no errors: {result.errors}"
    
    @given(st.sampled_from(list(ComputeProvider)))
    @settings(max_examples=50)
    def test_provider_selection_required(self, provider: ComputeProvider):
        """
        Property: For any training configuration, a compute provider must be selected.
        Validates: Requirement 4.1
        """
        config = TrainingConfiguration(
            provider=provider,
            algorithm=PEFTAlgorithm.LORA,
            model_name="test-model",
            model_path="/path/to/model",
            dataset_id="test-dataset",
            dataset_path="/path/to/dataset",
        )
        
        service = TrainingConfigService()
        result = service.validate_configuration(config)
        
        # Should not have provider-related errors
        provider_errors = [e for e in result.errors if "provider" in e.lower()]
        assert len(provider_errors) == 0, f"Valid provider should not cause errors: {provider_errors}"
    
    @given(st.sampled_from(list(PEFTAlgorithm)))
    @settings(max_examples=50)
    def test_algorithm_selection_required(self, algorithm: PEFTAlgorithm):
        """
        Property: For any training configuration, a PEFT algorithm must be selected.
        Validates: Requirement 4.2
        """
        config = TrainingConfiguration(
            provider=ComputeProvider.LOCAL,
            algorithm=algorithm,
            model_name="test-model",
            model_path="/path/to/model",
            dataset_id="test-dataset",
            dataset_path="/path/to/dataset",
        )
        
        service = TrainingConfigService()
        result = service.validate_configuration(config)
        
        # Should not have algorithm-related errors
        algorithm_errors = [e for e in result.errors if "algorithm" in e.lower()]
        assert len(algorithm_errors) == 0, f"Valid algorithm should not cause errors: {algorithm_errors}"
    
    @given(
        st.sampled_from([q for q in QuantizationType if q != QuantizationType.NONE]),
        st.sampled_from([a for a in PEFTAlgorithm if a != PEFTAlgorithm.DORA])
    )
    @settings(max_examples=50)
    def test_quantization_compatibility_valid(self, quantization: QuantizationType, algorithm: PEFTAlgorithm):
        """
        Property: For any non-DoRA algorithm, quantization should be compatible.
        Validates: Requirement 4.3
        """
        config = TrainingConfiguration(
            provider=ComputeProvider.LOCAL,
            algorithm=algorithm,
            quantization=quantization,
            model_name="test-model",
            model_path="/path/to/model",
            dataset_id="test-dataset",
            dataset_path="/path/to/dataset",
        )
        
        service = TrainingConfigService()
        result = service.validate_configuration(config)
        
        # Should not have quantization compatibility errors
        quant_errors = [e for e in result.errors if "quantization" in e.lower() and "compatible" in e.lower()]
        assert len(quant_errors) == 0, f"Compatible quantization should not cause errors: {quant_errors}"
    
    @given(st.sampled_from([q for q in QuantizationType if q != QuantizationType.NONE]))
    @settings(max_examples=50)
    def test_dora_quantization_incompatibility(self, quantization: QuantizationType):
        """
        Property: For any quantization type (except none), DoRA should be incompatible.
        Validates: Requirement 4.3
        """
        config = TrainingConfiguration(
            provider=ComputeProvider.LOCAL,
            algorithm=PEFTAlgorithm.DORA,
            quantization=quantization,
            model_name="test-model",
            model_path="/path/to/model",
            dataset_id="test-dataset",
            dataset_path="/path/to/dataset",
        )
        
        service = TrainingConfigService()
        result = service.validate_configuration(config)
        
        # Should have quantization compatibility error
        assert not result.is_valid, "DoRA with quantization should be invalid"
        quant_errors = [e for e in result.errors if "dora" in e.lower() and "quantization" in e.lower()]
        assert len(quant_errors) > 0, "Should have DoRA-quantization incompatibility error"
    
    @given(
        st.sampled_from([t for t in ExperimentTracker if t != ExperimentTracker.NONE]),
        st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'))
    )
    @settings(max_examples=50)
    def test_experiment_tracker_with_project_name(self, tracker: ExperimentTracker, project_name: str):
        """
        Property: For any experiment tracker (except none), a project name should be required.
        Validates: Requirement 4.4
        """
        config = TrainingConfiguration(
            provider=ComputeProvider.LOCAL,
            algorithm=PEFTAlgorithm.LORA,
            experiment_tracker=tracker,
            project_name=project_name,
            model_name="test-model",
            model_path="/path/to/model",
            dataset_id="test-dataset",
            dataset_path="/path/to/dataset",
        )
        
        service = TrainingConfigService()
        result = service.validate_configuration(config)
        
        # Should not have project name errors
        project_errors = [e for e in result.errors if "project" in e.lower()]
        assert len(project_errors) == 0, f"Valid project name should not cause errors: {project_errors}"
    
    @given(st.sampled_from([t for t in ExperimentTracker if t != ExperimentTracker.NONE]))
    @settings(max_examples=50)
    def test_experiment_tracker_requires_project_name(self, tracker: ExperimentTracker):
        """
        Property: For any experiment tracker (except none), missing project name should cause error.
        Validates: Requirement 4.4
        """
        config = TrainingConfiguration(
            provider=ComputeProvider.LOCAL,
            algorithm=PEFTAlgorithm.LORA,
            experiment_tracker=tracker,
            project_name=None,  # Missing project name
            model_name="test-model",
            model_path="/path/to/model",
            dataset_id="test-dataset",
            dataset_path="/path/to/dataset",
        )
        
        service = TrainingConfigService()
        result = service.validate_configuration(config)
        
        # Should have project name error
        assert not result.is_valid, "Tracker without project name should be invalid"
        project_errors = [e for e in result.errors if "project" in e.lower()]
        assert len(project_errors) > 0, "Should have project name error"
    
    @given(
        st.floats(min_value=1e-6, max_value=1e-2),
        st.integers(min_value=1, max_value=128),
        st.integers(min_value=1, max_value=32),
        st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100)
    def test_valid_hyperparameters(self, learning_rate: float, batch_size: int, grad_accum: int, epochs: int):
        """
        Property: For any valid hyperparameters, configuration should pass validation.
        Validates: Requirement 4.5
        """
        config = TrainingConfiguration(
            provider=ComputeProvider.LOCAL,
            algorithm=PEFTAlgorithm.LORA,
            model_name="test-model",
            model_path="/path/to/model",
            dataset_id="test-dataset",
            dataset_path="/path/to/dataset",
            learning_rate=learning_rate,
            batch_size=batch_size,
            gradient_accumulation_steps=grad_accum,
            num_epochs=epochs,
        )
        
        service = TrainingConfigService()
        result = service.validate_configuration(config)
        
        # Should not have hyperparameter errors
        hyperparam_errors = [e for e in result.errors if any(term in e.lower() for term in ["learning", "batch", "gradient", "epoch"])]
        assert len(hyperparam_errors) == 0, f"Valid hyperparameters should not cause errors: {hyperparam_errors}"
    
    @given(training_configuration_strategy(complete=False))
    @settings(max_examples=100)
    def test_incomplete_configuration_detected(self, config: TrainingConfiguration):
        """
        Property: For any incomplete training configuration, validation should detect issues.
        
        This tests that validation properly catches:
        - Missing required fields
        - Invalid hyperparameters
        - Incompatible combinations
        """
        service = TrainingConfigService()
        result = service.validate_configuration(config)
        
        # Check if configuration is actually incomplete
        is_incomplete = (
            not config.model_name or
            not config.model_path or
            not config.dataset_id or
            not config.dataset_path or
            config.learning_rate <= 0 or
            config.batch_size <= 0 or
            config.gradient_accumulation_steps <= 0 or
            (config.num_epochs <= 0 and config.max_steps <= 0) or
            config.lora_r <= 0 or
            config.lora_alpha <= 0 or
            not (0 <= config.lora_dropout < 1) or
            len(config.target_modules) == 0 or
            (config.experiment_tracker != ExperimentTracker.NONE and not config.project_name) or
            (config.quantization != QuantizationType.NONE and config.algorithm == PEFTAlgorithm.DORA)
        )
        
        if is_incomplete:
            # Incomplete configuration should be invalid
            assert not result.is_valid, "Incomplete configuration should be invalid"
            assert len(result.errors) > 0, "Incomplete configuration should have errors"
        else:
            # If all checks pass, it's actually complete
            assert result.is_valid, f"Complete configuration should be valid. Errors: {result.errors}"
    
    @given(training_configuration_strategy(complete=True))
    @settings(max_examples=100)
    def test_is_configuration_complete_method(self, config: TrainingConfiguration):
        """
        Property: For any complete configuration, is_configuration_complete should return True.
        """
        # Ensure quantization compatibility
        if config.quantization != QuantizationType.NONE and config.algorithm == PEFTAlgorithm.DORA:
            assume(False)
        
        service = TrainingConfigService()
        is_complete = service.is_configuration_complete(config)
        
        assert is_complete, "Complete configuration should return True from is_configuration_complete"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
