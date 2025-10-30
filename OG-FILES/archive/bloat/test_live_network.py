#!/usr/bin/env python3
"""
Test script for Huawei iMaster MAE API integration
Run this script to validate the API connection and basic functionality
"""

import sys
import os
import time
from datetime import datetime

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_api_authentication():
    """Test basic API authentication"""
    print("\n=== Testing API Authentication ===")
    
    try:
        from agentic_llm_workflow.huawei_api_client import HuaweiAPIClient
        
        # Initialize client with your credentials
        client = HuaweiAPIClient(
            base_url="https://41.174.191.214:31127",
            username="cassava.ai", 
            password="#Pass123#"
        )
        
        print("✓ API client initialized")
        
        # Test authentication
        if client.authenticate():
            print("✓ Authentication successful")
            print(f"✓ Token expires at: {client.token_expires_at}")
            return True
        else:
            print("✗ Authentication failed")
            return False
            
    except Exception as e:
        print(f"✗ Error during authentication test: {e}")
        return False

def test_network_elements():
    """Test network element listing"""
    print("\n=== Testing Network Elements ===")
    
    try:
        from agentic_llm_workflow.huawei_api_client import HuaweiAPIClient
        
        client = HuaweiAPIClient(
            base_url="https://41.174.191.214:31127",
            username="cassava.ai",
            password="#Pass123#"
        )
        
        if not client.authenticate():
            print("✗ Authentication failed")
            return False
        
        # Get network elements
        elements = client.get_network_elements()
        print(f"✓ Found {len(elements)} network elements:")
        
        for ne in elements:
            print(f"  - {ne.name} ({ne.location})")
            print(f"    Site ID: {ne.site_id}, Cells: {ne.cell_ids}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing network elements: {e}")
        return False

def test_parameter_query():
    """Test parameter querying"""
    print("\n=== Testing Parameter Query ===")
    
    try:
        from agentic_llm_workflow.huawei_api_client import HuaweiAPIClient
        
        client = HuaweiAPIClient(
            base_url="https://41.174.191.214:31127",
            username="cassava.ai",
            password="#Pass123#"
        )
        
        if not client.authenticate():
            print("✗ Authentication failed")
            return False
        
        # Test parameter query (read-only, safe to test)
        test_ne = "MSH-0112-Bindura Hospital"  # From your NE Names.txt
        print(f"✓ Testing parameter query on: {test_ne}")
        
        try:
            result = client.query_parameter("reference_signal_power", [test_ne])
            print("✓ Parameter query successful")
            print(f"  Result type: {type(result)}")
            print(f"  Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            return True
            
        except Exception as e:
            print(f"✗ Parameter query failed: {e}")
            print("  This might be expected if the network element is not accessible")
            return False
        
    except Exception as e:
        print(f"✗ Error during parameter query test: {e}")
        return False

def test_live_network_manager():
    """Test the live network manager"""
    print("\n=== Testing Live Network Manager ===")
    
    try:
        from agentic_llm_workflow.live_network_manager import LiveNetworkManager
        
        manager = LiveNetworkManager()
        print("✓ Live network manager initialized")
        
        # Test network status check
        print("Testing network status check...")
        status = manager.check_network_status(print_output=True)
        
        if status:
            print("✓ Network status check passed")
        else:
            print("✗ Network status check failed")
        
        return status
        
    except Exception as e:
        print(f"✗ Error testing live network manager: {e}")
        return False

def test_database_operations():
    """Test database initialization and operations"""
    print("\n=== Testing Database Operations ===")
    
    try:
        from agentic_llm_workflow.live_network_manager import LiveNetworkManager
        
        manager = LiveNetworkManager()
        
        # Test database connection
        import sqlite3
        with sqlite3.connect(manager.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print(f"✓ Database connected: {manager.db_path}")
            print(f"✓ Found {len(tables)} tables: {[t[0] for t in tables]}")
            
            # Check network elements
            cursor.execute("SELECT COUNT(*) FROM network_elements")
            ne_count = cursor.fetchone()[0]
            print(f"✓ Network elements in database: {ne_count}")
            
        return True
        
    except Exception as e:
        print(f"✗ Error testing database operations: {e}")
        return False

def main():
    """Run all tests"""
    print("Huawei iMaster MAE API Integration Tests")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    
    tests = [
        ("API Authentication", test_api_authentication),
        ("Network Elements", test_network_elements), 
        ("Parameter Query", test_parameter_query),
        ("Live Network Manager", test_live_network_manager),
        ("Database Operations", test_database_operations)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\nRunning: {test_name}")
            success = test_func()
            results.append((test_name, success))
            
        except KeyboardInterrupt:
            print("\n\nTests interrupted by user")
            break
        except Exception as e:
            print(f"✗ Unexpected error in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name:.<30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Live network integration is ready.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
        print("\nCommon issues:")
        print("- Network connectivity to iMaster MAE server")
        print("- Authentication credentials")
        print("- Network element accessibility")
        print("- Missing dependencies")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)