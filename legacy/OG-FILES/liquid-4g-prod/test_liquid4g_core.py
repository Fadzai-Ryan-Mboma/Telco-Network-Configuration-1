#!/usr/bin/env python3
"""
Test the liquid-4g-core API client to understand the working implementation
"""

import sys
import os
from pathlib import Path

# Add liquid-4g-core to path
sys.path.insert(0, '/Users/fadzai/Library/CloudStorage/OneDrive-LiquidIntelligentTechnologies/Documents/Cassava AI/Telco-Network-Config/Telco-Network-Configuration/liquid-4g-core')

# Set environment variables
os.environ['HUAWEI_API_URL'] = 'https://41.174.191.214:31127'
os.environ['HUAWEI_USERNAME'] = 'cassava.ai'
os.environ['HUAWEI_PASSWORD'] = '#Pass123#'

try:
    from agents.huawei_api_client import HuaweiAPIClient
    
    print("🔌 Testing liquid-4g-core Huawei API Client...")
    print("=" * 60)
    
    # Initialize client
    client = HuaweiAPIClient()
    
    # Test authentication
    print("🔐 Testing authentication...")
    auth_result = client.authenticate()
    print(f"   Authentication: {'✅ Success' if auth_result else '❌ Failed'}")
    
    if auth_result:
        print(f"   Token: {client.auth_token[:20]}...{client.auth_token[-10:]}")
        
        # Test MML command
        print("\n📡 Testing MML command...")
        try:
            result = client.execute_mml_command(
                "DSP VERSION;", 
                ["MSH-0112-Bindura Hospital"]
            )
            print("✅ MML command successful!")
            print(f"   Result: {result}")
        except Exception as e:
            print(f"❌ MML command failed: {e}")
            
except Exception as e:
    print(f"❌ Failed to test liquid-4g-core client: {e}")
    import traceback
    traceback.print_exc()