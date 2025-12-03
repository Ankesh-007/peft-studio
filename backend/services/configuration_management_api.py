"""
Configuration Management API
FastAPI endpoints for configuration import/export and library management
Validates: Requirements 18.1, 18.2, 18.3, 18.4, 18.5
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import tempfile
import os
import logging

from services.configuration_management_service import (
    get_configuration_management_service,
    ConfigurationMetadata,
)
from services.training_config_service import TrainingConfiguration

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/configurations", tags=["configurations"])


class ExportConfigurationRequest(BaseModel):
    """Request to export a configuration"""
    configuration: dict
    name: str
    description: str = ""
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    training_results: Optional[Dict] = None
    hardware_requirements: Optional[Dict] = None


class SaveConfigurationRequest(BaseModel):
    """Request to save a configuration to library"""
    configuration: dict
    name: str
    description: str = ""
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    training_results: Optional[Dict] = None
    hardware_requirements: Optional[Dict] = None


class UpdateMetadataRequest(BaseModel):
    """Request to update configuration metadata"""
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    training_results: Optional[Dict] = None
    hardware_requirements: Optional[Dict] = None


class ListConfigurationsRequest(BaseModel):
    """Request to list configurations with filters"""
    tags: Optional[List[str]] = None
    search_query: Optional[str] = None


@router.post("/export")
async def export_configuration(request: ExportConfigurationRequest):
    """
    Export a training configuration to JSON format.
    Requirement 18.1: Export configuration
    
    Args:
        request: Export configuration request
        
    Returns:
        Exported configuration data
    """
    try:
        service = get_configuration_management_service()
        
        # Convert dict to TrainingConfiguration
        config = TrainingConfiguration(**request.configuration)
        
        # Export configuration
        export_data = service.export_configuration(
            config=config,
            name=request.name,
            description=request.description,
            author=request.author,
            tags=request.tags,
            training_results=request.training_results,
            hardware_requirements=request.hardware_requirements
        )
        
        return {
            "success": True,
            "data": export_data
        }
    
    except Exception as e:
        logger.error(f"Error exporting configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_configuration(export_data: dict):
    """
    Import a training configuration from JSON format.
    Requirement 18.2: Import configuration with validation
    
    Args:
        export_data: Exported configuration data
        
    Returns:
        Imported configuration with metadata
    """
    try:
        service = get_configuration_management_service()
        
        # Import configuration
        saved_config = service.import_configuration(export_data)
        
        return {
            "success": True,
            "data": {
                "metadata": saved_config.metadata.__dict__,
                "configuration": saved_config.configuration.__dict__
            }
        }
    
    except ValueError as e:
        logger.error(f"Validation error importing configuration: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error importing configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/library/save")
async def save_to_library(request: SaveConfigurationRequest):
    """
    Save a configuration to the library.
    Requirement 18.3: Configuration library management
    
    Args:
        request: Save configuration request
        
    Returns:
        Configuration ID
    """
    try:
        service = get_configuration_management_service()
        
        # Convert dict to TrainingConfiguration
        config = TrainingConfiguration(**request.configuration)
        
        # Save to library
        config_id = service.save_to_library(
            config=config,
            name=request.name,
            description=request.description,
            author=request.author,
            tags=request.tags,
            training_results=request.training_results,
            hardware_requirements=request.hardware_requirements
        )
        
        return {
            "success": True,
            "config_id": config_id
        }
    
    except Exception as e:
        logger.error(f"Error saving configuration to library: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/library/{config_id}")
async def load_from_library(config_id: str):
    """
    Load a configuration from the library.
    Requirement 18.3: Configuration library management
    
    Args:
        config_id: Configuration ID
        
    Returns:
        Saved configuration with metadata
    """
    try:
        service = get_configuration_management_service()
        
        # Load from library
        saved_config = service.load_from_library(config_id)
        
        return {
            "success": True,
            "data": {
                "metadata": saved_config.metadata.__dict__,
                "configuration": saved_config.configuration.__dict__
            }
        }
    
    except FileNotFoundError as e:
        logger.error(f"Configuration not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error loading configuration from library: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/library/list")
async def list_library_configurations(request: ListConfigurationsRequest):
    """
    List all configurations in the library.
    Requirement 18.3: Configuration library browser
    
    Args:
        request: List configurations request with filters
        
    Returns:
        List of configuration metadata
    """
    try:
        service = get_configuration_management_service()
        
        # List configurations
        configurations = service.list_library_configurations(
            tags=request.tags,
            search_query=request.search_query
        )
        
        return {
            "success": True,
            "configurations": [config.__dict__ for config in configurations]
        }
    
    except Exception as e:
        logger.error(f"Error listing library configurations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/library/{config_id}")
async def delete_from_library(config_id: str):
    """
    Delete a configuration from the library.
    Requirement 18.3: Configuration library management
    
    Args:
        config_id: Configuration ID
        
    Returns:
        Success status
    """
    try:
        service = get_configuration_management_service()
        
        # Delete from library
        success = service.delete_from_library(config_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        return {
            "success": True,
            "message": "Configuration deleted successfully"
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error deleting configuration from library: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/library/{config_id}/metadata")
async def update_metadata(config_id: str, request: UpdateMetadataRequest):
    """
    Update metadata for a saved configuration.
    Requirement 18.5: Configuration versioning
    
    Args:
        config_id: Configuration ID
        request: Update metadata request
        
    Returns:
        Success status
    """
    try:
        service = get_configuration_management_service()
        
        # Update metadata
        success = service.update_metadata(
            config_id=config_id,
            name=request.name,
            description=request.description,
            tags=request.tags,
            training_results=request.training_results,
            hardware_requirements=request.hardware_requirements
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        return {
            "success": True,
            "message": "Metadata updated successfully"
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error updating configuration metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-file")
async def export_to_file(request: ExportConfigurationRequest):
    """
    Export configuration to a downloadable file.
    Requirement 18.4: Configuration sharing
    
    Args:
        request: Export configuration request
        
    Returns:
        File download response
    """
    try:
        service = get_configuration_management_service()
        
        # Convert dict to TrainingConfiguration
        config = TrainingConfiguration(**request.configuration)
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False
        )
        temp_path = temp_file.name
        temp_file.close()
        
        # Export to file
        service.export_to_file(
            config=config,
            file_path=temp_path,
            name=request.name,
            description=request.description,
            author=request.author,
            tags=request.tags,
            training_results=request.training_results,
            hardware_requirements=request.hardware_requirements
        )
        
        # Generate filename
        safe_name = "".join(c for c in request.name if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_name}.json" if safe_name else "configuration.json"
        
        return FileResponse(
            path=temp_path,
            filename=filename,
            media_type="application/json",
            background=lambda: os.unlink(temp_path)  # Clean up after sending
        )
    
    except Exception as e:
        logger.error(f"Error exporting configuration to file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-file")
async def import_from_file(file: UploadFile = File(...)):
    """
    Import configuration from an uploaded file.
    Requirement 18.4: Configuration sharing
    
    Args:
        file: Uploaded configuration file
        
    Returns:
        Imported configuration with metadata
    """
    try:
        service = get_configuration_management_service()
        
        # Save uploaded file temporarily
        temp_file = tempfile.NamedTemporaryFile(
            mode='wb',
            suffix='.json',
            delete=False
        )
        temp_path = temp_file.name
        
        # Write uploaded content
        content = await file.read()
        temp_file.write(content)
        temp_file.close()
        
        try:
            # Import from file
            saved_config = service.import_from_file(temp_path)
            
            return {
                "success": True,
                "data": {
                    "metadata": saved_config.metadata.__dict__,
                    "configuration": saved_config.configuration.__dict__
                }
            }
        
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
    
    except ValueError as e:
        logger.error(f"Validation error importing file: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error importing configuration from file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
