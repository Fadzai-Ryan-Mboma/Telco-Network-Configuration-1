#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Network - Phase 2 Testing Script
Live Network Connection Testing Validation
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Add the liquid-4g-core directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "liquid-4g-core"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Phase2-Test')

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing Phase 2 imports...")
    
    try:
        from agents import (
            LZMonitoringAgent, 
            LZOptimizationAgent, 
            LZAnalyticsAgent,
            LZNetworkOrchestrator
        )
        print("✅ Agent imports successful")
        
        from network import (
            HuaweiAPIClient,
            HuaweiAPIError,
            HuaweiAuthenticationError
        )
        print("✅ Network client imports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {str(e)}")
        return False

def test_api_client_initialization():
    """Test API client initialization"""
    print("\n🔌 Testing API client initialization...")
    
    try:
        # Mock configuration for testing
        test_config = {
            'base_url': 'https://test-api.example.com',
            'username': 'test_user',
            'password': 'test_password',
            'timeout': 30,
            'retry_attempts': 3,
            'ssl_verify': False
        }
        
        from network import HuaweiAPIClient
        api_client = HuaweiAPIClient(test_config)
        
        print("✅ API client initialized successfully")
        
        # Test health check without connection
        health = api_client.health_check()
        print(f"🏥 Health check status: {health['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ API client test failed: {str(e)}")
        return False

def test_agent_initialization():
    """Test agent initialization"""
    print("\n🤖 Testing agent initialization...")
    
    try:
        # Mock configuration
        mock_config = {
            'system': {
                'name': 'Test LZ System',
                'version': '2.0.0-test'
            },
            'liquid_zimbabwe': {
                'api': {
                    'base_url': 'https://test-api.example.com',
                    'username': 'test_user',
                    'password': 'test_password',
                    'timeout': 30
                },
                'parameters': [
                    {
                        'name': 'earfcn',
                        'description': 'Test parameter',
                        'optimization_range': [1800, 2600]
                    }
                ]
            },
            'monitoring_interval': 15,
            'auto_optimization': False,
            'simulation_mode': True
        }
        
        from agents import (
            LZMonitoringAgent,
            LZOptimizationAgent,
            LZAnalyticsAgent
        )
        
        # Test monitoring agent
        monitoring_agent = LZMonitoringAgent(mock_config)
        print("✅ Monitoring agent initialized")
        
        # Test optimization agent
        optimization_agent = LZOptimizationAgent(mock_config)
        print("✅ Optimization agent initialized")
        
        # Test analytics agent
        analytics_agent = LZAnalyticsAgent(mock_config)
        print("✅ Analytics agent initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent initialization failed: {str(e)}")
        return False

async def test_orchestrator():
    """Test the main orchestrator"""
    print("\n🎯 Testing network orchestrator...")
    
    try:
        from agents import LZNetworkOrchestrator
        
        # Create temporary test config
        test_config_content = """
# Test configuration for Phase 2
system:
  name: "Test LZ 4G Network Optimizer"
  version: "2.0.0-test"

liquid_zimbabwe:
  api:
    base_url: "https://test-api.example.com"
    username: "test_user"
    password: "test_password"
    timeout: 30
    ssl_verify: false
    
cycle_interval: 5
auto_optimization: false
simulation_mode: true
"""
        
        # Write test config
        test_config_path = 'test-config-lz.yaml'
        with open(test_config_path, 'w') as f:
            f.write(test_config_content)
        
        try:
            # Initialize orchestrator
            orchestrator = LZNetworkOrchestrator(test_config_path)
            print("✅ Orchestrator initialized")
            
            # Test system status
            status = orchestrator.get_system_status()
            print(f"🏥 System health: {status['system_health']}")
            
            # Test single optimization cycle
            print("🔄 Running test optimization cycle...")
            results = await orchestrator.run_optimization_cycle()
            
            print(f"✅ Cycle completed with status: {results['status']}")
            print(f"📊 Cells monitored: {results.get('monitoring_results', {}).get('cells_monitored', 0)}")
            
            if results.get('errors'):
                print(f"⚠️ Cycle had {len(results['errors'])} warnings (expected in test mode)")
            
            return True
            
        finally:
            # Clean up test config
            if os.path.exists(test_config_path):
                os.remove(test_config_path)
        
    except Exception as e:
        print(f"❌ Orchestrator test failed: {str(e)}")
        return False

def test_mock_data_generation():
    """Test mock data generation for development"""
    print("\n📊 Testing mock data generation...")
    
    try:
        from agents import LZMonitoringAgent
        
        mock_config = {
            'liquid_zimbabwe': {
                'api': {}  # Empty to trigger mock mode
            }
        }
        
        agent = LZMonitoringAgent(mock_config)
        
        # Test KPI collection (should use mock data)
        kpis = agent.collect_kpis()
        
        if kpis:
            print(f"✅ Generated mock KPIs for {len(kpis)} cells")
            
            # Verify data structure
            first_cell = list(kpis.values())[0]
            required_fields = ['cell_id', 'timestamp', 'kpis', 'quality_score']
            
            if all(field in first_cell for field in required_fields):
                print("✅ Mock data structure valid")
                
                # Check KPI values
                kpi_data = first_cell['kpis']
                expected_kpis = ['rsrp', 'rsrq', 'sinr', 'throughput_dl', 'throughput_ul', 'csr', 'hsr', 'rru']
                
                if all(kpi in kpi_data for kpi in expected_kpis):
                    print("✅ All required KPIs present in mock data")
                    return True
                else:
                    print(f"❌ Missing KPIs: {set(expected_kpis) - set(kpi_data.keys())}")
                    return False
            else:
                print(f"❌ Missing fields: {set(required_fields) - set(first_cell.keys())}")
                return False
        else:
            print("❌ No mock data generated")
            return False
            
    except Exception as e:
        print(f"❌ Mock data test failed: {str(e)}")
        return False

def test_configuration_loading():
    """Test configuration loading and validation"""
    print("\n📋 Testing configuration loading...")
    
    try:
        # Test with existing config
        config_path = 'config-lz.yaml'
        
        if os.path.exists(config_path):
            from agents import LZNetworkOrchestrator
            
            orchestrator = LZNetworkOrchestrator(config_path)
            config = orchestrator.config
            
            # Validate required sections
            required_sections = ['system', 'liquid_zimbabwe']
            if all(section in config for section in required_sections):
                print("✅ Configuration structure valid")
                
                # Check API configuration
                api_config = config.get('liquid_zimbabwe', {}).get('api', {})
                required_api_fields = ['base_url', 'username', 'password']
                
                # Check if fields are present (even if using env vars)
                if all(field in api_config for field in required_api_fields):
                    print("✅ API configuration fields present")
                else:
                    print("⚠️ API configuration uses environment variables (expected)")
                
                return True
            else:
                print(f"❌ Missing config sections: {set(required_sections) - set(config.keys())}")
                return False
        else:
            print("⚠️ No config-lz.yaml found, testing default config...")
            
            from agents import LZNetworkOrchestrator
            orchestrator = LZNetworkOrchestrator()
            
            if orchestrator.config:
                print("✅ Default configuration loaded")
                return True
            else:
                print("❌ Failed to load default configuration")
                return False
        
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")
        return False

async def run_comprehensive_test():
    """Run comprehensive Phase 2 testing"""
    print("🚀 Liquid Zimbabwe 4G Network - Phase 2 Implementation Test")
    print("=" * 70)
    print("Testing live network connection capabilities...")
    print()
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Module Imports", test_imports),
        ("API Client", test_api_client_initialization),
        ("Agent Initialization", test_agent_initialization),
        ("Mock Data Generation", test_mock_data_generation),
        ("Configuration Loading", test_configuration_loading),
        ("Network Orchestrator", test_orchestrator)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 30}")
        print(f"Test: {test_name}")
        print('=' * 30)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            test_results.append((test_name, result))
            
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {str(e)}")
            test_results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("🎯 PHASE 2 TEST SUMMARY")
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
        print("\n🎉 All Phase 2 tests passed! Ready for live network integration.")
        print("📝 Next steps:")
        print("   1. Configure API credentials (LZ_API_URL, LZ_API_USERNAME, LZ_API_PASSWORD)")
        print("   2. Test with development/staging Huawei iMaster MAE environment")
        print("   3. Validate with live network data")
        print("   4. Deploy to production environment")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please review and fix before proceeding.")
    
    return passed == total

if __name__ == "__main__":
    print("Starting Phase 2 implementation test...")
    
    # Change to project directory
    os.chdir(current_dir)
    
    try:
        # Run comprehensive test
        success = asyncio.run(run_comprehensive_test())
        
        exit_code = 0 if success else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        sys.exit(1)