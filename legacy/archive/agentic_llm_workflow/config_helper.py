"""
Configuration Helper for Hybrid System
Provides centralized config loading with path resolution
"""

import os
import yaml
from typing import Dict, Any, Optional

def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.yaml with automatic path resolution.
    Tries multiple paths to find the config file.
    """
    possible_paths = [
        'config.yaml',
        '../config.yaml',
        '/Users/fadzai/Library/CloudStorage/OneDrive-LiquidIntelligentTechnologies/Documents/Cassava AI/Telco-Network-Config/Telco-Network-Configuration/config.yaml'
    ]
    
    for config_path in possible_paths:
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f)
        except Exception:
            continue
    
    # Return default configuration if no file found
    return {
        "table_name": "liquid_zimbabwe_kpis",
        "persistent_db_path": "../data/liquid_zimbabwe.db",
        "historical_db_path": "../data/historical_db",
        "validation_wait_time": 3
    }

def get_config_value(key: str, default: Any = None) -> Any:
    """Get a specific configuration value with fallback to default"""
    config = load_config()
    return config.get(key, default)

# Global config instance for easy access
_global_config = None

def get_global_config() -> Dict[str, Any]:
    """Get the global configuration instance"""
    global _global_config
    if _global_config is None:
        _global_config = load_config()
    return _global_config