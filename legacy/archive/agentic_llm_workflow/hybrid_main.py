#!/usr/bin/env python3
"""
Hybrid Telco Network Monitoring System - Main Entry Point

This is the main entry point for the hybrid system that automatically detects
available dependencies and provides appropriate functionality.

Usage:
    python hybrid_main.py                    # Show system status
    python hybrid_main.py --monitor          # Run basic monitoring
    python hybrid_main.py --analyze          # Run enhanced analysis (if available)
    python hybrid_main.py --optimize         # Run advanced optimization (if available)
    python hybrid_main.py --test             # Run system tests
"""

import sys
import os
import logging
import argparse
from datetime import datetime
from typing import Dict, Any

# Add the agentic_llm_workflow directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from hybrid_config import hybrid_config, print_system_status, DeploymentMode, FeatureLevel
    from hybrid_agent_manager import hybrid_agent_manager, AgentType, execute_workflow
except ImportError as e:
    print(f"❌ Failed to import hybrid system components: {e}")
    print("🔧 Please ensure you're running from the agentic_llm_workflow directory")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HybridTelcoSystem:
    """Main hybrid telco network monitoring system"""
    
    def __init__(self):
        self.config = hybrid_config
        self.agent_manager = hybrid_agent_manager
        self.logger = logger
        
    def show_status(self):
        """Display comprehensive system status"""
        print_system_status()
        
        # Show agent-specific status
        status = self.agent_manager.get_system_status()
        
        print("🤖 AGENT ECOSYSTEM STATUS:")
        for agent_name, capability in status['agent_capabilities'].items():
            icon = "✅" if capability['available'] else "❌"
            print(f"   {icon} {capability['name']}: {capability['description']}")
        print()
        
        return status
    
    def run_monitoring(self) -> Dict[str, Any]:
        """Run basic network monitoring"""
        print("🔍 Running Network Monitoring...")
        
        result = execute_workflow("basic_monitoring")
        
        if result.get('status') == 'completed':
            print("✅ Monitoring completed successfully")
            if 'data' in result:
                data = result['data']
                if isinstance(data, dict) and 'error' not in data:
                    print(f"📊 Collected {len(data) if isinstance(data, dict) else 'N/A'} data points")
        else:
            print(f"❌ Monitoring failed: {result.get('error', 'Unknown error')}")
        
        return result
    
    def run_analysis(self) -> Dict[str, Any]:
        """Run enhanced analysis if available"""
        print("🧠 Running Enhanced Analysis...")
        
        if not self.config.is_feature_available(FeatureLevel.ENHANCED):
            result = {
                "error": "Enhanced analysis requires LangChain dependencies",
                "suggestion": "Run: pip install langchain langchain-core"
            }
            print("❌ Enhanced analysis not available")
            print("💡 To enable: pip install langchain langchain-core")
        else:
            result = execute_workflow("enhanced_analysis")
            if result.get('status') == 'completed':
                print("✅ Enhanced analysis completed")
                features = result.get('features', [])
                for feature in features:
                    print(f"   🔬 {feature}")
            else:
                print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
        
        return result
    
    def run_optimization(self) -> Dict[str, Any]:
        """Run advanced optimization if available"""
        print("🚀 Running Advanced Optimization...")
        
        if not self.config.is_feature_available(FeatureLevel.ADVANCED):
            result = {
                "error": "Advanced optimization requires LangGraph dependencies",
                "suggestion": "Run: pip install langchain langchain-core langgraph"
            }
            print("❌ Advanced optimization not available")
            print("💡 To enable: pip install langchain langchain-core langgraph")
        else:
            result = execute_workflow("advanced_optimization")
            if result.get('status') == 'completed':
                print("✅ Advanced optimization completed")
                features = result.get('features', [])
                for feature in features:
                    print(f"   ⚡ {feature}")
            else:
                print(f"❌ Optimization failed: {result.get('error', 'Unknown error')}")
        
        return result
    
    def run_tests(self) -> Dict[str, Any]:
        """Run comprehensive system tests"""
        print("🧪 Running System Tests...")
        print("=" * 40)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        # Test 1: Configuration
        print("1️⃣ Testing Configuration...")
        try:
            status = self.config.get_deployment_info()
            results["tests"]["configuration"] = {
                "status": "passed",
                "mode": status.get("deployment_mode", "unknown"),
                "features": status.get("features", {})
            }
            print(f"   ✅ Configuration OK - Mode: {status.get('deployment_mode', 'unknown')}")
        except Exception as e:
            results["tests"]["configuration"] = {"status": "failed", "error": str(e)}
            print(f"   ❌ Configuration failed: {e}")
        
        # Test 2: Agent Manager
        print("2️⃣ Testing Agent Manager...")
        try:
            available_agents = self.agent_manager.get_available_agents()
            results["tests"]["agent_manager"] = {
                "status": "passed",
                "available_agents": [agent.value for agent in available_agents],
                "agent_count": len(available_agents)
            }
            print(f"   ✅ Agent Manager OK - {len(available_agents)} agents available")
        except Exception as e:
            results["tests"]["agent_manager"] = {"status": "failed", "error": str(e)}
            print(f"   ❌ Agent Manager failed: {e}")
        
        # Test 3: Core Agent Creation
        print("3️⃣ Testing Core Agent Creation...")
        try:
            monitoring_agent = self.agent_manager.create_agent(AgentType.MONITORING)
            if monitoring_agent:
                results["tests"]["core_agents"] = {"status": "passed"}
                print("   ✅ Core agents can be created")
            else:
                results["tests"]["core_agents"] = {"status": "failed", "error": "Could not create monitoring agent"}
                print("   ❌ Core agent creation failed")
        except Exception as e:
            results["tests"]["core_agents"] = {"status": "failed", "error": str(e)}
            print(f"   ❌ Core agent creation failed: {e}")
        
        # Test 4: Basic Workflow
        print("4️⃣ Testing Basic Workflow...")
        try:
            workflow_result = execute_workflow("basic_monitoring")
            if workflow_result.get('status') == 'completed':
                results["tests"]["basic_workflow"] = {"status": "passed"}
                print("   ✅ Basic workflow executed successfully")
            else:
                results["tests"]["basic_workflow"] = {"status": "failed", "error": workflow_result.get('error')}
                print("   ❌ Basic workflow failed")
        except Exception as e:
            results["tests"]["basic_workflow"] = {"status": "failed", "error": str(e)}
            print(f"   ❌ Basic workflow failed: {e}")
        
        # Summary
        passed_tests = sum(1 for test in results["tests"].values() if test.get("status") == "passed")
        total_tests = len(results["tests"])
        
        print()
        print(f"📊 TEST SUMMARY: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! System is ready.")
        else:
            print("⚠️ Some tests failed. Check the output above for details.")
        
        return results

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Hybrid Telco Network Monitoring System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python hybrid_main.py                 # Show system status
  python hybrid_main.py --monitor       # Run monitoring
  python hybrid_main.py --analyze       # Run analysis (requires LangChain)
  python hybrid_main.py --optimize      # Run optimization (requires LangGraph)
  python hybrid_main.py --test          # Run system tests
  python hybrid_main.py --upgrade       # Show upgrade instructions
        """
    )
    
    parser.add_argument('--monitor', action='store_true',
                       help='Run basic network monitoring')
    parser.add_argument('--analyze', action='store_true',
                       help='Run enhanced analysis (requires LangChain)')
    parser.add_argument('--optimize', action='store_true',
                       help='Run advanced optimization (requires LangGraph)')
    parser.add_argument('--test', action='store_true',
                       help='Run comprehensive system tests')
    parser.add_argument('--upgrade', action='store_true',
                       help='Show upgrade instructions')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize system
    try:
        system = HybridTelcoSystem()
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        return 1
    
    # Execute requested action
    try:
        if args.monitor:
            system.run_monitoring()
        elif args.analyze:
            system.run_analysis()
        elif args.optimize:
            system.run_optimization()
        elif args.test:
            system.run_tests()
        elif args.upgrade:
            show_upgrade_instructions()
        else:
            # Default: show status
            system.show_status()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
        return 130
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

def show_upgrade_instructions():
    """Show upgrade instructions for different feature levels"""
    print("🚀 HYBRID SYSTEM UPGRADE GUIDE")
    print("=" * 50)
    print()
    
    # Check current deployment mode
    current_info = hybrid_config.get_deployment_info()
    current_mode = current_info.get('deployment_mode', 'unknown')
    
    print(f"📊 Current Mode: {current_mode.upper()}")
    print()
    
    if current_mode == 'basic':
        print("💡 TO ENABLE ENHANCED FEATURES (AI Analytics):")
        print("   pip install langchain langchain-core")
        print()
        print("🚀 TO ENABLE ADVANCED FEATURES (Full AI Ecosystem):")
        print("   pip install langchain langchain-core langgraph")
        print("   pip install langchain-nvidia-ai-endpoints  # Optional: NVIDIA AI")
        print()
    elif current_mode == 'enhanced':
        print("✅ Enhanced features already available!")
        print()
        print("🚀 TO ENABLE ADVANCED FEATURES (Orchestration):")
        print("   pip install langgraph")
        print("   pip install langchain-nvidia-ai-endpoints  # Optional: NVIDIA AI")
        print()
    else:
        print("🎉 All features already available!")
        print()
    
    print("📚 FEATURE COMPARISON:")
    print()
    print("🔹 BASIC MODE:")
    print("   • Core network monitoring")
    print("   • Parameter configuration")
    print("   • System validation")
    print("   • Memory: 512MB-1GB")
    print()
    print("🔸 ENHANCED MODE:")
    print("   • All basic features")
    print("   • AI-powered analytics")
    print("   • Smart optimization")
    print("   • Trend analysis")
    print("   • Memory: 1-2GB")
    print()
    print("🔶 ADVANCED MODE:")
    print("   • All enhanced features")
    print("   • Multi-agent orchestration")
    print("   • Automated optimization")
    print("   • Real-time adaptation")
    print("   • Live network management")
    print("   • Memory: 2-4GB")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)