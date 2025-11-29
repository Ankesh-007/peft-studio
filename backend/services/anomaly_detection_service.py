"""
Anomaly detection and recovery service for training runs.
Detects common training issues and provides recovery strategies.
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Callable
from enum import Enum
import numpy as np


class AnomalyType(Enum):
    """Types of training anomalies"""
    LOSS_DIVERGENCE = "loss_divergence"
    GRADIENT_EXPLOSION = "gradient_explosion"
    OVERFITTING = "overfitting"
    OOM = "oom"
    MEMORY_LEAK = "memory_leak"


class AnomalySeverity(Enum):
    """Severity levels for anomalies"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Action:
    """Suggested action to resolve an anomaly"""
    description: str
    automatic: bool
    execute: Optional[Callable] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'description': self.description,
            'automatic': self.automatic
        }


@dataclass
class Anomaly:
    """Detected training anomaly"""
    type: AnomalyType
    severity: AnomalySeverity
    message: str
    detected_at: Dict[str, Any]  # step, timestamp
    suggested_actions: List[Action]
    auto_recoverable: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'type': self.type.value,
            'severity': self.severity.value,
            'message': self.message,
            'detected_at': self.detected_at,
            'suggested_actions': [action.to_dict() for action in self.suggested_actions],
            'auto_recoverable': self.auto_recoverable
        }


class AnomalyDetectionService:
    """Service for detecting and recovering from training anomalies"""
    
    def __init__(self):
        self.loss_history: Dict[str, List[float]] = {}
        self.gradient_history: Dict[str, List[float]] = {}
        self.memory_history: Dict[str, List[float]] = {}
        self.val_loss_history: Dict[str, List[float]] = {}
        self.train_loss_history: Dict[str, List[float]] = {}
        
        # Thresholds
        self.memory_threshold = 0.90  # 90% GPU memory usage
        self.loss_divergence_threshold = 2.0  # 2x increase in loss
        self.gradient_explosion_threshold = 10.0  # gradient norm threshold
        self.overfitting_gap_threshold = 0.5  # train-val loss gap
    
    def detect_loss_divergence(
        self,
        job_id: str,
        current_loss: float,
        step: int
    ) -> Optional[Anomaly]:
        """
        Detect if loss is diverging (increasing rapidly).
        
        Args:
            job_id: Training job identifier
            current_loss: Current loss value
            step: Current training step
            
        Returns:
            Anomaly if detected, None otherwise
        """
        # Initialize history if needed
        if job_id not in self.loss_history:
            self.loss_history[job_id] = []
        
        self.loss_history[job_id].append(current_loss)
        
        # Need at least 5 data points to detect divergence
        if len(self.loss_history[job_id]) < 5:
            return None
        
        # Check if loss is NaN or infinite
        if not np.isfinite(current_loss):
            return Anomaly(
                type=AnomalyType.LOSS_DIVERGENCE,
                severity=AnomalySeverity.CRITICAL,
                message="Training loss has become NaN or infinite. This indicates numerical instability.",
                detected_at={'step': step, 'timestamp': None},
                suggested_actions=[
                    Action(
                        description="Reduce learning rate by 50% and restart from last checkpoint",
                        automatic=True
                    ),
                    Action(
                        description="Enable gradient clipping to prevent numerical overflow",
                        automatic=True
                    ),
                    Action(
                        description="Check your dataset for corrupted or extreme values",
                        automatic=False
                    )
                ],
                auto_recoverable=True
            )
        
        # Get recent loss values
        recent_losses = self.loss_history[job_id][-5:]
        
        # Check if loss is consistently increasing
        if len(recent_losses) >= 3:
            # Calculate if loss has increased significantly
            min_recent = min(recent_losses[:-1])
            if current_loss > min_recent * self.loss_divergence_threshold:
                return Anomaly(
                    type=AnomalyType.LOSS_DIVERGENCE,
                    severity=AnomalySeverity.HIGH,
                    message=f"Training loss has increased by {((current_loss/min_recent - 1) * 100):.1f}% from recent minimum. The model may be diverging.",
                    detected_at={'step': step, 'timestamp': None},
                    suggested_actions=[
                        Action(
                            description="Reduce learning rate by 50%",
                            automatic=True
                        ),
                        Action(
                            description="Reload from the last stable checkpoint",
                            automatic=True
                        ),
                        Action(
                            description="Consider using a smaller learning rate or different optimizer",
                            automatic=False
                        )
                    ],
                    auto_recoverable=True
                )
        
        return None
    
    def detect_gradient_explosion(
        self,
        job_id: str,
        grad_norm: float,
        step: int
    ) -> Optional[Anomaly]:
        """
        Detect if gradients are exploding.
        
        Args:
            job_id: Training job identifier
            grad_norm: Current gradient norm
            step: Current training step
            
        Returns:
            Anomaly if detected, None otherwise
        """
        # Initialize history if needed
        if job_id not in self.gradient_history:
            self.gradient_history[job_id] = []
        
        self.gradient_history[job_id].append(grad_norm)
        
        # Check if gradient norm is extremely high
        if grad_norm > self.gradient_explosion_threshold:
            return Anomaly(
                type=AnomalyType.GRADIENT_EXPLOSION,
                severity=AnomalySeverity.HIGH,
                message=f"Gradient norm ({grad_norm:.2f}) has exceeded safe threshold ({self.gradient_explosion_threshold}). This can cause training instability.",
                detected_at={'step': step, 'timestamp': None},
                suggested_actions=[
                    Action(
                        description="Enable gradient clipping with max_norm=1.0",
                        automatic=True
                    ),
                    Action(
                        description="Reduce learning rate by 50%",
                        automatic=True
                    ),
                    Action(
                        description="Restart from last stable checkpoint",
                        automatic=False
                    )
                ],
                auto_recoverable=True
            )
        
        # Check for sudden spike in gradient norm
        if len(self.gradient_history[job_id]) >= 5:
            recent_grads = self.gradient_history[job_id][-5:]
            avg_grad = np.mean(recent_grads[:-1])
            
            if avg_grad > 0 and grad_norm > avg_grad * 5:
                return Anomaly(
                    type=AnomalyType.GRADIENT_EXPLOSION,
                    severity=AnomalySeverity.MEDIUM,
                    message=f"Gradient norm has spiked to {grad_norm:.2f}, which is 5x higher than recent average ({avg_grad:.2f}).",
                    detected_at={'step': step, 'timestamp': None},
                    suggested_actions=[
                        Action(
                            description="Enable gradient clipping",
                            automatic=True
                        ),
                        Action(
                            description="Monitor for continued instability",
                            automatic=False
                        )
                    ],
                    auto_recoverable=True
                )
        
        return None
    
    def detect_overfitting(
        self,
        job_id: str,
        train_loss: float,
        val_loss: float,
        step: int
    ) -> Optional[Anomaly]:
        """
        Detect if model is overfitting.
        
        Args:
            job_id: Training job identifier
            train_loss: Current training loss
            val_loss: Current validation loss
            step: Current training step
            
        Returns:
            Anomaly if detected, None otherwise
        """
        # Initialize history if needed
        if job_id not in self.train_loss_history:
            self.train_loss_history[job_id] = []
        if job_id not in self.val_loss_history:
            self.val_loss_history[job_id] = []
        
        self.train_loss_history[job_id].append(train_loss)
        self.val_loss_history[job_id].append(val_loss)
        
        # Need at least 3 data points to detect overfitting
        if len(self.train_loss_history[job_id]) < 3:
            return None
        
        # Check if validation loss is significantly higher than training loss
        loss_gap = val_loss - train_loss
        
        if loss_gap > self.overfitting_gap_threshold:
            # Check if validation loss is increasing while training loss decreases
            recent_train = self.train_loss_history[job_id][-3:]
            recent_val = self.val_loss_history[job_id][-3:]
            
            train_decreasing = recent_train[-1] < recent_train[0]
            val_increasing = recent_val[-1] > recent_val[0]
            
            if train_decreasing and val_increasing:
                return Anomaly(
                    type=AnomalyType.OVERFITTING,
                    severity=AnomalySeverity.MEDIUM,
                    message=f"Model appears to be overfitting. Training loss is decreasing ({train_loss:.4f}) while validation loss is increasing ({val_loss:.4f}).",
                    detected_at={'step': step, 'timestamp': None},
                    suggested_actions=[
                        Action(
                            description="Consider early stopping to prevent further overfitting",
                            automatic=False
                        ),
                        Action(
                            description="Increase dropout rate or add regularization",
                            automatic=False
                        ),
                        Action(
                            description="Use a smaller model or reduce training epochs",
                            automatic=False
                        )
                    ],
                    auto_recoverable=False
                )
        
        return None
    
    def detect_memory_issue(
        self,
        job_id: str,
        gpu_memory_used: List[float],
        gpu_memory_total: List[float],
        step: int
    ) -> Optional[Anomaly]:
        """
        Detect if GPU memory usage is too high.
        
        Args:
            job_id: Training job identifier
            gpu_memory_used: List of memory used per GPU (MB)
            gpu_memory_total: List of total memory per GPU (MB)
            step: Current training step
            
        Returns:
            Anomaly if detected, None otherwise
        """
        if not gpu_memory_used or not gpu_memory_total:
            return None
        
        # Calculate memory utilization for each GPU
        memory_utilizations = []
        for used, total in zip(gpu_memory_used, gpu_memory_total):
            if total > 0:
                utilization = used / total
                memory_utilizations.append(utilization)
        
        if not memory_utilizations:
            return None
        
        # Check if any GPU exceeds threshold
        max_utilization = max(memory_utilizations)
        
        if max_utilization > self.memory_threshold:
            gpu_idx = memory_utilizations.index(max_utilization)
            return Anomaly(
                type=AnomalyType.OOM,
                severity=AnomalySeverity.HIGH,
                message=f"GPU {gpu_idx} memory usage is at {max_utilization*100:.1f}% ({gpu_memory_used[gpu_idx]:.0f}MB / {gpu_memory_total[gpu_idx]:.0f}MB). Risk of out-of-memory error.",
                detected_at={'step': step, 'timestamp': None},
                suggested_actions=[
                    Action(
                        description="Reduce batch size by 50%",
                        automatic=True
                    ),
                    Action(
                        description="Enable gradient checkpointing to save memory",
                        automatic=True
                    ),
                    Action(
                        description="Consider using a smaller model or quantization",
                        automatic=False
                    )
                ],
                auto_recoverable=True
            )
        
        # Track memory history for leak detection
        if job_id not in self.memory_history:
            self.memory_history[job_id] = []
        
        self.memory_history[job_id].append(max_utilization)
        
        # Detect memory leak (consistently increasing memory usage)
        if len(self.memory_history[job_id]) >= 10:
            recent_memory = self.memory_history[job_id][-10:]
            
            # Check if memory is consistently increasing
            increasing_count = sum(
                1 for i in range(1, len(recent_memory))
                if recent_memory[i] > recent_memory[i-1]
            )
            
            if increasing_count >= 7:  # 7 out of 9 increases
                return Anomaly(
                    type=AnomalyType.MEMORY_LEAK,
                    severity=AnomalySeverity.MEDIUM,
                    message="GPU memory usage is consistently increasing, suggesting a potential memory leak.",
                    detected_at={'step': step, 'timestamp': None},
                    suggested_actions=[
                        Action(
                            description="Clear GPU cache periodically",
                            automatic=True
                        ),
                        Action(
                            description="Monitor for continued increase",
                            automatic=False
                        ),
                        Action(
                            description="Check for memory leaks in custom code",
                            automatic=False
                        )
                    ],
                    auto_recoverable=True
                )
        
        return None
    
    def check_all_anomalies(
        self,
        job_id: str,
        step: int,
        loss: float,
        grad_norm: Optional[float] = None,
        val_loss: Optional[float] = None,
        gpu_memory_used: Optional[List[float]] = None,
        gpu_memory_total: Optional[List[float]] = None
    ) -> List[Anomaly]:
        """
        Check for all types of anomalies.
        
        Args:
            job_id: Training job identifier
            step: Current training step
            loss: Current training loss
            grad_norm: Current gradient norm (optional)
            val_loss: Current validation loss (optional)
            gpu_memory_used: GPU memory used per device (optional)
            gpu_memory_total: GPU memory total per device (optional)
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Check loss divergence
        loss_anomaly = self.detect_loss_divergence(job_id, loss, step)
        if loss_anomaly:
            anomalies.append(loss_anomaly)
        
        # Check gradient explosion
        if grad_norm is not None:
            grad_anomaly = self.detect_gradient_explosion(job_id, grad_norm, step)
            if grad_anomaly:
                anomalies.append(grad_anomaly)
        
        # Check overfitting
        if val_loss is not None:
            overfit_anomaly = self.detect_overfitting(job_id, loss, val_loss, step)
            if overfit_anomaly:
                anomalies.append(overfit_anomaly)
        
        # Check memory issues
        if gpu_memory_used and gpu_memory_total:
            memory_anomaly = self.detect_memory_issue(
                job_id, gpu_memory_used, gpu_memory_total, step
            )
            if memory_anomaly:
                anomalies.append(memory_anomaly)
        
        return anomalies
    
    def clear_history(self, job_id: str):
        """Clear all history for a job"""
        if job_id in self.loss_history:
            del self.loss_history[job_id]
        if job_id in self.gradient_history:
            del self.gradient_history[job_id]
        if job_id in self.memory_history:
            del self.memory_history[job_id]
        if job_id in self.val_loss_history:
            del self.val_loss_history[job_id]
        if job_id in self.train_loss_history:
            del self.train_loss_history[job_id]


# Global anomaly detection service instance
_anomaly_service = None


def get_anomaly_detection_service() -> AnomalyDetectionService:
    """Get or create the global anomaly detection service instance"""
    global _anomaly_service
    if _anomaly_service is None:
        _anomaly_service = AnomalyDetectionService()
    return _anomaly_service
