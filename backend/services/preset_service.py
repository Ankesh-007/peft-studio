"""
Configuration Preset Service

Handles saving, loading, importing, exporting, and managing training configuration presets.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ConfigurationPreset(BaseModel):
    """Complete training configuration preset"""
    id: str
    name: str
    description: str = ""
    created_at: str
    updated_at: str
    tags: List[str] = Field(default_factory=list)
    
    # Model configuration
    model_name: str
    model_path: str = ""
    
    # Dataset configuration
    dataset_id: str = ""
    dataset_path: str = ""
    
    # PEFT Settings
    peft_method: str = "lora"
    lora_r: int
    lora_alpha: int
    lora_dropout: float
    target_modules: List[str]
    
    # Training Hyperparameters
    learning_rate: float
    batch_size: int
    gradient_accumulation: int
    epochs: int
    max_steps: int = 0
    warmup_steps: int = 0
    
    # Optimization
    optimizer: str = "adamw"
    scheduler: str = "linear"
    weight_decay: float = 0.0
    max_grad_norm: float = 1.0
    
    # Precision
    precision: str = "fp16"
    quantization: Optional[str] = None
    
    # Checkpointing
    save_steps: int = 500
    save_total: int = 3
    
    # Validation
    eval_steps: int = 500
    eval_strategy: str = "steps"
    
    @field_validator('peft_method')
    @classmethod
    def validate_peft_method(cls, v):
        allowed = ['lora', 'qlora', 'prefix-tuning']
        if v not in allowed:
            raise ValueError(f"peft_method must be one of {allowed}")
        return v
    
    @field_validator('optimizer')
    @classmethod
    def validate_optimizer(cls, v):
        allowed = ['adamw', 'sgd']
        if v not in allowed:
            raise ValueError(f"optimizer must be one of {allowed}")
        return v
    
    @field_validator('scheduler')
    @classmethod
    def validate_scheduler(cls, v):
        allowed = ['linear', 'cosine', 'constant']
        if v not in allowed:
            raise ValueError(f"scheduler must be one of {allowed}")
        return v
    
    @field_validator('precision')
    @classmethod
    def validate_precision(cls, v):
        allowed = ['fp32', 'fp16', 'bf16']
        if v not in allowed:
            raise ValueError(f"precision must be one of {allowed}")
        return v
    
    @field_validator('eval_strategy')
    @classmethod
    def validate_eval_strategy(cls, v):
        allowed = ['steps', 'epoch']
        if v not in allowed:
            raise ValueError(f"eval_strategy must be one of {allowed}")
        return v


class PresetService:
    """Service for managing configuration presets"""
    
    def __init__(self, presets_dir: str = "presets"):
        """Initialize preset service with storage directory"""
        self.presets_dir = Path(presets_dir)
        self.presets_dir.mkdir(parents=True, exist_ok=True)
    
    def save_preset(self, preset: ConfigurationPreset) -> ConfigurationPreset:
        """
        Save a configuration preset to disk
        
        Args:
            preset: Configuration preset to save
            
        Returns:
            Saved preset with updated timestamp
        """
        preset.updated_at = datetime.utcnow().isoformat()
        
        preset_path = self.presets_dir / f"{preset.id}.json"
        with open(preset_path, 'w') as f:
            json.dump(preset.dict(), f, indent=2)
        
        return preset
    
    def load_preset(self, preset_id: str) -> Optional[ConfigurationPreset]:
        """
        Load a configuration preset from disk
        
        Args:
            preset_id: ID of preset to load
            
        Returns:
            Loaded preset or None if not found
        """
        preset_path = self.presets_dir / f"{preset_id}.json"
        
        if not preset_path.exists():
            return None
        
        with open(preset_path, 'r') as f:
            data = json.load(f)
        
        return ConfigurationPreset(**data)
    
    def list_presets(
        self, 
        search: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[ConfigurationPreset]:
        """
        List all presets with optional filtering
        
        Args:
            search: Optional search term for name/description
            tags: Optional list of tags to filter by
            
        Returns:
            List of matching presets
        """
        presets = []
        
        for preset_file in self.presets_dir.glob("*.json"):
            try:
                with open(preset_file, 'r') as f:
                    data = json.load(f)
                preset = ConfigurationPreset(**data)
                
                # Apply search filter
                if search:
                    search_lower = search.lower()
                    if (search_lower not in preset.name.lower() and 
                        search_lower not in preset.description.lower()):
                        continue
                
                # Apply tag filter
                if tags:
                    if not any(tag in preset.tags for tag in tags):
                        continue
                
                presets.append(preset)
            except Exception as e:
                print(f"Error loading preset {preset_file}: {e}")
                continue
        
        # Sort by updated_at descending
        presets.sort(key=lambda p: p.updated_at, reverse=True)
        
        return presets
    
    def delete_preset(self, preset_id: str) -> bool:
        """
        Delete a configuration preset
        
        Args:
            preset_id: ID of preset to delete
            
        Returns:
            True if deleted, False if not found
        """
        preset_path = self.presets_dir / f"{preset_id}.json"
        
        if not preset_path.exists():
            return False
        
        preset_path.unlink()
        return True
    
    def export_preset(self, preset_id: str) -> Optional[Dict[str, Any]]:
        """
        Export a preset to a shareable JSON format
        
        Args:
            preset_id: ID of preset to export
            
        Returns:
            Preset data as dictionary or None if not found
        """
        preset = self.load_preset(preset_id)
        
        if not preset:
            return None
        
        # Create export format with metadata
        export_data = {
            "format_version": "1.0",
            "export_date": datetime.utcnow().isoformat(),
            "preset": preset.dict()
        }
        
        return export_data
    
    def import_preset(
        self, 
        import_data: Dict[str, Any],
        new_id: Optional[str] = None
    ) -> ConfigurationPreset:
        """
        Import a preset from JSON data with validation
        
        Args:
            import_data: Imported preset data
            new_id: Optional new ID for imported preset
            
        Returns:
            Imported and saved preset
            
        Raises:
            ValueError: If import data is invalid
        """
        # Validate format
        if "preset" not in import_data:
            raise ValueError("Invalid import format: missing 'preset' field")
        
        preset_data = import_data["preset"]
        
        # Assign new ID if provided
        if new_id:
            preset_data["id"] = new_id
        
        # Update timestamps
        preset_data["created_at"] = datetime.utcnow().isoformat()
        preset_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Validate and create preset
        preset = ConfigurationPreset(**preset_data)
        
        # Save to disk
        return self.save_preset(preset)
    
    def update_preset(
        self, 
        preset_id: str, 
        updates: Dict[str, Any]
    ) -> Optional[ConfigurationPreset]:
        """
        Update an existing preset
        
        Args:
            preset_id: ID of preset to update
            updates: Dictionary of fields to update
            
        Returns:
            Updated preset or None if not found
        """
        preset = self.load_preset(preset_id)
        
        if not preset:
            return None
        
        # Update fields
        preset_dict = preset.dict()
        preset_dict.update(updates)
        preset_dict["updated_at"] = datetime.utcnow().isoformat()
        
        # Validate and save
        updated_preset = ConfigurationPreset(**preset_dict)
        return self.save_preset(updated_preset)


# Global service instance
_preset_service: Optional[PresetService] = None


def get_preset_service() -> PresetService:
    """Get or create the global preset service instance"""
    global _preset_service
    if _preset_service is None:
        _preset_service = PresetService()
    return _preset_service
