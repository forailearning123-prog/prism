"""
Custom Connectors
Generic connectors for REST APIs, GraphQL, SOAP, and Webhooks.
"""

from .rest_api import RestApiConnector
from .graphql import GraphQLConnector
from .webhook import WebhookConnector

__all__ = ["RestApiConnector", "GraphQLConnector", "WebhookConnector"]