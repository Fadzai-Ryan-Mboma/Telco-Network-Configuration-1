"""
Agent Orchestrator for Liquid Zimbabwe
Coordinates all 6 agents working together in real-time API environment

AGENT ECOSYSTEM:
1. Configuration Agent (ENHANCED) - Strategic optimization decisions
2. Validation Agent (ENHANCED) - Safety and validation checks  
3. Monitoring Agent (ENHANCED) - Real-time network monitoring
4. Live Network Connector Agent (NEW) - API connectivity and network health
5. KPI Analytics Agent (NEW) - Deep KPI analysis and insights
6. MML Command Agent (NEW) - Safe parameter execution

This orchestrator manages:
- Agent workflow coordination
- Real-time API integration
- State sharing between agents
- Cascading decision flows
- Safety validation chains
"""

from datetime import datetime
from typing import Dict, List, Any, Optional

# Import all agents - simplified approach without complex type dependencies
try:
    from agentic_llm_workflow.agents import configuration_agent, validation_agent, monitoring_agent
    from agentic_llm_workflow.live_network_connector_agent import live_network_connector_agent
    from agentic_llm_workflow.kpi_analytics_agent import kpi_analytics_agent
    from agentic_llm_workflow.mml_command_agent import mml_command_agent
    AGENTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some agents not available: {e}")
    AGENTS_AVAILABLE = False

class AgentOrchestrator:
    """
    Orchestrates all 6 agents working together for real-time network optimization
    """
    
    def __init__(self):
        self.workflow = None
        self.agent_status = {
            'configuration': 'ready',
            'validation': 'ready',
            'monitoring': 'ready', 
            'network_connector': 'ready',
            'kpi_analytics': 'ready',
            'mml_command': 'ready'
        }
        self.create_workflow()
    
    def create_workflow(self):
        """Create the coordinated agent workflow"""
        workflow = StateGraph(State)
        
        # Add all agent nodes
        workflow.add_node("network_connector", self.network_connector_node)
        workflow.add_node("monitoring", self.monitoring_node)
        workflow.add_node("kpi_analytics", self.kpi_analytics_node)
        workflow.add_node("configuration", self.configuration_node)
        workflow.add_node("validation", self.validation_node)
        workflow.add_node("mml_command", self.mml_command_node)
        
        # Define workflow paths based on request type
        workflow.set_entry_point("network_connector")
        
        # Network connector always runs first to ensure connectivity
        workflow.add_edge("network_connector", "monitoring")
        
        # Monitoring feeds into analytics for deeper insights
        workflow.add_edge("monitoring", "kpi_analytics")
        
        # Analytics results guide configuration decisions
        workflow.add_edge("kpi_analytics", "configuration")
        
        # Configuration changes must be validated
        workflow.add_edge("configuration", "validation")
        
        # Validated changes executed via MML commands
        workflow.add_conditional_edges(
            "validation",
            self.should_execute_changes,
            {
                "execute": "mml_command",
                "end": END
            }
        )
        
        # MML execution completes the workflow
        workflow.add_edge("mml_command", END)
        
        self.workflow = workflow.compile()
    
    def network_connector_node(self, state: State) -> State:
        """Network connectivity and health check node"""
        print("🌐 Step 1: Network Connector Agent")
        try:
            result_state = live_network_connector_agent.handle_request(state)
            result_state["last_agent"] = "network_connector"
            self.agent_status['network_connector'] = 'completed'
            return result_state
        except Exception as e:
            print(f"❌ Network Connector Agent error: {e}")
            state["agent_errors"] = state.get("agent_errors", []) + [f"network_connector: {str(e)}"]
            return state
    
    def monitoring_node(self, state: State) -> State:
        """Enhanced monitoring with live network data"""
        print("📊 Step 2: Monitoring Agent (Enhanced)")
        try:
            result_state = monitoring_agent(state)
            result_state["last_agent"] = "monitoring"
            self.agent_status['monitoring'] = 'completed'
            return result_state
        except Exception as e:
            print(f"❌ Monitoring Agent error: {e}")
            state["agent_errors"] = state.get("agent_errors", []) + [f"monitoring: {str(e)}"]
            return state
    
    def kpi_analytics_node(self, state: State) -> State:
        """Deep KPI analysis and insights"""
        print("📈 Step 3: KPI Analytics Agent")
        try:
            result_state = kpi_analytics_agent.handle_request(state)
            result_state["last_agent"] = "kpi_analytics"
            self.agent_status['kpi_analytics'] = 'completed'
            return result_state
        except Exception as e:
            print(f"❌ KPI Analytics Agent error: {e}")
            state["agent_errors"] = state.get("agent_errors", []) + [f"kpi_analytics: {str(e)}"]
            return state
    
    def configuration_node(self, state: State) -> State:
        """Strategic optimization decisions"""
        print("🔧 Step 4: Configuration Agent (Enhanced)")
        try:
            result_state = configuration_agent(state)
            result_state["last_agent"] = "configuration" 
            self.agent_status['configuration'] = 'completed'
            return result_state
        except Exception as e:
            print(f"❌ Configuration Agent error: {e}")
            state["agent_errors"] = state.get("agent_errors", []) + [f"configuration: {str(e)}"]
            return state
    
    def validation_node(self, state: State) -> State:
        """Safety and validation checks"""
        print("✅ Step 5: Validation Agent (Enhanced)")
        try:
            result_state = validation_agent(state)
            result_state["last_agent"] = "validation"
            self.agent_status['validation'] = 'completed'
            return result_state
        except Exception as e:
            print(f"❌ Validation Agent error: {e}")
            state["agent_errors"] = state.get("agent_errors", []) + [f"validation: {str(e)}"]
            return state
    
    def mml_command_node(self, state: State) -> State:
        """Safe parameter execution"""
        print("⚙️ Step 6: MML Command Agent")
        try:
            result_state = mml_command_agent.handle_request(state)
            result_state["last_agent"] = "mml_command"
            self.agent_status['mml_command'] = 'completed'
            return result_state
        except Exception as e:
            print(f"❌ MML Command Agent error: {e}")
            state["agent_errors"] = state.get("agent_errors", []) + [f"mml_command: {str(e)}"]
            return state
    
    def should_execute_changes(self, state: State) -> str:
        """Determine if changes should be executed based on validation results"""
        # Check if validation passed
        messages = state.get("messages", [])
        
        if not messages:
            return "end"
        
        last_message = messages[-1]
        if isinstance(last_message, tuple):
            content = last_message[1]
        else:
            content = str(last_message)
        
        # Look for validation approval indicators
        if any(phrase in content.lower() for phrase in [
            "validation passed",
            "approved for execution", 
            "safe to proceed",
            "changes validated"
        ]):
            return "execute"
        
        # Look for validation rejection indicators
        if any(phrase in content.lower() for phrase in [
            "validation failed",
            "not approved",
            "unsafe",
            "rejected"
        ]):
            return "end"
        
        # Check if there are proposed parameter changes
        has_changes = state.get("parameter_recommendations") or state.get("proposed_changes")
        
        return "execute" if has_changes else "end"
    
    def run_optimization_workflow(self, user_request: str, cell_id: Optional[str] = None) -> Dict[str, Any]:
        """Run the complete 6-agent optimization workflow"""
        print("\n🚀 LIQUID ZIMBABWE AGENT ECOSYSTEM ACTIVATED")
        print("=" * 55)
        print(f"Request: {user_request}")
        print(f"Target Cell: {cell_id or 'All cells'}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 55)
        
        # Reset agent status
        for agent in self.agent_status:
            self.agent_status[agent] = 'pending'
        
        # Initialize state
        initial_state = State(
            messages=[("user", user_request)],
            cell_id=cell_id,
            workflow_id=f"lz_opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            cassava_branding=True,
            liquid_zimbabwe_context=True
        )
        
        try:
            # Run the workflow
            final_state = self.workflow.invoke(initial_state)
            
            # Compile results
            results = {
                "workflow_status": "completed",
                "execution_time": (datetime.now() - initial_state.get("timestamp", datetime.now())).total_seconds(),
                "agent_status": self.agent_status.copy(),
                "final_state": final_state,
                "recommendations": self._extract_recommendations(final_state),
                "actions_taken": self._extract_actions(final_state),
                "kpi_insights": self._extract_kpi_insights(final_state),
                "network_health": self._extract_network_health(final_state)
            }
            
            print("\n✅ WORKFLOW COMPLETED SUCCESSFULLY")
            print(f"⏱️ Execution Time: {results['execution_time']:.2f} seconds")
            
            return results
            
        except Exception as e:
            print(f"\n❌ WORKFLOW FAILED: {str(e)}")
            return {
                "workflow_status": "failed",
                "error": str(e),
                "agent_status": self.agent_status.copy(),
                "partial_results": initial_state
            }
    
    def _extract_recommendations(self, state: State) -> List[str]:
        """Extract optimization recommendations from final state"""
        recommendations = []
        
        # From messages
        messages = state.get("messages", [])
        for message in messages:
            content = str(message[1]) if isinstance(message, tuple) else str(message)
            if "recommendation" in content.lower():
                recommendations.append(content)
        
        # From state fields
        if state.get("parameter_recommendations"):
            recommendations.extend(state["parameter_recommendations"])
        
        return recommendations
    
    def _extract_actions(self, state: State) -> List[str]:
        """Extract actions taken during workflow"""
        actions = []
        
        if state.get("command_history"):
            for cmd in state["command_history"]:
                if cmd.get("result") == "success":
                    actions.append(f"Executed: {cmd.get('command', 'Unknown command')}")
        
        if state.get("parameter_changes"):
            for change in state["parameter_changes"]:
                actions.append(f"Changed {change.get('parameter')}: {change.get('old_value')} → {change.get('new_value')}")
        
        return actions
    
    def _extract_kpi_insights(self, state: State) -> Dict[str, Any]:
        """Extract KPI analysis insights"""
        insights = {}
        
        if state.get("current_kpis"):
            insights["current_values"] = state["current_kpis"]
        
        if state.get("kpi_trends"):
            insights["trends"] = state["kpi_trends"]
        
        if state.get("alert_thresholds"):
            insights["thresholds"] = state["alert_thresholds"]
        
        return insights
    
    def _extract_network_health(self, state: State) -> Dict[str, Any]:
        """Extract network health information"""
        health = {}
        
        if state.get("network_status"):
            health["status"] = state["network_status"]
        
        if state.get("api_connectivity"):
            health["api_connected"] = state["api_connectivity"]
        
        if state.get("cell_status"):
            health["cell_info"] = state["cell_status"]
        
        return health
    
    def get_agent_status(self) -> Dict[str, str]:
        """Get current status of all agents"""
        return self.agent_status.copy()
    
    def run_quick_analysis(self, cell_id: str) -> Dict[str, Any]:
        """Run quick network analysis (monitoring + analytics only)"""
        print(f"\n🔍 QUICK ANALYSIS - Cell {cell_id}")
        
        # Create focused state for analysis
        analysis_state = State(
            messages=[("user", f"Analyze current performance for cell {cell_id}")],
            cell_id=cell_id,
            cassava_branding=True
        )
        
        try:
            # Run network connector and monitoring
            analysis_state = self.network_connector_node(analysis_state)
            analysis_state = self.monitoring_node(analysis_state)
            analysis_state = self.kpi_analytics_node(analysis_state)
            
            return {
                "status": "completed",
                "kpi_insights": self._extract_kpi_insights(analysis_state),
                "network_health": self._extract_network_health(analysis_state),
                "recommendations": self._extract_recommendations(analysis_state)
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}

# Singleton orchestrator instance
agent_orchestrator = AgentOrchestrator()

# Convenience functions for different workflow types
def run_full_optimization(user_request: str, cell_id: Optional[str] = None):
    """Run complete 6-agent optimization workflow"""
    return agent_orchestrator.run_optimization_workflow(user_request, cell_id)

def run_quick_analysis(cell_id: str):
    """Run quick analysis without parameter changes"""
    return agent_orchestrator.run_quick_analysis(cell_id)

def get_all_agent_status():
    """Get status of all 6 agents"""
    return agent_orchestrator.get_agent_status()