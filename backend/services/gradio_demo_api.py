"""
FastAPI endpoints for Gradio Demo Generator
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from .gradio_demo_service import (
    get_gradio_demo_service,
    DemoConfig,
    DemoInfo,
    DemoStatus
)

router = APIRouter(prefix="/api/gradio-demos", tags=["gradio-demos"])


class CreateDemoRequest(BaseModel):
    """Request to create a new demo"""
    demo_id: str
    model_id: str
    model_path: str
    title: str
    description: str
    input_type: str = "textbox"
    input_label: str = "Input"
    input_placeholder: str = "Enter your prompt here..."
    output_type: str = "textbox"
    output_label: str = "Output"
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    server_name: str = "127.0.0.1"
    server_port: int = 7860
    share: bool = False
    use_local_model: bool = True
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None


class DemoResponse(BaseModel):
    """Response with demo information"""
    demo_id: str
    status: str
    local_url: Optional[str] = None
    public_url: Optional[str] = None
    process_id: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None


class GenerateCodeResponse(BaseModel):
    """Response with generated Gradio code"""
    demo_id: str
    code: str


class EmbedCodeResponse(BaseModel):
    """Response with embeddable code"""
    demo_id: str
    embed_code: str


@router.post("/create", response_model=DemoResponse)
async def create_demo(request: CreateDemoRequest):
    """
    Create a new Gradio demo configuration.
    
    Validates: Requirements 11.1
    """
    service = get_gradio_demo_service()
    
    config = DemoConfig(
        demo_id=request.demo_id,
        model_id=request.model_id,
        model_path=request.model_path,
        title=request.title,
        description=request.description,
        input_type=request.input_type,
        input_label=request.input_label,
        input_placeholder=request.input_placeholder,
        output_type=request.output_type,
        output_label=request.output_label,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        top_p=request.top_p,
        top_k=request.top_k,
        server_name=request.server_name,
        server_port=request.server_port,
        share=request.share,
        use_local_model=request.use_local_model,
        api_endpoint=request.api_endpoint,
        api_key=request.api_key
    )
    
    demo_info = service.create_demo(config)
    
    return DemoResponse(
        demo_id=demo_info.demo_id,
        status=demo_info.status.value,
        local_url=demo_info.local_url,
        public_url=demo_info.public_url,
        process_id=demo_info.process_id,
        error_message=demo_info.error_message,
        created_at=demo_info.created_at,
        started_at=demo_info.started_at,
        stopped_at=demo_info.stopped_at
    )


@router.post("/{demo_id}/launch", response_model=DemoResponse)
async def launch_demo(demo_id: str):
    """
    Launch a Gradio demo server.
    
    Validates: Requirements 11.2
    """
    service = get_gradio_demo_service()
    
    try:
        demo_info = service.launch_demo(demo_id)
        
        return DemoResponse(
            demo_id=demo_info.demo_id,
            status=demo_info.status.value,
            local_url=demo_info.local_url,
            public_url=demo_info.public_url,
            process_id=demo_info.process_id,
            error_message=demo_info.error_message,
            created_at=demo_info.created_at,
            started_at=demo_info.started_at,
            stopped_at=demo_info.stopped_at
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{demo_id}/stop", response_model=DemoResponse)
async def stop_demo(demo_id: str):
    """
    Stop a running Gradio demo.
    """
    service = get_gradio_demo_service()
    
    try:
        demo_info = service.stop_demo(demo_id)
        
        return DemoResponse(
            demo_id=demo_info.demo_id,
            status=demo_info.status.value,
            local_url=demo_info.local_url,
            public_url=demo_info.public_url,
            process_id=demo_info.process_id,
            error_message=demo_info.error_message,
            created_at=demo_info.created_at,
            started_at=demo_info.started_at,
            stopped_at=demo_info.stopped_at
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{demo_id}", response_model=DemoResponse)
async def get_demo(demo_id: str):
    """
    Get information about a demo.
    """
    service = get_gradio_demo_service()
    demo_info = service.get_demo(demo_id)
    
    if not demo_info:
        raise HTTPException(status_code=404, detail=f"Demo {demo_id} not found")
    
    return DemoResponse(
        demo_id=demo_info.demo_id,
        status=demo_info.status.value,
        local_url=demo_info.local_url,
        public_url=demo_info.public_url,
        process_id=demo_info.process_id,
        error_message=demo_info.error_message,
        created_at=demo_info.created_at,
        started_at=demo_info.started_at,
        stopped_at=demo_info.stopped_at
    )


@router.get("/", response_model=List[DemoResponse])
async def list_demos(status: Optional[str] = None):
    """
    List all demos with optional status filter.
    """
    service = get_gradio_demo_service()
    
    status_filter = None
    if status:
        try:
            status_filter = DemoStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    demos = service.list_demos(status=status_filter)
    
    return [
        DemoResponse(
            demo_id=demo.demo_id,
            status=demo.status.value,
            local_url=demo.local_url,
            public_url=demo.public_url,
            process_id=demo.process_id,
            error_message=demo.error_message,
            created_at=demo.created_at,
            started_at=demo.started_at,
            stopped_at=demo.stopped_at
        )
        for demo in demos
    ]


@router.get("/{demo_id}/code", response_model=GenerateCodeResponse)
async def get_demo_code(demo_id: str):
    """
    Get the generated Gradio code for a demo.
    
    Validates: Requirements 11.1
    """
    service = get_gradio_demo_service()
    demo_info = service.get_demo(demo_id)
    
    if not demo_info:
        raise HTTPException(status_code=404, detail=f"Demo {demo_id} not found")
    
    code = service.generate_gradio_code(demo_info.config)
    
    return GenerateCodeResponse(
        demo_id=demo_id,
        code=code
    )


@router.get("/{demo_id}/embed", response_model=EmbedCodeResponse)
async def get_embed_code(demo_id: str):
    """
    Get embeddable HTML/JavaScript code for a demo.
    
    Validates: Requirements 11.5
    """
    service = get_gradio_demo_service()
    
    try:
        embed_code = service.generate_embeddable_code(demo_id)
        
        return EmbedCodeResponse(
            demo_id=demo_id,
            embed_code=embed_code
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{demo_id}")
async def delete_demo(demo_id: str):
    """
    Delete a demo.
    """
    service = get_gradio_demo_service()
    
    if not service.delete_demo(demo_id):
        raise HTTPException(status_code=404, detail=f"Demo {demo_id} not found")
    
    return {"message": f"Demo {demo_id} deleted successfully"}
