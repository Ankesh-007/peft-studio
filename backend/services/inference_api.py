"""
Inference Playground API endpoints.
Provides REST API for local inference testing.
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import asyncio
import json

from .inference_service import (
    get_inference_service,
    InferenceRequest,
    InferenceResult,
    ComparisonResult,
    ConversationMessage,
    ConversationHistory
)
from .profile_service import UseCase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/inference", tags=["inference"])


# Request/Response Models
class LoadModelRequest(BaseModel):
    """Request to load a model for inference"""
    model_id: str = Field(..., description="Model identifier")
    adapter_path: Optional[str] = Field(None, description="Path to adapter weights")
    quantization: Optional[str] = Field(None, description="Quantization method (int8, int4, nf4)")
    use_case: str = Field(..., description="Use case for the model")


class LoadModelResponse(BaseModel):
    """Response from loading a model"""
    model_id: str
    status: str
    example_prompts: List[str]
    loaded_at: str
    memory_usage_mb: Optional[float] = None


class GenerateRequest(BaseModel):
    """Request to generate inference"""
    model_id: str = Field(..., description="Loaded model identifier")
    prompt: str = Field(..., description="Input prompt")
    max_tokens: int = Field(512, ge=1, le=4096, description="Maximum tokens to generate")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    top_k: int = Field(50, ge=0, le=100, description="Top-k sampling parameter")
    repetition_penalty: float = Field(1.1, ge=1.0, le=2.0, description="Repetition penalty")
    stop_sequences: Optional[List[str]] = Field(None, description="Stop sequences")
    stream: bool = Field(False, description="Enable streaming response")


class GenerateResponse(BaseModel):
    """Response from inference generation"""
    prompt: str
    response: str
    model_id: str
    timestamp: str
    generation_time_seconds: float
    tokens_generated: int
    tokens_per_second: float


class CompareRequest(BaseModel):
    """Request to compare fine-tuned with base model"""
    prompt: str
    fine_tuned_model_id: str
    base_model_id: str


class CompareResponse(BaseModel):
    """Response from model comparison"""
    prompt: str
    fine_tuned_output: str
    base_model_output: str
    fine_tuned_model_id: str
    base_model_id: str
    timestamp: str


class ConversationMessageModel(BaseModel):
    """Conversation message model"""
    role: str
    content: str
    timestamp: str
    model_id: Optional[str] = None


class ConversationHistoryModel(BaseModel):
    """Conversation history model"""
    id: str
    messages: List[ConversationMessageModel]
    use_case: str
    model_id: str
    created_at: str
    updated_at: str


class SaveMessageRequest(BaseModel):
    """Request to save a conversation message"""
    conversation_id: str
    role: str
    content: str
    model_id: str
    use_case: str


# Endpoints
@router.post("/load", response_model=LoadModelResponse)
async def load_model(request: LoadModelRequest):
    """
    Load a model for inference.
    
    Validates: Requirements 10.1, 10.2
    """
    try:
        service = get_inference_service()
        
        # Parse use case
        try:
            use_case = UseCase(request.use_case)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid use case: {request.use_case}")
        
        # Load the model
        result = service.auto_load_model(request.model_id, use_case)
        
        return LoadModelResponse(
            model_id=result["model_version_id"],
            status=result["status"],
            example_prompts=result["example_prompts"],
            loaded_at=result["loaded_at"],
            memory_usage_mb=None  # Would be calculated in real implementation
        )
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    Generate inference from a loaded model.
    
    Validates: Requirements 10.3, 10.4
    """
    try:
        service = get_inference_service()
        
        # Create inference request
        inference_request = InferenceRequest(
            prompt=request.prompt,
            model_version_id=request.model_id,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p
        )
        
        # Generate inference
        result = service.generate_inference(inference_request)
        
        # Calculate tokens per second
        tokens_per_second = (
            result.tokens_generated / result.generation_time_seconds
            if result.generation_time_seconds > 0
            else 0
        )
        
        return GenerateResponse(
            prompt=result.prompt,
            response=result.response,
            model_id=result.model_version_id,
            timestamp=result.timestamp.isoformat(),
            generation_time_seconds=result.generation_time_seconds,
            tokens_generated=result.tokens_generated,
            tokens_per_second=tokens_per_second
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating inference: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/stream")
async def stream_generate(websocket: WebSocket):
    """
    Stream inference generation via WebSocket.
    
    Validates: Requirements 10.4
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive request
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            # Validate request
            try:
                request = GenerateRequest(**request_data)
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "error": f"Invalid request: {str(e)}"
                })
                continue
            
            # Generate with streaming
            service = get_inference_service()
            
            try:
                # Send start event
                await websocket.send_json({
                    "type": "start",
                    "model_id": request.model_id
                })
                
                # In a real implementation, this would stream tokens
                # For now, simulate streaming
                inference_request = InferenceRequest(
                    prompt=request.prompt,
                    model_version_id=request.model_id,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    top_p=request.top_p
                )
                
                result = service.generate_inference(inference_request)
                
                # Simulate token-by-token streaming
                words = result.response.split()
                for i, word in enumerate(words):
                    await websocket.send_json({
                        "type": "token",
                        "token": word + " ",
                        "index": i
                    })
                    await asyncio.sleep(0.05)  # Simulate generation delay
                
                # Send completion event
                await websocket.send_json({
                    "type": "complete",
                    "total_tokens": len(words),
                    "generation_time": result.generation_time_seconds
                })
                
            except Exception as e:
                logger.error(f"Error during streaming: {e}")
                await websocket.send_json({
                    "type": "error",
                    "error": str(e)
                })
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


@router.post("/compare", response_model=CompareResponse)
async def compare_models(request: CompareRequest):
    """
    Compare fine-tuned model with base model.
    
    Validates: Requirements 10.3
    """
    try:
        service = get_inference_service()
        
        result = service.compare_with_base_model(
            prompt=request.prompt,
            fine_tuned_model_id=request.fine_tuned_model_id,
            base_model_id=request.base_model_id
        )
        
        return CompareResponse(
            prompt=result.prompt,
            fine_tuned_output=result.fine_tuned_output,
            base_model_output=result.base_model_output,
            fine_tuned_model_id=result.fine_tuned_model_id,
            base_model_id=result.base_model_id,
            timestamp=result.timestamp.isoformat()
        )
    except Exception as e:
        logger.error(f"Error comparing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversation/save")
async def save_conversation_message(request: SaveMessageRequest):
    """
    Save a message to conversation history.
    
    Validates: Requirements 10.5
    """
    try:
        service = get_inference_service()
        
        # Parse use case
        try:
            use_case = UseCase(request.use_case)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid use case: {request.use_case}")
        
        # Create message
        message = ConversationMessage(
            role=request.role,
            content=request.content,
            timestamp=datetime.now(),
            model_version_id=request.model_id
        )
        
        # Save to conversation
        conversation = service.save_conversation(
            conversation_id=request.conversation_id,
            message=message,
            use_case=use_case,
            model_version_id=request.model_id
        )
        
        return {
            "conversation_id": conversation.id,
            "message_count": len(conversation.messages),
            "updated_at": conversation.updated_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/{conversation_id}", response_model=ConversationHistoryModel)
async def get_conversation(conversation_id: str):
    """
    Get conversation history.
    
    Validates: Requirements 10.5
    """
    try:
        service = get_inference_service()
        conversation = service.get_conversation(conversation_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return ConversationHistoryModel(
            id=conversation.id,
            messages=[
                ConversationMessageModel(
                    role=msg.role,
                    content=msg.content,
                    timestamp=msg.timestamp.isoformat(),
                    model_id=msg.model_version_id
                )
                for msg in conversation.messages
            ],
            use_case=conversation.use_case.value,
            model_id=conversation.model_version_id,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations", response_model=List[ConversationHistoryModel])
async def list_conversations(
    model_id: Optional[str] = None,
    use_case: Optional[str] = None
):
    """
    List conversation histories with optional filtering.
    
    Validates: Requirements 10.5
    """
    try:
        service = get_inference_service()
        
        # Parse use case if provided
        use_case_enum = None
        if use_case:
            try:
                use_case_enum = UseCase(use_case)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid use case: {use_case}")
        
        conversations = service.list_conversations(
            model_version_id=model_id,
            use_case=use_case_enum
        )
        
        return [
            ConversationHistoryModel(
                id=conv.id,
                messages=[
                    ConversationMessageModel(
                        role=msg.role,
                        content=msg.content,
                        timestamp=msg.timestamp.isoformat(),
                        model_id=msg.model_version_id
                    )
                    for msg in conv.messages
                ],
                use_case=conv.use_case.value,
                model_id=conv.model_version_id,
                created_at=conv.created_at.isoformat(),
                updated_at=conv.updated_at.isoformat()
            )
            for conv in conversations
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation history.
    """
    try:
        service = get_inference_service()
        deleted = service.delete_conversation(conversation_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"status": "deleted", "conversation_id": conversation_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/loaded")
async def list_loaded_models():
    """
    List currently loaded models.
    
    Validates: Requirements 10.1
    """
    try:
        service = get_inference_service()
        
        # In a real implementation, this would return actual loaded models
        # For now, return the cached models
        loaded_models = [
            {
                "model_id": model_id,
                "status": info["status"],
                "loaded_at": info["loaded_at"].isoformat(),
                "use_case": info["use_case"].value
            }
            for model_id, info in service._loaded_models.items()
        ]
        
        return {"models": loaded_models}
    except Exception as e:
        logger.error(f"Error listing loaded models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/{model_id}/unload")
async def unload_model(model_id: str):
    """
    Unload a model from memory.
    
    Validates: Requirements 10.1
    """
    try:
        service = get_inference_service()
        
        if model_id in service._loaded_models:
            del service._loaded_models[model_id]
            return {"status": "unloaded", "model_id": model_id}
        else:
            raise HTTPException(status_code=404, detail="Model not loaded")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unloading model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/{model_id}/swap-adapter")
async def swap_adapter(model_id: str, adapter_path: str):
    """
    Hot-swap adapter without reloading base model.
    
    Validates: Requirements 10.5
    """
    try:
        service = get_inference_service()
        
        if model_id not in service._loaded_models:
            raise HTTPException(status_code=404, detail="Model not loaded")
        
        # In a real implementation, this would hot-swap the adapter
        # For now, simulate the swap
        service._loaded_models[model_id]["adapter_path"] = adapter_path
        service._loaded_models[model_id]["swapped_at"] = datetime.now()
        
        return {
            "status": "swapped",
            "model_id": model_id,
            "adapter_path": adapter_path,
            "swapped_at": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error swapping adapter: {e}")
        raise HTTPException(status_code=500, detail=str(e))
