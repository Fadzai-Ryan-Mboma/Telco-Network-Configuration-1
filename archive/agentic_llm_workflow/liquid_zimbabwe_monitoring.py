"""
Liquid Zimbabwe Real Network Monitoring Agent

This module provides monitoring functionality specifically designed for 
Liquid Zimbabwe's real network data, replacing the BubbleRAN simulation-based monitoring.
"""

import time
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Generator, Optional, Union
from liquid_zimbabwe_kpi import LiquidZimbabweKPIManager
import yaml


class LiquidZimbabweMonitor:
    """
    Real Network Monitoring Agent for Liquid Zimbabwe
    
    Monitors actual network KPIs and identifies performance issues
    using real Bindura site data instead of simulation parameters.
    """
    
    def __init__(self, db_path: str = "../data/liquid_zimbabwe.db"):
        self.kpi_manager = LiquidZimbabweKPIManager(db_path)
        self.config = yaml.safe_load(open('../config.yaml', 'r'))
        
        # KPI monitoring thresholds (based on your real data ranges)
        self.thresholds = {
            'network_access_success': {'critical': 0.2, 'warning': 0.4, 'target': 0.8},
            'download_quality': {'critical': 20.0, 'warning': 17.0, 'target': 12.0},  # IBLER - lower is better
            'upload_quality': {'critical': 15.0, 'warning': 10.0, 'target': 5.0},    # IBLER - lower is better  
            'control_channel_load': {'critical': 50.0, 'warning': 40.0, 'target': 25.0},
            'feedback_channel_load': {'critical': 10.0, 'warning': 7.0, 'target': 3.0},
            'download_speed': {'critical': 10.0, 'warning': 15.0, 'target': 25.0},   # Higher is better
            'upload_speed': {'critical': 3.0, 'warning': 5.0, 'target': 8.0}        # Higher is better
        }
        
        # Access KPI configuration
        self.kpi_config = self.kpi_manager.KPI_CONFIG
        
    def monitor_network_kpis(self, site_name: Optional[str] = None) -> Generator[str, None, Dict]:
        """
        Monitor real network KPIs for Liquid Zimbabwe sites
        
        Args:
            site_name: Specific site to monitor, or None for all sites
            
        Yields:
            Status messages during monitoring
            
        Returns:
            Monitoring results and recommendations
        """
        try:
            yield "🔍 Starting Liquid Zimbabwe Network Monitoring..."
            
            # Get current KPI summary
            if site_name:
                yield f"📊 Monitoring site: {site_name}"
                kpi_data = self.kpi_manager.get_historical_kpis(site_name=site_name)
            else:
                yield "📊 Monitoring all Bindura sites..."
                kpi_data = self.kpi_manager.get_historical_kpis()
            
            if kpi_data.empty:
                yield "❌ No KPI data available for monitoring"
                return {"status": "error", "message": "No data available"}
            
            # Analyze each KPI
            yield "🔎 Analyzing network performance..."
            kpi_analysis = {}
            alerts = []
            
            for kpi_id, config in self.kpi_config.items():
                if kpi_id in kpi_data.columns:
                    # Get recent values (last 24 hours worth)
                    recent_values = kpi_data[kpi_id].tail(144)  # 6 sites × 24 hours
                    avg_value = recent_values.mean()
                    
                    # Determine status
                    status = self._assess_kpi_status(kpi_id, avg_value)
                    kpi_analysis[kpi_id] = {
                        'current_avg': avg_value,
                        'status': status,
                        'user_friendly_name': config['user_friendly_name'],
                        'unit': config.get('unit', '')
                    }
                    
                    # Generate alerts if needed
                    if status in ['critical', 'warning']:
                        alerts.append(self._generate_alert(kpi_id, avg_value, status))
                        
                    yield f"✓ {config['user_friendly_name']}: {avg_value:.2f} {config.get('unit', '')} ({status})"
            
            # Site-specific analysis
            if not site_name:
                yield "🏢 Analyzing individual sites..."
                site_analysis = self._analyze_sites(kpi_data)
                
                # Find problem sites
                problem_sites = [site for site, data in site_analysis.items() 
                               if data.get('issues', 0) > 2]
                
                if problem_sites:
                    yield f"⚠️ Sites requiring attention: {', '.join(problem_sites)}"
                else:
                    yield "✅ All sites performing within acceptable ranges"
            
            # Generate recommendations
            yield "💡 Generating optimization recommendations..."
            recommendations = self._generate_recommendations(kpi_analysis, alerts)
            
            return {
                "status": "success",
                "kpi_analysis": kpi_analysis,
                "alerts": alerts,
                "recommendations": recommendations,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"❌ Monitoring failed: {str(e)}"
            yield error_msg
            return {"status": "error", "message": str(e)}
    
    def _assess_kpi_status(self, kpi_id: str, value: float) -> str:
        """Assess KPI status based on thresholds"""
        thresholds = self.thresholds.get(kpi_id, {})
        
        # For KPIs where lower is better (IBLER)
        if kpi_id in ['download_quality', 'upload_quality']:
            if value >= thresholds.get('critical', float('inf')):
                return 'critical'
            elif value >= thresholds.get('warning', float('inf')):
                return 'warning'
            else:
                return 'good'
        
        # For KPIs where higher is better (speeds, success rates)
        elif kpi_id in ['network_access_success', 'download_speed', 'upload_speed']:
            if value <= thresholds.get('critical', 0):
                return 'critical'
            elif value <= thresholds.get('warning', 0):
                return 'warning'
            else:
                return 'good'
        
        # For load KPIs (moderate levels are optimal)
        else:
            if value >= thresholds.get('critical', float('inf')):
                return 'critical'
            elif value >= thresholds.get('warning', float('inf')):
                return 'warning'
            else:
                return 'good'
    
    def _generate_alert(self, kpi_id: str, value: float, status: str) -> Dict:
        """Generate alert for problematic KPI"""
        config = self.kpi_config[kpi_id]
        
        return {
            'kpi_id': kpi_id,
            'kpi_name': config['user_friendly_name'],
            'current_value': value,
            'status': status,
            'message': f"{config['user_friendly_name']} is {status}: {value:.2f} {config.get('unit', '')}",
            'recommendation': self._get_kpi_recommendation(kpi_id, value, status)
        }
    
    def _get_kpi_recommendation(self, kpi_id: str, value: float, status: str) -> str:
        """Get specific recommendation for KPI issue"""
        recommendations = {
            'network_access_success': {
                'critical': "Immediate attention required - check RACH configuration and cell capacity",
                'warning': "Monitor RACH parameters and consider load balancing"
            },
            'download_quality': {
                'critical': "High error rate detected - check RF conditions and interference",
                'warning': "Elevated error rate - monitor for RF optimization opportunities"
            },
            'upload_quality': {
                'critical': "Poor uplink quality - investigate power control and interference",
                'warning': "Uplink performance degraded - consider optimization"
            },
            'control_channel_load': {
                'critical': "Control channels overloaded - urgent capacity expansion needed",
                'warning': "High control channel usage - monitor for congestion"
            },
            'feedback_channel_load': {
                'critical': "PUCCH overloaded - review channel allocation",
                'warning': "PUCCH usage elevated - monitor capacity"
            },
            'download_speed': {
                'critical': "Poor download performance - check backhaul and RF conditions",
                'warning': "Below-target download speeds - optimization recommended"
            },
            'upload_speed': {
                'critical': "Poor upload performance - investigate power control and scheduling",
                'warning': "Suboptimal upload speeds - consider parameter tuning"
            }
        }
        
        return recommendations.get(kpi_id, {}).get(status, "Monitor and optimize as needed")
    
    def _analyze_sites(self, kpi_data: pd.DataFrame) -> Dict:
        """Analyze performance by individual site"""
        site_analysis = {}
        
        if 'site_name' in kpi_data.columns:
            for site in kpi_data['site_name'].unique():
                site_data = kpi_data[kpi_data['site_name'] == site]
                
                # Count issues for this site
                issues = 0
                for kpi_id in self.kpi_config.keys():
                    if kpi_id in site_data.columns:
                        avg_value = site_data[kpi_id].mean()
                        status = self._assess_kpi_status(kpi_id, avg_value)
                        if status in ['critical', 'warning']:
                            issues += 1
                
                site_analysis[site] = {
                    'issues': issues,
                    'data_points': len(site_data),
                    'status': 'critical' if issues > 3 else 'warning' if issues > 1 else 'good'
                }
        
        return site_analysis
    
    def _generate_recommendations(self, kpi_analysis: Dict, alerts: List) -> List[str]:
        """Generate overall recommendations based on analysis"""
        recommendations = []
        
        if not alerts:
            recommendations.append("✅ Network performance is within acceptable ranges")
            recommendations.append("💡 Continue regular monitoring and maintain current configurations")
            return recommendations
        
        # Critical issues first
        critical_alerts = [alert for alert in alerts if alert['status'] == 'critical']
        if critical_alerts:
            recommendations.append("🚨 URGENT: Address critical issues immediately:")
            for alert in critical_alerts:
                recommendations.append(f"   • {alert['message']} - {alert['recommendation']}")
        
        # Warning issues
        warning_alerts = [alert for alert in alerts if alert['status'] == 'warning']
        if warning_alerts:
            recommendations.append("⚠️ WARNING: Monitor and plan optimization for:")
            for alert in warning_alerts:
                recommendations.append(f"   • {alert['message']} - {alert['recommendation']}")
        
        # General recommendations
        if len(alerts) > 3:
            recommendations.append("📋 GENERAL: Consider comprehensive network audit and optimization")
        
        return recommendations


def monitor_liquid_zimbabwe_network(site_name: Optional[str] = None) -> Union[Generator[str, None, None], Dict]:
    """
    Main monitoring function for Liquid Zimbabwe network
    
    This replaces the BubbleRAN parameter monitoring with real KPI monitoring
    """
    monitor = LiquidZimbabweMonitor()
    
    # Start monitoring and collect results
    results = None
    for message in monitor.monitor_network_kpis(site_name):
        if isinstance(message, dict):
            results = message
        else:
            yield message
    
    # Return final results
    yield "🎯 Monitoring complete!"
    return results or {"status": "error", "message": "No results generated"}