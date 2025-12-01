"""
Connector system for integrating with external platforms.

This module provides the base infrastructure for pluggable connectors
that integrate with cloud GPU providers, model registries, experiment
trackers, and deployment platforms.
"""

from .base import PlatformConnector, Resource, PricingInfo, TrainingConfig
from .manager import ConnectorManager
from .registry import ConnectorRegistry

__all__ = [
    'PlatformConnector',
    'Resource',
    'PricingInfo',
    'TrainingConfig',
    'ConnectorManager',
    'ConnectorRegistry',
]
