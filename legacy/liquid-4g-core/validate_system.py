#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Network - Comprehensive System Validation
Database-driven system testing with live network validation
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add the liquid-4g-core directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "liquid-4g-core"))

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise for cleaner output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('LZ-System-Validation')

def test_environment_setup():
    """Test environment variables and setup"""
    print("🔧 Testing environment setup...")
    
    try:
        required_vars = ['LZ_API_URL', 'LZ_API_USERNAME', 'LZ_API_PASSWORD']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            return False
        
        print("✅ All required environment variables present")
        return True
        
    except Exception as e:
        print(f"❌ Environment setup test failed: {e}")
        return False

def test_database_integration():
    """Test database helper integration"""
    print("\n📊 Testing database integration...")
    
    try:
        from utils import (
            get_live_active_sites, 
            get_database_stats,
            LZDatabaseHelper
        )
        
        # Test database helper
        db_helper = LZDatabaseHelper()
        stats = db_helper.get_database_stats()
        
        print(f"✅ Database connection successful")
        print(f"   📈 Total sites in database: {stats.get('total_sites', 0)}")
        print(f"   🟢 Live active sites: {stats.get('live_active_count', 0)}")
        print(f"   📱 Total live cells: {stats.get('total_live_cells', 0)}")
        
        # Test live active sites retrieval
        live_sites = get_live_active_sites()
        if len(live_sites) > 0:
            print(f"✅ Successfully retrieved {len(live_sites)} live active sites")
            for name, info in live_sites.items():
                print(f"   🟢 {name} ({info['location']})")
            return True
        else:
            print("⚠️ No live active sites found in database")
            return False
            
    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        return False

def test_api_client_initialization():
    """Test API client with database integration"""
    print("\n🔌 Testing API client initialization...")
    
    try:
        from agents.huawei_api_client import HuaweiAPIClient
        
        # Set environment variables
        os.environ['HUAWEI_API_URL'] = os.getenv('LZ_API_URL', '')
        os.environ['HUAWEI_USERNAME'] = os.getenv('LZ_API_USERNAME', '')
        os.environ['HUAWEI_PASSWORD'] = os.getenv('LZ_API_PASSWORD', '')
        
        # Initialize API client
        client = HuaweiAPIClient()
        elements = client.get_network_elements()
        
        print(f"✅ API client initialized successfully")
        print(f"   📡 Loaded {len(elements)} network elements from database")
        
        for element in elements:
            print(f"   🟢 {element.name} ({element.location}) - {len(element.cell_ids)} cells")
        
        return True, client
        
    except Exception as e:
        print(f"❌ API client initialization failed: {e}")
        return False, None

def test_live_network_authentication(client):
    """Test live network authentication"""
    print("\n🔐 Testing live network authentication...")
    
    try:
        if client.authenticate():
            print("✅ Live network authentication successful")
            return True
        else:
            print("❌ Live network authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def test_parameter_queries(client):
    """Test all 5 core parameter queries"""
    print("\n📊 Testing parameter queries...")
    
    try:
        elements = client.get_network_elements()
        if not elements:
            print("❌ No network elements available for testing")
            return False
        
        # Test site - use first available
        test_site = elements[0]
        print(f"🎯 Testing with: {test_site.name}")
        
        # Define all 5 core parameters
        parameters = [
            ("Reference Signal Power", "LST PDSCHCFG:;"),
            ("A3 Event Offset", "LST UECOOPERATIONPARA:;"),
            ("T310 Timer", "LST UETIMERCONST:;"),
            ("P0_NominalPUSCH", "LST CELLULPCCOMM:;"),
            ("PDCCH Aggregation", "LST CELLUSPARACFG:;")
        ]
        
        successful_queries = 0
        for param_name, command in parameters:
            try:
                result = client.execute_mml_command(
                    command=command,
                    ne_names=[test_site.name]
                )
                
                if result and isinstance(result, dict) and 'results' in result:
                    if len(result['results']) > 0:
                        ret_code = result['results'][0].get('retCode', -1)
                        if ret_code == 0:
                            print(f"   ✅ {param_name}: Working")
                            successful_queries += 1
                        else:
                            print(f"   ❌ {param_name}: Error (retCode: {ret_code})")
                    else:
                        print(f"   ❌ {param_name}: Empty response")
                else:
                    print(f"   ❌ {param_name}: Invalid response format")
                    
            except Exception as e:
                print(f"   ❌ {param_name}: Exception - {e}")
        
        success_rate = (successful_queries / len(parameters)) * 100
        print(f"\n📈 Parameter Query Results: {successful_queries}/{len(parameters)} successful ({success_rate:.1f}%)")
        
        return successful_queries == len(parameters)
        
    except Exception as e:
        print(f"❌ Parameter queries test failed: {e}")
        return False

def test_multi_site_capability(client):
    """Test multi-site operations"""
    print("\n🌐 Testing multi-site capabilities...")
    
    try:
        elements = client.get_network_elements()
        if len(elements) < 2:
            print("⚠️ Only 1 site available, skipping multi-site test")
            return True
        
        print(f"🎯 Testing with {len(elements)} sites...")
        
        # Test with all sites
        site_names = [element.name for element in elements]
        result = client.execute_mml_command(
            command="LST PDSCHCFG:;",
            ne_names=site_names
        )
        
        if result and isinstance(result, dict) and 'results' in result:
            successful_sites = sum(1 for r in result['results'] if r.get('retCode', -1) == 0)
            print(f"✅ Multi-site query successful: {successful_sites}/{len(site_names)} sites responded")
            return successful_sites > 0
        else:
            print("❌ Multi-site query failed")
            return False
            
    except Exception as e:
        print(f"❌ Multi-site test failed: {e}")
        return False

def test_system_health():
    """Test overall system health"""
    print("\n🏥 Testing system health...")
    
    try:
        from utils import get_database_stats
        
        # Database health
        stats = get_database_stats()
        db_health = stats.get('live_active_count', 0) > 0
        
        # Check if required directories exist
        required_dirs = [
            Path("liquid-4g-core"),
            Path("liquid-4g-core/agents"),
            Path("liquid-4g-core/utils"),
            Path("data")
        ]
        
        dir_health = all(d.exists() for d in required_dirs)
        
        # Check if database file exists
        db_file = Path("data/live_network.db")
        db_file_health = db_file.exists()
        
        print(f"✅ Database health: {'OK' if db_health else 'ISSUES'}")
        print(f"✅ Directory structure: {'OK' if dir_health else 'ISSUES'}")
        print(f"✅ Database file: {'OK' if db_file_health else 'MISSING'}")
        
        overall_health = db_health and dir_health and db_file_health
        print(f"🏥 Overall system health: {'HEALTHY' if overall_health else 'NEEDS ATTENTION'}")
        
        return overall_health
        
    except Exception as e:
        print(f"❌ System health test failed: {e}")
        return False

async def run_comprehensive_validation():
    """Run all validation tests"""
    print("🚀 Starting Liquid Zimbabwe 4G Network System Validation")
    print("=" * 70)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    test_results = []
    
    # Test sequence
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Database Integration", test_database_integration), 
        ("System Health", test_system_health),
        ("API Client Initialization", lambda: test_api_client_initialization()[0]),
        ("Live Network Authentication", lambda: test_live_network_authentication(client) if client else False),
        ("Parameter Queries", lambda: test_parameter_queries(client) if client else False),
        ("Multi-site Capabilities", lambda: test_multi_site_capability(client) if client else False),
    ]
    
    client = None
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            if test_name == "API Client Initialization":
                success, client = test_api_client_initialization()
            else:
                success = test_func()
            
            test_results.append((test_name, success))
            
            if not success and test_name in ["Environment Setup", "Database Integration"]:
                print(f"⚠️ Critical test '{test_name}' failed. Stopping validation.")
                break
                
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {str(e)}")
            test_results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("🎯 SYSTEM VALIDATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "-" * 70)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All system validation tests passed!")
        print("✅ Database-driven architecture operational")
        print("✅ Live network connectivity confirmed")
        print("✅ Parameter queries functional")
        print("✅ Multi-site capabilities verified")
        print("\n📝 System is ready for production operations!")
    else:
        print(f"\n⚠️ {total - passed} tests failed.")
        print("🔧 Please review and resolve issues before proceeding to production.")
        
        # Provide specific guidance based on failures
        failed_tests = [name for name, result in test_results if not result]
        
        if "Environment Setup" in failed_tests:
            print("\n💡 Environment Setup Issues:")
            print("   • Check that .env file exists with LZ_API_URL, LZ_API_USERNAME, LZ_API_PASSWORD")
            
        if "Database Integration" in failed_tests:
            print("\n💡 Database Issues:")
            print("   • Ensure data/live_network.db exists")
            print("   • Run database setup/initialization if needed")
            
        if "Live Network Authentication" in failed_tests:
            print("\n💡 Network Issues:")
            print("   • Verify API credentials are correct")
            print("   • Check network connectivity to Huawei iMaster MAE")
    
    return passed == total

if __name__ == "__main__":
    print("🔍 Liquid Zimbabwe 4G Network - Comprehensive System Validation")
    
    try:
        # Run validation
        success = asyncio.run(run_comprehensive_validation())
        
        exit_code = 0 if success else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n🛑 Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation execution failed: {str(e)}")
        sys.exit(1)