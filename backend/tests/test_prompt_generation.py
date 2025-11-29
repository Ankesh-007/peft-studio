"""
Property-based tests for inference prompt generation.
Tests that example prompts are generated for all use cases.
"""

import pytest
from hypothesis import given, strategies as st

from backend.services.inference_service import InferenceService
from backend.services.profile_service import UseCase


# **Feature: simplified-llm-optimization, Property 14: Use case generates relevant prompts**
@given(st.sampled_from(list(UseCase)))
def test_use_case_generates_relevant_prompts(use_case: UseCase):
    """
    For any training use case, the inference playground should generate
    at least 3 example prompts relevant to that use case.
    
    Validates: Requirements 7.2
    """
    service = InferenceService()
    
    # Generate prompts for the use case
    prompts = service.generate_example_prompts(use_case)
    
    # Property 1: Should return a list
    assert isinstance(prompts, list), f"Expected list, got {type(prompts)}"
    
    # Property 2: Should have at least 3 prompts
    assert len(prompts) >= 3, f"Expected at least 3 prompts, got {len(prompts)}"
    
    # Property 3: All prompts should be non-empty strings
    for i, prompt in enumerate(prompts):
        assert isinstance(prompt, str), f"Prompt {i} is not a string: {type(prompt)}"
        assert len(prompt) > 0, f"Prompt {i} is empty"
        assert len(prompt.strip()) > 0, f"Prompt {i} is only whitespace"
    
    # Property 4: Prompts should be unique (no duplicates)
    assert len(prompts) == len(set(prompts)), "Prompts contain duplicates"
    
    # Property 5: Prompts should be relevant to the use case
    # We verify this by checking that prompts are contextually appropriate
    # For example, code generation prompts should mention programming concepts
    if use_case == UseCase.CODE_GENERATION:
        # At least one prompt should mention code-related terms
        code_terms = ['function', 'code', 'program', 'algorithm', 'class', 'method', 
                      'API', 'component', 'query', 'script', 'implement', 'write']
        has_code_term = any(
            any(term.lower() in prompt.lower() for term in code_terms)
            for prompt in prompts
        )
        assert has_code_term, "Code generation prompts should mention programming concepts"
    
    elif use_case == UseCase.CHATBOT:
        # Chatbot prompts should be conversational
        conversational_indicators = ['?', 'hello', 'hi', 'help', 'can you', 'tell me', 
                                     'what', 'how', 'why', 'please']
        has_conversational = any(
            any(indicator.lower() in prompt.lower() for indicator in conversational_indicators)
            for prompt in prompts
        )
        assert has_conversational, "Chatbot prompts should be conversational"
    
    elif use_case == UseCase.SUMMARIZATION:
        # Summarization prompts should mention summarization concepts
        summary_terms = ['summarize', 'summary', 'brief', 'overview', 'condense', 
                        'key points', 'main ideas', 'extract']
        has_summary_term = any(
            any(term.lower() in prompt.lower() for term in summary_terms)
            for prompt in prompts
        )
        assert has_summary_term, "Summarization prompts should mention summarization concepts"
    
    elif use_case == UseCase.QA:
        # Q&A prompts should be questions
        question_indicators = ['?', 'what', 'how', 'why', 'who', 'when', 'where', 'explain']
        has_question = any(
            any(indicator.lower() in prompt.lower() for indicator in question_indicators)
            for prompt in prompts
        )
        assert has_question, "Q&A prompts should be questions"
    
    elif use_case == UseCase.CREATIVE_WRITING:
        # Creative writing prompts should mention creative tasks
        creative_terms = ['write', 'create', 'story', 'poem', 'compose', 'generate', 
                         'creative', 'novel', 'haiku']
        has_creative_term = any(
            any(term.lower() in prompt.lower() for term in creative_terms)
            for prompt in prompts
        )
        assert has_creative_term, "Creative writing prompts should mention creative tasks"
    
    elif use_case == UseCase.DOMAIN_ADAPTATION:
        # Domain adaptation prompts should mention domain-specific concepts
        domain_terms = ['domain', 'specialized', 'technical', 'industry', 'expertise', 
                       'specific', 'terminology']
        has_domain_term = any(
            any(term.lower() in prompt.lower() for term in domain_terms)
            for prompt in prompts
        )
        assert has_domain_term, "Domain adaptation prompts should mention domain concepts"


def test_prompt_generation_consistency():
    """
    Test that prompt generation is consistent across multiple calls.
    """
    service = InferenceService()
    
    for use_case in UseCase:
        prompts1 = service.generate_example_prompts(use_case)
        prompts2 = service.generate_example_prompts(use_case)
        
        # Should return the same prompts each time
        assert prompts1 == prompts2, f"Prompts for {use_case} are not consistent"


def test_all_use_cases_have_prompts():
    """
    Test that all defined use cases have example prompts.
    """
    service = InferenceService()
    
    for use_case in UseCase:
        prompts = service.generate_example_prompts(use_case)
        assert len(prompts) >= 3, f"Use case {use_case} has insufficient prompts"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
