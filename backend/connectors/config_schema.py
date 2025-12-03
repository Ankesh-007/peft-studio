"""
Configuration schema for connectors.

Defines the structure and validation for connector configuration files.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator


class ConnectorCredentialSchema(BaseModel):
    """Schema for a single credential field."""
    key: str = Field(..., description="Credential key name")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Description of the credential")
    required: bool = Field(True, description="Whether this credential is required")
    secret: bool = Field(True, description="Whether this is a secret value")
    placeholder: Optional[str] = Field(None, description="Placeholder text for input")


class ConnectorFeatures(BaseModel):
    """Features supported by a connector."""
    training: bool = Field(False, description="Supports training jobs")
    inference: bool = Field(False, description="Supports inference")
    registry: bool = Field(False, description="Supports model registry")
    tracking: bool = Field(False, description="Supports experiment tracking")


class ConnectorConfig(BaseModel):
    """Configuration for a single connector."""
    name: str = Field(..., description="Unique connector identifier")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Connector description")
    enabled: bool = Field(True, description="Whether connector is enabled")
    credentials: List[ConnectorCredentialSchema] = Field(
        default_factory=list,
        description="Required credentials"
    )
    features: ConnectorFeatures = Field(
        default_factory=ConnectorFeatures,
        description="Supported features"
    )
    documentation_url: Optional[str] = Field(
        None,
        description="URL to connector documentation"
    )
    settings: Dict[str, any] = Field(
        default_factory=dict,
        description="Additional connector-specific settings"
    )
    
    @validator('name')
    def validate_name(cls, v):
        """Validate connector name format."""
        if not v or not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Connector name must be alphanumeric with underscores or hyphens")
        return v


class ConnectorsConfig(BaseModel):
    """Configuration for all connectors."""
    version: str = Field("1.0", description="Configuration version")
    connectors: Dict[str, ConnectorConfig] = Field(
        default_factory=dict,
        description="Connector configurations keyed by name"
    )
    
    def get_connector(self, name: str) -> Optional[ConnectorConfig]:
        """Get configuration for a specific connector."""
        return self.connectors.get(name)
    
    def add_connector(self, config: ConnectorConfig) -> None:
        """Add or update a connector configuration."""
        self.connectors[config.name] = config
    
    def remove_connector(self, name: str) -> bool:
        """Remove a connector configuration."""
        if name in self.connectors:
            del self.connectors[name]
            return True
        return False
    
    def list_enabled(self) -> List[ConnectorConfig]:
        """List all enabled connectors."""
        return [c for c in self.connectors.values() if c.enabled]
    
    def enable_connector(self, name: str) -> bool:
        """Enable a connector."""
        if name in self.connectors:
            self.connectors[name].enabled = True
            return True
        return False
    
    def disable_connector(self, name: str) -> bool:
        """Disable a connector."""
        if name in self.connectors:
            self.connectors[name].enabled = False
            return True
        return False


# Example configuration
EXAMPLE_CONFIG = {
    "version": "1.0",
    "connectors": {
        "runpod": {
            "name": "runpod",
            "display_name": "RunPod",
            "description": "Cloud GPU provider with on-demand and spot instances",
            "enabled": True,
            "credentials": [
                {
                    "key": "api_key",
                    "display_name": "API Key",
                    "description": "RunPod API key from your account settings",
                    "required": True,
                    "secret": True,
                    "placeholder": "Enter your RunPod API key"
                }
            ],
            "features": {
                "training": True,
                "inference": True,
                "registry": False,
                "tracking": False
            },
            "documentation_url": "https://docs.runpod.io/",
            "settings": {
                "default_region": "us-west",
                "timeout_seconds": 300
            }
        },
        "huggingface": {
            "name": "huggingface",
            "display_name": "HuggingFace Hub",
            "description": "Model registry and hosting platform",
            "enabled": True,
            "credentials": [
                {
                    "key": "token",
                    "display_name": "Access Token",
                    "description": "HuggingFace access token with write permissions",
                    "required": True,
                    "secret": True,
                    "placeholder": "hf_..."
                }
            ],
            "features": {
                "training": False,
                "inference": False,
                "registry": True,
                "tracking": False
            },
            "documentation_url": "https://huggingface.co/docs/hub/",
            "settings": {
                "default_visibility": "private"
            }
        }
    }
}
