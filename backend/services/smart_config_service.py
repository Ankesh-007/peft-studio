"""
Smart Configuration Engine for calculating optimal training parameters.

This service automatically calculates optimal hyperparameters based on:
- Hardware specifications (GPU memory, CPU, RAM)
- Model size and architecture
- Dataset characteristics
- User preferences and constraints
"""

from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
import math
import logging

logger = logging.getLogger(__name__)


class PrecisionType(str, Enum):
    """Supported precision types"""
    FP32 = "fp32"
    FP16 = "fp16"
    BF16 = "bf16"
    INT8 = "int8"
    INT4 = "int4"


class QuantizationType(str, Enum):
    """Supported quantization types"""
    NONE = "none"
    INT8 = "8bit"
    INT4 = "4bit"


@dataclass
class HardwareSpecs:
    """Hardware specifications for configuration calculation"""
    gpu_memory_mb: int  # Available GPU memory in MB
    cpu_cores: int
    ram_gb: int
    compute_capability: Optional[str] = None  # e.g., "8.0" for A100


@dataclass
class ModelSpecs:
    """Model specifications"""
    model_size_mb: int  # Approximate model size in MB
    num_parameters: Optional[int] = None  # Number of parameters (in millions)
    max_seq_length: int = 2048
    architecture: Optional[str] = None


@dataclass
class DatasetSpecs:
    """Dataset specifications"""
    num_samples: int
    avg_sequence_length: Optional[int] = None
    max_sequence_length: Optional[int] = None


@dataclass
class SmartConfig:
    """Smart configuration with calculated defaults"""
    # Batch configuration
    batch_size: int
    gradient_accumulation_steps: int
    effective_batch_size: int
    
    # Precision and quantization
    precision: PrecisionType
    quantization: QuantizationType
    
    # Learning rate
    learning_rate: float
    
    # Training duration
    num_epochs: int
    
    # Memory estimates
    estimated_memory_mb: int
    memory_utilization_percent: float
    
    # Optional fields with defaults
    max_steps: Optional[int] = None
    estimated_training_time_hours: Optional[float] = None
    tokens_per_second: Optional[float] = None
    explanations: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.explanations is None:
            self.explanations = {}


@dataclass
class ConfigurationAlternative:
    """Alternative configuration suggestion with description and trade-offs"""
    config: SmartConfig
    description: str  # Plain-language description of the alternative
    trade_offs: str  # Explanation of trade-offs vs base configuration


class SmartConfigEngine:
    """
    Engine for calculating optimal training configurations based on hardware and data.
    """
    
    # Constants for memory estimation
    BYTES_PER_PARAM = {
        PrecisionType.FP32: 4,
        PrecisionType.FP16: 2,
        PrecisionType.BF16: 2,
        PrecisionType.INT8: 1,
        PrecisionType.INT4: 0.5,
    }
    
    # Memory overhead multipliers (for optimizer states, gradients, activations)
    MEMORY_OVERHEAD_MULTIPLIER = {
        PrecisionType.FP32: 4.0,  # Model + gradients + optimizer states
        PrecisionType.FP16: 3.0,  # Mixed precision reduces overhead
        PrecisionType.BF16: 3.0,
        PrecisionType.INT8: 2.5,  # Quantization reduces overhead
        PrecisionType.INT4: 2.0,
    }
    
    # Safety margin for memory allocation (keep 20% free)
    MEMORY_SAFETY_MARGIN = 0.8
    
    # Learning rate scaling constants
    BASE_LEARNING_RATE = 2e-4
    LR_SQRT_SCALING = True  # Use sqrt scaling for batch size
    
    def __init__(self):
        logger.info("SmartConfigEngine initialized")
    
    def calculate_batch_size(
        self,
        gpu_memory_mb: int,
        model_size_mb: int,
        seq_length: int,
        precision: PrecisionType = PrecisionType.FP16
    ) -> int:
        """
        Calculate optimal batch size based on GPU memory and model size.
        
        Args:
            gpu_memory_mb: Available GPU memory in MB
            model_size_mb: Model size in MB
            seq_length: Sequence length
            precision: Precision type
            
        Returns:
            Optimal batch size
        """
        # Apply safety margin
        usable_memory_mb = gpu_memory_mb * self.MEMORY_SAFETY_MARGIN
        
        # Estimate memory per sample (model + activations + gradients)
        overhead_multiplier = self.MEMORY_OVERHEAD_MULTIPLIER[precision]
        
        # Activation memory scales with sequence length and batch size
        # Rough estimate: hidden_size * seq_length * num_layers * bytes_per_param
        # We'll use a simplified model: ~10% of model size per sample for activations
        activation_memory_per_sample = model_size_mb * 0.1
        
        # Total memory per sample
        memory_per_sample = activation_memory_per_sample * overhead_multiplier
        
        # Calculate batch size
        available_for_batch = usable_memory_mb - (model_size_mb * overhead_multiplier)
        
        if available_for_batch <= 0:
            logger.warning(f"Insufficient memory: {usable_memory_mb}MB available, "
                         f"model needs {model_size_mb * overhead_multiplier}MB")
            return 1
        
        batch_size = max(1, int(available_for_batch / memory_per_sample))
        
        # Cap at reasonable maximum
        batch_size = min(batch_size, 128)
        
        # Prefer power of 2 for efficiency
        batch_size = self._round_to_power_of_2(batch_size)
        
        logger.info(f"Calculated batch size: {batch_size} "
                   f"(GPU: {gpu_memory_mb}MB, Model: {model_size_mb}MB, "
                   f"Precision: {precision.value})")
        
        return batch_size
    
    def calculate_gradient_accumulation(
        self,
        target_batch_size: int,
        max_batch_size: int
    ) -> int:
        """
        Calculate gradient accumulation steps to reach target effective batch size.
        
        Args:
            target_batch_size: Desired effective batch size
            max_batch_size: Maximum batch size that fits in memory
            
        Returns:
            Number of gradient accumulation steps
        """
        if max_batch_size >= target_batch_size:
            return 1
        
        # Calculate steps needed
        steps = math.ceil(target_batch_size / max_batch_size)
        
        logger.info(f"Gradient accumulation: {steps} steps "
                   f"(target: {target_batch_size}, max: {max_batch_size})")
        
        return steps
    
    def recommend_precision(
        self,
        compute_capability: Optional[str] = None,
        gpu_memory_mb: Optional[int] = None,
        model_size_mb: Optional[int] = None
    ) -> PrecisionType:
        """
        Recommend optimal precision based on hardware capabilities.
        
        Args:
            compute_capability: GPU compute capability (e.g., "8.0")
            gpu_memory_mb: Available GPU memory
            model_size_mb: Model size
            
        Returns:
            Recommended precision type
        """
        # If no GPU info, default to FP16
        if compute_capability is None:
            logger.info("No compute capability provided, defaulting to FP16")
            return PrecisionType.FP16
        
        try:
            major, minor = map(int, compute_capability.split('.'))
            cc_value = major * 10 + minor
        except (ValueError, AttributeError):
            logger.warning(f"Invalid compute capability: {compute_capability}, defaulting to FP16")
            return PrecisionType.FP16
        
        # BF16 is supported on Ampere (8.0+) and newer
        if cc_value >= 80:
            logger.info(f"Compute capability {compute_capability} supports BF16")
            return PrecisionType.BF16
        
        # FP16 is widely supported on modern GPUs (7.0+)
        if cc_value >= 70:
            logger.info(f"Compute capability {compute_capability} supports FP16")
            return PrecisionType.FP16
        
        # Older GPUs: use FP32
        logger.info(f"Compute capability {compute_capability} - using FP32")
        return PrecisionType.FP32
    
    def should_enable_quantization(
        self,
        gpu_memory_mb: int,
        model_size_mb: int,
        precision: PrecisionType
    ) -> QuantizationType:
        """
        Determine if quantization should be enabled based on memory constraints.
        
        Args:
            gpu_memory_mb: Available GPU memory in MB
            model_size_mb: Model size in MB
            precision: Current precision type
            
        Returns:
            Recommended quantization type
        """
        # Estimate memory needed with overhead
        overhead_multiplier = self.MEMORY_OVERHEAD_MULTIPLIER[precision]
        estimated_memory_needed = model_size_mb * overhead_multiplier
        
        # Apply safety margin
        usable_memory = gpu_memory_mb * self.MEMORY_SAFETY_MARGIN
        
        # If model fits comfortably, no quantization needed
        if estimated_memory_needed < usable_memory * 0.7:
            logger.info("Sufficient memory available - no quantization needed")
            return QuantizationType.NONE
        
        # If model barely fits, use 8-bit quantization
        if estimated_memory_needed < usable_memory:
            logger.info("Memory tight - recommending 8-bit quantization")
            return QuantizationType.INT8
        
        # If model doesn't fit, use 4-bit quantization
        logger.info("Insufficient memory - recommending 4-bit quantization")
        return QuantizationType.INT4
    
    def calculate_learning_rate(
        self,
        effective_batch_size: int,
        base_lr: Optional[float] = None
    ) -> float:
        """
        Calculate learning rate based on effective batch size.
        
        Uses square root scaling: lr = base_lr * sqrt(batch_size / base_batch_size)
        
        Args:
            effective_batch_size: Effective batch size (batch_size * grad_accum)
            base_lr: Base learning rate (default: 2e-4)
            
        Returns:
            Scaled learning rate
        """
        if base_lr is None:
            base_lr = self.BASE_LEARNING_RATE
        
        base_batch_size = 8  # Reference batch size
        
        if self.LR_SQRT_SCALING:
            # Square root scaling (more conservative)
            scale_factor = math.sqrt(effective_batch_size / base_batch_size)
        else:
            # Linear scaling
            scale_factor = effective_batch_size / base_batch_size
        
        learning_rate = base_lr * scale_factor
        
        # Clamp to reasonable range
        learning_rate = max(1e-6, min(learning_rate, 1e-3))
        
        logger.info(f"Calculated learning rate: {learning_rate:.2e} "
                   f"(effective batch size: {effective_batch_size})")
        
        return learning_rate
    
    def estimate_training_time(
        self,
        num_samples: int,
        batch_size: int,
        gradient_accumulation: int,
        num_epochs: int,
        tokens_per_second: Optional[float] = None,
        avg_seq_length: Optional[int] = None
    ) -> Tuple[float, float, float]:
        """
        Estimate training time using throughput benchmarks.
        
        Args:
            num_samples: Number of training samples
            batch_size: Batch size per step
            gradient_accumulation: Gradient accumulation steps
            num_epochs: Number of epochs
            tokens_per_second: Throughput in tokens/second (if available)
            avg_seq_length: Average sequence length
            
        Returns:
            Tuple of (min_hours, expected_hours, max_hours)
        """
        # Calculate total steps
        effective_batch_size = batch_size * gradient_accumulation
        steps_per_epoch = math.ceil(num_samples / effective_batch_size)
        total_steps = steps_per_epoch * num_epochs
        
        if tokens_per_second and avg_seq_length:
            # Use throughput benchmark
            total_tokens = num_samples * avg_seq_length * num_epochs
            seconds = total_tokens / tokens_per_second
            hours = seconds / 3600
            
            # Add 20% overhead for data loading, checkpointing, etc.
            overhead_factor = 1.2
            expected_hours = hours * overhead_factor
            
            # Provide confidence interval (±30%)
            min_hours = expected_hours * 0.7
            max_hours = expected_hours * 1.3
        else:
            # Rough estimate: 1-2 seconds per step
            seconds_per_step = 1.5
            expected_hours = (total_steps * seconds_per_step) / 3600
            
            # Confidence interval without benchmarks (±50%, capped at 3x min)
            min_hours = expected_hours * 0.5
            max_hours = expected_hours * 1.5
            # Ensure max is not more than 3x min
            if max_hours > min_hours * 3:
                max_hours = min_hours * 3
        
        logger.info(f"Estimated training time: {expected_hours:.2f}h "
                   f"(range: {min_hours:.2f}h - {max_hours:.2f}h)")
        
        return min_hours, expected_hours, max_hours
    
    def calculate_smart_defaults(
        self,
        hardware: HardwareSpecs,
        model: ModelSpecs,
        dataset: DatasetSpecs,
        target_effective_batch_size: int = 32
    ) -> SmartConfig:
        """
        Calculate complete smart configuration with all defaults.
        
        Args:
            hardware: Hardware specifications
            model: Model specifications
            dataset: Dataset specifications
            target_effective_batch_size: Desired effective batch size
            
        Returns:
            SmartConfig with all calculated parameters
        """
        logger.info("Calculating smart defaults...")
        
        explanations = {}
        
        # 1. Recommend precision
        precision = self.recommend_precision(
            compute_capability=hardware.compute_capability,
            gpu_memory_mb=hardware.gpu_memory_mb,
            model_size_mb=model.model_size_mb
        )
        explanations["precision"] = (
            f"Using {precision.value} precision based on your GPU's compute capability. "
            f"This provides a good balance of speed and accuracy."
        )
        
        # 2. Check if quantization is needed
        quantization = self.should_enable_quantization(
            gpu_memory_mb=hardware.gpu_memory_mb,
            model_size_mb=model.model_size_mb,
            precision=precision
        )
        
        if quantization != QuantizationType.NONE:
            explanations["quantization"] = (
                f"Enabling {quantization.value} quantization to fit the model in "
                f"{hardware.gpu_memory_mb}MB of GPU memory. This reduces memory usage "
                f"with minimal impact on quality."
            )
            # Adjust model size for quantization
            if quantization == QuantizationType.INT8:
                effective_model_size = model.model_size_mb * 0.5
            else:  # INT4
                effective_model_size = model.model_size_mb * 0.25
        else:
            effective_model_size = model.model_size_mb
            explanations["quantization"] = "No quantization needed - model fits comfortably in memory."
        
        # 3. Calculate batch size
        batch_size = self.calculate_batch_size(
            gpu_memory_mb=hardware.gpu_memory_mb,
            model_size_mb=effective_model_size,
            seq_length=model.max_seq_length,
            precision=precision
        )
        explanations["batch_size"] = (
            f"Batch size of {batch_size} maximizes GPU utilization while staying "
            f"within memory limits ({hardware.gpu_memory_mb}MB available)."
        )
        
        # 4. Calculate gradient accumulation
        gradient_accumulation = self.calculate_gradient_accumulation(
            target_batch_size=target_effective_batch_size,
            max_batch_size=batch_size
        )
        effective_batch_size = batch_size * gradient_accumulation
        
        if gradient_accumulation > 1:
            explanations["gradient_accumulation"] = (
                f"Using {gradient_accumulation} gradient accumulation steps to reach "
                f"effective batch size of {effective_batch_size}. This improves training "
                f"stability without requiring more memory."
            )
        else:
            explanations["gradient_accumulation"] = (
                f"No gradient accumulation needed - batch size of {batch_size} is sufficient."
            )
        
        # 5. Calculate learning rate
        learning_rate = self.calculate_learning_rate(effective_batch_size)
        explanations["learning_rate"] = (
            f"Learning rate of {learning_rate:.2e} is scaled based on effective batch size "
            f"of {effective_batch_size} for optimal convergence."
        )
        
        # 6. Estimate memory usage
        overhead_multiplier = self.MEMORY_OVERHEAD_MULTIPLIER[precision]
        estimated_memory_mb = int(effective_model_size * overhead_multiplier)
        # Ensure estimated memory doesn't exceed available GPU memory (cap at available)
        estimated_memory_mb = min(estimated_memory_mb, hardware.gpu_memory_mb)
        # Ensure memory utilization doesn't exceed 100% due to rounding
        memory_utilization = min(100.0, (estimated_memory_mb / hardware.gpu_memory_mb) * 100)
        
        explanations["memory"] = (
            f"Estimated memory usage: {estimated_memory_mb}MB "
            f"({memory_utilization:.1f}% of available {hardware.gpu_memory_mb}MB)"
        )
        
        # 7. Calculate training duration
        # Default to 3 epochs for fine-tuning
        num_epochs = 3
        explanations["epochs"] = (
            f"Using {num_epochs} epochs as a good starting point for fine-tuning. "
            f"You can adjust this based on your validation metrics."
        )
        
        # 8. Estimate training time
        avg_seq_length = dataset.avg_sequence_length or model.max_seq_length // 2
        min_hours, expected_hours, max_hours = self.estimate_training_time(
            num_samples=dataset.num_samples,
            batch_size=batch_size,
            gradient_accumulation=gradient_accumulation,
            num_epochs=num_epochs,
            tokens_per_second=None,  # Would come from benchmarks
            avg_seq_length=avg_seq_length
        )
        
        explanations["training_time"] = (
            f"Estimated training time: {expected_hours:.1f} hours "
            f"(range: {min_hours:.1f}h - {max_hours:.1f}h) for {dataset.num_samples} samples "
            f"over {num_epochs} epochs."
        )
        
        config = SmartConfig(
            batch_size=batch_size,
            gradient_accumulation_steps=gradient_accumulation,
            effective_batch_size=effective_batch_size,
            precision=precision,
            quantization=quantization,
            learning_rate=learning_rate,
            num_epochs=num_epochs,
            estimated_memory_mb=estimated_memory_mb,
            memory_utilization_percent=memory_utilization,
            estimated_training_time_hours=expected_hours,
            explanations=explanations
        )
        
        logger.info(f"Smart defaults calculated: batch_size={batch_size}, "
                   f"grad_accum={gradient_accumulation}, lr={learning_rate:.2e}, "
                   f"precision={precision.value}, quantization={quantization.value}")
        
        return config
    
    def suggest_configuration_alternatives(
        self,
        base_config: SmartConfig,
        hardware: HardwareSpecs,
        model: ModelSpecs,
        dataset: DatasetSpecs
    ) -> List['ConfigurationAlternative']:
        """
        Suggest alternative configurations that are faster or more resource-efficient.
        
        Args:
            base_config: The current/base configuration
            hardware: Hardware specifications
            model: Model specifications
            dataset: Dataset specifications
            
        Returns:
            List of ConfigurationAlternative objects with descriptions and trade-offs
        """
        alternatives = []
        
        # Alternative 1: Faster training with larger batch size (if memory allows)
        # Only suggest if we have significant memory headroom
        if base_config.memory_utilization_percent < 60:
            # We have memory headroom - try larger batch size
            larger_batch_size = min(base_config.batch_size * 2, 128)
            if larger_batch_size > base_config.batch_size:
                alt_config = self._create_alternative_config(
                    base_config=base_config,
                    hardware=hardware,
                    model=model,
                    dataset=dataset,
                    batch_size_override=larger_batch_size,
                    reduce_grad_accum=True  # Reduce gradient accumulation to maintain effective batch size
                )
                
                # Only add if it's actually faster (fewer total steps)
                if alt_config.estimated_training_time_hours < base_config.estimated_training_time_hours:
                    speedup = self._calculate_speedup(base_config, alt_config)
                    alternatives.append(ConfigurationAlternative(
                        config=alt_config,
                        description=(
                            f"Faster training with larger batch size ({larger_batch_size} vs {base_config.batch_size}). "
                            f"Reduces training time by ~{speedup:.0f}%."
                        ),
                        trade_offs=(
                            f"Uses more GPU memory ({alt_config.memory_utilization_percent:.1f}% vs "
                            f"{base_config.memory_utilization_percent:.1f}%). "
                            f"May require slightly different learning rate tuning."
                        )
                    ))
        
        # Alternative 2: More memory-efficient with quantization (if not already using it)
        if base_config.quantization == QuantizationType.NONE:
            # Try 8-bit quantization
            alt_config = self._create_alternative_config(
                base_config=base_config,
                hardware=hardware,
                model=model,
                dataset=dataset,
                quantization_override=QuantizationType.INT8
            )
            
            memory_savings = base_config.estimated_memory_mb - alt_config.estimated_memory_mb
            memory_savings_percent = (memory_savings / base_config.estimated_memory_mb) * 100
            
            alternatives.append(ConfigurationAlternative(
                config=alt_config,
                description=(
                    f"More memory-efficient with 8-bit quantization. "
                    f"Saves ~{memory_savings_percent:.0f}% GPU memory ({memory_savings}MB)."
                ),
                trade_offs=(
                    f"Slightly reduced precision may affect final model quality. "
                    f"Generally minimal impact for fine-tuning tasks."
                )
            ))
        
        # Alternative 3: Faster training with fewer epochs (if epochs > 1)
        if base_config.num_epochs > 1:
            reduced_epochs = max(1, base_config.num_epochs - 1)
            alt_config = self._create_alternative_config(
                base_config=base_config,
                hardware=hardware,
                model=model,
                dataset=dataset,
                epochs_override=reduced_epochs
            )
            
            time_savings_percent = (
                (base_config.estimated_training_time_hours - alt_config.estimated_training_time_hours) /
                base_config.estimated_training_time_hours * 100
            )
            
            alternatives.append(ConfigurationAlternative(
                config=alt_config,
                description=(
                    f"Faster training with fewer epochs ({reduced_epochs} vs {base_config.num_epochs}). "
                    f"Reduces training time by ~{time_savings_percent:.0f}%."
                ),
                trade_offs=(
                    f"Model may not be fully converged. Monitor validation loss to ensure "
                    f"adequate training. Can always train for more epochs if needed."
                )
            ))
        
        # Alternative 4: Balanced approach with gradient accumulation (if not already using it much)
        if base_config.gradient_accumulation_steps == 1 and base_config.batch_size > 2:
            # Reduce batch size, increase gradient accumulation
            smaller_batch = max(1, base_config.batch_size // 2)
            new_grad_accum = base_config.gradient_accumulation_steps * 2
            
            alt_config = self._create_alternative_config(
                base_config=base_config,
                hardware=hardware,
                model=model,
                dataset=dataset,
                batch_size_override=smaller_batch,
                grad_accum_override=new_grad_accum
            )
            
            # Only add if it's actually more memory efficient
            if alt_config.estimated_memory_mb < base_config.estimated_memory_mb:
                alternatives.append(ConfigurationAlternative(
                    config=alt_config,
                    description=(
                        f"More memory-efficient with gradient accumulation. "
                        f"Reduces memory usage to {alt_config.memory_utilization_percent:.1f}% "
                        f"while maintaining effective batch size of {alt_config.effective_batch_size}."
                    ),
                    trade_offs=(
                        f"Slightly slower training due to more gradient accumulation steps. "
                        f"Frees up memory for other tasks or larger models."
                    )
                ))
        
        # Note: We do NOT suggest "higher precision" alternatives because they are neither
        # faster nor more efficient - they may improve quality but use more resources.
        # Per Requirement 9.5, we only suggest faster or more efficient alternatives.
        
        logger.info(f"Generated {len(alternatives)} configuration alternatives")
        return alternatives
    
    def _create_alternative_config(
        self,
        base_config: SmartConfig,
        hardware: HardwareSpecs,
        model: ModelSpecs,
        dataset: DatasetSpecs,
        batch_size_override: Optional[int] = None,
        grad_accum_override: Optional[int] = None,
        epochs_override: Optional[int] = None,
        quantization_override: Optional[QuantizationType] = None,
        precision_override: Optional[PrecisionType] = None,
        reduce_grad_accum: bool = False
    ) -> SmartConfig:
        """
        Create an alternative configuration with specific overrides.
        
        Args:
            base_config: Base configuration to modify
            hardware: Hardware specifications
            model: Model specifications
            dataset: Dataset specifications
            batch_size_override: Override batch size
            grad_accum_override: Override gradient accumulation
            epochs_override: Override number of epochs
            quantization_override: Override quantization type
            precision_override: Override precision type
            
        Returns:
            New SmartConfig with overrides applied
        """
        # Start with base config values
        batch_size = batch_size_override if batch_size_override is not None else base_config.batch_size
        grad_accum = grad_accum_override if grad_accum_override is not None else base_config.gradient_accumulation_steps
        
        # If we're increasing batch size and want to reduce gradient accumulation
        if reduce_grad_accum and batch_size_override and batch_size_override > base_config.batch_size:
            # Reduce gradient accumulation proportionally
            grad_accum = max(1, base_config.gradient_accumulation_steps // 2)
        
        num_epochs = epochs_override if epochs_override is not None else base_config.num_epochs
        quantization = quantization_override if quantization_override is not None else base_config.quantization
        precision = precision_override if precision_override is not None else base_config.precision
        
        # Recalculate dependent values
        effective_batch_size = batch_size * grad_accum
        learning_rate = self.calculate_learning_rate(effective_batch_size)
        
        # Adjust model size based on quantization
        if quantization == QuantizationType.INT8:
            effective_model_size = model.model_size_mb * 0.5
        elif quantization == QuantizationType.INT4:
            effective_model_size = model.model_size_mb * 0.25
        else:
            effective_model_size = model.model_size_mb
        
        # Recalculate memory usage
        overhead_multiplier = self.MEMORY_OVERHEAD_MULTIPLIER[precision]
        estimated_memory_mb = int(effective_model_size * overhead_multiplier)
        # Cap at available GPU memory
        estimated_memory_mb = min(estimated_memory_mb, hardware.gpu_memory_mb)
        memory_utilization = min(100.0, (estimated_memory_mb / hardware.gpu_memory_mb) * 100)
        
        # Recalculate training time
        avg_seq_length = dataset.avg_sequence_length or model.max_seq_length // 2
        min_hours, expected_hours, max_hours = self.estimate_training_time(
            num_samples=dataset.num_samples,
            batch_size=batch_size,
            gradient_accumulation=grad_accum,
            num_epochs=num_epochs,
            tokens_per_second=None,
            avg_seq_length=avg_seq_length
        )
        
        return SmartConfig(
            batch_size=batch_size,
            gradient_accumulation_steps=grad_accum,
            effective_batch_size=effective_batch_size,
            precision=precision,
            quantization=quantization,
            learning_rate=learning_rate,
            num_epochs=num_epochs,
            estimated_memory_mb=estimated_memory_mb,
            memory_utilization_percent=memory_utilization,
            estimated_training_time_hours=expected_hours,
            explanations={}  # Alternatives don't need detailed explanations
        )
    
    def _calculate_speedup(self, base_config: SmartConfig, alt_config: SmartConfig) -> float:
        """
        Calculate speedup percentage between two configurations.
        
        Args:
            base_config: Base configuration
            alt_config: Alternative configuration
            
        Returns:
            Speedup percentage (positive means faster)
        """
        if (base_config.estimated_training_time_hours is None or 
            alt_config.estimated_training_time_hours is None):
            return 0.0
        
        time_saved = base_config.estimated_training_time_hours - alt_config.estimated_training_time_hours
        speedup_percent = (time_saved / base_config.estimated_training_time_hours) * 100
        return speedup_percent
    
    @staticmethod
    def _round_to_power_of_2(n: int) -> int:
        """Round down to nearest power of 2"""
        if n <= 0:
            return 1
        power = int(math.log2(n))
        return 2 ** power


# Singleton instance
_smart_config_engine_instance = None


def get_smart_config_engine() -> SmartConfigEngine:
    """Get singleton instance of SmartConfigEngine"""
    global _smart_config_engine_instance
    if _smart_config_engine_instance is None:
        _smart_config_engine_instance = SmartConfigEngine()
    return _smart_config_engine_instance
