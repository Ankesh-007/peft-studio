"""
Cloud Platform Integration Example

This example demonstrates how to use the cloud platform service
to compare costs and select the best platform for training.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.cloud_platform_service import (
    get_cloud_platform_service,
    GPUType
)


def example_basic_comparison():
    """Example: Basic cost comparison"""
    print("\n=== Basic Cost Comparison ===\n")
    
    cloud_service = get_cloud_platform_service()
    
    # Compare costs for 10 hours of training
    comparison = cloud_service.compare_costs(
        training_hours=10.0,
        min_memory_gb=24
    )
    
    # Display summary
    print(f"Cheapest Option: {comparison.cheapest_option.platform.value}")
    print(f"  GPU: {comparison.cheapest_option.instance.gpu_type.value}")
    print(f"  Cost: ${comparison.cheapest_option.total_cost_usd:.2f}")
    print(f"  Hourly Rate: ${comparison.cheapest_option.instance.hourly_rate_usd:.2f}/hr")
    
    print(f"\nFastest Option: {comparison.fastest_option.platform.value}")
    print(f"  Setup Time: {comparison.fastest_option.setup_time_minutes:.0f} minutes")
    print(f"  Start Time: {comparison.fastest_option.estimated_start_time}")
    
    print(f"\nRecommended Option: {comparison.recommended_option.platform.value}")
    print(f"  GPU: {comparison.recommended_option.instance.gpu_type.value}")
    print(f"  Cost: ${comparison.recommended_option.total_cost_usd:.2f}")
    
    return comparison


def example_local_vs_cloud():
    """Example: Compare local GPU with cloud options"""
    print("\n=== Local vs Cloud Comparison ===\n")
    
    cloud_service = get_cloud_platform_service()
    
    # Compare with local RTX 4090
    comparison = cloud_service.compare_costs(
        training_hours=10.0,
        local_gpu_type=GPUType.RTX_4090,
        local_electricity_cost=2.50,  # $2.50 for 10 hours
        min_memory_gb=24
    )
    
    # Display local estimate
    if comparison.local_estimate:
        print("Local Training:")
        print(f"  GPU: {comparison.local_estimate.instance.gpu_type.value}")
        print(f"  Cost: ${comparison.local_estimate.total_cost_usd:.2f}")
        print(f"  Setup Time: {comparison.local_estimate.setup_time_minutes:.0f} minutes")
    
    # Display cloud options
    print("\nTop 3 Cloud Options:")
    for i, estimate in enumerate(comparison.cloud_estimates[:3], 1):
        print(f"\n{i}. {estimate.platform.value}")
        print(f"   GPU: {estimate.instance.gpu_type.value}")
        print(f"   Cost: ${estimate.total_cost_usd:.2f}")
        print(f"   Hourly Rate: ${estimate.instance.hourly_rate_usd:.2f}/hr")
        print(f"   Setup Time: {estimate.setup_time_minutes:.0f} minutes")
    
    # Display savings
    if comparison.savings_vs_local:
        print(f"\nSavings vs Local: {comparison.savings_vs_local:.1f}%")
    
    return comparison


def example_specific_gpu():
    """Example: Find instances with specific GPU"""
    print("\n=== Find A100 80GB Instances ===\n")
    
    cloud_service = get_cloud_platform_service()
    
    # Get all A100 80GB instances
    instances = cloud_service.get_all_cloud_instances(
        gpu_type=GPUType.A100_80GB
    )
    
    print(f"Found {len(instances)} A100 80GB instances:\n")
    
    for inst in instances:
        print(f"{inst.platform.value}:")
        print(f"  Price: ${inst.hourly_rate_usd:.2f}/hr")
        print(f"  Memory: {inst.memory_gb}GB")
        print(f"  vCPUs: {inst.vcpus}")
        print(f"  RAM: {inst.ram_gb}GB")
        print(f"  Storage: {inst.storage_gb}GB")
        print(f"  Availability: {inst.availability}")
        print(f"  Region: {inst.region}")
        print()
    
    return instances


def example_platform_specific():
    """Example: Get instances from specific platform"""
    print("\n=== Lambda Labs Instances ===\n")
    
    cloud_service = get_cloud_platform_service()
    
    # Get Lambda Labs instances
    instances = cloud_service.get_lambda_labs_instances()
    
    print(f"Found {len(instances)} Lambda Labs instances:\n")
    
    for inst in instances:
        print(f"{inst.gpu_type.value}:")
        print(f"  Price: ${inst.hourly_rate_usd:.2f}/hr")
        print(f"  Memory: {inst.memory_gb}GB")
        print(f"  Availability: {inst.availability}")
        print()
    
    return instances


def example_setup_instructions():
    """Example: Get setup instructions for platforms"""
    print("\n=== Setup Instructions ===\n")
    
    cloud_service = get_cloud_platform_service()
    
    from services.cloud_platform_service import PlatformType
    
    for platform in [PlatformType.RUNPOD, PlatformType.LAMBDA_LABS, PlatformType.TOGETHER_AI]:
        instructions = cloud_service.get_platform_setup_instructions(platform)
        
        print(f"{instructions['title']}")
        print(f"Estimated Time: {instructions['estimated_time']}")
        print("\nSteps:")
        for step in instructions['steps']:
            print(f"  {step}")
        print(f"\nDocumentation: {instructions.get('api_docs', 'N/A')}")
        print("\n" + "="*60 + "\n")


def example_formatted_comparison():
    """Example: Get formatted cost comparison"""
    print("\n=== Formatted Cost Comparison ===\n")
    
    cloud_service = get_cloud_platform_service()
    
    # Get comparison
    comparison = cloud_service.compare_costs(
        training_hours=5.0,
        local_gpu_type=GPUType.RTX_4090,
        local_electricity_cost=1.50,
        min_memory_gb=24
    )
    
    # Format for display
    formatted = cloud_service.format_cost_comparison(comparison)
    
    # Display summary
    print("Summary:")
    print(f"  Cheapest: {formatted['summary']['cheapest']['platform']} - {formatted['summary']['cheapest']['cost']}")
    print(f"  Fastest: {formatted['summary']['fastest']['platform']} - {formatted['summary']['fastest']['setup_time']}")
    print(f"  Recommended: {formatted['summary']['recommended']['platform']} - {formatted['summary']['recommended']['cost']}")
    print(f"  Reason: {formatted['summary']['recommended']['reason']}")
    
    if 'savings_vs_local' in formatted['summary']:
        print(f"  Savings vs Local: {formatted['summary']['savings_vs_local']}")
    
    # Display options
    print("\nAll Options:")
    for option in formatted['options']:
        print(f"\n{option['platform']} - {option['gpu']}")
        print(f"  Cost: {option['cost']}")
        if 'hourly_rate' in option:
            print(f"  Hourly Rate: {option['hourly_rate']}")
        print(f"  Setup Time: {option['setup_time']}")
        
        print("  Pros:")
        for pro in option['pros']:
            print(f"    + {pro}")
        
        print("  Cons:")
        for con in option['cons']:
            print(f"    - {con}")
    
    return formatted


def example_cost_scaling():
    """Example: Show how costs scale with training time"""
    print("\n=== Cost Scaling Analysis ===\n")
    
    cloud_service = get_cloud_platform_service()
    
    training_times = [1, 5, 10, 24, 48]
    
    print("Cost scaling for different training durations:\n")
    print(f"{'Hours':<10} {'Local':<15} {'RunPod':<15} {'Lambda':<15} {'Together':<15}")
    print("-" * 70)
    
    for hours in training_times:
        comparison = cloud_service.compare_costs(
            training_hours=float(hours),
            local_gpu_type=GPUType.RTX_4090,
            local_electricity_cost=0.50 * hours,  # $0.50/hr electricity
            min_memory_gb=24
        )
        
        # Find costs for each platform
        local_cost = comparison.local_estimate.total_cost_usd if comparison.local_estimate else 0
        
        runpod_cost = next(
            (e.total_cost_usd for e in comparison.cloud_estimates if e.platform.value == "runpod"),
            0
        )
        
        lambda_cost = next(
            (e.total_cost_usd for e in comparison.cloud_estimates if e.platform.value == "lambda_labs"),
            0
        )
        
        together_cost = next(
            (e.total_cost_usd for e in comparison.cloud_estimates if e.platform.value == "together_ai"),
            0
        )
        
        print(f"{hours:<10} ${local_cost:<14.2f} ${runpod_cost:<14.2f} ${lambda_cost:<14.2f} ${together_cost:<14.2f}")


def run_all_examples():
    """Run all examples"""
    print("\n" + "="*70)
    print("Cloud Platform Integration Examples")
    print("="*70)
    
    example_basic_comparison()
    example_local_vs_cloud()
    example_specific_gpu()
    example_platform_specific()
    example_setup_instructions()
    example_formatted_comparison()
    example_cost_scaling()
    
    print("\n" + "="*70)
    print("Examples Complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    run_all_examples()
