#!/usr/bin/env python3
"""
Test the exact Postman command that worked
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add the liquid-4g-core directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "liquid-4g-core"))

# Load environment variables
load_dotenv()

def test_exact_postman_command():
    """Test the exact command that worked in Postman"""
    print("🧪 Testing exact Postman command...")
    
    try:
        from agents.huawei_api_client import HuaweiAPIClient
        
        # Set environment variables that the API client expects
        os.environ['HUAWEI_API_URL'] = os.getenv('LZ_API_URL', '')
        os.environ['HUAWEI_USERNAME'] = os.getenv('LZ_API_USERNAME', '')
        os.environ['HUAWEI_PASSWORD'] = os.getenv('LZ_API_PASSWORD', '')
        
        client = HuaweiAPIClient()
        
        print(f"📡 Connecting to: {client.base_url}")
        
        # Authenticate
        if client.authenticate():
            print("✅ Authentication successful!")
            
            # Test the exact command from your Postman success
            print("\n🔍 Testing exact Postman command: LST UECOOPERATIONPARA:;")
            
            result = client.execute_mml_command(
                command="LST UECOOPERATIONPARA:;",
                ne_names=["MSH-0112-Bindura Hospital"]
            )
            
            print("✅ Command executed successfully!")
            print(f"📋 Result type: {type(result)}")
            print(f"📋 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            print(f"📄 Full result:")
            print(json.dumps(result, indent=2))
            
            return True
            
        else:
            print("❌ Authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_exact_postman_command()