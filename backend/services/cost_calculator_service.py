"""
Cost and Carbon Footprint Calculator Service

This service calculates:
- Electricity cost based on GPU hours and user-input electricity rate
- GPU hours estimation based on training time
- Carbon footprint based on energy consumption and regional carbon intensity
- Real-time estimate updates when configuration changes
"""

from typing import Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CostEstimates:
    """Cost and environmental impact estimates"""
    # GPU usage
    gpu_hours: float  # Total GPU hours for training
    
    # Cost
    electricity_cost_usd: float  # Cost in USD
    electricity_rate_per_kwh: float  # User's electricity rate
    
    # Carbon footprint
    carbon_footprint_kg: float  # CO2 emissions in kg
    carbon_intensity_g_per_kwh: float  # Regional carbon intensity
    
    # Energy consumption
    total_energy_kwh: float  # Total energy consumed
    
    # Confidence
    confidence: float  # 0-1, confidence in estimates


@dataclass
class GPUPowerProfile:
    """Power consumption profile for different GPU models"""
    model_name: str
    tdp_watts: int  # Thermal Design Power
    avg_power_watts: int  # Average power during training
    idle_power_watts: int  # Idle power consumption


class CostCalculatorService:
    """
    Service for calculating training costs and carbon footprint.
    """
    
    # GPU power profiles (TDP and average training power)
    GPU_POWER_PROFILES = {
        # NVIDIA Consumer GPUs
        "RTX 4090": GPUPowerProfile("RTX 4090", 450, 400, 50),
        "RTX 4080": GPUPowerProfile("RTX 4080", 320, 280, 40),
        "RTX 4070": GPUPowerProfile("RTX 4070", 200, 180, 30),
        "RTX 3090": GPUPowerProfile("RTX 3090", 350, 320, 45),
        "RTX 3080": GPUPowerProfile("RTX 3080", 320, 290, 40),
        "RTX 3070": GPUPowerProfile("RTX 3070", 220, 200, 30),
        
        # NVIDIA Data Center GPUs
        "A100": GPUPowerProfile("A100", 400, 350, 50),
        "A100-80GB": GPUPowerProfile("A100-80GB", 400, 350, 50),
        "H100": GPUPowerProfile("H100", 700, 600, 80),
        "V100": GPUPowerProfile("V100", 300, 270, 40),
        "A10": GPUPowerProfile("A10", 150, 130, 25),
        "T4": GPUPowerProfile("T4", 70, 60, 15),
        
        # AMD GPUs
        "MI250": GPUPowerProfile("MI250", 500, 450, 60),
        "MI210": GPUPowerProfile("MI210", 300, 270, 40),
        
        # Default fallback
        "default": GPUPowerProfile("default", 300, 250, 40),
    }
    
    # Regional carbon intensity (grams CO2 per kWh)
    # Source: IEA and various grid operators
    CARBON_INTENSITY = {
        "US": 386,  # United States average
        "US-CA": 200,  # California (cleaner grid)
        "US-TX": 450,  # Texas (more fossil fuels)
        "EU": 275,  # European Union average
        "UK": 233,  # United Kingdom
        "DE": 311,  # Germany
        "FR": 57,   # France (nuclear heavy)
        "CN": 555,  # China
        "IN": 632,  # India
        "JP": 462,  # Japan
        "AU": 510,  # Australia
        "CA": 120,  # Canada (hydro heavy)
        "default": 400,  # Global average
    }
    
    # Default electricity rates (USD per kWh)
    DEFAULT_ELECTRICITY_RATES = {
        "US": 0.14,
        "EU": 0.25,
        "UK": 0.30,
        "default": 0.15,
    }
    
    def __init__(self):
        logger.info("CostCalculatorService initialized")
    
    def get_gpu_power_profile(self, gpu_name: str) -> GPUPowerProfile:
        """
        Get power profile for a GPU model.
        
        Args:
            gpu_name: Name of the GPU (e.g., "RTX 4090", "A100")
            
        Returns:
            GPUPowerProfile for the GPU
        """
        # Try exact match first
        if gpu_name in self.GPU_POWER_PROFILES:
            return self.GPU_POWER_PROFILES[gpu_name]
        
        # Try partial match (e.g., "NVIDIA RTX 4090" -> "RTX 4090")
        for key in self.GPU_POWER_PROFILES:
            if key in gpu_name or gpu_name in key:
                logger.info(f"Matched GPU '{gpu_name}' to profile '{key}'")
                return self.GPU_POWER_PROFILES[key]
        
        # Fallback to default
        logger.warning(f"No power profile found for GPU '{gpu_name}', using default")
        return self.GPU_POWER_PROFILES["default"]
    
    def calculate_gpu_hours(
        self,
        training_time_hours: float,
        num_gpus: int = 1
    ) -> float:
        """
        Calculate total GPU hours for training.
        
        Args:
            training_time_hours: Estimated training time in hours
            num_gpus: Number of GPUs used
            
        Returns:
            Total GPU hours
        """
        gpu_hours = training_time_hours * num_gpus
        logger.info(f"Calculated GPU hours: {gpu_hours:.2f} "
                   f"({training_time_hours:.2f}h × {num_gpus} GPUs)")
        return gpu_hours
    
    def calculate_energy_consumption(
        self,
        training_time_hours: float,
        gpu_name: str,
        num_gpus: int = 1,
        utilization: float = 0.85
    ) -> float:
        """
        Calculate total energy consumption in kWh.
        
        Args:
            training_time_hours: Training time in hours
            gpu_name: GPU model name
            num_gpus: Number of GPUs
            utilization: Average GPU utilization (0-1)
            
        Returns:
            Total energy consumption in kWh
        """
        power_profile = self.get_gpu_power_profile(gpu_name)
        
        # Calculate average power based on utilization
        # At 0% utilization = idle power, at 100% = avg training power
        avg_power_watts = (
            power_profile.idle_power_watts +
            (power_profile.avg_power_watts - power_profile.idle_power_watts) * utilization
        )
        
        # Convert to kW and multiply by hours and number of GPUs
        energy_kwh = (avg_power_watts / 1000) * training_time_hours * num_gpus
        
        logger.info(f"Calculated energy consumption: {energy_kwh:.2f} kWh "
                   f"({avg_power_watts}W × {training_time_hours:.2f}h × {num_gpus} GPUs)")
        
        return energy_kwh
    
    def calculate_electricity_cost(
        self,
        energy_kwh: float,
        electricity_rate_per_kwh: Optional[float] = None,
        region: str = "default"
    ) -> float:
        """
        Calculate electricity cost in USD.
        
        Args:
            energy_kwh: Energy consumption in kWh
            electricity_rate_per_kwh: User's electricity rate (USD per kWh)
            region: Region code for default rate if not provided
            
        Returns:
            Electricity cost in USD
        """
        # Use user-provided rate or default for region
        if electricity_rate_per_kwh is None:
            electricity_rate_per_kwh = self.DEFAULT_ELECTRICITY_RATES.get(
                region,
                self.DEFAULT_ELECTRICITY_RATES["default"]
            )
        
        cost_usd = energy_kwh * electricity_rate_per_kwh
        
        logger.info(f"Calculated electricity cost: ${cost_usd:.2f} "
                   f"({energy_kwh:.2f} kWh × ${electricity_rate_per_kwh:.3f}/kWh)")
        
        return cost_usd
    
    def calculate_carbon_footprint(
        self,
        energy_kwh: float,
        region: str = "default"
    ) -> float:
        """
        Calculate carbon footprint in kg CO2.
        
        Args:
            energy_kwh: Energy consumption in kWh
            region: Region code for carbon intensity
            
        Returns:
            Carbon footprint in kg CO2
        """
        # Get carbon intensity for region (grams CO2 per kWh)
        carbon_intensity = self.CARBON_INTENSITY.get(
            region,
            self.CARBON_INTENSITY["default"]
        )
        
        # Convert to kg CO2
        carbon_kg = (energy_kwh * carbon_intensity) / 1000
        
        logger.info(f"Calculated carbon footprint: {carbon_kg:.2f} kg CO2 "
                   f"({energy_kwh:.2f} kWh × {carbon_intensity}g/kWh)")
        
        return carbon_kg
    
    def calculate_complete_estimates(
        self,
        training_time_hours: float,
        gpu_name: str,
        num_gpus: int = 1,
        electricity_rate_per_kwh: Optional[float] = None,
        region: str = "default",
        utilization: float = 0.85,
        confidence: float = 0.7
    ) -> CostEstimates:
        """
        Calculate complete cost and carbon footprint estimates.
        
        Args:
            training_time_hours: Estimated training time in hours
            gpu_name: GPU model name
            num_gpus: Number of GPUs used
            electricity_rate_per_kwh: User's electricity rate (USD per kWh)
            region: Region code for defaults
            utilization: Average GPU utilization (0-1)
            confidence: Confidence in time estimate (0-1)
            
        Returns:
            CostEstimates with all calculated values
        """
        logger.info(f"Calculating complete estimates for {training_time_hours:.2f}h "
                   f"on {num_gpus}x {gpu_name}")
        
        # Calculate GPU hours
        gpu_hours = self.calculate_gpu_hours(training_time_hours, num_gpus)
        
        # Calculate energy consumption
        energy_kwh = self.calculate_energy_consumption(
            training_time_hours,
            gpu_name,
            num_gpus,
            utilization
        )
        
        # Get electricity rate
        if electricity_rate_per_kwh is None:
            electricity_rate_per_kwh = self.DEFAULT_ELECTRICITY_RATES.get(
                region,
                self.DEFAULT_ELECTRICITY_RATES["default"]
            )
        
        # Calculate cost
        electricity_cost = self.calculate_electricity_cost(
            energy_kwh,
            electricity_rate_per_kwh,
            region
        )
        
        # Calculate carbon footprint
        carbon_footprint = self.calculate_carbon_footprint(energy_kwh, region)
        
        # Get carbon intensity for the region
        carbon_intensity = self.CARBON_INTENSITY.get(
            region,
            self.CARBON_INTENSITY["default"]
        )
        
        estimates = CostEstimates(
            gpu_hours=gpu_hours,
            electricity_cost_usd=electricity_cost,
            electricity_rate_per_kwh=electricity_rate_per_kwh,
            carbon_footprint_kg=carbon_footprint,
            carbon_intensity_g_per_kwh=carbon_intensity,
            total_energy_kwh=energy_kwh,
            confidence=confidence
        )
        
        logger.info(f"Complete estimates: ${electricity_cost:.2f}, "
                   f"{carbon_footprint:.2f} kg CO2, {gpu_hours:.2f} GPU hours")
        
        return estimates
    
    def get_default_electricity_rate(self, region: str = "default") -> float:
        """
        Get default electricity rate for a region.
        
        Args:
            region: Region code
            
        Returns:
            Default electricity rate in USD per kWh
        """
        return self.DEFAULT_ELECTRICITY_RATES.get(
            region,
            self.DEFAULT_ELECTRICITY_RATES["default"]
        )
    
    def get_carbon_intensity(self, region: str = "default") -> float:
        """
        Get carbon intensity for a region.
        
        Args:
            region: Region code
            
        Returns:
            Carbon intensity in grams CO2 per kWh
        """
        return self.CARBON_INTENSITY.get(
            region,
            self.CARBON_INTENSITY["default"]
        )
    
    def format_cost_summary(self, estimates: CostEstimates) -> Dict[str, str]:
        """
        Format cost estimates into human-readable strings.
        
        Args:
            estimates: CostEstimates object
            
        Returns:
            Dictionary with formatted strings
        """
        return {
            "gpu_hours": f"{estimates.gpu_hours:.1f} GPU hours",
            "electricity_cost": f"${estimates.electricity_cost_usd:.2f}",
            "carbon_footprint": f"{estimates.carbon_footprint_kg:.2f} kg CO₂",
            "energy_consumption": f"{estimates.total_energy_kwh:.2f} kWh",
            "electricity_rate": f"${estimates.electricity_rate_per_kwh:.3f}/kWh",
            "carbon_intensity": f"{estimates.carbon_intensity_g_per_kwh}g CO₂/kWh",
            "confidence": f"{estimates.confidence * 100:.0f}%"
        }


# Singleton instance
_cost_calculator_instance = None


def get_cost_calculator() -> CostCalculatorService:
    """Get singleton instance of CostCalculatorService"""
    global _cost_calculator_instance
    if _cost_calculator_instance is None:
        _cost_calculator_instance = CostCalculatorService()
    return _cost_calculator_instance
