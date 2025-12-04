"""
PEFT Service for managing Parameter-Efficient Fine-Tuning operations.
Uses Unsloth for 2x speed and 60-70% less VRAM.
"""

from typing import Dict, List, Optional, Literal
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Lazy imports for heavy ML libraries to reduce startup memory usage
_torch = None
_transformers = None
_peft = None
_unsloth = None
UNSLOTH_AVAILABLE = None

def _get_torch():
    """Lazy load torch module"""
    global _torch
    if _torch is None:
        import torch as _torch_module
        _torch = _torch_module
    return _torch

def _get_transformers():
    """Lazy load transformers module"""
    global _transformers
    if _transformers is None:
        import transformers as _transformers_module
        _transformers = _transformers_module
    return _transformers

def _get_peft():
    """Lazy load peft module"""
    global _peft
    if _peft is None:
        import peft as _peft_module
        _peft = _peft_module
    return _peft

def _get_unsloth():
    """Lazy load unsloth module"""
    global _unsloth, UNSLOTH_AVAILABLE
    if _unsloth is None and UNSLOTH_AVAILABLE is None:
        try:
            import unsloth as _unsloth_module
            _unsloth = _unsloth_module
            UNSLOTH_AVAILABLE = True
        except ImportError:
            UNSLOTH_AVAILABLE = False
            _unsloth = None
    return _unsloth


class PEFTAlgorithm(str, Enum):
    """Supported PEFT algorithms"""
    LORA = "lora"
    QLORA = "qlora"
    DORA = "dora"
    PISSA = "pissa"
    RSLORA = "rslora"


@dataclass
class ParameterDefinition:
    """Definition of a PEFT parameter"""
    name: str
    display_name: str
    description: str
    type: str  # "int", "float", "list", "bool"
    default: any
    min_value: Optional[any] = None
    max_value: Optional[any] = None
    recommended_range: Optional[str] = None


@dataclass
class AlgorithmInfo:
    """Detailed information about a PEFT algorithm"""
    id: str
    name: str
    description: str
    long_description: str
    recommended: bool
    use_cases: List[str]
    requirements: List[str]
    advantages: List[str]
    disadvantages: List[str]
    parameters: List[ParameterDefinition]
    memory_efficiency: str  # "low", "medium", "high"
    training_speed: str  # "slow", "medium", "fast"


@dataclass
class PEFTConfig:
    """Configuration for PEFT training"""
    algorithm: PEFTAlgorithm
    r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    target_modules: List[str] = None
    bias: str = "none"
    task_type: str = "CAUSAL_LM"
    use_rslora: bool = False
    use_dora: bool = False
    use_pissa: bool = False
    
    def __post_init__(self):
        if self.target_modules is None:
            self.target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", 
                                   "gate_proj", "up_proj", "down_proj"]
        
        # Configure algorithm-specific settings
        if self.algorithm == PEFTAlgorithm.RSLORA:
            self.use_rslora = True
        elif self.algorithm == PEFTAlgorithm.DORA:
            self.use_dora = True
        elif self.algorithm == PEFTAlgorithm.PISSA:
            self.use_pissa = True
        elif self.algorithm == PEFTAlgorithm.QLORA:
            # QLoRA uses 4-bit quantization
            pass


@dataclass
class ModelInfo:
    """Information about a loaded model"""
    model_name: str
    model: any
    tokenizer: any
    max_seq_length: int
    supports_gradient_checkpointing: bool
    memory_footprint_mb: float


class PEFTService:
    """Service for PEFT operations using Unsloth"""
    
    def __init__(self):
        self.loaded_models: Dict[str, ModelInfo] = {}
        torch = _get_torch()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"PEFTService initialized on device: {self.device}")
    
    def get_algorithm_info(self, algorithm: PEFTAlgorithm) -> AlgorithmInfo:
        """
        Get detailed information about a PEFT algorithm.
        
        Args:
            algorithm: The PEFT algorithm to get info for
            
        Returns:
            AlgorithmInfo with complete details about the algorithm
        """
        # Common parameters for all algorithms
        common_params = [
            ParameterDefinition(
                name="r",
                display_name="Rank (r)",
                description="The rank of the low-rank decomposition matrices",
                type="int",
                default=8,
                min_value=1,
                max_value=256,
                recommended_range="4-64 for most models"
            ),
            ParameterDefinition(
                name="lora_alpha",
                display_name="LoRA Alpha",
                description="Scaling factor for LoRA weights. Higher values increase adapter influence",
                type="int",
                default=16,
                min_value=1,
                max_value=128,
                recommended_range="Usually 2x the rank value"
            ),
            ParameterDefinition(
                name="lora_dropout",
                display_name="LoRA Dropout",
                description="Dropout probability for LoRA layers to prevent overfitting",
                type="float",
                default=0.1,
                min_value=0.0,
                max_value=0.5,
                recommended_range="0.0-0.2 for most cases"
            ),
            ParameterDefinition(
                name="target_modules",
                display_name="Target Modules",
                description="Which model layers to apply LoRA adapters to",
                type="list",
                default=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
                recommended_range="All attention layers for best results"
            ),
        ]
        
        if algorithm == PEFTAlgorithm.LORA:
            return AlgorithmInfo(
                id="lora",
                name="LoRA",
                description="Low-Rank Adaptation - efficient fine-tuning with minimal parameters",
                long_description="LoRA (Low-Rank Adaptation) decomposes weight updates into low-rank matrices, "
                               "dramatically reducing the number of trainable parameters while maintaining model quality. "
                               "It's the most widely used and battle-tested PEFT method.",
                recommended=True,
                use_cases=[
                    "General-purpose fine-tuning",
                    "When you have limited GPU memory",
                    "When you want fast training",
                    "Production deployments requiring stability"
                ],
                requirements=[
                    "PyTorch 1.13+",
                    "PEFT library",
                    "4GB+ GPU memory (depending on model size)"
                ],
                advantages=[
                    "Reduces trainable parameters by 90%+",
                    "Fast training and inference",
                    "Well-documented and widely supported",
                    "Easy to merge adapters back into base model",
                    "Multiple adapters can be trained and swapped"
                ],
                disadvantages=[
                    "May require tuning rank (r) for optimal results",
                    "Slightly lower quality than full fine-tuning in some cases"
                ],
                parameters=common_params,
                memory_efficiency="high",
                training_speed="fast"
            )
        
        elif algorithm == PEFTAlgorithm.QLORA:
            return AlgorithmInfo(
                id="qlora",
                name="QLoRA",
                description="Quantized LoRA with 4-bit precision for extreme memory efficiency",
                long_description="QLoRA combines LoRA with 4-bit quantization, enabling fine-tuning of very large models "
                               "on consumer GPUs. It uses NormalFloat4 (NF4) quantization and double quantization to "
                               "minimize memory usage while maintaining quality.",
                recommended=True,
                use_cases=[
                    "Fine-tuning large models (7B-70B+) on limited hardware",
                    "When GPU memory is severely constrained",
                    "Training on consumer GPUs (RTX 3090, 4090, etc.)",
                    "Experimenting with very large models"
                ],
                requirements=[
                    "PyTorch 2.0+",
                    "PEFT library",
                    "bitsandbytes library",
                    "CUDA-capable GPU",
                    "8GB+ GPU memory"
                ],
                advantages=[
                    "Reduces memory usage by 75% compared to LoRA",
                    "Enables training 65B models on 48GB GPU",
                    "Minimal quality loss vs full precision",
                    "Can fine-tune models that wouldn't fit otherwise"
                ],
                disadvantages=[
                    "Slower training than regular LoRA (1.3-1.5x)",
                    "Requires CUDA GPU (no CPU support)",
                    "Slightly more complex setup",
                    "May have numerical instability in rare cases"
                ],
                parameters=common_params,
                memory_efficiency="very high",
                training_speed="medium"
            )
        
        elif algorithm == PEFTAlgorithm.DORA:
            return AlgorithmInfo(
                id="dora",
                name="DoRA",
                description="Weight-Decomposed Low-Rank Adaptation for improved learning",
                long_description="DoRA (Weight-Decomposed Low-Rank Adaptation) decomposes pre-trained weights into "
                               "magnitude and direction components, applying LoRA only to the directional component. "
                               "This can lead to better learning dynamics and improved performance.",
                recommended=False,
                use_cases=[
                    "When LoRA performance is insufficient",
                    "Tasks requiring fine-grained weight updates",
                    "Research and experimentation",
                    "When you have extra compute budget"
                ],
                requirements=[
                    "PyTorch 2.0+",
                    "PEFT library 0.7.0+",
                    "Same memory as LoRA",
                    "Slightly more compute than LoRA"
                ],
                advantages=[
                    "Can outperform LoRA on some tasks",
                    "Better learning dynamics",
                    "Same memory footprint as LoRA",
                    "Compatible with existing LoRA infrastructure"
                ],
                disadvantages=[
                    "10-20% slower training than LoRA",
                    "Less mature and tested than LoRA",
                    "May not always improve over LoRA",
                    "Requires newer PEFT versions"
                ],
                parameters=common_params,
                memory_efficiency="high",
                training_speed="medium"
            )
        
        elif algorithm == PEFTAlgorithm.PISSA:
            return AlgorithmInfo(
                id="pissa",
                name="PiSSA",
                description="Principal Singular values and Singular vectors Adaptation",
                long_description="PiSSA (Principal Singular values and Singular vectors Adaptation) initializes "
                               "LoRA adapters using principal components from SVD of pre-trained weights. This can "
                               "lead to faster convergence and better final performance.",
                recommended=False,
                use_cases=[
                    "When you want faster convergence",
                    "Tasks with limited training data",
                    "Research and experimentation",
                    "When initialization matters"
                ],
                requirements=[
                    "PyTorch 2.0+",
                    "PEFT library 0.8.0+",
                    "Extra memory for SVD computation during initialization",
                    "Longer initialization time"
                ],
                advantages=[
                    "Faster convergence than random initialization",
                    "Can achieve better final performance",
                    "Particularly effective with small datasets",
                    "Theoretically grounded approach"
                ],
                disadvantages=[
                    "Slower initialization (SVD computation)",
                    "Requires more memory during initialization",
                    "Less tested than LoRA",
                    "May not always improve over LoRA",
                    "Requires very recent PEFT versions"
                ],
                parameters=common_params,
                memory_efficiency="high",
                training_speed="medium"
            )
        
        elif algorithm == PEFTAlgorithm.RSLORA:
            return AlgorithmInfo(
                id="rslora",
                name="RSLoRA",
                description="Rank-Stabilized LoRA for improved training stability",
                long_description="RSLoRA (Rank-Stabilized LoRA) modifies the LoRA scaling to be rank-dependent, "
                               "which can improve training stability and performance, especially with higher ranks. "
                               "It uses a scaling factor of 1/sqrt(r) instead of alpha/r.",
                recommended=False,
                use_cases=[
                    "When using high rank values (r > 32)",
                    "When training stability is a concern",
                    "Research and experimentation",
                    "When standard LoRA shows instability"
                ],
                requirements=[
                    "PyTorch 1.13+",
                    "PEFT library 0.6.0+",
                    "Same requirements as LoRA"
                ],
                advantages=[
                    "Better training stability with high ranks",
                    "Can enable using higher rank values",
                    "Same speed and memory as LoRA",
                    "Easy drop-in replacement for LoRA"
                ],
                disadvantages=[
                    "May require different hyperparameter tuning",
                    "Less widely tested than standard LoRA",
                    "Benefits mainly visible with high ranks",
                    "Not always better than standard LoRA"
                ],
                parameters=common_params,
                memory_efficiency="high",
                training_speed="fast"
            )
        
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
    
    def get_all_algorithms_info(self) -> List[AlgorithmInfo]:
        """
        Get information about all supported PEFT algorithms.
        
        Returns:
            List of AlgorithmInfo for all algorithms
        """
        return [
            self.get_algorithm_info(PEFTAlgorithm.LORA),
            self.get_algorithm_info(PEFTAlgorithm.QLORA),
            self.get_algorithm_info(PEFTAlgorithm.DORA),
            self.get_algorithm_info(PEFTAlgorithm.PISSA),
            self.get_algorithm_info(PEFTAlgorithm.RSLORA),
        ]
    
    def load_model_with_unsloth(
        self,
        model_name: str,
        max_seq_length: int = 2048,
        dtype: Optional[torch.dtype] = None,
        load_in_4bit: bool = False,
        load_in_8bit: bool = False
    ) -> ModelInfo:
        """
        Load a model using Unsloth for optimized performance.
        
        Args:
            model_name: HuggingFace model identifier
            max_seq_length: Maximum sequence length
            dtype: Data type (None for auto)
            load_in_4bit: Use 4-bit quantization (QLoRA)
            load_in_8bit: Use 8-bit quantization
            
        Returns:
            ModelInfo object with loaded model and tokenizer
        """
        try:
            logger.info(f"Loading model {model_name} with Unsloth...")
            
            if not UNSLOTH_AVAILABLE:
                raise ImportError("Unsloth is not available. Please install it to use this feature.")
            
            # Use Unsloth's FastLanguageModel for optimized loading
            model, tokenizer = FastLanguageModel.from_pretrained(
                model_name=model_name,
                max_seq_length=max_seq_length,
                dtype=dtype,
                load_in_4bit=load_in_4bit,
                load_in_8bit=load_in_8bit,
            )
            
            # Calculate memory footprint
            memory_footprint = sum(
                p.numel() * p.element_size() 
                for p in model.parameters()
            ) / (1024 ** 2)  # Convert to MB
            
            model_info = ModelInfo(
                model_name=model_name,
                model=model,
                tokenizer=tokenizer,
                max_seq_length=max_seq_length,
                supports_gradient_checkpointing=True,
                memory_footprint_mb=memory_footprint
            )
            
            self.loaded_models[model_name] = model_info
            logger.info(f"Model loaded successfully. Memory footprint: {memory_footprint:.2f} MB")
            
            return model_info
            
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {str(e)}")
            raise
    
    def configure_peft(
        self,
        model_info: ModelInfo,
        peft_config: PEFTConfig
    ) -> any:
        """
        Configure PEFT adapters on a loaded model.
        
        Args:
            model_info: Loaded model information
            peft_config: PEFT configuration
            
        Returns:
            Model with PEFT adapters configured
        """
        try:
            logger.info(f"Configuring PEFT with algorithm: {peft_config.algorithm}")
            
            if not UNSLOTH_AVAILABLE:
                raise ImportError("Unsloth is not available. Please install it to use this feature.")
            
            # Use Unsloth's get_peft_model for optimized PEFT
            model = FastLanguageModel.get_peft_model(
                model_info.model,
                r=peft_config.r,
                lora_alpha=peft_config.lora_alpha,
                lora_dropout=peft_config.lora_dropout,
                target_modules=peft_config.target_modules,
                bias=peft_config.bias,
                use_gradient_checkpointing="unsloth",  # Unsloth's optimized checkpointing
                random_state=42,
                use_rslora=peft_config.use_rslora,
                use_dora=peft_config.use_dora,
                # Note: PiSSA support may require specific Unsloth version
            )
            
            logger.info("PEFT configuration applied successfully")
            return model
            
        except Exception as e:
            logger.error(f"Error configuring PEFT: {str(e)}")
            raise
    
    def get_trainable_parameters(self, model: any) -> Dict[str, int]:
        """
        Get count of trainable vs total parameters.
        
        Args:
            model: PEFT model
            
        Returns:
            Dictionary with trainable and total parameter counts
        """
        trainable_params = 0
        all_params = 0
        
        for param in model.parameters():
            all_params += param.numel()
            if param.requires_grad:
                trainable_params += param.numel()
        
        return {
            "trainable_params": trainable_params,
            "all_params": all_params,
            "trainable_percentage": 100 * trainable_params / all_params if all_params > 0 else 0
        }
    
    def unload_model(self, model_name: str) -> None:
        """
        Unload a model from memory.
        
        Args:
            model_name: Name of model to unload
        """
        if model_name in self.loaded_models:
            del self.loaded_models[model_name]
            torch.cuda.empty_cache()
            logger.info(f"Model {model_name} unloaded from memory")
    
    def list_loaded_models(self) -> List[str]:
        """Get list of currently loaded models"""
        return list(self.loaded_models.keys())


# Singleton instance
_peft_service_instance = None


def get_peft_service() -> PEFTService:
    """Get singleton instance of PEFTService"""
    global _peft_service_instance
    if _peft_service_instance is None:
        _peft_service_instance = PEFTService()
    return _peft_service_instance
