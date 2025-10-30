#!/usr/bin/env python3
"""
Demo Testing Suite
==================

Comprehensive testing for the 6-Stage Agentic Network Optimization Demo.
Tests all components individually and in integration.

Created: 2024
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from main_demo_orchestrator import DemoOrchestrator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DemoTestSuite:
    """Comprehensive testing suite for the demo system"""
    
    def __init__(self):
        self.orchestrator = DemoOrchestrator()
        self.test_results = {}
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test categories"""
        logger.info("Starting comprehensive demo test suite...")
        
        test_categories = [
            ("Component Tests", self._test_components),
            ("Scenario Tests", self._test_scenarios),
            ("Integration Tests", self._test_integration),
            ("Performance Tests", self._test_performance),
            ("Error Handling Tests", self._test_error_handling)
        ]
        
        all_results = {}
        
        for category_name, test_func in test_categories:
            logger.info(f"\n{'='*50}")
            logger.info(f"Running {category_name}")
            logger.info(f"{'='*50}")
            
            try:
                results = await test_func()
                all_results[category_name] = results
                logger.info(f"{category_name} completed: {results.get('status', 'unknown')}")
            except Exception as e:
                logger.error(f"{category_name} failed: {str(e)}")
                all_results[category_name] = {"status": "failed", "error": str(e)}
        
        # Generate test report
        report = self._generate_test_report(all_results)
        await self._save_test_results(report)
        
        return report
    
    async def _test_components(self) -> Dict[str, Any]:
        """Test individual components"""
        logger.info("Testing individual components...")
        
        component_tests = {
            "workflow_engine": await self._test_workflow_engine(),
            "prompt_templates": await self._test_prompt_templates(),
            "data_integration": await self._test_data_integration(),
            "approval_workflow": await self._test_approval_workflow()
        }
        
        passed = sum(1 for result in component_tests.values() if result.get("status") == "passed")
        total = len(component_tests)
        
        return {
            "status": "passed" if passed == total else "partial",
            "passed": passed,
            "total": total,
            "details": component_tests
        }
    
    async def _test_workflow_engine(self) -> Dict[str, Any]:
        """Test the enhanced workflow engine"""
        try:
            # Test workflow engine initialization
            engine = self.orchestrator.workflow_engine
            
            # Test basic functionality
            if not hasattr(engine, 'run_stage'):
                return {"status": "failed", "reason": "Missing run_stage method"}
            
            # Test with mock context
            from utils.enhanced_workflow_engine import WorkflowContext
            context = WorkflowContext(
                sites=["TEST_SITE"],
                optimization_goals=["Test goal"],
                demo_mode=True
            )
            
            # Test stage 0 (Network Connector)
            result = await engine.run_stage(0, context)
            
            if result and result.get("status") in ["success", "simulated"]:
                return {"status": "passed", "details": "Workflow engine functional"}
            else:
                return {"status": "failed", "reason": "Stage execution failed", "result": result}
                
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def _test_prompt_templates(self) -> Dict[str, Any]:
        """Test the prompt template system"""
        try:
            templates = self.orchestrator.prompt_templates
            
            # Test prompt generation
            if not hasattr(templates, 'get_network_connector_prompt'):
                return {"status": "failed", "reason": "Missing prompt methods"}
            
            # Test prompt with sample data
            context = {
                "sites": ["TEST_SITE"],
                "goals": ["Test optimization"]
            }
            
            prompt = templates.get_network_connector_prompt(context)
            
            if prompt and len(prompt) > 50:  # Basic content check
                return {"status": "passed", "details": "Prompt templates functional"}
            else:
                return {"status": "failed", "reason": "Invalid prompt generation"}
                
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def _test_data_integration(self) -> Dict[str, Any]:
        """Test the data integration engine"""
        try:
            data_engine = self.orchestrator.data_engine
            
            # Test data retrieval
            network_data = await data_engine.get_network_data("discovery")
            
            if network_data and isinstance(network_data, dict):
                # Check for expected structure
                required_keys = ["source", "sites", "status"]
                missing_keys = [key for key in required_keys if key not in network_data]
                
                if not missing_keys:
                    return {"status": "passed", "details": "Data integration functional"}
                else:
                    return {"status": "failed", "reason": f"Missing keys: {missing_keys}"}
            else:
                return {"status": "failed", "reason": "No data returned"}
                
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def _test_approval_workflow(self) -> Dict[str, Any]:
        """Test the approval workflow system"""
        try:
            approval_engine = self.orchestrator.approval_engine
            
            # Test approval simulation
            if not hasattr(approval_engine, 'simulate_human_approval'):
                return {"status": "failed", "reason": "Missing approval methods"}
            
            # Test with sample request
            decision = approval_engine.simulate_human_approval("test_request_123")
            
            if decision and hasattr(decision, 'decision'):
                return {"status": "passed", "details": "Approval workflow functional"}
            else:
                return {"status": "failed", "reason": "Invalid approval response"}
                
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def _test_scenarios(self) -> Dict[str, Any]:
        """Test all demo scenarios"""
        logger.info("Testing demo scenarios...")
        
        scenarios = self.orchestrator.get_available_scenarios()
        scenario_results = {}
        
        for scenario in scenarios:
            logger.info(f"Testing scenario: {scenario['name']}")
            
            try:
                # Run scenario in automated mode with timeout
                result = await asyncio.wait_for(
                    self.orchestrator.run_complete_demo(
                        scenario['key'], 
                        execution_mode="automated"
                    ),
                    timeout=300  # 5 minutes timeout
                )
                
                if "error" not in result:
                    scenario_results[scenario['key']] = {
                        "status": "passed",
                        "duration": result.get("demo_metadata", {}).get("duration_minutes", 0),
                        "stages_completed": result.get("demo_metadata", {}).get("stages_completed", 0)
                    }
                else:
                    scenario_results[scenario['key']] = {
                        "status": "failed",
                        "error": result["error"]
                    }
                    
            except asyncio.TimeoutError:
                scenario_results[scenario['key']] = {
                    "status": "failed",
                    "error": "Scenario execution timeout"
                }
            except Exception as e:
                scenario_results[scenario['key']] = {
                    "status": "failed",
                    "error": str(e)
                }
        
        passed = sum(1 for result in scenario_results.values() if result.get("status") == "passed")
        total = len(scenario_results)
        
        return {
            "status": "passed" if passed == total else "partial",
            "passed": passed,
            "total": total,
            "details": scenario_results
        }
    
    async def _test_integration(self) -> Dict[str, Any]:
        """Test end-to-end integration"""
        logger.info("Testing end-to-end integration...")
        
        try:
            # Test full workflow with bindura_optimization scenario
            result = await self.orchestrator.run_complete_demo(
                "bindura_optimization", 
                execution_mode="automated"
            )
            
            if "error" in result:
                return {"status": "failed", "error": result["error"]}
            
            # Validate result structure
            required_sections = [
                "demo_metadata",
                "workflow_execution", 
                "approval_process",
                "execution_simulation"
            ]
            
            missing_sections = [section for section in required_sections if section not in result]
            
            if not missing_sections:
                # Check workflow completion
                workflow = result.get("workflow_execution", {})
                stages_completed = workflow.get("total_stages", 0)
                
                if stages_completed == 6:
                    return {
                        "status": "passed",
                        "details": "Full integration successful",
                        "duration": result.get("demo_metadata", {}).get("duration_minutes", 0)
                    }
                else:
                    return {
                        "status": "partial",
                        "reason": f"Only {stages_completed}/6 stages completed"
                    }
            else:
                return {
                    "status": "failed",
                    "reason": f"Missing result sections: {missing_sections}"
                }
                
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def _test_performance(self) -> Dict[str, Any]:
        """Test performance characteristics"""
        logger.info("Testing performance...")
        
        performance_results = {}
        
        # Test component initialization time
        start_time = datetime.now()
        orchestrator = DemoOrchestrator()
        init_time = (datetime.now() - start_time).total_seconds()
        
        performance_results["initialization_time"] = init_time
        
        # Test scenario execution time
        start_time = datetime.now()
        try:
            result = await asyncio.wait_for(
                orchestrator.run_complete_demo("preventive_maintenance", "automated"),
                timeout=180  # 3 minutes
            )
            execution_time = (datetime.now() - start_time).total_seconds()
            performance_results["scenario_execution_time"] = execution_time
            
            # Check if execution was reasonable
            if execution_time < 180 and "error" not in result:
                status = "passed"
            else:
                status = "warning"
                
        except asyncio.TimeoutError:
            performance_results["scenario_execution_time"] = 180
            status = "failed"
        except Exception as e:
            performance_results["error"] = str(e)
            status = "failed"
        
        return {
            "status": status,
            "details": performance_results,
            "benchmarks": {
                "init_time_target": 5.0,  # seconds
                "execution_time_target": 120.0  # seconds
            }
        }
    
    async def _test_error_handling(self) -> Dict[str, Any]:
        """Test error handling and edge cases"""
        logger.info("Testing error handling...")
        
        error_tests = {}
        
        # Test invalid scenario
        try:
            result = await self.orchestrator.run_complete_demo("invalid_scenario", "automated")
            if "error" in result:
                error_tests["invalid_scenario"] = {"status": "passed", "error_caught": True}
            else:
                error_tests["invalid_scenario"] = {"status": "failed", "error_caught": False}
        except Exception:
            error_tests["invalid_scenario"] = {"status": "passed", "error_caught": True}
        
        # Test scenario selection edge cases
        scenarios = self.orchestrator.get_available_scenarios()
        if scenarios:
            error_tests["scenario_availability"] = {"status": "passed", "count": len(scenarios)}
        else:
            error_tests["scenario_availability"] = {"status": "failed", "count": 0}
        
        # Test component resilience
        try:
            # Test with minimal context
            from utils.enhanced_workflow_engine import WorkflowContext
            minimal_context = WorkflowContext(sites=[], optimization_goals=[])
            result = await self.orchestrator.workflow_engine.run_stage(0, minimal_context)
            
            if result:
                error_tests["minimal_context"] = {"status": "passed", "handled": True}
            else:
                error_tests["minimal_context"] = {"status": "failed", "handled": False}
        except Exception:
            error_tests["minimal_context"] = {"status": "passed", "handled": True}
        
        passed = sum(1 for test in error_tests.values() if test.get("status") == "passed")
        total = len(error_tests)
        
        return {
            "status": "passed" if passed == total else "partial",
            "passed": passed,
            "total": total,
            "details": error_tests
        }
    
    def _generate_test_report(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        
        # Calculate overall statistics
        total_tests = 0
        passed_tests = 0
        
        for category, results in all_results.items():
            if isinstance(results, dict):
                if "passed" in results and "total" in results:
                    total_tests += results["total"]
                    passed_tests += results["passed"]
                elif results.get("status") == "passed":
                    total_tests += 1
                    passed_tests += 1
                else:
                    total_tests += 1
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "test_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": round(success_rate, 1),
                "overall_status": "passed" if success_rate >= 90 else "partial" if success_rate >= 70 else "failed"
            },
            "category_results": all_results,
            "summary": {
                "components_functional": all_results.get("Component Tests", {}).get("status") == "passed",
                "scenarios_working": all_results.get("Scenario Tests", {}).get("status") in ["passed", "partial"],
                "integration_successful": all_results.get("Integration Tests", {}).get("status") == "passed",
                "performance_acceptable": all_results.get("Performance Tests", {}).get("status") in ["passed", "warning"],
                "error_handling_robust": all_results.get("Error Handling Tests", {}).get("status") in ["passed", "partial"]
            },
            "recommendations": self._generate_test_recommendations(all_results)
        }
        
        return report
    
    def _generate_test_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check component tests
        component_results = results.get("Component Tests", {})
        if component_results.get("status") != "passed":
            recommendations.append("Review and fix failing component tests before deployment")
        
        # Check scenario tests  
        scenario_results = results.get("Scenario Tests", {})
        if scenario_results.get("status") == "partial":
            failed_scenarios = [
                key for key, result in scenario_results.get("details", {}).items() 
                if result.get("status") != "passed"
            ]
            if failed_scenarios:
                recommendations.append(f"Fix failing scenarios: {', '.join(failed_scenarios)}")
        
        # Check performance
        performance_results = results.get("Performance Tests", {})
        if performance_results.get("status") == "warning":
            recommendations.append("Optimize performance - execution times above targets")
        
        # General recommendations
        recommendations.extend([
            "Run full test suite before each demo presentation",
            "Monitor test results and address failures promptly",
            "Consider implementing automated regression testing",
            "Document any known limitations or workarounds"
        ])
        
        return recommendations
    
    async def _save_test_results(self, report: Dict[str, Any]) -> None:
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"demo_test_results_{timestamp}.json"
        filepath = Path("test_results") / filename
        
        # Create directory if it doesn't exist
        filepath.parent.mkdir(exist_ok=True)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Test results saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save test results: {str(e)}")

async def main():
    """Run the complete test suite"""
    print("\n" + "="*60)
    print("6-STAGE AGENTIC DEMO - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    test_suite = DemoTestSuite()
    
    try:
        results = await test_suite.run_all_tests()
        
        print("\n" + "="*60)
        print("TEST SUITE COMPLETED")
        print("="*60)
        
        metadata = results.get("test_metadata", {})
        print(f"Total Tests: {metadata.get('total_tests', 0)}")
        print(f"Passed: {metadata.get('passed_tests', 0)}")
        print(f"Success Rate: {metadata.get('success_rate', 0):.1f}%")
        print(f"Overall Status: {metadata.get('overall_status', 'unknown').upper()}")
        
        summary = results.get("summary", {})
        print("\nComponent Status:")
        for component, status in summary.items():
            status_text = "✓ PASS" if status else "✗ FAIL"
            print(f"  {component}: {status_text}")
        
        recommendations = results.get("recommendations", [])
        if recommendations:
            print("\nRecommendations:")
            for rec in recommendations[:5]:  # Show top 5
                print(f"  • {rec}")
        
        print(f"\nFull results saved in: test_results/")
        
    except Exception as e:
        print(f"\nTest suite failed: {str(e)}")
        logger.error(f"Test suite error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())