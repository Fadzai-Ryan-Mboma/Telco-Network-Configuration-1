#!/usr/bin/env python3
"""
Test Huawei API Connectivity

Test the actual connection to the Huawei iMaster MAE API.
"""

import sys
import os
sys.path.insert(0, 'src')

from liquid4g.infrastructure.api.huawei_client import get_huawei_client
from liquid4g.core.config import get_settings

def test_huawei_api():
    """Test Huawei API connectivity"""
    
    print("🔌 Testing Huawei API Connectivity...")
    print("=" * 50)
    
    # Show configuration
    settings = get_settings()
    print(f"📋 Configuration:")
    print(f"   • API URL: {settings.huawei_api_url}")
    print(f"   • Username: {settings.huawei_username}")
    print(f"   • SSL Verify: {settings.huawei_ssl_verify}")
    print()
    
    try:
        # Get API client
        print("🔧 Initializing Huawei API client...")
        client = get_huawei_client()
        print("✅ API client initialized")
        
        # Test authentication
        print("🔐 Testing authentication...")
        token = client.authenticate()
        print(f"✅ Authentication successful!")
        print(f"   Token: {token[:20]}...{token[-10:]}")
        print()
        
        # Test health check
        print("🏥 Testing health check...")
        if client.health_check():
            print("✅ Health check passed - API is responding")
        else:
            print("⚠️ Health check failed - API might be having issues")
        print()
        
        # Test basic MML command with working format from API Use.txt
        print("📡 Testing basic MML command...")
        try:
            result = client.execute_mml_command("LST UECOOPERATIONPARA:;")
            print("✅ MML command successful!")
            print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            if isinstance(result, dict) and 'results' in result:
                print(f"   Results count: {len(result['results'])}")
                if result['results']:
                    print(f"   First result retCode: {result['results'][0].get('retCode')}")
        except Exception as e:
            print(f"⚠️ MML command failed: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Huawei API Test Complete!")
        
    except Exception as e:
        print(f"❌ Huawei API test failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("   • Check network connectivity to Huawei server")
        print("   • Verify credentials are correct")
        print("   • Check if SSL certificate is valid")
        print("   • Ensure firewall allows connection to port 31127")

if __name__ == "__main__":
    test_huawei_api()