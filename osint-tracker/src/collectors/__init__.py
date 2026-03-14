"""
Collectors package — each collector pulls from one public data source.
All collectors share a common async interface via BaseCollector.
"""

from .base_collector import BaseCollector

__all__ = ["BaseCollector"]
