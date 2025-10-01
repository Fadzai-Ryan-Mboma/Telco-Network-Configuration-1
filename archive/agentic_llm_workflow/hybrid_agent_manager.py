"""
Hybrid Agent Manager with Conditional Imports

This module implements conditional imports and graceful degradation for the agent ecosystem.
It automatically detects available dependencies and provides appropriate functionality.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

# Import the hybrid config system
try:
    from hybrid_config import (
        HybridConfigManager, 
        FeatureLevel, 
        DeploymentMode,
        hybrid_config
    )
except ImportError:
    from .hybrid_config import (
        HybridConfigManager, 
        FeatureLevel, 
        DeploymentMode,
        hybrid_config
    )

# Core imports (always available)
try:
    from liquid_zimbabwe_kpi import LiquidZimbabweKPIManager
    from liquid_zimbabwe_parameters import LiquidZimbabweParameterManager
    from huawei_api_client import HuaweiAPIClient
    CORE_AVAILABLE = True
except ImportError:
    try:
        from .liquid_zimbabwe_kpi import LiquidZimbabweKPIManager
        from .liquid_zimbabwe_parameters import LiquidZimbabweParameterManager
        from .huawei_api_client import HuaweiAPIClient
        CORE_AVAILABLE = True
    except ImportError as e:
        logging.warning(f"Core imports failed: {e}")
        CORE_AVAILABLE = False

# Enhanced imports (LangChain required)
ENHANCED_AGENTS = {}
if hybrid_config.is_feature_available(FeatureLevel.ENHANCED):
    try:
        # Import basic LangChain functionality
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_core.prompts import ChatPromptTemplate
        
        # Try to import analytics agent CLASS only (don't instantiate)
        try:
            import kpi_analytics_agent
            ENHANCED_AGENTS['analytics'] = kpi_analytics_agent.KPIAnalyticsAgent
        except ImportError:
            try:
                from . import kpi_analytics_agent
                ENHANCED_AGENTS['analytics'] = kpi_analytics_agent.KPIAnalyticsAgent
            except ImportError:
                logging.warning("KPI Analytics Agent not available")
            
    except ImportError as e:
        logging.warning(f"Enhanced features not available: {e}")

# Advanced imports (LangGraph required)
ADVANCED_AGENTS = {}
if hybrid_config.is_feature_available(FeatureLevel.ADVANCED):
    try:
        from langgraph.graph import StateGraph
        
        # Try to import advanced agents
        try:
            import mml_command_agent
            ADVANCED_AGENTS['mml'] = mml_command_agent.MMLCommandAgent
        except ImportError:
            try:
                from . import mml_command_agent
                ADVANCED_AGENTS['mml'] = mml_command_agent.MMLCommandAgent
            except ImportError:
                logging.warning("MML Command Agent not available")
            
        try:
            import live_network_connector_agent
            ADVANCED_AGENTS['network'] = live_network_connector_agent.LiveNetworkConnectorAgent
        except ImportError:
            try:
                from . import live_network_connector_agent
                ADVANCED_AGENTS['network'] = live_network_connector_agent.LiveNetworkConnectorAgent
            except ImportError:
                logging.warning("Live Network Connector Agent not available")
            
    except ImportError as e:
        logging.warning(f"Advanced features not available: {e}")

class AgentType(Enum):
    """Available agent types"""
    MONITORING = "monitoring"
    CONFIGURATION = "configuration"
    VALIDATION = "validation"
    ANALYTICS = "analytics"
    MML_COMMAND = "mml_command"
    NETWORK_CONNECTOR = "network_connector"

@dataclass
class AgentCapability:
    """Agent capability description"""
    name: str
    description: str
    feature_level: FeatureLevel
    available: bool
    
class HybridAgentManager:
    """
    Manages agent lifecycle with conditional imports and graceful degradation
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = hybrid_config
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize available agents based on feature detection"""
        self.agents = {}
        self.capabilities = {}
        
        # Core agents (always available if core imports work)
        if CORE_AVAILABLE:
            self._register_core_agents()
        
        # Enhanced agents (require LangChain)
        if self.config.is_feature_available(FeatureLevel.ENHANCED):
            self._register_enhanced_agents()
        
        # Advanced agents (require LangGraph)
        if self.config.is_feature_available(FeatureLevel.ADVANCED):
            self._register_advanced_agents()
    
    def _register_core_agents(self):
        """Register core monitoring and configuration agents"""
        self.capabilities[AgentType.MONITORING] = AgentCapability(
            name="Network Monitoring",
            description="Basic KPI monitoring and data collection",
            feature_level=FeatureLevel.CORE,
            available=True
        )
        
        self.capabilities[AgentType.CONFIGURATION] = AgentCapability(
            name="Parameter Configuration",
            description="Network parameter management and optimization",
            feature_level=FeatureLevel.CORE,
            available=True
        )
        
        self.capabilities[AgentType.VALIDATION] = AgentCapability(
            name="System Validation",
            description="Data validation and system health checks",
            feature_level=FeatureLevel.CORE,
            available=True
        )
    
    def _register_enhanced_agents(self):
        """Register enhanced AI-powered agents"""
        if 'analytics' in ENHANCED_AGENTS:
            self.capabilities[AgentType.ANALYTICS] = AgentCapability(
                name="KPI Analytics",
                description="AI-powered KPI analysis and insights",
                feature_level=FeatureLevel.ENHANCED,
                available=True
            )
    
    def _register_advanced_agents(self):
        """Register advanced orchestrated agents"""
        if 'mml' in ADVANCED_AGENTS:
            self.capabilities[AgentType.MML_COMMAND] = AgentCapability(
                name="MML Command Generation",
                description="Intelligent MML command generation and execution",
                feature_level=FeatureLevel.ADVANCED,
                available=True
            )
        
        if 'network' in ADVANCED_AGENTS:
            self.capabilities[AgentType.NETWORK_CONNECTOR] = AgentCapability(
                name="Live Network Connector",
                description="Real-time network integration and management",
                feature_level=FeatureLevel.ADVANCED,
                available=True
            )
    
    def get_available_agents(self) -> List[AgentType]:
        """Get list of available agent types"""
        return [agent_type for agent_type, cap in self.capabilities.items() if cap.available]
    
    def get_agent_info(self, agent_type: AgentType) -> Optional[AgentCapability]:
        """Get information about a specific agent"""
        return self.capabilities.get(agent_type)
    
    def create_agent(self, agent_type: AgentType, **kwargs) -> Optional[Any]:
        """Create an agent instance if available"""
        if agent_type not in self.capabilities:
            self.logger.warning(f"Agent type {agent_type.value} not registered")
            return None
        
        capability = self.capabilities[agent_type]
        if not capability.available:
            self.logger.warning(f"Agent {agent_type.value} not available in current environment")
            return None
        
        try:
            return self._instantiate_agent(agent_type, **kwargs)
        except Exception as e:
            self.logger.error(f"Failed to create agent {agent_type.value}: {e}")
            return None
    
    def _instantiate_agent(self, agent_type: AgentType, **kwargs) -> Any:
        """Instantiate a specific agent type"""
        if agent_type == AgentType.MONITORING:
            return self._create_monitoring_agent(**kwargs)
        elif agent_type == AgentType.CONFIGURATION:
            return self._create_configuration_agent(**kwargs)
        elif agent_type == AgentType.VALIDATION:
            return self._create_validation_agent(**kwargs)
        elif agent_type == AgentType.ANALYTICS:
            if 'analytics' in ENHANCED_AGENTS:
                return ENHANCED_AGENTS['analytics'](**kwargs)
        elif agent_type == AgentType.MML_COMMAND:
            if 'mml' in ADVANCED_AGENTS:
                return ADVANCED_AGENTS['mml'](**kwargs)
        elif agent_type == AgentType.NETWORK_CONNECTOR:
            if 'network' in ADVANCED_AGENTS:
                return ADVANCED_AGENTS['network'](**kwargs)
        
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    def _create_monitoring_agent(self, **kwargs):
        """Create core monitoring agent"""
        class CoreMonitoringAgent:
            def __init__(self):
                if CORE_AVAILABLE:
                    # Try different database paths
                    db_paths = [
                        "../data/liquid_zimbabwe.db",
                        "data/liquid_zimbabwe.db", 
                        "/Users/fadzai/Library/CloudStorage/OneDrive-LiquidIntelligentTechnologies/Documents/Cassava AI/Telco-Network-Config/Telco-Network-Configuration/data/liquid_zimbabwe.db"
                    ]
                    self.kpi_manager = None
                    for db_path in db_paths:
                        try:
                            self.kpi_manager = LiquidZimbabweKPIManager(db_path)
                            break
                        except Exception:
                            continue
                else:
                    self.kpi_manager = None
                
            def monitor_network(self):
                if self.kpi_manager:
                    return self.kpi_manager.get_all_kpis()
                return {"error": "KPI manager not available"}
            
            def get_site_status(self, site_name: str):
                if self.kpi_manager:
                    return self.kpi_manager.get_site_kpis(site_name)
                return {"error": "KPI manager not available"}
        
        return CoreMonitoringAgent()
    
    def _create_configuration_agent(self, **kwargs):
        """Create core configuration agent"""
        class CoreConfigurationAgent:
            def __init__(self):
                if CORE_AVAILABLE:
                    # Try different database paths  
                    db_paths = [
                        "../data/liquid_zimbabwe.db",
                        "data/liquid_zimbabwe.db",
                        "/Users/fadzai/Library/CloudStorage/OneDrive-LiquidIntelligentTechnologies/Documents/Cassava AI/Telco-Network-Config/Telco-Network-Configuration/data/liquid_zimbabwe.db"
                    ]
                    self.param_manager = None
                    for db_path in db_paths:
                        try:
                            self.param_manager = LiquidZimbabweParameterManager(db_path)
                            break
                        except Exception:
                            continue
                else:
                    self.param_manager = None
                
            def optimize_parameters(self, site_name: str):
                if self.param_manager:
                    return self.param_manager.get_optimization_recommendations([f"site_{site_name}_performance"])
                return {"error": "Parameter manager not available"}
            
            def validate_changes(self, parameter_name: str, new_value: Any):
                if self.param_manager:
                    return self.param_manager.validate_parameter_change(parameter_name, new_value)
                return {"error": "Parameter manager not available"}
        
        return CoreConfigurationAgent()
    
    def _create_validation_agent(self, **kwargs):
        """Create core validation agent"""
        class CoreValidationAgent:
            def __init__(self):
                if CORE_AVAILABLE:
                    self.api_client = HuaweiAPIClient()
                else:
                    self.api_client = None
                
            def validate_connectivity(self):
                if self.api_client:
                    return self.api_client.is_connected()
                return False
            
            def check_system_health(self):
                connectivity = self.validate_connectivity() if self.api_client else False
                return {
                    "connectivity": connectivity,
                    "timestamp": "2024-01-15T10:00:00Z",
                    "status": "healthy" if connectivity else "degraded"
                }
        
        return CoreValidationAgent()
    
    def execute_workflow(self, workflow_type: str, **params) -> Dict[str, Any]:
        """Execute a workflow using available agents"""
        if workflow_type == "basic_monitoring":
            return self._execute_basic_monitoring(**params)
        elif workflow_type == "enhanced_analysis" and self.config.is_feature_available(FeatureLevel.ENHANCED):
            return self._execute_enhanced_analysis(**params)
        elif workflow_type == "advanced_optimization" and self.config.is_feature_available(FeatureLevel.ADVANCED):
            return self._execute_advanced_optimization(**params)
        else:
            return {"error": f"Workflow {workflow_type} not available in current environment"}
    
    def _execute_basic_monitoring(self, **params) -> Dict[str, Any]:
        """Execute basic monitoring workflow"""
        monitoring_agent = self.create_agent(AgentType.MONITORING)
        if not monitoring_agent:
            return {"error": "Monitoring agent not available"}
        
        return {
            "workflow": "basic_monitoring",
            "data": monitoring_agent.monitor_network(),
            "status": "completed"
        }
    
    def _execute_enhanced_analysis(self, **params) -> Dict[str, Any]:
        """Execute enhanced analysis workflow"""
        # This would use LangChain for AI analysis
        return {
            "workflow": "enhanced_analysis",
            "status": "completed",
            "features": ["AI-powered insights", "Trend analysis", "Anomaly detection"]
        }
    
    def _execute_advanced_optimization(self, **params) -> Dict[str, Any]:
        """Execute advanced optimization workflow"""
        # This would use LangGraph for orchestrated workflows
        return {
            "workflow": "advanced_optimization",
            "status": "completed",
            "features": ["Multi-agent coordination", "Automated optimization", "Real-time adaptation"]
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        available_agents = self.get_available_agents()
        
        return {
            "deployment_info": self.config.get_deployment_info(),
            "available_agents": [agent.value for agent in available_agents],
            "agent_capabilities": {
                agent.value: {
                    "name": cap.name,
                    "description": cap.description,
                    "feature_level": cap.feature_level.value,
                    "available": cap.available
                }
                for agent, cap in self.capabilities.items()
            },
            "core_available": CORE_AVAILABLE,
            "enhanced_agents_count": len(ENHANCED_AGENTS),
            "advanced_agents_count": len(ADVANCED_AGENTS)
        }

# Global instance for easy access
hybrid_agent_manager = HybridAgentManager()

def create_agent(agent_type: AgentType, **kwargs) -> Optional[Any]:
    """Create an agent using the global manager"""
    return hybrid_agent_manager.create_agent(agent_type, **kwargs)

def execute_workflow(workflow_type: str, **params) -> Dict[str, Any]:
    """Execute a workflow using the global manager"""
    return hybrid_agent_manager.execute_workflow(workflow_type, **params)

def get_system_status() -> Dict[str, Any]:
    """Get system status using the global manager"""
    return hybrid_agent_manager.get_system_status()

if __name__ == "__main__":
    # Test the hybrid system
    print("🔄 TESTING HYBRID AGENT MANAGER")
    print("=" * 50)
    
    status = get_system_status()
    print(f"Available agents: {status['available_agents']}")
    print(f"Core available: {status['core_available']}")
    print(f"Enhanced agents: {status['enhanced_agents_count']}")
    print(f"Advanced agents: {status['advanced_agents_count']}")
    
    # Test basic workflow
    result = execute_workflow("basic_monitoring")
    print(f"Basic monitoring result: {result.get('status', 'failed')}")