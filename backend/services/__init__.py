"""
Services module for PEFT Studio backend.

STARTUP OPTIMIZATION: This module uses lazy loading to improve startup time.
Heavy services are only imported when actually needed.
"""

# Import startup service first (lightweight)
from .startup_service import (
    get_startup_optimizer,
    measure_startup,
    lazy_import_torch,
    lazy_import_transformers,
    lazy_import_unsloth
)

from .peft_service import (
    PEFTService,
    PEFTAlgorithm,
    PEFTConfig,
    ModelInfo,
    get_peft_service
)

from .hardware_service import (
    HardwareService,
    GPUInfo,
    CPUInfo,
    RAMInfo,
    HardwareProfile,
    get_hardware_service
)

from .model_registry_service import (
    ModelRegistryService,
    ModelMetadata,
    get_model_registry_service
)

from .smart_config_service import (
    SmartConfigEngine,
    SmartConfig,
    HardwareSpecs,
    ModelSpecs,
    DatasetSpecs,
    PrecisionType,
    QuantizationType,
    get_smart_config_engine
)

from .profile_service import (
    ProfileService,
    OptimizationProfile,
    ProfileConfig,
    HardwareRequirements,
    UseCase,
    get_profile_service
)

from .dataset_service import (
    DatasetService,
    DatasetFormat,
    ValidationLevel,
    ValidationResult,
    DatasetStatistics,
    DatasetPreview,
    QualityReport,
    get_dataset_service
)

from .training_orchestration_service import (
    TrainingOrchestrator,
    TrainingState,
    TrainingJob,
    TrainingConfig,
    TrainingMetrics,
    CheckpointData,
    ArtifactInfo,
    get_training_orchestrator
)

from .monitoring_service import (
    MonitoringService,
    TrainingMetrics as MonitoringMetrics,
    get_monitoring_service
)

from .anomaly_detection_service import (
    AnomalyDetectionService,
    AnomalyType,
    AnomalySeverity,
    Anomaly,
    Action,
    get_anomaly_detection_service
)

from .model_versioning_service import (
    ModelVersioningService,
    ModelVersion,
    VersionComparison,
    DiskSpaceInfo,
    get_model_versioning_service
)

from .inference_service import (
    InferenceService,
    InferenceRequest,
    InferenceResult,
    ComparisonResult,
    ConversationMessage,
    ConversationHistory,
    get_inference_service
)

from .export_service import (
    ModelExporter,
    ExportResult,
    ExportFormat,
    HuggingFaceExport,
    OllamaExport,
    GGUFExport,
    LMStudioExport,
    get_model_exporter
)

from .cost_calculator_service import (
    CostCalculatorService,
    CostEstimates,
    GPUPowerProfile,
    get_cost_calculator
)

from .cloud_platform_service import (
    CloudPlatformService,
    PlatformType,
    GPUType,
    GPUInstance,
    PlatformCostEstimate,
    CostComparison,
    get_cloud_platform_service
)

__all__ = [
    # PEFT Service
    "PEFTService",
    "PEFTAlgorithm",
    "PEFTConfig",
    "ModelInfo",
    "get_peft_service",
    
    # Hardware Service
    "HardwareService",
    "GPUInfo",
    "CPUInfo",
    "RAMInfo",
    "HardwareProfile",
    "get_hardware_service",
    
    # Model Registry Service
    "ModelRegistryService",
    "ModelMetadata",
    "get_model_registry_service",
    
    # Smart Config Service
    "SmartConfigEngine",
    "SmartConfig",
    "HardwareSpecs",
    "ModelSpecs",
    "DatasetSpecs",
    "PrecisionType",
    "QuantizationType",
    "get_smart_config_engine",
    
    # Profile Service
    "ProfileService",
    "OptimizationProfile",
    "ProfileConfig",
    "HardwareRequirements",
    "UseCase",
    "get_profile_service",
    
    # Dataset Service
    "DatasetService",
    "DatasetFormat",
    "ValidationLevel",
    "ValidationResult",
    "DatasetStatistics",
    "DatasetPreview",
    "QualityReport",
    "get_dataset_service",
    
    # Training Orchestration Service
    "TrainingOrchestrator",
    "TrainingState",
    "TrainingJob",
    "TrainingConfig",
    "TrainingMetrics",
    "CheckpointData",
    "ArtifactInfo",
    "get_training_orchestrator",
    
    # Monitoring Service
    "MonitoringService",
    "MonitoringMetrics",
    "get_monitoring_service",
    
    # Anomaly Detection Service
    "AnomalyDetectionService",
    "AnomalyType",
    "AnomalySeverity",
    "Anomaly",
    "Action",
    "get_anomaly_detection_service",
    
    # Model Versioning Service
    "ModelVersioningService",
    "ModelVersion",
    "VersionComparison",
    "DiskSpaceInfo",
    "get_model_versioning_service",
    
    # Inference Service
    "InferenceService",
    "InferenceRequest",
    "InferenceResult",
    "ComparisonResult",
    "ConversationMessage",
    "ConversationHistory",
    "get_inference_service",
    
    # Export Service
    "ModelExporter",
    "ExportResult",
    "ExportFormat",
    "HuggingFaceExport",
    "OllamaExport",
    "GGUFExport",
    "LMStudioExport",
    "get_model_exporter",
    
    # Cost Calculator Service
    "CostCalculatorService",
    "CostEstimates",
    "GPUPowerProfile",
    "get_cost_calculator",
    
    # Cloud Platform Service
    "CloudPlatformService",
    "PlatformType",
    "GPUType",
    "GPUInstance",
    "PlatformCostEstimate",
    "CostComparison",
    "get_cloud_platform_service",
]
