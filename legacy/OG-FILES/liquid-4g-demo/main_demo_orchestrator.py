#!/usr/bin/env python3
"""
Main Demo Orchestrator
=====================

This is the master controller for the 6-Stage Agentic Network Optimization Demo.
Coordinates all enhanced components into a comprehensive demonstration.

Created: 2024
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Add current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    print("Warning: Streamlit not available - demo will run in console mode")

# Import our enhanced components
from agents.enhanced_workflow_engine import EnhancedWorkflowEngine, WorkflowContext
from prompts.enhanced_prompt_templates import PromptTemplates
from utils.enhanced_data_integration import DataIntegrationEngine
from utils.human_approval_workflow import ApprovalWorkflowEngine, ApprovalRequest

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('demo_orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DemoScenario:
    """Represents a complete demo scenario with all parameters"""
    name: str
    description: str
    target_sites: List[str]
    optimization_goals: List[str]
    expected_duration: int  # minutes
    complexity_level: str  # "basic", "intermediate", "advanced"
    risk_level: str  # "low", "medium", "high"
    requires_approval: bool = True
    demo_parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DemoState:
    """Tracks the complete state of the demo execution"""
    scenario: Optional[DemoScenario] = None
    current_stage: int = 0
    workflow_results: Dict[str, Any] = field(default_factory=dict)
    approval_decisions: List[Dict[str, Any]] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_mode: str = "interactive"  # "interactive", "automated", "presentation"
    
class DemoOrchestrator:
    """
    Master controller for the 6-Stage Agentic Network Optimization Demo
    
    This class coordinates all enhanced components:
    - Enhanced Workflow Engine (6-stage agents)
    - Prompt Architecture System
    - Data Integration with fallback hierarchy
    - Human Approval Workflow
    - Advanced Streamlit UI
    """
    
    def __init__(self):
        self.state = DemoState()
        self.workflow_engine = EnhancedWorkflowEngine()
        self.prompt_templates = PromptTemplates()
        self.data_engine = DataIntegrationEngine()
        self.approval_engine = ApprovalWorkflowEngine()
        
        # Demo scenarios
        self.scenarios = self._create_demo_scenarios()
        
        # Results storage
        self.results_dir = Path("demo_results")
        self.results_dir.mkdir(exist_ok=True)
        
        logger.info("Demo Orchestrator initialized successfully")
    
    def _create_demo_scenarios(self) -> Dict[str, DemoScenario]:
        """Create predefined demo scenarios showcasing different capabilities"""
        scenarios = {
            "bindura_optimization": DemoScenario(
                name="Bindura Network Optimization",
                description="Comprehensive optimization of Bindura network sites using real historical data",
                target_sites=["MSH0013-Bindura-Zaoga", "MSH-0331-Chiwaridzo 2"],
                optimization_goals=[
                    "Improve RACH Success Rate (currently 0.536%)",
                    "Reduce DL IBLER (currently 15.94%)",
                    "Optimize Call Setup Success Rate",
                    "Enhance Handover Performance"
                ],
                expected_duration=25,
                complexity_level="intermediate",
                risk_level="medium",
                demo_parameters={
                    "use_real_data": True,
                    "simulate_commands": True,
                    "detailed_analysis": True,
                    "include_predictions": True
                }
            ),
            
            "emergency_response": DemoScenario(
                name="Emergency Network Response",
                description="Rapid response to network degradation with automated intervention",
                target_sites=["MSH0013-Bindura-Zaoga"],
                optimization_goals=[
                    "Immediate service restoration",
                    "Emergency capacity optimization",
                    "Critical KPI stabilization"
                ],
                expected_duration=15,
                complexity_level="advanced",
                risk_level="high",
                demo_parameters={
                    "emergency_mode": True,
                    "accelerated_approval": True,
                    "real_time_monitoring": True
                }
            ),
            
            "preventive_maintenance": DemoScenario(
                name="Preventive Network Maintenance",
                description="Proactive optimization to prevent performance degradation",
                target_sites=["MSH0013-Bindura-Zaoga", "MSH-0331-Chiwaridzo 2", "MSH0024-Bindura-Town"],
                optimization_goals=[
                    "Proactive parameter tuning",
                    "Capacity planning optimization",
                    "Quality of service enhancement"
                ],
                expected_duration=35,
                complexity_level="basic",
                risk_level="low",
                demo_parameters={
                    "preventive_mode": True,
                    "comprehensive_analysis": True,
                    "gradual_implementation": True
                }
            ),
            
            "full_showcase": DemoScenario(
                name="Complete Capability Showcase",
                description="Comprehensive demonstration of all 6-stage capabilities",
                target_sites=["MSH0013-Bindura-Zaoga", "MSH-0331-Chiwaridzo 2", "MSH0024-Bindura-Town", "MSH0074-Chiwaridzo"],
                optimization_goals=[
                    "Complete workflow demonstration",
                    "All agent capabilities",
                    "Full prompt architecture",
                    "Human approval workflow",
                    "Real data integration"
                ],
                expected_duration=45,
                complexity_level="advanced",
                risk_level="medium",
                demo_parameters={
                    "showcase_mode": True,
                    "detailed_logging": True,
                    "step_by_step": True,
                    "interactive_approval": True
                }
            )
        }
        
        return scenarios
    
    def get_available_scenarios(self) -> List[Dict[str, str]]:
        """Get list of available demo scenarios for selection"""
        return [
            {
                "key": key,
                "name": scenario.name,
                "description": scenario.description,
                "duration": f"{scenario.expected_duration} minutes",
                "complexity": scenario.complexity_level,
                "risk": scenario.risk_level
            }
            for key, scenario in self.scenarios.items()
        ]
    
    def select_scenario(self, scenario_key: str) -> bool:
        """Select and initialize a demo scenario"""
        if scenario_key not in self.scenarios:
            logger.error(f"Unknown scenario: {scenario_key}")
            return False
        
        self.state.scenario = self.scenarios[scenario_key]
        self.state.current_stage = 0
        self.state.workflow_results = {}
        self.state.approval_decisions = []
        self.state.start_time = datetime.now()
        
        logger.info(f"Selected scenario: {self.state.scenario.name}")
        return True
    
    async def run_complete_demo(self, scenario_key: str, execution_mode: str = "interactive") -> Dict[str, Any]:
        """
        Run a complete demo scenario from start to finish
        
        Args:
            scenario_key: Key of the scenario to run
            execution_mode: "interactive", "automated", or "presentation"
        
        Returns:
            Complete demo results
        """
        if not self.select_scenario(scenario_key):
            return {"error": "Failed to select scenario"}
        
        if not self.state.scenario:
            return {"error": "No scenario selected"}
        
        self.state.execution_mode = execution_mode
        logger.info(f"Starting complete demo: {self.state.scenario.name} in {execution_mode} mode")
        
        try:
            # Phase 1: Initialize demo context
            demo_context = await self._initialize_demo_context()
            
            # Phase 2: Run 6-stage workflow
            workflow_results = await self._run_workflow_stages(demo_context)
            
            # Phase 3: Process approvals (if required)
            approval_results = await self._process_approvals(workflow_results)
            
            # Phase 4: Simulate execution (if approved)
            execution_results = await self._simulate_execution(approval_results)
            
            # Phase 5: Generate comprehensive report
            final_report = await self._generate_final_report(
                demo_context, workflow_results, approval_results, execution_results
            )
            
            self.state.end_time = datetime.now()
            
            # Save results
            await self._save_demo_results(final_report)
            
            logger.info("Demo completed successfully")
            return final_report
            
        except Exception as e:
            logger.error(f"Demo execution failed: {str(e)}")
            return {"error": str(e), "stage": self.state.current_stage}
    
    async def _initialize_demo_context(self) -> WorkflowContext:
        """Initialize the demo context with data and parameters"""
        logger.info("Initializing demo context...")
        
        if not self.state.scenario:
            raise ValueError("No scenario selected")
        
        # Get network data using our enhanced data integration
        network_data = await self.data_engine.get_network_data(data_type="discovery")
        
        # Create workflow context with required parameters
        current_time = datetime.now()
        context = WorkflowContext(
            workflow_id=f"demo_{current_time.strftime('%Y%m%d_%H%M%S')}",
            target_region="Bindura",
            user_query=f"Optimize network for {', '.join(self.state.scenario.target_sites)}",
            optimization_objectives=self.state.scenario.optimization_goals,
            stage_results={},
            real_data_context=network_data,
            network_state={"sites": self.state.scenario.target_sites},
            started_at=current_time
        )
        
        logger.info(f"Demo context initialized for {len(self.state.scenario.target_sites)} sites")
        return context
    
    async def _run_workflow_stages(self, context: WorkflowContext) -> Dict[str, Any]:
        """Run all 6 workflow stages with enhanced orchestration"""
        logger.info("Starting 6-stage workflow execution...")
        
        workflow_results = {}
        
        # Track stage execution
        stage_names = [
            "Network Connector",
            "Monitoring Analysis", 
            "KPI Analytics",
            "Configuration",
            "Validation",
            "Execution"
        ]
        
        for stage_idx in range(6):
            self.state.current_stage = stage_idx + 1
            stage_name = stage_names[stage_idx]
            
            logger.info(f"Executing Stage {self.state.current_stage}: {stage_name}")
            
            # Run stage with enhanced orchestration
            stage_result = await self._execute_stage_with_orchestration(
                stage_idx, context, workflow_results
            )
            
            workflow_results[f"stage_{stage_idx + 1}"] = stage_result
            
            # Update context with stage results
            context.stage_results[f"stage_{stage_idx + 1}"] = stage_result
            
            # Add pause for interactive mode
            if self.state.execution_mode == "interactive":
                await asyncio.sleep(1)  # Brief pause for user observation
        
        logger.info("All 6 stages completed successfully")
        return workflow_results
    
    async def _execute_stage_with_orchestration(
        self, stage_idx: int, context: WorkflowContext, previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single stage with enhanced orchestration and error handling"""
        
        try:
            # Use the enhanced workflow engine - for demo we'll call the engine directly
            # Since run_stage may not exist, we'll simulate the stage execution
            if hasattr(self.workflow_engine, 'run_stage'):
                result = await self.workflow_engine.run_stage(stage_idx, context)
            else:
                # Fallback simulation for demo
                result = await self._simulate_stage_execution(stage_idx, context)
            
            # Convert to dict if needed
            if not isinstance(result, dict):
                result = {"status": "success", "message": "Stage completed", "data": str(result)}
            
            # Add orchestration metadata by creating new dict
            enhanced_result = dict(result)
            enhanced_result.update({
                "execution_time": datetime.now().isoformat(),
                "stage_index": stage_idx,
                "orchestration_metadata": {
                    "scenario": self.state.scenario.name if self.state.scenario else "unknown",
                    "execution_mode": self.state.execution_mode,
                    "demo_parameters": self.state.scenario.demo_parameters if self.state.scenario else {}
                }
            })
            
            # Enhanced logging for demo purposes
            if enhanced_result.get("status") == "success":
                logger.info(f"Stage {stage_idx + 1} completed successfully")
            else:
                logger.warning(f"Stage {stage_idx + 1} completed with issues: {enhanced_result.get('message', 'Unknown issue')}")
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Stage {stage_idx + 1} failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "stage_index": stage_idx,
                "execution_time": datetime.now().isoformat()
            }
    
    async def _simulate_stage_execution(self, stage_idx: int, context: WorkflowContext) -> Dict[str, Any]:
        """Simulate stage execution when actual workflow engine method is not available"""
        stage_names = [
            "Network Connector",
            "Monitoring Analysis", 
            "KPI Analytics",
            "Configuration",
            "Validation",
            "Execution"
        ]
        
        # Simulate some processing time
        await asyncio.sleep(1.0)
        
        stage_name = stage_names[stage_idx] if stage_idx < len(stage_names) else f"Stage {stage_idx + 1}"
        
        return {
            "status": "success",
            "stage": stage_name,
            "message": f"{stage_name} completed successfully",
            "simulation": True,
            "data": {
                "sites_processed": len(context.network_state.get("sites", [])),
                "objectives": context.optimization_objectives,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    async def _process_approvals(self, workflow_results: Dict[str, Any]) -> Dict[str, Any]:
        """Process human approvals for configuration changes"""
        logger.info("Processing approval workflow...")
        
        if not self.state.scenario or not self.state.scenario.requires_approval:
            logger.info("Scenario does not require approval - skipping")
            return {"status": "skipped", "reason": "no_approval_required"}
        
        # Extract validation results (typically from stage 5)
        validation_stage = workflow_results.get("stage_5", {})
        if validation_stage.get("status") != "success":
            logger.warning("Validation stage failed - cannot proceed to approval")
            return {"status": "blocked", "reason": "validation_failed"}
        
        # Create approval request with all required fields
        current_time = datetime.now()
        approval_request = ApprovalRequest(
            request_id=f"demo_{self.state.scenario.name}_{current_time.strftime('%Y%m%d_%H%M%S')}",
            workflow_id=f"workflow_{current_time.strftime('%Y%m%d_%H%M%S')}",
            requester="Demo System",
            request_type="network_optimization",
            change_description=f"Network optimization for {', '.join(self.state.scenario.target_sites)}",
            business_justification="Demo scenario execution for capability showcase",
            risk_assessment=validation_stage.get("risk_assessment", {"level": "medium", "factors": []}),
            proposed_changes=validation_stage.get("proposed_changes", {}),
            expected_benefits=self.state.scenario.optimization_goals,
            rollback_plan={"type": "automated", "steps": ["backup_restore", "parameter_revert"]},
            monitoring_plan={"duration": "24h", "metrics": ["KPI", "performance"]},
            urgency_level=self._determine_urgency_level(),
            estimated_impact=validation_stage.get("estimated_impact", {"scope": "limited"}),
            compliance_checks={"status": "passed", "requirements": []},
            created_at=current_time,
            expires_at=current_time + timedelta(hours=24),
            approval_level_required="manager"
        )
        
        # Process through approval engine
        if self.state.execution_mode == "automated":
            # Simulate approval for automated demo
            approval_decision = self.approval_engine.simulate_human_approval(approval_request.request_id)
        else:
            # In interactive mode, we would present to user (for demo, we'll simulate)
            approval_decision = self.approval_engine.simulate_human_approval(approval_request.request_id)
        
        # Track approval decision
        self.state.approval_decisions.append({
            "request": approval_request.__dict__,
            "decision": approval_decision.__dict__,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Approval decision: {approval_decision.decision}")
        return {
            "status": "completed",
            "decision": approval_decision.decision,
            "approval_details": approval_decision.__dict__
        }
    
    def _determine_urgency_level(self) -> str:
        """Determine urgency level based on scenario characteristics"""
        if not self.state.scenario:
            return "low"
            
        if self.state.scenario.name == "emergency_response":
            return "critical"
        elif self.state.scenario.risk_level == "high":
            return "high"
        elif self.state.scenario.complexity_level == "advanced":
            return "medium"
        else:
            return "low"
    
    async def _simulate_execution(self, approval_results: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate the execution of approved changes"""
        logger.info("Simulating execution of approved changes...")
        
        if approval_results.get("decision") != "approved":
            logger.info("Changes not approved - skipping execution simulation")
            return {"status": "skipped", "reason": "not_approved"}
        
        # Simulate execution progress
        execution_steps = [
            "Preparing MML commands",
            "Establishing network connections",
            "Backing up current configurations",
            "Applying parameter changes",
            "Validating changes",
            "Monitoring KPI impacts",
            "Completing execution"
        ]
        
        execution_results = {
            "status": "success",
            "execution_steps": [],
            "simulated_impacts": {},
            "monitoring_data": {}
        }
        
        for step in execution_steps:
            logger.info(f"Executing: {step}")
            
            # Simulate step execution
            step_result = {
                "step": step,
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": 2.5  # Simulated duration
            }
            
            execution_results["execution_steps"].append(step_result)
            
            if self.state.execution_mode == "interactive":
                await asyncio.sleep(0.5)  # Brief pause for demonstration
        
        # Simulate KPI improvements
        execution_results["simulated_impacts"] = {
            "RACH_success_rate": {"before": "0.536%", "after": "2.1%", "improvement": "+291%"},
            "DL_IBLER": {"before": "15.94%", "after": "8.2%", "improvement": "-48.5%"},
            "call_setup_success": {"before": "92.3%", "after": "97.8%", "improvement": "+5.9%"}
        }
        
        logger.info("Execution simulation completed successfully")
        return execution_results
    
    async def _generate_final_report(
        self, 
        context: WorkflowContext,
        workflow_results: Dict[str, Any],
        approval_results: Dict[str, Any],
        execution_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive final demo report"""
        logger.info("Generating final demo report...")
        
        duration = 0
        if self.state.end_time and self.state.start_time:
            duration = (self.state.end_time - self.state.start_time).total_seconds() / 60
        
        report = {
            "demo_metadata": {
                "scenario": self.state.scenario.__dict__,
                "execution_mode": self.state.execution_mode,
                "start_time": self.state.start_time.isoformat() if self.state.start_time else None,
                "end_time": self.state.end_time.isoformat() if self.state.end_time else None,
                "duration_minutes": round(duration, 2),
                "stages_completed": self.state.current_stage
            },
            
            "workflow_execution": {
                "status": "completed" if self.state.current_stage == 6 else "partial",
                "stages": workflow_results,
                "total_stages": 6,
                "success_rate": len([r for r in workflow_results.values() if r.get("status") == "success"]) / 6 * 100
            },
            
            "approval_process": approval_results,
            "execution_simulation": execution_results,
            
            "demo_highlights": self._extract_demo_highlights(workflow_results, execution_results),
            
            "technical_summary": {
                "prompt_architecture_used": True,
                "real_data_integration": context.real_data_context.get("source") == "real_api",
                "fallback_data_sources": context.real_data_context.get("fallback_sources", []),
                "sites_analyzed": len(context.network_state.get("sites", [])),
                "optimization_goals_addressed": len(context.optimization_objectives)
            },
            
            "recommendations": self._generate_recommendations(workflow_results)
        }
        
        logger.info("Final report generated successfully")
        return report
    
    def _extract_demo_highlights(self, workflow_results: Dict[str, Any], execution_results: Dict[str, Any]) -> List[str]:
        """Extract key highlights from the demo execution"""
        highlights = []
        
        # Check for successful stages
        successful_stages = len([r for r in workflow_results.values() if r.get("status") == "success"])
        highlights.append(f"Successfully executed {successful_stages}/6 workflow stages")
        
        # Check for data integration
        if any("real_data" in str(r) for r in workflow_results.values()):
            highlights.append("Demonstrated real network data integration with fallback hierarchy")
        
        # Check for prompt architecture usage
        if any("prompt_template" in str(r) for r in workflow_results.values()):
            highlights.append("Utilized comprehensive prompt architecture for AI agent coordination")
        
        # Check for approval workflow
        if self.state.approval_decisions:
            highlights.append("Executed human approval workflow with risk assessment")
        
        # Check for execution simulation
        if execution_results.get("status") == "success":
            highlights.append("Simulated configuration changes with predicted KPI improvements")
        
        return highlights
    
    def _generate_recommendations(self, workflow_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on demo results"""
        recommendations = []
        
        # Analyze workflow performance
        failed_stages = [k for k, v in workflow_results.items() if v.get("status") != "success"]
        if failed_stages:
            recommendations.append(f"Review and improve stages: {', '.join(failed_stages)}")
        
        # Check data quality
        if any("fallback" in str(r) for r in workflow_results.values()):
            recommendations.append("Consider improving primary data source connectivity")
        
        # Performance recommendations
        recommendations.extend([
            "Implement real-time monitoring for production deployment",
            "Establish automated rollback procedures for failed changes",
            "Create comprehensive logging and alerting system",
            "Develop operator training program for approval workflow"
        ])
        
        return recommendations
    
    async def _save_demo_results(self, report: Dict[str, Any]) -> None:
        """Save demo results to file for later analysis"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        scenario_name = self.state.scenario.name if self.state.scenario else "unknown"
        filename = f"demo_results_{scenario_name}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Demo results saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save demo results: {str(e)}")
    
    def get_demo_status(self) -> Dict[str, Any]:
        """Get current demo execution status"""
        return {
            "scenario": self.state.scenario.name if self.state.scenario else None,
            "current_stage": self.state.current_stage,
            "total_stages": 6,
            "execution_mode": self.state.execution_mode,
            "start_time": self.state.start_time.isoformat() if self.state.start_time else None,
            "duration_minutes": (
                (datetime.now() - self.state.start_time).total_seconds() / 60 
                if self.state.start_time else 0
            ),
            "approval_decisions": len(self.state.approval_decisions)
        }

# Console interface for running demos without Streamlit
class ConsoleInterface:
    """Console-based interface for running demos when Streamlit is not available"""
    
    def __init__(self):
        self.orchestrator = DemoOrchestrator()
    
    def run_interactive_demo(self):
        """Run an interactive demo from the console"""
        print("\n" + "="*60)
        print("6-STAGE AGENTIC NETWORK OPTIMIZATION DEMO")
        print("="*60)
        
        # Show available scenarios
        scenarios = self.orchestrator.get_available_scenarios()
        print("\nAvailable Demo Scenarios:")
        for i, scenario in enumerate(scenarios, 1):
            print(f"{i}. {scenario['name']}")
            print(f"   Description: {scenario['description']}")
            print(f"   Duration: {scenario['duration']} | Complexity: {scenario['complexity']} | Risk: {scenario['risk']}")
            print()
        
        # Get user selection
        while True:
            try:
                choice = input(f"Select scenario (1-{len(scenarios)}): ").strip()
                scenario_idx = int(choice) - 1
                if 0 <= scenario_idx < len(scenarios):
                    selected_scenario = scenarios[scenario_idx]
                    break
                else:
                    print("Invalid selection. Please try again.")
            except (ValueError, KeyboardInterrupt):
                print("\nExiting demo...")
                return
        
        print(f"\nSelected: {selected_scenario['name']}")
        print("Starting demo execution...\n")
        
        # Run the demo
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.orchestrator.run_complete_demo(
                    selected_scenario['key'], 
                    execution_mode="interactive"
                )
            )
            
            # Display results
            self._display_results(result)
            
        except KeyboardInterrupt:
            print("\n\nDemo interrupted by user")
        except Exception as e:
            print(f"\nDemo failed with error: {str(e)}")
        finally:
            if loop:
                loop.close()
    
    def _display_results(self, result: Dict[str, Any]):
        """Display demo results in console format"""
        if "error" in result:
            print(f"\nDemo failed: {result['error']}")
            return
        
        print("\n" + "="*60)
        print("DEMO EXECUTION COMPLETED")
        print("="*60)
        
        metadata = result.get("demo_metadata", {})
        print(f"Scenario: {metadata.get('scenario', {}).get('name', 'Unknown')}")
        print(f"Duration: {metadata.get('duration_minutes', 0):.1f} minutes")
        print(f"Stages Completed: {metadata.get('stages_completed', 0)}/6")
        
        workflow = result.get("workflow_execution", {})
        print(f"Success Rate: {workflow.get('success_rate', 0):.1f}%")
        
        highlights = result.get("demo_highlights", [])
        if highlights:
            print("\nDemo Highlights:")
            for highlight in highlights:
                print(f"  • {highlight}")
        
        recommendations = result.get("recommendations", [])
        if recommendations:
            print("\nRecommendations:")
            for rec in recommendations[:3]:  # Show top 3
                print(f"  • {rec}")
        
        print(f"\nFull results saved in: demo_results/")

def main():
    """Main entry point for the demo orchestrator"""
    if len(sys.argv) > 1:
        # Command line mode
        scenario_key = sys.argv[1]
        execution_mode = sys.argv[2] if len(sys.argv) > 2 else "automated"
        
        print(f"Running demo: {scenario_key} in {execution_mode} mode")
        
        orchestrator = DemoOrchestrator()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                orchestrator.run_complete_demo(scenario_key, execution_mode)
            )
            print("Demo completed successfully!")
            print(f"Results: {json.dumps(result.get('demo_metadata', {}), indent=2)}")
        except Exception as e:
            print(f"Demo failed: {str(e)}")
        finally:
            loop.close()
    
    else:
        # Interactive console mode
        console = ConsoleInterface()
        console.run_interactive_demo()

if __name__ == "__main__":
    main()