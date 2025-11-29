"""
Tests for Cost Calculator Service

Tests cover:
- GPU hours calculation
- Energy consumption calculation
- Electricity cost calculation
- Carbon footprint calculation
- Complete estimates calculation
- Real-time estimate updates
"""

import pytest
from services.cost_calculator_service import (
    CostCalculatorService,
    CostEstimates,
    GPUPowerProfile,
    get_cost_calculator
)


class TestCostCalculatorService:
    """Test suite for CostCalculatorService"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = CostCalculatorService()
    
    def test_calculate_gpu_hours_single_gpu(self):
        """Test GPU hours calculation with single GPU"""
        gpu_hours = self.service.calculate_gpu_hours(
            training_time_hours=2.5,
            num_gpus=1
        )
        
        assert gpu_hours == 2.5
    
    def test_calculate_gpu_hours_multiple_gpus(self):
        """Test GPU hours calculation with multiple GPUs"""
        gpu_hours = self.service.calculate_gpu_hours(
            training_time_hours=2.0,
            num_gpus=4
        )
        
        assert gpu_hours == 8.0
    
    def test_get_gpu_power_profile_exact_match(self):
        """Test getting GPU power profile with exact match"""
        profile = self.service.get_gpu_power_profile("RTX 4090")
        
        assert profile.model_name == "RTX 4090"
        assert profile.tdp_watts == 450
        assert profile.avg_power_watts == 400
        assert profile.idle_power_watts == 50
    
    def test_get_gpu_power_profile_partial_match(self):
        """Test getting GPU power profile with partial match"""
        profile = self.service.get_gpu_power_profile("NVIDIA RTX 4090")
        
        assert profile.model_name == "RTX 4090"
    
    def test_get_gpu_power_profile_fallback(self):
        """Test getting GPU power profile with unknown GPU"""
        profile = self.service.get_gpu_power_profile("Unknown GPU")
        
        assert profile.model_name == "default"
        assert profile.tdp_watts == 300
    
    def test_calculate_energy_consumption(self):
        """Test energy consumption calculation"""
        energy_kwh = self.service.calculate_energy_consumption(
            training_time_hours=2.0,
            gpu_name="RTX 4090",
            num_gpus=1,
            utilization=0.85
        )
        
        # RTX 4090: idle=50W, avg=400W
        # At 85% utilization: 50 + (400-50)*0.85 = 347.5W
        # Energy: 347.5W * 2h = 695Wh = 0.695kWh
        expected_energy = 0.695
        assert abs(energy_kwh - expected_energy) < 0.01
    
    def test_calculate_energy_consumption_multiple_gpus(self):
        """Test energy consumption with multiple GPUs"""
        energy_kwh = self.service.calculate_energy_consumption(
            training_time_hours=1.0,
            gpu_name="A100",
            num_gpus=2,
            utilization=0.9
        )
        
        # A100: idle=50W, avg=350W
        # At 90% utilization: 50 + (350-50)*0.9 = 320W per GPU
        # Energy: 320W * 1h * 2 GPUs = 640Wh = 0.64kWh
        expected_energy = 0.64
        assert abs(energy_kwh - expected_energy) < 0.01
    
    def test_calculate_electricity_cost_with_user_rate(self):
        """Test electricity cost calculation with user-provided rate"""
        cost = self.service.calculate_electricity_cost(
            energy_kwh=10.0,
            electricity_rate_per_kwh=0.15
        )
        
        assert cost == 1.5
    
    def test_calculate_electricity_cost_with_default_rate(self):
        """Test electricity cost calculation with default rate"""
        cost = self.service.calculate_electricity_cost(
            energy_kwh=10.0,
            electricity_rate_per_kwh=None,
            region="US"
        )
        
        # US default rate is 0.14
        assert abs(cost - 1.4) < 0.01
    
    def test_calculate_carbon_footprint(self):
        """Test carbon footprint calculation"""
        carbon_kg = self.service.calculate_carbon_footprint(
            energy_kwh=10.0,
            region="US"
        )
        
        # US carbon intensity: 386g/kWh
        # 10 kWh * 386g/kWh = 3860g = 3.86kg
        assert abs(carbon_kg - 3.86) < 0.01
    
    def test_calculate_carbon_footprint_clean_grid(self):
        """Test carbon footprint with clean grid (France)"""
        carbon_kg = self.service.calculate_carbon_footprint(
            energy_kwh=10.0,
            region="FR"
        )
        
        # France carbon intensity: 57g/kWh (nuclear heavy)
        # 10 kWh * 57g/kWh = 570g = 0.57kg
        assert abs(carbon_kg - 0.57) < 0.01
    
    def test_calculate_complete_estimates(self):
        """Test complete estimates calculation"""
        estimates = self.service.calculate_complete_estimates(
            training_time_hours=2.0,
            gpu_name="RTX 4090",
            num_gpus=1,
            electricity_rate_per_kwh=0.15,
            region="US",
            utilization=0.85,
            confidence=0.8
        )
        
        assert isinstance(estimates, CostEstimates)
        assert estimates.gpu_hours == 2.0
        assert estimates.electricity_rate_per_kwh == 0.15
        assert estimates.carbon_intensity_g_per_kwh == 386
        assert estimates.confidence == 0.8
        assert estimates.electricity_cost_usd > 0
        assert estimates.carbon_footprint_kg > 0
        assert estimates.total_energy_kwh > 0
    
    def test_calculate_complete_estimates_with_defaults(self):
        """Test complete estimates with default values"""
        estimates = self.service.calculate_complete_estimates(
            training_time_hours=1.0,
            gpu_name="A100",
            num_gpus=2
        )
        
        assert isinstance(estimates, CostEstimates)
        assert estimates.gpu_hours == 2.0  # 1h * 2 GPUs
        # Should use default electricity rate for "default" region
        assert estimates.electricity_rate_per_kwh == 0.15
        # Should use default carbon intensity
        assert estimates.carbon_intensity_g_per_kwh == 400
    
    def test_get_default_electricity_rate(self):
        """Test getting default electricity rate"""
        us_rate = self.service.get_default_electricity_rate("US")
        assert us_rate == 0.14
        
        eu_rate = self.service.get_default_electricity_rate("EU")
        assert eu_rate == 0.25
        
        default_rate = self.service.get_default_electricity_rate("unknown")
        assert default_rate == 0.15
    
    def test_get_carbon_intensity(self):
        """Test getting carbon intensity"""
        us_intensity = self.service.get_carbon_intensity("US")
        assert us_intensity == 386
        
        fr_intensity = self.service.get_carbon_intensity("FR")
        assert fr_intensity == 57
        
        default_intensity = self.service.get_carbon_intensity("unknown")
        assert default_intensity == 400
    
    def test_format_cost_summary(self):
        """Test formatting cost summary"""
        estimates = CostEstimates(
            gpu_hours=2.5,
            electricity_cost_usd=0.35,
            electricity_rate_per_kwh=0.14,
            carbon_footprint_kg=0.96,
            carbon_intensity_g_per_kwh=386,
            total_energy_kwh=2.5,
            confidence=0.75
        )
        
        formatted = self.service.format_cost_summary(estimates)
        
        assert formatted["gpu_hours"] == "2.5 GPU hours"
        assert formatted["electricity_cost"] == "$0.35"
        assert formatted["carbon_footprint"] == "0.96 kg CO₂"
        assert formatted["energy_consumption"] == "2.50 kWh"
        assert formatted["electricity_rate"] == "$0.140/kWh"
        assert formatted["carbon_intensity"] == "386g CO₂/kWh"
        assert formatted["confidence"] == "75%"
    
    def test_singleton_instance(self):
        """Test that get_cost_calculator returns singleton"""
        instance1 = get_cost_calculator()
        instance2 = get_cost_calculator()
        
        assert instance1 is instance2


class TestCostEstimatesValidation:
    """Test validation of cost estimates"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = CostCalculatorService()
    
    def test_estimates_scale_with_training_time(self):
        """Test that estimates scale linearly with training time"""
        estimates_1h = self.service.calculate_complete_estimates(
            training_time_hours=1.0,
            gpu_name="RTX 4090",
            num_gpus=1,
            electricity_rate_per_kwh=0.15,
            region="US"
        )
        
        estimates_2h = self.service.calculate_complete_estimates(
            training_time_hours=2.0,
            gpu_name="RTX 4090",
            num_gpus=1,
            electricity_rate_per_kwh=0.15,
            region="US"
        )
        
        # All metrics should approximately double
        assert abs(estimates_2h.gpu_hours - 2 * estimates_1h.gpu_hours) < 0.01
        assert abs(estimates_2h.total_energy_kwh - 2 * estimates_1h.total_energy_kwh) < 0.01
        assert abs(estimates_2h.electricity_cost_usd - 2 * estimates_1h.electricity_cost_usd) < 0.01
        assert abs(estimates_2h.carbon_footprint_kg - 2 * estimates_1h.carbon_footprint_kg) < 0.01
    
    def test_estimates_scale_with_num_gpus(self):
        """Test that estimates scale with number of GPUs"""
        estimates_1gpu = self.service.calculate_complete_estimates(
            training_time_hours=1.0,
            gpu_name="A100",
            num_gpus=1,
            electricity_rate_per_kwh=0.15,
            region="US"
        )
        
        estimates_4gpu = self.service.calculate_complete_estimates(
            training_time_hours=1.0,
            gpu_name="A100",
            num_gpus=4,
            electricity_rate_per_kwh=0.15,
            region="US"
        )
        
        # All metrics should approximately quadruple
        assert abs(estimates_4gpu.gpu_hours - 4 * estimates_1gpu.gpu_hours) < 0.01
        assert abs(estimates_4gpu.total_energy_kwh - 4 * estimates_1gpu.total_energy_kwh) < 0.01
        assert abs(estimates_4gpu.electricity_cost_usd - 4 * estimates_1gpu.electricity_cost_usd) < 0.01
        assert abs(estimates_4gpu.carbon_footprint_kg - 4 * estimates_1gpu.carbon_footprint_kg) < 0.01
    
    def test_cost_varies_with_electricity_rate(self):
        """Test that cost varies with electricity rate"""
        estimates_cheap = self.service.calculate_complete_estimates(
            training_time_hours=1.0,
            gpu_name="RTX 4090",
            num_gpus=1,
            electricity_rate_per_kwh=0.10,
            region="US"
        )
        
        estimates_expensive = self.service.calculate_complete_estimates(
            training_time_hours=1.0,
            gpu_name="RTX 4090",
            num_gpus=1,
            electricity_rate_per_kwh=0.30,
            region="US"
        )
        
        # Cost should be 3x higher with 3x rate
        ratio = estimates_expensive.electricity_cost_usd / estimates_cheap.electricity_cost_usd
        assert abs(ratio - 3.0) < 0.01
        
        # Energy and carbon should be the same
        assert abs(estimates_expensive.total_energy_kwh - estimates_cheap.total_energy_kwh) < 0.01
        assert abs(estimates_expensive.carbon_footprint_kg - estimates_cheap.carbon_footprint_kg) < 0.01
    
    def test_carbon_varies_with_region(self):
        """Test that carbon footprint varies with region"""
        estimates_us = self.service.calculate_complete_estimates(
            training_time_hours=1.0,
            gpu_name="RTX 4090",
            num_gpus=1,
            electricity_rate_per_kwh=0.15,
            region="US"  # 386g/kWh
        )
        
        estimates_fr = self.service.calculate_complete_estimates(
            training_time_hours=1.0,
            gpu_name="RTX 4090",
            num_gpus=1,
            electricity_rate_per_kwh=0.15,
            region="FR"  # 57g/kWh (much cleaner)
        )
        
        # France should have much lower carbon footprint
        assert estimates_fr.carbon_footprint_kg < estimates_us.carbon_footprint_kg
        
        # Energy should be the same
        assert abs(estimates_fr.total_energy_kwh - estimates_us.total_energy_kwh) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
