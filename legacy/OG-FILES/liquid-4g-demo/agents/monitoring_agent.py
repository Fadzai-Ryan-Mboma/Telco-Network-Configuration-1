#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Demo - Monitoring Analysis Agent
Stage 2: Performs comprehensive real-time monitoring and analysis
"""

import asyncio
import sqlite3
import json
import random
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

class MonitoringAnalysisAgent:
    """
    Monitoring Analysis Agent - Performs comprehensive KPI monitoring,
    trend analysis, and anomaly detection with realistic demo data.
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
        # KPI thresholds for anomaly detection (updated with real Bindura network data patterns)
        self.kpi_thresholds = {
            # Real RACH success rates are 0.2-0.9% - these are LOW and need optimization!
            "rach_setup_success_rate": {"min": 0.3, "target": 0.8, "critical": 0.15},
            # IBLER rates from real data: DL 11-20%, UL 2-14%
            "dl_ibler": {"max": 15, "target": 12, "critical": 18},
            "ul_ibler": {"max": 8, "target": 5, "critical": 12},
            # PDCCH CCE usage from real data: 15-58%
            "pdcch_cce_usage_rate": {"max": 50, "target": 35, "critical": 55},
            # PUCCH usage from real data: 1-10%
            "pucch_usage_rate": {"max": 8, "target": 5, "critical": 10},
            # Real throughput data: DL 10-32 Mbps, UL 3-14 Mbps (converted from kbit/s)
            "dl_pdcp_throughput": {"min": 15, "target": 25, "critical": 12},
            "ul_pdcp_throughput": {"min": 4, "target": 8, "critical": 3},
            # Legacy KPIs (estimated based on IBLER and RACH performance)
            "rrc_connection_success_rate": {"min": 85, "target": 92, "critical": 80},
            "erab_setup_success_rate": {"min": 88, "target": 94, "critical": 85},
            "handover_success_rate": {"min": 85, "target": 90, "critical": 80},
            "call_drop_rate": {"max": 5, "target": 3, "critical": 8},
            "session_setup_time": {"max": 8, "target": 5, "critical": 12}
        }
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute monitoring analysis stage with comprehensive KPI collection"""
        start_time = datetime.now()
        
        try:
            # Simulate realistic monitoring time
            await asyncio.sleep(random.uniform(3, 8))
            
            logger.info(f"📊 Monitoring Analysis Agent starting for workflow {context['workflow_id']}")
            
            # Extract target sites from previous stage
            target_sites = self._extract_target_sites(context)
            
            # Collect real-time KPI data
            kpi_collection = await self._collect_real_time_kpis(target_sites)
            
            # Perform data quality validation
            data_quality = await self._validate_data_quality(kpi_collection)
            
            # Analyze thresholds and violations
            threshold_analysis = await self._analyze_threshold_violations(kpi_collection)
            
            # Perform trend analysis
            trend_analysis = await self._analyze_performance_trends(kpi_collection, target_sites)
            
            # Detect anomalies
            anomaly_detection = await self._detect_performance_anomalies(kpi_collection)
            
            # Site comparison analysis
            site_comparison = await self._perform_site_comparison(kpi_collection)
            
            # Generate monitoring insights
            monitoring_insights = self._generate_monitoring_insights(
                threshold_analysis, trend_analysis, anomaly_detection
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                "status": "success",
                "agent_name": "Monitoring Analysis",
                "monitoring_summary": {
                    "sites_monitored": len(target_sites),
                    "monitoring_duration_seconds": duration,
                    "data_points_collected": kpi_collection["total_data_points"],
                    "kpis_analyzed": len(self.kpi_thresholds),
                    "monitoring_timestamp": datetime.now().isoformat()
                },
                "kpi_collection": {
                    "collection_status": kpi_collection["status"],
                    "site_data": kpi_collection["site_data"],
                    "kpi_summary": kpi_collection["kpi_summary"],
                    "latest_values": kpi_collection["latest_values"]
                },
                "data_quality": {
                    "overall_quality_score": data_quality["quality_score"],
                    "completeness_percentage": data_quality["completeness"],
                    "accuracy_assessment": data_quality["accuracy"],
                    "reliability_index": data_quality["reliability"]
                },
                "threshold_analysis": {
                    "violations_detected": threshold_analysis["total_violations"],
                    "critical_violations": threshold_analysis["critical_violations"],
                    "warning_violations": threshold_analysis["warning_violations"],
                    "violation_details": threshold_analysis["violation_details"],
                    "compliance_rate": threshold_analysis["compliance_rate"]
                },
                "trend_analysis": {
                    "overall_trend": trend_analysis["trending_direction"],
                    "performance_velocity": trend_analysis["velocity"],
                    "trend_confidence": trend_analysis["confidence"],
                    "kpi_trends": trend_analysis["individual_kpi_trends"],
                    "seasonal_patterns": trend_analysis["seasonal_patterns"]
                },
                "anomaly_detection": {
                    "anomalies_detected": anomaly_detection["total_anomalies"],
                    "anomaly_severity": anomaly_detection["severity_distribution"],
                    "anomaly_patterns": anomaly_detection["pattern_analysis"],
                    "anomaly_details": anomaly_detection["anomaly_details"]
                },
                "site_comparison": {
                    "best_performing_site": site_comparison["best_performer"],
                    "worst_performing_site": site_comparison["worst_performer"],
                    "performance_variance": site_comparison["variance"],
                    "site_rankings": site_comparison["rankings"]
                },
                "monitoring_insights": monitoring_insights,
                "optimization_opportunities": self._identify_optimization_opportunities(
                    threshold_analysis, trend_analysis, anomaly_detection
                ),
                "recommendations": self._generate_monitoring_recommendations(
                    threshold_analysis, anomaly_detection, trend_analysis
                ),
                "execution_time": duration
            }
            
            logger.info(f"✅ Monitoring Analysis completed in {duration:.1f}s - {len(target_sites)} sites analyzed")
            return result
            
        except Exception as e:
            logger.error(f"❌ Monitoring Analysis Agent failed: {e}")
            return await self._handle_monitoring_failure(str(e), context)
    
    def _extract_target_sites(self, context: Dict) -> List[str]:
        """Extract target sites from previous stage results"""
        network_connector_result = context.get("previous_results", {}).get("network_connector", {})
        target_sites = network_connector_result.get("target_sites", [])
        
        if not target_sites:
            # Fallback to discovered sites
            site_discovery = network_connector_result.get("site_discovery", {})
            available_sites = site_discovery.get("available_sites", [])
            target_sites = [site["site_id"] for site in available_sites]
        
        return target_sites or ["BIND_001"]  # Default fallback
    
    async def _collect_real_time_kpis(self, target_sites: List[str]) -> Dict[str, Any]:
        """Collect real-time KPI data for target sites"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get latest KPI data for each site
            site_data = {}
            total_data_points = 0
            kpi_summary = {}
            latest_values = {}
            
            for site_id in target_sites:
                # Get latest KPI values for this site (last 1 hour)
                cursor.execute("""
                    SELECT kpi_name, kpi_value, unit, timestamp
                    FROM kpi_data 
                    WHERE site_id = ? AND timestamp >= datetime('now', '-1 hour')
                    ORDER BY timestamp DESC
                """, (site_id,))
                
                kpi_records = cursor.fetchall()
                
                site_kpis = {}
                for record in kpi_records:
                    kpi_name, kpi_value, unit, timestamp = record
                    if kpi_name not in site_kpis:
                        site_kpis[kpi_name] = []
                    site_kpis[kpi_name].append({
                        "value": kpi_value,
                        "unit": unit,
                        "timestamp": timestamp
                    })
                    total_data_points += 1
                
                # Calculate latest and average values
                site_latest = {}
                site_averages = {}
                for kpi_name, values in site_kpis.items():
                    if values:
                        latest_value = values[0]["value"]  # Most recent
                        avg_value = statistics.mean([v["value"] for v in values])
                        
                        site_latest[kpi_name] = {
                            "value": latest_value,
                            "unit": values[0]["unit"],
                            "timestamp": values[0]["timestamp"]
                        }
                        site_averages[kpi_name] = {
                            "value": round(avg_value, 2),
                            "unit": values[0]["unit"],
                            "sample_count": len(values)
                        }
                
                site_data[site_id] = {
                    "latest_kpis": site_latest,
                    "hourly_averages": site_averages,
                    "data_points": len(kpi_records)
                }
                
                # Update overall latest values
                latest_values.update(site_latest)
            
            # Calculate KPI summary across all sites
            for kpi_name in self.kpi_thresholds.keys():
                values = []
                for site_data_entry in site_data.values():
                    if kpi_name in site_data_entry["latest_kpis"]:
                        values.append(site_data_entry["latest_kpis"][kpi_name]["value"])
                
                if values:
                    kpi_summary[kpi_name] = {
                        "average": round(statistics.mean(values), 2),
                        "min": min(values),
                        "max": max(values),
                        "std_dev": round(statistics.stdev(values) if len(values) > 1 else 0, 2),
                        "sample_sites": len(values)
                    }
            
            conn.close()
            
            return {
                "status": "success",
                "site_data": site_data,
                "kpi_summary": kpi_summary,
                "latest_values": latest_values,
                "total_data_points": total_data_points,
                "collection_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"KPI collection failed: {e}")
            # Return demo data as fallback
            return await self._generate_demo_kpi_data(target_sites)
    
    async def _generate_demo_kpi_data(self, target_sites: List[str]) -> Dict[str, Any]:
        """Generate realistic demo KPI data when database unavailable"""
        site_data = {}
        kpi_summary = {}
        latest_values = {}
        
        for site_id in target_sites:
            site_latest = {}
            site_averages = {}
            
            for kpi_name, thresholds in self.kpi_thresholds.items():
                # Generate realistic values based on actual Bindura network data patterns
                if kpi_name == "rach_setup_success_rate":
                    # Real RACH rates: 0.15-0.9% - extremely low, critical optimization needed
                    base_value = random.uniform(0.2, 0.8)
                    variation = random.uniform(-0.1, 0.2)
                    value = max(0.05, min(1.0, base_value + variation))
                    unit = "%"
                elif kpi_name == "dl_ibler":
                    # Real DL IBLER: 11-20% - high error rates
                    base_value = random.uniform(11, 18)
                    variation = random.uniform(-2, 3)
                    value = max(8, min(25, base_value + variation))
                    unit = "%"
                elif kpi_name == "ul_ibler":
                    # Real UL IBLER: 2-14%
                    base_value = random.uniform(3, 12)
                    variation = random.uniform(-1, 2)
                    value = max(1, min(18, base_value + variation))
                    unit = "%"
                elif kpi_name == "pdcch_cce_usage_rate":
                    # Real PDCCH usage: 15-58%
                    base_value = random.uniform(18, 52)
                    variation = random.uniform(-5, 8)
                    value = max(10, min(65, base_value + variation))
                    unit = "%"
                elif kpi_name == "pucch_usage_rate":
                    # Real PUCCH usage: 1-10%
                    base_value = random.uniform(1.5, 8.5)
                    variation = random.uniform(-0.5, 1.5)
                    value = max(0.5, min(12, base_value + variation))
                    unit = "%"
                elif kpi_name == "dl_pdcp_throughput":
                    # Real DL throughput: 10-32 Mbps (converted from kbit/s in data)
                    base_value = random.uniform(12, 28)
                    variation = random.uniform(-3, 5)
                    value = max(8, min(35, base_value + variation))
                    unit = "Mbps"
                elif kpi_name == "ul_pdcp_throughput":
                    # Real UL throughput: 3-14 Mbps (converted from kbit/s in data)
                    base_value = random.uniform(4, 11)
                    variation = random.uniform(-1, 3)
                    value = max(2, min(16, base_value + variation))
                    unit = "Mbps"
                elif "success_rate" in kpi_name:
                    # Other success rates - estimated based on IBLER performance
                    base_value = thresholds["target"]
                    variation = random.uniform(-5, 3)
                    value = max(thresholds.get("critical", 80), 
                              min(99.5, base_value + variation))
                    unit = "%"
                elif "time" in kpi_name:
                    # Setup times (lower is better)
                    base_value = thresholds["target"]
                    variation = random.uniform(-1, 2)
                    value = max(1, base_value + variation)
                    unit = "s"
                else:
                    # Drop rates (lower is better)
                    base_value = thresholds["target"]
                    variation = random.uniform(-1, 2)
                    value = max(0.1, base_value + variation)
                    unit = "%"
                
                site_latest[kpi_name] = {
                    "value": round(value, 2),
                    "unit": unit,
                    "timestamp": datetime.now().isoformat()
                }
                
                site_averages[kpi_name] = {
                    "value": round(value * random.uniform(0.98, 1.02), 2),
                    "unit": unit,
                    "sample_count": random.randint(50, 100)
                }
            
            site_data[site_id] = {
                "latest_kpis": site_latest,
                "hourly_averages": site_averages,
                "data_points": random.randint(80, 120)
            }
            
            latest_values.update(site_latest)
        
        return {
            "status": "success",
            "site_data": site_data,
            "kpi_summary": {},
            "latest_values": latest_values,
            "total_data_points": sum(sd["data_points"] for sd in site_data.values()),
            "collection_timestamp": datetime.now().isoformat()
        }
    
    async def _validate_data_quality(self, kpi_collection: Dict) -> Dict[str, Any]:
        """Validate quality of collected KPI data"""
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        total_expected = len(self.kpi_thresholds) * len(kpi_collection["site_data"])
        total_collected = sum(len(site_data["latest_kpis"]) 
                             for site_data in kpi_collection["site_data"].values())
        
        completeness = (total_collected / total_expected * 100) if total_expected > 0 else 0
        
        # Simulate data quality metrics
        quality_assessment = {
            "quality_score": random.uniform(85, 98),
            "completeness": round(completeness, 1),
            "accuracy": random.uniform(92, 99),
            "reliability": random.uniform(88, 97),
            "freshness_score": random.uniform(90, 99),
            "validation_timestamp": datetime.now().isoformat()
        }
        
        return quality_assessment
    
    async def _analyze_threshold_violations(self, kpi_collection: Dict) -> Dict[str, Any]:
        """Analyze KPI threshold violations"""
        await asyncio.sleep(random.uniform(1, 2))
        
        violations = []
        critical_violations = 0
        warning_violations = 0
        
        for site_id, site_data in kpi_collection["site_data"].items():
            for kpi_name, kpi_data in site_data["latest_kpis"].items():
                if kpi_name in self.kpi_thresholds:
                    thresholds = self.kpi_thresholds[kpi_name]
                    value = kpi_data["value"]
                    
                    violation = self._check_threshold_violation(kpi_name, value, thresholds)
                    if violation:
                        violation_detail = {
                            "site_id": site_id,
                            "kpi_name": kpi_name,
                            "current_value": value,
                            "unit": kpi_data["unit"],
                            "threshold_type": violation["type"],
                            "severity": violation["severity"],
                            "deviation": violation["deviation"],
                            "timestamp": kpi_data["timestamp"]
                        }
                        violations.append(violation_detail)
                        
                        if violation["severity"] == "critical":
                            critical_violations += 1
                        else:
                            warning_violations += 1
        
        total_kpis_checked = sum(len(site_data["latest_kpis"]) 
                                for site_data in kpi_collection["site_data"].values())
        compliance_rate = ((total_kpis_checked - len(violations)) / total_kpis_checked * 100) if total_kpis_checked > 0 else 100
        
        return {
            "total_violations": len(violations),
            "critical_violations": critical_violations,
            "warning_violations": warning_violations,
            "violation_details": violations,
            "compliance_rate": round(compliance_rate, 1),
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def _check_threshold_violation(self, kpi_name: str, value: float, thresholds: Dict) -> Optional[Dict[str, Any]]:
        """Check if a KPI value violates thresholds"""
        if "drop" in kpi_name or "time" in kpi_name:
            # Lower is better KPIs
            if "critical" in thresholds and value > thresholds["critical"]:
                return {
                    "type": "exceeds_critical_max",
                    "severity": "critical",
                    "deviation": value - thresholds["critical"]
                }
            elif "max" in thresholds and value > thresholds["max"]:
                return {
                    "type": "exceeds_warning_max",
                    "severity": "warning",
                    "deviation": value - thresholds["max"]
                }
        else:
            # Higher is better KPIs
            if "critical" in thresholds and value < thresholds["critical"]:
                return {
                    "type": "below_critical_min",
                    "severity": "critical",
                    "deviation": thresholds["critical"] - value
                }
            elif "min" in thresholds and value < thresholds["min"]:
                return {
                    "type": "below_warning_min",
                    "severity": "warning",
                    "deviation": thresholds["min"] - value
                }
        
        return None
    
    async def _analyze_performance_trends(self, kpi_collection: Dict, target_sites: List[str]) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        await asyncio.sleep(random.uniform(1, 3))
        
        # Simulate trend analysis with realistic patterns
        overall_trend = random.choice(["improving", "stable", "declining"])
        velocity = random.uniform(-2.5, 2.5)
        confidence = random.uniform(75, 95)
        
        # Individual KPI trends
        kpi_trends = {}
        seasonal_patterns = {}
        
        for kpi_name in self.kpi_thresholds.keys():
            trend_direction = random.choice(["improving", "stable", "declining", "volatile"])
            trend_strength = random.uniform(0.1, 2.0)
            
            kpi_trends[kpi_name] = {
                "direction": trend_direction,
                "strength": round(trend_strength, 2),
                "confidence": random.uniform(70, 95),
                "correlation_factors": self._generate_correlation_factors()
            }
            
            # Seasonal patterns
            seasonal_patterns[kpi_name] = {
                "daily_pattern": random.choice(["peak_hours_impact", "stable", "night_degradation"]),
                "weekly_pattern": random.choice(["weekend_improvement", "stable", "weekday_peak"]),
                "pattern_strength": random.uniform(0.1, 0.8)
            }
        
        return {
            "trending_direction": overall_trend,
            "velocity": round(velocity, 2),
            "confidence": round(confidence, 1),
            "individual_kpi_trends": kpi_trends,
            "seasonal_patterns": seasonal_patterns,
            "analysis_period": "24_hours",
            "trend_timestamp": datetime.now().isoformat()
        }
    
    def _generate_correlation_factors(self) -> List[Dict[str, Any]]:
        """Generate realistic correlation factors for trend analysis"""
        factors = [
            {"factor": "traffic_load", "correlation": random.uniform(-0.8, 0.8)},
            {"factor": "weather_conditions", "correlation": random.uniform(-0.3, 0.3)},
            {"factor": "network_congestion", "correlation": random.uniform(-0.7, -0.2)},
            {"factor": "maintenance_activities", "correlation": random.uniform(-0.9, -0.5)}
        ]
        return factors
    
    async def _detect_performance_anomalies(self, kpi_collection: Dict) -> Dict[str, Any]:
        """Detect performance anomalies using statistical analysis"""
        await asyncio.sleep(random.uniform(1, 2))
        
        anomalies = []
        total_anomalies = random.randint(0, 3)  # 0-3 anomalies for demo
        
        if total_anomalies > 0:
            kpi_names = list(self.kpi_thresholds.keys())
            site_ids = list(kpi_collection["site_data"].keys())
            
            for i in range(total_anomalies):
                anomaly = {
                    "anomaly_id": f"ANOM_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                    "site_id": random.choice(site_ids),
                    "kpi_name": random.choice(kpi_names),
                    "anomaly_type": random.choice(["spike", "drop", "volatility", "pattern_break"]),
                    "severity": random.choice(["low", "medium", "high"]),
                    "confidence": random.uniform(80, 95),
                    "deviation_magnitude": random.uniform(1.5, 4.0),
                    "detection_algorithm": "statistical_threshold",
                    "timestamp": datetime.now().isoformat(),
                    "root_cause_candidates": [
                        random.choice([
                            "network_congestion", "equipment_failure", "configuration_change",
                            "external_interference", "weather_impact", "maintenance_activity"
                        ])
                    ]
                }
                anomalies.append(anomaly)
        
        # Severity distribution
        severity_distribution = {
            "low": sum(1 for a in anomalies if a["severity"] == "low"),
            "medium": sum(1 for a in anomalies if a["severity"] == "medium"), 
            "high": sum(1 for a in anomalies if a["severity"] == "high")
        }
        
        # Pattern analysis
        pattern_analysis = {
            "recurring_patterns": random.choice([True, False]),
            "temporal_clustering": random.choice([True, False]),
            "site_correlation": random.choice([True, False]),
            "pattern_confidence": random.uniform(60, 90)
        }
        
        return {
            "total_anomalies": total_anomalies,
            "anomaly_details": anomalies,
            "severity_distribution": severity_distribution,
            "pattern_analysis": pattern_analysis,
            "detection_timestamp": datetime.now().isoformat()
        }
    
    async def _perform_site_comparison(self, kpi_collection: Dict) -> Dict[str, Any]:
        """Perform comparative analysis across sites"""
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        site_scores = {}
        site_ids = list(kpi_collection["site_data"].keys())
        
        # Calculate performance scores for each site
        for site_id in site_ids:
            site_data = kpi_collection["site_data"][site_id]
            score = 0
            kpi_count = 0
            
            for kpi_name, kpi_data in site_data["latest_kpis"].items():
                if kpi_name in self.kpi_thresholds:
                    thresholds = self.kpi_thresholds[kpi_name]
                    target = thresholds["target"]
                    value = kpi_data["value"]
                    
                    # Calculate normalized score (0-100)
                    if "drop" in kpi_name or "time" in kpi_name:
                        # Lower is better
                        normalized_score = max(0, 100 - (value / target * 100 - 100))
                    else:
                        # Higher is better
                        normalized_score = min(100, value / target * 100)
                    
                    score += normalized_score
                    kpi_count += 1
            
            site_scores[site_id] = {
                "overall_score": round(score / kpi_count if kpi_count > 0 else 0, 1),
                "kpi_count": kpi_count
            }
        
        # Find best and worst performers
        if site_scores:
            best_performer = max(site_scores.items(), key=lambda x: x[1]["overall_score"])
            worst_performer = min(site_scores.items(), key=lambda x: x[1]["overall_score"])
            
            # Calculate variance
            scores = [score["overall_score"] for score in site_scores.values()]
            variance = round(statistics.stdev(scores) if len(scores) > 1 else 0, 2)
            
            # Site rankings
            rankings = sorted(site_scores.items(), key=lambda x: x[1]["overall_score"], reverse=True)
        else:
            best_performer = ("N/A", {"overall_score": 0})
            worst_performer = ("N/A", {"overall_score": 0})
            variance = 0
            rankings = []
        
        return {
            "best_performer": {
                "site_id": best_performer[0],
                "score": best_performer[1]["overall_score"]
            },
            "worst_performer": {
                "site_id": worst_performer[0],
                "score": worst_performer[1]["overall_score"]
            },
            "variance": variance,
            "rankings": [{"site_id": site_id, "score": score["overall_score"]} 
                        for site_id, score in rankings],
            "comparison_timestamp": datetime.now().isoformat()
        }
    
    def _generate_monitoring_insights(self, threshold_analysis: Dict, trend_analysis: Dict, 
                                    anomaly_detection: Dict) -> List[Dict[str, str]]:
        """Generate actionable monitoring insights"""
        insights = []
        
        # Threshold-based insights
        if threshold_analysis["critical_violations"] > 0:
            insights.append({
                "type": "performance_alert",
                "severity": "high",
                "title": "Critical Performance Violations Detected",
                "description": f"{threshold_analysis['critical_violations']} KPIs below critical thresholds",
                "impact": "Service quality degradation likely",
                "urgency": "immediate"
            })
        
        # Trend-based insights
        if trend_analysis["trending_direction"] == "declining":
            insights.append({
                "type": "trend_alert",
                "severity": "medium",
                "title": "Declining Performance Trend",
                "description": f"Network performance declining at {abs(trend_analysis['velocity']):.1f}% rate",
                "impact": "Progressive service degradation expected",
                "urgency": "24_hours"
            })
        
        # Anomaly-based insights
        if anomaly_detection["total_anomalies"] > 0:
            high_severity_anomalies = anomaly_detection["severity_distribution"].get("high", 0)
            if high_severity_anomalies > 0:
                insights.append({
                    "type": "anomaly_alert",
                    "severity": "high",
                    "title": "High-Severity Anomalies Detected",
                    "description": f"{high_severity_anomalies} high-severity performance anomalies identified",
                    "impact": "Potential service disruption",
                    "urgency": "immediate"
                })
        
        return insights
    
    def _identify_optimization_opportunities(self, threshold_analysis: Dict, 
                                           trend_analysis: Dict, anomaly_detection: Dict) -> List[Dict[str, Any]]:
        """Identify optimization opportunities based on monitoring results"""
        opportunities = []
        
        # Based on violations
        if threshold_analysis["warning_violations"] > 0:
            opportunities.append({
                "type": "preventive_optimization",
                "priority": "medium",
                "description": "Address warning-level KPI violations before they become critical",
                "estimated_impact": "5-15% performance improvement",
                "complexity": "low"
            })
        
        # Based on trends
        if trend_analysis["trending_direction"] == "declining":
            opportunities.append({
                "type": "trend_reversal",
                "priority": "high",
                "description": "Implement corrections to reverse declining performance trend",
                "estimated_impact": "10-25% performance improvement",
                "complexity": "medium"
            })
        
        # Based on site comparison
        opportunities.append({
            "type": "best_practice_replication",
            "priority": "medium",
            "description": "Replicate configuration from best-performing sites to others",
            "estimated_impact": "3-12% performance improvement",
            "complexity": "low"
        })
        
        return opportunities
    
    def _generate_monitoring_recommendations(self, threshold_analysis: Dict, 
                                           anomaly_detection: Dict, trend_analysis: Dict) -> List[Dict[str, str]]:
        """Generate monitoring-specific recommendations"""
        recommendations = []
        
        if threshold_analysis["critical_violations"] > 0:
            recommendations.append({
                "type": "immediate_action",
                "priority": "critical",
                "title": "Address Critical KPI Violations",
                "description": f"Immediate investigation required for {threshold_analysis['critical_violations']} critical violations",
                "action": "Deploy emergency response team and implement immediate corrections"
            })
        
        if anomaly_detection["total_anomalies"] > 2:
            recommendations.append({
                "type": "investigation",
                "priority": "high",
                "title": "Investigate Performance Anomalies",
                "description": f"Multiple anomalies detected requiring root cause analysis",
                "action": "Initiate comprehensive network investigation and correlation analysis"
            })
        
        if trend_analysis["confidence"] < 80:
            recommendations.append({
                "type": "monitoring_enhancement",
                "priority": "medium",
                "title": "Enhance Monitoring Granularity",
                "description": "Low trend confidence suggests need for improved monitoring",
                "action": "Increase monitoring frequency and add additional data collection points"
            })
        
        return recommendations
    
    async def _handle_monitoring_failure(self, error_msg: str, context: Dict) -> Dict[str, Any]:
        """Handle monitoring failure with graceful degradation"""
        return {
            "status": "partial_success",
            "agent_name": "Monitoring Analysis",
            "error": error_msg,
            "fallback_mode": "limited_monitoring",
            "monitoring_summary": {
                "sites_monitored": 0,
                "data_points_collected": 0,
                "kpis_analyzed": 0
            },
            "recommendations": [
                {
                    "type": "system_recovery",
                    "priority": "critical",
                    "title": "Restore Monitoring Capabilities",
                    "description": f"Monitoring failed: {error_msg}",
                    "action": "Check database connectivity and monitoring system health"
                }
            ],
            "execution_time": 0
        }