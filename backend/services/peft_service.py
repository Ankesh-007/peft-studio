"""
PEFT Service for managing Parameter-Efficient Fine-Tuning operations.
Uses Unsloth for 2x speed and 60-70% less VRAM.
"""

from typing import Dict, List, Optional, Literal
from dataclasses import dataclass
from enum import Enum
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, PeftModel, TaskType
import logging

# Try to import unsloth, but make it optional for testing
try:
    from unsloth import FastLanguageModel
    UNSLOTH_AVAILABLE = True
except ImportError:
    UNSLOTH_AVAILABLE = False
    FastLanguageModel = None

logger = logging.getLogger(__name__)


class PEFTAlgorithm(str, Enum):
    """Supported PEFT algorithms"""
    LORA = "lora"
    QLORA = "qlora"
    DORA = "dora"
    PISSA = "pissa"
    RSLORA = "rslora"


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
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"PEFTService initialized on device: {self.device}")
    
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
