"""
Standalone test for Cost Calculator Service

This test can run without FastAPI dependencies.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.cost_calculator_service import get_cost_calculator


def test_complete_workflow():
    """Test complete cost calculator workflow"""
    print("Testing Cost Calculator Service...")
    
    calculator = get_cost_calculator()
    
    # Test 1: Calculate estimates for RTX 4090
    print("\n1. Testing RTX 4090 estimates...")
    estimates = calculator.calculate_complete_estimates(
        training_time_hours=2.5,
        gpu_name="RTX 4090",
        num_gpus=1,
        electricity_rate_per_kwh=0.15,
        region="US",
        utilization=0.85
    )
    
    print(f"   GPU Hours: {estimates.gpu_hours}")
    print(f"   Cost: ${estimates.electricity_cost_usd:.2f}")
    print(f"   Carbon: {estimates.carbon_footprint_kg:.2f} kg CO₂")
    print(f"   Energy: {estimates.total_energy_kwh:.2f} kWh")
    
    assert estimates.gpu_hours == 2.5
    assert estimates.electricity_cost_usd > 0
    assert estimates.carbon_footprint_kg > 0
    print("   ✓ RTX 4090 estimates calculated correctly")
    
    # Test 2: Multi-GPU calculation
    print("\n2. Testing multi-GPU calculation...")
    estimates_multi = calculator.calculate_complete_estimates(
        training_time_hours=1.0,
        gpu_name="A100",
        num_gpus=4,
        electricity_rate_per_kwh=0.15,
        region="US"
    )
    
    print(f"   GPU Hours: {estimates_multi.gpu_hours}")
    assert estimates_multi.gpu_hours == 4.0
    print("   ✓ Multi-GPU calculation correct")
    
    # Test 3: Regional differences
    print("\n3. Testing regional carbon intensity differences...")
    estimates_us = calculator.calculate_complete_estimates(
        training_time_hours=1.0,
        gpu_name="RTX 4090",
        num_gpus=1,
        electricity_rate_per_kwh=0.15,
        region="US"
    )
    
    estimates_fr = calculator.calculate_complete_estimates(
        training_time_hours=1.0,
        gpu_name="RTX 4090",
        num_gpus=1,
        electricity_rate_per_kwh=0.15,
        region="FR"
    )
    
    print(f"   US Carbon: {estimates_us.carbon_footprint_kg:.2f} kg CO₂")
    print(f"   FR Carbon: {estimates_fr.carbon_footprint_kg:.2f} kg CO₂")
    assert estimates_fr.carbon_footprint_kg < estimates_us.carbon_footprint_kg
    print("   ✓ Regional carbon intensity working correctly")
    
    # Test 4: Formatted output
    print("\n4. Testing formatted output...")
    formatted = calculator.format_cost_summary(estimates)
    print(f"   Formatted GPU Hours: {formatted['gpu_hours']}")
    print(f"   Formatted Cost: {formatted['electricity_cost']}")
    print(f"   Formatted Carbon: {formatted['carbon_footprint']}")
    
    assert "GPU hours" in formatted['gpu_hours']
    assert "$" in formatted['electricity_cost']
    assert "kg CO₂" in formatted['carbon_footprint']
    print("   ✓ Formatted output correct")
    
    # Test 5: Default rates
    print("\n5. Testing default rates...")
    us_rate = calculator.get_default_electricity_rate("US")
    eu_rate = calculator.get_default_electricity_rate("EU")
    print(f"   US Rate: ${us_rate}/kWh")
    print(f"   EU Rate: ${eu_rate}/kWh")
    
    assert us_rate == 0.14
    assert eu_rate == 0.25
    print("   ✓ Default rates correct")
    
    # Test 6: Carbon intensity
    print("\n6. Testing carbon intensity...")
    us_intensity = calculator.get_carbon_intensity("US")
    fr_intensity = calculator.get_carbon_intensity("FR")
    print(f"   US Intensity: {us_intensity}g CO₂/kWh")
    print(f"   FR Intensity: {fr_intensity}g CO₂/kWh")
    
    assert us_intensity == 386
    assert fr_intensity == 57
    print("   ✓ Carbon intensity correct")
    
    # Test 7: GPU power profiles
    print("\n7. Testing GPU power profiles...")
    profile_4090 = calculator.get_gpu_power_profile("RTX 4090")
    profile_a100 = calculator.get_gpu_power_profile("A100")
    print(f"   RTX 4090: {profile_4090.avg_power_watts}W avg")
    print(f"   A100: {profile_a100.avg_power_watts}W avg")
    
    assert profile_4090.avg_power_watts == 400
    assert profile_a100.avg_power_watts == 350
    print("   ✓ GPU power profiles correct")
    
    print("\n" + "="*50)
    print("✓ All tests passed!")
    print("="*50)
    
    return True


if __name__ == "__main__":
    try:
        test_complete_workflow()
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
