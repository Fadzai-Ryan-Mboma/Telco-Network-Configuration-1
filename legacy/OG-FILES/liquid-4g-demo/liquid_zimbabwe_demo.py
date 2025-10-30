#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Demo - Main Application
Comprehensive demonstration of 6-stage agentic workflow for telecom optimization
Using real Bindura network data for authentic demonstration
"""

import asyncio
import json
import logging
import os
import sys
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add agents directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

# Import agents
from network_connector import NetworkConnector
from monitoring_agent import MonitoringAgent  
from kpi_analytics_agent import KPIAnalyticsAgent
from configuration_agent import ConfigurationAgent
from validation_agent import ValidationAgent
from execution_agent import ExecutionAgent
from agent_manager import AgentManager

# Import utilities
from bindura_data_loader import BinduraDataLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/demo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LiquidZimbabweDemo:
    """
    Main demo application showcasing the complete 6-stage agentic workflow
    for telecom network optimization using real Bindura network data
    """
    
    def __init__(self):
        self.db_path = "data/demo_network.db"
        self.workflow_id = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize data loader for real Bindura data
        self.data_loader = BinduraDataLoader("../data/historical_data.csv")
        
        # Initialize agent manager
        self.agent_manager = AgentManager(self.db_path)
        
        # Initialize agents
        self.agents = {
            "network_connector": NetworkConnector(self.db_path),
            "monitoring_agent": MonitoringAgent(self.db_path),
            "kpi_analytics": KPIAnalyticsAgent(self.db_path),
            "configuration_agent": ConfigurationAgent(self.db_path),
            "validation_agent": ValidationAgent(self.db_path),
            "execution_agent": ExecutionAgent()
        }
        
        self.results = {}
        
    async def setup_database(self):
        """Setup demo database with real Bindura data"""
        logger.info("🔧 Setting up demo database with real Bindura data...")
        
        # Load real Bindura data
        analysis = self.data_loader.analyze_data()
        
        # Create database tables
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create sites table with real Bindura sites
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sites (
                site_id TEXT PRIMARY KEY,
                site_name TEXT,
                latitude REAL,
                longitude REAL,
                technology TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert real Bindura sites
        bindura_sites = [
            ("MSH0013", "MSH0013-Bindura-Zaoga", -17.3014, 31.3269, "4G", "active"),
            ("MSH0331", "MSH-0331-Chiwaridzo 2", -17.3089, 31.3187, "4G", "active"), 
            ("MSH0112", "MSH-0112-Bindura Hospital", -17.3025, 31.3156, "4G", "active"),
            ("MSH0014", "MSH-0014-Chipadze", -17.2967, 31.3298, "4G", "active")
        ]
        
        cursor.executemany('''
            INSERT OR REPLACE INTO sites (site_id, site_name, latitude, longitude, technology, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', bindura_sites)
        
        # Create KPI data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kpi_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id TEXT,
                timestamp TIMESTAMP,
                kpi_name TEXT,
                kpi_value REAL,
                FOREIGN KEY (site_id) REFERENCES sites (site_id)
            )
        ''')
        
        # Insert real KPI data from Bindura analysis
        current_time = datetime.now()
        real_kpi_data = []
        
        for site in ["MSH0013", "MSH0331", "MSH0112", "MSH0014"]:
            # Insert real critical KPI values based on analysis
            real_kpi_data.extend([
                (site, current_time, "rach_setup_success_rate", 0.536),  # Real measured value
                (site, current_time, "dl_ibler", 15.94),                 # Real measured value
                (site, current_time, "average_dl_throughput", 8.5),      # Converted from kbit/s
                (site, current_time, "rrc_connection_success_rate", 65.0), # Estimated
                (site, current_time, "erab_setup_success_rate", 60.0),   # Estimated
                (site, current_time, "handover_success_rate", 55.0),     # Estimated
                (site, current_time, "call_drop_rate", 12.0),            # Estimated
            ])
        
        cursor.executemany('''
            INSERT INTO kpi_data (site_id, timestamp, kpi_name, kpi_value)
            VALUES (?, ?, ?, ?)
        ''', real_kpi_data)
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Database setup complete with {len(bindura_sites)} real Bindura sites")
        
    async def run_complete_workflow(self):
        """Execute the complete 6-stage agentic workflow"""
        logger.info(f"🚀 Starting complete agentic workflow: {self.workflow_id}")
        
        workflow_context = {
            "workflow_id": self.workflow_id,
            "start_time": datetime.now().isoformat(),
            "target_region": "Bindura, Zimbabwe",
            "optimization_objective": "Critical RACH and IBLER optimization",
            "previous_results": {},
            "real_data_source": "bindura_historical_data.csv"
        }
        
        try:
            # Stage 1: Network Connectivity
            logger.info("📡 Stage 1: Network Connectivity & Site Discovery")
            stage1_result = await self.agents["network_connector"].execute(workflow_context)
            self.results["stage_1"] = stage1_result
            workflow_context["previous_results"]["network_connector"] = stage1_result
            
            # Stage 2: Monitoring & Data Collection  
            logger.info("📊 Stage 2: Monitoring & Data Collection")
            stage2_result = await self.agents["monitoring_agent"].execute(workflow_context)
            self.results["stage_2"] = stage2_result
            workflow_context["previous_results"]["monitoring_agent"] = stage2_result
            
            # Stage 3: KPI Analytics
            logger.info("📈 Stage 3: Advanced KPI Analytics")
            stage3_result = await self.agents["kpi_analytics"].execute(workflow_context)
            self.results["stage_3"] = stage3_result
            workflow_context["previous_results"]["kpi_analytics"] = stage3_result
            
            # Stage 4: Configuration Generation
            logger.info("⚙️ Stage 4: Configuration Generation")
            stage4_result = await self.agents["configuration_agent"].execute(workflow_context)
            self.results["stage_4"] = stage4_result
            workflow_context["previous_results"]["configuration_agent"] = stage4_result
            
            # Stage 5: Validation & Safety Checks
            logger.info("✅ Stage 5: Validation & Safety Checks")
            stage5_result = await self.agents["validation_agent"].execute(workflow_context)
            self.results["stage_5"] = stage5_result
            workflow_context["previous_results"]["validation_agent"] = stage5_result
            
            # Stage 6: Execution (Simulation)
            logger.info("🔧 Stage 6: Configuration Execution")
            stage6_result = await self.agents["execution_agent"].execute(workflow_context)
            self.results["stage_6"] = stage6_result
            
            # Generate comprehensive summary
            await self.generate_workflow_summary()
            
            logger.info("🎉 Complete agentic workflow execution finished successfully!")
            
        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {str(e)}")
            raise
    
    async def generate_workflow_summary(self):
        """Generate comprehensive workflow summary with real data insights"""
        logger.info("📋 Generating comprehensive workflow summary...")
        
        # Real Bindura data analysis
        bindura_analysis = self.data_loader.analyze_data()
        
        summary = {
            "workflow_metadata": {
                "workflow_id": self.workflow_id,
                "execution_date": datetime.now().isoformat(),
                "total_stages": 6,
                "data_source": "real_bindura_network_historical_data",
                "optimization_scope": "critical_performance_issues"
            },
            "real_network_baseline": {
                "data_source": bindura_analysis["status"],
                "total_records": bindura_analysis["total_records"],
                "sites_analyzed": bindura_analysis["sites"],
                "date_range": bindura_analysis["date_range"],
                "critical_findings": bindura_analysis["critical_findings"],
                "optimization_opportunities": bindura_analysis["optimization_opportunities"]
            },
            "stage_execution_summary": {},
            "key_insights": {
                "critical_issues_identified": [
                    f"RACH Success Rate: {bindura_analysis['critical_findings']['rach_performance']['value']} - {bindura_analysis['critical_findings']['rach_performance']['priority']} priority",
                    f"DL IBLER: {bindura_analysis['critical_findings']['dl_quality']['value']} - {bindura_analysis['critical_findings']['dl_quality']['priority']} priority"
                ],
                "optimization_potential": [
                    f"RACH improvement: {bindura_analysis['optimization_opportunities']['rach_configuration']['description']}",
                    f"DL Quality improvement: {bindura_analysis['optimization_opportunities']['dl_quality_optimization']['description']}"
                ],
                "real_world_impact": [
                    "Extremely poor RACH performance (0.536%) indicates severe accessibility issues",
                    "High IBLER (15.94%) suggests significant quality problems affecting user experience",
                    "Low throughput indicates capacity constraints requiring immediate optimization"
                ]
            },
            "recommendations": {
                "immediate_actions": [
                    "Implement critical RACH parameter optimization",
                    "Deploy DL quality enhancement configurations", 
                    "Increase monitoring frequency for real-time performance tracking"
                ],
                "medium_term_actions": [
                    "Comprehensive RF optimization across all Bindura sites",
                    "Load balancing configuration to improve capacity",
                    "Implement proactive alarm management"
                ],
                "long_term_strategy": [
                    "Consider site densification in high-traffic areas",
                    "Implement AI-driven continuous optimization",
                    "Deploy advanced antenna systems for coverage improvement"
                ]
            }
        }
        
        # Add stage-specific summaries
        for stage_name, stage_result in self.results.items():
            if stage_result.get("status") == "success":
                summary["stage_execution_summary"][stage_name] = {
                    "agent_name": stage_result.get("agent_name"),
                    "execution_duration": stage_result.get("analytics_summary", {}).get("analysis_duration_seconds") or 
                                         stage_result.get("monitoring_summary", {}).get("collection_duration_seconds") or
                                         stage_result.get("configuration_summary", {}).get("generation_duration_seconds") or
                                         stage_result.get("validation_summary", {}).get("validation_duration_seconds") or 0,
                    "key_outputs": self._extract_key_outputs(stage_result),
                    "status": "success"
                }
        
        # Save summary to file
        summary_file = f"logs/workflow_summary_{self.workflow_id}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Print key insights
        print("\n" + "="*80)
        print("🎯 LIQUID ZIMBABWE 4G AGENTIC WORKFLOW - EXECUTION SUMMARY")
        print("="*80)
        print(f"Workflow ID: {self.workflow_id}")
        print(f"Real Data Source: Bindura Network Historical Data")
        print(f"Sites Analyzed: {bindura_analysis['sites']}")
        print(f"Records Processed: {bindura_analysis['total_records']}")
        
        print("\n🚨 CRITICAL FINDINGS:")
        for finding in summary["key_insights"]["critical_issues_identified"]:
            print(f"   • {finding}")
        
        print("\n🎯 OPTIMIZATION OPPORTUNITIES:")
        for opportunity in summary["key_insights"]["optimization_potential"]:
            print(f"   • {opportunity}")
        
        print("\n📋 IMMEDIATE RECOMMENDATIONS:")
        for recommendation in summary["recommendations"]["immediate_actions"]:
            print(f"   • {recommendation}")
        
        print(f"\n📄 Full summary saved to: {summary_file}")
        print("="*80)
        
    def _extract_key_outputs(self, stage_result: Dict) -> List[str]:
        """Extract key outputs from stage result"""
        outputs = []
        
        if "target_sites" in stage_result:
            outputs.append(f"Sites discovered: {len(stage_result['target_sites'])}")
        
        if "kpi_collection" in stage_result:
            kpis = stage_result["kpi_collection"].get("latest_values", {})
            outputs.append(f"KPIs collected: {len(kpis)}")
        
        if "correlation_analysis" in stage_result:
            correlations = stage_result["correlation_analysis"].get("significant_correlations", 0)
            outputs.append(f"Correlations identified: {correlations}")
        
        if "configuration_changes" in stage_result:
            changes = stage_result["configuration_changes"].get("total_changes", 0)
            outputs.append(f"Configuration changes: {changes}")
        
        if "validation_summary" in stage_result:
            tests = stage_result["validation_summary"].get("tests_passed", 0)
            outputs.append(f"Validation tests passed: {tests}")
        
        return outputs or ["Stage completed successfully"]

async def main():
    """Main demo execution"""
    print("\n🇿🇼 LIQUID ZIMBABWE 4G NETWORK OPTIMIZATION DEMO")
    print("=" * 60)
    print("Real Bindura Network Data Integration & 6-Stage Agentic Workflow")
    print("=" * 60)
    
    # Ensure required directories exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Initialize and run demo
    demo = LiquidZimbabweDemo()
    
    try:
        # Setup database with real data
        await demo.setup_database()
        
        # Run complete workflow
        await demo.run_complete_workflow()
        
        print("\n✅ Demo completed successfully!")
        print("Check logs/ directory for detailed results and analysis.")
        
    except Exception as e:
        logger.error(f"Demo execution failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))