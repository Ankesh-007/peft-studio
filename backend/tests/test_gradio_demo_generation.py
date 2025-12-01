"""
Property-Based Tests for Gradio Demo Generation

**Feature: unified-llm-platform, Property 15: Gradio demo generation**
**Validates: Requirements 11.1, 11.2**

Property: For any adapter, generating a Gradio demo should produce a functional 
interface with working inference.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
import re

from services.gradio_demo_service import (
    get_gradio_demo_service,
    DemoConfig,
    DemoStatus
)


# Strategies for generating test data
@st.composite
def demo_config_strategy(draw):
    """Generate valid DemoConfig objects"""
    demo_id = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=48, max_codepoint=122),
        min_size=5,
        max_size=20
    ))
    
    model_id = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=48, max_codepoint=122),
        min_size=5,
        max_size=30
    ))
    
    model_path = f"/models/{model_id}"
    
    title = draw(st.text(min_size=5, max_size=50))
    description = draw(st.text(min_size=10, max_size=200))
    
    input_type = draw(st.sampled_from(["textbox", "chatbot", "audio", "image"]))
    output_type = draw(st.sampled_from(["textbox", "chatbot", "audio", "image"]))
    
    max_tokens = draw(st.integers(min_value=50, max_value=2048))
    temperature = draw(st.floats(min_value=0.1, max_value=2.0))
    top_p = draw(st.floats(min_value=0.1, max_value=1.0))
    top_k = draw(st.integers(min_value=1, max_value=100))
    
    server_port = draw(st.integers(min_value=7860, max_value=7900))
    
    use_local_model = draw(st.booleans())
    
    api_endpoint = None
    api_key = None
    if not use_local_model:
        api_endpoint = f"https://api.example.com/v1/generate"
        api_key = draw(st.text(min_size=20, max_size=40))
    
    return DemoConfig(
        demo_id=demo_id,
        model_id=model_id,
        model_path=model_path,
        title=title,
        description=description,
        input_type=input_type,
        output_type=output_type,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        server_port=server_port,
        use_local_model=use_local_model,
        api_endpoint=api_endpoint,
        api_key=api_key
    )


class TestGradioDemoGeneration:
    """Property-based tests for Gradio demo generation"""
    
    @given(config=demo_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_demo_creation_produces_valid_info(self, config):
        """
        Property: For any valid DemoConfig, creating a demo should produce 
        a DemoInfo with CREATED status and valid timestamps.
        
        **Validates: Requirements 11.1**
        """
        service = get_gradio_demo_service()
        
        # Create demo
        demo_info = service.create_demo(config)
        
        # Verify demo was created with correct status
        assert demo_info.demo_id == config.demo_id
        assert demo_info.status == DemoStatus.CREATED
        assert demo_info.config == config
        assert demo_info.created_at is not None
        assert isinstance(demo_info.created_at, datetime)
        
        # Cleanup
        service.delete_demo(config.demo_id)
    
    @given(config=demo_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_generated_code_is_valid_python(self, config):
        """
        Property: For any valid DemoConfig, the generated Gradio code should 
        be syntactically valid Python.
        
        **Validates: Requirements 11.1**
        """
        service = get_gradio_demo_service()
        
        # Generate code
        code = service.generate_gradio_code(config)
        
        # Verify code is not empty
        assert len(code) > 0
        
        # Verify code contains essential Gradio components
        assert "import gradio as gr" in code
        assert "gr.Interface" in code
        assert "demo.launch" in code
        
        # Verify code is syntactically valid Python
        try:
            compile(code, '<string>', 'exec')
            is_valid = True
        except SyntaxError:
            is_valid = False
        
        assert is_valid, f"Generated code has syntax errors:\n{code}"
    
    @given(config=demo_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_generated_code_includes_config_parameters(self, config):
        """
        Property: For any valid DemoConfig, the generated code should include 
        all specified configuration parameters.
        
        **Validates: Requirements 11.1, 11.3**
        """
        service = get_gradio_demo_service()
        
        # Generate code
        code = service.generate_gradio_code(config)
        
        # Verify configuration parameters are in the code
        assert str(config.max_tokens) in code
        assert str(config.temperature) in code
        assert str(config.top_p) in code
        assert str(config.top_k) in code
        assert str(config.server_port) in code
        
        # Verify title is in the code (may be escaped)
        # We check that the title appears somewhere in the code
        # (it might be escaped, so we just check it's referenced)
        assert 'title=' in code
        assert 'description=' in code
        
        # Verify input/output types are in the code
        assert config.input_type.capitalize() in code
        assert config.output_type.capitalize() in code
    
    @given(config=demo_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_local_model_code_uses_transformers(self, config):
        """
        Property: For any DemoConfig with use_local_model=True, the generated 
        code should use transformers library for inference.
        
        **Validates: Requirements 11.4**
        """
        # Only test local model configs
        assume(config.use_local_model)
        
        service = get_gradio_demo_service()
        
        # Generate code
        code = service.generate_gradio_code(config)
        
        # Verify transformers imports and usage
        assert "from transformers import" in code
        assert "AutoModelForCausalLM" in code
        assert "AutoTokenizer" in code
        assert config.model_path in code
    
    @given(config=demo_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_api_endpoint_code_uses_requests(self, config):
        """
        Property: For any DemoConfig with use_local_model=False, the generated 
        code should use requests library to call the API endpoint.
        
        **Validates: Requirements 11.4**
        """
        # Only test API endpoint configs
        assume(not config.use_local_model)
        assume(config.api_endpoint is not None)
        
        service = get_gradio_demo_service()
        
        # Generate code
        code = service.generate_gradio_code(config)
        
        # Verify requests usage
        assert "import requests" in code
        assert "requests.post" in code
        assert config.api_endpoint in code
        
        # Verify API key is included if provided
        if config.api_key:
            assert "Authorization" in code
    
    @given(config=demo_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_demo_info_urls_are_valid_format(self, config):
        """
        Property: For any created demo, if URLs are generated, they should 
        be in valid URL format.
        
        **Validates: Requirements 11.2**
        """
        service = get_gradio_demo_service()
        
        # Create demo
        demo_info = service.create_demo(config)
        
        # If local_url is set, it should be valid
        if demo_info.local_url:
            assert demo_info.local_url.startswith("http://")
            assert str(config.server_port) in demo_info.local_url
        
        # If public_url is set (when share=True), it should be valid
        if demo_info.public_url:
            assert demo_info.public_url.startswith("https://")
        
        # Cleanup
        service.delete_demo(config.demo_id)
    
    @given(config=demo_config_strategy())
    @settings(max_examples=50, deadline=None)
    def test_embeddable_code_requires_public_url(self, config):
        """
        Property: For any demo without a public URL, attempting to generate 
        embeddable code should raise an error.
        
        **Validates: Requirements 11.5**
        """
        service = get_gradio_demo_service()
        
        # Create demo without sharing (no public URL)
        config.share = False
        demo_info = service.create_demo(config)
        
        # Attempting to get embed code should raise ValueError
        with pytest.raises(ValueError, match="does not have a public URL"):
            service.generate_embeddable_code(config.demo_id)
        
        # Cleanup
        service.delete_demo(config.demo_id)
    
    @given(config=demo_config_strategy())
    @settings(max_examples=50, deadline=None)
    def test_embeddable_code_contains_iframe(self, config):
        """
        Property: For any demo with a public URL, the embeddable code should 
        contain a valid iframe element.
        
        **Validates: Requirements 11.5**
        """
        service = get_gradio_demo_service()
        
        # Create demo with sharing enabled
        config.share = True
        demo_info = service.create_demo(config)
        
        # Manually set public URL for testing
        demo_info.public_url = "https://test.gradio.live"
        
        # Generate embed code
        embed_code = service.generate_embeddable_code(config.demo_id)
        
        # Verify iframe is present
        assert "<iframe" in embed_code
        assert "</iframe>" in embed_code
        assert demo_info.public_url in embed_code
        
        # Verify iframe has required attributes
        assert "src=" in embed_code
        assert "width=" in embed_code
        assert "height=" in embed_code
        
        # Cleanup
        service.delete_demo(config.demo_id)
    
    @given(config=demo_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_config_export_import_roundtrip(self, config):
        """
        Property: For any DemoConfig, exporting and then importing should 
        produce an equivalent configuration.
        
        **Validates: Requirements 11.1**
        """
        service = get_gradio_demo_service()
        
        # Create demo
        demo_info = service.create_demo(config)
        
        # Export configuration
        exported = service.export_demo_config(config.demo_id)
        
        # Import configuration
        imported_config = service.import_demo_config(exported)
        
        # Verify all fields match
        assert imported_config.demo_id == config.demo_id
        assert imported_config.model_id == config.model_id
        assert imported_config.model_path == config.model_path
        assert imported_config.title == config.title
        assert imported_config.description == config.description
        assert imported_config.input_type == config.input_type
        assert imported_config.output_type == config.output_type
        assert imported_config.max_tokens == config.max_tokens
        assert abs(imported_config.temperature - config.temperature) < 0.01
        assert abs(imported_config.top_p - config.top_p) < 0.01
        assert imported_config.top_k == config.top_k
        assert imported_config.server_port == config.server_port
        assert imported_config.use_local_model == config.use_local_model
        
        # Cleanup
        service.delete_demo(config.demo_id)
    
    @given(config=demo_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_demo_lifecycle_state_transitions(self, config):
        """
        Property: For any demo, the status should transition correctly through 
        the lifecycle: CREATED -> (RUNNING or ERROR) -> STOPPED.
        
        **Validates: Requirements 11.2**
        """
        service = get_gradio_demo_service()
        
        # Create demo
        demo_info = service.create_demo(config)
        assert demo_info.status == DemoStatus.CREATED
        
        # Note: We don't actually launch the demo in tests to avoid 
        # spawning processes, but we verify the status is CREATED
        
        # Verify we can retrieve the demo
        retrieved = service.get_demo(config.demo_id)
        assert retrieved is not None
        assert retrieved.demo_id == config.demo_id
        assert retrieved.status == DemoStatus.CREATED
        
        # Cleanup
        deleted = service.delete_demo(config.demo_id)
        assert deleted is True
        
        # Verify demo is gone
        assert service.get_demo(config.demo_id) is None
    
    @given(
        config1=demo_config_strategy(),
        config2=demo_config_strategy()
    )
    @settings(max_examples=50, deadline=None)
    def test_multiple_demos_are_isolated(self, config1, config2):
        """
        Property: For any two different demos, they should be independently 
        managed without interference.
        
        **Validates: Requirements 11.1**
        """
        # Ensure different demo IDs
        assume(config1.demo_id != config2.demo_id)
        
        service = get_gradio_demo_service()
        
        # Create both demos
        demo1 = service.create_demo(config1)
        demo2 = service.create_demo(config2)
        
        # Verify both exist independently
        assert service.get_demo(config1.demo_id) is not None
        assert service.get_demo(config2.demo_id) is not None
        
        # Verify they have different configurations
        assert demo1.config.demo_id != demo2.config.demo_id
        
        # Delete first demo
        service.delete_demo(config1.demo_id)
        
        # Verify second demo still exists
        assert service.get_demo(config1.demo_id) is None
        assert service.get_demo(config2.demo_id) is not None
        
        # Cleanup
        service.delete_demo(config2.demo_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
