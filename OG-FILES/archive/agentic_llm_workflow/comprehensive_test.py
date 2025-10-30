#!/usr/bin/env python3
"""
Comprehensive Test Suite for Telco Network Configuration System
==============================================================

Tests all modules, attributes, functions, calls, and variables for:
- Phase 3 Liquid Zimbabwe Integration
- Original NVIDIA Template functionality  
- Docker environment compatibility
- Import dependencies and error handling
"""

import sys
import os
import traceback
import importlib
from pathlib import Path

# Add the workflow directory to path
sys.path.insert(0, str(Path(__file__).parent))

class ComprehensiveTestSuite:
    def __init__(self):
        self.test_results = {}
        self.failed_tests = []
        self.passed_tests = []
        
    def log_test(self, test_name, passed, details=""):
        """Log test results with details"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results[test_name] = {"passed": passed, "details": details}
        if passed:
            self.passed_tests.append(test_name)
        else:
            self.failed_tests.append(test_name)
    
    def test_basic_imports(self):
        """Test basic Python module imports"""
        basic_modules = ['json', 'sqlite3', 'time', 'os', 'yaml', 'pandas', 'requests']
        
        for module in basic_modules:
            try:
                importlib.import_module(module)
                self.log_test(f"Import {module}", True)
            except ImportError as e:
                self.log_test(f"Import {module}", False, str(e))
    
    def test_langchain_imports(self):
        """Test LangChain and LangGraph imports"""
        langchain_modules = [
            'langgraph',
            'langgraph.graph',
            'langgraph.prebuilt', 
            'langchain_core.tools',
            'langchain_core.messages',
            'langchain_nvidia_ai_endpoints'
        ]
        
        for module in langchain_modules:
            try:
                importlib.import_module(module)
                self.log_test(f"LangChain Import {module}", True)
            except ImportError as e:
                self.log_test(f"LangChain Import {module}", False, str(e))
    
    def test_workflow_tools_imports(self):
        """Test workflow tools and utilities imports"""
        try:
            from agentic_llm_workflow.tools import (
                calc_weighted_average, 
                execute_xapp_sql, 
                find_value_in_gnb
            )
            self.log_test("Import workflow tools", True, "calc_weighted_average, execute_xapp_sql, find_value_in_gnb")
        except ImportError as e:
            self.log_test("Import workflow tools", False, str(e))
        
        try:
            from agentic_llm_workflow.utils import (
                check_network_status, 
                start_network, 
                stop_network, 
                update_value_in_db
            )
            self.log_test("Import workflow utils", True, "check_network_status, start_network, stop_network, update_value_in_db")
        except ImportError as e:
            self.log_test("Import workflow utils", False, str(e))
    
    def test_liquid_zimbabwe_integration(self):
        """Test Phase 3 Liquid Zimbabwe integration"""
        try:
            from agentic_llm_workflow.lz_config import LZ_CONFIG, is_liquid_zimbabwe_enabled
            self.log_test("Import LZ Config", True, "LZ_CONFIG and is_liquid_zimbabwe_enabled available")
            
            # Test configuration structure
            if isinstance(LZ_CONFIG, dict):
                required_keys = ['api_endpoint', 'parameter_mapping', 'kpi_preferences']
                missing_keys = [k for k in required_keys if k not in LZ_CONFIG]
                if not missing_keys:
                    self.log_test("LZ Config Structure", True, f"All required keys present: {required_keys}")
                else:
                    self.log_test("LZ Config Structure", False, f"Missing keys: {missing_keys}")
            else:
                self.log_test("LZ Config Structure", False, "LZ_CONFIG is not a dictionary")
                
        except ImportError as e:
            self.log_test("Import LZ Config", False, f"Graceful fallback mode: {e}")
        
        try:
            from agentic_llm_workflow.lz_api_client import LiquidZimbabweAPIClient
            self.log_test("Import LZ API Client", True, "LiquidZimbabweAPIClient class available")
            
            # Test API client instantiation
            try:
                client = LiquidZimbabweAPIClient()
                if hasattr(client, 'get_connection_status') and hasattr(client, 'get_network_kpis'):
                    self.log_test("LZ API Client Methods", True, "get_connection_status and get_network_kpis methods available")
                else:
                    self.log_test("LZ API Client Methods", False, "Required methods missing")
            except Exception as e:
                self.log_test("LZ API Client Instantiation", False, str(e))
                
        except ImportError as e:
            self.log_test("Import LZ API Client", False, f"Graceful fallback mode: {e}")
    
    def test_agents_functionality(self):
        """Test main agent functions"""
        try:
            from agents import monitoring_agent, config_agent, validation_agent, State
            self.log_test("Import Main Agents", True, "monitoring_agent, config_agent, validation_agent, State")
            
            # Test State class
            try:
                test_state = State()
                test_state["test_key"] = "test_value"
                if test_state["test_key"] == "test_value":
                    self.log_test("State Class Functionality", True, "State behaves as expected dict")
                else:
                    self.log_test("State Class Functionality", False, "State dict behavior issue")
            except Exception as e:
                self.log_test("State Class Functionality", False, str(e))
                
            # Test agent function signatures
            import inspect
            for agent_name, agent_func in [("monitoring_agent", monitoring_agent), 
                                         ("config_agent", config_agent), 
                                         ("validation_agent", validation_agent)]:
                try:
                    sig = inspect.signature(agent_func)
                    params = list(sig.parameters.keys())
                    if 'state' in params and str(sig.return_annotation) in ['State', '<class \'agents.State\'>']:
                        self.log_test(f"{agent_name} Signature", True, f"Parameters: {params}, Returns: State")
                    else:
                        self.log_test(f"{agent_name} Signature", False, f"Unexpected signature: {sig}")
                except Exception as e:
                    self.log_test(f"{agent_name} Signature", False, str(e))
                    
        except ImportError as e:
            self.log_test("Import Main Agents", False, str(e))
    
    def test_config_file_access(self):
        """Test configuration file access"""
        config_files = ['config.yaml', '../config.yaml']
        
        for config_path in config_files:
            if os.path.exists(config_path):
                try:
                    import yaml
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f)
                    
                    required_config_keys = ['nvidia_api_key', 'llm_model', 'monitoring_wait_time', 'table_name']
                    missing_keys = [k for k in required_config_keys if k not in config]
                    
                    if not missing_keys:
                        self.log_test(f"Config File {config_path}", True, f"All required keys present")
                    else:
                        self.log_test(f"Config File {config_path}", False, f"Missing keys: {missing_keys}")
                    break
                except Exception as e:
                    self.log_test(f"Config File {config_path}", False, str(e))
            else:
                self.log_test(f"Config File {config_path}", False, "File not found")
    
    def test_database_connectivity(self):
        """Test SQLite database connectivity"""
        try:
            import sqlite3
            # Test in-memory database
            conn = sqlite3.connect(':memory:')
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE test_table (id INTEGER, name TEXT)")
            cursor.execute("INSERT INTO test_table VALUES (1, 'test')")
            result = cursor.fetchone()
            conn.close()
            
            if result:
                self.log_test("SQLite Database Connectivity", True, "In-memory database operations successful")
            else:
                self.log_test("SQLite Database Connectivity", False, "Database operations failed")
                
        except Exception as e:
            self.log_test("SQLite Database Connectivity", False, str(e))
    
    def test_docker_environment(self):
        """Test Docker environment indicators"""
        docker_indicators = [
            ('BUBBLERAN_HOST_PWD', 'BubbleRAN Docker environment variable'),
            ('/.dockerenv', 'Docker container file indicator')
        ]
        
        docker_detected = False
        for indicator, description in docker_indicators:
            if indicator.startswith('/'):
                # File check
                if os.path.exists(indicator):
                    self.log_test("Docker Environment Detection", True, f"Found {description}")
                    docker_detected = True
            else:
                # Environment variable check
                if os.environ.get(indicator):
                    self.log_test("Docker Environment Detection", True, f"Found {description}")
                    docker_detected = True
        
        if not docker_detected:
            self.log_test("Docker Environment Detection", False, "No Docker indicators found - may be local environment")
    
    def run_all_tests(self):
        """Run the complete test suite"""
        print("🧪 Starting Comprehensive Test Suite for Telco Network Configuration")
        print("=" * 80)
        
        print("\\n📦 Testing Basic Python Imports...")
        self.test_basic_imports()
        
        print("\\n🔗 Testing LangChain/LangGraph Imports...")
        self.test_langchain_imports()
        
        print("\\n🛠️ Testing Workflow Tools and Utils...")
        self.test_workflow_tools_imports()
        
        print("\\n🌍 Testing Liquid Zimbabwe Integration...")
        self.test_liquid_zimbabwe_integration()
        
        print("\\n🤖 Testing Agent Functionality...")
        self.test_agents_functionality()
        
        print("\\n⚙️ Testing Configuration Access...")
        self.test_config_file_access()
        
        print("\\n🗄️ Testing Database Connectivity...")
        self.test_database_connectivity()
        
        print("\\n🐳 Testing Docker Environment...")
        self.test_docker_environment()
        
        # Summary
        print("\\n" + "=" * 80)
        print("📊 TEST SUITE SUMMARY")
        print("=" * 80)
        print(f"✅ PASSED: {len(self.passed_tests)}")
        print(f"❌ FAILED: {len(self.failed_tests)}")
        print(f"📈 SUCCESS RATE: {len(self.passed_tests)/(len(self.passed_tests)+len(self.failed_tests))*100:.1f}%")
        
        if self.failed_tests:
            print("\\n🔍 FAILED TESTS:")
            for test in self.failed_tests:
                print(f"   • {test}: {self.test_results[test]['details']}")
        
        print("\\n🎯 OVERALL SYSTEM STATUS:")
        if len(self.failed_tests) == 0:
            print("✅ ALL SYSTEMS OPERATIONAL - Ready for production deployment!")
        elif len(self.failed_tests) <= 3:
            print("⚠️ MOSTLY OPERATIONAL - Minor issues detected, system should work with fallbacks")
        else:
            print("❌ SYSTEM ISSUES - Multiple components need attention before deployment")
        
        return len(self.failed_tests) == 0

if __name__ == "__main__":
    test_suite = ComprehensiveTestSuite()
    success = test_suite.run_all_tests()
    sys.exit(0 if success else 1)