#!/usr/bin/env python3
"""
Live API Credentials Test Script
Tests authentication and reference power query using .env credentials
"""

import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add the liquid-4g-core directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "liquid-4g-core"))

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('LZ-Live-API-Test')

def test_env_loading():
    """Test if environment variables are properly loaded"""
    print("🔧 Testing environment variable loading...")
    
    # Set environment variables that the API client expects
    os.environ['HUAWEI_API_URL'] = os.getenv('LZ_API_URL', '')
    os.environ['HUAWEI_USERNAME'] = os.getenv('LZ_API_USERNAME', '')
    os.environ['HUAWEI_PASSWORD'] = os.getenv('LZ_API_PASSWORD', '')
    
    api_url = os.getenv('HUAWEI_API_URL')
    username = os.getenv('HUAWEI_USERNAME')
    password = os.getenv('HUAWEI_PASSWORD')
    
    if api_url and username and password:
        print(f"✅ API URL: {api_url}")
        print(f"✅ Username: {username}")
        print(f"✅ Password: {'*' * len(password)}")
        return True
    else:
        print("❌ Missing environment variables")
        return False

def test_authentication():
    """Test live authentication with Huawei iMaster MAE"""
    print("\n🔐 Testing live authentication...")
    
    try:
        from agents.huawei_api_client import HuaweiAPIClient
        
        # Create client (will auto-load from environment variables)
        client = HuaweiAPIClient()
        
        print(f"📡 Connecting to: {client.base_url}")
        print(f"👤 Username: {client.username}")
        
        # Attempt authentication
        auth_success = client.authenticate()
        
        if auth_success:
            print("✅ Authentication successful!")
            print(f"🎫 Token: {client.auth_token[:20]}..." if client.auth_token else "No token")
            print(f"⏰ Expires: {client.token_expires_at}")
            return client
        else:
            print("❌ Authentication failed")
            return None
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_reference_power_query(client):
    """Test querying all 5 core parameters"""
    print("\n📊 Testing parameter queries...")
    
    if not client:
        print("❌ No authenticated client available")
        return False
    
    try:
        # Test network elements list first
        elements = client.get_network_elements()
        print(f"📍 Available network elements: {len(elements)}")
        
        for element in elements[:3]:  # Show first 3
            print(f"   - {element.name} ({element.location})")
        
        if not elements:
            print("❌ No network elements available for testing")
            return False
            
        # Test all 5 parameters using first network element
        test_element = elements[0]
        print(f"\n🔍 Testing parameter queries for: {test_element.name}")
        
        # Get parameter configurations
        param_configs = client.get_parameter_configs()
        
        success_count = 0
        total_params = len(param_configs)
        
        for param_name, config in param_configs.items():
            try:
                print(f"\n📋 Testing {config.parameter_name}...")
                print(f"   Query: {config.query_command}")
                print(f"   Range: {config.value_range}")
                
                # Query the parameter
                result = client.query_parameter(param_name, [test_element.name])
                
                print(f"   ✅ Query successful!")
                print(f"   � Response keys: {list(result.keys()) if isinstance(result, dict) else 'Non-dict response'}")
                
                success_count += 1
                
            except Exception as e:
                print(f"   ❌ Query failed: {e}")
        
        print(f"\n📊 Parameter Query Summary: {success_count}/{total_params} successful")
        return success_count == total_params
            
    except Exception as e:
        print(f"❌ Parameter query test failed: {e}")
        return False

def test_health_check(client):
    """Test API health check"""
    print("\n🏥 Testing API health check...")
    
    if not client:
        print("❌ No authenticated client available")
        return False
    
    try:
        health = client.health_check()
        print("✅ Health check completed!")
        print(f"📋 Health status:")
        print(json.dumps(health, indent=2))
        return health.get('status') == 'healthy'
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def main():
    """Main test execution"""
    print("🚀 Liquid Zimbabwe Live API Test")
    print("=" * 50)
    
    # Test 1: Environment loading
    env_ok = test_env_loading()
    if not env_ok:
        print("\n❌ Environment test failed. Please check your .env file.")
        return
    
    # Test 2: Authentication
    client = test_authentication()
    if not client:
        print("\n❌ Authentication test failed. Please check your credentials.")
        return
    
    # Test 3: Health check
    health_ok = test_health_check(client)
    
    # Test 4: All parameter queries
    query_ok = test_reference_power_query(client)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"✅ Environment Loading: {'PASS' if env_ok else 'FAIL'}")
    print(f"✅ Authentication: {'PASS' if client else 'FAIL'}")
    print(f"✅ Health Check: {'PASS' if health_ok else 'FAIL'}")
    print(f"✅ All Parameter Queries: {'PASS' if query_ok else 'FAIL'}")
    
    if all([env_ok, client, health_ok, query_ok]):
        print("\n🎉 ALL TESTS PASSED! Live API integration ready.")
    else:
        print("\n⚠️ Some tests failed. Please review and fix issues.")

if __name__ == "__main__":
    main()