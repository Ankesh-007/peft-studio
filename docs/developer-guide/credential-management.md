# Credential Management System

## Overview

The credential management system provides secure storage and management of API credentials using OS-level keystore integration and encryption. This ensures that sensitive credentials are never stored in plain text and are protected by the operating system's native security mechanisms.

## Features

- **OS Keystore Integration**: Uses Windows Credential Manager, macOS Keychain, or Linux Secret Service
- **Encryption**: Additional layer of encryption using Fernet symmetric encryption
- **CRUD Operations**: Complete create, read, update, delete operations for credentials
- **Validation**: Platform-specific credential format validation
- **Migration Tools**: Tools to migrate from legacy storage systems
- **Metadata Support**: Store additional metadata alongside credentials

## Requirements

Validates Requirements: 15.1, 15.2, 15.3

## Usage

### Basic Operations

```python
from services.credential_service import CredentialService

# Initialize service
service = CredentialService()

# Store a credential
service.store_credential(
    platform="runpod",
    credential_value="your_api_key_here",
    metadata={"username": "user@example.com"}
)

# Retrieve a credential
api_key = service.get_credential("runpod")

# Update a credential
service.update_credential(
    platform="runpod",
    credential_value="new_api_key_here"
)

# Delete a credential
service.delete_credential("runpod")

# List all platforms with stored credentials
platforms = service.list_platforms()

# Get metadata for a platform
metadata = service.get_credential_metadata("runpod")
```

### Validation

```python
# Validate credential format before storing
is_valid = service.validate_credential("huggingface", "hf_token_12345")
if is_valid:
    service.store_credential("huggingface", "hf_token_12345")
```

### Migration

```python
from services.credential_service import CredentialService, CredentialMigrationTool

service = CredentialService()
migration_tool = CredentialMigrationTool(service)

# Migrate from JSON file
results = migration_tool.migrate_from_json("old_credentials.json")

# Migrate from environment variables
env_mapping = {
    "runpod": "RUNPOD_API_KEY",
    "huggingface": "HF_TOKEN",
    "wandb": "WANDB_API_KEY"
}
results = migration_tool.migrate_from_env(env_mapping)

# Export credentials (for backup - use with caution!)
migration_tool.export_to_json("backup.json", include_values=False)
```

## Security Features

### OS Keystore

Credentials are stored in the operating system's native keystore:
- **Windows**: Windows Credential Manager
- **macOS**: Keychain
- **Linux**: Secret Service (GNOME Keyring, KWallet, etc.)

### Encryption

An additional layer of encryption is applied using Fernet (symmetric encryption):
- Master encryption key is stored in the OS keystore
- All sensitive data is encrypted before storage
- Automatic key generation on first use

### Best Practices

1. **Never log credentials**: The service automatically prevents credential logging
2. **Validate before storing**: Use `validate_credential()` to check format
3. **Use metadata wisely**: Don't store sensitive data in metadata
4. **Regular rotation**: Update credentials periodically using `update_credential()`
5. **Secure exports**: Only export with `include_values=True` for secure backups

## Platform-Specific Validation

The service includes validation rules for common platforms:

- **HuggingFace**: Tokens must start with "hf_"
- **Weights & Biases**: Keys are typically 40 characters
- **RunPod, Lambda Labs, Vast.ai**: Minimum 20 characters

## Testing

The credential management system includes comprehensive property-based tests:

```bash
pytest backend/tests/test_credential_encryption_roundtrip.py -v
```

**Property 2: Credential encryption round-trip**
- For any API credential stored in the keystore, retrieving and decrypting should produce the original value
- Validates Requirements 15.1, 15.2

## Error Handling

The service handles errors gracefully:
- Returns `False` on storage/update/delete failures
- Returns `None` on retrieval failures
- Logs errors for debugging
- Never exposes credentials in error messages

## API Reference

### CredentialService

#### `store_credential(platform, credential_value, credential_type="api-key", metadata=None) -> bool`
Store a credential securely.

#### `get_credential(platform, credential_type="api-key") -> Optional[str]`
Retrieve a credential.

#### `update_credential(platform, credential_value, credential_type="api-key", metadata=None) -> bool`
Update an existing credential.

#### `delete_credential(platform, credential_type="api-key") -> bool`
Delete a credential.

#### `list_platforms() -> List[str]`
List all platforms with stored credentials.

#### `get_credential_metadata(platform) -> Optional[Dict]`
Get metadata for a platform's credential.

#### `validate_credential(platform, credential_value) -> bool`
Validate a credential format.

### SecureStorage

#### `encrypt(data: str) -> bytes`
Encrypt a string.

#### `decrypt(encrypted: bytes) -> str`
Decrypt encrypted data.

### CredentialMigrationTool

#### `migrate_from_json(json_file_path: str) -> Dict[str, bool]`
Migrate credentials from a JSON file.

#### `migrate_from_env(env_mapping: Dict[str, str]) -> Dict[str, bool]`
Migrate credentials from environment variables.

#### `export_to_json(output_path: str, include_values: bool = False) -> bool`
Export credential metadata (and optionally values) to JSON.

## Integration with Connectors

The credential service integrates seamlessly with platform connectors:

```python
from services.credential_service import CredentialService
from connectors.base import PlatformConnector

service = CredentialService()

# Store credentials
service.store_credential("runpod", "your_api_key")

# Use in connector
class RunPodConnector(PlatformConnector):
    async def connect(self, credentials: Dict[str, str]) -> bool:
        # Credentials retrieved from secure storage
        self.api_key = credentials.get("api_key")
        # Verify connection...
```

## Troubleshooting

### Windows: "The stub received bad data" error
This occurs when platform names contain characters not supported by Windows Credential Manager. Use only ASCII alphanumeric characters, hyphens, and underscores in platform names.

### Linux: "No keyring backend available"
Install a keyring backend:
```bash
# For GNOME
sudo apt-get install gnome-keyring

# For KDE
sudo apt-get install kwalletmanager
```

### macOS: "User interaction required"
The first time accessing Keychain, macOS may prompt for permission. Grant access to allow the application to store credentials.

## Future Enhancements

- Credential expiration and automatic rotation
- Multi-factor authentication support
- Credential sharing between team members (with encryption)
- Audit logging for credential access
- Integration with cloud secret managers (AWS Secrets Manager, Azure Key Vault)
