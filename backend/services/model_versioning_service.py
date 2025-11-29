"""
Model Versioning Service for tracking and managing model versions.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import json
import shutil
import logging
import semver

logger = logging.getLogger(__name__)


@dataclass
class ModelVersion:
    """Represents a versioned model with metadata"""
    id: str
    model_name: str
    version: str  # semantic versioning: v1.0.0
    timestamp: str
    config: Dict[str, Any]
    metrics: Dict[str, float]
    checkpoint_path: str
    size_bytes: int
    parent_version: Optional[str] = None


@dataclass
class VersionComparison:
    """Comparison between two model versions"""
    version1: ModelVersion
    version2: ModelVersion
    config_diff: Dict[str, Any]
    metric_diff: Dict[str, float]
    performance_improvement: float


@dataclass
class DiskSpaceInfo:
    """Information about disk space usage"""
    total_bytes: int
    used_bytes: int
    available_bytes: int
    percent_used: float
    versions_total_size: int
    low_space_threshold: int = 5 * 1024 * 1024 * 1024  # 5GB


class ModelVersioningService:
    """Service for managing model versions with semantic versioning"""
    
    def __init__(self, base_path: str = "./models"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.versions_file = self.base_path / "versions.json"
        self._versions: Dict[str, List[ModelVersion]] = {}
        self._load_versions()
        logger.info(f"ModelVersioningService initialized at {self.base_path}")
    
    def create_version(
        self,
        model_name: str,
        checkpoint_path: str,
        config: Dict[str, Any],
        metrics: Dict[str, float],
        parent_version: Optional[str] = None
    ) -> ModelVersion:
        """
        Create a new model version with automatic version number assignment.
        
        Args:
            model_name: Name of the model
            checkpoint_path: Path to the checkpoint file
            config: Training configuration
            metrics: Final training metrics
            parent_version: Optional parent version for tracking lineage
            
        Returns:
            ModelVersion object
        """
        # Get next version number
        version_number = self._get_next_version(model_name, parent_version)
        
        # Generate unique ID
        version_id = f"{model_name}_{version_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Copy checkpoint to versioned location
        checkpoint_src = Path(checkpoint_path)
        checkpoint_dest = self.base_path / model_name / version_number / "checkpoint"
        checkpoint_dest.mkdir(parents=True, exist_ok=True)
        
        # Copy checkpoint files
        if checkpoint_src.is_file():
            shutil.copy2(checkpoint_src, checkpoint_dest / checkpoint_src.name)
            size_bytes = checkpoint_src.stat().st_size
        elif checkpoint_src.is_dir():
            shutil.copytree(checkpoint_src, checkpoint_dest, dirs_exist_ok=True)
            size_bytes = sum(f.stat().st_size for f in checkpoint_dest.rglob('*') if f.is_file())
        else:
            raise ValueError(f"Checkpoint path does not exist: {checkpoint_path}")
        
        # Create version object
        version = ModelVersion(
            id=version_id,
            model_name=model_name,
            version=version_number,
            timestamp=datetime.now().isoformat(),
            config=config,
            metrics=metrics,
            checkpoint_path=str(checkpoint_dest),
            size_bytes=size_bytes,
            parent_version=parent_version
        )
        
        # Store version
        if model_name not in self._versions:
            self._versions[model_name] = []
        self._versions[model_name].append(version)
        self._save_versions()
        
        logger.info(f"Created version {version_number} for model {model_name}")
        return version
    
    def list_versions(self, model_name: str) -> List[ModelVersion]:
        """
        List all versions for a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            List of ModelVersion objects sorted by timestamp (newest first)
        """
        versions = self._versions.get(model_name, [])
        return sorted(versions, key=lambda v: v.timestamp, reverse=True)
    
    def get_version(self, model_name: str, version: str) -> Optional[ModelVersion]:
        """
        Get a specific version of a model.
        
        Args:
            model_name: Name of the model
            version: Version string (e.g., "v1.0.0")
            
        Returns:
            ModelVersion object or None if not found
        """
        versions = self._versions.get(model_name, [])
        for v in versions:
            if v.version == version:
                return v
        return None
    
    def get_latest_version(self, model_name: str) -> Optional[ModelVersion]:
        """
        Get the latest version of a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            ModelVersion object or None if no versions exist
        """
        versions = self.list_versions(model_name)
        return versions[0] if versions else None
    
    def compare_versions(
        self,
        model_name: str,
        version1: str,
        version2: str
    ) -> Optional[VersionComparison]:
        """
        Compare two versions of a model.
        
        Args:
            model_name: Name of the model
            version1: First version string
            version2: Second version string
            
        Returns:
            VersionComparison object or None if versions not found
        """
        v1 = self.get_version(model_name, version1)
        v2 = self.get_version(model_name, version2)
        
        if not v1 or not v2:
            return None
        
        # Calculate config differences
        config_diff = self._calculate_config_diff(v1.config, v2.config)
        
        # Calculate metric differences
        metric_diff = {}
        all_metrics = set(v1.metrics.keys()) | set(v2.metrics.keys())
        for metric in all_metrics:
            val1 = v1.metrics.get(metric, 0)
            val2 = v2.metrics.get(metric, 0)
            metric_diff[metric] = val2 - val1
        
        # Calculate overall performance improvement (based on loss reduction)
        loss1 = v1.metrics.get('final_loss', float('inf'))
        loss2 = v2.metrics.get('final_loss', float('inf'))
        performance_improvement = ((loss1 - loss2) / loss1 * 100) if loss1 > 0 else 0
        
        return VersionComparison(
            version1=v1,
            version2=v2,
            config_diff=config_diff,
            metric_diff=metric_diff,
            performance_improvement=performance_improvement
        )
    
    def delete_version(self, model_name: str, version: str) -> bool:
        """
        Delete a specific version.
        
        Args:
            model_name: Name of the model
            version: Version string
            
        Returns:
            True if deleted successfully, False otherwise
        """
        versions = self._versions.get(model_name, [])
        version_obj = None
        
        for i, v in enumerate(versions):
            if v.version == version:
                version_obj = v
                versions.pop(i)
                break
        
        if not version_obj:
            return False
        
        # Delete checkpoint files
        checkpoint_path = Path(version_obj.checkpoint_path)
        if checkpoint_path.exists():
            if checkpoint_path.is_dir():
                shutil.rmtree(checkpoint_path)
            else:
                checkpoint_path.unlink()
        
        self._save_versions()
        logger.info(f"Deleted version {version} for model {model_name}")
        return True
    
    def get_disk_space_info(self) -> DiskSpaceInfo:
        """
        Get disk space information including version storage usage.
        
        Returns:
            DiskSpaceInfo object
        """
        # Get disk usage
        stat = shutil.disk_usage(self.base_path)
        
        # Calculate total size of all versions
        versions_total_size = 0
        for versions_list in self._versions.values():
            for version in versions_list:
                versions_total_size += version.size_bytes
        
        return DiskSpaceInfo(
            total_bytes=stat.total,
            used_bytes=stat.used,
            available_bytes=stat.free,
            percent_used=(stat.used / stat.total * 100) if stat.total > 0 else 0,
            versions_total_size=versions_total_size
        )
    
    def should_prompt_cleanup(self) -> bool:
        """
        Check if disk space is low and cleanup should be prompted.
        
        Returns:
            True if cleanup should be prompted, False otherwise
        """
        disk_info = self.get_disk_space_info()
        return disk_info.available_bytes < disk_info.low_space_threshold
    
    def get_cleanup_candidates(
        self,
        model_name: Optional[str] = None,
        keep_latest: int = 3
    ) -> List[ModelVersion]:
        """
        Get versions that can be cleaned up (older versions beyond keep_latest).
        
        Args:
            model_name: Optional model name to filter by
            keep_latest: Number of latest versions to keep
            
        Returns:
            List of ModelVersion objects that can be deleted
        """
        candidates = []
        
        models_to_check = [model_name] if model_name else list(self._versions.keys())
        
        for model in models_to_check:
            versions = self.list_versions(model)
            if len(versions) > keep_latest:
                # Add older versions beyond keep_latest
                candidates.extend(versions[keep_latest:])
        
        return candidates
    
    def archive_versions(
        self,
        versions_to_archive: List[ModelVersion],
        archive_path: Optional[str] = None
    ) -> bool:
        """
        Archive old versions to free up space.
        
        Args:
            versions_to_archive: List of versions to archive
            archive_path: Optional custom archive path
            
        Returns:
            True if archived successfully, False otherwise
        """
        if not archive_path:
            archive_path = str(self.base_path / "archive")
        
        archive_dir = Path(archive_path)
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            for version in versions_to_archive:
                # Move checkpoint to archive
                src = Path(version.checkpoint_path)
                dest = archive_dir / version.model_name / version.version
                
                if src.exists():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dest))
                    
                    # Update checkpoint path
                    version.checkpoint_path = str(dest)
            
            self._save_versions()
            logger.info(f"Archived {len(versions_to_archive)} versions")
            return True
            
        except Exception as e:
            logger.error(f"Error archiving versions: {str(e)}")
            return False
    
    def _get_next_version(self, model_name: str, parent_version: Optional[str]) -> str:
        """
        Calculate the next semantic version number.
        
        Args:
            model_name: Name of the model
            parent_version: Optional parent version
            
        Returns:
            Next version string (e.g., "v1.0.0")
        """
        versions = self._versions.get(model_name, [])
        
        if not versions:
            return "v1.0.0"
        
        # Get all version numbers
        version_numbers = []
        for v in versions:
            try:
                # Remove 'v' prefix and parse
                ver = semver.VersionInfo.parse(v.version.lstrip('v'))
                version_numbers.append(ver)
            except:
                continue
        
        if not version_numbers:
            return "v1.0.0"
        
        # Get the latest version
        latest = max(version_numbers)
        
        # Increment minor version
        next_version = latest.bump_minor()
        
        return f"v{next_version}"
    
    def _calculate_config_diff(self, config1: Dict, config2: Dict) -> Dict[str, Any]:
        """Calculate differences between two configurations"""
        diff = {}
        all_keys = set(config1.keys()) | set(config2.keys())
        
        for key in all_keys:
            val1 = config1.get(key)
            val2 = config2.get(key)
            
            if val1 != val2:
                diff[key] = {
                    'old': val1,
                    'new': val2
                }
        
        return diff
    
    def _load_versions(self) -> None:
        """Load versions from disk"""
        if self.versions_file.exists():
            try:
                with open(self.versions_file, 'r') as f:
                    data = json.load(f)
                    
                # Convert to ModelVersion objects
                for model_name, versions_data in data.items():
                    self._versions[model_name] = [
                        ModelVersion(**v) for v in versions_data
                    ]
                    
                logger.info(f"Loaded {sum(len(v) for v in self._versions.values())} versions")
            except Exception as e:
                logger.error(f"Error loading versions: {str(e)}")
                self._versions = {}
        else:
            self._versions = {}
    
    def _save_versions(self) -> None:
        """Save versions to disk"""
        try:
            data = {}
            for model_name, versions in self._versions.items():
                data[model_name] = [asdict(v) for v in versions]
            
            with open(self.versions_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.debug("Saved versions to disk")
        except Exception as e:
            logger.error(f"Error saving versions: {str(e)}")


# Singleton instance
_model_versioning_service_instance = None


def get_model_versioning_service() -> ModelVersioningService:
    """Get singleton instance of ModelVersioningService"""
    global _model_versioning_service_instance
    if _model_versioning_service_instance is None:
        _model_versioning_service_instance = ModelVersioningService()
    return _model_versioning_service_instance
