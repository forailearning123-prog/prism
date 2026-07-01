"""
Connector Registry
Manages registration, discovery, and instantiation of connectors.
"""

from typing import Any, Optional
from importlib import import_module
from pathlib import Path

from .base import BaseConnector, ConnectorCapabilities


class ConnectorRegistry:
    """
    Central registry for all connectors.
    Manages connector discovery, registration, and instantiation.
    """
    
    def __init__(self):
        self._connectors: dict[str, type[BaseConnector]] = {}
        self._metadata: dict[str, dict[str, Any]] = {}
    
    def register(
        self,
        name: str,
        connector_class: type[BaseConnector],
        metadata: dict[str, Any] = None
    ) -> None:
        """
        Register a connector class.
        
        Args:
            name: Unique connector name (e.g., 'salesforce', 'postgresql')
            connector_class: Connector class that inherits from BaseConnector
            metadata: Additional metadata (category, capabilities, etc.)
        """
        if name in self._connectors:
            raise ValueError(f"Connector '{name}' is already registered")
        
        if not issubclass(connector_class, BaseConnector):
            raise TypeError(f"Connector class must inherit from BaseConnector")
        
        self._connectors[name] = connector_class
        self._metadata[name] = metadata or {}
    
    def unregister(self, name: str) -> None:
        """Unregister a connector."""
        if name not in self._connectors:
            raise ValueError(f"Connector '{name}' is not registered")
        
        del self._connectors[name]
        del self._metadata[name]
    
    def get(self, name: str) -> Optional[type[BaseConnector]]:
        """
        Get a connector class by name.
        
        Args:
            name: Connector name
            
        Returns:
            Connector class or None if not found
        """
        return self._connectors.get(name)
    
    def get_metadata(self, name: str) -> Optional[dict[str, Any]]:
        """
        Get connector metadata.
        
        Args:
            name: Connector name
            
        Returns:
            Metadata dictionary or None if not found
        """
        return self._metadata.get(name)
    
    def list_connectors(self) -> list[str]:
        """
        List all registered connector names.
        
        Returns:
            List of connector names
        """
        return list(self._connectors.keys())
    
    def list_by_category(self, category: str) -> list[str]:
        """
        List connectors by category.
        
        Args:
            category: Category name (e.g., 'crm', 'database')
            
        Returns:
            List of connector names in the category
        """
        return [
            name for name, meta in self._metadata.items()
            if meta.get("category") == category
        ]
    
    def create_instance(
        self,
        name: str,
        config: dict[str, Any],
        auth_config: dict[str, Any]
    ) -> BaseConnector:
        """
        Create an instance of a connector.
        
        Args:
            name: Connector name
            config: Connector configuration
            auth_config: Authentication configuration
            
        Returns:
            Connector instance
            
        Raises:
            ValueError: If connector is not registered
        """
        connector_class = self.get(name)
        if not connector_class:
            raise ValueError(f"Connector '{name}' is not registered")
        
        return connector_class(config, auth_config)
    
    def discover_connectors(self, package_path: str = "app.integrations.connectors") -> list[str]:
        """
        Auto-discover connectors from a package.
        
        Args:
            package_path: Python package path to search
            
        Returns:
            List of discovered connector names
        """
        discovered = []
        
        try:
            package = import_module(package_path)
            package_dir = Path(package.__file__).parent
            
            # Iterate through subdirectories (categories)
            for category_dir in package_dir.iterdir():
                if not category_dir.is_dir() or category_dir.name.startswith("_"):
                    continue
                
                # Iterate through Python files
                for py_file in category_dir.glob("*.py"):
                    if py_file.name.startswith("_"):
                        continue
                    
                    module_name = py_file.stem
                    full_module_path = f"{package_path}.{category_dir.name}.{module_name}"
                    
                    try:
                        module = import_module(full_module_path)
                        
                        # Look for connector classes
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            
                            if (
                                isinstance(attr, type)
                                and issubclass(attr, BaseConnector)
                                and attr != BaseConnector
                            ):
                                # Auto-register if not already registered
                                if attr_name.lower() not in self._connectors:
                                    self.register(
                                        name=attr_name.lower(),
                                        connector_class=attr,
                                        metadata={
                                            "category": category_dir.name,
                                            "module": full_module_path,
                                            "class": attr_name,
                                        }
                                    )
                                    discovered.append(attr_name.lower())
                    except Exception as e:
                        # Log but continue discovery
                        pass
        
        except Exception as e:
            pass
        
        return discovered
    
    def get_capabilities(self, name: str) -> Optional[ConnectorCapabilities]:
        """
        Get capabilities of a connector.
        
        Args:
            name: Connector name
            
        Returns:
            ConnectorCapabilities or None if not found
        """
        connector_class = self.get(name)
        if not connector_class:
            return None
        
        # Create a temporary instance to get capabilities
        # This is a simplified approach - in production, you might cache this
        try:
            instance = connector_class({}, {})
            return instance.get_capabilities()
        except Exception:
            return None
    
    def validate_connector(self, name: str) -> bool:
        """
        Validate that a connector is properly implemented.
        
        Args:
            name: Connector name
            
        Returns:
            True if valid, False otherwise
        """
        connector_class = self.get(name)
        if not connector_class:
            return False
        
        # Check that all abstract methods are implemented
        required_methods = [
            "connect", "disconnect", "test_connection", "health_check",
            "read", "write"
        ]
        
        for method in required_methods:
            if not hasattr(connector_class, method):
                return False
        
        return True
    
    def clear(self) -> None:
        """Clear all registered connectors."""
        self._connectors.clear()
        self._metadata.clear()


# Global registry instance
connector_registry = ConnectorRegistry()


def register_connector(name: str, metadata: dict[str, Any] = None):
    """
    Decorator to register a connector.
    
    Usage:
        @register_connector("salesforce", {"category": "crm"})
        class SalesforceConnector(BaseConnector):
            ...
    """
    def decorator(connector_class: type[BaseConnector]) -> type[BaseConnector]:
        connector_registry.register(name, connector_class, metadata)
        return connector_class
    
    return decorator