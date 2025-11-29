"""
Inference Playground Service for testing fine-tuned models.
Provides auto-loading, prompt generation, and comparison functionality.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

from .profile_service import UseCase

logger = logging.getLogger(__name__)


@dataclass
class InferenceRequest:
    """Request for model inference"""
    prompt: str
    model_version_id: str
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9


@dataclass
class InferenceResult:
    """Result from model inference"""
    prompt: str
    response: str
    model_version_id: str
    timestamp: datetime
    generation_time_seconds: float
    tokens_generated: int


@dataclass
class ComparisonResult:
    """Side-by-side comparison of fine-tuned and base model outputs"""
    prompt: str
    fine_tuned_output: str
    base_model_output: str
    fine_tuned_model_id: str
    base_model_id: str
    timestamp: datetime


@dataclass
class ConversationMessage:
    """Single message in conversation history"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    model_version_id: Optional[str] = None


@dataclass
class ConversationHistory:
    """Complete conversation history"""
    id: str
    messages: List[ConversationMessage]
    use_case: UseCase
    model_version_id: str
    created_at: datetime
    updated_at: datetime


class InferenceService:
    """Service for managing inference playground functionality"""
    
    def __init__(self):
        self._conversations: Dict[str, ConversationHistory] = {}
        self._loaded_models: Dict[str, any] = {}  # Cache for loaded models
        logger.info("InferenceService initialized")
    
    def generate_example_prompts(self, use_case: UseCase) -> List[str]:
        """
        Generate example prompts relevant to a specific use case.
        
        Args:
            use_case: The training use case
            
        Returns:
            List of at least 3 example prompts relevant to the use case
            
        Validates: Requirements 7.2
        """
        prompts_by_use_case = {
            UseCase.CHATBOT: [
                "Hello! Can you help me with a question?",
                "What's the weather like today?",
                "Tell me about your capabilities.",
                "How can I improve my productivity?",
                "What are some good book recommendations?"
            ],
            UseCase.CODE_GENERATION: [
                "Write a Python function to calculate fibonacci numbers",
                "Create a React component for a login form",
                "Implement a binary search algorithm in JavaScript",
                "Write a SQL query to find duplicate records",
                "Generate a REST API endpoint for user authentication"
            ],
            UseCase.SUMMARIZATION: [
                "Summarize the following article: [article text]",
                "Provide a brief overview of this document",
                "Condense this meeting transcript into key points",
                "Create an executive summary of this report",
                "Extract the main ideas from this research paper"
            ],
            UseCase.QA: [
                "What is the capital of France?",
                "How does photosynthesis work?",
                "Who invented the telephone?",
                "What are the benefits of exercise?",
                "Explain quantum computing in simple terms"
            ],
            UseCase.CREATIVE_WRITING: [
                "Write a short story about a time traveler",
                "Create a poem about the ocean",
                "Generate a creative product description for a smart watch",
                "Write an engaging opening paragraph for a mystery novel",
                "Compose a haiku about technology"
            ],
            UseCase.DOMAIN_ADAPTATION: [
                "Explain this technical concept in domain-specific terms",
                "Translate this general description into specialized vocabulary",
                "Provide domain-specific insights on this topic",
                "Apply industry knowledge to this scenario",
                "Interpret this data using domain expertise"
            ]
        }
        
        prompts = prompts_by_use_case.get(use_case, [])
        if not prompts:
            logger.warning(f"No prompts defined for use case: {use_case}")
            return [
                "Tell me about yourself",
                "What can you help me with?",
                "Give me an example of what you can do"
            ]
        
        return prompts
    
    def auto_load_model(self, model_version_id: str, use_case: UseCase) -> Dict[str, any]:
        """
        Automatically load a completed model into the inference playground.
        
        Args:
            model_version_id: ID of the model version to load
            use_case: The use case the model was trained for
            
        Returns:
            Dictionary with load status and example prompts
            
        Validates: Requirements 7.1
        """
        logger.info(f"Auto-loading model {model_version_id} for use case {use_case}")
        
        # In a real implementation, this would load the actual model
        # For now, we simulate the loading process
        self._loaded_models[model_version_id] = {
            "model_id": model_version_id,
            "use_case": use_case,
            "loaded_at": datetime.now(),
            "status": "ready"
        }
        
        # Generate example prompts for the use case
        example_prompts = self.generate_example_prompts(use_case)
        
        return {
            "model_version_id": model_version_id,
            "use_case": use_case.value,
            "status": "loaded",
            "example_prompts": example_prompts,
            "loaded_at": datetime.now().isoformat()
        }
    
    def generate_inference(self, request: InferenceRequest) -> InferenceResult:
        """
        Generate inference from a loaded model.
        
        Args:
            request: InferenceRequest with prompt and parameters
            
        Returns:
            InferenceResult with generated response
            
        Validates: Requirements 7.3
        """
        start_time = datetime.now()
        
        # Check if model is loaded
        if request.model_version_id not in self._loaded_models:
            raise ValueError(f"Model {request.model_version_id} is not loaded")
        
        # In a real implementation, this would call the actual model
        # For now, we simulate inference
        response = f"[Generated response to: {request.prompt[:50]}...]"
        
        end_time = datetime.now()
        generation_time = (end_time - start_time).total_seconds()
        
        result = InferenceResult(
            prompt=request.prompt,
            response=response,
            model_version_id=request.model_version_id,
            timestamp=end_time,
            generation_time_seconds=generation_time,
            tokens_generated=len(response.split())
        )
        
        logger.info(f"Generated inference in {generation_time:.2f}s")
        return result
    
    def compare_with_base_model(
        self,
        prompt: str,
        fine_tuned_model_id: str,
        base_model_id: str
    ) -> ComparisonResult:
        """
        Generate side-by-side comparison with base model output.
        
        Args:
            prompt: The input prompt
            fine_tuned_model_id: ID of the fine-tuned model
            base_model_id: ID of the base model
            
        Returns:
            ComparisonResult with both outputs
            
        Validates: Requirements 7.4
        """
        logger.info(f"Comparing fine-tuned model {fine_tuned_model_id} with base model {base_model_id}")
        
        # In a real implementation, this would generate from both models
        # For now, we simulate the comparison
        fine_tuned_output = f"[Fine-tuned response to: {prompt[:50]}...]"
        base_model_output = f"[Base model response to: {prompt[:50]}...]"
        
        result = ComparisonResult(
            prompt=prompt,
            fine_tuned_output=fine_tuned_output,
            base_model_output=base_model_output,
            fine_tuned_model_id=fine_tuned_model_id,
            base_model_id=base_model_id,
            timestamp=datetime.now()
        )
        
        return result
    
    def save_conversation(
        self,
        conversation_id: str,
        message: ConversationMessage,
        use_case: UseCase,
        model_version_id: str
    ) -> ConversationHistory:
        """
        Save a message to conversation history.
        
        Args:
            conversation_id: Unique conversation identifier
            message: The message to add
            use_case: The use case for this conversation
            model_version_id: The model being used
            
        Returns:
            Updated ConversationHistory
            
        Validates: Requirements 7.5
        """
        now = datetime.now()
        
        if conversation_id in self._conversations:
            # Add to existing conversation
            conversation = self._conversations[conversation_id]
            conversation.messages.append(message)
            conversation.updated_at = now
        else:
            # Create new conversation
            conversation = ConversationHistory(
                id=conversation_id,
                messages=[message],
                use_case=use_case,
                model_version_id=model_version_id,
                created_at=now,
                updated_at=now
            )
            self._conversations[conversation_id] = conversation
        
        logger.info(f"Saved message to conversation {conversation_id}")
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationHistory]:
        """
        Retrieve a conversation history.
        
        Args:
            conversation_id: Unique conversation identifier
            
        Returns:
            ConversationHistory if found, None otherwise
        """
        return self._conversations.get(conversation_id)
    
    def list_conversations(
        self,
        model_version_id: Optional[str] = None,
        use_case: Optional[UseCase] = None
    ) -> List[ConversationHistory]:
        """
        List conversation histories with optional filtering.
        
        Args:
            model_version_id: Filter by model version
            use_case: Filter by use case
            
        Returns:
            List of ConversationHistory objects
        """
        conversations = list(self._conversations.values())
        
        if model_version_id:
            conversations = [c for c in conversations if c.model_version_id == model_version_id]
        
        if use_case:
            conversations = [c for c in conversations if c.use_case == use_case]
        
        return conversations
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation history.
        
        Args:
            conversation_id: Unique conversation identifier
            
        Returns:
            True if deleted, False if not found
        """
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            logger.info(f"Deleted conversation {conversation_id}")
            return True
        return False


# Singleton instance
_inference_service_instance = None


def get_inference_service() -> InferenceService:
    """Get singleton instance of InferenceService"""
    global _inference_service_instance
    if _inference_service_instance is None:
        _inference_service_instance = InferenceService()
    return _inference_service_instance
