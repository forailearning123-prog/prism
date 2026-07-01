"""
Version Manager
Manages integration versions and change tracking.
"""

from typing import Any, Optional, Dict, List
from datetime import datetime, timezone
import hashlib
import json


class VersionManager:
    """
    Manages integration versions.
    Tracks changes, supports rollback, and maintains version history.
    """
    
    def __init__(self):
        """Initialize version manager."""
        self.versions: Dict[int, List[dict[str, Any]]] = {}
        self.next_version_id = 1
    
    def create_version(
        self,
        integration_id: int,
        config: dict[str, Any],
        created_by: int,
        change_description: str = "",
        parent_version_id: int = None
    ) -> dict[str, Any]:
        """
        Create a new version of an integration.
        
        Args:
            integration_id: Integration ID
            config: Integration configuration
            created_by: User ID who created the version
            change_description: Description of changes
            parent_version_id: Parent version ID
            
        Returns:
            Version dictionary
        """
        # Calculate config hash
        config_str = json.dumps(config, sort_keys=True)
        config_hash = hashlib.sha256(config_str.encode()).hexdigest()[:16]
        
        version = {
            "id": self.next_version_id,
            "integration_id": integration_id,
            "version": self._generate_version(integration_id),
            "config": config,
            "config_hash": config_hash,
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "change_description": change_description,
            "parent_version_id": parent_version_id,
            "is_active": True,
            "metadata": {
                "config_size": len(config_str),
                "fields_count": len(config.get("mappings", [])) + len(config.get("transformations", []))
            }
        }
        
        # Store version
        if integration_id not in self.versions:
            self.versions[integration_id] = []
        
        self.versions[integration_id].append(version)
        self.next_version_id += 1
        
        return version
    
    def _generate_version(self, integration_id: int) -> str:
        """
        Generate version number.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Version string (e.g., "1.0.1")
        """
        existing_versions = self.versions.get(integration_id, [])
        
        if not existing_versions:
            return "1.0.0"
        
        # Get latest version
        latest = existing_versions[-1]
        version_parts = latest["version"].split(".")
        
        # Increment patch version
        major, minor, patch = int(version_parts[0]), int(version_parts[1]), int(version_parts[2])
        patch += 1
        
        return f"{major}.{minor}.{patch}"
    
    def get_version(self, integration_id: int, version_id: int) -> Optional[dict[str, Any]]:
        """
        Get a specific version.
        
        Args:
            integration_id: Integration ID
            version_id: Version ID
            
        Returns:
            Version dictionary or None
        """
        versions = self.versions.get(integration_id, [])
        for version in versions:
            if version["id"] == version_id:
                return version
        return None
    
    def get_version_by_number(self, integration_id: int, version: str) -> Optional[dict[str, Any]]:
        """
        Get version by version number.
        
        Args:
            integration_id: Integration ID
            version: Version number (e.g., "1.0.1")
            
        Returns:
            Version dictionary or None
        """
        versions = self.versions.get(integration_id, [])
        for v in versions:
            if v["version"] == version:
                return v
        return None
    
    def get_latest_version(self, integration_id: int) -> Optional[dict[str, Any]]:
        """
        Get the latest version of an integration.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Latest version or None
        """
        versions = self.versions.get(integration_id, [])
        return versions[-1] if versions else None
    
    def list_versions(
        self,
        integration_id: int,
        limit: int = 100
    ) -> List[dict[str, Any]]:
        """
        List versions for an integration.
        
        Args:
            integration_id: Integration ID
            limit: Maximum number of versions
            
        Returns:
            List of version dictionaries
        """
        versions = self.versions.get(integration_id, [])
        return versions[-limit:]
    
    def rollback(self, integration_id: int, version_id: int, user_id: int) -> dict[str, Any]:
        """
        Rollback to a previous version.
        
        Args:
            integration_id: Integration ID
            version_id: Version ID to rollback to
            user_id: User ID performing rollback
            
        Returns:
            New version created from rollback
        """
        target_version = self.get_version(integration_id, version_id)
        if not target_version:
            raise ValueError(f"Version {version_id} not found")
        
        # Create new version from target
        new_version = self.create_version(
            integration_id=integration_id,
            config=target_version["config"],
            created_by=user_id,
            change_description=f"Rollback to version {target_version['version']}",
            parent_version_id=target_version["id"]
        )
        
        new_version["is_rollback"] = True
        new_version["rollback_from_version"] = target_version["version"]
        
        return new_version
    
    def compare_versions(
        self,
        integration_id: int,
        version_id_1: int,
        version_id_2: int
    ) -> dict[str, Any]:
        """
        Compare two versions.
        
        Args:
            integration_id: Integration ID
            version_id_1: First version ID
            version_id_2: Second version ID
            
        Returns:
            Comparison result
        """
        v1 = self.get_version(integration_id, version_id_1)
        v2 = self.get_version(integration_id, version_id_2)
        
        if not v1 or not v2:
            raise ValueError("One or both versions not found")
        
        # Compare configs
        config1 = v1["config"]
        config2 = v2["config"]
        
        changes = {
            "mappings_added": [],
            "mappings_removed": [],
            "mappings_modified": [],
            "transformations_added": [],
            "transformations_removed": [],
            "transformations_modified": []
        }
        
        # Compare mappings
        mappings1 = {m.get("source_field"): m for m in config1.get("mappings", [])}
        mappings2 = {m.get("source_field"): m for m in config2.get("mappings", [])}
        
        for field in mappings2:
            if field not in mappings1:
                changes["mappings_added"].append(mappings2[field])
            elif mappings1[field] != mappings2[field]:
                changes["mappings_modified"].append({
                    "old": mappings1[field],
                    "new": mappings2[field]
                })
        
        for field in mappings1:
            if field not in mappings2:
                changes["mappings_removed"].append(mappings1[field])
        
        return {
            "version_1": v1["version"],
            "version_2": v2["version"],
            "changes": changes,
            "has_changes": any(len(v) > 0 for v in changes.values())
        }
    
    def get_version_history(self, integration_id: int) -> List[dict[str, Any]]:
        """
        Get complete version history for an integration.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            List of versions
        """
        return self.versions.get(integration_id, [])
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get version manager statistics.
        
        Returns:
            Statistics dictionary
        """
        total_versions = sum(len(versions) for versions in self.versions.values())
        
        return {
            "total_integrations": len(self.versions),
            "total_versions": total_versions,
            "avg_versions_per_integration": total_versions / len(self.versions) if self.versions else 0
        }