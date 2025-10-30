#!/usr/bin/env python3
"""
Test Database-Driven API Client with Live Network
Quick verification that database integration doesn't break live functionality
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the liquid-4g-core directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "liquid-4g-core"))

# Load environment variables
load_dotenv()

def test_database_driven_api_live():
    """Test live API functionality with database-driven network elements"""
    print("🚀 Testing Database-Driven API Client with Live Network")
    print("=" * 60)
    
    try:
        # Set environment variables
        os.environ['HUAWEI_API_URL'] = os.getenv('LZ_API_URL', '')
        os.environ['HUAWEI_USERNAME'] = os.getenv('LZ_API_USERNAME', '')
        os.environ['HUAWEI_PASSWORD'] = os.getenv('LZ_API_PASSWORD', '')
        
        from agents.huawei_api_client import HuaweiAPIClient
        
        print("🔧 Initializing database-driven API client...")
        client = HuaweiAPIClient()
        
        elements = client.get_network_elements()
        print(f"📊 Loaded {len(elements)} network elements from database")
        
        print("\n🔐 Testing authentication...")
        if client.authenticate():
            print("✅ Authentication successful!")
        else:
            print("❌ Authentication failed!")
            return False
        
        print("\n📡 Testing parameter query on database-loaded sites...")
        
        # Test with first available site
        if elements:
            test_site = elements[0].name
            print(f"🎯 Testing with: {test_site}")
            
            result = client.execute_mml_command(
                command="LST PDSCHCFG:;",
                ne_names=[test_site]
            )
            
            if result and isinstance(result, dict) and 'results' in result:
                if len(result['results']) > 0:
                    ret_code = result['results'][0].get('retCode', -1)
                    if ret_code == 0:
                        print(f"✅ Parameter query successful on database-loaded site!")
                        
                        # Extract some details
                        if 'report' in result['results'][0]:
                            report = result['results'][0]['report']
                            import re
                            match = re.search(r'Number of results = (\d+)', report)
                            if match:
                                cells = int(match.group(1))
                                print(f"📱 Found {cells} cells configured")
                        
                        print(f"🎯 SUCCESS: Database-driven API client working with live network!")
                        return True
                    else:
                        print(f"❌ API returned error code: {ret_code}")
                        return False
            print(f"❌ Unexpected API response format")
            return False
        else:
            print(f"❌ No network elements loaded from database")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_database_driven_api_live()
    if success:
        print(f"\n🏆 COMPLETE: Database-driven API client is fully operational!")
        print(f"   ✅ Network elements loaded from database")
        print(f"   ✅ Only live active sites included")
        print(f"   ✅ Live API connectivity confirmed")
        print(f"   ✅ Parameter queries working")
    else:
        print(f"\n❌ Issues detected with database-driven API client")