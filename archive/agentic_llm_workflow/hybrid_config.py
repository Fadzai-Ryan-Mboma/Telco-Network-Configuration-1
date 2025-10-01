"""
Hybrid Deployment Configuration Manager

This module implements the hybrid approach combining:
- Strategy 2: Conditional imports with graceful degradation
- Strategy 3: Environment separation with deployment options

Usage:
- Automatically detects available dependencies
- Provides appropriate functionality based on environment
- Supports multiple deployment configurations
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class DeploymentMode(Enum):
    """Deployment mode options"""
    BASIC = "basic"           # Core monitoring only
    ENHANCED = "enhanced"     # Basic AI features
    ADVANCED = "advanced"     # Full AI ecosystem
    HYBRID = "hybrid"         # Runtime detection

class FeatureLevel(Enum):
    """Feature availability levels"""
    CORE = "core"             # Always available
    ENHANCED = "enhanced"     # Available with basic AI packages
    ADVANCED = "advanced"     # Requires full AI ecosystem

@dataclass
class FeatureStatus:
    """Status of system features"""
    deployment_mode: DeploymentMode
    langchain_available: bool
    langgraph_available: bool
    nvidia_ai_available: bool
    core_features: bool
    enhanced_features: bool
    advanced_features: bool
    
class HybridConfigManager:
    """
    Manages hybrid deployment configuration and feature detection
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._feature_status: Optional[FeatureStatus] = None
        self._initialize_feature_detection()
        
        # Ensure initialization completed
        if self._feature_status is None:
            raise RuntimeError("Failed to initialize feature detection")
    
    def _initialize_feature_detection(self):
        """Detect available dependencies and set feature levels"""
        
        # Test for LangChain availability
        langchain_available = self._test_import('langchain_core')
        langgraph_available = self._test_import('langgraph')
        nvidia_ai_available = self._test_import('langchain_nvidia_ai_endpoints')
        
        # Determine deployment mode
        if langchain_available and langgraph_available:
            deployment_mode = DeploymentMode.ADVANCED
        elif langchain_available:
            deployment_mode = DeploymentMode.ENHANCED
        else:
            deployment_mode = DeploymentMode.BASIC
            
        # Set feature availability
        core_features = True  # Always available
        enhanced_features = langchain_available
        advanced_features = langchain_available and langgraph_available
        
        self._feature_status = FeatureStatus(
            deployment_mode=deployment_mode,
            langchain_available=langchain_available,
            langgraph_available=langgraph_available,
            nvidia_ai_available=nvidia_ai_available,
            core_features=core_features,
            enhanced_features=enhanced_features,
            advanced_features=advanced_features
        )
        
        self._log_feature_status()
    
    def _test_import(self, module_name: str) -> bool:
        """Test if a module can be imported"""
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False
    
    def _log_feature_status(self):
        """Log the current feature status"""
        if self._feature_status is None:
            self.logger.error("Feature status not initialized")
            return
            
        status = self._feature_status
        self.logger.info(f"🚀 Hybrid System Initialization")
        self.logger.info(f"   Deployment Mode: {status.deployment_mode.value}")
        self.logger.info(f"   Core Features: {'✅' if status.core_features else '❌'}")
        self.logger.info(f"   Enhanced Features: {'✅' if status.enhanced_features else '❌'}")
        self.logger.info(f"   Advanced Features: {'✅' if status.advanced_features else '❌'}")
        
        if not status.enhanced_features:
            self.logger.warning("⚠️ Enhanced features disabled - install LangChain for AI capabilities")
        if not status.advanced_features:
            self.logger.warning("⚠️ Advanced features disabled - install LangGraph for orchestration")
    
    @property
    def feature_status(self) -> FeatureStatus:
        """Get current feature status"""
        if self._feature_status is None:
            raise RuntimeError("Feature status not initialized")
        return self._feature_status
    
    def is_feature_available(self, feature_level: FeatureLevel) -> bool:
        """Check if a feature level is available"""
        if self._feature_status is None:
            return False
            
        if feature_level == FeatureLevel.CORE:
            return self._feature_status.core_features
        elif feature_level == FeatureLevel.ENHANCED:
            return self._feature_status.enhanced_features
        elif feature_level == FeatureLevel.ADVANCED:
            return self._feature_status.advanced_features
        return False
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent types"""
        agents = ["monitoring", "configuration", "validation"]  # Core agents
        
        if self.is_feature_available(FeatureLevel.ENHANCED):
            agents.extend(["kpi_analytics", "parameter_optimization"])
            
        if self.is_feature_available(FeatureLevel.ADVANCED):
            agents.extend(["mml_command", "live_network_connector", "orchestrated_workflow"])
            
        return agents
    
    def get_deployment_info(self) -> Dict[str, Any]:
        """Get comprehensive deployment information"""
        if self._feature_status is None:
            return {"error": "Feature status not initialized"}
            
        status = self._feature_status
        return {
            "deployment_mode": status.deployment_mode.value,
            "version": "2.0.0-hybrid",
            "features": {
                "core_monitoring": status.core_features,
                "ai_analytics": status.enhanced_features,
                "smart_optimization": status.enhanced_features,
                "advanced_orchestration": status.advanced_features,
                "live_network_management": status.advanced_features
            },
            "dependencies": {
                "langchain": status.langchain_available,
                "langgraph": status.langgraph_available,
                "nvidia_ai": status.nvidia_ai_available
            },
            "available_agents": self.get_available_agents(),
            "resource_requirements": self._get_resource_requirements()
        }
    
    def _get_resource_requirements(self) -> Dict[str, str]:
        """Get estimated resource requirements"""
        if self._feature_status is None:
            return {"error": "Feature status not initialized"}
            
        mode = self._feature_status.deployment_mode
        
        if mode == DeploymentMode.BASIC:
            return {
                "memory": "512MB - 1GB",
                "disk": "50MB",
                "cpu": "Low",
                "startup_time": "10-15 seconds"
            }
        elif mode == DeploymentMode.ENHANCED:
            return {
                "memory": "1-2GB", 
                "disk": "200MB",
                "cpu": "Medium",
                "startup_time": "30-45 seconds"
            }
        else:  # ADVANCED
            return {
                "memory": "2-4GB",
                "disk": "600MB",
                "cpu": "High", 
                "startup_time": "60-90 seconds"
            }

# Global instance for easy access
hybrid_config = HybridConfigManager()

def get_feature_status() -> FeatureStatus:
    """Get current feature status"""
    return hybrid_config.feature_status

def is_feature_available(feature_level: FeatureLevel) -> bool:
    """Check if a feature level is available"""
    return hybrid_config.is_feature_available(feature_level)

def get_deployment_info() -> Dict[str, Any]:
    """Get deployment information"""
    return hybrid_config.get_deployment_info()

def print_system_status():
    """Print comprehensive system status"""
    info = get_deployment_info()
    status = get_feature_status()
    
    print("🔄 HYBRID TELCO NETWORK MONITORING SYSTEM")
    print("=" * 50)
    print(f"🚀 Deployment Mode: {info['deployment_mode'].upper()}")
    print(f"📦 Version: {info['version']}")
    print()
    
    print("✅ AVAILABLE FEATURES:")
    for feature, available in info['features'].items():
        icon = "✅" if available else "❌"
        print(f"   {icon} {feature.replace('_', ' ').title()}")
    print()
    
    print("📊 DEPENDENCY STATUS:")
    for dep, available in info['dependencies'].items():
        icon = "✅" if available else "❌"
        print(f"   {icon} {dep}")
    print()
    
    print("🤖 AVAILABLE AGENTS:")
    for agent in info['available_agents']:
        print(f"   ✅ {agent.replace('_', ' ').title()}")
    print()
    
    print("💻 RESOURCE REQUIREMENTS:")
    for resource, requirement in info['resource_requirements'].items():
        print(f"   📈 {resource.title()}: {requirement}")
    print()
    
    if status.deployment_mode == DeploymentMode.BASIC:
        print("💡 UPGRADE HINTS:")
        print("   To enable advanced features:")
        print("   pip install langchain langchain-core langgraph")
        print()

if __name__ == "__main__":
    print_system_status()