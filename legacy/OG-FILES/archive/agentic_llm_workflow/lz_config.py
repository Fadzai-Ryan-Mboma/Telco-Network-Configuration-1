"""
Liquid Zimbabwe Configuration Extensions
Adds LZ-specific configuration while preserving original functionality
"""

import yaml
import os
from typing import Dict, Optional

# Default Liquid Zimbabwe Configuration
LZ_CONFIG = {
    "liquid_zimbabwe": {
        "enabled": True,
        "api_endpoint": "https://41.174.191.214:31127",
        "username": "cassava.ai",
        "password": "#Pass123#",
        "fallback_to_simulation": True,
        "timeout_seconds": 10,
        "verify_ssl": False
    },
    "parameter_mapping": {
        # Original param -> Liquid Zimbabwe parameter
        "p0_nominal": "P0_NominalPUSCH", 
        "dl_carrierBandwidth": "ReferenceSignalPower_PDSCH",
        "ul_carrierBandwidth": "ReferenceSignalPower_PUSCH",
        "att_tx": "A3EventOffset",
        "att_rx": "T310Timer"
    },
    "kpi_preferences": {
        # Liquid Zimbabwe specific KPIs  
        "priority_kpis": ["RACH_Success_Rate", "IBLER", "Throughput_DL", "Throughput_UL"],
        "weight_adjustments": {
            "rach_success": 0.3,
            "throughput": 0.4, 
            "interference": 0.3
        }
    }
}

def load_enhanced_config() -> Dict:
    """Load configuration with Liquid Zimbabwe enhancements"""
    try:
        # Load base config
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Add LZ config if not present
        if 'liquid_zimbabwe' not in config:
            config.update(LZ_CONFIG)
            
        return config
    except Exception as e:
        print(f"Warning: Could not load enhanced config: {e}")
        # Fallback to basic config
        with open('config.yaml', 'r') as f:
            return yaml.safe_load(f)

def is_liquid_zimbabwe_enabled() -> bool:
    """Check if LZ integration is enabled"""
    try:
        config = load_enhanced_config()
        return config.get('liquid_zimbabwe', {}).get('enabled', False)
    except:
        return False