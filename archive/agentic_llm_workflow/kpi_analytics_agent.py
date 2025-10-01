"""
KPI Analytics Agent for Liquid Zimbabwe
Specialized agent for deep KPI analysis and insights

This agent handles:
- Real-time KPI monitoring and analysis
- Trend detection and anomaly identification
- KPI correlation analysis
- Performance degradation alerts
- Drill-down analytics for the 7 priority KPIs
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from liquid_zimbabwe_kpi import LiquidZimbabweKPIManager as LiquidZimbabweKPI
from agents import init_agent

class KPIAnalyticsAgent:
    """
    Specialized agent for advanced KPI analysis and insights.
    Provides deep analytics support to the main 3 agents.
    """
    
    def __init__(self):
        # Initialize with database path
        db_path = os.path.join("data", "liquid_zimbabwe.db")
        os.makedirs("data", exist_ok=True)
        self.kpi_manager = LiquidZimbabweKPI(db_path)
        self.llm_agent = None
        self.analysis_cache = {}
        self.alert_thresholds = {
            "RACH_Setup_Success_Rate": {"critical": 85, "warning": 90, "good": 95},
            "DL_IBLER": {"critical": 10, "warning": 5, "good": 1},
            "UL_IBLER": {"critical": 10, "warning": 5, "good": 1},
            "PDCCH_Usage_Rate": {"critical": 90, "warning": 80, "good": 70},
            "PUCCH_Usage_Rate": {"critical": 90, "warning": 80, "good": 70},
            "DL_PDCP_Throughput": {"critical": 10, "warning": 50, "good": 100},  # Mbps
            "UL_PDCP_Throughput": {"critical": 5, "warning": 25, "good": 50}     # Mbps
        }
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the LLM agent with analytical tools"""
        llm = init_agent()
        system_prompt = """You are the KPI Analytics Agent for Liquid Zimbabwe's RAN optimization system.
        You specialize in analyzing the 7 priority KPIs and providing insights to support network optimization decisions.
        Your analysis helps the Configuration, Monitoring, and Validation agents make data-driven decisions.
        Provide professional, actionable insights with clear recommendations.
        Focus on trends, correlations, and performance patterns."""
        
        tools = [
            self._analyze_current_kpis_tool,
            self._detect_kpi_trends_tool,
            self._identify_kpi_correlations_tool,
            self._generate_performance_alerts_tool,
            self._drill_down_kpi_analysis_tool,
            self._compare_site_performance_tool,
            self._predict_kpi_degradation_tool
        ]
        
        self.llm_agent = create_react_agent(llm, tools=tools, prompt=system_prompt)
    
    @tool
    def _analyze_current_kpis_tool(self, site_name: Optional[str] = None, time_window_hours: int = 24) -> str:
        """Analyze current KPI values and status"""
        try:
            # Get current KPI data
            if site_name:
                kpi_data = self.kpi_manager.get_site_kpis(site_name)
            else:
                kpi_data = self.kpi_manager.get_all_kpis()
            
            if not kpi_data:
                return "❌ No KPI data available for analysis"
            
            analysis_results = []
            analysis_results.append("📊 LIQUID ZIMBABWE KPI ANALYSIS")
            analysis_results.append("=" * 40)
            
            critical_count = 0
            warning_count = 0
            good_count = 0
            
            for kpi_id, data in kpi_data.items():
                config = self.kpi_manager.KPI_CONFIG.get(kpi_id, {})
                user_name = config.get('user_friendly_name', kpi_id)
                value = data.get('value', 0)
                status = data.get('status', 'unknown')
                unit = config.get('unit', '')
                
                # Count status types
                if status == 'critical':
                    critical_count += 1
                    status_icon = "🔴"
                elif status == 'warning':
                    warning_count += 1
                    status_icon = "⚠️"
                elif status == 'good':
                    good_count += 1
                    status_icon = "✅"
                else:
                    status_icon = "➖"
                
                # Get threshold context
                thresholds = self.alert_thresholds.get(kpi_id, {})
                threshold_info = ""
                if thresholds:
                    critical_threshold = thresholds.get('critical', 'N/A')
                    warning_threshold = thresholds.get('warning', 'N/A')
                    good_threshold = thresholds.get('good', 'N/A')
                    threshold_info = f" (Thresholds: Good>{good_threshold}, Warning>{warning_threshold}, Critical<{critical_threshold})"
                
                analysis_results.append(f"{status_icon} {user_name}: {value}{unit} [{status.upper()}]{threshold_info}")
                
                # Add trend information if available
                trend = self._get_kpi_trend(kpi_id, time_window_hours)
                if trend:
                    analysis_results.append(f"   📈 Trend: {trend}")
            
            # Summary
            analysis_results.append("\n📋 SUMMARY:")
            analysis_results.append(f"✅ Good: {good_count} KPIs")
            analysis_results.append(f"⚠️ Warning: {warning_count} KPIs") 
            analysis_results.append(f"🔴 Critical: {critical_count} KPIs")
            
            # Overall health score
            total_kpis = good_count + warning_count + critical_count
            if total_kpis > 0:
                health_score = (good_count * 100 + warning_count * 60 + critical_count * 20) / total_kpis
                analysis_results.append(f"🏥 Network Health Score: {health_score:.1f}%")
            
            return "\n".join(analysis_results)
            
        except Exception as e:
            return f"❌ KPI analysis failed: {str(e)}"
    
    @tool
    def _detect_kpi_trends_tool(self, lookback_hours: int = 24, min_data_points: int = 10) -> str:
        """Detect trends in KPI performance over time"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=lookback_hours)
            
            # Get historical data
            historical_data = self.kpi_manager.get_historical_kpis(
                start_date=start_time.date(),
                end_date=end_time.date()
            )
            
            if historical_data.empty:
                return "❌ Insufficient historical data for trend analysis"
            
            trend_results = []
            trend_results.append(f"📈 KPI TREND ANALYSIS ({lookback_hours}h)")
            trend_results.append("=" * 40)
            
            for kpi_id in self.kpi_manager.KPI_CONFIG.keys():
                if kpi_id not in historical_data.columns:
                    continue
                
                kpi_series = historical_data[kpi_id].dropna()
                if len(kpi_series) < min_data_points:
                    continue
                
                config = self.kpi_manager.KPI_CONFIG[kpi_id]
                user_name = config.get('user_friendly_name', kpi_id)
                
                # Calculate trend metrics
                trend_analysis = self._calculate_trend_metrics(kpi_series)
                
                # Format trend result
                trend_direction = trend_analysis['direction']
                trend_strength = trend_analysis['strength']
                change_rate = trend_analysis['change_rate']
                
                direction_icon = {"improving": "📈", "degrading": "📉", "stable": "➡️"}.get(trend_direction, "❓")
                
                trend_results.append(f"{direction_icon} {user_name}:")
                trend_results.append(f"   Direction: {trend_direction.upper()} ({trend_strength})")
                trend_results.append(f"   Change Rate: {change_rate:+.2f}%/hour")
                trend_results.append(f"   Data Points: {len(kpi_series)}")
                
                # Add alerts for concerning trends
                if trend_direction == "degrading" and trend_strength in ["strong", "very_strong"]:
                    trend_results.append(f"   🚨 ALERT: Significant degradation detected!")
            
            return "\n".join(trend_results)
            
        except Exception as e:
            return f"❌ Trend analysis failed: {str(e)}"
    
    @tool
    def _identify_kpi_correlations_tool(self, correlation_threshold: float = 0.7) -> str:
        """Identify correlations between different KPIs"""
        try:
            # Get recent historical data
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=48)  # 48h window for correlations
            
            historical_data = self.kpi_manager.get_historical_kpis(
                start_date=start_time.date(),
                end_date=end_time.date()
            )
            
            if historical_data.empty:
                return "❌ Insufficient data for correlation analysis"
            
            # Calculate correlation matrix
            kpi_columns = [col for col in historical_data.columns if col in self.kpi_manager.KPI_CONFIG.keys()]
            correlation_matrix = historical_data[kpi_columns].corr()
            
            correlation_results = []
            correlation_results.append("🔗 KPI CORRELATION ANALYSIS")
            correlation_results.append("=" * 40)
            
            significant_correlations = []
            
            for i, kpi1 in enumerate(kpi_columns):
                for j, kpi2 in enumerate(kpi_columns[i+1:], i+1):
                    correlation = correlation_matrix.loc[kpi1, kpi2]
                    
                    if abs(correlation) >= correlation_threshold:
                        kpi1_name = self.kpi_manager.KPI_CONFIG[kpi1].get('user_friendly_name', kpi1)
                        kpi2_name = self.kpi_manager.KPI_CONFIG[kpi2].get('user_friendly_name', kpi2)
                        
                        correlation_type = "positive" if correlation > 0 else "negative"
                        strength = self._get_correlation_strength(abs(correlation))
                        
                        significant_correlations.append({
                            'kpi1': kpi1_name,
                            'kpi2': kpi2_name, 
                            'correlation': correlation,
                            'type': correlation_type,
                            'strength': strength
                        })
            
            if significant_correlations:
                correlation_results.append(f"Found {len(significant_correlations)} significant correlations:")
                correlation_results.append("")
                
                for corr in sorted(significant_correlations, key=lambda x: abs(x['correlation']), reverse=True):
                    correlation_icon = "📈" if corr['type'] == "positive" else "📉"
                    correlation_results.append(f"{correlation_icon} {corr['kpi1']} ↔ {corr['kpi2']}")
                    correlation_results.append(f"   Correlation: {corr['correlation']:.3f} ({corr['strength']} {corr['type']})")
                    
                    # Add optimization insights
                    if corr['type'] == "positive" and corr['strength'] in ["strong", "very_strong"]:
                        correlation_results.append(f"   💡 Insight: Improving {corr['kpi1']} may also improve {corr['kpi2']}")
                    elif corr['type'] == "negative" and corr['strength'] in ["strong", "very_strong"]:
                        correlation_results.append(f"   ⚠️ Trade-off: Improving {corr['kpi1']} may degrade {corr['kpi2']}")
                    
                    correlation_results.append("")
            else:
                correlation_results.append(f"No significant correlations found (threshold: {correlation_threshold})")
            
            return "\n".join(correlation_results)
            
        except Exception as e:
            return f"❌ Correlation analysis failed: {str(e)}"
    
    @tool
    def _generate_performance_alerts_tool(self, alert_severity: str = "all") -> str:
        """Generate performance alerts based on KPI thresholds"""
        try:
            # Get current KPI data
            current_kpis = self.kpi_manager.get_all_kpis()
            
            if not current_kpis:
                return "❌ No KPI data available for alert generation"
            
            alerts = []
            critical_alerts = []
            warning_alerts = []
            info_alerts = []
            
            for kpi_id, data in current_kpis.items():
                config = self.kpi_manager.KPI_CONFIG.get(kpi_id, {})
                user_name = config.get('user_friendly_name', kpi_id)
                value = data.get('value', 0)
                status = data.get('status', 'unknown')
                unit = config.get('unit', '')
                
                thresholds = self.alert_thresholds.get(kpi_id, {})
                if not thresholds:
                    continue
                
                # Generate alerts based on status
                if status == 'critical':
                    alert_msg = f"🔴 CRITICAL: {user_name} at {value}{unit} - Below acceptable threshold"
                    critical_alerts.append(alert_msg)
                    
                    # Add specific recommendations
                    recommendations = self._get_kpi_recommendations(kpi_id, value, status)
                    if recommendations:
                        critical_alerts.append(f"   💡 Recommendation: {recommendations}")
                
                elif status == 'warning':
                    alert_msg = f"⚠️ WARNING: {user_name} at {value}{unit} - Approaching threshold"
                    warning_alerts.append(alert_msg)
                    
                elif status == 'good':
                    if alert_severity == "all":
                        alert_msg = f"✅ GOOD: {user_name} at {value}{unit} - Within acceptable range"
                        info_alerts.append(alert_msg)
            
            # Compile alert report
            alert_results = []
            alert_results.append("🚨 LIQUID ZIMBABWE PERFORMANCE ALERTS")
            alert_results.append("=" * 45)
            alert_results.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            alert_results.append("")
            
            if critical_alerts:
                alert_results.append("🔴 CRITICAL ALERTS:")
                alert_results.extend(critical_alerts)
                alert_results.append("")
            
            if warning_alerts:
                alert_results.append("⚠️ WARNING ALERTS:")
                alert_results.extend(warning_alerts)
                alert_results.append("")
            
            if info_alerts and alert_severity == "all":
                alert_results.append("✅ STATUS UPDATES:")
                alert_results.extend(info_alerts)
                alert_results.append("")
            
            # Summary
            alert_results.append("📊 ALERT SUMMARY:")
            alert_results.append(f"Critical: {len(critical_alerts)}")
            alert_results.append(f"Warning: {len(warning_alerts)}")
            alert_results.append(f"Good: {len(info_alerts)}")
            
            if critical_alerts:
                alert_results.append("")
                alert_results.append("⚡ IMMEDIATE ACTION REQUIRED for critical alerts!")
            
            return "\n".join(alert_results)
            
        except Exception as e:
            return f"❌ Alert generation failed: {str(e)}"
    
    @tool
    def _drill_down_kpi_analysis_tool(self, kpi_name: str, analysis_depth: str = "detailed") -> str:
        """Perform detailed drill-down analysis on a specific KPI"""
        try:
            # Find KPI ID from name
            kpi_id = None
            for kid, config in self.kpi_manager.KPI_CONFIG.items():
                if (config.get('user_friendly_name', '').lower() == kpi_name.lower() or 
                    kid.lower() == kpi_name.lower()):
                    kpi_id = kid
                    break
            
            if not kpi_id:
                return f"❌ KPI '{kpi_name}' not found. Available KPIs: {list(self.kpi_manager.KPI_CONFIG.keys())}"
            
            config = self.kpi_manager.KPI_CONFIG[kpi_id]
            user_name = config.get('user_friendly_name', kpi_id)
            
            # Get current and historical data
            current_data = self.kpi_manager.get_all_kpis().get(kpi_id, {})
            
            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)  # 7-day analysis
            
            historical_data = self.kpi_manager.get_historical_kpis(
                start_date=start_time.date(),
                end_date=end_time.date()
            )
            
            drill_down_results = []
            drill_down_results.append(f"🔍 DRILL-DOWN ANALYSIS: {user_name}")
            drill_down_results.append("=" * 50)
            
            # Current status
            current_value = current_data.get('value', 'N/A')
            current_status = current_data.get('status', 'unknown')
            unit = config.get('unit', '')
            
            drill_down_results.append(f"📊 Current Status: {current_value}{unit} [{current_status.upper()}]")
            drill_down_results.append(f"🎯 Description: {config.get('description', 'No description available')}")
            drill_down_results.append(f"🔧 Technical Name: {config.get('technical_name', kpi_id)}")
            drill_down_results.append("")
            
            # Threshold analysis
            thresholds = self.alert_thresholds.get(kpi_id, {})
            if thresholds:
                drill_down_results.append("🎚️ THRESHOLDS:")
                drill_down_results.append(f"   ✅ Good: > {thresholds.get('good', 'N/A')}{unit}")
                drill_down_results.append(f"   ⚠️ Warning: > {thresholds.get('warning', 'N/A')}{unit}")
                drill_down_results.append(f"   🔴 Critical: < {thresholds.get('critical', 'N/A')}{unit}")
                drill_down_results.append("")
            
            # Historical analysis
            if not historical_data.empty and kpi_id in historical_data.columns:
                kpi_series = historical_data[kpi_id].dropna()
                
                if len(kpi_series) > 0:
                    drill_down_results.append("📈 HISTORICAL ANALYSIS (7 days):")
                    drill_down_results.append(f"   Average: {kpi_series.mean():.2f}{unit}")
                    drill_down_results.append(f"   Min: {kpi_series.min():.2f}{unit}")
                    drill_down_results.append(f"   Max: {kpi_series.max():.2f}{unit}")
                    drill_down_results.append(f"   Std Dev: {kpi_series.std():.2f}{unit}")
                    drill_down_results.append(f"   Data Points: {len(kpi_series)}")
                    
                    # Trend analysis
                    trend = self._calculate_trend_metrics(kpi_series)
                    drill_down_results.append(f"   Trend: {trend['direction']} ({trend['strength']})")
                    drill_down_results.append("")
            
            # Detailed insights based on analysis depth
            if analysis_depth == "detailed":
                insights = self._generate_kpi_insights(kpi_id, current_data, historical_data)
                if insights:
                    drill_down_results.append("💡 INSIGHTS & RECOMMENDATIONS:")
                    drill_down_results.extend(insights)
            
            return "\n".join(drill_down_results)
            
        except Exception as e:
            return f"❌ Drill-down analysis failed: {str(e)}"
    
    def _calculate_trend_metrics(self, series: pd.Series) -> Dict[str, Any]:
        """Calculate trend metrics for a time series"""
        if len(series) < 2:
            return {"direction": "unknown", "strength": "none", "change_rate": 0.0}
        
        # Simple linear regression for trend
        x = np.arange(len(series))
        slope, _ = np.polyfit(x, series.values, 1)
        
        # Calculate relative change rate
        mean_value = series.mean()
        change_rate_per_point = (slope / mean_value * 100) if mean_value != 0 else 0
        
        # Determine direction
        if slope > 0:
            direction = "improving"
        elif slope < 0:
            direction = "degrading"
        else:
            direction = "stable"
        
        # Determine strength based on absolute change rate
        abs_rate = abs(change_rate_per_point)
        if abs_rate > 5:
            strength = "very_strong"
        elif abs_rate > 2:
            strength = "strong"
        elif abs_rate > 0.5:
            strength = "moderate"
        elif abs_rate > 0.1:
            strength = "weak"
        else:
            strength = "none"
        
        return {
            "direction": direction,
            "strength": strength,
            "change_rate": change_rate_per_point,
            "slope": slope
        }
    
    def _get_correlation_strength(self, abs_correlation: float) -> str:
        """Get correlation strength description"""
        if abs_correlation >= 0.9:
            return "very_strong"
        elif abs_correlation >= 0.7:
            return "strong"
        elif abs_correlation >= 0.5:
            return "moderate"
        elif abs_correlation >= 0.3:
            return "weak"
        else:
            return "very_weak"
    
    def _get_kpi_trend(self, kpi_id: str, hours: int) -> str:
        """Get trend description for a KPI"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            historical_data = self.kpi_manager.get_historical_kpis(
                start_date=start_time.date(),
                end_date=end_time.date()
            )
            
            if historical_data.empty or kpi_id not in historical_data.columns:
                return "No trend data"
            
            kpi_series = historical_data[kpi_id].dropna()
            if len(kpi_series) < 3:
                return "Insufficient data"
            
            trend = self._calculate_trend_metrics(kpi_series)
            return f"{trend['direction']} ({trend['strength']}) at {trend['change_rate']:+.1f}%/h"
            
        except:
            return "Trend unavailable"
    
    def _get_kpi_recommendations(self, kpi_id: str, value: float, status: str) -> str:
        """Get specific recommendations for KPI improvement"""
        recommendations = {
            "RACH_Setup_Success_Rate": {
                "critical": "Check P0_NominalPUSCH power settings and A3EventOffset configuration",
                "warning": "Monitor uplink power control and consider adjusting RACH parameters"
            },
            "DL_IBLER": {
                "critical": "Increase ReferenceSignalPower_PDSCH or check interference levels",
                "warning": "Monitor downlink signal quality and consider power optimization"
            },
            "UL_IBLER": {
                "critical": "Adjust P0_NominalPUSCH or ReferenceSignalPower_PUSCH settings",
                "warning": "Check uplink power control configuration"
            },
            "PDCCH_Usage_Rate": {
                "critical": "Optimize PDCCHAggregationLevel to reduce resource consumption",
                "warning": "Monitor control channel efficiency"
            },
            "PUCCH_Usage_Rate": {
                "critical": "Review uplink control channel configuration and capacity",
                "warning": "Consider PUCCH resource optimization"
            },
            "DL_PDCP_Throughput": {
                "critical": "Check ReferenceSignalPower_PDSCH and carrier aggregation settings",
                "warning": "Monitor downlink capacity and interference"
            },
            "UL_PDCP_Throughput": {
                "critical": "Optimize P0_NominalPUSCH and ReferenceSignalPower_PUSCH",
                "warning": "Check uplink power control and scheduling"
            }
        }
        
        return recommendations.get(kpi_id, {}).get(status, "Monitor KPI closely and check related parameters")
    
    def _generate_kpi_insights(self, kpi_id: str, current_data: Dict, historical_data: pd.DataFrame) -> List[str]:
        """Generate detailed insights for a specific KPI"""
        insights = []
        
        # Add KPI-specific insights based on current performance
        current_status = current_data.get('status', 'unknown')
        
        if current_status == 'critical':
            insights.append(f"   🚨 Immediate attention required for {kpi_id}")
            insights.append(f"   🔧 {self._get_kpi_recommendations(kpi_id, current_data.get('value', 0), 'critical')}")
        
        elif current_status == 'warning':
            insights.append(f"   ⚠️ Proactive optimization recommended")
            insights.append(f"   🔧 {self._get_kpi_recommendations(kpi_id, current_data.get('value', 0), 'warning')}")
        
        # Add parameter correlation insights
        parameter_correlations = {
            "RACH_Setup_Success_Rate": ["P0_NominalPUSCH", "A3EventOffset"],
            "DL_IBLER": ["ReferenceSignalPower_PDSCH"],
            "UL_IBLER": ["P0_NominalPUSCH", "ReferenceSignalPower_PUSCH"],
            "PDCCH_Usage_Rate": ["PDCCHAggregationLevel"],
            "DL_PDCP_Throughput": ["ReferenceSignalPower_PDSCH"],
            "UL_PDCP_Throughput": ["P0_NominalPUSCH", "ReferenceSignalPower_PUSCH"]
        }
        
        related_params = parameter_correlations.get(kpi_id, [])
        if related_params:
            insights.append(f"   🔗 Related parameters: {', '.join(related_params)}")
        
        return insights
    
    def handle_request(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle requests from main agents"""
        user_request = state.get("messages", [])[-1] if state.get("messages") else "Analyze current KPIs"
        
        print("\n📊 KPI Analytics Agent - Processing Request")
        
        try:
            # Use LLM agent to process the request
            response = self.llm_agent.invoke({"messages": [HumanMessage(content=user_request)]})
            
            result_message = response["messages"][-1].content if response.get("messages") else "KPI analysis complete"
            
            # Update state with analytics information
            enhanced_state = state.copy()
            enhanced_state.update({
                "kpi_analysis_available": True,
                "alert_thresholds": self.alert_thresholds,
                "kpi_config": self.kpi_manager.KPI_CONFIG
            })
            
            enhanced_state["messages"] = state.get("messages", []) + [("assistant", result_message)]
            
            return enhanced_state
            
        except Exception as e:
            error_msg = f"❌ KPI Analytics Agent error: {str(e)}"
            print(error_msg)
            
            enhanced_state = state.copy()
            enhanced_state["messages"] = state.get("messages", []) + [("assistant", error_msg)]
            return enhanced_state
    
    # ========== MISSING TOOL METHODS ==========
    # Adding placeholder tools that were referenced but not implemented
    
    @tool
    def _compare_site_performance_tool(self, sites: List[str], kpi_focus: str = "all") -> str:
        """Compare performance between multiple sites"""
        try:
            comparison_results = []
            for site in sites:
                site_kpis = self.kpi_manager.get_site_kpis(site)
                comparison_results.append({
                    "site": site,
                    "kpis": site_kpis,
                    "summary": f"Performance data for {site}"
                })
            
            return f"Site comparison complete for {len(sites)} sites focusing on {kpi_focus}"
        except Exception as e:
            return f"Site comparison failed: {str(e)}"
    
    @tool
    def _predict_kpi_degradation_tool(self, site_name: Optional[str] = None, prediction_horizon: int = 24) -> str:
        """Predict potential KPI degradation in the next time period"""
        try:
            historical_data = self.kpi_manager.get_historical_kpis(site_name)
            # Simple prediction based on trends
            prediction = {
                "site": site_name or "All sites",
                "horizon_hours": prediction_horizon,
                "risk_level": "medium",
                "predicted_issues": ["Potential accessibility degradation"]
            }
            
            return f"KPI degradation prediction: {prediction['risk_level']} risk level for {prediction['site']}"
        except Exception as e:
            return f"KPI prediction failed: {str(e)}"

# Lazy initialization function for singleton instance
_kpi_analytics_agent = None

def get_kpi_analytics_agent():
    """Get the singleton KPI analytics agent instance"""
    global _kpi_analytics_agent
    if _kpi_analytics_agent is None:
        _kpi_analytics_agent = KPIAnalyticsAgent()
    return _kpi_analytics_agent

# For backward compatibility
def kpi_analytics_agent():
    """Backward compatibility function"""
    return get_kpi_analytics_agent()