"""
Property-Based Tests for Configuration Preset Round-Trip

**Feature: simplified-llm-optimization, Property 16: Configuration save/load round-trip**
**Validates: Requirements 8.2, 8.4, 8.5**

Tests that saving a configuration as a preset and then loading that preset
restores all hyperparameters, dataset references, and model selections identically.
"""

import pytest
from hypothesis import given, strategies as st, settings
from services.preset_service import PresetService, ConfigurationPreset
import tempfile
import shutil
from pathlib import Path


# Strategy for generating valid configuration presets
@st.composite
def configuration_preset_strategy(draw):
    """Generate random but valid configuration presets"""
    
    # Generate valid PEFT methods, optimizers, schedulers, etc.
    peft_methods = ['lora', 'qlora', 'prefix-tuning']
    optimizers = ['adamw', 'sgd']
    schedulers = ['linear', 'cosine', 'constant']
    precisions = ['fp32', 'fp16', 'bf16']
    quantizations = [None, '8bit', '4bit']
    eval_strategies = ['steps', 'epoch']
    
    # Generate target modules (common transformer module names)
    possible_modules = ['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj']
    target_modules = draw(st.lists(
        st.sampled_from(possible_modules),
        min_size=1,
        max_size=4,
        unique=True
    ))
    
    # Generate tags
    possible_tags = ['chatbot', 'code', 'summarization', 'qa', 'creative', 'domain-specific']
    tags = draw(st.lists(
        st.sampled_from(possible_tags),
        min_size=0,
        max_size=3,
        unique=True
    ))
    
    preset = ConfigurationPreset(
        id=draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=5, max_size=20)),
        name=draw(st.text(min_size=1, max_size=50)),
        description=draw(st.text(min_size=0, max_size=200)),
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
        tags=tags,
        
        # Model configuration
        model_name=draw(st.text(min_size=1, max_size=100)),
        model_path=draw(st.text(min_size=0, max_size=200)),
        
        # Dataset configuration
        dataset_id=draw(st.text(min_size=0, max_size=50)),
        dataset_path=draw(st.text(min_size=0, max_size=200)),
        
        # PEFT Settings
        peft_method=draw(st.sampled_from(peft_methods)),
        lora_r=draw(st.integers(min_value=1, max_value=256)),
        lora_alpha=draw(st.integers(min_value=1, max_value=512)),
        lora_dropout=draw(st.floats(min_value=0.0, max_value=0.5)),
        target_modules=target_modules,
        
        # Training Hyperparameters
        learning_rate=draw(st.floats(min_value=1e-6, max_value=1e-3)),
        batch_size=draw(st.integers(min_value=1, max_value=128)),
        gradient_accumulation=draw(st.integers(min_value=1, max_value=32)),
        epochs=draw(st.integers(min_value=1, max_value=100)),
        max_steps=draw(st.integers(min_value=0, max_value=100000)),
        warmup_steps=draw(st.integers(min_value=0, max_value=10000)),
        
        # Optimization
        optimizer=draw(st.sampled_from(optimizers)),
        scheduler=draw(st.sampled_from(schedulers)),
        weight_decay=draw(st.floats(min_value=0.0, max_value=0.1)),
        max_grad_norm=draw(st.floats(min_value=0.1, max_value=10.0)),
        
        # Precision
        precision=draw(st.sampled_from(precisions)),
        quantization=draw(st.sampled_from(quantizations)),
        
        # Checkpointing
        save_steps=draw(st.integers(min_value=10, max_value=10000)),
        save_total=draw(st.integers(min_value=1, max_value=10)),
        
        # Validation
        eval_steps=draw(st.integers(min_value=10, max_value=10000)),
        eval_strategy=draw(st.sampled_from(eval_strategies))
    )
    
    return preset


class TestPresetRoundTrip:
    """Test configuration preset save/load round-trip"""
    
    @given(preset=configuration_preset_strategy())
    @settings(max_examples=100, deadline=None)
    def test_save_load_roundtrip_preserves_all_fields(self, preset):
        """
        **Feature: simplified-llm-optimization, Property 16: Configuration save/load round-trip**
        
        For any training configuration, saving it as a preset and then loading that preset
        should restore all hyperparameters, dataset references, and model selections identically.
        
        **Validates: Requirements 8.2, 8.4, 8.5**
        """
        # Create temporary service
        temp_dir = tempfile.mkdtemp()
        try:
            temp_preset_service = PresetService(presets_dir=temp_dir)
            
            # Save the preset
            saved_preset = temp_preset_service.save_preset(preset)
            
            # Load the preset
            loaded_preset = temp_preset_service.load_preset(preset.id)
            
            # Verify preset was loaded
            assert loaded_preset is not None, "Preset should be loaded successfully"
            
            # Verify all fields are preserved (excluding timestamps which may be updated)
            assert loaded_preset.id == preset.id
            assert loaded_preset.name == preset.name
            assert loaded_preset.description == preset.description
            assert loaded_preset.tags == preset.tags
            
            # Model configuration
            assert loaded_preset.model_name == preset.model_name
            assert loaded_preset.model_path == preset.model_path
            
            # Dataset configuration
            assert loaded_preset.dataset_id == preset.dataset_id
            assert loaded_preset.dataset_path == preset.dataset_path
            
            # PEFT Settings
            assert loaded_preset.peft_method == preset.peft_method
            assert loaded_preset.lora_r == preset.lora_r
            assert loaded_preset.lora_alpha == preset.lora_alpha
            assert abs(loaded_preset.lora_dropout - preset.lora_dropout) < 1e-6
            assert loaded_preset.target_modules == preset.target_modules
            
            # Training Hyperparameters
            assert abs(loaded_preset.learning_rate - preset.learning_rate) < 1e-9
            assert loaded_preset.batch_size == preset.batch_size
            assert loaded_preset.gradient_accumulation == preset.gradient_accumulation
            assert loaded_preset.epochs == preset.epochs
            assert loaded_preset.max_steps == preset.max_steps
            assert loaded_preset.warmup_steps == preset.warmup_steps
            
            # Optimization
            assert loaded_preset.optimizer == preset.optimizer
            assert loaded_preset.scheduler == preset.scheduler
            assert abs(loaded_preset.weight_decay - preset.weight_decay) < 1e-6
            assert abs(loaded_preset.max_grad_norm - preset.max_grad_norm) < 1e-6
            
            # Precision
            assert loaded_preset.precision == preset.precision
            assert loaded_preset.quantization == preset.quantization
            
            # Checkpointing
            assert loaded_preset.save_steps == preset.save_steps
            assert loaded_preset.save_total == preset.save_total
            
            # Validation
            assert loaded_preset.eval_steps == preset.eval_steps
            assert loaded_preset.eval_strategy == preset.eval_strategy
        finally:
            # Cleanup
            shutil.rmtree(temp_dir)
    
    @given(preset=configuration_preset_strategy())
    @settings(max_examples=100, deadline=None)
    def test_export_import_roundtrip_preserves_all_fields(self, preset):
        """
        **Feature: simplified-llm-optimization, Property 16: Configuration save/load round-trip**
        
        For any training configuration, exporting it and then importing should restore
        all hyperparameters, dataset references, and model selections identically.
        
        **Validates: Requirements 8.3, 8.4, 8.5**
        """
        # Create temporary service
        temp_dir = tempfile.mkdtemp()
        try:
            temp_preset_service = PresetService(presets_dir=temp_dir)
            
            # Save the original preset
            temp_preset_service.save_preset(preset)
            
            # Export the preset
            export_data = temp_preset_service.export_preset(preset.id)
            
            # Verify export data structure
            assert export_data is not None
            assert "format_version" in export_data
            assert "export_date" in export_data
            assert "preset" in export_data
            
            # Import with a new ID
            new_id = f"{preset.id}_imported"
            imported_preset = temp_preset_service.import_preset(export_data, new_id=new_id)
            
            # Verify the imported preset has the new ID
            assert imported_preset.id == new_id
            
            # Verify all other fields match the original (excluding id and timestamps)
            assert imported_preset.name == preset.name
            assert imported_preset.description == preset.description
            assert imported_preset.tags == preset.tags
            
            # Model configuration
            assert imported_preset.model_name == preset.model_name
            assert imported_preset.model_path == preset.model_path
            
            # Dataset configuration
            assert imported_preset.dataset_id == preset.dataset_id
            assert imported_preset.dataset_path == preset.dataset_path
            
            # PEFT Settings
            assert imported_preset.peft_method == preset.peft_method
            assert imported_preset.lora_r == preset.lora_r
            assert imported_preset.lora_alpha == preset.lora_alpha
            assert abs(imported_preset.lora_dropout - preset.lora_dropout) < 1e-6
            assert imported_preset.target_modules == preset.target_modules
            
            # Training Hyperparameters
            assert abs(imported_preset.learning_rate - preset.learning_rate) < 1e-9
            assert imported_preset.batch_size == preset.batch_size
            assert imported_preset.gradient_accumulation == preset.gradient_accumulation
            assert imported_preset.epochs == preset.epochs
            assert imported_preset.max_steps == preset.max_steps
            assert imported_preset.warmup_steps == preset.warmup_steps
            
            # Optimization
            assert imported_preset.optimizer == preset.optimizer
            assert imported_preset.scheduler == preset.scheduler
            assert abs(imported_preset.weight_decay - preset.weight_decay) < 1e-6
            assert abs(imported_preset.max_grad_norm - preset.max_grad_norm) < 1e-6
            
            # Precision
            assert imported_preset.precision == preset.precision
            assert imported_preset.quantization == preset.quantization
            
            # Checkpointing
            assert imported_preset.save_steps == preset.save_steps
            assert imported_preset.save_total == preset.save_total
            
            # Validation
            assert imported_preset.eval_steps == preset.eval_steps
            assert imported_preset.eval_strategy == preset.eval_strategy
        finally:
            # Cleanup
            shutil.rmtree(temp_dir)
    
    @given(preset=configuration_preset_strategy())
    @settings(max_examples=100, deadline=None)
    def test_update_preserves_unchanged_fields(self, preset):
        """
        Test that updating a preset only changes specified fields and preserves others.
        
        **Validates: Requirements 8.2**
        """
        # Create temporary service
        temp_dir = tempfile.mkdtemp()
        try:
            temp_preset_service = PresetService(presets_dir=temp_dir)
            
            # Save the original preset
            temp_preset_service.save_preset(preset)
            
            # Update only the name and description
            updates = {
                "name": "Updated Name",
                "description": "Updated Description"
            }
            
            updated_preset = temp_preset_service.update_preset(preset.id, updates)
            
            # Verify updates were applied
            assert updated_preset is not None
            assert updated_preset.name == "Updated Name"
            assert updated_preset.description == "Updated Description"
            
            # Verify all other fields remain unchanged
            assert updated_preset.id == preset.id
            assert updated_preset.tags == preset.tags
            assert updated_preset.model_name == preset.model_name
            assert updated_preset.lora_r == preset.lora_r
            assert updated_preset.learning_rate == preset.learning_rate
            assert updated_preset.batch_size == preset.batch_size
            # ... all other fields should be preserved
        finally:
            # Cleanup
            shutil.rmtree(temp_dir)
