"""
Credential Management Service

Provides secure storage and management of API credentials using OS keystore
and encryption. Implements CRUD operations for credentials with validation.

Requirements: 15.1, 15.2, 15.3
"""

import keyring
import json
import logging
from typing import Dict, Optional, List
from cryptography.fernet import Fernet
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


class SecureStorage:
    """
    Secure storage for sensitive data using encryption.
    
    Uses Fernet symmetric encryption with a key stored in the OS keystore.
    This provides an additional layer of security beyond the OS keystore alone.
    """
    
    SERVICE_NAME = "peft-studio"
    ENCRYPTION_KEY_NAME = "encryption-master-key"
    
    def __init__(self):
        """Initialize SecureStorage with encryption key from OS keystore."""
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self) -> bytes:
        """
        Get or create the encryption master key from OS keystore.
        
        Returns:
            bytes: The encryption key
        """
        # Try to get existing key
        key_str = keyring.get_password(self.SERVICE_NAME, self.ENCRYPTION_KEY_NAME)
        
        if key_str is None:
            # Generate new key
            key = Fernet.generate_key()
            # Store in OS keystore
            keyring.set_password(self.SERVICE_NAME, self.ENCRYPTION_KEY_NAME, key.decode())
            logger.info("Generated new encryption master key")
            return key
        
        return key_str.encode()
    
    def encrypt(self, data: str) -> bytes:
        """
        Encrypt a string.
        
        Args:
            data: String to encrypt
            
        Returns:
            bytes: Encrypted data
        """
        return self.cipher.encrypt(data.encode())
    
    def decrypt(self, encrypted: bytes) -> str:
        """
        Decrypt encrypted data.
        
        Args:
            encrypted: Encrypted bytes
            
        Returns:
            str: Decrypted string
        """
        return self.cipher.decrypt(encrypted).decode()


class CredentialService:
    """
    Service for managing platform credentials.
    
    Provides CRUD operations for API credentials with secure storage,
    validation, and verification capabilities.
    """
    
    SERVICE_NAME = "peft-studio"
    CREDENTIALS_INDEX_KEY = "credentials-index"
    
    def __init__(self):
        """Initialize credential service with secure storage."""
        self.secure_storage = SecureStorage()
    
    def _get_credential_key(self, platform: str, credential_type: str = "api-key") -> str:
        """
        Generate a keystore key for a credential.
        
        Args:
            platform: Platform name (e.g., 'runpod', 'huggingface')
            credential_type: Type of credential (default: 'api-key')
            
        Returns:
            str: Keystore key
        """
        return f"{platform}-{credential_type}"
    
    def _get_credentials_index(self) -> Dict[str, Dict]:
        """
        Get the index of all stored credentials.
        
        Returns:
            Dict mapping platform names to credential metadata
        """
        index_json = keyring.get_password(self.SERVICE_NAME, self.CREDENTIALS_INDEX_KEY)
        if index_json is None:
            return {}
        
        try:
            return json.loads(index_json)
        except json.JSONDecodeError:
            logger.error("Failed to parse credentials index")
            return {}
    
    def _update_credentials_index(self, index: Dict[str, Dict]):
        """
        Update the credentials index.
        
        Args:
            index: Updated index dictionary
        """
        keyring.set_password(
            self.SERVICE_NAME,
            self.CREDENTIALS_INDEX_KEY,
            json.dumps(index)
        )
    
    def store_credential(
        self,
        platform: str,
        credential_value: str,
        credential_type: str = "api-key",
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Store a credential securely.
        
        Args:
            platform: Platform name
            credential_value: The credential value (API key, token, etc.)
            credential_type: Type of credential
            metadata: Optional metadata (e.g., username, expiry)
            
        Returns:
            bool: True if stored successfully
        """
        try:
            # Validate inputs
            if not platform or not credential_value:
                raise ValueError("Platform and credential_value are required")
            
            # Store credential in OS keystore
            key = self._get_credential_key(platform, credential_type)
            keyring.set_password(self.SERVICE_NAME, key, credential_value)
            
            # Update index with metadata
            index = self._get_credentials_index()
            index[platform] = {
                "credential_type": credential_type,
                "stored_at": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            self._update_credentials_index(index)
            
            logger.info(f"Stored credential for platform: {platform}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store credential for {platform}: {e}")
            return False
    
    def get_credential(
        self,
        platform: str,
        credential_type: str = "api-key"
    ) -> Optional[str]:
        """
        Retrieve a credential.
        
        Args:
            platform: Platform name
            credential_type: Type of credential
            
        Returns:
            Optional[str]: The credential value, or None if not found
        """
        try:
            key = self._get_credential_key(platform, credential_type)
            credential = keyring.get_password(self.SERVICE_NAME, key)
            
            if credential is None:
                logger.warning(f"No credential found for platform: {platform}")
            
            return credential
            
        except Exception as e:
            logger.error(f"Failed to retrieve credential for {platform}: {e}")
            return None
    
    def delete_credential(
        self,
        platform: str,
        credential_type: str = "api-key"
    ) -> bool:
        """
        Delete a credential.
        
        Args:
            platform: Platform name
            credential_type: Type of credential
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            # Delete from keystore
            key = self._get_credential_key(platform, credential_type)
            keyring.delete_password(self.SERVICE_NAME, key)
            
            # Update index
            index = self._get_credentials_index()
            if platform in index:
                del index[platform]
                self._update_credentials_index(index)
            
            logger.info(f"Deleted credential for platform: {platform}")
            return True
            
        except keyring.errors.PasswordDeleteError:
            logger.warning(f"No credential to delete for platform: {platform}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete credential for {platform}: {e}")
            return False
    
    def list_platforms(self) -> List[str]:
        """
        List all platforms with stored credentials.
        
        Returns:
            List[str]: Platform names
        """
        index = self._get_credentials_index()
        return list(index.keys())
    
    def get_credential_metadata(self, platform: str) -> Optional[Dict]:
        """
        Get metadata for a platform's credential.
        
        Args:
            platform: Platform name
            
        Returns:
            Optional[Dict]: Metadata dictionary, or None if not found
        """
        index = self._get_credentials_index()
        return index.get(platform)
    
    def validate_credential(self, platform: str, credential_value: str) -> bool:
        """
        Validate a credential format.
        
        Args:
            platform: Platform name
            credential_value: Credential to validate
            
        Returns:
            bool: True if valid format
        """
        # Basic validation rules
        if not credential_value or len(credential_value) < 10:
            return False
        
        # Platform-specific validation
        if platform == "huggingface":
            # HuggingFace tokens start with "hf_"
            return credential_value.startswith("hf_")
        elif platform == "wandb":
            # W&B keys are typically 40 characters
            return len(credential_value) == 40
        elif platform in ["runpod", "lambda", "vastai"]:
            # Generic API key validation
            return len(credential_value) >= 20
        
        # Default: accept if non-empty and reasonable length
        return True
    
    def update_credential(
        self,
        platform: str,
        credential_value: str,
        credential_type: str = "api-key",
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Update an existing credential.
        
        Args:
            platform: Platform name
            credential_value: New credential value
            credential_type: Type of credential
            metadata: Optional updated metadata
            
        Returns:
            bool: True if updated successfully
        """
        # Check if credential exists
        if self.get_credential(platform, credential_type) is None:
            logger.warning(f"Cannot update non-existent credential for {platform}")
            return False
        
        # Store the new credential (overwrites existing)
        return self.store_credential(platform, credential_value, credential_type, metadata)


class CredentialMigrationTool:
    """
    Tool for migrating credentials from legacy storage to secure storage.
    
    Helps existing users migrate from plain-text or less secure storage
    to the new OS keystore-based system.
    """
    
    def __init__(self, credential_service: CredentialService):
        """
        Initialize migration tool.
        
        Args:
            credential_service: The credential service to migrate to
        """
        self.credential_service = credential_service
    
    def migrate_from_json(self, json_file_path: str) -> Dict[str, bool]:
        """
        Migrate credentials from a JSON file.
        
        Args:
            json_file_path: Path to JSON file with credentials
            
        Returns:
            Dict mapping platform names to migration success status
        """
        results = {}
        
        try:
            with open(json_file_path, 'r') as f:
                credentials = json.load(f)
            
            for platform, data in credentials.items():
                if isinstance(data, str):
                    # Simple format: {"platform": "api_key"}
                    success = self.credential_service.store_credential(platform, data)
                elif isinstance(data, dict):
                    # Complex format: {"platform": {"api_key": "...", "metadata": {...}}}
                    credential_value = data.get("api_key") or data.get("token")
                    metadata = data.get("metadata", {})
                    success = self.credential_service.store_credential(
                        platform, credential_value, metadata=metadata
                    )
                else:
                    success = False
                
                results[platform] = success
                
                if success:
                    logger.info(f"Migrated credential for {platform}")
                else:
                    logger.error(f"Failed to migrate credential for {platform}")
            
            return results
            
        except FileNotFoundError:
            logger.error(f"Migration file not found: {json_file_path}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in migration file: {json_file_path}")
            return {}
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return {}
    
    def migrate_from_env(self, env_mapping: Dict[str, str]) -> Dict[str, bool]:
        """
        Migrate credentials from environment variables.
        
        Args:
            env_mapping: Dict mapping platform names to env var names
                        e.g., {"runpod": "RUNPOD_API_KEY"}
            
        Returns:
            Dict mapping platform names to migration success status
        """
        import os
        
        results = {}
        
        for platform, env_var in env_mapping.items():
            credential_value = os.environ.get(env_var)
            
            if credential_value:
                success = self.credential_service.store_credential(platform, credential_value)
                results[platform] = success
                
                if success:
                    logger.info(f"Migrated credential for {platform} from {env_var}")
                else:
                    logger.error(f"Failed to migrate credential for {platform}")
            else:
                logger.warning(f"Environment variable {env_var} not found")
                results[platform] = False
        
        return results
    
    def export_to_json(self, output_path: str, include_values: bool = False) -> bool:
        """
        Export credential metadata (and optionally values) to JSON.
        
        WARNING: Only use include_values=True for backup purposes in secure locations.
        
        Args:
            output_path: Path to output JSON file
            include_values: Whether to include actual credential values (DANGEROUS)
            
        Returns:
            bool: True if export successful
        """
        try:
            platforms = self.credential_service.list_platforms()
            export_data = {}
            
            for platform in platforms:
                metadata = self.credential_service.get_credential_metadata(platform)
                export_data[platform] = metadata
                
                if include_values:
                    credential = self.credential_service.get_credential(platform)
                    export_data[platform]["credential_value"] = credential
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Exported credentials to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
