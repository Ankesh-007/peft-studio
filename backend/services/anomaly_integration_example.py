"""
Example integration of anomaly detection with training orchestration.
This demonstrates how to use the anomaly detection service during training.
"""

from typing import Optional, List
from .anomaly_detection_service import get_anomaly_detection_service, Anomaly
from .monitoring_service import get_monitoring_service


class TrainingWithAnomalyDetection:
    """
    Example class showing how to integrate anomaly detection into training loop.
    """
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.anomaly_service = get_anomaly_detection_service()
        self.monitoring_service = get_monitoring_service()
        self.current_batch_size = 32
        self.current_learning_rate = 1e-4
        self.gradient_clipping_enabled = False
    
    def training_step(
        self,
        step: int,
        loss: float,
        grad_norm: Optional[float] = None,
        val_loss: Optional[float] = None,
        gpu_memory_used: Optional[List[float]] = None,
        gpu_memory_total: Optional[List[float]] = None
    ) -> List[Anomaly]:
        """
        Execute a training step with anomaly detection.
        
        Returns:
            List of detected anomalies
        """
        # Check for anomalies
        anomalies = self.anomaly_service.check_all_anomalies(
            job_id=self.job_id,
            step=step,
            loss=loss,
            grad_norm=grad_norm,
            val_loss=val_loss,
            gpu_memory_used=gpu_memory_used,
            gpu_memory_total=gpu_memory_total
        )
        
        # Handle detected anomalies
        for anomaly in anomalies:
            print(f"[Step {step}] Anomaly detected: {anomaly.type.value}")
            print(f"  Message: {anomaly.message}")
            print(f"  Severity: {anomaly.severity.value}")
            
            # Apply automatic recovery actions
            if anomaly.auto_recoverable:
                self._apply_recovery_actions(anomaly)
        
        return anomalies
    
    def _apply_recovery_actions(self, anomaly: Anomaly):
        """
        Apply automatic recovery actions for an anomaly.
        """
        for action in anomaly.suggested_actions:
            if not action.automatic:
                continue
            
            desc_lower = action.description.lower()
            
            # Handle batch size reduction
            if 'batch' in desc_lower and 'reduce' in desc_lower:
                self.current_batch_size = max(1, self.current_batch_size // 2)
                print(f"  → Automatically reduced batch size to {self.current_batch_size}")
            
            # Handle learning rate reduction
            elif 'learning rate' in desc_lower and 'reduce' in desc_lower:
                self.current_learning_rate *= 0.5
                print(f"  → Automatically reduced learning rate to {self.current_learning_rate}")
            
            # Handle gradient clipping
            elif 'gradient' in desc_lower and 'clip' in desc_lower:
                self.gradient_clipping_enabled = True
                print(f"  → Automatically enabled gradient clipping")
            
            # Handle gradient checkpointing
            elif 'gradient' in desc_lower and 'checkpoint' in desc_lower:
                print(f"  → Automatically enabled gradient checkpointing")
    
    def cleanup(self):
        """Clean up resources"""
        self.anomaly_service.clear_history(self.job_id)


# Example usage
if __name__ == "__main__":
    # Create training instance
    trainer = TrainingWithAnomalyDetection(job_id="example_job")
    
    # Simulate training steps
    print("=== Simulating Training with Anomaly Detection ===\n")
    
    # Step 1: Normal training
    print("Step 1: Normal training")
    anomalies = trainer.training_step(
        step=1,
        loss=2.5,
        grad_norm=1.2,
        gpu_memory_used=[5000.0],
        gpu_memory_total=[10000.0]
    )
    print(f"Detected {len(anomalies)} anomalies\n")
    
    # Step 2: High memory usage
    print("Step 2: High memory usage (>90%)")
    anomalies = trainer.training_step(
        step=2,
        loss=2.3,
        grad_norm=1.5,
        gpu_memory_used=[9500.0],  # 95% usage
        gpu_memory_total=[10000.0]
    )
    print(f"Detected {len(anomalies)} anomalies\n")
    
    # Step 3: Gradient explosion
    print("Step 3: Gradient explosion")
    anomalies = trainer.training_step(
        step=3,
        loss=2.1,
        grad_norm=15.0,  # Very high gradient
        gpu_memory_used=[5000.0],
        gpu_memory_total=[10000.0]
    )
    print(f"Detected {len(anomalies)} anomalies\n")
    
    # Step 4: Loss divergence
    print("Step 4: Loss divergence")
    # Build up history first
    for i in range(5):
        trainer.training_step(
            step=4+i,
            loss=2.0 + i * 0.1,
            grad_norm=1.0,
            gpu_memory_used=[5000.0],
            gpu_memory_total=[10000.0]
        )
    
    # Now trigger divergence
    anomalies = trainer.training_step(
        step=10,
        loss=10.0,  # Sudden spike
        grad_norm=1.0,
        gpu_memory_used=[5000.0],
        gpu_memory_total=[10000.0]
    )
    print(f"Detected {len(anomalies)} anomalies\n")
    
    # Cleanup
    trainer.cleanup()
    print("=== Training simulation complete ===")
