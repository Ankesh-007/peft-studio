"""
Property-Based Tests for Credential Encryption Round-Trip

Tests that credentials can be encrypted and decrypted without data loss.

**Feature: unified-llm-platform, Property 2: Credential encryption round-trip**
**Validates: Requirements 15.1, 15.2**
"""

import pytest
from hypothesis import given, strategies as st, settings
from services.credential_service import SecureStorage, CredentialService
import keyring
import tempfile
import os


# Strategy for generating credential-like strings
credential_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),  # Uppercase, lowercase, digits
        whitelist_characters='-_.'
    ),
    min_size=10,
    max_size=200
)


class TestCredentialEncryptionRoundtrip:
    """
    Property 2: Credential encryption round-trip
    
    For any API credential stored in the keystore, retrieving and decrypting
    should produce the original value.
    """
    
    @given(credential_value=credential_strategy)
    @settings(max_examples=100)
    def test_secure_storage_encryption_roundtrip(self, credential_value):
        """
        Test that SecureStorage can encrypt and decrypt any credential value.
        
        Property: For any credential string, encrypt(decrypt(x)) == x
        """
        # Create a fresh SecureStorage instance
        storage = SecureStorage()
        
        # Encrypt the credential
        encrypted = storage.encrypt(credential_value)
        
        # Verify it's actually encrypted (different from original)
        assert encrypted != credential_value.encode()
        
        # Decrypt and verify round-trip
        decrypted = storage.decrypt(encrypted)
        assert decrypted == credential_value
    
    @given(
        platform=st.text(
            alphabet='abcdefghijklmnopqrstuvwxyz0123456789-_',
            min_size=3,
            max_size=20
        ),
        credential_value=credential_strategy
    )
    @settings(max_examples=100)
    def test_credential_service_storage_roundtrip(self, platform, credential_value):
        """
        Test that CredentialService can store and retrieve any credential.
        
        Property: For any platform and credential, get(store(x)) == x
        """
        service = CredentialService()
        
        try:
            # Store the credential
            success = service.store_credential(platform, credential_value)
            assert success, f"Failed to store credential for {platform}"
            
            # Retrieve the credential
            retrieved = service.get_credential(platform)
            
            # Verify round-trip
            assert retrieved == credential_value, \
                f"Round-trip failed: expected {credential_value}, got {retrieved}"
        
        finally:
            # Cleanup: delete the test credential
            try:
                service.delete_credential(platform)
            except:
                pass  # Ignore cleanup errors
    
    @given(
        platform=st.text(
            alphabet='abcdefghijklmnopqrstuvwxyz0123456789-_',
            min_size=3,
            max_size=20
        ),
        credential_value=credential_strategy,
        metadata=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.text(min_size=0, max_size=50),
            max_size=5
        )
    )
    @settings(max_examples=50)
    def test_credential_with_metadata_roundtrip(self, platform, credential_value, metadata):
        """
        Test that credentials with metadata can be stored and retrieved.
        
        Property: For any platform, credential, and metadata,
                 the credential value should round-trip correctly.
        """
        service = CredentialService()
        
        try:
            # Store credential with metadata
            success = service.store_credential(
                platform,
                credential_value,
                metadata=metadata
            )
            assert success, f"Failed to store credential with metadata for {platform}"
            
            # Retrieve credential
            retrieved = service.get_credential(platform)
            assert retrieved == credential_value
            
            # Retrieve metadata
            retrieved_metadata = service.get_credential_metadata(platform)
            assert retrieved_metadata is not None
            assert retrieved_metadata["metadata"] == metadata
        
        finally:
            # Cleanup
            try:
                service.delete_credential(platform)
            except:
                pass
    
    @given(
        platform=st.text(
            alphabet='abcdefghijklmnopqrstuvwxyz0123456789-_',
            min_size=3,
            max_size=20
        ),
        original_credential=credential_strategy,
        updated_credential=credential_strategy
    )
    @settings(max_examples=50)
    def test_credential_update_roundtrip(self, platform, original_credential, updated_credential):
        """
        Test that updating a credential preserves round-trip property.
        
        Property: After updating a credential, the new value should be retrievable.
        """
        service = CredentialService()
        
        try:
            # Store original credential
            service.store_credential(platform, original_credential)
            
            # Update credential
            success = service.update_credential(platform, updated_credential)
            assert success, f"Failed to update credential for {platform}"
            
            # Retrieve and verify it's the updated value
            retrieved = service.get_credential(platform)
            assert retrieved == updated_credential, \
                f"Update failed: expected {updated_credential}, got {retrieved}"
        
        finally:
            # Cleanup
            try:
                service.delete_credential(platform)
            except:
                pass
    
    def test_multiple_platforms_isolation(self):
        """
        Test that credentials for different platforms don't interfere.
        
        Property: Storing credentials for multiple platforms should not cause
                 cross-contamination.
        """
        service = CredentialService()
        
        platforms_and_creds = {
            "runpod": "runpod_api_key_12345",
            "huggingface": "hf_token_67890",
            "wandb": "wandb_key_abcdef1234567890abcdef1234567890"
        }
        
        try:
            # Store all credentials
            for platform, cred in platforms_and_creds.items():
                success = service.store_credential(platform, cred)
                assert success, f"Failed to store credential for {platform}"
            
            # Verify each credential independently
            for platform, expected_cred in platforms_and_creds.items():
                retrieved = service.get_credential(platform)
                assert retrieved == expected_cred, \
                    f"Isolation failed for {platform}: expected {expected_cred}, got {retrieved}"
        
        finally:
            # Cleanup all
            for platform in platforms_and_creds.keys():
                try:
                    service.delete_credential(platform)
                except:
                    pass
    
    @given(credential_value=credential_strategy)
    @settings(max_examples=50)
    def test_encryption_produces_different_output(self, credential_value):
        """
        Test that encryption actually transforms the data.
        
        Property: For any credential, encrypted form should differ from plaintext.
        """
        storage = SecureStorage()
        
        encrypted = storage.encrypt(credential_value)
        
        # Encrypted data should be different from original
        assert encrypted != credential_value.encode()
        
        # Encrypted data should be bytes
        assert isinstance(encrypted, bytes)
        
        # Encrypted data should be longer (due to encryption overhead)
        # Fernet adds ~57 bytes of overhead
        assert len(encrypted) > len(credential_value)
    
    def test_delete_credential_removes_access(self):
        """
        Test that deleted credentials cannot be retrieved.
        
        Property: After deleting a credential, get() should return None.
        """
        service = CredentialService()
        platform = "test_platform_delete"
        credential = "test_credential_value"
        
        try:
            # Store credential
            service.store_credential(platform, credential)
            
            # Verify it exists
            assert service.get_credential(platform) == credential
            
            # Delete credential
            success = service.delete_credential(platform)
            assert success
            
            # Verify it's gone
            retrieved = service.get_credential(platform)
            assert retrieved is None
        
        finally:
            # Ensure cleanup
            try:
                service.delete_credential(platform)
            except:
                pass
    
    @given(
        platforms=st.lists(
            st.text(
                alphabet='abcdefghijklmnopqrstuvwxyz0123456789-_',
                min_size=3,
                max_size=20
            ),
            min_size=1,
            max_size=10,
            unique=True
        )
    )
    @settings(max_examples=30, deadline=500)
    def test_list_platforms_accuracy(self, platforms):
        """
        Test that list_platforms returns all stored platforms.
        
        Property: After storing credentials for N platforms,
                 list_platforms() should return exactly those N platforms.
        """
        service = CredentialService()
        
        try:
            # Store credentials for all platforms
            for platform in platforms:
                service.store_credential(platform, f"credential_for_{platform}")
            
            # Get list of platforms
            listed_platforms = service.list_platforms()
            
            # Verify all platforms are listed
            for platform in platforms:
                assert platform in listed_platforms, \
                    f"Platform {platform} not in list: {listed_platforms}"
        
        finally:
            # Cleanup
            for platform in platforms:
                try:
                    service.delete_credential(platform)
                except:
                    pass


class TestSecureStorageEdgeCases:
    """Test edge cases for SecureStorage."""
    
    def test_empty_string_roundtrip(self):
        """Test that empty strings can be encrypted and decrypted."""
        storage = SecureStorage()
        
        encrypted = storage.encrypt("")
        decrypted = storage.decrypt(encrypted)
        
        assert decrypted == ""
    
    def test_unicode_roundtrip(self):
        """Test that Unicode characters are preserved."""
        storage = SecureStorage()
        
        unicode_text = "Hello 世界 🌍 Привет"
        encrypted = storage.encrypt(unicode_text)
        decrypted = storage.decrypt(encrypted)
        
        assert decrypted == unicode_text
    
    def test_special_characters_roundtrip(self):
        """Test that special characters are preserved."""
        storage = SecureStorage()
        
        special_text = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        encrypted = storage.encrypt(special_text)
        decrypted = storage.decrypt(encrypted)
        
        assert decrypted == special_text
    
    def test_very_long_credential_roundtrip(self):
        """Test that very long credentials work."""
        storage = SecureStorage()
        
        # 10KB credential
        long_credential = "a" * 10000
        encrypted = storage.encrypt(long_credential)
        decrypted = storage.decrypt(encrypted)
        
        assert decrypted == long_credential
