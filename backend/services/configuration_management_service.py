"""
Configuration Management Service
Handles export, import, and library management of training configurations
Validates: Requirements 18.1, 18.2, 18.3, 18.4, 18.5
"""

import json
import os
import hashlib
from typing import Dict, List, Optional
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
import logging

from services.training_config_service import (
    TrainingConfiguration,
    PEFTAlgorithm,
    QuantizationType,
    ComputeProvider,
    ExperimentTracker,
)

logger = logging.getLogger(__name__)


@dataclass
class ConfigurationMetadata:
    """Metadata for a saved configuration"""
    id: str
    name: str
    description: str
    created_at: str
    modified_at: str
    author: Optional[str] = None
    tags: List[str] = None
    training_results: Optional[Dict] = None
    hardware_requirements: Optional[Dict] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class SavedConfiguration:
    """Complete saved configuration with metadata"""
    metadata: ConfigurationMetadata
    configuration: TrainingConfiguration


class ConfigurationManagementService:
    """Service for managing configuration import/export and library"""
    
    def __init__(self, library_path: Optional[str] = None):
        """
        Initialize configuration management service.
        
        Args:
            library_path: Path to configuration library directory
        """
        self.logger = logging.getLogger(__name__)
        
        # Set up library path
        if library_path is None:
            home = Path.home()
            library_path = home / ".peft-studio" / "config" / "library"
        
        self.library_path = Path(library_path)
        self.library_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Configuration library initialized at: {self.library_path}")
    
    def export_configuration(
        self, 
        config: TrainingConfiguration,
        name: str,
        description: str = "",
        author: Optional[str] = None,
        tags: Optional[List[str]] = None,
        training_results: Optional[Dict] = None,
        hardware_requirements: Optional[Dict] = None
    ) -> dict:
        """
        Export a training configuration to dictionary format.
        Requirement 18.1: Export configuration with metadata
        
        Args:
            config: Training configuration to export
            name: Name for the configuration
            description: Description of the configuration
            author: Author name (optional)
            tags: List of tags for categorization (optional)
            training_results: Results from training with this config (optional)
            hardware_requirements: Hardware requirements (optional)
            
        Returns:
            Dictionary representation of the configuration with metadata
        """
        # Convert dataclass to dictionary
        config_dict = asdict(config)
        
        # Convert enums to their string values for JSON serialization
        config_dict['provider'] = config.provider.value
        config_dict['algorithm'] = config.algorithm.value
        config_dict['quantization'] = config.quantization.value
        config_dict['experiment_tracker'] = config.experiment_tracker.value
        
        # Generate unique ID
        config_id = self._generate_config_id(config_dict, name)
        
        # Create metadata
        now = datetime.utcnow().isoformat()
        metadata = {
            "id": config_id,
            "name": name,
            "description": description,
            "created_at": now,
            "modified_at": now,
            "author": author,
            "tags": tags or [],
            "training_results": training_results,
            "hardware_requirements": hardware_requirements,
        }
        
        # Create export data
        export_data = {
            "format_version": "1.0",
            "config_type": "training_configuration",
            "metadata": metadata,
            "configuration": config_dict
        }
        
        self.logger.info(f"Exported configuration: {name} (ID: {config_id})")
        return export_data
    
    def import_configuration(self, export_data: dict) -> SavedConfiguration:
        """
        Import a training configuration from exported dictionary format.
        Requirement 18.2: Import configuration with validation
        
        Args:
            export_data: Exported configuration data
            
        Returns:
            SavedConfiguration with metadata and configuration
            
        Raises:
            ValueError: If import data is invalid
        """
        # Validate format
        if "configuration" not in export_data:
            raise ValueError("Invalid export format: missing 'configuration' field")
        
        if "metadata" not in export_data:
            raise ValueError("Invalid export format: missing 'metadata' field")
        
        # Validate format version
        format_version = export_data.get("format_version", "unknown")
        if format_version != "1.0":
            self.logger.warning(f"Importing configuration with version {format_version}, expected 1.0")
        
        # Parse metadata
        metadata_dict = export_data["metadata"]
        metadata = ConfigurationMetadata(**metadata_dict)
        
        # Parse configuration
        config_dict = export_data["configuration"]
        
        # Convert string values back to enums
        config_dict['provider'] = ComputeProvider(config_dict['provider'])
        config_dict['algorithm'] = PEFTAlgorithm(config_dict['algorithm'])
        config_dict['quantization'] = QuantizationType(config_dict['quantization'])
        config_dict['experiment_tracker'] = ExperimentTracker(config_dict['experiment_tracker'])
        
        # Reconstruct configuration
        config = TrainingConfiguration(**config_dict)
        
        self.logger.info(f"Imported configuration: {metadata.name} (ID: {metadata.id})")
        
        return SavedConfiguration(metadata=metadata, configuration=config)
    
    def save_to_library(
        self,
        config: TrainingConfiguration,
        name: str,
        description: str = "",
        author: Optional[str] = None,
        tags: Optional[List[str]] = None,
        training_results: Optional[Dict] = None,
        hardware_requirements: Optional[Dict] = None
    ) -> str:
        """
        Save a configuration to the library.
        Requirement 18.3: Configuration library management
        
        Args:
            config: Training configuration to save
            name: Name for the configuration
            description: Description
            author: Author name
            tags: Tags for categorization
            training_results: Training results
            hardware_requirements: Hardware requirements
            
        Returns:
            Configuration ID
        """
        # Export configuration
        export_data = self.export_configuration(
            config=config,
            name=name,
            description=description,
            author=author,
            tags=tags,
            training_results=training_results,
            hardware_requirements=hardware_requirements
        )
        
        # Save to file
        config_id = export_data["metadata"]["id"]
        file_path = self.library_path / f"{config_id}.json"
        
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Saved configuration to library: {name} at {file_path}")
        return config_id
    
    def load_from_library(self, config_id: str) -> SavedConfiguration:
        """
        Load a configuration from the library.
        Requirement 18.3: Configuration library management
        
        Args:
            config_id: Configuration ID
            
        Returns:
            SavedConfiguration
            
        Raises:
            FileNotFoundError: If configuration not found
        """
        file_path = self.library_path / f"{config_id}.json"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration not found: {config_id}")
        
        with open(file_path, 'r') as f:
            export_data = json.load(f)
        
        return self.import_configuration(export_data)
    
    def list_library_configurations(
        self,
        tags: Optional[List[str]] = None,
        search_query: Optional[str] = None
    ) -> List[ConfigurationMetadata]:
        """
        List all configurations in the library.
        Requirement 18.3: Configuration library browser
        
        Args:
            tags: Filter by tags (optional)
            search_query: Search in name and description (optional)
            
        Returns:
            List of configuration metadata
        """
        configurations = []
        
        for file_path in self.library_path.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    export_data = json.load(f)
                
                metadata_dict = export_data.get("metadata", {})
                metadata = ConfigurationMetadata(**metadata_dict)
                
                # Apply filters
                if tags:
                    if not any(tag in metadata.tags for tag in tags):
                        continue
                
                if search_query:
                    query_lower = search_query.lower()
                    if (query_lower not in metadata.name.lower() and 
                        query_lower not in metadata.description.lower()):
                        continue
                
                configurations.append(metadata)
            
            except Exception as e:
                self.logger.error(f"Error loading configuration from {file_path}: {e}")
                continue
        
        # Sort by modified date (newest first)
        configurations.sort(key=lambda x: x.modified_at, reverse=True)
        
        return configurations
    
    def delete_from_library(self, config_id: str) -> bool:
        """
        Delete a configuration from the library.
        Requirement 18.3: Configuration library management
        
        Args:
            config_id: Configuration ID
            
        Returns:
            True if deleted successfully
        """
        file_path = self.library_path / f"{config_id}.json"
        
        if not file_path.exists():
            return False
        
        file_path.unlink()
        self.logger.info(f"Deleted configuration from library: {config_id}")
        return True
    
    def export_to_file(
        self,
        config: TrainingConfiguration,
        file_path: str,
        name: str,
        description: str = "",
        author: Optional[str] = None,
        tags: Optional[List[str]] = None,
        training_results: Optional[Dict] = None,
        hardware_requirements: Optional[Dict] = None
    ) -> str:
        """
        Export configuration to a file.
        Requirement 18.4: Configuration sharing
        
        Args:
            config: Training configuration
            file_path: Path to save the file
            name: Configuration name
            description: Description
            author: Author name
            tags: Tags
            training_results: Training results
            hardware_requirements: Hardware requirements
            
        Returns:
            Path to the saved file
        """
        export_data = self.export_configuration(
            config=config,
            name=name,
            description=description,
            author=author,
            tags=tags,
            training_results=training_results,
            hardware_requirements=hardware_requirements
        )
        
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Exported configuration to file: {file_path}")
        return file_path
    
    def import_from_file(self, file_path: str) -> SavedConfiguration:
        """
        Import configuration from a file.
        Requirement 18.4: Configuration sharing
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            SavedConfiguration
            
        Raises:
            FileNotFoundError: If file not found
            ValueError: If file format is invalid
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            export_data = json.load(f)
        
        return self.import_configuration(export_data)
    
    def update_metadata(
        self,
        config_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        training_results: Optional[Dict] = None,
        hardware_requirements: Optional[Dict] = None
    ) -> bool:
        """
        Update metadata for a saved configuration.
        Requirement 18.5: Configuration versioning
        
        Args:
            config_id: Configuration ID
            name: New name (optional)
            description: New description (optional)
            tags: New tags (optional)
            training_results: New training results (optional)
            hardware_requirements: New hardware requirements (optional)
            
        Returns:
            True if updated successfully
        """
        file_path = self.library_path / f"{config_id}.json"
        
        if not file_path.exists():
            return False
        
        # Load existing configuration
        with open(file_path, 'r') as f:
            export_data = json.load(f)
        
        # Update metadata
        metadata = export_data["metadata"]
        
        if name is not None:
            metadata["name"] = name
        if description is not None:
            metadata["description"] = description
        if tags is not None:
            metadata["tags"] = tags
        if training_results is not None:
            metadata["training_results"] = training_results
        if hardware_requirements is not None:
            metadata["hardware_requirements"] = hardware_requirements
        
        # Update modified timestamp
        metadata["modified_at"] = datetime.utcnow().isoformat()
        
        # Save updated configuration
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Updated metadata for configuration: {config_id}")
        return True
    
    def _generate_config_id(self, config_dict: dict, name: str) -> str:
        """Generate a unique ID for a configuration"""
        # Create a hash from configuration and name
        config_str = json.dumps(config_dict, sort_keys=True)
        hash_input = f"{name}:{config_str}".encode('utf-8')
        config_hash = hashlib.sha256(hash_input).hexdigest()[:16]
        
        # Add timestamp for uniqueness
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        
        return f"config_{timestamp}_{config_hash}"


# Singleton instance
_config_management_service_instance = None


def get_configuration_management_service() -> ConfigurationManagementService:
    """Get singleton instance of ConfigurationManagementService"""
    global _config_management_service_instance
    if _config_management_service_instance is None:
        _config_management_service_instance = ConfigurationManagementService()
    return _config_management_service_instance
