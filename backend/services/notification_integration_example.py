"""
Notification System Integration Example

This example demonstrates how the notification system integrates with
the training orchestrator to provide desktop notifications, taskbar progress,
and Do Not Disturb support.
"""

from services.notification_service import (
    NotificationManager,
    ProgressUpdate,
    create_error_notification,
    check_do_not_disturb,
    calculate_taskbar_progress
)
from services.training_orchestration_service import get_training_orchestrator
import asyncio
import logging

logger = logging.getLogger(__name__)


async def example_training_with_notifications():
    """
    Example of training with full notification support.
    """
    # Get training orchestrator
    orchestrator = get_training_orchestrator()
    
    # Create a training job
    from services.training_orchestration_service import TrainingConfig
    
    config = TrainingConfig(
        model_name="meta-llama/Llama-2-7b-hf",
        dataset_path="./data/training_data.jsonl",
        output_dir="./models/my_model",
        num_epochs=3,
        batch_size=4,
        learning_rate=2e-4,
        lora_r=16,
        lora_alpha=32
    )
    
    job_id = orchestrator.create_job(config)
    
    # Register notification callback
    async def notification_callback(notification):
        """Handle notifications from training."""
        logger.info(f"Notification: {notification.title}")
        logger.info(f"Message: {notification.message}")
        logger.info(f"Urgency: {notification.urgency}")
        logger.info(f"Sound: {notification.sound}")
        
        # In a real application, this would:
        # 1. Send to Electron main process via IPC
        # 2. Show desktop notification
        # 3. Update taskbar progress
        # 4. Play sound if enabled
        
        # Example: Send to frontend via WebSocket
        # await websocket.send_json({
        #     "type": "notification",
        #     "data": {
        #         "type": notification.type.value,
        #         "title": notification.title,
        #         "message": notification.message,
        #         "urgency": notification.urgency,
        #         "sound": notification.sound,
        #         "taskbar_progress": notification.taskbar_progress
        #     }
        # })
    
    orchestrator.register_notification_callback(job_id, notification_callback)
    
    # Start training
    orchestrator.start_training(job_id)
    
    # Monitor progress
    while True:
        status = orchestrator.get_status(job_id)
        
        if status["state"] in ["COMPLETED", "FAILED"]:
            break
        
        await asyncio.sleep(1)
    
    logger.info(f"Training finished with state: {status['state']}")


def example_error_notification():
    """
    Example of creating and handling error notifications.
    """
    # Simulate different types of errors
    error_types = [
        ("Out of memory error occurred", "oom_error"),
        ("CUDA error: device-side assert triggered", "cuda_error"),
        ("Loss diverged to infinity", "loss_divergence"),
        ("Gradient explosion detected", "gradient_explosion"),
        ("Dataset validation failed", "data_error")
    ]
    
    for error_message, error_type in error_types:
        notification = create_error_notification(error_message, error_type)
        
        logger.info(f"\nError Type: {error_type}")
        logger.info(f"Title: {notification.title}")
        logger.info(f"Message: {notification.message}")
        logger.info(f"Urgency: {notification.urgency}")
        logger.info(f"Sound: {notification.sound}")
        logger.info(f"Actions: {notification.actions}")
        logger.info(f"Respects DND: {notification.respect_dnd}")


def example_progress_notifications():
    """
    Example of progress milestone notifications.
    """
    notification_manager = NotificationManager()
    
    total_steps = 1000
    
    # Simulate training progress
    for step in range(0, total_steps + 1, 50):
        progress_update = ProgressUpdate(
            current_step=step,
            total_steps=total_steps,
            previous_step=max(0, step - 50)
        )
        
        notification = notification_manager.get_next_notification(progress_update)
        
        if notification:
            logger.info(f"\nStep {step}/{total_steps}")
            logger.info(f"Milestone: {notification.milestone}%")
            logger.info(f"Title: {notification.title}")
            logger.info(f"Message: {notification.message}")
            logger.info(f"Taskbar Progress: {notification.taskbar_progress:.2%}")
            logger.info(f"Sound: {notification.sound}")


def example_dnd_integration():
    """
    Example of Do Not Disturb integration.
    """
    # Check current DND status
    dnd_enabled = check_do_not_disturb()
    logger.info(f"Do Not Disturb enabled: {dnd_enabled}")
    
    # Create notification manager
    notification_manager = NotificationManager()
    
    # Create a progress notification
    progress_update = ProgressUpdate(
        current_step=250,
        total_steps=1000,
        previous_step=200
    )
    
    notification = notification_manager.get_next_notification(progress_update)
    
    if notification:
        logger.info(f"Notification would be shown: {notification.title}")
    else:
        logger.info("Notification suppressed due to Do Not Disturb")
    
    # Error notifications always bypass DND
    error_notification = create_error_notification(
        "Critical error occurred",
        "system_crash"
    )
    
    logger.info(f"\nError notification respects DND: {error_notification.respect_dnd}")
    logger.info("Error notifications always show regardless of DND status")


def example_taskbar_progress():
    """
    Example of taskbar progress calculation.
    """
    total_steps = 1000
    
    for step in [0, 250, 500, 750, 1000]:
        progress = calculate_taskbar_progress(step, total_steps)
        logger.info(f"Step {step}/{total_steps}: Taskbar progress = {progress:.2%}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("Notification System Integration Examples")
    print("=" * 60)
    
    print("\n1. Error Notifications")
    print("-" * 60)
    example_error_notification()
    
    print("\n2. Progress Notifications")
    print("-" * 60)
    example_progress_notifications()
    
    print("\n3. Do Not Disturb Integration")
    print("-" * 60)
    example_dnd_integration()
    
    print("\n4. Taskbar Progress")
    print("-" * 60)
    example_taskbar_progress()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
