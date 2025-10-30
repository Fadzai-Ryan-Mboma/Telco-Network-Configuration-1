#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Network - Network Integration Module
Phase 2 Implementation: Live Network Connection Testing
"""

from .huawei_api_client import HuaweiAPIClient, HuaweiAPIError, HuaweiAuthenticationError

__all__ = [
    'HuaweiAPIClient',
    'HuaweiAPIError', 
    'HuaweiAuthenticationError'
]

__version__ = '2.0.0-phase2'