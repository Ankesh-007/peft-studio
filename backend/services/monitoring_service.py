"""
Real-time training monitoring service.
Collects and streams training metrics via WebSocket.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
import time
import psutil
import GPUtil


@dataclass
class TrainingMetrics:
    """Real-time training metrics"""
    # Training progress
    step: int
    epoch: int
    loss: float
    learning_rate: float
    throughput: float  # steps/sec
    samples_per_second: float
    
    # Optional fields
    grad_norm: Optional[float] = None
    
    # Resources
    gpu_utilization: List[float] = None  # per GPU
    gpu_memory_used: List[float] = None  # MB per GPU
    gpu_temperature: List[float] = None  # Celsius per GPU
    cpu_utilization: float = 0.0
    ram_used: float = 0.0  # MB
    
    # Validation (optional)
    val_loss: Optional[float] = None
    val_perplexity: Optional[float] = None
    
    # Timing
    timestamp: str = None
    elapsed_time: float = 0.0  # seconds
    estimated_time_remaining: float = 0.0  # seconds
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.gpu_utilization is None:
            self.gpu_utilization = []
        if self.gpu_memory_used is None:
            self.gpu_memory_used = []
        if self.gpu_temperature is None:
            self.gpu_temperature = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class MonitoringService:
    """Service for collecting and managing training metrics"""
    
    def __init__(self):
        self.metrics_history: Dict[str, List[TrainingMetrics]] = {}
        self.start_times: Dict[str, float] = {}
    
    def start_monitoring(self, job_id: str):
        """Start monitoring a training job"""
        self.metrics_history[job_id] = []
        self.start_times[job_id] = time.time()
    
    def stop_monitoring(self, job_id: str):
        """Stop monitoring a training job"""
        if job_id in self.metrics_history:
            del self.metrics_history[job_id]
        if job_id in self.start_times:
            del self.start_times[job_id]
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system resource metrics"""
        metrics = {
            'cpu_utilization': psutil.cpu_percent(interval=0.1),
            'ram_used': psutil.virtual_memory().used / (1024 ** 2),  # MB
            'gpu_utilization': [],
            'gpu_memory_used': [],
            'gpu_temperature': []
        }
        
        # Collect GPU metrics if available
        try:
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                metrics['gpu_utilization'].append(gpu.load * 100)
                metrics['gpu_memory_used'].append(gpu.memoryUsed)
                metrics['gpu_temperature'].append(gpu.temperature)
        except Exception:
            # GPU metrics not available
            pass
        
        return metrics
    
    def record_metrics(
        self,
        job_id: str,
        step: int,
        epoch: int,
        loss: float,
        learning_rate: float,
        throughput: float,
        samples_per_second: float,
        grad_norm: Optional[float] = None,
        val_loss: Optional[float] = None,
        val_perplexity: Optional[float] = None
    ) -> TrainingMetrics:
        """Record training metrics for a job"""
        
        # Collect system metrics
        system_metrics = self.collect_system_metrics()
        
        # Calculate elapsed time
        elapsed_time = 0.0
        if job_id in self.start_times:
            elapsed_time = time.time() - self.start_times[job_id]
        
        # Create metrics object
        metrics = TrainingMetrics(
            step=step,
            epoch=epoch,
            loss=loss,
            learning_rate=learning_rate,
            grad_norm=grad_norm,
            throughput=throughput,
            samples_per_second=samples_per_second,
            gpu_utilization=system_metrics['gpu_utilization'],
            gpu_memory_used=system_metrics['gpu_memory_used'],
            gpu_temperature=system_metrics['gpu_temperature'],
            cpu_utilization=system_metrics['cpu_utilization'],
            ram_used=system_metrics['ram_used'],
            val_loss=val_loss,
            val_perplexity=val_perplexity,
            elapsed_time=elapsed_time,
            estimated_time_remaining=0.0  # Will be calculated separately
        )
        
        # Store in history
        if job_id not in self.metrics_history:
            self.metrics_history[job_id] = []
        self.metrics_history[job_id].append(metrics)
        
        return metrics
    
    def get_metrics_history(
        self,
        job_id: str,
        limit: Optional[int] = None
    ) -> List[TrainingMetrics]:
        """Get metrics history for a job"""
        if job_id not in self.metrics_history:
            return []
        
        history = self.metrics_history[job_id]
        if limit:
            return history[-limit:]
        return history
    
    def get_latest_metrics(self, job_id: str) -> Optional[TrainingMetrics]:
        """Get the most recent metrics for a job"""
        if job_id not in self.metrics_history or not self.metrics_history[job_id]:
            return None
        return self.metrics_history[job_id][-1]
    
    def calculate_loss_zone(
        self,
        current_loss: float,
        previous_loss: Optional[float] = None
    ) -> str:
        """
        Calculate color zone for loss visualization.
        Returns: 'green', 'yellow', or 'red'
        """
        # Handle invalid inputs
        if current_loss < 0 or not isinstance(current_loss, (int, float)):
            return 'red'
        
        good_threshold = 1.0
        acceptable_threshold = 2.0
        
        # If we have previous loss, check for trend
        if previous_loss is not None and previous_loss > 0:
            loss_change = current_loss - previous_loss
            percent_change = (loss_change / previous_loss) * 100
            
            # Red zone: Loss is increasing significantly (>10% increase)
            if percent_change > 10:
                return 'red'
            
            # Red zone: Loss is very high (>acceptableThreshold)
            if current_loss > acceptable_threshold:
                return 'red'
            
            # Yellow zone: Loss is slightly increasing or stable
            if percent_change > 0 or abs(percent_change) < 1:
                return 'yellow'
            
            # Green zone: Loss is decreasing and below good threshold
            if loss_change < 0 and current_loss < good_threshold:
                return 'green'
            
            # Yellow zone: Loss is decreasing but still above good threshold
            if loss_change < 0 and current_loss >= good_threshold:
                return 'yellow'
        
        # No previous loss - judge based on absolute value only
        if current_loss < good_threshold:
            return 'green'
        elif current_loss < acceptable_threshold:
            return 'yellow'
        else:
            return 'red'
    
    def estimate_time_remaining(
        self,
        job_id: str,
        current_step: int,
        total_steps: int
    ) -> float:
        """
        Estimate remaining training time based on recent throughput.
        Returns: estimated seconds remaining
        """
        if job_id not in self.metrics_history or not self.metrics_history[job_id]:
            return 0.0
        
        # Get recent metrics (last 10 data points)
        recent_metrics = self.metrics_history[job_id][-10:]
        
        # Calculate average throughput
        avg_throughput = sum(m.throughput for m in recent_metrics) / len(recent_metrics)
        
        if avg_throughput <= 0:
            return 0.0
        
        # Calculate remaining steps
        remaining_steps = total_steps - current_step
        
        # Estimate time
        estimated_seconds = remaining_steps / avg_throughput
        
        return estimated_seconds


# Global monitoring service instance
_monitoring_service = None


def get_monitoring_service() -> MonitoringService:
    """Get or create the global monitoring service instance"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service
