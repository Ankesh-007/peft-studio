"""
Cloud Platform Integration Service

This service integrates with cloud GPU providers:
- RunPod API for GPU rental
- Lambda Labs for H100/A100 access
- Together AI for serverless endpoints
- Cost comparison across platforms
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PlatformType(Enum):
    """Cloud platform types"""
    LOCAL = "local"
    RUNPOD = "runpod"
    LAMBDA_LABS = "lambda_labs"
    TOGETHER_AI = "together_ai"


class GPUType(Enum):
    """GPU types available across platforms"""
    RTX_4090 = "RTX 4090"
    RTX_3090 = "RTX 3090"
    A100_40GB = "A100 40GB"
    A100_80GB = "A100 80GB"
    H100 = "H100"
    A10 = "A10"
    V100 = "V100"
    T4 = "T4"


@dataclass
class GPUInstance:
    """GPU instance configuration"""
    platform: PlatformType
    gpu_type: GPUType
    gpu_count: int
    memory_gb: int
    vcpus: int
    ram_gb: int
    storage_gb: int
    hourly_rate_usd: float
    availability: str  # "high", "medium", "low", "unavailable"
    region: str
    instance_id: Optional[str] = None


@dataclass
class PlatformCostEstimate:
    """Cost estimate for a specific platform"""
    platform: PlatformType
    instance: GPUInstance
    training_hours: float
    total_cost_usd: float
    setup_time_minutes: float
    estimated_start_time: str  # "immediate", "5-10 min", "30+ min"
    pros: List[str]
    cons: List[str]


@dataclass
class CostComparison:
    """Comparison of costs across platforms"""
    local_estimate: Optional[PlatformCostEstimate]
    cloud_estimates: List[PlatformCostEstimate]
    cheapest_option: PlatformCostEstimate
    fastest_option: PlatformCostEstimate
    recommended_option: PlatformCostEstimate
    savings_vs_local: Optional[float]  # Percentage saved vs local


class CloudPlatformService:
    """
    Service for integrating with cloud GPU platforms and comparing costs.
    """
    
    # RunPod pricing (as of 2024, approximate)
    RUNPOD_PRICING = {
        GPUType.RTX_4090: {"hourly": 0.69, "memory_gb": 24, "vcpus": 16, "ram_gb": 64},
        GPUType.RTX_3090: {"hourly": 0.44, "memory_gb": 24, "vcpus": 12, "ram_gb": 48},
        GPUType.A100_40GB: {"hourly": 1.89, "memory_gb": 40, "vcpus": 24, "ram_gb": 128},
        GPUType.A100_80GB: {"hourly": 2.49, "memory_gb": 80, "vcpus": 32, "ram_gb": 256},
        GPUType.H100: {"hourly": 4.25, "memory_gb": 80, "vcpus": 48, "ram_gb": 384},
        GPUType.A10: {"hourly": 0.79, "memory_gb": 24, "vcpus": 12, "ram_gb": 64},
    }
    
    # Lambda Labs pricing (as of 2024, approximate)
    LAMBDA_LABS_PRICING = {
        GPUType.RTX_3090: {"hourly": 0.50, "memory_gb": 24, "vcpus": 14, "ram_gb": 46},
        GPUType.A100_40GB: {"hourly": 1.10, "memory_gb": 40, "vcpus": 30, "ram_gb": 200},
        GPUType.A100_80GB: {"hourly": 1.29, "memory_gb": 80, "vcpus": 30, "ram_gb": 200},
        GPUType.H100: {"hourly": 2.49, "memory_gb": 80, "vcpus": 52, "ram_gb": 200},
        GPUType.V100: {"hourly": 0.50, "memory_gb": 16, "vcpus": 14, "ram_gb": 46},
    }
    
    # Together AI pricing (serverless, per token/request)
    # Converted to approximate hourly equivalent for comparison
    TOGETHER_AI_PRICING = {
        GPUType.A100_80GB: {"hourly": 2.00, "memory_gb": 80, "vcpus": 32, "ram_gb": 256},
        GPUType.H100: {"hourly": 3.50, "memory_gb": 80, "vcpus": 48, "ram_gb": 384},
    }
    
    def __init__(self):
        logger.info("CloudPlatformService initialized")
    
    def get_runpod_instances(
        self,
        gpu_type: Optional[GPUType] = None,
        min_memory_gb: Optional[int] = None
    ) -> List[GPUInstance]:
        """
        Get available RunPod instances.
        
        Args:
            gpu_type: Filter by GPU type
            min_memory_gb: Minimum GPU memory required
            
        Returns:
            List of available GPU instances
        """
        instances = []
        
        for gpu, specs in self.RUNPOD_PRICING.items():
            # Apply filters
            if gpu_type and gpu != gpu_type:
                continue
            if min_memory_gb and specs["memory_gb"] < min_memory_gb:
                continue
            
            instance = GPUInstance(
                platform=PlatformType.RUNPOD,
                gpu_type=gpu,
                gpu_count=1,
                memory_gb=specs["memory_gb"],
                vcpus=specs["vcpus"],
                ram_gb=specs["ram_gb"],
                storage_gb=200,  # Standard storage
                hourly_rate_usd=specs["hourly"],
                availability="high",  # RunPod typically has good availability
                region="US-Central"
            )
            instances.append(instance)
        
        logger.info(f"Found {len(instances)} RunPod instances")
        return instances
    
    def get_lambda_labs_instances(
        self,
        gpu_type: Optional[GPUType] = None,
        min_memory_gb: Optional[int] = None
    ) -> List[GPUInstance]:
        """
        Get available Lambda Labs instances.
        
        Args:
            gpu_type: Filter by GPU type
            min_memory_gb: Minimum GPU memory required
            
        Returns:
            List of available GPU instances
        """
        instances = []
        
        for gpu, specs in self.LAMBDA_LABS_PRICING.items():
            # Apply filters
            if gpu_type and gpu != gpu_type:
                continue
            if min_memory_gb and specs["memory_gb"] < min_memory_gb:
                continue
            
            instance = GPUInstance(
                platform=PlatformType.LAMBDA_LABS,
                gpu_type=gpu,
                gpu_count=1,
                memory_gb=specs["memory_gb"],
                vcpus=specs["vcpus"],
                ram_gb=specs["ram_gb"],
                storage_gb=512,  # Lambda Labs provides more storage
                hourly_rate_usd=specs["hourly"],
                availability="medium",  # Lambda Labs can have limited availability
                region="US-West"
            )
            instances.append(instance)
        
        logger.info(f"Found {len(instances)} Lambda Labs instances")
        return instances
    
    def get_together_ai_instances(
        self,
        gpu_type: Optional[GPUType] = None,
        min_memory_gb: Optional[int] = None
    ) -> List[GPUInstance]:
        """
        Get available Together AI serverless endpoints.
        
        Args:
            gpu_type: Filter by GPU type
            min_memory_gb: Minimum GPU memory required
            
        Returns:
            List of available GPU instances
        """
        instances = []
        
        for gpu, specs in self.TOGETHER_AI_PRICING.items():
            # Apply filters
            if gpu_type and gpu != gpu_type:
                continue
            if min_memory_gb and specs["memory_gb"] < min_memory_gb:
                continue
            
            instance = GPUInstance(
                platform=PlatformType.TOGETHER_AI,
                gpu_type=gpu,
                gpu_count=1,
                memory_gb=specs["memory_gb"],
                vcpus=specs["vcpus"],
                ram_gb=specs["ram_gb"],
                storage_gb=1000,  # Serverless, flexible storage
                hourly_rate_usd=specs["hourly"],
                availability="high",  # Serverless typically has high availability
                region="Multi-Region"
            )
            instances.append(instance)
        
        logger.info(f"Found {len(instances)} Together AI instances")
        return instances
    
    def get_all_cloud_instances(
        self,
        gpu_type: Optional[GPUType] = None,
        min_memory_gb: Optional[int] = None
    ) -> List[GPUInstance]:
        """
        Get all available cloud instances across platforms.
        
        Args:
            gpu_type: Filter by GPU type
            min_memory_gb: Minimum GPU memory required
            
        Returns:
            List of all available GPU instances
        """
        instances = []
        
        instances.extend(self.get_runpod_instances(gpu_type, min_memory_gb))
        instances.extend(self.get_lambda_labs_instances(gpu_type, min_memory_gb))
        instances.extend(self.get_together_ai_instances(gpu_type, min_memory_gb))
        
        # Sort by hourly rate
        instances.sort(key=lambda x: x.hourly_rate_usd)
        
        logger.info(f"Found {len(instances)} total cloud instances")
        return instances
    
    def calculate_platform_cost(
        self,
        instance: GPUInstance,
        training_hours: float
    ) -> PlatformCostEstimate:
        """
        Calculate cost estimate for a specific platform instance.
        
        Args:
            instance: GPU instance configuration
            training_hours: Estimated training time in hours
            
        Returns:
            Platform cost estimate
        """
        total_cost = instance.hourly_rate_usd * training_hours
        
        # Determine setup time and start time based on platform
        if instance.platform == PlatformType.RUNPOD:
            setup_time = 5.0
            start_time = "5-10 min"
            pros = [
                "Fast deployment",
                "Good GPU availability",
                "Flexible billing (per-minute)",
                "Easy to use interface"
            ]
            cons = [
                "Slightly higher prices than Lambda Labs",
                "Network storage can be slower"
            ]
        elif instance.platform == PlatformType.LAMBDA_LABS:
            setup_time = 3.0
            start_time = "immediate" if instance.availability == "high" else "30+ min"
            pros = [
                "Lowest prices for A100/H100",
                "Fast NVMe storage",
                "Excellent network bandwidth",
                "Pre-configured ML environments"
            ]
            cons = [
                "Limited availability (high demand)",
                "Hourly billing minimum",
                "May need to wait for instances"
            ]
        elif instance.platform == PlatformType.TOGETHER_AI:
            setup_time = 1.0
            start_time = "immediate"
            pros = [
                "Instant availability (serverless)",
                "No setup required",
                "Auto-scaling",
                "Pay only for actual usage"
            ]
            cons = [
                "Higher per-hour equivalent cost",
                "Less control over environment",
                "May have cold start delays"
            ]
        else:
            setup_time = 0.0
            start_time = "immediate"
            pros = ["Full control", "No network latency", "Data privacy"]
            cons = ["Upfront hardware cost", "Maintenance required"]
        
        estimate = PlatformCostEstimate(
            platform=instance.platform,
            instance=instance,
            training_hours=training_hours,
            total_cost_usd=total_cost,
            setup_time_minutes=setup_time,
            estimated_start_time=start_time,
            pros=pros,
            cons=cons
        )
        
        logger.info(f"Calculated cost for {instance.platform.value}: ${total_cost:.2f}")
        return estimate
    
    def compare_costs(
        self,
        training_hours: float,
        local_gpu_type: Optional[GPUType] = None,
        local_electricity_cost: Optional[float] = None,
        min_memory_gb: Optional[int] = None
    ) -> CostComparison:
        """
        Compare costs across all platforms.
        
        Args:
            training_hours: Estimated training time in hours
            local_gpu_type: Local GPU type (if available)
            local_electricity_cost: Local electricity cost for training
            min_memory_gb: Minimum GPU memory required
            
        Returns:
            Cost comparison across platforms
        """
        logger.info(f"Comparing costs for {training_hours:.2f}h training")
        
        # Get local estimate if available
        local_estimate = None
        if local_gpu_type and local_electricity_cost is not None:
            local_instance = GPUInstance(
                platform=PlatformType.LOCAL,
                gpu_type=local_gpu_type,
                gpu_count=1,
                memory_gb=self._get_gpu_memory(local_gpu_type),
                vcpus=0,
                ram_gb=0,
                storage_gb=0,
                hourly_rate_usd=local_electricity_cost / training_hours,
                availability="high",
                region="Local"
            )
            local_estimate = self.calculate_platform_cost(local_instance, training_hours)
        
        # Get cloud estimates
        cloud_instances = self.get_all_cloud_instances(min_memory_gb=min_memory_gb)
        cloud_estimates = [
            self.calculate_platform_cost(instance, training_hours)
            for instance in cloud_instances
        ]
        
        # Find cheapest option
        all_estimates = cloud_estimates + ([local_estimate] if local_estimate else [])
        cheapest = min(all_estimates, key=lambda x: x.total_cost_usd)
        
        # Find fastest option (lowest setup time + training time)
        fastest = min(
            all_estimates,
            key=lambda x: x.setup_time_minutes / 60 + training_hours
        )
        
        # Recommend based on balance of cost and convenience
        # Prefer cloud if cost difference is < 20% and setup is faster
        if local_estimate:
            cloud_cheapest = min(cloud_estimates, key=lambda x: x.total_cost_usd)
            cost_diff_pct = (
                (cloud_cheapest.total_cost_usd - local_estimate.total_cost_usd) /
                local_estimate.total_cost_usd * 100
            )
            
            if cost_diff_pct < 20 and cloud_cheapest.setup_time_minutes < 10:
                recommended = cloud_cheapest
            else:
                recommended = cheapest
        else:
            recommended = cheapest
        
        # Calculate savings vs local
        savings_vs_local = None
        if local_estimate and cheapest.platform != PlatformType.LOCAL:
            savings_vs_local = (
                (local_estimate.total_cost_usd - cheapest.total_cost_usd) /
                local_estimate.total_cost_usd * 100
            )
        
        comparison = CostComparison(
            local_estimate=local_estimate,
            cloud_estimates=cloud_estimates,
            cheapest_option=cheapest,
            fastest_option=fastest,
            recommended_option=recommended,
            savings_vs_local=savings_vs_local
        )
        
        logger.info(f"Cost comparison complete. Cheapest: {cheapest.platform.value} "
                   f"(${cheapest.total_cost_usd:.2f})")
        
        return comparison
    
    def _get_gpu_memory(self, gpu_type: GPUType) -> int:
        """Get memory for a GPU type"""
        memory_map = {
            GPUType.RTX_4090: 24,
            GPUType.RTX_3090: 24,
            GPUType.A100_40GB: 40,
            GPUType.A100_80GB: 80,
            GPUType.H100: 80,
            GPUType.A10: 24,
            GPUType.V100: 16,
            GPUType.T4: 16,
        }
        return memory_map.get(gpu_type, 24)
    
    def format_cost_comparison(self, comparison: CostComparison) -> Dict:
        """
        Format cost comparison into human-readable structure.
        
        Args:
            comparison: Cost comparison object
            
        Returns:
            Dictionary with formatted comparison data
        """
        result = {
            "summary": {
                "cheapest": {
                    "platform": comparison.cheapest_option.platform.value,
                    "cost": f"${comparison.cheapest_option.total_cost_usd:.2f}",
                    "gpu": comparison.cheapest_option.instance.gpu_type.value,
                },
                "fastest": {
                    "platform": comparison.fastest_option.platform.value,
                    "setup_time": f"{comparison.fastest_option.setup_time_minutes:.0f} min",
                    "gpu": comparison.fastest_option.instance.gpu_type.value,
                },
                "recommended": {
                    "platform": comparison.recommended_option.platform.value,
                    "cost": f"${comparison.recommended_option.total_cost_usd:.2f}",
                    "gpu": comparison.recommended_option.instance.gpu_type.value,
                    "reason": self._get_recommendation_reason(comparison)
                }
            },
            "options": []
        }
        
        # Add local option if available
        if comparison.local_estimate:
            result["options"].append({
                "platform": "Local",
                "gpu": comparison.local_estimate.instance.gpu_type.value,
                "cost": f"${comparison.local_estimate.total_cost_usd:.2f}",
                "setup_time": "immediate",
                "pros": comparison.local_estimate.pros,
                "cons": comparison.local_estimate.cons
            })
        
        # Add cloud options
        for estimate in comparison.cloud_estimates[:5]:  # Top 5 options
            result["options"].append({
                "platform": estimate.platform.value,
                "gpu": estimate.instance.gpu_type.value,
                "cost": f"${estimate.total_cost_usd:.2f}",
                "hourly_rate": f"${estimate.instance.hourly_rate_usd:.2f}/hr",
                "setup_time": estimate.estimated_start_time,
                "availability": estimate.instance.availability,
                "pros": estimate.pros,
                "cons": estimate.cons
            })
        
        if comparison.savings_vs_local:
            result["summary"]["savings_vs_local"] = f"{comparison.savings_vs_local:.1f}%"
        
        return result
    
    def _get_recommendation_reason(self, comparison: CostComparison) -> str:
        """Get reason for recommendation"""
        rec = comparison.recommended_option
        
        if rec == comparison.cheapest_option:
            return "Lowest cost option"
        elif rec == comparison.fastest_option:
            return "Fastest to start training"
        elif rec.platform == PlatformType.LOCAL:
            return "Best value with your local hardware"
        else:
            return "Best balance of cost and convenience"
    
    def get_platform_setup_instructions(self, platform: PlatformType) -> Dict[str, str]:
        """
        Get setup instructions for a platform.
        
        Args:
            platform: Platform type
            
        Returns:
            Dictionary with setup instructions
        """
        instructions = {
            PlatformType.RUNPOD: {
                "title": "RunPod Setup",
                "steps": [
                    "1. Create account at runpod.io",
                    "2. Add payment method and credits",
                    "3. Select GPU template (PyTorch recommended)",
                    "4. Deploy pod and wait for initialization",
                    "5. Connect via SSH or Jupyter notebook",
                    "6. Upload your dataset and training script"
                ],
                "api_docs": "https://docs.runpod.io/",
                "estimated_time": "5-10 minutes"
            },
            PlatformType.LAMBDA_LABS: {
                "title": "Lambda Labs Setup",
                "steps": [
                    "1. Create account at lambdalabs.com",
                    "2. Add SSH key to your account",
                    "3. Launch instance (may need to wait for availability)",
                    "4. Connect via SSH",
                    "5. Environment is pre-configured with ML libraries",
                    "6. Upload your dataset and start training"
                ],
                "api_docs": "https://docs.lambdalabs.com/",
                "estimated_time": "3-5 minutes (if instances available)"
            },
            PlatformType.TOGETHER_AI: {
                "title": "Together AI Setup",
                "steps": [
                    "1. Create account at together.ai",
                    "2. Get API key from dashboard",
                    "3. Install Together AI Python SDK",
                    "4. Configure API key in environment",
                    "5. Use serverless training API",
                    "6. Monitor training via dashboard"
                ],
                "api_docs": "https://docs.together.ai/",
                "estimated_time": "1-2 minutes"
            }
        }
        
        return instructions.get(platform, {
            "title": "Local Training",
            "steps": ["Training will run on your local GPU"],
            "estimated_time": "immediate"
        })


# Singleton instance
_cloud_platform_instance = None


def get_cloud_platform_service() -> CloudPlatformService:
    """Get singleton instance of CloudPlatformService"""
    global _cloud_platform_instance
    if _cloud_platform_instance is None:
        _cloud_platform_instance = CloudPlatformService()
    return _cloud_platform_instance
