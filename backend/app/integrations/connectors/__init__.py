"""
Connector Framework
Plugin-based architecture for enterprise system integrations.
"""

from .base import BaseConnector, ConnectorCapabilities
from .registry import ConnectorRegistry

__all__ = ["BaseConnector", "ConnectorCapabilities", "ConnectorRegistry"]