#!/usr/bin/env python3
"""
Test Database Integration in API Client
Verify that the API client correctly loads network elements from database
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

def test_api_client_database_integration():
    """Test that API client loads from database correctly"""
    print("🔍 Testing API Client Database Integration")
    print("=" * 50)
    
    try:
        # Set environment variables
        os.environ['HUAWEI_API_URL'] = os.getenv('LZ_API_URL', '')
        os.environ['HUAWEI_USERNAME'] = os.getenv('LZ_API_USERNAME', '')
        os.environ['HUAWEI_PASSWORD'] = os.getenv('LZ_API_PASSWORD', '')
        
        from agents.huawei_api_client import HuaweiAPIClient
        
        print("🚀 Initializing API Client...")
        client = HuaweiAPIClient()
        
        print("📡 Checking loaded network elements...")
        elements = client.get_network_elements()
        
        print(f"✅ Loaded {len(elements)} network elements:")
        for element in elements:
            print(f"   🟢 {element.name}")
            print(f"      📍 Location: {element.location}")
            print(f"      🏢 Site ID: {element.site_id}")
            print(f"      📱 Cells: {len(element.cell_ids)} cells")
        
        # Verify these are from database (should only be live_active ones)
        from database_helper import get_live_active_site_names
        db_sites = get_live_active_site_names()
        api_sites = [element.name for element in elements]
        
        print(f"\n🔍 Database vs API Client Comparison:")
        print(f"   📊 Database Live Active Sites: {len(db_sites)}")
        print(f"   📊 API Client Loaded Sites: {len(api_sites)}")
        
        matches = set(db_sites) == set(api_sites)
        if matches:
            print(f"   ✅ Perfect match! API client loaded from database")
        else:
            print(f"   ⚠️ Mismatch detected:")
            print(f"      Database: {sorted(db_sites)}")
            print(f"      API Client: {sorted(api_sites)}")
        
        return matches
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_api_client_database_integration()
    if success:
        print(f"\n🎯 SUCCESS: API Client is now database-driven!")
    else:
        print(f"\n❌ FAILURE: API Client database integration needs fixing")