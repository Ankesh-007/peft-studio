"""
Dependency Checker Service for verifying system dependencies.
"""

import sys
import subprocess
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# Lazy import torch to reduce startup memory usage
_torch = None


def _get_torch():
    """Lazy load torch module"""
    global _torch
    if _torch is None:
        try:
            import torch as _torch_module
            _torch = _torch_module
        except ImportError:
            _torch = None
    return _torch


@dataclass
class DependencyCheck:
    """Information about a single dependency check"""
    name: str
    required: bool
    installed: bool
    version: Optional[str] = None
    expected_version: Optional[str] = None
    error: Optional[str] = None
    fix_instructions: Optional[str] = None


@dataclass
class DependencyReport:
    """Complete dependency verification report"""
    all_passed: bool
    checks: List[DependencyCheck] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class DependencyChecker:
    """Service for checking system dependencies"""
    
    def __init__(self):
        logger.info("DependencyChecker initialized")
    
    def check_python_version(self) -> DependencyCheck:
        """
        Check if Python version meets requirements.
        
        Returns:
            DependencyCheck object for Python version
        """
        try:
            current_version = sys.version.split()[0]
            version_info = sys.version_info
            
            # Require Python 3.10+
            required_major = 3
            required_minor = 10
            
            is_compatible = (
                version_info.major > required_major or
                (version_info.major == required_major and version_info.minor >= required_minor)
            )
            
            check = DependencyCheck(
                name="Python",
                required=True,
                installed=True,
                version=current_version,
                expected_version=f"{required_major}.{required_minor}+",
                error=None if is_compatible else f"Python {required_major}.{required_minor}+ is required",
                fix_instructions=None if is_compatible else (
                    f"Please install Python {required_major}.{required_minor} or higher from https://www.python.org/downloads/"
                )
            )
            
            logger.info(f"Python version check: {current_version} (compatible: {is_compatible})")
            return check
            
        except Exception as e:
            logger.error(f"Error checking Python version: {str(e)}")
            return DependencyCheck(
                name="Python",
                required=True,
                installed=False,
                error=f"Failed to check Python version: {str(e)}",
                fix_instructions="Please ensure Python is properly installed"
            )
    
    def check_cuda_availability(self) -> DependencyCheck:
        """
        Check if CUDA is available for GPU acceleration.
        
        Returns:
            DependencyCheck object for CUDA
        """
        try:
            torch = _get_torch()
            
            if torch is None:
                return DependencyCheck(
                    name="CUDA",
                    required=False,
                    installed=False,
                    error="PyTorch not installed - cannot check CUDA",
                    fix_instructions="Install PyTorch first: pip install torch"
                )
            
            cuda_available = torch.cuda.is_available()
            cuda_version = torch.version.cuda if cuda_available else None
            device_count = torch.cuda.device_count() if cuda_available else 0
            
            if cuda_available:
                device_names = [
                    torch.cuda.get_device_name(i) 
                    for i in range(device_count)
                ]
                
                check = DependencyCheck(
                    name="CUDA",
                    required=False,
                    installed=True,
                    version=cuda_version,
                    error=None,
                    fix_instructions=None
                )
                
                logger.info(f"CUDA available: version {cuda_version}, {device_count} device(s): {device_names}")
            else:
                check = DependencyCheck(
                    name="CUDA",
                    required=False,
                    installed=False,
                    error="CUDA not available - GPU training will not work",
                    fix_instructions=(
                        "To enable GPU acceleration:\n"
                        "1. Install NVIDIA GPU drivers from https://www.nvidia.com/drivers\n"
                        "2. Install CUDA Toolkit from https://developer.nvidia.com/cuda-downloads\n"
                        "3. Install PyTorch with CUDA support: pip install torch --index-url https://download.pytorch.org/whl/cu118\n"
                        "Note: Training will work on CPU but will be significantly slower"
                    )
                )
                
                logger.warning("CUDA not available")
            
            return check
            
        except Exception as e:
            logger.error(f"Error checking CUDA availability: {str(e)}")
            return DependencyCheck(
                name="CUDA",
                required=False,
                installed=False,
                error=f"Failed to check CUDA: {str(e)}",
                fix_instructions="Please check your PyTorch installation"
            )
    
    def check_package_versions(self) -> List[DependencyCheck]:
        """
        Check if required Python packages are installed with correct versions.
        
        Returns:
            List of DependencyCheck objects for each package
        """
        checks = []
        
        # Define required packages with their expected versions
        required_packages = {
            "torch": {"min_version": "2.0.0", "required": True},
            "transformers": {"min_version": "4.30.0", "required": True},
            "peft": {"min_version": "0.4.0", "required": True},
            "datasets": {"min_version": "2.0.0", "required": True},
            "accelerate": {"min_version": "0.20.0", "required": True},
            "bitsandbytes": {"min_version": "0.40.0", "required": False},
            "scipy": {"min_version": "1.10.0", "required": True},
            "sentencepiece": {"min_version": "0.1.99", "required": True},
            "protobuf": {"min_version": "3.20.0", "required": True},
        }
        
        for package_name, requirements in required_packages.items():
            check = self._check_single_package(
                package_name,
                requirements["min_version"],
                requirements["required"]
            )
            checks.append(check)
        
        return checks
    
    def _check_single_package(
        self, 
        package_name: str, 
        min_version: str,
        required: bool
    ) -> DependencyCheck:
        """
        Check a single package installation and version.
        
        Args:
            package_name: Name of the package
            min_version: Minimum required version
            required: Whether the package is required
            
        Returns:
            DependencyCheck object
        """
        try:
            # Try to import the package
            if package_name == "torch":
                torch = _get_torch()
                if torch is None:
                    raise ImportError("torch not installed")
                installed_version = torch.__version__.split("+")[0]  # Remove +cu118 suffix
            else:
                module = __import__(package_name)
                installed_version = getattr(module, "__version__", "unknown")
            
            # Compare versions
            is_compatible = self._compare_versions(installed_version, min_version)
            
            if is_compatible:
                check = DependencyCheck(
                    name=package_name,
                    required=required,
                    installed=True,
                    version=installed_version,
                    expected_version=f"{min_version}+",
                    error=None,
                    fix_instructions=None
                )
                logger.info(f"Package {package_name} version {installed_version} is compatible")
            else:
                check = DependencyCheck(
                    name=package_name,
                    required=required,
                    installed=True,
                    version=installed_version,
                    expected_version=f"{min_version}+",
                    error=f"Version {installed_version} is below minimum {min_version}",
                    fix_instructions=f"Upgrade {package_name}: pip install --upgrade {package_name}>={min_version}"
                )
                logger.warning(f"Package {package_name} version {installed_version} is below minimum {min_version}")
            
            return check
            
        except ImportError:
            check = DependencyCheck(
                name=package_name,
                required=required,
                installed=False,
                expected_version=f"{min_version}+",
                error=f"Package {package_name} is not installed",
                fix_instructions=f"Install {package_name}: pip install {package_name}>={min_version}"
            )
            logger.warning(f"Package {package_name} is not installed")
            return check
            
        except Exception as e:
            logger.error(f"Error checking package {package_name}: {str(e)}")
            return DependencyCheck(
                name=package_name,
                required=required,
                installed=False,
                error=f"Failed to check {package_name}: {str(e)}",
                fix_instructions=f"Try reinstalling {package_name}: pip install --force-reinstall {package_name}"
            )
    
    def _compare_versions(self, installed: str, minimum: str) -> bool:
        """
        Compare version strings.
        
        Args:
            installed: Installed version string
            minimum: Minimum required version string
            
        Returns:
            True if installed >= minimum
        """
        try:
            # Handle "unknown" version
            if installed == "unknown":
                return True  # Assume compatible if we can't determine version
            
            # Parse version strings (handle x.y.z format)
            installed_parts = [int(x) for x in installed.split(".")[:3]]
            minimum_parts = [int(x) for x in minimum.split(".")[:3]]
            
            # Pad with zeros if needed
            while len(installed_parts) < 3:
                installed_parts.append(0)
            while len(minimum_parts) < 3:
                minimum_parts.append(0)
            
            # Compare
            return installed_parts >= minimum_parts
            
        except Exception as e:
            logger.warning(f"Error comparing versions {installed} and {minimum}: {str(e)}")
            return True  # Assume compatible on error
    
    def check_all(self) -> DependencyReport:
        """
        Run all dependency checks and generate a comprehensive report.
        
        Returns:
            DependencyReport with all check results
        """
        logger.info("Running comprehensive dependency check...")
        
        checks = []
        recommendations = []
        
        # Check Python version
        python_check = self.check_python_version()
        checks.append(python_check)
        
        # Check CUDA
        cuda_check = self.check_cuda_availability()
        checks.append(cuda_check)
        
        # Check packages
        package_checks = self.check_package_versions()
        checks.extend(package_checks)
        
        # Determine if all required checks passed
        all_passed = all(
            check.installed and check.error is None
            for check in checks
            if check.required
        )
        
        # Generate recommendations
        if not cuda_check.installed:
            recommendations.append(
                "GPU acceleration is not available. Training will be slower on CPU. "
                "Consider installing CUDA for better performance."
            )
        
        failed_required = [
            check for check in checks 
            if check.required and (not check.installed or check.error)
        ]
        
        if failed_required:
            recommendations.append(
                f"Critical dependencies missing: {', '.join(c.name for c in failed_required)}. "
                "Please install these before starting training."
            )
        
        failed_optional = [
            check for check in checks 
            if not check.required and (not check.installed or check.error)
        ]
        
        if failed_optional:
            recommendations.append(
                f"Optional dependencies missing: {', '.join(c.name for c in failed_optional)}. "
                "Some features may not be available."
            )
        
        report = DependencyReport(
            all_passed=all_passed,
            checks=checks,
            recommendations=recommendations,
            timestamp=datetime.now()
        )
        
        logger.info(f"Dependency check complete: all_passed={all_passed}, "
                   f"{len(checks)} checks, {len(recommendations)} recommendations")
        
        return report


# Singleton instance
_dependency_checker_instance = None


def get_dependency_checker() -> DependencyChecker:
    """Get singleton instance of DependencyChecker"""
    global _dependency_checker_instance
    if _dependency_checker_instance is None:
        _dependency_checker_instance = DependencyChecker()
    return _dependency_checker_instance
