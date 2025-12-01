"""
Settings API Endpoints

REST API for managing user settings and preferences.
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging

from services.settings_service import get_settings_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingUpdate(BaseModel):
    """Model for updating a single setting"""
    category: str = Field(..., description="Settings category")
    key: str = Field(..., description="Setting key")
    value: Any = Field(..., description="Setting value")


class CategoryUpdate(BaseModel):
    """Model for updating a category of settings"""
    category: str = Field(..., description="Settings category")
    values: Dict[str, Any] = Field(..., description="Settings values")


class SettingsImport(BaseModel):
    """Model for importing settings"""
    settings_json: str = Field(..., description="JSON string of settings")


@router.get("")
async def get_all_settings():
    """Get all settings"""
    try:
        service = get_settings_service()
        settings = service.get_all_settings()
        return {
            "success": True,
            "settings": settings
        }
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{category}")
async def get_category_settings(category: str):
    """Get settings for a specific category"""
    try:
        service = get_settings_service()
        settings = service.get_setting(category)
        
        if settings is None:
            raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
        
        return {
            "success": True,
            "category": category,
            "settings": settings
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting category settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{category}/{key}")
async def get_specific_setting(category: str, key: str):
    """Get a specific setting value"""
    try:
        service = get_settings_service()
        value = service.get_setting(category, key)
        
        if value is None:
            raise HTTPException(
                status_code=404,
                detail=f"Setting '{category}.{key}' not found"
            )
        
        return {
            "success": True,
            "category": category,
            "key": key,
            "value": value
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting specific setting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/setting")
async def update_setting(update: SettingUpdate):
    """Update a specific setting"""
    try:
        service = get_settings_service()
        settings = service.update_setting(
            update.category,
            update.key,
            update.value
        )
        
        return {
            "success": True,
            "message": f"Setting '{update.category}.{update.key}' updated",
            "settings": settings
        }
    except Exception as e:
        logger.error(f"Error updating setting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/category")
async def update_category(update: CategoryUpdate):
    """Update an entire category of settings"""
    try:
        service = get_settings_service()
        settings = service.update_category(update.category, update.values)
        
        return {
            "success": True,
            "message": f"Category '{update.category}' updated",
            "settings": settings
        }
    except Exception as e:
        logger.error(f"Error updating category: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_settings(category: Optional[str] = None):
    """Reset settings to defaults"""
    try:
        service = get_settings_service()
        settings = service.reset_to_defaults(category)
        
        message = "All settings reset to defaults" if category is None else f"Category '{category}' reset to defaults"
        
        return {
            "success": True,
            "message": message,
            "settings": settings
        }
    except Exception as e:
        logger.error(f"Error resetting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/json")
async def export_settings():
    """Export settings as JSON"""
    try:
        service = get_settings_service()
        settings_json = service.export_settings()
        
        return {
            "success": True,
            "settings_json": settings_json
        }
    except Exception as e:
        logger.error(f"Error exporting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_settings(import_data: SettingsImport):
    """Import settings from JSON"""
    try:
        service = get_settings_service()
        settings = service.import_settings(import_data.settings_json)
        
        return {
            "success": True,
            "message": "Settings imported successfully",
            "settings": settings
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error importing settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_settings(settings: Dict[str, Any] = Body(...)):
    """Validate settings structure and values"""
    try:
        service = get_settings_service()
        is_valid, error_message = service.validate_settings(settings)
        
        if not is_valid:
            return {
                "success": False,
                "valid": False,
                "error": error_message
            }
        
        return {
            "success": True,
            "valid": True,
            "message": "Settings are valid"
        }
    except Exception as e:
        logger.error(f"Error validating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cleanup/candidates")
async def get_cleanup_candidates():
    """Get files that can be cleaned up based on retention policies"""
    try:
        service = get_settings_service()
        candidates = service.get_cleanup_candidates()
        
        return {
            "success": True,
            "cleanup_candidates": candidates
        }
    except Exception as e:
        logger.error(f"Error getting cleanup candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))
