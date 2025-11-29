"""
Optimization Profile Service for managing pre-configured training profiles.
Provides 6 built-in profiles optimized for common use cases.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class UseCase(str, Enum):
    """Supported use cases for optimization profiles"""
    CHATBOT = "chatbot"
    CODE_GENERATION = "code-generation"
    SUMMARIZATION = "summarization"
    QA = "qa"
    CREATIVE_WRITING = "creative-writing"
    DOMAIN_ADAPTATION = "domain-adaptation"


@dataclass
class ProfileConfig:
    """Configuration parameters for an optimization profile"""
    # LoRA parameters
    lora_r: int
    lora_alpha: int
    lora_dropout: float
    target_modules: List[str]
    
    # Training hyperparameters
    learning_rate: float
    num_epochs: int
    warmup_ratio: float
    max_seq_length: int
    
    # Optimization settings
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    scheduler: str = "cosine"
    
    def __post_init__(self):
        """Validate configuration parameters"""
        if self.lora_r <= 0:
            raise ValueError(f"lora_r must be positive, got {self.lora_r}")
        if self.lora_alpha <= 0:
            raise ValueError(f"lora_alpha must be positive, got {self.lora_alpha}")
        if not 0.0 <= self.lora_dropout <= 1.0:
            raise ValueError(f"lora_dropout must be in [0, 1], got {self.lora_dropout}")
        if not self.target_modules:
            raise ValueError("target_modules cannot be empty")
        if self.learning_rate <= 0:
            raise ValueError(f"learning_rate must be positive, got {self.learning_rate}")
        if self.num_epochs <= 0:
            raise ValueError(f"num_epochs must be positive, got {self.num_epochs}")
        if not 0.0 <= self.warmup_ratio <= 1.0:
            raise ValueError(f"warmup_ratio must be in [0, 1], got {self.warmup_ratio}")
        if self.max_seq_length <= 0:
            raise ValueError(f"max_seq_length must be positive, got {self.max_seq_length}")


@dataclass
class HardwareRequirements:
    """Hardware requirements for a profile"""
    min_gpu_memory_gb: float
    recommended_gpu_memory_gb: float
    min_dataset_size: int
    recommended_dataset_size: int
    estimated_time_per_epoch_minutes: float  # For a 7B model on typical hardware


@dataclass
class OptimizationProfile:
    """Complete optimization profile with metadata and configuration"""
    id: str
    name: str
    description: str
    use_case: UseCase
    icon: str
    example_use_cases: List[str]
    config: ProfileConfig
    requirements: HardwareRequirements
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert profile to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "use_case": self.use_case.value,
            "icon": self.icon,
            "example_use_cases": self.example_use_cases,
            "config": {
                "lora_r": self.config.lora_r,
                "lora_alpha": self.config.lora_alpha,
                "lora_dropout": self.config.lora_dropout,
                "target_modules": self.config.target_modules,
                "learning_rate": self.config.learning_rate,
                "num_epochs": self.config.num_epochs,
                "warmup_ratio": self.config.warmup_ratio,
                "max_seq_length": self.config.max_seq_length,
                "weight_decay": self.config.weight_decay,
                "max_grad_norm": self.config.max_grad_norm,
                "scheduler": self.config.scheduler
            },
            "requirements": {
                "min_gpu_memory_gb": self.requirements.min_gpu_memory_gb,
                "recommended_gpu_memory_gb": self.requirements.recommended_gpu_memory_gb,
                "min_dataset_size": self.requirements.min_dataset_size,
                "recommended_dataset_size": self.requirements.recommended_dataset_size,
                "estimated_time_per_epoch_minutes": self.requirements.estimated_time_per_epoch_minutes
            },
            "tags": self.tags
        }


class ProfileService:
    """Service for managing optimization profiles"""
    
    def __init__(self):
        self._profiles: Dict[str, OptimizationProfile] = {}
        self._initialize_builtin_profiles()
        logger.info(f"ProfileService initialized with {len(self._profiles)} built-in profiles")
    
    def _initialize_builtin_profiles(self):
        """Initialize the 6 built-in optimization profiles"""
        
        # 1. Chatbot Assistant Profile
        chatbot_profile = OptimizationProfile(
            id="chatbot",
            name="Chatbot Assistant",
            description="Optimized for conversational AI with natural dialogue flow and context awareness",
            use_case=UseCase.CHATBOT,
            icon="💬",
            example_use_cases=[
                "Customer support chatbots",
                "Personal AI assistants",
                "Interactive tutoring systems",
                "Conversational agents"
            ],
            config=ProfileConfig(
                lora_r=16,
                lora_alpha=32,
                lora_dropout=0.05,
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
                learning_rate=2e-4,
                num_epochs=3,
                warmup_ratio=0.1,
                max_seq_length=2048,
                weight_decay=0.01,
                max_grad_norm=1.0,
                scheduler="cosine"
            ),
            requirements=HardwareRequirements(
                min_gpu_memory_gb=8.0,
                recommended_gpu_memory_gb=16.0,
                min_dataset_size=500,
                recommended_dataset_size=5000,
                estimated_time_per_epoch_minutes=30.0
            ),
            tags=["conversational", "dialogue", "chat", "assistant"]
        )
        
        # 2. Code Generation Profile
        code_generation_profile = OptimizationProfile(
            id="code-generation",
            name="Code Generation",
            description="Syntax-aware settings optimized for programming tasks and code completion",
            use_case=UseCase.CODE_GENERATION,
            icon="💻",
            example_use_cases=[
                "Code completion and suggestions",
                "Bug fixing and refactoring",
                "Documentation generation",
                "Code translation between languages"
            ],
            config=ProfileConfig(
                lora_r=32,
                lora_alpha=64,
                lora_dropout=0.1,
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
                learning_rate=1e-4,
                num_epochs=5,
                warmup_ratio=0.05,
                max_seq_length=4096,
                weight_decay=0.05,
                max_grad_norm=0.5,
                scheduler="linear"
            ),
            requirements=HardwareRequirements(
                min_gpu_memory_gb=12.0,
                recommended_gpu_memory_gb=24.0,
                min_dataset_size=1000,
                recommended_dataset_size=10000,
                estimated_time_per_epoch_minutes=45.0
            ),
            tags=["code", "programming", "syntax", "completion"]
        )
        
        # 3. Text Summarization Profile
        summarization_profile = OptimizationProfile(
            id="summarization",
            name="Text Summarization",
            description="Efficient settings for document processing and content condensation",
            use_case=UseCase.SUMMARIZATION,
            icon="📝",
            example_use_cases=[
                "Document summarization",
                "News article condensation",
                "Meeting notes generation",
                "Research paper abstracts"
            ],
            config=ProfileConfig(
                lora_r=8,
                lora_alpha=16,
                lora_dropout=0.05,
                target_modules=["q_proj", "v_proj", "o_proj"],
                learning_rate=3e-4,
                num_epochs=4,
                warmup_ratio=0.1,
                max_seq_length=2048,
                weight_decay=0.01,
                max_grad_norm=1.0,
                scheduler="cosine"
            ),
            requirements=HardwareRequirements(
                min_gpu_memory_gb=6.0,
                recommended_gpu_memory_gb=12.0,
                min_dataset_size=300,
                recommended_dataset_size=3000,
                estimated_time_per_epoch_minutes=20.0
            ),
            tags=["summarization", "condensation", "extraction", "documents"]
        )
        
        # 4. Question Answering Profile
        qa_profile = OptimizationProfile(
            id="qa",
            name="Question Answering",
            description="Focused on factual accuracy and information retrieval",
            use_case=UseCase.QA,
            icon="❓",
            example_use_cases=[
                "FAQ systems",
                "Knowledge base queries",
                "Educational Q&A",
                "Information extraction"
            ],
            config=ProfileConfig(
                lora_r=16,
                lora_alpha=32,
                lora_dropout=0.05,
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
                learning_rate=2e-4,
                num_epochs=3,
                warmup_ratio=0.1,
                max_seq_length=1024,
                weight_decay=0.01,
                max_grad_norm=1.0,
                scheduler="cosine"
            ),
            requirements=HardwareRequirements(
                min_gpu_memory_gb=6.0,
                recommended_gpu_memory_gb=12.0,
                min_dataset_size=500,
                recommended_dataset_size=5000,
                estimated_time_per_epoch_minutes=25.0
            ),
            tags=["qa", "questions", "answers", "factual", "knowledge"]
        )
        
        # 5. Creative Writing Profile
        creative_writing_profile = OptimizationProfile(
            id="creative-writing",
            name="Creative Writing",
            description="Higher temperature settings for diverse and creative text generation",
            use_case=UseCase.CREATIVE_WRITING,
            icon="✍️",
            example_use_cases=[
                "Story generation",
                "Poetry and creative content",
                "Marketing copy",
                "Content ideation"
            ],
            config=ProfileConfig(
                lora_r=24,
                lora_alpha=48,
                lora_dropout=0.1,
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
                learning_rate=1.5e-4,
                num_epochs=4,
                warmup_ratio=0.15,
                max_seq_length=2048,
                weight_decay=0.005,
                max_grad_norm=1.5,
                scheduler="cosine"
            ),
            requirements=HardwareRequirements(
                min_gpu_memory_gb=8.0,
                recommended_gpu_memory_gb=16.0,
                min_dataset_size=500,
                recommended_dataset_size=5000,
                estimated_time_per_epoch_minutes=35.0
            ),
            tags=["creative", "writing", "generation", "storytelling"]
        )
        
        # 6. Domain Adaptation Profile
        domain_adaptation_profile = OptimizationProfile(
            id="domain-adaptation",
            name="Domain Adaptation",
            description="General-purpose fine-tuning for adapting models to specific domains",
            use_case=UseCase.DOMAIN_ADAPTATION,
            icon="🎯",
            example_use_cases=[
                "Medical/legal domain adaptation",
                "Industry-specific terminology",
                "Custom knowledge integration",
                "Specialized vocabulary"
            ],
            config=ProfileConfig(
                lora_r=16,
                lora_alpha=32,
                lora_dropout=0.05,
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
                learning_rate=2e-4,
                num_epochs=5,
                warmup_ratio=0.1,
                max_seq_length=2048,
                weight_decay=0.01,
                max_grad_norm=1.0,
                scheduler="cosine"
            ),
            requirements=HardwareRequirements(
                min_gpu_memory_gb=8.0,
                recommended_gpu_memory_gb=16.0,
                min_dataset_size=1000,
                recommended_dataset_size=10000,
                estimated_time_per_epoch_minutes=40.0
            ),
            tags=["domain", "adaptation", "specialized", "custom"]
        )
        
        # Register all profiles
        self._profiles[chatbot_profile.id] = chatbot_profile
        self._profiles[code_generation_profile.id] = code_generation_profile
        self._profiles[summarization_profile.id] = summarization_profile
        self._profiles[qa_profile.id] = qa_profile
        self._profiles[creative_writing_profile.id] = creative_writing_profile
        self._profiles[domain_adaptation_profile.id] = domain_adaptation_profile
    
    def get_profile(self, profile_id: str) -> Optional[OptimizationProfile]:
        """
        Get a specific optimization profile by ID.
        
        Args:
            profile_id: Profile identifier
            
        Returns:
            OptimizationProfile if found, None otherwise
        """
        return self._profiles.get(profile_id)
    
    def get_profile_by_use_case(self, use_case: UseCase) -> Optional[OptimizationProfile]:
        """
        Get a profile by use case.
        
        Args:
            use_case: UseCase enum value
            
        Returns:
            OptimizationProfile if found, None otherwise
        """
        for profile in self._profiles.values():
            if profile.use_case == use_case:
                return profile
        return None
    
    def list_profiles(self) -> List[OptimizationProfile]:
        """
        Get all available optimization profiles.
        
        Returns:
            List of all OptimizationProfile objects
        """
        return list(self._profiles.values())
    
    def list_profile_ids(self) -> List[str]:
        """
        Get list of all profile IDs.
        
        Returns:
            List of profile ID strings
        """
        return list(self._profiles.keys())
    
    def apply_profile_config(
        self,
        profile_id: str,
        overrides: Optional[Dict] = None
    ) -> Dict:
        """
        Apply a profile configuration with optional parameter overrides.
        
        Args:
            profile_id: Profile identifier
            overrides: Optional dictionary of parameters to override
            
        Returns:
            Complete configuration dictionary
            
        Raises:
            ValueError: If profile_id is not found
        """
        profile = self.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile not found: {profile_id}")
        
        # Start with profile configuration
        config = profile.to_dict()["config"].copy()
        
        # Apply overrides if provided
        if overrides:
            for key, value in overrides.items():
                if key in config:
                    config[key] = value
                    logger.info(f"Override applied: {key} = {value}")
        
        return config
    
    def validate_profile_compatibility(
        self,
        profile_id: str,
        gpu_memory_gb: float,
        dataset_size: int
    ) -> Dict[str, any]:
        """
        Validate if hardware and dataset meet profile requirements.
        
        Args:
            profile_id: Profile identifier
            gpu_memory_gb: Available GPU memory in GB
            dataset_size: Number of training samples
            
        Returns:
            Dictionary with compatibility status and warnings
        """
        profile = self.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile not found: {profile_id}")
        
        warnings = []
        is_compatible = True
        
        # Check GPU memory
        if gpu_memory_gb < profile.requirements.min_gpu_memory_gb:
            is_compatible = False
            warnings.append(
                f"Insufficient GPU memory: {gpu_memory_gb:.1f}GB available, "
                f"{profile.requirements.min_gpu_memory_gb:.1f}GB required minimum"
            )
        elif gpu_memory_gb < profile.requirements.recommended_gpu_memory_gb:
            warnings.append(
                f"GPU memory below recommended: {gpu_memory_gb:.1f}GB available, "
                f"{profile.requirements.recommended_gpu_memory_gb:.1f}GB recommended"
            )
        
        # Check dataset size
        if dataset_size < profile.requirements.min_dataset_size:
            is_compatible = False
            warnings.append(
                f"Insufficient dataset size: {dataset_size} samples, "
                f"{profile.requirements.min_dataset_size} required minimum"
            )
        elif dataset_size < profile.requirements.recommended_dataset_size:
            warnings.append(
                f"Dataset size below recommended: {dataset_size} samples, "
                f"{profile.requirements.recommended_dataset_size} recommended"
            )
        
        return {
            "compatible": is_compatible,
            "warnings": warnings,
            "profile_name": profile.name,
            "requirements": profile.to_dict()["requirements"]
        }


# Singleton instance
_profile_service_instance = None


def get_profile_service() -> ProfileService:
    """Get singleton instance of ProfileService"""
    global _profile_service_instance
    if _profile_service_instance is None:
        _profile_service_instance = ProfileService()
    return _profile_service_instance
