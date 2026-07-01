"""
Secrets Manager
Manages secure storage and retrieval of credentials.
"""

from typing import Any, Optional
import json

from .encryption import EncryptionService
from app.integrations.exceptions import SecretsManagementError


class SecretsManager:
    """
    Manages secrets for connector configurations.
    Provides encryption at rest and integration with external secret stores.
    """
    
    def __init__(self, encryption_service: Optional[EncryptionService] = None):
        """
        Initialize secrets manager.
        
        Args:
            encryption_service: Encryption service instance
        """
        self.encryption = encryption_service or EncryptionService()
    
    def encrypt_credentials(self, credentials: dict[str, Any]) -> str:
        """
        Encrypt credentials for storage.
        
        Args:
            credentials: Dictionary of credentials to encrypt
            
        Returns:
            Encrypted string
        """
        try:
            return self.encryption.encrypt_dict(credentials)
        except Exception as e:
            raise SecretsManagementError(f"Failed to encrypt credentials: {str(e)}")
    
    def decrypt_credentials(self, encrypted_credentials: str) -> dict[str, Any]:
        """
        Decrypt credentials from storage.
        
        Args:
            encrypted_credentials: Encrypted credentials string
            
        Returns:
            Decrypted credentials dictionary
        """
        try:
            return self.encryption.decrypt_dict(encrypted_credentials)
        except Exception as e:
            raise SecretsManagementError(f"Failed to decrypt credentials: {str(e)}")
    
    def mask_credentials(self, credentials: dict[str, Any]) -> dict[str, Any]:
        """
        Mask sensitive values for logging/display.
        
        Args:
            credentials: Credentials dictionary
            
        Returns:
            Masked credentials dictionary
        """
        masked = {}
        sensitive_keys = ["password", "secret", "token", "api_key", "key", "credential"]
        
        for key, value in credentials.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                if isinstance(value, str) and len(value) > 8:
                    masked[key] = value[:4] + "****" + value[-4:]
                else:
                    masked[key] = "****"
            else:
                masked[key] = value
        
        return masked
    
    def validate_credentials(self, credentials: dict[str, Any], required_fields: list[str]) -> bool:
        """
        Validate that all required credential fields are present.
        
        Args:
            credentials: Credentials dictionary
            required_fields: List of required field names
            
        Returns:
            True if all required fields are present and non-empty
        """
        for field in required_fields:
            if field not in credentials or not credentials[field]:
                return False
        return True
    
    def rotate_credentials(
        self,
        old_credentials: dict[str, Any],
        new_credentials: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Rotate credentials by merging old and new.
        Keeps unchanged fields from old credentials.
        
        Args:
            old_credentials: Old credentials
            new_credentials: New credentials (partial update)
            
        Returns:
            Merged credentials
        """
        merged = old_credentials.copy()
        merged.update(new_credentials)
        return merged
    
    def get_secret_reference(self, provider: str, secret_id: str) -> str:
        """
        Generate a reference string for external secret managers.
        
        Args:
            provider: Secret provider (e.g., 'aws', 'azure', 'vault')
            secret_id: Secret identifier
            
        Returns:
            Reference string
        """
        return f"{provider}://{secret_id}"
    
    def parse_secret_reference(self, reference: str) -> tuple[str, str]:
        """
        Parse a secret reference string.
        
        Args:
            reference: Reference string (e.g., 'aws://my-secret')
            
        Returns:
            Tuple of (provider, secret_id)
        """
        parts = reference.split("://", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid secret reference format: {reference}")
        
        provider, secret_id = parts
        return provider, secret_id
    
    async def fetch_from_external(
        self,
        provider: str,
        secret_id: str,
        **kwargs
    ) -> dict[str, Any]:
        """
        Fetch secrets from external secret manager.
        
        Args:
            provider: Secret provider ('aws', 'azure', 'vault', etc.)
            secret_id: Secret identifier
            **kwargs: Provider-specific parameters
            
        Returns:
            Secret credentials dictionary
        """
        if provider == "aws":
            return await self._fetch_from_aws(secret_id, **kwargs)
        elif provider == "azure":
            return await self._fetch_from_azure(secret_id, **kwargs)
        elif provider == "vault":
            return await self._fetch_from_vault(secret_id, **kwargs)
        else:
            raise SecretsManagementError(f"Unsupported secret provider: {provider}")
    
    async def _fetch_from_aws(self, secret_id: str, **kwargs) -> dict[str, Any]:
        """Fetch secret from AWS Secrets Manager."""
        try:
            import boto3
            
            client = boto3.client("secretsmanager", **kwargs)
            response = client.get_secret_value(SecretId=secret_id)
            
            # Parse the secret
            secret_string = response.get("SecretString")
            if secret_string:
                return json.loads(secret_string)
            
            # Binary secret
            secret_binary = response.get("SecretBinary")
            if secret_binary:
                return json.loads(secret_binary.decode())
            
            return {}
        except ImportError:
            raise SecretsManagementError(
                "boto3 is required for AWS Secrets Manager. Install with: pip install boto3"
            )
        except Exception as e:
            raise SecretsManagementError(f"Failed to fetch secret from AWS: {str(e)}")
    
    async def _fetch_from_azure(self, secret_id: str, **kwargs) -> dict[str, Any]:
        """Fetch secret from Azure Key Vault."""
        try:
            from azure.keyvault.secrets import SecretClient
            from azure.identity import DefaultAzureCredential
            
            vault_url = kwargs.get("vault_url")
            if not vault_url:
                raise ValueError("vault_url is required for Azure Key Vault")
            
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=vault_url, credential=credential)
            
            secret = client.get_secret(secret_id)
            return json.loads(secret.value)
        except ImportError:
            raise SecretsManagementError(
                "azure-keyvault-secrets is required. Install with: pip install azure-keyvault-secrets"
            )
        except Exception as e:
            raise SecretsManagementError(f"Failed to fetch secret from Azure: {str(e)}")
    
    async def _fetch_from_vault(self, secret_id: str, **kwargs) -> dict[str, Any]:
        """Fetch secret from HashiCorp Vault."""
        try:
            import hvac
            
            client = hvac.Client(**kwargs)
            response = client.secrets.kv.read_secret_version(path=secret_id)
            
            if "data" in response and "data" in response["data"]:
                return response["data"]["data"]
            
            return {}
        except ImportError:
            raise SecretsManagementError(
                "hvac is required for HashiCorp Vault. Install with: pip install hvac"
            )
        except Exception as e:
            raise SecretsManagementError(f"Failed to fetch secret from Vault: {str(e)}")
    
    async def store_in_external(
        self,
        provider: str,
        secret_id: str,
        credentials: dict[str, Any],
        **kwargs
    ) -> str:
        """
        Store secrets in external secret manager.
        
        Args:
            provider: Secret provider
            secret_id: Secret identifier
            credentials: Credentials to store
            **kwargs: Provider-specific parameters
            
        Returns:
            Secret reference string
        """
        if provider == "aws":
            await self._store_in_aws(secret_id, credentials, **kwargs)
        elif provider == "azure":
            await self._store_in_azure(secret_id, credentials, **kwargs)
        elif provider == "vault":
            await self._store_in_vault(secret_id, credentials, **kwargs)
        else:
            raise SecretsManagementError(f"Unsupported secret provider: {provider}")
        
        return self.get_secret_reference(provider, secret_id)
    
    async def _store_in_aws(self, secret_id: str, credentials: dict[str, Any], **kwargs):
        """Store secret in AWS Secrets Manager."""
        try:
            import boto3
            
            client = boto3.client("secretsmanager", **kwargs)
            client.create_secret(
                Name=secret_id,
                SecretString=json.dumps(credentials)
            )
        except ImportError:
            raise SecretsManagementError("boto3 is required for AWS Secrets Manager")
        except Exception as e:
            raise SecretsManagementError(f"Failed to store secret in AWS: {str(e)}")
    
    async def _store_in_azure(self, secret_id: str, credentials: dict[str, Any], **kwargs):
        """Store secret in Azure Key Vault."""
        try:
            from azure.keyvault.secrets import SecretClient
            from azure.identity import DefaultAzureCredential
            
            vault_url = kwargs.get("vault_url")
            if not vault_url:
                raise ValueError("vault_url is required for Azure Key Vault")
            
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=vault_url, credential=credential)
            
            client.set_secret(secret_id, json.dumps(credentials))
        except ImportError:
            raise SecretsManagementError("azure-keyvault-secrets is required")
        except Exception as e:
            raise SecretsManagementError(f"Failed to store secret in Azure: {str(e)}")
    
    async def _store_in_vault(self, secret_id: str, credentials: dict[str, Any], **kwargs):
        """Store secret in HashiCorp Vault."""
        try:
            import hvac
            
            client = hvac.Client(**kwargs)
            client.secrets.kv.create_or_update_secret(
                path=secret_id,
                secret=credentials
            )
        except ImportError:
            raise SecretsManagementError("hvac is required for HashiCorp Vault")
        except Exception as e:
            raise SecretsManagementError(f"Failed to store secret in Vault: {str(e)}")