"""
Example integration of quality analysis and notifications with training orchestration.

This demonstrates how to use the quality analysis and notification services
with the training orchestrator.
"""

import logging
from services.training_orchestration_service import (
    get_training_orchestrator,
    TrainingConfig
)
from services.quality_analysis_service import generate_quality_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def notification_handler(notification):
    """Handle incoming notifications"""
    logger.info(f"📢 NOTIFICATION: {notification.title}")
    logger.info(f"   Message: {notification.message}")
    if notification.milestone:
        logger.info(f"   Milestone: {notification.milestone}%")
    logger.info(f"   Urgency: {notification.urgency}")
    logger.info("")


def metrics_handler(metrics):
    """Handle metrics updates"""
    if metrics.step % 100 == 0:  # Log every 100 steps
        logger.info(f"Step {metrics.step}: Loss={metrics.loss:.4f}, LR={metrics.learning_rate:.6f}")


def run_training_with_quality_analysis():
    """
    Example: Run a training job with quality analysis and notifications.
    """
    logger.info("=" * 60)
    logger.info("Training with Quality Analysis and Notifications Example")
    logger.info("=" * 60)
    logger.info("")
    
    # Get orchestrator
    orchestrator = get_training_orchestrator()
    
    # Create training configuration
    config = TrainingConfig(
        job_id="example-training-001",
        model_name="meta-llama/Llama-2-7b-hf",
        dataset_path="./data/example_dataset.json",
        output_dir="./output/example-001",
        num_epochs=3,
        max_steps=1000,
        learning_rate=2e-4,
        batch_size=4,
        save_steps=250
    )
    
    # Create job
    job = orchestrator.create_job(config)
    logger.info(f"✅ Created training job: {job.job_id}")
    logger.info("")
    
    # Register callbacks
    orchestrator.register_metrics_callback(job.job_id, metrics_handler)
    orchestrator.register_notification_callback(job.job_id, notification_handler)
    logger.info("✅ Registered callbacks for metrics and notifications")
    logger.info("")
    
    # Start training
    logger.info("🚀 Starting training...")
    logger.info("")
    orchestrator.start_training(job.job_id)
    
    # Wait for training to complete
    import time
    while True:
        status = orchestrator.get_status(job.job_id)
        
        if status.state in ["completed", "failed", "stopped"]:
            break
        
        time.sleep(1)
    
    # Get final status
    final_status = orchestrator.get_status(job.job_id)
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"Training Status: {final_status.state.value.upper()}")
    logger.info("=" * 60)
    logger.info("")
    
    # Display quality analysis
    if final_status.quality_analysis:
        logger.info("📊 QUALITY ANALYSIS")
        logger.info("=" * 60)
        report = generate_quality_report(final_status.quality_analysis)
        logger.info(report)
        logger.info("")
    else:
        logger.warning("⚠️  No quality analysis available")
        logger.info("")
    
    # Display notifications summary
    logger.info("📬 NOTIFICATIONS SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total notifications: {len(final_status.notifications)}")
    
    for i, notification in enumerate(final_status.notifications, 1):
        logger.info(f"\n{i}. {notification.title}")
        logger.info(f"   Type: {notification.type.value}")
        if notification.milestone:
            logger.info(f"   Milestone: {notification.milestone}%")
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("Example completed!")
    logger.info("=" * 60)


def demonstrate_manual_quality_analysis():
    """
    Example: Manually trigger quality analysis on a completed job.
    """
    from services.quality_analysis_service import analyze_training_quality, TrainingResult
    
    logger.info("=" * 60)
    logger.info("Manual Quality Analysis Example")
    logger.info("=" * 60)
    logger.info("")
    
    # Simulate training results
    training_result = TrainingResult(
        final_loss=0.35,
        initial_loss=2.1,
        epochs_completed=3,
        total_steps=1000,
        best_val_loss=0.42,
        convergence_achieved=True,
        gradient_norm_stable=True,
        loss_history=[2.1 - (i/1000) * 1.75 for i in range(1000)]
    )
    
    # Analyze quality
    analysis = analyze_training_quality(training_result)
    
    # Display report
    report = generate_quality_report(analysis)
    logger.info(report)
    logger.info("")


def demonstrate_notification_milestones():
    """
    Example: Demonstrate notification milestones.
    """
    from services.notification_service import check_progress_milestone, ProgressUpdate
    
    logger.info("=" * 60)
    logger.info("Notification Milestones Example")
    logger.info("=" * 60)
    logger.info("")
    
    total_steps = 1000
    
    # Simulate progress through training
    test_points = [
        (0, "Start"),
        (250, "25% milestone"),
        (500, "50% milestone"),
        (750, "75% milestone"),
        (1000, "100% completion")
    ]
    
    previous_step = 0
    
    for current_step, description in test_points:
        progress = ProgressUpdate(
            current_step=current_step,
            total_steps=total_steps,
            previous_step=previous_step
        )
        
        notification = check_progress_milestone(progress)
        
        logger.info(f"Step {current_step}/{total_steps} ({description})")
        if notification:
            logger.info(f"  ✅ Notification: {notification.title}")
            logger.info(f"     {notification.message}")
        else:
            logger.info(f"  ⏭️  No notification")
        logger.info("")
        
        previous_step = current_step


if __name__ == "__main__":
    # Run examples
    print("\n")
    
    # Example 1: Manual quality analysis
    demonstrate_manual_quality_analysis()
    
    print("\n")
    
    # Example 2: Notification milestones
    demonstrate_notification_milestones()
    
    print("\n")
    
    # Example 3: Full training with quality analysis (commented out as it takes time)
    # run_training_with_quality_analysis()
