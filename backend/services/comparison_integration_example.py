"""
Example integration of the Training Run Comparison System.

This demonstrates how to use the comparison service to:
1. Add completed training runs to the comparison cache
2. Compare multiple runs
3. Generate charts and identify best performers
4. Calculate configuration differences
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from datetime import datetime
from services.comparison_service import (
    get_comparison_service,
    TrainingRunSummary
)


def example_comparison_workflow():
    """
    Example workflow showing how to use the comparison system.
    """
    print("=" * 80)
    print("Training Run Comparison System - Example Workflow")
    print("=" * 80)
    
    # Get the comparison service
    comparison_service = get_comparison_service()
    
    # Step 1: Add completed training runs
    print("\n1. Adding training runs to comparison cache...")
    
    run1 = TrainingRunSummary(
        job_id="job_001",
        model_name="llama-7b",
        dataset_name="alpaca",
        final_loss=0.45,
        best_val_loss=0.52,
        final_learning_rate=2e-4,
        total_steps=5000,
        epochs_completed=3,
        training_time_seconds=7200.0,  # 2 hours
        config={
            'learning_rate': 2e-4,
            'batch_size': 4,
            'lora_r': 8,
            'lora_alpha': 16,
            'optimizer': 'adamw',
            'scheduler': 'linear'
        },
        quality_score=85.5,
        started_at=datetime(2024, 1, 1, 10, 0),
        completed_at=datetime(2024, 1, 1, 12, 0)
    )
    
    run2 = TrainingRunSummary(
        job_id="job_002",
        model_name="llama-7b",
        dataset_name="alpaca",
        final_loss=0.38,
        best_val_loss=0.44,
        final_learning_rate=3e-4,
        total_steps=5000,
        epochs_completed=3,
        training_time_seconds=6800.0,  # 1.89 hours
        config={
            'learning_rate': 3e-4,  # Higher learning rate
            'batch_size': 8,  # Larger batch size
            'lora_r': 16,  # Higher rank
            'lora_alpha': 32,
            'optimizer': 'adamw',
            'scheduler': 'cosine'  # Different scheduler
        },
        quality_score=92.3,
        started_at=datetime(2024, 1, 2, 10, 0),
        completed_at=datetime(2024, 1, 2, 11, 53)
    )
    
    run3 = TrainingRunSummary(
        job_id="job_003",
        model_name="mistral-7b",
        dataset_name="alpaca",
        final_loss=0.42,
        best_val_loss=0.48,
        final_learning_rate=2e-4,
        total_steps=5000,
        epochs_completed=3,
        training_time_seconds=6500.0,  # 1.81 hours
        config={
            'learning_rate': 2e-4,
            'batch_size': 4,
            'lora_r': 8,
            'lora_alpha': 16,
            'optimizer': 'adamw',
            'scheduler': 'linear'
        },
        quality_score=88.7,
        started_at=datetime(2024, 1, 3, 10, 0),
        completed_at=datetime(2024, 1, 3, 11, 48)
    )
    
    comparison_service.add_run(run1)
    comparison_service.add_run(run2)
    comparison_service.add_run(run3)
    
    print(f"   Added {len(comparison_service.list_all_runs())} runs to cache")
    
    # Step 2: Compare all three runs
    print("\n2. Comparing all three training runs...")
    
    result = comparison_service.compare_runs(
        job_ids=["job_001", "job_002", "job_003"],
        include_charts=True,
        include_config_diff=False  # Only works for 2 runs
    )
    
    print(f"   Comparison includes {len(result.runs)} runs")
    print(f"   Generated {len(result.charts)} comparison charts")
    print(f"   Identified {len(result.best_performers)} best performers")
    
    # Step 3: Display best performers
    print("\n3. Best Performers:")
    for performer in result.best_performers:
        direction = "lowest" if performer.is_lower_better else "highest"
        print(f"   - {performer.metric_name}: {performer.job_id} ({direction} = {performer.value:.4f})")
    
    # Step 4: Display chart information
    print("\n4. Generated Charts:")
    for chart in result.charts:
        print(f"   - {chart.title} ({chart.chart_type})")
        print(f"     X-axis: {chart.x_label}, Y-axis: {chart.y_label}")
        print(f"     Series count: {len(chart.series)}")
    
    # Step 5: Compare just two runs with config diff
    print("\n5. Comparing two runs with configuration diff...")
    
    result_2 = comparison_service.compare_runs(
        job_ids=["job_001", "job_002"],
        include_charts=False,
        include_config_diff=True
    )
    
    print(f"   Configuration differences found: {len(result_2.config_diffs)}")
    
    # Display only the different parameters
    different_params = [d for d in result_2.config_diffs if d.is_different]
    print(f"\n   Parameters that differ ({len(different_params)}):")
    for diff in different_params:
        print(f"   - {diff.parameter}:")
        print(f"       job_001: {diff.run1_value}")
        print(f"       job_002: {diff.run2_value}")
    
    # Step 6: Demonstrate sortable table data
    print("\n6. Training Runs Table (sortable by any column):")
    print(f"   {'Job ID':<12} {'Model':<15} {'Final Loss':<12} {'Quality':<10} {'Time (hrs)':<12}")
    print("   " + "-" * 70)
    
    for run in result.runs:
        time_hrs = run.training_time_seconds / 3600
        quality = f"{run.quality_score:.1f}" if run.quality_score else "N/A"
        print(f"   {run.job_id:<12} {run.model_name:<15} {run.final_loss:<12.4f} {quality:<10} {time_hrs:<12.2f}")
    
    print("\n" + "=" * 80)
    print("Comparison workflow complete!")
    print("=" * 80)
    
    return result


if __name__ == "__main__":
    # Run the example
    result = example_comparison_workflow()
    
    # Additional demonstration: Create new run with best settings
    print("\n\nBonus: Creating new run configuration based on best performer...")
    
    best_loss_performer = next(p for p in result.best_performers if p.metric_name == 'final_loss')
    best_run = next(r for r in result.runs if r.job_id == best_loss_performer.job_id)
    
    print(f"\nBest performing run: {best_run.job_id}")
    print(f"Configuration to replicate:")
    for key, value in best_run.config.items():
        print(f"  {key}: {value}")
    
    print("\nThis configuration can be used to create a new training run!")
