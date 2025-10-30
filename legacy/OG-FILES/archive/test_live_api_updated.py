#!/usr/bin/env python3
"""
Liquid Zimbabwe Live API Test Script - Updated with Correct Command Syntax
Tests authentication and all 5 core parameters using verified working commands
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
logger = logging.getLogger('LZ-Live-API-Test-Updated')

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

def test_all_parameters(client):
    """Test all 5 core parameters with verified command syntax"""
    print("\n📊 Testing all 5 core parameters...")
    
    if not client:
        print("❌ No authenticated client available")
        return False
    
    try:
        # Use the verified working NE
        test_ne = "MSH-0112-Bindura Hospital"
        print(f"🔍 Testing parameter queries for: {test_ne}")
        
        # Test each parameter with correct command syntax from Configurations.txt
        parameter_tests = [
            {
                "name": "Reference Signal Power (RS Power)",
                "command": "LST PDSCHCFG:;",
                "range": "-600 to 500 (0.1 dBm units)",
                "description": "Controls cell coverage area"
            },
            {
                "name": "A3 Event Offset (Handover Threshold)", 
                "command": "LST UECOOPERATIONPARA:;",
                "range": "dB0 to dB15",
                "description": "Intra-frequency handover sensitivity"
            },
            {
                "name": "T310 Timer (RLF Detection)",
                "command": "LST UETIMERCONST:;", 
                "range": "Timer constants (e.g., MS1000_T310)",
                "description": "Radio Link Failure detection timing"
            },
            {
                "name": "P0_NominalPUSCH (UL Power Control)",
                "command": "LST CELLULPCCOMM:;",
                "range": "-126 to 24",
                "description": "Uplink power control optimization"
            },
            {
                "name": "PDCCH Aggregation Level",
                "command": "LST CELLUSPARACFG:;",
                "range": "0 to 30",
                "description": "Control channel robustness"
            }
        ]
        
        success_count = 0
        results_summary = {}
        
        for i, param in enumerate(parameter_tests, 1):
            try:
                print(f"\n📋 Test {i}/5: {param['name']}")
                print(f"   Command: {param['command']}")
                print(f"   Range: {param['range']}")
                print(f"   Purpose: {param['description']}")
                
                # Execute the MML command directly
                result = client.execute_mml_command(
                    command=param['command'],
                    ne_names=[test_ne]
                )
                
                if result and isinstance(result, dict):
                    if 'results' in result and len(result['results']) > 0:
                        ret_code = result['results'][0].get('retCode', -1)
                        has_report = 'report' in result['results'][0]
                        
                        if ret_code == 0:
                            print(f"   ✅ SUCCESS! (retCode: 0)")
                            print(f"   📊 Has detailed report: {has_report}")
                            
                            # Extract cell count from report if available
                            if has_report:
                                report = result['results'][0]['report']
                                # Count cells by looking for "Number of results" or cell entries
                                if "Number of results" in report:
                                    import re
                                    match = re.search(r'Number of results = (\d+)', report)
                                    if match:
                                        cell_count = match.group(1)
                                        print(f"   📱 Cells found: {cell_count}")
                            
                            results_summary[param['name']] = {
                                'status': '✅ SUCCESS',
                                'retCode': ret_code,
                                'has_data': has_report
                            }
                            success_count += 1
                        else:
                            print(f"   ⚠️ Command executed but returned error (retCode: {ret_code})")
                            results_summary[param['name']] = {
                                'status': '⚠️ ERROR_CODE',
                                'retCode': ret_code
                            }
                    else:
                        print(f"   ⚠️ Empty or malformed results")
                        results_summary[param['name']] = {
                            'status': '⚠️ NO_RESULTS',
                            'retCode': 'N/A'
                        }
                else:
                    print(f"   ⚠️ Unexpected response format")
                    results_summary[param['name']] = {
                        'status': '⚠️ BAD_FORMAT',
                        'response_type': str(type(result))
                    }
                
            except Exception as e:
                print(f"   ❌ FAILED: {e}")
                results_summary[param['name']] = {
                    'status': '❌ EXCEPTION',
                    'error': str(e)
                }
        
        # Print summary
        print(f"\n" + "="*60)
        print(f"📊 PARAMETER TESTING SUMMARY")
        print(f"="*60)
        print(f"Tests passed: {success_count}/{len(parameter_tests)}")
        print(f"Success rate: {(success_count/len(parameter_tests)*100):.1f}%")
        
        print(f"\n📋 Detailed Results:")
        for param_name, result_info in results_summary.items():
            status = result_info['status']
            if 'retCode' in result_info:
                print(f"   {status} {param_name} (retCode: {result_info['retCode']})")
            else:
                print(f"   {status} {param_name}")
        
        return success_count == len(parameter_tests)
            
    except Exception as e:
        print(f"❌ Parameter testing failed: {e}")
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
        return health.get('status') == 'healthy'
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def main():
    """Main test execution"""
    print("🚀 Liquid Zimbabwe Live API Test - UPDATED")
    print("=" * 60)
    print("Testing all 5 core parameters with verified command syntax")
    print("=" * 60)
    
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
    params_ok = test_all_parameters(client)
    
    # Final Summary
    print("\n" + "="*60)
    print("🎯 FINAL TEST SUMMARY")
    print("="*60)
    test_results = [
        ("Environment Loading", "✅ PASS" if env_ok else "❌ FAIL"),
        ("Authentication", "✅ PASS" if client else "❌ FAIL"),
        ("Health Check", "✅ PASS" if health_ok else "❌ FAIL"),
        ("Parameter Queries", "✅ PASS" if params_ok else "❌ FAIL")
    ]
    
    for test_name, result in test_results:
        print(f"{result} {test_name}")
    
    total_passed = sum(1 for _, result in test_results if "PASS" in result)
    total_tests = len(test_results)
    
    print(f"\nOverall Success Rate: {total_passed}/{total_tests} ({(total_passed/total_tests*100):.1f}%)")
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! Live API integration is fully operational.")
        print("📝 Ready for Phase 2 implementation!")
    else:
        print(f"\n⚠️ {total_tests - total_passed} test(s) failed. Please review and fix issues.")

if __name__ == "__main__":
    main()