from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import uvicorn
import logging
import asyncio
import json

# STARTUP OPTIMIZATION: Import startup optimizer first
from services.startup_service import get_startup_optimizer, measure_startup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize startup optimizer
startup_optimizer = get_startup_optimizer()

# STARTUP OPTIMIZATION: Lazy load heavy services
# These will be imported only when actually needed
_services_loaded = False

def _lazy_load_services():
    """Lazily load service imports"""
    global _services_loaded
    if _services_loaded:
        return
    
    global get_peft_service, get_hardware_service, get_model_registry_service
    global get_smart_config_engine, get_profile_service, get_monitoring_service
    global PEFTAlgorithm, PEFTConfig, HardwareSpecs, ModelSpecs, DatasetSpecs, UseCase
    global get_inference_service, get_queue_manager, OperationType
    global get_network_monitor, get_sync_engine, ConflictResolution
    
    from services import (
        get_peft_service,
        get_hardware_service,
        get_model_registry_service,
        get_smart_config_engine,
        get_profile_service,
        get_monitoring_service,
        PEFTAlgorithm,
        PEFTConfig,
        HardwareSpecs,
        ModelSpecs,
        DatasetSpecs,
        UseCase
    )
    from services.inference_service import get_inference_service
    from services.offline_queue_service import get_queue_manager, OperationType
    from services.network_service import get_network_monitor
    from services.sync_engine import get_sync_engine, ConflictResolution
    
    _services_loaded = True

# STARTUP OPTIMIZATION: Import routers (lightweight)
from services.experiment_tracking_api import router as experiment_tracking_router
from services.deployment_api import router as deployment_router
from services.gradio_demo_api import router as gradio_demo_router
from services.security_api import router as security_router
from services.telemetry_api import router as telemetry_router
from services.settings_api import router as settings_router
from services.inference_api import router as inference_router
from services.configuration_management_api import router as configuration_management_router
from services.logging_api import router as logging_router

# SECURITY: Import security middleware
from services.security_middleware import SecurityMiddleware, InputValidationMiddleware

app = FastAPI(title="PEFT Studio Backend")

# SECURITY: Add security middleware (before CORS)
app.add_middleware(SecurityMiddleware)
app.add_middleware(InputValidationMiddleware)

# CORS middleware for Electron
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Performance monitoring middleware
@app.middleware("http")
async def performance_monitoring_middleware(request, call_next):
    """Middleware to monitor request performance."""
    import time
    from services.performance_service import get_performance_monitor
    
    start_time = time.time()
    error = False
    
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        error = True
        raise
    finally:
        duration = time.time() - start_time
        endpoint = f"{request.method} {request.url.path}"
        
        monitor = get_performance_monitor()
        monitor.record_request(endpoint, duration, error)

# Include routers
app.include_router(security_router)
app.include_router(experiment_tracking_router)
app.include_router(deployment_router)
app.include_router(gradio_demo_router)
app.include_router(telemetry_router)
app.include_router(settings_router)
app.include_router(inference_router)
app.include_router(configuration_management_router)
app.include_router(logging_router)


# Request/Response Models
class PEFTConfigRequest(BaseModel):
    algorithm: str
    r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    target_modules: Optional[List[str]] = None


class ModelLoadRequest(BaseModel):
    model_name: str
    max_seq_length: int = 2048
    load_in_4bit: bool = False
    load_in_8bit: bool = False


class ModelSearchRequest(BaseModel):
    query: Optional[str] = None
    task: Optional[str] = "text-generation"
    limit: int = 20


@app.on_event("startup")
@measure_startup("app_startup")
async def startup_event():
    """
    Application startup event handler.
    
    Implements startup optimizations:
    - Preload critical resources
    - Optimize database queries
    - Initialize connection pools
    """
    logger.info("Starting PEFT Studio Backend...")
    
    # Initialize performance service
    from services.performance_service import get_performance_service
    from database import engine
    
    perf_service = get_performance_service()
    await perf_service.initialize(engine)
    logger.info("Performance optimizations initialized")
    
    # Preload critical resources (non-blocking)
    await startup_optimizer.preload_critical_resources()
    
    # Optimize database queries
    startup_optimizer.optimize_database_queries()
    
    # Log startup metrics
    report = startup_optimizer.get_startup_report()
    logger.info(f"Startup complete in {report['total_time']:.3f}s")
    
    if not report['meets_target']:
        logger.warning(f"Startup time exceeds 3-second target!")
        for rec in report['recommendations']:
            logger.warning(f"  - {rec}")


@app.get("/")
async def root():
    return {"message": "PEFT Studio Backend Running"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint - responds immediately without loading heavy services"""
    return {"status": "healthy"}


@app.get("/api/startup/metrics")
async def get_startup_metrics():
    """Get startup performance metrics"""
    report = startup_optimizer.get_startup_report()
    return report


# Hardware Endpoints
@app.get("/api/hardware/profile")
async def get_hardware_profile():
    """Get complete hardware profile"""
    try:
        # STARTUP OPTIMIZATION: Lazy load services
        _lazy_load_services()
        hardware_service = get_hardware_service()
        profile = hardware_service.get_hardware_profile()
        
        return {
            "gpus": [
                {
                    "id": gpu.id,
                    "name": gpu.name,
                    "memory_total_gb": gpu.memory_total / (1024**3),
                    "memory_available_gb": gpu.memory_available / (1024**3),
                    "memory_used_gb": gpu.memory_used / (1024**3),
                    "compute_capability": gpu.compute_capability,
                    "cuda_version": gpu.cuda_version,
                    "temperature": gpu.temperature,
                    "utilization": gpu.utilization
                }
                for gpu in profile.gpus
            ],
            "cpu": {
                "cores_physical": profile.cpu.cores_physical,
                "cores_logical": profile.cpu.cores_logical,
                "frequency_mhz": profile.cpu.frequency_mhz,
                "architecture": profile.cpu.architecture,
                "utilization": profile.cpu.utilization
            },
            "ram": {
                "total_gb": profile.ram.total / (1024**3),
                "available_gb": profile.ram.available / (1024**3),
                "used_gb": profile.ram.used / (1024**3),
                "percent_used": profile.ram.percent_used
            },
            "platform": profile.platform,
            "python_version": profile.python_version,
            "torch_version": profile.torch_version,
            "cuda_available": profile.cuda_available,
            "timestamp": profile.timestamp.isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting hardware profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hardware/cuda/validate")
async def validate_cuda():
    """Validate CUDA environment"""
    try:
        hardware_service = get_hardware_service()
        validation = hardware_service.validate_cuda_environment()
        return validation
    except Exception as e:
        logger.error(f"Error validating CUDA: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Model Registry Endpoints
@app.post("/api/models/search")
async def search_models(request: ModelSearchRequest):
    """Search for models on HuggingFace Hub"""
    try:
        registry_service = get_model_registry_service()
        models = registry_service.search_models(
            query=request.query,
            task=request.task,
            limit=request.limit
        )
        
        return {
            "models": [
                {
                    "model_id": m.model_id,
                    "author": m.author,
                    "model_name": m.model_name,
                    "downloads": m.downloads,
                    "likes": m.likes,
                    "tags": m.tags,
                    "pipeline_tag": m.pipeline_tag,
                    "library_name": m.library_name,
                    "size_mb": m.size_mb,
                    "parameters": m.parameters,
                    "architecture": m.architecture,
                    "license": m.license
                }
                for m in models
            ]
        }
    except Exception as e:
        logger.error(f"Error searching models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/{model_id:path}")
async def get_model_info(model_id: str):
    """Get detailed information about a specific model"""
    try:
        registry_service = get_model_registry_service()
        model = registry_service.get_model_info(model_id)
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return {
            "model_id": model.model_id,
            "author": model.author,
            "model_name": model.model_name,
            "downloads": model.downloads,
            "likes": model.likes,
            "tags": model.tags,
            "pipeline_tag": model.pipeline_tag,
            "library_name": model.library_name,
            "size_mb": model.size_mb,
            "parameters": model.parameters,
            "architecture": model.architecture,
            "license": model.license,
            "created_at": model.created_at,
            "last_modified": model.last_modified
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/popular/{task}")
async def get_popular_models(task: str = "text-generation", limit: int = 10):
    """Get popular models for a specific task"""
    try:
        registry_service = get_model_registry_service()
        models = registry_service.get_popular_models(task=task, limit=limit)
        
        return {
            "models": [
                {
                    "model_id": m.model_id,
                    "author": m.author,
                    "model_name": m.model_name,
                    "downloads": m.downloads,
                    "likes": m.likes,
                    "parameters": m.parameters,
                    "architecture": m.architecture,
                    "registry": m.registry
                }
                for m in models
            ]
        }
    except Exception as e:
        logger.error(f"Error getting popular models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class MultiRegistrySearchRequest(BaseModel):
    query: Optional[str] = None
    task: Optional[str] = "text-generation"
    registries: Optional[List[str]] = None
    limit: int = 20


@app.post("/api/models/search/multi-registry")
async def search_multi_registry(request: MultiRegistrySearchRequest):
    """Search across multiple model registries"""
    try:
        registry_service = get_model_registry_service()
        models = registry_service.search_multi_registry(
            query=request.query,
            task=request.task,
            registries=request.registries,
            limit=request.limit
        )
        
        return {
            "models": [
                {
                    "model_id": m.model_id,
                    "author": m.author,
                    "model_name": m.model_name,
                    "downloads": m.downloads,
                    "likes": m.likes,
                    "tags": m.tags,
                    "pipeline_tag": m.pipeline_tag,
                    "library_name": m.library_name,
                    "size_mb": m.size_mb,
                    "parameters": m.parameters,
                    "architecture": m.architecture,
                    "license": m.license,
                    "registry": m.registry
                }
                for m in models
            ]
        }
    except Exception as e:
        logger.error(f"Error searching multi-registry: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/cache")
async def list_cached_models():
    """List all cached models"""
    try:
        registry_service = get_model_registry_service()
        cached = registry_service.list_cached_models()
        
        return {
            "cached_models": [
                {
                    "model_id": c.model_id,
                    "registry": c.registry,
                    "cached_at": c.cached_at,
                    "expires_at": c.expires_at,
                    "metadata": c.metadata
                }
                for c in cached
            ]
        }
    except Exception as e:
        logger.error(f"Error listing cached models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/models/cache")
async def clear_model_cache():
    """Clear all model cache"""
    try:
        registry_service = get_model_registry_service()
        registry_service.clear_cache()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/models/cache/{registry}/{model_id:path}")
async def remove_from_cache(registry: str, model_id: str):
    """Remove a specific model from cache"""
    try:
        registry_service = get_model_registry_service()
        success = registry_service.remove_from_cache(model_id, registry)
        
        if success:
            return {"message": f"Model {model_id} removed from cache"}
        else:
            raise HTTPException(status_code=404, detail="Model not found in cache")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class ModelCompatibilityRequest(BaseModel):
    model_id: str
    gpu_memory_gb: float


@app.post("/api/models/compatibility")
async def check_model_compatibility(request: ModelCompatibilityRequest):
    """Check if a model is compatible with available hardware"""
    try:
        registry_service = get_model_registry_service()
        model = registry_service.get_model_info(request.model_id)
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Estimate VRAM requirements
        estimated_vram = 0.0
        if model.parameters:
            # Rough estimate: 2 bytes per parameter for FP16
            estimated_vram = (model.parameters * 2) / (1024**3)
        
        compatible = estimated_vram <= request.gpu_memory_gb
        warnings = []
        recommendations = []
        
        if not compatible:
            warnings.append(f"Model requires ~{estimated_vram:.1f}GB VRAM but only {request.gpu_memory_gb:.1f}GB available")
            recommendations.append("Consider using 4-bit quantization to reduce memory usage")
            recommendations.append("Try a smaller model variant")
        elif estimated_vram > request.gpu_memory_gb * 0.8:
            warnings.append("Model will use most of available VRAM")
            recommendations.append("Consider using 8-bit quantization for better performance")
        
        return {
            "compatible": compatible,
            "estimatedVRAM": estimated_vram,
            "warnings": warnings,
            "recommendations": recommendations
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking compatibility: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# PEFT Endpoints
@app.post("/api/peft/load-model")
async def load_model(request: ModelLoadRequest):
    """Load a model with Unsloth optimization"""
    try:
        peft_service = get_peft_service()
        model_info = peft_service.load_model_with_unsloth(
            model_name=request.model_name,
            max_seq_length=request.max_seq_length,
            load_in_4bit=request.load_in_4bit,
            load_in_8bit=request.load_in_8bit
        )
        
        return {
            "model_name": model_info.model_name,
            "max_seq_length": model_info.max_seq_length,
            "supports_gradient_checkpointing": model_info.supports_gradient_checkpointing,
            "memory_footprint_mb": model_info.memory_footprint_mb
        }
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/peft/loaded-models")
async def list_loaded_models():
    """Get list of currently loaded models"""
    try:
        peft_service = get_peft_service()
        models = peft_service.list_loaded_models()
        return {"models": models}
    except Exception as e:
        logger.error(f"Error listing loaded models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/peft/algorithms")
async def list_peft_algorithms():
    """Get list of supported PEFT algorithms"""
    return {
        "algorithms": [algo.value for algo in PEFTAlgorithm]
    }


# Smart Configuration Endpoints
class SmartConfigRequest(BaseModel):
    # Hardware specs
    gpu_memory_mb: int
    cpu_cores: int
    ram_gb: int
    compute_capability: Optional[str] = None
    
    # Model specs
    model_size_mb: int
    num_parameters: Optional[int] = None
    max_seq_length: int = 2048
    architecture: Optional[str] = None
    
    # Dataset specs
    num_samples: int
    avg_sequence_length: Optional[int] = None
    max_sequence_length: Optional[int] = None
    
    # Preferences
    target_effective_batch_size: int = 32


@app.post("/api/config/smart-defaults")
async def calculate_smart_defaults(request: SmartConfigRequest):
    """Calculate smart configuration defaults based on hardware and data"""
    try:
        config_engine = get_smart_config_engine()
        
        hardware = HardwareSpecs(
            gpu_memory_mb=request.gpu_memory_mb,
            cpu_cores=request.cpu_cores,
            ram_gb=request.ram_gb,
            compute_capability=request.compute_capability
        )
        
        model = ModelSpecs(
            model_size_mb=request.model_size_mb,
            num_parameters=request.num_parameters,
            max_seq_length=request.max_seq_length,
            architecture=request.architecture
        )
        
        dataset = DatasetSpecs(
            num_samples=request.num_samples,
            avg_sequence_length=request.avg_sequence_length,
            max_sequence_length=request.max_sequence_length
        )
        
        config = config_engine.calculate_smart_defaults(
            hardware=hardware,
            model=model,
            dataset=dataset,
            target_effective_batch_size=request.target_effective_batch_size
        )
        
        return {
            "batch_size": config.batch_size,
            "gradient_accumulation_steps": config.gradient_accumulation_steps,
            "effective_batch_size": config.effective_batch_size,
            "precision": config.precision.value,
            "quantization": config.quantization.value,
            "learning_rate": config.learning_rate,
            "num_epochs": config.num_epochs,
            "max_steps": config.max_steps,
            "estimated_memory_mb": config.estimated_memory_mb,
            "memory_utilization_percent": config.memory_utilization_percent,
            "estimated_training_time_hours": config.estimated_training_time_hours,
            "tokens_per_second": config.tokens_per_second,
            "explanations": config.explanations
        }
    except Exception as e:
        logger.error(f"Error calculating smart defaults: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class TrainingConfigValidationRequest(BaseModel):
    provider: str
    algorithm: str
    quantization: str = "none"
    experiment_tracker: str = "none"
    project_name: Optional[str] = None
    model_name: str
    model_path: str
    dataset_id: str
    dataset_path: str
    lora_r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    target_modules: List[str] = ["q_proj", "k_proj", "v_proj", "o_proj"]
    learning_rate: float = 2e-4
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    num_epochs: int = 3
    max_steps: int = -1


@app.post("/api/config/validate-training")
async def validate_training_configuration(request: TrainingConfigValidationRequest):
    """
    Validate a training configuration for completeness and correctness.
    Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
    """
    try:
        from services.training_config_service import (
            get_training_config_service,
            TrainingConfiguration,
            PEFTAlgorithm,
            QuantizationType,
            ComputeProvider,
            ExperimentTracker,
        )
        
        # Convert request to TrainingConfiguration
        config = TrainingConfiguration(
            provider=ComputeProvider(request.provider),
            algorithm=PEFTAlgorithm(request.algorithm),
            quantization=QuantizationType(request.quantization),
            experiment_tracker=ExperimentTracker(request.experiment_tracker),
            project_name=request.project_name,
            model_name=request.model_name,
            model_path=request.model_path,
            dataset_id=request.dataset_id,
            dataset_path=request.dataset_path,
            lora_r=request.lora_r,
            lora_alpha=request.lora_alpha,
            lora_dropout=request.lora_dropout,
            target_modules=request.target_modules,
            learning_rate=request.learning_rate,
            batch_size=request.batch_size,
            gradient_accumulation_steps=request.gradient_accumulation_steps,
            num_epochs=request.num_epochs,
            max_steps=request.max_steps,
        )
        
        # Validate configuration
        service = get_training_config_service()
        validation_result = service.validate_configuration(config)
        
        return {
            "is_valid": validation_result.is_valid,
            "errors": validation_result.errors,
            "warnings": validation_result.warnings,
            "suggestions": validation_result.suggestions,
        }
    except ValueError as e:
        # Invalid enum value
        raise HTTPException(status_code=400, detail=f"Invalid configuration value: {str(e)}")
    except Exception as e:
        logger.error(f"Error validating training configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class BatchSizeRequest(BaseModel):
    gpu_memory_mb: int
    model_size_mb: int
    seq_length: int
    precision: str = "fp16"


@app.post("/api/config/batch-size")
async def calculate_batch_size(request: BatchSizeRequest):
    """Calculate optimal batch size"""
    try:
        from services.smart_config_service import PrecisionType
        
        config_engine = get_smart_config_engine()
        precision = PrecisionType(request.precision)
        
        batch_size = config_engine.calculate_batch_size(
            gpu_memory_mb=request.gpu_memory_mb,
            model_size_mb=request.model_size_mb,
            seq_length=request.seq_length,
            precision=precision
        )
        
        return {"batch_size": batch_size}
    except Exception as e:
        logger.error(f"Error calculating batch size: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class PrecisionRecommendationRequest(BaseModel):
    compute_capability: Optional[str] = None
    gpu_memory_mb: Optional[int] = None
    model_size_mb: Optional[int] = None


@app.post("/api/config/recommend-precision")
async def recommend_precision(request: PrecisionRecommendationRequest):
    """Recommend optimal precision"""
    try:
        config_engine = get_smart_config_engine()
        
        precision = config_engine.recommend_precision(
            compute_capability=request.compute_capability,
            gpu_memory_mb=request.gpu_memory_mb,
            model_size_mb=request.model_size_mb
        )
        
        return {"precision": precision.value}
    except Exception as e:
        logger.error(f"Error recommending precision: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class QuantizationCheckRequest(BaseModel):
    gpu_memory_mb: int
    model_size_mb: int
    precision: str = "fp16"


@app.post("/api/config/check-quantization")
async def check_quantization(request: QuantizationCheckRequest):
    """Check if quantization should be enabled"""
    try:
        from services.smart_config_service import PrecisionType
        
        config_engine = get_smart_config_engine()
        precision = PrecisionType(request.precision)
        
        quantization = config_engine.should_enable_quantization(
            gpu_memory_mb=request.gpu_memory_mb,
            model_size_mb=request.model_size_mb,
            precision=precision
        )
        
        return {
            "quantization": quantization.value,
            "should_quantize": quantization.value != "none"
        }
    except Exception as e:
        logger.error(f"Error checking quantization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Profile Endpoints
@app.get("/api/profiles")
async def list_profiles():
    """Get all available optimization profiles"""
    try:
        profile_service = get_profile_service()
        profiles = profile_service.list_profiles()
        
        return {
            "profiles": [profile.to_dict() for profile in profiles]
        }
    except Exception as e:
        logger.error(f"Error listing profiles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profiles/{profile_id}")
async def get_profile(profile_id: str):
    """Get a specific optimization profile"""
    try:
        profile_service = get_profile_service()
        profile = profile_service.get_profile(profile_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile not found: {profile_id}")
        
        return profile.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profiles/use-case/{use_case}")
async def get_profile_by_use_case(use_case: str):
    """Get profile by use case"""
    try:
        profile_service = get_profile_service()
        use_case_enum = UseCase(use_case)
        profile = profile_service.get_profile_by_use_case(use_case_enum)
        
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile not found for use case: {use_case}")
        
        return profile.to_dict()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid use case: {use_case}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile by use case: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class ProfileConfigRequest(BaseModel):
    profile_id: str
    overrides: Optional[dict] = None


@app.post("/api/profiles/apply")
async def apply_profile_config(request: ProfileConfigRequest):
    """Apply a profile configuration with optional overrides"""
    try:
        profile_service = get_profile_service()
        config = profile_service.apply_profile_config(
            profile_id=request.profile_id,
            overrides=request.overrides
        )
        
        return {"config": config}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error applying profile config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class ProfileCompatibilityRequest(BaseModel):
    profile_id: str
    gpu_memory_gb: float
    dataset_size: int


@app.post("/api/profiles/validate-compatibility")
async def validate_profile_compatibility(request: ProfileCompatibilityRequest):
    """Validate if hardware and dataset meet profile requirements"""
    try:
        profile_service = get_profile_service()
        result = profile_service.validate_profile_compatibility(
            profile_id=request.profile_id,
            gpu_memory_gb=request.gpu_memory_gb,
            dataset_size=request.dataset_size
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error validating profile compatibility: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)
        logger.info(f"WebSocket connected for job {job_id}")
    
    def disconnect(self, websocket: WebSocket, job_id: str):
        if job_id in self.active_connections:
            self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
        logger.info(f"WebSocket disconnected for job {job_id}")
    
    async def broadcast(self, job_id: str, message: dict):
        if job_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message: {e}")
                    disconnected.append(connection)
            
            # Remove disconnected clients
            for connection in disconnected:
                self.disconnect(connection, job_id)


manager = ConnectionManager()


# Monitoring Endpoints
@app.websocket("/ws/training/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time training metrics"""
    await manager.connect(websocket, job_id)
    
    try:
        monitoring_service = get_monitoring_service()
        
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "job_id": job_id,
            "message": "Connected to training metrics stream"
        })
        
        # Keep connection alive and send periodic updates
        while True:
            try:
                # Wait for messages from client (ping/pong)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=2.0)
                
                # Handle client messages if needed
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except asyncio.TimeoutError:
                # Send latest metrics every 2 seconds
                latest_metrics = monitoring_service.get_latest_metrics(job_id)
                if latest_metrics:
                    await websocket.send_json({
                        "type": "metrics",
                        "data": latest_metrics.to_dict()
                    })
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)
        logger.info(f"Client disconnected from job {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, job_id)


@app.post("/api/monitoring/start/{job_id}")
async def start_monitoring(job_id: str):
    """Start monitoring a training job"""
    try:
        monitoring_service = get_monitoring_service()
        monitoring_service.start_monitoring(job_id)
        return {"status": "success", "job_id": job_id}
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/monitoring/stop/{job_id}")
async def stop_monitoring(job_id: str):
    """Stop monitoring a training job"""
    try:
        monitoring_service = get_monitoring_service()
        monitoring_service.stop_monitoring(job_id)
        return {"status": "success", "job_id": job_id}
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class MetricsRecordRequest(BaseModel):
    step: int
    epoch: int
    loss: float
    learning_rate: float
    throughput: float
    samples_per_second: float
    grad_norm: Optional[float] = None
    val_loss: Optional[float] = None
    val_perplexity: Optional[float] = None


@app.post("/api/monitoring/record/{job_id}")
async def record_metrics(job_id: str, request: MetricsRecordRequest):
    """Record training metrics for a job"""
    try:
        monitoring_service = get_monitoring_service()
        
        metrics = monitoring_service.record_metrics(
            job_id=job_id,
            step=request.step,
            epoch=request.epoch,
            loss=request.loss,
            learning_rate=request.learning_rate,
            throughput=request.throughput,
            samples_per_second=request.samples_per_second,
            grad_norm=request.grad_norm,
            val_loss=request.val_loss,
            val_perplexity=request.val_perplexity
        )
        
        # Broadcast to connected WebSocket clients
        await manager.broadcast(job_id, {
            "type": "metrics",
            "data": metrics.to_dict()
        })
        
        return {"status": "success", "metrics": metrics.to_dict()}
    except Exception as e:
        logger.error(f"Error recording metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitoring/metrics/{job_id}")
async def get_metrics(job_id: str, limit: Optional[int] = 100):
    """Get metrics history for a job"""
    try:
        monitoring_service = get_monitoring_service()
        history = monitoring_service.get_metrics_history(job_id, limit=limit)
        
        return {
            "job_id": job_id,
            "metrics": [m.to_dict() for m in history]
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitoring/latest/{job_id}")
async def get_latest_metrics(job_id: str):
    """Get the latest metrics for a job"""
    try:
        monitoring_service = get_monitoring_service()
        metrics = monitoring_service.get_latest_metrics(job_id)
        
        if not metrics:
            raise HTTPException(status_code=404, detail="No metrics found for job")
        
        return {"job_id": job_id, "metrics": metrics.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitoring/loss-zone/{job_id}")
async def get_loss_zone(job_id: str):
    """Get the current loss color zone for visualization"""
    try:
        monitoring_service = get_monitoring_service()
        history = monitoring_service.get_metrics_history(job_id, limit=2)
        
        if not history:
            raise HTTPException(status_code=404, detail="No metrics found for job")
        
        current_loss = history[-1].loss
        previous_loss = history[-2].loss if len(history) > 1 else None
        
        zone = monitoring_service.calculate_loss_zone(current_loss, previous_loss)
        
        return {
            "job_id": job_id,
            "current_loss": current_loss,
            "previous_loss": previous_loss,
            "zone": zone
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating loss zone: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Quality Analysis Endpoints
@app.get("/api/quality-analysis/{job_id}")
async def get_quality_analysis(job_id: str):
    """Get quality analysis for a completed training job"""
    try:
        from services.training_orchestration_service import get_training_orchestrator
        
        orchestrator = get_training_orchestrator()
        job = orchestrator.get_status(job_id)
        
        if not job.quality_analysis:
            raise HTTPException(status_code=404, detail="Quality analysis not available. Training may not be complete.")
        
        return {
            "job_id": job_id,
            "quality_score": job.quality_analysis.quality_score,
            "overall_assessment": job.quality_analysis.overall_assessment,
            "improvement_suggestions": [
                {
                    "category": s.category.value,
                    "description": s.description,
                    "priority": s.priority.value,
                    "action": s.action
                }
                for s in job.quality_analysis.improvement_suggestions
            ],
            "metrics_summary": job.quality_analysis.metrics_summary
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quality analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/quality-analysis/analyze/{job_id}")
async def trigger_quality_analysis(job_id: str):
    """Manually trigger quality analysis for a job"""
    try:
        from services.training_orchestration_service import get_training_orchestrator
        from services.quality_analysis_service import analyze_training_quality, TrainingResult
        
        orchestrator = get_training_orchestrator()
        job = orchestrator.get_status(job_id)
        
        if job.state not in ["completed", "stopped"]:
            raise HTTPException(status_code=400, detail="Can only analyze completed or stopped jobs")
        
        # Extract training data
        if not job.metrics_history:
            raise HTTPException(status_code=400, detail="No training metrics available")
        
        loss_history = [m.loss for m in job.metrics_history]
        
        training_result = TrainingResult(
            final_loss=loss_history[-1],
            initial_loss=loss_history[0],
            epochs_completed=job.config.num_epochs,
            total_steps=len(loss_history),
            best_val_loss=None,
            convergence_achieved=loss_history[-1] < 0.5,
            gradient_norm_stable=True,
            loss_history=loss_history
        )
        
        quality_analysis = analyze_training_quality(training_result)
        job.quality_analysis = quality_analysis
        
        return {
            "job_id": job_id,
            "quality_score": quality_analysis.quality_score,
            "overall_assessment": quality_analysis.overall_assessment,
            "improvement_suggestions": [
                {
                    "category": s.category.value,
                    "description": s.description,
                    "priority": s.priority.value,
                    "action": s.action
                }
                for s in quality_analysis.improvement_suggestions
            ],
            "metrics_summary": quality_analysis.metrics_summary
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering quality analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Notification Endpoints
@app.get("/api/notifications/{job_id}")
async def get_notifications(job_id: str):
    """Get all notifications for a training job"""
    try:
        from services.training_orchestration_service import get_training_orchestrator
        
        orchestrator = get_training_orchestrator()
        job = orchestrator.get_status(job_id)
        
        return {
            "job_id": job_id,
            "notifications": [
                {
                    "type": n.type.value,
                    "title": n.title,
                    "message": n.message,
                    "milestone": n.milestone,
                    "urgency": n.urgency,
                    "sound": n.sound,
                    "actions": n.actions
                }
                for n in job.notifications
            ]
        }
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/notifications/{job_id}")
async def notification_websocket(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time notifications"""
    await websocket.accept()
    
    try:
        from services.training_orchestration_service import get_training_orchestrator
        
        orchestrator = get_training_orchestrator()
        
        # Register notification callback
        async def notification_callback(notification):
            await websocket.send_json({
                "type": "notification",
                "data": {
                    "type": notification.type.value,
                    "title": notification.title,
                    "message": notification.message,
                    "milestone": notification.milestone,
                    "urgency": notification.urgency,
                    "sound": notification.sound,
                    "actions": notification.actions
                }
            })
        
        orchestrator.register_notification_callback(job_id, notification_callback)
        
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "job_id": job_id,
            "message": "Connected to notification stream"
        })
        
        # Keep connection alive
        while True:
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        logger.info(f"Notification WebSocket disconnected for job {job_id}")
    except Exception as e:
        logger.error(f"Error in notification WebSocket: {e}")


# ============================================================================
# Paused Run Management Endpoints
# ============================================================================

@app.get("/api/training/paused/{job_id}")
async def get_paused_run_info(job_id: str):
    """Get complete information about a paused training run"""
    try:
        from services.training_orchestration_service import get_training_orchestrator
        
        orchestrator = get_training_orchestrator()
        job = orchestrator.get_status(job_id)
        
        if job.state != "paused":
            raise HTTPException(
                status_code=400,
                detail=f"Job {job_id} is not in paused state. Current state: {job.state}"
            )
        
        # Verify required information is available
        if not job.paused_at:
            raise HTTPException(status_code=500, detail="Paused timestamp not available")
        if not job.started_at:
            raise HTTPException(status_code=500, detail="Started timestamp not available")
        if not job.current_metrics:
            raise HTTPException(status_code=500, detail="Current metrics not available")
        
        # Calculate elapsed time
        elapsed_seconds = (job.paused_at - job.started_at).total_seconds()
        
        # Build paused run information
        paused_run_info = {
            "job_id": job.job_id,
            "state": job.state.value,
            "paused_at": job.paused_at.isoformat(),
            "started_at": job.started_at.isoformat(),
            "elapsed_time": elapsed_seconds,
            "remaining_time_estimate": job.current_metrics.estimated_time_remaining,
            "current_step": job.current_metrics.step,
            "current_epoch": job.current_metrics.epoch,
            "current_loss": job.current_metrics.loss,
            "resource_usage": {
                "gpu_utilization": job.current_metrics.gpu_utilization,
                "gpu_memory_used": job.current_metrics.gpu_memory_used,
                "cpu_utilization": job.current_metrics.cpu_utilization,
                "ram_used": job.current_metrics.ram_used
            },
            "model_name": job.config.model_name,
            "dataset_path": job.config.dataset_path
        }
        
        return paused_run_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting paused run info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/training/resume/{job_id}")
async def resume_paused_training(job_id: str):
    """Resume a paused training run"""
    try:
        from services.training_orchestration_service import get_training_orchestrator
        
        orchestrator = get_training_orchestrator()
        orchestrator.resume_training(job_id)
        
        return {
            "job_id": job_id,
            "status": "resumed",
            "message": "Training resumed successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error resuming training: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/training/paused")
async def list_paused_runs():
    """Get list of all paused training runs"""
    try:
        from services.training_orchestration_service import get_training_orchestrator
        
        orchestrator = get_training_orchestrator()
        all_jobs = orchestrator.list_jobs()
        
        # Filter for paused jobs
        paused_jobs = [job for job in all_jobs if job.state.value == "paused"]
        
        # Build summary for each paused job
        paused_runs = []
        for job in paused_jobs:
            if job.paused_at and job.started_at and job.current_metrics:
                elapsed_seconds = (job.paused_at - job.started_at).total_seconds()
                
                paused_runs.append({
                    "job_id": job.job_id,
                    "model_name": job.config.model_name,
                    "paused_at": job.paused_at.isoformat(),
                    "elapsed_time": elapsed_seconds,
                    "current_step": job.current_metrics.step,
                    "current_epoch": job.current_metrics.epoch,
                    "current_loss": job.current_metrics.loss
                })
        
        return {
            "paused_runs": paused_runs,
            "count": len(paused_runs)
        }
        
    except Exception as e:
        logger.error(f"Error listing paused runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Model Versioning Endpoints
# ============================================================================

from services.model_versioning_service import get_model_versioning_service

class VersionCreateRequest(BaseModel):
    model_name: str
    checkpoint_path: str
    config: Dict
    metrics: Dict
    parent_version: Optional[str] = None


@app.post("/api/versions/create")
async def create_version(request: VersionCreateRequest):
    """Create a new model version"""
    try:
        versioning_service = get_model_versioning_service()
        version = versioning_service.create_version(
            model_name=request.model_name,
            checkpoint_path=request.checkpoint_path,
            config=request.config,
            metrics=request.metrics,
            parent_version=request.parent_version
        )
        
        return {
            "id": version.id,
            "model_name": version.model_name,
            "version": version.version,
            "timestamp": version.timestamp,
            "config": version.config,
            "metrics": version.metrics,
            "checkpoint_path": version.checkpoint_path,
            "size_bytes": version.size_bytes,
            "parent_version": version.parent_version
        }
    except Exception as e:
        logger.error(f"Error creating version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/versions/{model_name}")
async def list_versions(model_name: str):
    """List all versions for a model"""
    try:
        versioning_service = get_model_versioning_service()
        versions = versioning_service.list_versions(model_name)
        
        return {
            "model_name": model_name,
            "versions": [
                {
                    "id": v.id,
                    "version": v.version,
                    "timestamp": v.timestamp,
                    "config": v.config,
                    "metrics": v.metrics,
                    "size_bytes": v.size_bytes,
                    "parent_version": v.parent_version
                }
                for v in versions
            ]
        }
    except Exception as e:
        logger.error(f"Error listing versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/versions/{model_name}/latest")
async def get_latest_version(model_name: str):
    """Get the latest version of a model"""
    try:
        versioning_service = get_model_versioning_service()
        version = versioning_service.get_latest_version(model_name)
        
        if not version:
            raise HTTPException(status_code=404, detail="No versions found")
        
        return {
            "id": version.id,
            "model_name": version.model_name,
            "version": version.version,
            "timestamp": version.timestamp,
            "config": version.config,
            "metrics": version.metrics,
            "checkpoint_path": version.checkpoint_path,
            "size_bytes": version.size_bytes,
            "parent_version": version.parent_version
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/versions/{model_name}/compare/{version1}/{version2}")
async def compare_versions(model_name: str, version1: str, version2: str):
    """Compare two versions of a model"""
    try:
        versioning_service = get_model_versioning_service()
        comparison = versioning_service.compare_versions(model_name, version1, version2)
        
        if not comparison:
            raise HTTPException(status_code=404, detail="One or both versions not found")
        
        return {
            "version1": {
                "version": comparison.version1.version,
                "timestamp": comparison.version1.timestamp,
                "metrics": comparison.version1.metrics
            },
            "version2": {
                "version": comparison.version2.version,
                "timestamp": comparison.version2.timestamp,
                "metrics": comparison.version2.metrics
            },
            "config_diff": comparison.config_diff,
            "metric_diff": comparison.metric_diff,
            "performance_improvement": comparison.performance_improvement
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/versions/{model_name}/{version}")
async def delete_version(model_name: str, version: str):
    """Delete a specific version"""
    try:
        versioning_service = get_model_versioning_service()
        success = versioning_service.delete_version(model_name, version)
        
        if not success:
            raise HTTPException(status_code=404, detail="Version not found")
        
        return {"success": True, "message": f"Version {version} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/disk-space")
async def get_disk_space_info():
    """Get disk space information"""
    try:
        versioning_service = get_model_versioning_service()
        disk_info = versioning_service.get_disk_space_info()
        
        return {
            "total_bytes": disk_info.total_bytes,
            "used_bytes": disk_info.used_bytes,
            "available_bytes": disk_info.available_bytes,
            "percent_used": disk_info.percent_used,
            "versions_total_size": disk_info.versions_total_size,
            "low_space_threshold": disk_info.low_space_threshold,
            "should_prompt_cleanup": versioning_service.should_prompt_cleanup()
        }
    except Exception as e:
        logger.error(f"Error getting disk space info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cleanup-candidates")
async def get_cleanup_candidates(model_name: Optional[str] = None, keep_latest: int = 3):
    """Get versions that can be cleaned up"""
    try:
        versioning_service = get_model_versioning_service()
        candidates = versioning_service.get_cleanup_candidates(model_name, keep_latest)
        
        return {
            "candidates": [
                {
                    "id": v.id,
                    "model_name": v.model_name,
                    "version": v.version,
                    "timestamp": v.timestamp,
                    "size_bytes": v.size_bytes,
                    "metrics": v.metrics
                }
                for v in candidates
            ],
            "total_size": sum(v.size_bytes for v in candidates)
        }
    except Exception as e:
        logger.error(f"Error getting cleanup candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Inference Playground Endpoints
# ============================================================================

class AutoLoadRequest(BaseModel):
    model_version_id: str
    use_case: str


@app.post("/api/inference/auto-load")
async def auto_load_model_for_inference(request: AutoLoadRequest):
    """
    Automatically load a completed model into the inference playground.
    Validates: Requirements 7.1
    """
    try:
        inference_service = get_inference_service()
        use_case_enum = UseCase(request.use_case)
        
        result = inference_service.auto_load_model(
            model_version_id=request.model_version_id,
            use_case=use_case_enum
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error auto-loading model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/inference/prompts/{use_case}")
async def get_example_prompts(use_case: str):
    """
    Generate example prompts for a specific use case.
    Validates: Requirements 7.2
    """
    try:
        inference_service = get_inference_service()
        use_case_enum = UseCase(use_case)
        
        prompts = inference_service.generate_example_prompts(use_case_enum)
        
        return {
            "use_case": use_case,
            "prompts": prompts
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid use case: {use_case}")
    except Exception as e:
        logger.error(f"Error generating prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class InferenceGenerateRequest(BaseModel):
    prompt: str
    model_version_id: str
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9


@app.post("/api/inference/generate")
async def generate_inference(request: InferenceGenerateRequest):
    """
    Generate inference from a loaded model.
    Validates: Requirements 7.3
    """
    try:
        from services.inference_service import InferenceRequest
        
        inference_service = get_inference_service()
        
        inference_request = InferenceRequest(
            prompt=request.prompt,
            model_version_id=request.model_version_id,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p
        )
        
        result = inference_service.generate_inference(inference_request)
        
        return {
            "prompt": result.prompt,
            "response": result.response,
            "model_version_id": result.model_version_id,
            "timestamp": result.timestamp.isoformat(),
            "generation_time_seconds": result.generation_time_seconds,
            "tokens_generated": result.tokens_generated
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating inference: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ComparisonRequest(BaseModel):
    prompt: str
    fine_tuned_model_id: str
    base_model_id: str


@app.post("/api/inference/compare")
async def compare_models(request: ComparisonRequest):
    """
    Generate side-by-side comparison with base model.
    Validates: Requirements 7.4
    """
    try:
        inference_service = get_inference_service()
        
        result = inference_service.compare_with_base_model(
            prompt=request.prompt,
            fine_tuned_model_id=request.fine_tuned_model_id,
            base_model_id=request.base_model_id
        )
        
        return {
            "prompt": result.prompt,
            "fine_tuned_output": result.fine_tuned_output,
            "base_model_output": result.base_model_output,
            "fine_tuned_model_id": result.fine_tuned_model_id,
            "base_model_id": result.base_model_id,
            "timestamp": result.timestamp.isoformat()
        }
    except Exception as e:
        logger.error(f"Error comparing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class SaveConversationRequest(BaseModel):
    conversation_id: str
    role: str  # 'user' or 'assistant'
    content: str
    use_case: str
    model_version_id: str


@app.post("/api/inference/conversation/save")
async def save_conversation_message(request: SaveConversationRequest):
    """
    Save a message to conversation history.
    Validates: Requirements 7.5
    """
    try:
        from services.inference_service import ConversationMessage
        from datetime import datetime
        
        inference_service = get_inference_service()
        use_case_enum = UseCase(request.use_case)
        
        message = ConversationMessage(
            role=request.role,
            content=request.content,
            timestamp=datetime.now(),
            model_version_id=request.model_version_id
        )
        
        conversation = inference_service.save_conversation(
            conversation_id=request.conversation_id,
            message=message,
            use_case=use_case_enum,
            model_version_id=request.model_version_id
        )
        
        return {
            "conversation_id": conversation.id,
            "message_count": len(conversation.messages),
            "use_case": conversation.use_case.value,
            "updated_at": conversation.updated_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/inference/conversation/{conversation_id}")
async def get_conversation_history(conversation_id: str):
    """Get a conversation history"""
    try:
        inference_service = get_inference_service()
        conversation = inference_service.get_conversation(conversation_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "id": conversation.id,
            "use_case": conversation.use_case.value,
            "model_version_id": conversation.model_version_id,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat(),
                    "model_version_id": m.model_version_id
                }
                for m in conversation.messages
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/inference/conversations")
async def list_conversations(
    model_version_id: Optional[str] = None,
    use_case: Optional[str] = None
):
    """List conversation histories with optional filtering"""
    try:
        inference_service = get_inference_service()
        use_case_enum = UseCase(use_case) if use_case else None
        
        conversations = inference_service.list_conversations(
            model_version_id=model_version_id,
            use_case=use_case_enum
        )
        
        return {
            "conversations": [
                {
                    "id": c.id,
                    "use_case": c.use_case.value,
                    "model_version_id": c.model_version_id,
                    "message_count": len(c.messages),
                    "created_at": c.created_at.isoformat(),
                    "updated_at": c.updated_at.isoformat()
                }
                for c in conversations
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/inference/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation history"""
    try:
        inference_service = get_inference_service()
        success = inference_service.delete_conversation(conversation_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"success": True, "message": f"Conversation {conversation_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Configuration Preset Endpoints
# ============================================================================

from services.preset_service import get_preset_service, ConfigurationPreset


class PresetSaveRequest(BaseModel):
    """Request to save a new configuration preset"""
    id: str
    name: str
    description: str = ""
    tags: List[str] = []
    
    # Model configuration
    model_name: str
    model_path: str = ""
    
    # Dataset configuration
    dataset_id: str = ""
    dataset_path: str = ""
    
    # PEFT Settings
    peft_method: str = "lora"
    lora_r: int
    lora_alpha: int
    lora_dropout: float
    target_modules: List[str]
    
    # Training Hyperparameters
    learning_rate: float
    batch_size: int
    gradient_accumulation: int
    epochs: int
    max_steps: int = 0
    warmup_steps: int = 0
    
    # Optimization
    optimizer: str = "adamw"
    scheduler: str = "linear"
    weight_decay: float = 0.0
    max_grad_norm: float = 1.0
    
    # Precision
    precision: str = "fp16"
    quantization: Optional[str] = None
    
    # Checkpointing
    save_steps: int = 500
    save_total: int = 3
    
    # Validation
    eval_steps: int = 500
    eval_strategy: str = "steps"


@app.post("/api/presets/save")
async def save_preset(request: PresetSaveRequest):
    """
    Save a configuration preset with all parameters.
    Validates: Requirements 8.1, 8.2
    """
    try:
        from datetime import datetime
        
        preset_service = get_preset_service()
        
        preset = ConfigurationPreset(
            id=request.id,
            name=request.name,
            description=request.description,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            tags=request.tags,
            model_name=request.model_name,
            model_path=request.model_path,
            dataset_id=request.dataset_id,
            dataset_path=request.dataset_path,
            peft_method=request.peft_method,
            lora_r=request.lora_r,
            lora_alpha=request.lora_alpha,
            lora_dropout=request.lora_dropout,
            target_modules=request.target_modules,
            learning_rate=request.learning_rate,
            batch_size=request.batch_size,
            gradient_accumulation=request.gradient_accumulation,
            epochs=request.epochs,
            max_steps=request.max_steps,
            warmup_steps=request.warmup_steps,
            optimizer=request.optimizer,
            scheduler=request.scheduler,
            weight_decay=request.weight_decay,
            max_grad_norm=request.max_grad_norm,
            precision=request.precision,
            quantization=request.quantization,
            save_steps=request.save_steps,
            save_total=request.save_total,
            eval_steps=request.eval_steps,
            eval_strategy=request.eval_strategy
        )
        
        saved_preset = preset_service.save_preset(preset)
        
        return {
            "success": True,
            "preset": saved_preset.dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error saving preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/presets")
async def list_presets(search: Optional[str] = None, tags: Optional[str] = None):
    """
    List all presets with optional search and filtering.
    Validates: Requirements 8.3
    """
    try:
        preset_service = get_preset_service()
        
        tag_list = tags.split(",") if tags else None
        
        presets = preset_service.list_presets(search=search, tags=tag_list)
        
        return {
            "presets": [preset.dict() for preset in presets],
            "count": len(presets)
        }
    except Exception as e:
        logger.error(f"Error listing presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/presets/{preset_id}")
async def get_preset(preset_id: str):
    """
    Get a specific preset by ID.
    Validates: Requirements 8.4
    """
    try:
        preset_service = get_preset_service()
        preset = preset_service.load_preset(preset_id)
        
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset not found: {preset_id}")
        
        return preset.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/presets/{preset_id}")
async def delete_preset(preset_id: str):
    """Delete a configuration preset"""
    try:
        preset_service = get_preset_service()
        success = preset_service.delete_preset(preset_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Preset not found: {preset_id}")
        
        return {"success": True, "message": f"Preset {preset_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/presets/{preset_id}/export")
async def export_preset(preset_id: str):
    """
    Export a preset to shareable JSON format.
    Validates: Requirements 8.3
    """
    try:
        preset_service = get_preset_service()
        export_data = preset_service.export_preset(preset_id)
        
        if not export_data:
            raise HTTPException(status_code=404, detail=f"Preset not found: {preset_id}")
        
        return export_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class PresetImportRequest(BaseModel):
    """Request to import a preset from JSON"""
    import_data: Dict
    new_id: Optional[str] = None


@app.post("/api/presets/import")
async def import_preset(request: PresetImportRequest):
    """
    Import a preset from JSON with validation.
    Validates: Requirements 8.4, 8.5
    """
    try:
        preset_service = get_preset_service()
        
        preset = preset_service.import_preset(
            import_data=request.import_data,
            new_id=request.new_id
        )
        
        return {
            "success": True,
            "preset": preset.dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid import data: {str(e)}")
    except Exception as e:
        logger.error(f"Error importing preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class PresetUpdateRequest(BaseModel):
    """Request to update a preset"""
    updates: Dict


@app.patch("/api/presets/{preset_id}")
async def update_preset(preset_id: str, request: PresetUpdateRequest):
    """Update an existing preset"""
    try:
        preset_service = get_preset_service()
        
        updated_preset = preset_service.update_preset(preset_id, request.updates)
        
        if not updated_preset:
            raise HTTPException(status_code=404, detail=f"Preset not found: {preset_id}")
        
        return {
            "success": True,
            "preset": updated_preset.dict()
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Training Run Comparison Endpoints
# ============================================================================

from services.comparison_service import (
    get_comparison_service,
    TrainingRunSummary
)


class ComparisonRequest(BaseModel):
    """Request to compare training runs"""
    job_ids: List[str]
    include_charts: bool = True
    include_config_diff: bool = True


class AddRunRequest(BaseModel):
    """Request to add a training run to comparison cache"""
    job_id: str
    model_name: str
    dataset_name: str
    final_loss: float
    best_val_loss: Optional[float] = None
    final_learning_rate: float = 0.0
    total_steps: int = 0
    epochs_completed: int = 0
    training_time_seconds: float = 0.0
    config: Dict[str, Any] = {}
    quality_score: Optional[float] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@app.post("/api/comparison/add-run")
async def add_run_to_comparison(request: AddRunRequest):
    """
    Add a training run to the comparison cache.
    This should be called when a training run completes.
    """
    try:
        comparison_service = get_comparison_service()
        
        # Parse datetime strings if provided
        started_at = None
        completed_at = None
        if request.started_at:
            from datetime import datetime
            started_at = datetime.fromisoformat(request.started_at)
        if request.completed_at:
            from datetime import datetime
            completed_at = datetime.fromisoformat(request.completed_at)
        
        # Create training run summary
        run = TrainingRunSummary(
            job_id=request.job_id,
            model_name=request.model_name,
            dataset_name=request.dataset_name,
            final_loss=request.final_loss,
            best_val_loss=request.best_val_loss,
            final_learning_rate=request.final_learning_rate,
            total_steps=request.total_steps,
            epochs_completed=request.epochs_completed,
            training_time_seconds=request.training_time_seconds,
            config=request.config,
            quality_score=request.quality_score,
            started_at=started_at,
            completed_at=completed_at
        )
        
        comparison_service.add_run(run)
        
        return {
            "success": True,
            "message": f"Run {request.job_id} added to comparison cache"
        }
    except Exception as e:
        logger.error(f"Error adding run to comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/comparison/runs")
async def list_comparison_runs():
    """
    Get all training runs available for comparison.
    """
    try:
        comparison_service = get_comparison_service()
        runs = comparison_service.list_all_runs()
        
        return {
            "success": True,
            "runs": [run.to_dict() for run in runs],
            "count": len(runs)
        }
    except Exception as e:
        logger.error(f"Error listing comparison runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/comparison/compare")
async def compare_training_runs(request: ComparisonRequest):
    """
    Compare multiple training runs (2-5 runs).
    
    Returns:
    - runs: List of training run summaries
    - charts: Comparison charts for visualization
    - best_performers: Best performing runs for each metric
    - config_diffs: Configuration differences (only for 2 runs)
    """
    try:
        comparison_service = get_comparison_service()
        
        # Validate job_ids
        if not request.job_ids or len(request.job_ids) < 2:
            raise HTTPException(
                status_code=400,
                detail="Must provide at least 2 job IDs for comparison"
            )
        
        if len(request.job_ids) > 5:
            raise HTTPException(
                status_code=400,
                detail="Cannot compare more than 5 runs at once"
            )
        
        # Perform comparison
        result = comparison_service.compare_runs(
            job_ids=request.job_ids,
            include_charts=request.include_charts,
            include_config_diff=request.include_config_diff
        )
        
        return {
            "success": True,
            "comparison": result.to_dict()
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error comparing training runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/comparison/run/{job_id}")
async def get_comparison_run(job_id: str):
    """
    Get a specific training run from the comparison cache.
    """
    try:
        comparison_service = get_comparison_service()
        run = comparison_service.get_run(job_id)
        
        if not run:
            raise HTTPException(status_code=404, detail=f"Run not found: {job_id}")
        
        return {
            "success": True,
            "run": run.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting comparison run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/comparison/clear")
async def clear_comparison_cache():
    """
    Clear all training runs from the comparison cache.
    """
    try:
        comparison_service = get_comparison_service()
        comparison_service.clear_cache()
        
        return {
            "success": True,
            "message": "Comparison cache cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing comparison cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Cost Calculator Endpoints
class CostEstimateRequest(BaseModel):
    training_time_hours: float
    gpu_name: str
    num_gpus: int = 1
    electricity_rate_per_kwh: Optional[float] = None
    region: str = "default"
    utilization: float = 0.85


@app.post("/api/cost/estimate")
async def calculate_cost_estimates(request: CostEstimateRequest):
    """
    Calculate complete cost and carbon footprint estimates.
    
    Validates: Requirements 9.2, 9.3, 9.4
    """
    try:
        from services.cost_calculator_service import get_cost_calculator
        
        cost_calculator = get_cost_calculator()
        
        # Calculate complete estimates
        estimates = cost_calculator.calculate_complete_estimates(
            training_time_hours=request.training_time_hours,
            gpu_name=request.gpu_name,
            num_gpus=request.num_gpus,
            electricity_rate_per_kwh=request.electricity_rate_per_kwh,
            region=request.region,
            utilization=request.utilization
        )
        
        # Format for response
        formatted = cost_calculator.format_cost_summary(estimates)
        
        return {
            "gpu_hours": estimates.gpu_hours,
            "electricity_cost_usd": estimates.electricity_cost_usd,
            "electricity_rate_per_kwh": estimates.electricity_rate_per_kwh,
            "carbon_footprint_kg": estimates.carbon_footprint_kg,
            "carbon_intensity_g_per_kwh": estimates.carbon_intensity_g_per_kwh,
            "total_energy_kwh": estimates.total_energy_kwh,
            "confidence": estimates.confidence,
            "formatted": formatted
        }
    except Exception as e:
        logger.error(f"Error calculating cost estimates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cost/electricity-rate/{region}")
async def get_default_electricity_rate(region: str = "default"):
    """
    Get default electricity rate for a region.
    
    Validates: Requirements 9.4
    """
    try:
        from services.cost_calculator_service import get_cost_calculator
        
        cost_calculator = get_cost_calculator()
        rate = cost_calculator.get_default_electricity_rate(region)
        
        return {
            "region": region,
            "electricity_rate_per_kwh": rate
        }
    except Exception as e:
        logger.error(f"Error getting electricity rate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cost/carbon-intensity/{region}")
async def get_carbon_intensity(region: str = "default"):
    """
    Get carbon intensity for a region.
    
    Validates: Requirements 9.2
    """
    try:
        from services.cost_calculator_service import get_cost_calculator
        
        cost_calculator = get_cost_calculator()
        intensity = cost_calculator.get_carbon_intensity(region)
        
        return {
            "region": region,
            "carbon_intensity_g_per_kwh": intensity
        }
    except Exception as e:
        logger.error(f"Error getting carbon intensity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cost/gpu-power/{gpu_name}")
async def get_gpu_power_profile(gpu_name: str):
    """
    Get power consumption profile for a GPU model.
    
    Validates: Requirements 9.2
    """
    try:
        from services.cost_calculator_service import get_cost_calculator
        
        cost_calculator = get_cost_calculator()
        profile = cost_calculator.get_gpu_power_profile(gpu_name)
        
        return {
            "model_name": profile.model_name,
            "tdp_watts": profile.tdp_watts,
            "avg_power_watts": profile.avg_power_watts,
            "idle_power_watts": profile.idle_power_watts
        }
    except Exception as e:
        logger.error(f"Error getting GPU power profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Weights & Biases Integration Endpoints
# ============================================================================

class WandBConfigRequest(BaseModel):
    """Request model for WandB configuration"""
    enabled: bool = True
    project_name: str = "peft-studio"
    entity: Optional[str] = None
    api_key: Optional[str] = None
    tags: Optional[List[str]] = None


class WandBStartRunRequest(BaseModel):
    """Request model for starting a WandB run"""
    job_id: str
    model_name: str
    dataset_name: str
    use_case: str
    run_name: Optional[str] = None
    config: Dict[str, Any]


@app.post("/api/wandb/configure")
async def configure_wandb_integration(request: WandBConfigRequest):
    """
    Configure Weights & Biases integration.
    
    Validates: Requirements 11.1
    """
    try:
        from services.wandb_integration_service import configure_wandb
        
        wandb_service = configure_wandb(
            enabled=request.enabled,
            project_name=request.project_name,
            entity=request.entity,
            api_key=request.api_key,
            tags=request.tags or []
        )
        
        return {
            "success": True,
            "enabled": wandb_service.is_enabled(),
            "available": wandb_service.is_available,
            "project_name": wandb_service.config.project_name,
            "message": "WandB integration configured successfully" if wandb_service.is_enabled() 
                      else "WandB integration disabled or not available"
        }
    except Exception as e:
        logger.error(f"Error configuring WandB: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/wandb/status")
async def get_wandb_status():
    """
    Get current WandB integration status.
    
    Validates: Requirements 11.1
    """
    try:
        from services.wandb_integration_service import get_wandb_service
        
        wandb_service = get_wandb_service()
        
        return {
            "enabled": wandb_service.is_enabled(),
            "available": wandb_service.is_available,
            "project_name": wandb_service.config.project_name,
            "entity": wandb_service.config.entity,
            "active_runs": wandb_service.get_active_runs()
        }
    except Exception as e:
        logger.error(f"Error getting WandB status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/wandb/start-run")
async def start_wandb_run(request: WandBStartRunRequest):
    """
    Start a WandB run for experiment tracking.
    
    Validates: Requirements 11.1, 11.2
    """
    try:
        from services.wandb_integration_service import get_wandb_service, ExperimentMetadata
        
        wandb_service = get_wandb_service()
        
        if not wandb_service.is_enabled():
            return {
                "success": False,
                "message": "WandB integration is not enabled"
            }
        
        metadata = ExperimentMetadata(
            job_id=request.job_id,
            model_name=request.model_name,
            dataset_name=request.dataset_name,
            use_case=request.use_case,
            run_name=request.run_name
        )
        
        success = wandb_service.start_run(
            job_id=request.job_id,
            metadata=metadata,
            config=request.config
        )
        
        run_url = wandb_service.get_run_url(request.job_id) if success else None
        
        return {
            "success": success,
            "job_id": request.job_id,
            "run_url": run_url,
            "message": "WandB run started successfully" if success else "Failed to start WandB run"
        }
    except Exception as e:
        logger.error(f"Error starting WandB run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/wandb/run-url/{job_id}")
async def get_wandb_run_url(job_id: str):
    """
    Get the WandB dashboard URL for a specific run.
    
    Validates: Requirements 11.1
    """
    try:
        from services.wandb_integration_service import get_wandb_service
        
        wandb_service = get_wandb_service()
        run_url = wandb_service.get_run_url(job_id)
        
        if run_url:
            return {
                "job_id": job_id,
                "run_url": run_url
            }
        else:
            raise HTTPException(status_code=404, detail=f"No active WandB run found for job {job_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting WandB run URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/wandb/finish-run/{job_id}")
async def finish_wandb_run(job_id: str, exit_code: int = 0, summary: Optional[Dict[str, Any]] = None):
    """
    Finish a WandB run.
    
    Validates: Requirements 11.1
    """
    try:
        from services.wandb_integration_service import get_wandb_service
        
        wandb_service = get_wandb_service()
        
        success = wandb_service.finish_run(
            job_id=job_id,
            exit_code=exit_code,
            summary=summary or {}
        )
        
        return {
            "success": success,
            "job_id": job_id,
            "message": "WandB run finished successfully" if success else "Failed to finish WandB run"
        }
    except Exception as e:
        logger.error(f"Error finishing WandB run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/wandb/compare")
async def get_wandb_comparison_url(job_ids: str):
    """
    Get a WandB comparison URL for multiple runs.
    
    Args:
        job_ids: Comma-separated list of job IDs
    
    Validates: Requirements 11.2
    """
    try:
        from services.wandb_integration_service import get_wandb_service
        
        wandb_service = get_wandb_service()
        
        # Parse job IDs
        job_id_list = [jid.strip() for jid in job_ids.split(',')]
        
        if len(job_id_list) < 2:
            raise HTTPException(status_code=400, detail="Must provide at least 2 job IDs for comparison")
        
        comparison_url = wandb_service.compare_runs(job_id_list)
        
        if comparison_url:
            return {
                "job_ids": job_id_list,
                "comparison_url": comparison_url
            }
        else:
            return {
                "job_ids": job_id_list,
                "comparison_url": None,
                "message": "WandB integration not enabled or comparison URL not available"
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating WandB comparison URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Cloud Platform Integration Endpoints
# ============================================================================

from services.cloud_platform_service import (
    get_cloud_platform_service,
    PlatformType,
    GPUType
)


class CloudInstancesRequest(BaseModel):
    """Request to get cloud instances"""
    gpu_type: Optional[str] = None
    min_memory_gb: Optional[int] = None


@app.post("/api/cloud/instances")
async def get_cloud_instances(request: CloudInstancesRequest):
    """
    Get available cloud GPU instances across all platforms.
    Validates: Requirements 9.2
    """
    try:
        cloud_service = get_cloud_platform_service()
        
        # Convert gpu_type string to enum if provided
        gpu_type_enum = None
        if request.gpu_type:
            try:
                gpu_type_enum = GPUType(request.gpu_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid GPU type: {request.gpu_type}"
                )
        
        # Get all cloud instances
        instances = cloud_service.get_all_cloud_instances(
            gpu_type=gpu_type_enum,
            min_memory_gb=request.min_memory_gb
        )
        
        return {
            "instances": [
                {
                    "platform": inst.platform.value,
                    "gpu_type": inst.gpu_type.value,
                    "gpu_count": inst.gpu_count,
                    "memory_gb": inst.memory_gb,
                    "vcpus": inst.vcpus,
                    "ram_gb": inst.ram_gb,
                    "storage_gb": inst.storage_gb,
                    "hourly_rate_usd": inst.hourly_rate_usd,
                    "availability": inst.availability,
                    "region": inst.region
                }
                for inst in instances
            ],
            "count": len(instances)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cloud instances: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cloud/platforms/{platform}")
async def get_platform_instances(
    platform: str,
    gpu_type: Optional[str] = None,
    min_memory_gb: Optional[int] = None
):
    """
    Get instances for a specific cloud platform.
    Validates: Requirements 9.2
    """
    try:
        cloud_service = get_cloud_platform_service()
        
        # Validate platform
        try:
            platform_enum = PlatformType(platform)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platform: {platform}. Must be one of: runpod, lambda_labs, together_ai"
            )
        
        # Convert gpu_type if provided
        gpu_type_enum = None
        if gpu_type:
            try:
                gpu_type_enum = GPUType(gpu_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid GPU type: {gpu_type}"
                )
        
        # Get instances for the platform
        if platform_enum == PlatformType.RUNPOD:
            instances = cloud_service.get_runpod_instances(gpu_type_enum, min_memory_gb)
        elif platform_enum == PlatformType.LAMBDA_LABS:
            instances = cloud_service.get_lambda_labs_instances(gpu_type_enum, min_memory_gb)
        elif platform_enum == PlatformType.TOGETHER_AI:
            instances = cloud_service.get_together_ai_instances(gpu_type_enum, min_memory_gb)
        else:
            raise HTTPException(status_code=400, detail="Invalid platform")
        
        return {
            "platform": platform,
            "instances": [
                {
                    "gpu_type": inst.gpu_type.value,
                    "gpu_count": inst.gpu_count,
                    "memory_gb": inst.memory_gb,
                    "vcpus": inst.vcpus,
                    "ram_gb": inst.ram_gb,
                    "storage_gb": inst.storage_gb,
                    "hourly_rate_usd": inst.hourly_rate_usd,
                    "availability": inst.availability,
                    "region": inst.region
                }
                for inst in instances
            ],
            "count": len(instances)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting platform instances: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class CostComparisonRequest(BaseModel):
    """Request to compare costs across platforms"""
    training_hours: float
    local_gpu_type: Optional[str] = None
    local_electricity_cost: Optional[float] = None
    min_memory_gb: Optional[int] = None


@app.post("/api/cloud/compare-costs")
async def compare_platform_costs(request: CostComparisonRequest):
    """
    Compare training costs across all platforms.
    Validates: Requirements 9.2
    """
    try:
        cloud_service = get_cloud_platform_service()
        
        # Convert local GPU type if provided
        local_gpu_enum = None
        if request.local_gpu_type:
            try:
                local_gpu_enum = GPUType(request.local_gpu_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid local GPU type: {request.local_gpu_type}"
                )
        
        # Get cost comparison
        comparison = cloud_service.compare_costs(
            training_hours=request.training_hours,
            local_gpu_type=local_gpu_enum,
            local_electricity_cost=request.local_electricity_cost,
            min_memory_gb=request.min_memory_gb
        )
        
        # Format the comparison
        formatted = cloud_service.format_cost_comparison(comparison)
        
        return formatted
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing costs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cloud/setup-instructions/{platform}")
async def get_platform_setup_instructions(platform: str):
    """
    Get setup instructions for a cloud platform.
    """
    try:
        cloud_service = get_cloud_platform_service()
        
        # Validate platform
        try:
            platform_enum = PlatformType(platform)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platform: {platform}. Must be one of: runpod, lambda_labs, together_ai"
            )
        
        instructions = cloud_service.get_platform_setup_instructions(platform_enum)
        
        return instructions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting setup instructions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cloud/gpu-types")
async def list_gpu_types():
    """
    Get list of available GPU types across platforms.
    """
    return {
        "gpu_types": [gpu.value for gpu in GPUType]
    }


@app.get("/api/cloud/platforms")
async def list_platforms():
    """
    Get list of supported cloud platforms.
    """
    return {
        "platforms": [
            {
                "id": "runpod",
                "name": "RunPod",
                "description": "Fast deployment with flexible billing",
                "features": ["Per-minute billing", "Good GPU availability", "Easy to use"]
            },
            {
                "id": "lambda_labs",
                "name": "Lambda Labs",
                "description": "Lowest prices for A100/H100 GPUs",
                "features": ["Best prices", "Fast NVMe storage", "Pre-configured ML environments"]
            },
            {
                "id": "together_ai",
                "name": "Together AI",
                "description": "Serverless endpoints with instant availability",
                "features": ["Instant availability", "Auto-scaling", "Pay per use"]
            }
        ]
    }


# ============================================================================
# Multi-Run Management Endpoints
# Requirements: 16.1, 16.2, 16.3, 16.4, 16.5
# ============================================================================

from services.multi_run_service import (
    get_multi_run_manager,
    RunFilter,
    RunStatus as MultiRunStatus
)
from database import get_db


class RunFilterRequest(BaseModel):
    """Request model for run filtering"""
    status: Optional[List[str]] = None
    provider: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    model_name: Optional[str] = None
    job_ids: Optional[List[str]] = None


@app.get("/api/runs/active")
async def get_active_runs():
    """
    Get all active (running or paused) training runs.
    
    Requirements: 16.2
    """
    try:
        multi_run_manager = get_multi_run_manager()
        db = next(get_db())
        
        try:
            active_runs = multi_run_manager.get_active_runs(db)
            return {
                "runs": [run.to_dict() for run in active_runs],
                "count": len(active_runs)
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error getting active runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/runs/history")
async def get_run_history(filter_request: RunFilterRequest, limit: int = 100, offset: int = 0):
    """
    Get run history with optional filtering.
    
    Requirements: 16.4
    """
    try:
        multi_run_manager = get_multi_run_manager()
        db = next(get_db())
        
        try:
            # Convert request to filter
            from datetime import datetime
            filter_criteria = RunFilter(
                status=filter_request.status,
                provider=filter_request.provider,
                date_from=datetime.fromisoformat(filter_request.date_from) if filter_request.date_from else None,
                date_to=datetime.fromisoformat(filter_request.date_to) if filter_request.date_to else None,
                model_name=filter_request.model_name,
                job_ids=filter_request.job_ids
            )
            
            runs = multi_run_manager.get_run_history(db, filter_criteria, limit, offset)
            
            return {
                "runs": [run.to_dict() for run in runs],
                "count": len(runs),
                "limit": limit,
                "offset": offset
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error getting run history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/runs/stats")
async def get_concurrent_stats():
    """
    Get statistics about concurrent runs.
    
    Requirements: 16.2
    """
    try:
        multi_run_manager = get_multi_run_manager()
        db = next(get_db())
        
        try:
            stats = multi_run_manager.get_concurrent_stats(db)
            return stats.to_dict()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error getting concurrent stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/runs/{job_id}")
async def get_run_details(job_id: str):
    """
    Get detailed information about a specific run.
    
    Requirements: 16.3
    """
    try:
        multi_run_manager = get_multi_run_manager()
        db = next(get_db())
        
        try:
            details = multi_run_manager.get_run_details(job_id, db)
            
            if details is None:
                raise HTTPException(status_code=404, detail=f"Run not found: {job_id}")
            
            return details
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting run details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/runs/{job_id}/cancel")
async def cancel_run(job_id: str):
    """
    Cancel a running or paused training run.
    
    Requirements: 16.5
    """
    try:
        multi_run_manager = get_multi_run_manager()
        db = next(get_db())
        
        try:
            success = multi_run_manager.cancel_run(job_id, db)
            
            if not success:
                raise HTTPException(status_code=500, detail=f"Failed to cancel run: {job_id}")
            
            return {"success": True, "message": f"Run {job_id} cancelled successfully"}
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/runs/{job_id}")
async def cleanup_run(job_id: str):
    """
    Cleanup resources for a completed/failed/stopped run.
    
    Requirements: 16.5
    """
    try:
        multi_run_manager = get_multi_run_manager()
        db = next(get_db())
        
        try:
            success = multi_run_manager.cleanup_run(job_id, db)
            
            if not success:
                raise HTTPException(status_code=500, detail=f"Failed to cleanup run: {job_id}")
            
            return {"success": True, "message": f"Run {job_id} cleaned up successfully"}
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Performance Monitoring Endpoints
# ============================================================================

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Shutting down PEFT Studio Backend...")
    
    # Cleanup performance service
    from services.performance_service import get_performance_service
    perf_service = get_performance_service()
    await perf_service.cleanup()
    
    logger.info("Shutdown complete")


@app.get("/api/performance/metrics")
async def get_performance_metrics():
    """
    Get comprehensive performance metrics.
    Validates: Requirements 14.4, 14.5
    """
    try:
        from services.performance_service import get_performance_service
        
        perf_service = get_performance_service()
        metrics = perf_service.get_all_metrics()
        
        return metrics
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/performance/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    try:
        from services.performance_service import get_request_cache
        
        cache = get_request_cache()
        stats = cache.get_stats()
        
        return stats
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/performance/cache/clear")
async def clear_cache():
    """Clear request cache."""
    try:
        from services.performance_service import get_request_cache
        
        cache = get_request_cache()
        await cache.clear()
        
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/performance/database/stats")
async def get_database_stats():
    """Get database query statistics."""
    try:
        from services.performance_service import get_db_optimizer
        
        optimizer = get_db_optimizer()
        stats = optimizer.get_query_stats()
        
        return stats
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/performance/database/slow-queries")
async def get_slow_queries(limit: int = 10):
    """Get recent slow database queries."""
    try:
        from services.performance_service import get_db_optimizer
        
        optimizer = get_db_optimizer()
        slow_queries = optimizer.get_slow_queries(limit=limit)
        
        return {
            "slow_queries": slow_queries,
            "count": len(slow_queries)
        }
    except Exception as e:
        logger.error(f"Error getting slow queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/performance/endpoints")
async def get_endpoint_performance():
    """Get performance metrics for all endpoints."""
    try:
        from services.performance_service import get_performance_monitor
        
        monitor = get_performance_monitor()
        slowest = monitor.get_slowest_endpoints(limit=20)
        
        return {
            "slowest_endpoints": slowest
        }
    except Exception as e:
        logger.error(f"Error getting endpoint performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/performance/system")
async def get_system_metrics():
    """Get system resource metrics."""
    try:
        from services.performance_service import get_performance_monitor
        
        monitor = get_performance_monitor()
        metrics = monitor.get_system_metrics()
        
        return metrics
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/performance/recommendations")
async def get_optimization_recommendations():
    """Get performance optimization recommendations."""
    try:
        from services.performance_service import get_performance_service
        
        perf_service = get_performance_service()
        recommendations = perf_service.get_optimization_recommendations()
        
        return {
            "recommendations": recommendations,
            "count": len(recommendations)
        }
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)


# Error Handling Endpoints
class ErrorFormatRequest(BaseModel):
    error_type: str
    error_message: str
    context: Optional[Dict] = {}

class AutoFixRequest(BaseModel):
    action_data: Dict
    context: Dict

@app.post("/api/errors/format")
async def format_error_endpoint(request: ErrorFormatRequest):
    """Format an error into plain language with suggested actions"""
    try:
        from services.error_service import get_error_service
        
        error_service = get_error_service()
        
        # Create an exception from the request
        error_class = globals().get(request.error_type, Exception)
        error = error_class(request.error_message)
        
        # Format the error
        formatted = error_service.format_error(error, request.context)
        
        return {
            "title": formatted.title,
            "what_happened": formatted.what_happened,
            "why_it_happened": formatted.why_it_happened,
            "actions": [
                {
                    "description": action.description,
                    "automatic": action.automatic,
                    "action_type": action.action_type,
                    "action_data": action.action_data
                }
                for action in formatted.actions
            ],
            "category": formatted.category.value,
            "severity": formatted.severity.value,
            "help_link": formatted.help_link,
            "auto_recoverable": formatted.auto_recoverable
        }
    except Exception as e:
        logger.error(f"Error formatting error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/errors/auto-fix")
async def execute_auto_fix_endpoint(request: AutoFixRequest):
    """Execute an automatic fix for an error"""
    try:
        from services.error_service import get_error_service, ErrorAction
        
        error_service = get_error_service()
        
        # Create an ErrorAction from the request
        action = ErrorAction(
            description=request.action_data.get('description', ''),
            automatic=True,
            action_type='auto_fix',
            action_data=request.action_data
        )
        
        # Execute the auto-fix
        success = error_service.execute_auto_fix(action, request.context)
        
        return {"success": success}
    except Exception as e:
        logger.error(f"Error executing auto-fix: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Model Export Endpoints
# ============================================================================

from services.export_service import get_model_exporter, ExportFormat

class ModelExportRequest(BaseModel):
    """Request to export a model"""
    model_path: str
    format: str  # 'huggingface', 'ollama', 'gguf', 'lmstudio'
    model_name: str
    metadata: Optional[Dict[str, Any]] = None
    quantization: Optional[str] = None
    merge_adapters: bool = True


@app.post("/api/export/model")
async def export_model_endpoint(request: ModelExportRequest):
    """
    Export a model to the specified format.
    Validates: Requirements 15.1, 15.2, 15.3, 15.4
    """
    try:
        exporter = get_model_exporter()
        
        # Validate format
        valid_formats = ['huggingface', 'ollama', 'gguf', 'lmstudio']
        if request.format not in valid_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}"
            )
        
        # Export the model
        result = exporter.export_model(
            model_path=request.model_path,
            format=request.format,
            model_name=request.model_name,
            metadata=request.metadata,
            quantization=request.quantization,
            merge_adapters=request.merge_adapters
        )
        
        return {
            "success": result.success,
            "format": result.format,
            "output_path": result.output_path,
            "artifacts": result.artifacts,
            "size_bytes": result.size_bytes,
            "message": result.message,
            "verification_passed": result.verification_passed,
            "verification_details": result.verification_details
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ExportVerificationRequest(BaseModel):
    """Request to verify an export"""
    export_path: str
    format: str


@app.post("/api/export/verify")
async def verify_export_endpoint(request: ExportVerificationRequest):
    """
    Verify an exported model.
    Validates: Requirements 15.5
    """
    try:
        exporter = get_model_exporter()
        
        # Validate format
        valid_formats = ['huggingface', 'ollama', 'gguf', 'lmstudio']
        if request.format not in valid_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}"
            )
        
        # Verify the export
        verification = exporter.verify_export(
            export_path=request.export_path,
            format=request.format
        )
        
        return {
            "passed": verification.get('passed', False),
            "details": verification
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying export: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/formats")
async def list_export_formats():
    """
    Get list of supported export formats.
    """
    return {
        "formats": [
            {
                "id": "huggingface",
                "name": "HuggingFace",
                "description": "Export to HuggingFace format with model card, config, and tokenizer",
                "artifacts": ["README.md", "config.json", "model weights", "tokenizer files"]
            },
            {
                "id": "ollama",
                "name": "Ollama",
                "description": "Export to Ollama format with Modelfile generation",
                "artifacts": ["Modelfile", "INSTALL.md", "model directory"]
            },
            {
                "id": "gguf",
                "name": "GGUF",
                "description": "Export to GGUF format using llama.cpp conversion",
                "artifacts": ["conversion instructions", "metadata"]
            },
            {
                "id": "lmstudio",
                "name": "LM Studio",
                "description": "Export to LM Studio format",
                "artifacts": ["lmstudio_config.json", "LMSTUDIO_SETUP.md", "model directory"]
            }
        ]
    }


class ExportFromVersionRequest(BaseModel):
    """Request to export a specific model version"""
    model_name: str
    version: str
    format: str
    quantization: Optional[str] = None
    merge_adapters: bool = True


@app.post("/api/export/from-version")
async def export_from_version(request: ExportFromVersionRequest):
    """
    Export a specific model version.
    Combines versioning and export functionality.
    """
    try:
        # Get the model version
        versioning_service = get_model_versioning_service()
        version = versioning_service.get_version(request.model_name, request.version)
        
        if not version:
            raise HTTPException(
                status_code=404,
                detail=f"Version {request.version} not found for model {request.model_name}"
            )
        
        # Export the model
        exporter = get_model_exporter()
        
        result = exporter.export_model(
            model_path=version.checkpoint_path,
            format=request.format,
            model_name=f"{request.model_name}-{request.version}",
            metadata={
                'config': version.config,
                'metrics': version.metrics,
                'version': version.version,
                'timestamp': version.timestamp
            },
            quantization=request.quantization,
            merge_adapters=request.merge_adapters
        )
        
        return {
            "success": result.success,
            "format": result.format,
            "output_path": result.output_path,
            "artifacts": result.artifacts,
            "size_bytes": result.size_bytes,
            "message": result.message,
            "verification_passed": result.verification_passed,
            "verification_details": result.verification_details,
            "source_version": {
                "model_name": version.model_name,
                "version": version.version,
                "timestamp": version.timestamp
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting from version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Offline-First Architecture Endpoints
# ============================================================================

class QueueOperationRequest(BaseModel):
    """Request to queue an offline operation"""
    operation_type: str
    payload: Dict[str, Any]
    priority: int = 0


@app.get("/api/offline/network-status")
async def get_network_status():
    """Get current network connectivity status"""
    try:
        monitor = get_network_monitor()
        return monitor.get_status_info()
    except Exception as e:
        logger.error(f"Error getting network status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/offline/check-connectivity")
async def check_connectivity():
    """Manually trigger a connectivity check"""
    try:
        monitor = get_network_monitor()
        is_online = await monitor.check_connectivity()
        await monitor.update_status()
        return {
            "is_online": is_online,
            "status": monitor.status.value,
            "last_check": monitor.last_check.isoformat() if monitor.last_check else None
        }
    except Exception as e:
        logger.error(f"Error checking connectivity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/offline/queue")
async def enqueue_operation(request: QueueOperationRequest):
    """Add an operation to the offline queue"""
    try:
        queue_manager = get_queue_manager()
        
        # Validate operation type
        try:
            op_type = OperationType(request.operation_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid operation type: {request.operation_type}"
            )
        
        operation_id = queue_manager.enqueue(
            operation_type=op_type,
            payload=request.payload,
            priority=request.priority
        )
        
        return {
            "success": True,
            "operation_id": operation_id,
            "message": "Operation queued successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error queueing operation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/offline/queue")
async def get_queue_operations(limit: Optional[int] = None):
    """Get pending operations from the queue"""
    try:
        queue_manager = get_queue_manager()
        operations = queue_manager.get_pending_operations(limit=limit)
        return {
            "operations": operations,
            "count": len(operations)
        }
    except Exception as e:
        logger.error(f"Error getting queue operations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/offline/queue/{operation_id}")
async def get_queue_operation(operation_id: int):
    """Get a specific operation from the queue"""
    try:
        queue_manager = get_queue_manager()
        operation = queue_manager.get_operation(operation_id)
        
        if not operation:
            raise HTTPException(
                status_code=404,
                detail=f"Operation {operation_id} not found"
            )
        
        return operation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting operation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/offline/queue/{operation_id}")
async def delete_queue_operation(operation_id: int):
    """Delete an operation from the queue"""
    try:
        queue_manager = get_queue_manager()
        success = queue_manager.delete_operation(operation_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Operation {operation_id} not found"
            )
        
        return {
            "success": True,
            "message": f"Operation {operation_id} deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting operation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/offline/queue/stats")
async def get_queue_stats():
    """Get statistics about the offline queue"""
    try:
        queue_manager = get_queue_manager()
        stats = queue_manager.get_queue_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting queue stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/offline/queue/clear-completed")
async def clear_completed_operations():
    """Clear all completed operations from the queue"""
    try:
        queue_manager = get_queue_manager()
        count = queue_manager.clear_completed()
        return {
            "success": True,
            "cleared": count,
            "message": f"Cleared {count} completed operations"
        }
    except Exception as e:
        logger.error(f"Error clearing completed operations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/offline/sync")
async def trigger_sync():
    """Manually trigger synchronization of offline operations"""
    try:
        sync_engine = get_sync_engine()
        results = await sync_engine.sync(force=False)
        return results
    except Exception as e:
        logger.error(f"Error triggering sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/offline/sync/status")
async def get_sync_status():
    """Get current synchronization status"""
    try:
        sync_engine = get_sync_engine()
        status = sync_engine.get_sync_status()
        return status
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/offline/sync/start-auto")
async def start_auto_sync():
    """Start automatic synchronization"""
    try:
        sync_engine = get_sync_engine()
        await sync_engine.start_auto_sync()
        return {
            "success": True,
            "message": "Auto-sync started"
        }
    except Exception as e:
        logger.error(f"Error starting auto-sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/offline/sync/stop-auto")
async def stop_auto_sync():
    """Stop automatic synchronization"""
    try:
        sync_engine = get_sync_engine()
        await sync_engine.stop_auto_sync()
        return {
            "success": True,
            "message": "Auto-sync stopped"
        }
    except Exception as e:
        logger.error(f"Error stopping auto-sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ConflictStrategyRequest(BaseModel):
    """Request to set conflict resolution strategy"""
    strategy: str


@app.post("/api/offline/sync/conflict-strategy")
async def set_conflict_strategy(request: ConflictStrategyRequest):
    """Set the conflict resolution strategy"""
    try:
        # Validate strategy
        try:
            strategy = ConflictResolution(request.strategy)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid conflict strategy: {request.strategy}"
            )
        
        sync_engine = get_sync_engine()
        sync_engine.set_conflict_strategy(strategy)
        
        return {
            "success": True,
            "strategy": strategy.value,
            "message": f"Conflict strategy set to {strategy.value}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting conflict strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Platform Connection Management Endpoints
# ============================================================================

from services.platform_connection_service import get_platform_connection_service

@app.get("/api/platforms")
async def list_available_platforms():
    """
    List all available platforms that can be connected.
    Validates: Requirements 1.1
    """
    try:
        connection_service = get_platform_connection_service()
        platforms = connection_service.list_available_platforms()
        
        return {
            "platforms": platforms,
            "count": len(platforms)
        }
    except Exception as e:
        logger.error(f"Error listing platforms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ConnectPlatformRequest(BaseModel):
    platform_name: str
    credentials: Dict[str, str]


@app.post("/api/platforms/connect")
async def connect_platform(request: ConnectPlatformRequest):
    """
    Connect to a platform with provided credentials.
    Validates: Requirements 1.2, 1.3
    """
    try:
        connection_service = get_platform_connection_service()
        connection = await connection_service.connect_platform(
            platform_name=request.platform_name,
            credentials=request.credentials
        )
        
        return connection.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error connecting platform: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/platforms/disconnect/{platform_name}")
async def disconnect_platform(platform_name: str):
    """
    Disconnect from a platform.
    Validates: Requirements 1.2
    """
    try:
        connection_service = get_platform_connection_service()
        success = await connection_service.disconnect_platform(platform_name)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to disconnect")
        
        return {
            "platform": platform_name,
            "status": "disconnected"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error disconnecting platform: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/platforms/verify/{platform_name}")
async def verify_platform_connection(platform_name: str):
    """
    Verify that a platform connection is still valid.
    Validates: Requirements 1.4, 1.5
    """
    try:
        connection_service = get_platform_connection_service()
        result = await connection_service.verify_connection(platform_name)
        
        return result
    except Exception as e:
        logger.error(f"Error verifying connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/platforms/test")
async def test_platform_connection(request: ConnectPlatformRequest):
    """
    Test a connection without storing credentials.
    Validates: Requirements 1.4
    """
    try:
        connection_service = get_platform_connection_service()
        result = await connection_service.test_connection(
            platform_name=request.platform_name,
            credentials=request.credentials
        )
        
        return result
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/platforms/connections")
async def list_platform_connections():
    """
    List all active platform connections.
    Validates: Requirements 1.1
    """
    try:
        connection_service = get_platform_connection_service()
        connections = connection_service.list_connections()
        
        return {
            "connections": [c.to_dict() for c in connections],
            "count": len(connections)
        }
    except Exception as e:
        logger.error(f"Error listing connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/platforms/connection/{platform_name}")
async def get_platform_connection(platform_name: str):
    """
    Get connection information for a specific platform.
    Validates: Requirements 1.1
    """
    try:
        connection_service = get_platform_connection_service()
        connection = connection_service.get_connection(platform_name)
        
        if not connection:
            raise HTTPException(status_code=404, detail="Platform not connected")
        
        return connection.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/platforms/credentials/{platform_name}")
async def update_platform_credentials(platform_name: str, request: ConnectPlatformRequest):
    """
    Update credentials for an existing connection.
    Validates: Requirements 1.2, 1.3
    """
    try:
        connection_service = get_platform_connection_service()
        success = await connection_service.update_credentials(
            platform_name=platform_name,
            credentials=request.credentials
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update credentials")
        
        return {
            "platform": platform_name,
            "status": "credentials_updated"
        }
    except Exception as e:
        logger.error(f"Error updating credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/platforms/verify-all")
async def verify_all_connections():
    """
    Verify all active platform connections.
    Validates: Requirements 1.4
    """
    try:
        connection_service = get_platform_connection_service()
        results = await connection_service.verify_all_connections()
        
        return {
            "results": results,
            "total": len(results),
            "valid": sum(1 for r in results.values() if r["valid"]),
            "invalid": sum(1 for r in results.values() if not r["valid"])
        }
    except Exception as e:
        logger.error(f"Error verifying all connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/platforms/stats")
async def get_connection_stats():
    """
    Get statistics about platform connections.
    Validates: Requirements 1.1
    """
    try:
        connection_service = get_platform_connection_service()
        stats = connection_service.get_connection_stats()
        
        return stats
    except Exception as e:
        logger.error(f"Error getting connection stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Cloud Platform Comparison Endpoints
class CloudCostComparisonRequest(BaseModel):
    training_hours: float
    local_gpu_type: Optional[str] = None
    local_electricity_cost: Optional[float] = None
    min_memory_gb: Optional[int] = None


@app.post("/api/cloud/compare-costs")
async def compare_cloud_costs(request: CloudCostComparisonRequest):
    """
    Compare costs across all cloud platforms.
    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
    """
    try:
        from services.cloud_platform_service import get_cloud_platform_service
        
        cloud_service = get_cloud_platform_service()
        
        # Perform cost comparison
        comparison = cloud_service.compare_costs(
            training_hours=request.training_hours,
            local_gpu_type=request.local_gpu_type,
            local_electricity_cost=request.local_electricity_cost,
            min_memory_gb=request.min_memory_gb
        )
        
        # Format the response
        result = cloud_service.format_cost_comparison(comparison)
        
        return result
    except Exception as e:
        logger.error(f"Error comparing cloud costs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cloud/instances")
async def list_cloud_instances(
    gpu_type: Optional[str] = None,
    min_memory_gb: Optional[int] = None,
    platform: Optional[str] = None
):
    """
    List available cloud GPU instances.
    Validates: Requirements 3.1, 3.3
    """
    try:
        from services.cloud_platform_service import get_cloud_platform_service, GPUType, PlatformType
        
        cloud_service = get_cloud_platform_service()
        
        # Convert string to enum if provided
        gpu_type_enum = None
        if gpu_type:
            try:
                gpu_type_enum = GPUType[gpu_type.upper().replace(" ", "_").replace("-", "_")]
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid GPU type: {gpu_type}")
        
        # Get instances based on platform
        if platform:
            try:
                platform_enum = PlatformType[platform.upper()]
                if platform_enum == PlatformType.RUNPOD:
                    instances = cloud_service.get_runpod_instances(gpu_type_enum, min_memory_gb)
                elif platform_enum == PlatformType.LAMBDA_LABS:
                    instances = cloud_service.get_lambda_labs_instances(gpu_type_enum, min_memory_gb)
                elif platform_enum == PlatformType.TOGETHER_AI:
                    instances = cloud_service.get_together_ai_instances(gpu_type_enum, min_memory_gb)
                else:
                    raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid platform: {platform}")
        else:
            instances = cloud_service.get_all_cloud_instances(gpu_type_enum, min_memory_gb)
        
        return {
            "instances": [
                {
                    "platform": inst.platform.value,
                    "gpu_type": inst.gpu_type.value,
                    "gpu_count": inst.gpu_count,
                    "memory_gb": inst.memory_gb,
                    "vcpus": inst.vcpus,
                    "ram_gb": inst.ram_gb,
                    "storage_gb": inst.storage_gb,
                    "hourly_rate_usd": inst.hourly_rate_usd,
                    "availability": inst.availability,
                    "region": inst.region
                }
                for inst in instances
            ],
            "count": len(instances)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing cloud instances: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cloud/platforms/{platform}/setup")
async def get_platform_setup_instructions(platform: str):
    """
    Get setup instructions for a specific platform.
    Validates: Requirements 3.4
    """
    try:
        from services.cloud_platform_service import get_cloud_platform_service, PlatformType
        
        cloud_service = get_cloud_platform_service()
        
        try:
            platform_enum = PlatformType[platform.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid platform: {platform}")
        
        instructions = cloud_service.get_platform_setup_instructions(platform_enum)
        
        return instructions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting setup instructions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class PlatformCostEstimateRequest(BaseModel):
    platform: str
    gpu_type: str
    training_hours: float


@app.post("/api/cloud/estimate-cost")
async def estimate_platform_cost(request: PlatformCostEstimateRequest):
    """
    Estimate cost for a specific platform and GPU type.
    Validates: Requirements 3.2
    """
    try:
        from services.cloud_platform_service import get_cloud_platform_service, GPUType, PlatformType
        
        cloud_service = get_cloud_platform_service()
        
        # Convert strings to enums
        try:
            platform_enum = PlatformType[request.platform.upper()]
            gpu_type_enum = GPUType[request.gpu_type.upper().replace(" ", "_").replace("-", "_")]
        except KeyError as e:
            raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
        
        # Get instances for this platform and GPU type
        if platform_enum == PlatformType.RUNPOD:
            instances = cloud_service.get_runpod_instances(gpu_type=gpu_type_enum)
        elif platform_enum == PlatformType.LAMBDA_LABS:
            instances = cloud_service.get_lambda_labs_instances(gpu_type=gpu_type_enum)
        elif platform_enum == PlatformType.TOGETHER_AI:
            instances = cloud_service.get_together_ai_instances(gpu_type=gpu_type_enum)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported platform: {request.platform}")
        
        if not instances:
            raise HTTPException(status_code=404, detail=f"No instances found for {request.gpu_type} on {request.platform}")
        
        # Calculate cost for the first matching instance
        instance = instances[0]
        estimate = cloud_service.calculate_platform_cost(instance, request.training_hours)
        
        return {
            "platform": estimate.platform.value,
            "gpu_type": estimate.instance.gpu_type.value,
            "training_hours": estimate.training_hours,
            "total_cost_usd": estimate.total_cost_usd,
            "hourly_rate_usd": estimate.instance.hourly_rate_usd,
            "setup_time_minutes": estimate.setup_time_minutes,
            "estimated_start_time": estimate.estimated_start_time,
            "pros": estimate.pros,
            "cons": estimate.cons
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error estimating cost: {e}")
        raise HTTPException(status_code=500, detail=str(e))
