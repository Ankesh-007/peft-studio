"""
Hardware Profiling Service for detecting and validating system capabilities.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import torch
import platform
import psutil
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class GPUInfo:
    """Information about a GPU device"""
    id: int
    name: str
    memory_total: int  # bytes
    memory_available: int  # bytes
    memory_used: int  # bytes
    compute_capability: str
    cuda_version: str
    temperature: Optional[float] = None
    utilization: Optional[float] = None


@dataclass
class CPUInfo:
    """Information about CPU"""
    cores_physical: int
    cores_logical: int
    frequency_mhz: float
    architecture: str
    utilization: float


@dataclass
class RAMInfo:
    """Information about system RAM"""
    total: int  # bytes
    available: int  # bytes
    used: int  # bytes
    percent_used: float


@dataclass
class ThroughputMetrics:
    """Throughput benchmarking metrics"""
    model_size_mb: int
    tokens_per_second: float
    samples_per_second: float
    memory_used_mb: int
    batch_size: int
    sequence_length: int
    timestamp: datetime


@dataclass
class HardwareProfile:
    """Complete hardware profile"""
    gpus: List[GPUInfo]
    cpu: CPUInfo
    ram: RAMInfo
    platform: str
    python_version: str
    torch_version: str
    cuda_available: bool
    timestamp: datetime
    throughput_benchmarks: Optional[Dict[str, ThroughputMetrics]] = None


class HardwareService:
    """Service for hardware detection and profiling"""
    
    def __init__(self):
        self._cached_profile: Optional[HardwareProfile] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_duration = timedelta(minutes=5)
        self._throughput_cache: Dict[str, ThroughputMetrics] = {}
        logger.info("HardwareService initialized")
    
    def detect_gpus(self) -> List[GPUInfo]:
        """
        Detect all available GPUs and their specifications.
        
        Returns:
            List of GPUInfo objects
        """
        gpus = []
        
        if not torch.cuda.is_available():
            logger.warning("CUDA not available - no GPUs detected")
            return gpus
        
        try:
            num_gpus = torch.cuda.device_count()
            logger.info(f"Detected {num_gpus} GPU(s)")
            
            for i in range(num_gpus):
                props = torch.cuda.get_device_properties(i)
                
                # Get memory info
                memory_total = props.total_memory
                memory_reserved = torch.cuda.memory_reserved(i)
                memory_allocated = torch.cuda.memory_allocated(i)
                memory_available = memory_total - memory_reserved
                
                # Get compute capability
                compute_capability = f"{props.major}.{props.minor}"
                
                # Get CUDA version
                cuda_version = torch.version.cuda or "Unknown"
                
                gpu_info = GPUInfo(
                    id=i,
                    name=props.name,
                    memory_total=memory_total,
                    memory_available=memory_available,
                    memory_used=memory_allocated,
                    compute_capability=compute_capability,
                    cuda_version=cuda_version
                )
                
                # Try to get temperature and utilization (requires nvidia-ml-py3)
                try:
                    import pynvml
                    pynvml.nvmlInit()
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_info.temperature = temp
                    gpu_info.utilization = util.gpu
                    pynvml.nvmlShutdown()
                except ImportError:
                    logger.debug("pynvml not available - temperature and utilization not reported")
                except Exception as e:
                    logger.debug(f"Could not get GPU metrics: {str(e)}")
                
                gpus.append(gpu_info)
                logger.info(f"GPU {i}: {gpu_info.name} - {memory_total / (1024**3):.2f} GB")
            
        except Exception as e:
            logger.error(f"Error detecting GPUs: {str(e)}")
        
        return gpus
    
    def detect_cpu(self) -> CPUInfo:
        """
        Detect CPU specifications.
        
        Returns:
            CPUInfo object
        """
        try:
            cpu_freq = psutil.cpu_freq()
            
            cpu_info = CPUInfo(
                cores_physical=psutil.cpu_count(logical=False),
                cores_logical=psutil.cpu_count(logical=True),
                frequency_mhz=cpu_freq.current if cpu_freq else 0.0,
                architecture=platform.machine(),
                utilization=psutil.cpu_percent(interval=0.1)
            )
            
            logger.info(f"CPU: {cpu_info.cores_physical} physical cores, "
                       f"{cpu_info.cores_logical} logical cores")
            
            return cpu_info
            
        except Exception as e:
            logger.error(f"Error detecting CPU: {str(e)}")
            # Return minimal info
            return CPUInfo(
                cores_physical=1,
                cores_logical=1,
                frequency_mhz=0.0,
                architecture="unknown",
                utilization=0.0
            )
    
    def detect_ram(self) -> RAMInfo:
        """
        Detect RAM specifications.
        
        Returns:
            RAMInfo object
        """
        try:
            mem = psutil.virtual_memory()
            
            ram_info = RAMInfo(
                total=mem.total,
                available=mem.available,
                used=mem.used,
                percent_used=mem.percent
            )
            
            logger.info(f"RAM: {mem.total / (1024**3):.2f} GB total, "
                       f"{mem.available / (1024**3):.2f} GB available")
            
            return ram_info
            
        except Exception as e:
            logger.error(f"Error detecting RAM: {str(e)}")
            return RAMInfo(total=0, available=0, used=0, percent_used=0.0)
    
    def validate_cuda_environment(self) -> Dict[str, any]:
        """
        Validate CUDA environment and return status.
        
        Returns:
            Dictionary with validation results
        """
        validation = {
            "cuda_available": torch.cuda.is_available(),
            "cuda_version": torch.version.cuda,
            "cudnn_available": torch.backends.cudnn.is_available(),
            "cudnn_version": torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else None,
            "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "torch_version": torch.__version__,
            "errors": []
        }
        
        # Check for common issues
        if not validation["cuda_available"]:
            validation["errors"].append("CUDA is not available. GPU training will not work.")
        
        if validation["cuda_available"] and validation["gpu_count"] == 0:
            validation["errors"].append("CUDA is available but no GPUs detected.")
        
        if validation["cuda_available"] and not validation["cudnn_available"]:
            validation["errors"].append("cuDNN is not available. Some operations may be slower.")
        
        logger.info(f"CUDA validation: {validation}")
        return validation
    
    def benchmark_throughput(
        self, 
        model_size_mb: int = 7000,
        batch_size: int = 1,
        sequence_length: int = 512,
        num_iterations: int = 10
    ) -> ThroughputMetrics:
        """
        Benchmark throughput for a given model size.
        
        Args:
            model_size_mb: Approximate model size in MB
            batch_size: Batch size for benchmarking
            sequence_length: Sequence length for benchmarking
            num_iterations: Number of iterations to average
            
        Returns:
            ThroughputMetrics object
        """
        cache_key = f"{model_size_mb}_{batch_size}_{sequence_length}"
        
        # Check cache
        if cache_key in self._throughput_cache:
            logger.debug(f"Returning cached throughput metrics for {cache_key}")
            return self._throughput_cache[cache_key]
        
        if not torch.cuda.is_available():
            logger.warning("CUDA not available - cannot benchmark throughput")
            # Return dummy metrics for CPU-only systems
            return ThroughputMetrics(
                model_size_mb=model_size_mb,
                tokens_per_second=0.0,
                samples_per_second=0.0,
                memory_used_mb=0,
                batch_size=batch_size,
                sequence_length=sequence_length,
                timestamp=datetime.now()
            )
        
        try:
            logger.info(f"Benchmarking throughput for model size {model_size_mb}MB...")
            
            # Create a simple model for benchmarking
            # We'll use a linear layer as a proxy for model computation
            device = torch.device("cuda:0")
            
            # Estimate parameter count from model size (assuming fp16)
            # model_size_mb * 1024 * 1024 bytes / 2 bytes per param
            param_count = (model_size_mb * 1024 * 1024) // 2
            
            # Create a simple benchmark model
            hidden_size = min(4096, int((param_count / sequence_length) ** 0.5))
            
            # Simple linear layer for benchmarking
            model = torch.nn.Linear(hidden_size, hidden_size).to(device).half()
            
            # Create dummy input
            dummy_input = torch.randn(
                batch_size, 
                sequence_length, 
                hidden_size, 
                device=device, 
                dtype=torch.float16
            )
            
            # Warmup
            for _ in range(3):
                _ = model(dummy_input)
            
            torch.cuda.synchronize()
            
            # Benchmark
            import time
            start_time = time.time()
            
            for _ in range(num_iterations):
                _ = model(dummy_input)
                torch.cuda.synchronize()
            
            end_time = time.time()
            elapsed = end_time - start_time
            
            # Calculate metrics
            total_tokens = batch_size * sequence_length * num_iterations
            tokens_per_second = total_tokens / elapsed
            samples_per_second = (batch_size * num_iterations) / elapsed
            
            # Get memory usage
            memory_used = torch.cuda.memory_allocated(0) / (1024 * 1024)  # MB
            
            metrics = ThroughputMetrics(
                model_size_mb=model_size_mb,
                tokens_per_second=tokens_per_second,
                samples_per_second=samples_per_second,
                memory_used_mb=int(memory_used),
                batch_size=batch_size,
                sequence_length=sequence_length,
                timestamp=datetime.now()
            )
            
            # Cache the result
            self._throughput_cache[cache_key] = metrics
            
            logger.info(f"Throughput: {tokens_per_second:.2f} tokens/sec, "
                       f"{samples_per_second:.2f} samples/sec")
            
            # Cleanup
            del model
            del dummy_input
            torch.cuda.empty_cache()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error benchmarking throughput: {str(e)}")
            # Return minimal metrics on error
            return ThroughputMetrics(
                model_size_mb=model_size_mb,
                tokens_per_second=0.0,
                samples_per_second=0.0,
                memory_used_mb=0,
                batch_size=batch_size,
                sequence_length=sequence_length,
                timestamp=datetime.now()
            )
    
    def get_hardware_profile(self, use_cache: bool = True) -> HardwareProfile:
        """
        Get complete hardware profile with caching.
        
        Args:
            use_cache: Whether to use cached profile if available
            
        Returns:
            HardwareProfile object
        """
        # Check cache
        if use_cache and self._cached_profile and self._cache_timestamp:
            age = datetime.now() - self._cache_timestamp
            if age < self._cache_duration:
                logger.debug("Returning cached hardware profile")
                return self._cached_profile
        
        # Detect hardware
        logger.info("Detecting hardware profile...")
        
        # Run basic throughput benchmarks for common model sizes
        throughput_benchmarks = {}
        if torch.cuda.is_available():
            try:
                # Benchmark small, medium, and large models
                for size_name, size_mb in [("small", 1000), ("medium", 7000), ("large", 13000)]:
                    throughput_benchmarks[size_name] = self.benchmark_throughput(
                        model_size_mb=size_mb,
                        batch_size=1,
                        sequence_length=512,
                        num_iterations=5
                    )
            except Exception as e:
                logger.warning(f"Could not complete throughput benchmarks: {str(e)}")
        
        profile = HardwareProfile(
            gpus=self.detect_gpus(),
            cpu=self.detect_cpu(),
            ram=self.detect_ram(),
            platform=platform.system(),
            python_version=platform.python_version(),
            torch_version=torch.__version__,
            cuda_available=torch.cuda.is_available(),
            timestamp=datetime.now(),
            throughput_benchmarks=throughput_benchmarks if throughput_benchmarks else None
        )
        
        # Update cache
        self._cached_profile = profile
        self._cache_timestamp = datetime.now()
        
        return profile
    
    def get_available_memory(self, device_id: int = 0) -> int:
        """
        Get available GPU memory for a specific device.
        
        Args:
            device_id: GPU device ID
            
        Returns:
            Available memory in bytes
        """
        if not torch.cuda.is_available():
            return 0
        
        try:
            torch.cuda.set_device(device_id)
            memory_total = torch.cuda.get_device_properties(device_id).total_memory
            memory_reserved = torch.cuda.memory_reserved(device_id)
            return memory_total - memory_reserved
        except Exception as e:
            logger.error(f"Error getting available memory: {str(e)}")
            return 0
    
    def clear_cache(self) -> None:
        """Clear the hardware profile cache"""
        self._cached_profile = None
        self._cache_timestamp = None
        logger.info("Hardware profile cache cleared")


# Singleton instance
_hardware_service_instance = None


def get_hardware_service() -> HardwareService:
    """Get singleton instance of HardwareService"""
    global _hardware_service_instance
    if _hardware_service_instance is None:
        _hardware_service_instance = HardwareService()
    return _hardware_service_instance
