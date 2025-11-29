"""
Tests for Cloud Platform Integration Service

Tests the integration with RunPod, Lambda Labs, and Together AI,
as well as cost comparison functionality.
"""

import pytest
from services.cloud_platform_service import (
    CloudPlatformService,
    PlatformType,
    GPUType,
    GPUInstance,
    PlatformCostEstimate,
    CostComparison
)


@pytest.fixture
def cloud_service():
    """Create a CloudPlatformService instance"""
    return CloudPlatformService()


class TestCloudPlatformService:
    """Test suite for CloudPlatformService"""
    
    def test_get_runpod_instances(self, cloud_service):
        """Test getting RunPod instances"""
        instances = cloud_service.get_runpod_instances()
        
        assert len(instances) > 0
        assert all(inst.platform == PlatformType.RUNPOD for inst in instances)
        assert all(inst.hourly_rate_usd > 0 for inst in instances)
        assert all(inst.memory_gb > 0 for inst in instances)
    
    def test_get_lambda_labs_instances(self, cloud_service):
        """Test getting Lambda Labs instances"""
        instances = cloud_service.get_lambda_labs_instances()
        
        assert len(instances) > 0
        assert all(inst.platform == PlatformType.LAMBDA_LABS for inst in instances)
        assert all(inst.hourly_rate_usd > 0 for inst in instances)
        assert all(inst.memory_gb > 0 for inst in instances)
    
    def test_get_together_ai_instances(self, cloud_service):
        """Test getting Together AI instances"""
        instances = cloud_service.get_together_ai_instances()
        
        assert len(instances) > 0
        assert all(inst.platform == PlatformType.TOGETHER_AI for inst in instances)
        assert all(inst.hourly_rate_usd > 0 for inst in instances)
        assert all(inst.memory_gb > 0 for inst in instances)
    
    def test_get_all_cloud_instances(self, cloud_service):
        """Test getting all cloud instances"""
        instances = cloud_service.get_all_cloud_instances()
        
        assert len(instances) > 0
        
        # Should have instances from multiple platforms
        platforms = {inst.platform for inst in instances}
        assert PlatformType.RUNPOD in platforms
        assert PlatformType.LAMBDA_LABS in platforms
        assert PlatformType.TOGETHER_AI in platforms
        
        # Should be sorted by price
        prices = [inst.hourly_rate_usd for inst in instances]
        assert prices == sorted(prices)
    
    def test_filter_by_gpu_type(self, cloud_service):
        """Test filtering instances by GPU type"""
        instances = cloud_service.get_all_cloud_instances(gpu_type=GPUType.A100_80GB)
        
        assert len(instances) > 0
        assert all(inst.gpu_type == GPUType.A100_80GB for inst in instances)
    
    def test_filter_by_memory(self, cloud_service):
        """Test filtering instances by minimum memory"""
        min_memory = 40
        instances = cloud_service.get_all_cloud_instances(min_memory_gb=min_memory)
        
        assert len(instances) > 0
        assert all(inst.memory_gb >= min_memory for inst in instances)
    
    def test_calculate_platform_cost(self, cloud_service):
        """Test calculating cost for a platform"""
        instance = GPUInstance(
            platform=PlatformType.RUNPOD,
            gpu_type=GPUType.A100_40GB,
            gpu_count=1,
            memory_gb=40,
            vcpus=24,
            ram_gb=128,
            storage_gb=200,
            hourly_rate_usd=1.89,
            availability="high",
            region="US-Central"
        )
        
        training_hours = 10.0
        estimate = cloud_service.calculate_platform_cost(instance, training_hours)
        
        assert estimate.platform == PlatformType.RUNPOD
        assert estimate.training_hours == training_hours
        assert estimate.total_cost_usd == 1.89 * 10.0
        assert estimate.setup_time_minutes > 0
        assert len(estimate.pros) > 0
        assert len(estimate.cons) > 0
    
    def test_compare_costs_cloud_only(self, cloud_service):
        """Test cost comparison without local GPU"""
        training_hours = 5.0
        comparison = cloud_service.compare_costs(
            training_hours=training_hours,
            min_memory_gb=24
        )
        
        assert comparison.local_estimate is None
        assert len(comparison.cloud_estimates) > 0
        assert comparison.cheapest_option is not None
        assert comparison.fastest_option is not None
        assert comparison.recommended_option is not None
        assert comparison.savings_vs_local is None
    
    def test_compare_costs_with_local(self, cloud_service):
        """Test cost comparison with local GPU"""
        training_hours = 5.0
        local_electricity_cost = 2.50  # $2.50 for 5 hours
        
        comparison = cloud_service.compare_costs(
            training_hours=training_hours,
            local_gpu_type=GPUType.RTX_4090,
            local_electricity_cost=local_electricity_cost,
            min_memory_gb=24
        )
        
        assert comparison.local_estimate is not None
        assert comparison.local_estimate.platform == PlatformType.LOCAL
        assert len(comparison.cloud_estimates) > 0
        assert comparison.cheapest_option is not None
        assert comparison.fastest_option is not None
        assert comparison.recommended_option is not None
        
        # Savings should be calculated if cloud is cheaper
        if comparison.cheapest_option.platform != PlatformType.LOCAL:
            assert comparison.savings_vs_local is not None
    
    def test_format_cost_comparison(self, cloud_service):
        """Test formatting cost comparison"""
        training_hours = 5.0
        comparison = cloud_service.compare_costs(
            training_hours=training_hours,
            min_memory_gb=24
        )
        
        formatted = cloud_service.format_cost_comparison(comparison)
        
        assert "summary" in formatted
        assert "cheapest" in formatted["summary"]
        assert "fastest" in formatted["summary"]
        assert "recommended" in formatted["summary"]
        assert "options" in formatted
        assert len(formatted["options"]) > 0
        
        # Check option structure
        for option in formatted["options"]:
            assert "platform" in option
            assert "gpu" in option
            assert "cost" in option
            assert "pros" in option
            assert "cons" in option
    
    def test_get_platform_setup_instructions(self, cloud_service):
        """Test getting setup instructions"""
        for platform in [PlatformType.RUNPOD, PlatformType.LAMBDA_LABS, PlatformType.TOGETHER_AI]:
            instructions = cloud_service.get_platform_setup_instructions(platform)
            
            assert "title" in instructions
            assert "steps" in instructions
            assert len(instructions["steps"]) > 0
            assert "estimated_time" in instructions
    
    def test_cheapest_option_is_actually_cheapest(self, cloud_service):
        """Test that the cheapest option is correctly identified"""
        training_hours = 10.0
        comparison = cloud_service.compare_costs(
            training_hours=training_hours,
            min_memory_gb=24
        )
        
        cheapest_cost = comparison.cheapest_option.total_cost_usd
        
        # Verify it's actually the cheapest
        for estimate in comparison.cloud_estimates:
            assert estimate.total_cost_usd >= cheapest_cost
    
    def test_fastest_option_has_lowest_setup_time(self, cloud_service):
        """Test that the fastest option has the lowest setup time"""
        training_hours = 10.0
        comparison = cloud_service.compare_costs(
            training_hours=training_hours,
            min_memory_gb=24
        )
        
        fastest_setup = comparison.fastest_option.setup_time_minutes
        
        # Verify it has the lowest setup time
        for estimate in comparison.cloud_estimates:
            assert estimate.setup_time_minutes >= fastest_setup
    
    def test_cost_scales_with_training_hours(self, cloud_service):
        """Test that cost scales linearly with training hours"""
        instance = GPUInstance(
            platform=PlatformType.RUNPOD,
            gpu_type=GPUType.A100_40GB,
            gpu_count=1,
            memory_gb=40,
            vcpus=24,
            ram_gb=128,
            storage_gb=200,
            hourly_rate_usd=2.00,
            availability="high",
            region="US-Central"
        )
        
        estimate_5h = cloud_service.calculate_platform_cost(instance, 5.0)
        estimate_10h = cloud_service.calculate_platform_cost(instance, 10.0)
        
        assert estimate_10h.total_cost_usd == 2 * estimate_5h.total_cost_usd
    
    def test_all_platforms_have_pros_and_cons(self, cloud_service):
        """Test that all platform estimates include pros and cons"""
        training_hours = 5.0
        comparison = cloud_service.compare_costs(
            training_hours=training_hours,
            min_memory_gb=24
        )
        
        for estimate in comparison.cloud_estimates:
            assert len(estimate.pros) > 0, f"Platform {estimate.platform.value} has no pros"
            assert len(estimate.cons) > 0, f"Platform {estimate.platform.value} has no cons"
    
    def test_gpu_memory_mapping(self, cloud_service):
        """Test that GPU memory is correctly mapped"""
        memory_map = {
            GPUType.RTX_4090: 24,
            GPUType.A100_40GB: 40,
            GPUType.A100_80GB: 80,
            GPUType.H100: 80,
        }
        
        for gpu_type, expected_memory in memory_map.items():
            actual_memory = cloud_service._get_gpu_memory(gpu_type)
            assert actual_memory == expected_memory, \
                f"GPU {gpu_type.value} should have {expected_memory}GB, got {actual_memory}GB"
    
    def test_recommendation_reason(self, cloud_service):
        """Test that recommendation includes a reason"""
        training_hours = 5.0
        comparison = cloud_service.compare_costs(
            training_hours=training_hours,
            min_memory_gb=24
        )
        
        formatted = cloud_service.format_cost_comparison(comparison)
        
        assert "reason" in formatted["summary"]["recommended"]
        assert len(formatted["summary"]["recommended"]["reason"]) > 0


class TestPlatformPricing:
    """Test that platform pricing is reasonable"""
    
    def test_runpod_pricing_reasonable(self, cloud_service):
        """Test that RunPod pricing is in reasonable range"""
        instances = cloud_service.get_runpod_instances()
        
        for inst in instances:
            # Prices should be between $0.10 and $10.00 per hour
            assert 0.10 <= inst.hourly_rate_usd <= 10.00, \
                f"RunPod {inst.gpu_type.value} price ${inst.hourly_rate_usd}/hr seems unreasonable"
    
    def test_lambda_labs_pricing_reasonable(self, cloud_service):
        """Test that Lambda Labs pricing is in reasonable range"""
        instances = cloud_service.get_lambda_labs_instances()
        
        for inst in instances:
            # Prices should be between $0.10 and $10.00 per hour
            assert 0.10 <= inst.hourly_rate_usd <= 10.00, \
                f"Lambda Labs {inst.gpu_type.value} price ${inst.hourly_rate_usd}/hr seems unreasonable"
    
    def test_together_ai_pricing_reasonable(self, cloud_service):
        """Test that Together AI pricing is in reasonable range"""
        instances = cloud_service.get_together_ai_instances()
        
        for inst in instances:
            # Prices should be between $0.10 and $10.00 per hour
            assert 0.10 <= inst.hourly_rate_usd <= 10.00, \
                f"Together AI {inst.gpu_type.value} price ${inst.hourly_rate_usd}/hr seems unreasonable"


class TestCostComparisonLogic:
    """Test cost comparison logic"""
    
    def test_local_vs_cloud_comparison(self, cloud_service):
        """Test comparison between local and cloud"""
        training_hours = 10.0
        
        # Expensive local electricity
        expensive_local = cloud_service.compare_costs(
            training_hours=training_hours,
            local_gpu_type=GPUType.RTX_4090,
            local_electricity_cost=50.00,  # $50 for 10 hours
            min_memory_gb=24
        )
        
        # Cloud should be recommended when local is expensive
        assert expensive_local.recommended_option.platform != PlatformType.LOCAL
        
        # Cheap local electricity
        cheap_local = cloud_service.compare_costs(
            training_hours=training_hours,
            local_gpu_type=GPUType.RTX_4090,
            local_electricity_cost=1.00,  # $1 for 10 hours
            min_memory_gb=24
        )
        
        # Local might be recommended when it's cheap
        # (depends on cloud prices, so we just check it's considered)
        assert cheap_local.local_estimate is not None
    
    def test_savings_calculation(self, cloud_service):
        """Test savings calculation"""
        training_hours = 10.0
        local_cost = 20.00
        
        comparison = cloud_service.compare_costs(
            training_hours=training_hours,
            local_gpu_type=GPUType.RTX_4090,
            local_electricity_cost=local_cost,
            min_memory_gb=24
        )
        
        if comparison.cheapest_option.platform != PlatformType.LOCAL:
            # Savings should be positive if cloud is cheaper
            assert comparison.savings_vs_local is not None
            
            expected_savings = (
                (local_cost - comparison.cheapest_option.total_cost_usd) /
                local_cost * 100
            )
            
            assert abs(comparison.savings_vs_local - expected_savings) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
