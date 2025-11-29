"""
Property-based tests for Weights & Biases integration.

Tests automatic metric logging and hyperparameter tracking.
"""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch, MagicMock
from services.wandb_integration_service import (
    WandBIntegrationService,
    WandBConfig,
    ExperimentMetadata
)


# Test data generators
@st.composite
def experiment_metadata_strategy(draw):
    """Generate random experiment metadata"""
    return ExperimentMetadata(
        job_id=draw(st.text(min_size=8, max_size=32, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        model_name=draw(st.sampled_from([
            "meta-llama/Llama-2-7b-hf",
            "mistralai/Mistral-7B-v0.1",
            "google/flan-t5-base",
            "EleutherAI/gpt-neo-2.7B"
        ])),
        dataset_name=draw(st.text(min_size=5, max_size=50)),
        use_case=draw(st.sampled_from([
            "chatbot", "code-generation", "summarization",
            "qa", "creative-writing", "domain-adaptation"
        ])),
        run_name=draw(st.one_of(st.none(), st.text(min_size=5, max_size=50)))
    )


@st.composite
def training_config_strategy(draw):
    """Generate random training configuration"""
    return {
        'model_name': draw(st.text(min_size=5, max_size=50)),
        'learning_rate': draw(st.floats(min_value=1e-6, max_value=1e-3)),
        'batch_size': draw(st.integers(min_value=1, max_value=128)),
        'num_epochs': draw(st.integers(min_value=1, max_value=100)),
        'lora_r': draw(st.integers(min_value=1, max_value=256)),
        'lora_alpha': draw(st.integers(min_value=1, max_value=512)),
        'lora_dropout': draw(st.floats(min_value=0.0, max_value=0.5))
    }


@st.composite
def metrics_strategy(draw):
    """Generate random training metrics"""
    return {
        'train/loss': draw(st.floats(min_value=0.01, max_value=10.0)),
        'train/learning_rate': draw(st.floats(min_value=1e-6, max_value=1e-3)),
        'train/grad_norm': draw(st.floats(min_value=0.0, max_value=10.0)),
        'train/epoch': draw(st.integers(min_value=0, max_value=100)),
        'performance/throughput': draw(st.floats(min_value=0.1, max_value=100.0)),
        'resources/gpu_0_utilization': draw(st.floats(min_value=0.0, max_value=100.0))
    }


class TestWandBIntegration:
    """Test suite for WandB integration service"""
    
    def test_service_initialization_disabled(self):
        """Test that service initializes correctly when disabled"""
        config = WandBConfig(enabled=False)
        service = WandBIntegrationService(config)
        
        assert not service.is_enabled()
        assert service.config.enabled == False
    
    def test_service_initialization_enabled(self):
        """Test that service initializes correctly when enabled"""
        with patch('services.wandb_integration_service.WANDB_AVAILABLE', True):
            with patch('services.wandb_integration_service.wandb', create=True):
                config = WandBConfig(
                    enabled=True,
                    project_name="test-project",
                    api_key="test-key"
                )
                service = WandBIntegrationService(config)
                
                assert service.is_enabled()
                assert service.config.project_name == "test-project"
    
    # **Feature: simplified-llm-optimization, Property: WandB automatic metric logging**
    @settings(max_examples=100)
    @given(
        metadata=experiment_metadata_strategy(),
        config=training_config_strategy(),
        metrics=metrics_strategy(),
        step=st.integers(min_value=0, max_value=10000)
    )
    def test_automatic_metric_logging(self, metadata, config, metrics, step):
        """
        For any training run with WandB enabled, all metrics should be automatically logged.
        
        Validates: Requirements 11.1, 11.2
        """
        with patch('services.wandb_integration_service.WANDB_AVAILABLE', True):
            with patch('services.wandb_integration_service.wandb', create=True) as mock_wandb:
                # Setup mock
                mock_run = MagicMock()
                mock_wandb.init.return_value = mock_run
                
                # Create service
                wandb_config = WandBConfig(enabled=True, project_name="test")
                service = WandBIntegrationService(wandb_config)
        
                # Start run
                success = service.start_run(
                    job_id=metadata.job_id,
                    metadata=metadata,
                    config=config
                )
                
                assert success, "Run should start successfully"
                
                # Log metrics
                log_success = service.log_metrics(
                    job_id=metadata.job_id,
                    metrics=metrics,
                    step=step
                )
                
                assert log_success, "Metrics should be logged successfully"
                
                # Verify wandb.init was called
                mock_wandb.init.assert_called_once()
                
                # Verify log was called with correct parameters
                mock_run.log.assert_called_once()
                call_args = mock_run.log.call_args
                
                # Check that all metrics were logged
                logged_metrics = call_args[0][0]
                for key in metrics.keys():
                    assert key in logged_metrics, f"Metric {key} should be logged"
                
                # Check step parameter
                assert call_args[1]['step'] == step, "Step should match"
    
    # **Feature: simplified-llm-optimization, Property: WandB hyperparameter tracking**
    @settings(max_examples=100)
    @given(
        metadata=experiment_metadata_strategy(),
        config=training_config_strategy()
    )
    def test_hyperparameter_tracking(self, metadata, config):
        """
        For any training run, all hyperparameters should be tracked in WandB.
        
        Validates: Requirements 11.1, 11.2
        """
        with patch('services.wandb_integration_service.WANDB_AVAILABLE', True):
            with patch('services.wandb_integration_service.wandb', create=True) as mock_wandb:
                # Setup mock
                mock_run = MagicMock()
                mock_wandb.init.return_value = mock_run
                
                # Create service
                wandb_config = WandBConfig(enabled=True, project_name="test")
                service = WandBIntegrationService(wandb_config)
                
                # Start run
                success = service.start_run(
                    job_id=metadata.job_id,
                    metadata=metadata,
                    config=config
                )
                
                assert success, "Run should start successfully"
                
                # Verify wandb.init was called with config
                mock_wandb.init.assert_called_once()
                call_kwargs = mock_wandb.init.call_args[1]
                
                # Check that config was passed
                assert 'config' in call_kwargs, "Config should be passed to wandb.init"
                
                # Check that all hyperparameters are in the config
                logged_config = call_kwargs['config']
                for key, value in config.items():
                    assert key in logged_config, f"Hyperparameter {key} should be tracked"
                    assert logged_config[key] == value, f"Hyperparameter {key} value should match"
    
    # **Feature: simplified-llm-optimization, Property: WandB run metadata completeness**
    @settings(max_examples=100)
    @given(
        metadata=experiment_metadata_strategy(),
        config=training_config_strategy()
    )
    def test_run_metadata_completeness(self, metadata, config):
        """
        For any WandB run, metadata should include job_id, model_name, dataset_name, and use_case.
        
        Validates: Requirements 11.1
        """
        with patch('services.wandb_integration_service.WANDB_AVAILABLE', True):
            with patch('services.wandb_integration_service.wandb', create=True) as mock_wandb:
                # Setup mock
                mock_run = MagicMock()
                mock_wandb.init.return_value = mock_run
                
                # Create service
                wandb_config = WandBConfig(enabled=True, project_name="test")
                service = WandBIntegrationService(wandb_config)
                
                # Start run
                success = service.start_run(
                    job_id=metadata.job_id,
                    metadata=metadata,
                    config=config
                )
                
                assert success, "Run should start successfully"
                
                # Verify summary was updated with metadata
                mock_run.summary.update.assert_called_once()
                summary_data = mock_run.summary.update.call_args[0][0]
                
                # Check all required metadata fields
                assert 'job_id' in summary_data, "job_id should be in summary"
                assert summary_data['job_id'] == metadata.job_id
                
                assert 'model_name' in summary_data, "model_name should be in summary"
                assert summary_data['model_name'] == metadata.model_name
                
                assert 'dataset_name' in summary_data, "dataset_name should be in summary"
                assert summary_data['dataset_name'] == metadata.dataset_name
                
                assert 'use_case' in summary_data, "use_case should be in summary"
                assert summary_data['use_case'] == metadata.use_case
    
    # **Feature: simplified-llm-optimization, Property: WandB comparison URL generation**
    @settings(max_examples=100)
    @given(
        job_ids=st.lists(
            st.text(min_size=8, max_size=32, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
            min_size=2,
            max_size=5,
            unique=True
        )
    )
    @patch('services.wandb_integration_service.WANDB_AVAILABLE', True)
    def test_comparison_url_generation(self, job_ids):
        """
        For any list of 2-5 job IDs, a comparison URL should be generated.
        
        Validates: Requirements 11.2
        """
        # Create service
        wandb_config = WandBConfig(
            enabled=True,
            project_name="test-project",
            entity="test-entity"
        )
        service = WandBIntegrationService(wandb_config)
        
        # Generate comparison URL
        comparison_url = service.compare_runs(job_ids)
        
        # Verify URL is generated
        assert comparison_url is not None, "Comparison URL should be generated"
        assert isinstance(comparison_url, str), "Comparison URL should be a string"
        assert len(comparison_url) > 0, "Comparison URL should not be empty"
        
        # Verify URL contains project and entity
        assert "test-entity" in comparison_url, "URL should contain entity"
        assert "test-project" in comparison_url, "URL should contain project"
    
    def test_finish_run_cleanup(self):
        """Test that finishing a run properly cleans up resources"""
        with patch('services.wandb_integration_service.WANDB_AVAILABLE', True):
            with patch('services.wandb_integration_service.wandb', create=True) as mock_wandb:
                # Setup mock
                mock_run = MagicMock()
                mock_wandb.init.return_value = mock_run
                
                # Create service
                wandb_config = WandBConfig(enabled=True, project_name="test")
                service = WandBIntegrationService(wandb_config)
                
                # Start run
                job_id = "test_job_123"
                metadata = ExperimentMetadata(
                    job_id=job_id,
                    model_name="test-model",
                    dataset_name="test-dataset",
                    use_case="chatbot"
                )
                
                service.start_run(job_id, metadata, {})
                
                # Verify run is active
                assert job_id in service.active_runs
                
                # Finish run
                summary = {'final_loss': 0.5, 'quality_score': 85.0}
                success = service.finish_run(job_id, exit_code=0, summary=summary)
                
                assert success, "Run should finish successfully"
                
                # Verify run was finished
                mock_run.finish.assert_called_once_with(exit_code=0)
                
                # Verify summary was updated
                mock_run.summary.update.assert_called()
                
                # Verify run is removed from active runs
                assert job_id not in service.active_runs
    
    def test_disabled_service_operations(self):
        """Test that operations return False when service is disabled"""
        config = WandBConfig(enabled=False)
        service = WandBIntegrationService(config)
        
        metadata = ExperimentMetadata(
            job_id="test_job",
            model_name="test-model",
            dataset_name="test-dataset",
            use_case="chatbot"
        )
        
        # All operations should return False when disabled
        assert not service.start_run("test_job", metadata, {})
        assert not service.log_metrics("test_job", {'loss': 0.5})
        assert not service.log_hyperparameters("test_job", {'lr': 0.001})
        assert not service.finish_run("test_job")
        
        # URL methods should return None
        assert service.get_run_url("test_job") is None
        assert service.compare_runs(["job1", "job2"]) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
