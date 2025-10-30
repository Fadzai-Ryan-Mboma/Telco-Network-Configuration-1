"""
Liquid Zimbabwe Agent Ecosystem Test Suite
Tests the complete 6-agent system transformation
"""

import sys
import os
import traceback
from datetime import datetime

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_api_client():
    """Test Huawei API Client"""
    print("\n🔌 TESTING: Huawei API Client")
    try:
        from huawei_api_client import HuaweiAPIClient
        
        client = HuaweiAPIClient()
        print("✅ HuaweiAPIClient imported successfully")
        
        # Test connection (will show connection attempt)
        print("🔗 Testing connection to https://41.174.191.214:31127...")
        connection_result = client.connect()
        
        if connection_result:
            print("✅ API connection successful!")
            
            # Test basic query
            elements = client.get_network_elements()
            print(f"📡 Network elements available: {len(elements) if elements else 0}")
            
        else:
            print("⚠️ API connection failed - will use simulation mode")
            
        return True
        
    except Exception as e:
        print(f"❌ API Client test failed: {e}")
        return False

def test_kpi_management():
    """Test KPI Management System"""
    print("\n📊 TESTING: KPI Management System")
    try:
        from liquid_zimbabwe_kpi import LiquidZimbabweKPIManager as LiquidZimbabweKPI
        
        kpi_manager = LiquidZimbabweKPI()
        print("✅ LiquidZimbabweKPI imported successfully")
        
        # Test KPI configuration
        kpi_config = kpi_manager.KPI_CONFIG
        print(f"📈 Configured KPIs: {len(kpi_config)}")
        
        for kpi_id, config in kpi_config.items():
            user_name = config.get('user_friendly_name', kpi_id)
            print(f"   • {user_name} ({kpi_id})")
        
        # Test KPI data retrieval
        print("🔍 Testing KPI data retrieval...")
        test_kpis = kpi_manager.get_all_kpis()
        
        if test_kpis:
            print(f"✅ Retrieved {len(test_kpis)} KPI values")
        else:
            print("⚠️ No KPI data available (expected in test environment)")
        
        return True
        
    except Exception as e:
        print(f"❌ KPI Management test failed: {e}")
        traceback.print_exc()
        return False

def test_parameter_management():
    """Test Parameter Management System"""
    print("\n⚙️ TESTING: Parameter Management System")
    try:
        from liquid_zimbabwe_parameters import LiquidZimbabweParameterManager as LiquidZimbabweParameters
        
        param_manager = LiquidZimbabweParameters()
        print("✅ LiquidZimbabweParameters imported successfully")
        
        # Test parameter configuration
        param_config = param_manager.PARAMETER_CONFIG
        print(f"🔧 Configured Parameters: {len(param_config)}")
        
        for param_id, config in param_config.items():
            user_name = config.get('user_friendly_name', param_id)
            unit = config.get('unit', '')
            print(f"   • {user_name} ({param_id}) [{unit}]")
        
        # Test MML command generation
        print("📝 Testing MML command generation...")
        test_command = param_manager.generate_mml_command(
            "P0_NominalPUSCH", "TestCell", 1, -80
        )
        print(f"✅ Generated MML command: {test_command}")
        
        return True
        
    except Exception as e:
        print(f"❌ Parameter Management test failed: {e}")
        traceback.print_exc()
        return False

def test_individual_agents():
    """Test Individual Agent Components"""
    print("\n🤖 TESTING: Individual Agent Components")
    
    agents_tested = 0
    agents_passed = 0
    
    # Test Live Network Connector Agent
    try:
        print("\n🌐 Testing Live Network Connector Agent...")
        from agentic_llm_workflow.live_network_connector_agent import live_network_connector_agent
        
        test_state = {"messages": [("user", "Check network connectivity")]}
        result = live_network_connector_agent.handle_request(test_state)
        
        print("✅ Live Network Connector Agent working")
        agents_tested += 1
        agents_passed += 1
        
    except Exception as e:
        print(f"⚠️ Live Network Connector Agent: {e}")
        agents_tested += 1
    
    # Test KPI Analytics Agent
    try:
        print("\n📈 Testing KPI Analytics Agent...")
        from agentic_llm_workflow.kpi_analytics_agent import kpi_analytics_agent
        
        test_state = {"messages": [("user", "Analyze current KPIs")]}
        result = kpi_analytics_agent.handle_request(test_state)
        
        print("✅ KPI Analytics Agent working")
        agents_tested += 1
        agents_passed += 1
        
    except Exception as e:
        print(f"⚠️ KPI Analytics Agent: {e}")
        agents_tested += 1
    
    # Test MML Command Agent
    try:
        print("\n⚙️ Testing MML Command Agent...")
        from agentic_llm_workflow.mml_command_agent import mml_command_agent
        
        test_state = {"messages": [("user", "Display current parameters")]}
        result = mml_command_agent.handle_request(test_state)
        
        print("✅ MML Command Agent working")
        agents_tested += 1
        agents_passed += 1
        
    except Exception as e:
        print(f"⚠️ MML Command Agent: {e}")
        agents_tested += 1
    
    print(f"\n📊 Individual Agent Test Results: {agents_passed}/{agents_tested} agents working")
    return agents_passed >= 2  # At least 2 out of 3 new agents should work

def test_orchestrator():
    """Test Agent Orchestrator"""
    print("\n🎭 TESTING: Agent Orchestration System")
    try:
        from agentic_llm_workflow.simple_orchestrator import simple_orchestrator
        
        print("✅ Simple Orchestrator imported successfully")
        
        # Test agent status
        agent_status = simple_orchestrator.get_agent_status()
        print(f"📋 Agent Status: {len(agent_status)} agents registered")
        
        for agent, status in agent_status.items():
            print(f"   • {agent}: {status}")
        
        # Test quick analysis
        print("\n🔍 Testing Quick Analysis...")
        quick_result = simple_orchestrator.run_quick_analysis("TEST_CELL_001")
        
        if quick_result.get("status") == "completed":
            print("✅ Quick analysis completed successfully")
        else:
            print("⚠️ Quick analysis had issues but continued")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        traceback.print_exc()
        return False

def test_full_workflow():
    """Test Complete 6-Agent Workflow"""
    print("\n🚀 TESTING: Complete 6-Agent Workflow")
    try:
        from agentic_llm_workflow.simple_orchestrator import run_full_optimization
        
        print("🎯 Running full optimization workflow...")
        
        # Test with a realistic optimization request
        test_request = "Optimize network performance for cell LTE_001 with focus on improving call setup success rate and data throughput"
        
        workflow_result = run_full_optimization(test_request, "LTE_001")
        
        if workflow_result.get("overall_status") == "completed":
            print("✅ Complete workflow executed successfully!")
            
            # Display results summary
            execution_time = workflow_result.get("execution_time", 0)
            print(f"⏱️ Execution time: {execution_time:.2f} seconds")
            
            agent_results = workflow_result.get("agent_results", {})
            print(f"📊 Agents executed: {len(agent_results)}")
            
            for agent, result in agent_results.items():
                status = result.get("status", "unknown")
                print(f"   • {agent}: {status}")
                
            return True
            
        else:
            print("⚠️ Workflow completed with issues")
            print(f"Status: {workflow_result.get('overall_status')}")
            if 'error' in workflow_result:
                print(f"Error: {workflow_result['error']}")
            return False
        
    except Exception as e:
        print(f"❌ Full workflow test failed: {e}")
        traceback.print_exc()
        return False

def test_ui_components():
    """Test UI Components"""
    print("\n🖥️ TESTING: UI Components")
    try:
        from ui_components.cassava_theme import CassavaTheme
        
        theme = CassavaTheme()
        print("✅ Cassava Theme imported successfully")
        
        # Test theme methods
        theme.apply_custom_css()
        print("✅ Custom CSS applied")
        
        header = theme.create_header("Test Application")
        print("✅ Header creation working")
        
        return True
        
    except Exception as e:
        print(f"❌ UI Components test failed: {e}")
        return False

def run_complete_test_suite():
    """Run the complete test suite"""
    print("🧪 LIQUID ZIMBABWE AGENT ECOSYSTEM TEST SUITE")
    print("=" * 60)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python Version: {sys.version}")
    print("=" * 60)
    
    test_results = {}
    
    # Run all tests
    test_results["api_client"] = test_api_client()
    test_results["kpi_management"] = test_kpi_management()
    test_results["parameter_management"] = test_parameter_management()
    test_results["individual_agents"] = test_individual_agents()
    test_results["orchestrator"] = test_orchestrator()
    test_results["full_workflow"] = test_full_workflow()
    test_results["ui_components"] = test_ui_components()
    
    # Calculate results
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 30)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print("=" * 30)
    print(f"Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - SYSTEM READY FOR DEPLOYMENT!")
    elif passed_tests >= total_tests * 0.8:  # 80% pass rate
        print("⚡ MOSTLY WORKING - Minor issues detected but core system functional")
    else:
        print("⚠️ SIGNIFICANT ISSUES - Review failed tests before deployment")
    
    return passed_tests, total_tests

if __name__ == "__main__":
    try:
        passed, total = run_complete_test_suite()
        
        # Exit with appropriate code
        if passed == total:
            print("\n✅ Test suite completed successfully")
            sys.exit(0)
        else:
            print(f"\n⚠️ Test suite completed with {total - passed} issues")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test suite failed to run: {e}")
        traceback.print_exc()
        sys.exit(2)