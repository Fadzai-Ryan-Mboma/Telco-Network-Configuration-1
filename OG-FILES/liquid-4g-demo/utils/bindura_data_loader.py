"""
Real Bindura Network Data Loader
Loads actual historical network data from CSV for realistic demo
"""

import pandas as pd
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class BinduraDataLoader:
    """
    Loads real Bindura network historical data from CSV files
    for use in the agentic workflow demo
    """
    
    def __init__(self, csv_file_path: str, db_path: str):
        self.csv_file_path = csv_file_path
        self.db_path = db_path
        
        # Real site mapping from historical data
        self.site_mapping = {
            "MSH0013-Bindura-Zaoga": {
                "site_id": "MSH0013-Bindura-Zaoga",
                "site_name": "Bindura Zaoga",
                "location": "Bindura Zaoga Area",
                "latitude": -17.3011,
                "longitude": 31.3135,
                "vendor": "Huawei",
                "technology": "LTE"
            },
            "MSH-0331-Chiwaridzo 2": {
                "site_id": "MSH-0331-Chiwaridzo",
                "site_name": "Chiwaridzo 2",
                "location": "Chiwaridzo Residential",
                "latitude": -17.3028,
                "longitude": 31.3142,
                "vendor": "Huawei",
                "technology": "LTE"
            },
            "MSH-0112-Bindura Hospital": {
                "site_id": "MSH-0112-Bindura-Hospital",
                "site_name": "Bindura Hospital",
                "location": "Bindura Provincial Hospital",
                "latitude": -17.3019,
                "longitude": 31.3089,
                "vendor": "Huawei",
                "technology": "LTE"
            },
            "MSH-0014-Chipadze": {
                "site_id": "MSH-0014-Chipadze",
                "site_name": "Chipadze",
                "location": "Chipadze Area",
                "latitude": -17.2995,
                "longitude": 31.3156,
                "vendor": "Huawei",
                "technology": "LTE"
            }
        }
        
        # KPI mapping from CSV columns to our standard names
        self.kpi_mapping = {
            "RACH Setup Success Rate(%)": "rach_setup_success_rate",
            "DL IBLER[%]": "dl_ibler",
            "UL IBLER[%]": "ul_ibler", 
            "PDCCH CCE Usage Rate[%]": "pdcch_cce_usage_rate",
            "PUCCHUsage Rate[%]": "pucch_usage_rate",
            "DL Cell PDCP Layer Average Throughput(kbit/s)": "dl_pdcp_throughput_kbps",
            "UL Cell PDCP Layer Average Throughput(kbit/s)": "ul_pdcp_throughput_kbps"
        }
    
    def load_historical_data(self) -> Dict[str, Any]:
        """Load and process historical network data from CSV"""
        try:
            logger.info(f"Loading real Bindura network data from {self.csv_file_path}")
            
            # Read CSV data
            df = pd.read_csv(self.csv_file_path)
            
            # Data processing summary
            processing_summary = {
                "total_records": len(df),
                "date_range": {
                    "start": df['Date'].min(),
                    "end": df['Date'].max()
                },
                "unique_sites": df['eNodeB Name'].nunique(),
                "unique_cells": df['Cell Name'].nunique(),
                "sites_list": df['eNodeB Name'].unique().tolist()
            }
            
            # Process KPI statistics
            kpi_statistics = self._calculate_kpi_statistics(df)
            
            # Generate site summaries
            site_summaries = self._generate_site_summaries(df)
            
            # Performance analysis
            performance_analysis = self._analyze_network_performance(df)
            
            return {
                "status": "success",
                "data_loaded": True,
                "processing_summary": processing_summary,
                "kpi_statistics": kpi_statistics,
                "site_summaries": site_summaries,
                "performance_analysis": performance_analysis,
                "optimization_opportunities": self._identify_optimization_opportunities(df),
                "data_quality": self._assess_data_quality(df)
            }
            
        except Exception as e:
            logger.error(f"Failed to load historical data: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "data_loaded": False
            }
    
    def _calculate_kpi_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive KPI statistics from real data"""
        kpi_stats = {}
        
        for csv_col, standard_name in self.kpi_mapping.items():
            if csv_col in df.columns:
                col_data = df[csv_col].dropna()
                
                kpi_stats[standard_name] = {
                    "min": round(col_data.min(), 4),
                    "max": round(col_data.max(), 4),
                    "mean": round(col_data.mean(), 4),
                    "median": round(col_data.median(), 4),
                    "std": round(col_data.std(), 4),
                    "percentile_25": round(col_data.quantile(0.25), 4),
                    "percentile_75": round(col_data.quantile(0.75), 4),
                    "sample_count": len(col_data),
                    "unit": self._get_kpi_unit(standard_name)
                }
        
        return kpi_stats
    
    def _generate_site_summaries(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate performance summaries for each site"""
        site_summaries = {}
        
        for site_name in df['eNodeB Name'].unique():
            site_data = df[df['eNodeB Name'] == site_name]
            
            # Convert site name to our standard format
            standard_site_info = self.site_mapping.get(site_name, {
                "site_id": site_name.replace(" ", "-"),
                "site_name": site_name,
                "location": "Unknown"
            })
            
            # Calculate site-level KPI averages
            site_kpis = {}
            for csv_col, standard_name in self.kpi_mapping.items():
                if csv_col in site_data.columns:
                    site_kpis[standard_name] = {
                        "average": round(site_data[csv_col].mean(), 4),
                        "best": round(site_data[csv_col].min() if 'IBLER' in csv_col or 'Usage' in csv_col 
                                    else site_data[csv_col].max(), 4),
                        "worst": round(site_data[csv_col].max() if 'IBLER' in csv_col or 'Usage' in csv_col 
                                     else site_data[csv_col].min(), 4),
                        "trend": self._calculate_trend(site_data[csv_col]),
                        "unit": self._get_kpi_unit(standard_name)
                    }
            
            site_summaries[standard_site_info["site_id"]] = {
                **standard_site_info,
                "cells_count": len(site_data['Cell Name'].unique()),
                "cell_names": site_data['Cell Name'].unique().tolist(),
                "cell_ids": site_data['LocalCell Id'].unique().tolist(),
                "data_points": len(site_data),
                "kpi_performance": site_kpis,
                "overall_score": self._calculate_site_score(site_kpis),
                "optimization_priority": self._determine_optimization_priority(site_kpis)
            }
        
        return site_summaries
    
    def _analyze_network_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze overall network performance patterns"""
        
        # Critical findings from real data
        critical_findings = []
        
        # Check RACH success rates
        rach_avg = df['RACH Setup Success Rate(%)'].mean()
        if rach_avg < 1.0:
            critical_findings.append({
                "type": "critical",
                "category": "RACH Performance", 
                "issue": f"RACH success rate extremely low: {rach_avg:.3f}%",
                "impact": "Severe impact on initial network access",
                "priority": "immediate"
            })
        
        # Check IBLER rates
        dl_ibler_avg = df['DL IBLER[%]'].mean()
        ul_ibler_avg = df['UL IBLER[%]'].mean()
        
        if dl_ibler_avg > 15:
            critical_findings.append({
                "type": "major",
                "category": "DL Quality",
                "issue": f"DL IBLER high: {dl_ibler_avg:.2f}%", 
                "impact": "Poor downlink data quality",
                "priority": "high"
            })
        
        if ul_ibler_avg > 10:
            critical_findings.append({
                "type": "major",
                "category": "UL Quality",
                "issue": f"UL IBLER elevated: {ul_ibler_avg:.2f}%",
                "impact": "Uplink quality degradation",
                "priority": "medium"
            })
        
        # Resource utilization analysis
        pdcch_avg = df['PDCCH CCE Usage Rate[%]'].mean()
        pucch_avg = df['PUCCHUsage Rate[%]'].mean()
        
        resource_analysis = {
            "pdcch_utilization": {
                "average": round(pdcch_avg, 2),
                "status": "high" if pdcch_avg > 45 else "normal" if pdcch_avg > 25 else "low",
                "recommendation": "Consider load balancing" if pdcch_avg > 45 else "Monitor trends"
            },
            "pucch_utilization": {
                "average": round(pucch_avg, 2),
                "status": "high" if pucch_avg > 8 else "normal" if pucch_avg > 3 else "low",
                "recommendation": "Review PUCCH configuration" if pucch_avg > 8 else "Normal operation"
            }
        }
        
        # Throughput analysis
        dl_throughput_avg = df['DL Cell PDCP Layer Average Throughput(kbit/s)'].mean() / 1000  # Convert to Mbps
        ul_throughput_avg = df['UL Cell PDCP Layer Average Throughput(kbit/s)'].mean() / 1000
        
        throughput_analysis = {
            "dl_throughput_mbps": round(dl_throughput_avg, 2),
            "ul_throughput_mbps": round(ul_throughput_avg, 2),
            "dl_performance": "poor" if dl_throughput_avg < 15 else "fair" if dl_throughput_avg < 25 else "good",
            "ul_performance": "poor" if ul_throughput_avg < 4 else "fair" if ul_throughput_avg < 8 else "good"
        }
        
        return {
            "critical_findings": critical_findings,
            "resource_analysis": resource_analysis,
            "throughput_analysis": throughput_analysis,
            "overall_network_health": "poor" if len([f for f in critical_findings if f["type"] == "critical"]) > 0 else "fair",
            "optimization_urgency": "immediate" if rach_avg < 0.5 else "high"
        }
    
    def _identify_optimization_opportunities(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify specific optimization opportunities from real data"""
        opportunities = []
        
        # RACH optimization - critical priority
        rach_avg = df['RACH Setup Success Rate(%)'].mean()
        opportunities.append({
            "parameter": "RACH Configuration",
            "current_performance": f"{rach_avg:.3f}%",
            "target_improvement": "5-10x increase",
            "optimization_type": "critical",
            "estimated_impact": "Dramatic improvement in network access",
            "implementation_complexity": "medium",
            "mml_parameters": ["rachMaxRetrans", "rachPowerRampStep", "rachPreambleFormat"]
        })
        
        # IBLER optimization
        dl_ibler_avg = df['DL IBLER[%]'].mean()
        if dl_ibler_avg > 15:
            opportunities.append({
                "parameter": "DL Quality Optimization",
                "current_performance": f"{dl_ibler_avg:.2f}%",
                "target_improvement": "Reduce to <12%",
                "optimization_type": "major", 
                "estimated_impact": "Improved data quality and throughput",
                "implementation_complexity": "medium",
                "mml_parameters": ["dlPowerControl", "modulation", "schedulingAlgorithm"]
            })
        
        # Resource optimization
        pdcch_avg = df['PDCCH CCE Usage Rate[%]'].mean()
        if pdcch_avg > 45:
            opportunities.append({
                "parameter": "PDCCH Resource Management",
                "current_performance": f"{pdcch_avg:.2f}%",
                "target_improvement": "Optimize to 30-40%",
                "optimization_type": "efficiency",
                "estimated_impact": "Better resource utilization",
                "implementation_complexity": "low",
                "mml_parameters": ["pdcchFormat", "cceAggregationLevel"]
            })
        
        return opportunities
    
    def _assess_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess the quality of the loaded data"""
        return {
            "completeness": {
                "total_records": len(df),
                "missing_values": df.isnull().sum().to_dict(),
                "completeness_percentage": round((1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100, 2)
            },
            "consistency": {
                "date_format": "valid",
                "site_naming": "consistent",
                "cell_id_range": f"{df['LocalCell Id'].min()}-{df['LocalCell Id'].max()}"
            },
            "data_freshness": {
                "latest_date": df['Date'].max(),
                "date_range_days": (pd.to_datetime(df['Date'].max()) - pd.to_datetime(df['Date'].min())).days
            }
        }
    
    def _get_kpi_unit(self, kpi_name: str) -> str:
        """Get the unit for a KPI"""
        if "rate" in kpi_name or "ibler" in kpi_name or "usage" in kpi_name:
            return "%"
        elif "throughput" in kpi_name:
            return "Mbps" if "kbps" not in kpi_name else "kbps"
        elif "time" in kpi_name:
            return "ms"
        else:
            return ""
    
    def _calculate_trend(self, data_series) -> str:
        """Calculate trend direction for a data series"""
        if len(data_series) < 2:
            return "stable"
        
        first_half = data_series.iloc[:len(data_series)//2].mean()
        second_half = data_series.iloc[len(data_series)//2:].mean()
        
        change_percent = ((second_half - first_half) / first_half) * 100
        
        if abs(change_percent) < 2:
            return "stable"
        elif change_percent > 0:
            return "improving" if "IBLER" not in str(data_series.name) else "degrading"
        else:
            return "degrading" if "IBLER" not in str(data_series.name) else "improving"
    
    def _calculate_site_score(self, site_kpis: Dict) -> float:
        """Calculate overall performance score for a site"""
        if not site_kpis:
            return 0.0
        
        score = 0.0
        weights = {
            "rach_setup_success_rate": 0.3,  # Critical weight due to low performance
            "dl_ibler": 0.2,
            "ul_ibler": 0.15,
            "dl_pdcp_throughput_kbps": 0.2,
            "ul_pdcp_throughput_kbps": 0.15
        }
        
        for kpi_name, weight in weights.items():
            if kpi_name in site_kpis:
                kpi_value = site_kpis[kpi_name]["average"]
                
                # Normalize KPI value to 0-100 scale
                if kpi_name == "rach_setup_success_rate":
                    # For RACH: 0.8% = 80/100, 0.3% = 30/100
                    normalized = min(100, (kpi_value / 0.8) * 100)
                elif "ibler" in kpi_name:
                    # For IBLER: lower is better, 10% = 100, 20% = 0
                    normalized = max(0, 100 - ((kpi_value - 10) / 10) * 100)
                elif "throughput" in kpi_name:
                    # For throughput: normalize to typical range
                    if "dl" in kpi_name:
                        normalized = min(100, (kpi_value / 30000) * 100)  # 30 Mbps target
                    else:
                        normalized = min(100, (kpi_value / 10000) * 100)   # 10 Mbps target
                else:
                    normalized = 50  # Default for unknown KPIs
                
                score += normalized * weight
        
        return round(score, 1)
    
    def _determine_optimization_priority(self, site_kpis: Dict) -> str:
        """Determine optimization priority based on KPI performance"""
        if not site_kpis:
            return "unknown"
        
        # Check for critical issues
        if "rach_setup_success_rate" in site_kpis:
            rach_rate = site_kpis["rach_setup_success_rate"]["average"]
            if rach_rate < 0.3:
                return "critical"
            elif rach_rate < 0.5:
                return "high"
        
        # Check IBLER performance
        ibler_issues = 0
        if "dl_ibler" in site_kpis and site_kpis["dl_ibler"]["average"] > 18:
            ibler_issues += 1
        if "ul_ibler" in site_kpis and site_kpis["ul_ibler"]["average"] > 12:
            ibler_issues += 1
        
        if ibler_issues >= 2:
            return "high"
        elif ibler_issues == 1:
            return "medium"
        
        return "low"

def load_bindura_data_to_demo(csv_path: str, db_path: str) -> Dict[str, Any]:
    """Convenience function to load Bindura data for demo"""
    loader = BinduraDataLoader(csv_path, db_path)
    return loader.load_historical_data()

if __name__ == "__main__":
    # Test the data loader
    csv_path = "/Users/fadzai/Library/CloudStorage/OneDrive-LiquidIntelligentTechnologies/Documents/Cassava AI/Telco-Network-Config/Telco-Network-Configuration/liquid-4g-core/data/historical_data.csv"
    db_path = "demo_liquid_zimbabwe.db"
    
    result = load_bindura_data_to_demo(csv_path, db_path)
    
    print("Real Bindura Network Data Analysis:")
    print("=" * 50)
    print(f"Data Load Status: {result['status']}")
    
    if result.get('data_loaded'):
        print(f"Total Records: {result['processing_summary']['total_records']}")
        print(f"Sites: {result['processing_summary']['unique_sites']}")
        print(f"Date Range: {result['processing_summary']['date_range']['start']} to {result['processing_summary']['date_range']['end']}")
        
        print("\nCritical Findings:")
        for finding in result['performance_analysis']['critical_findings']:
            print(f"- {finding['category']}: {finding['issue']} (Priority: {finding['priority']})")
        
        print("\nOptimization Opportunities:")
        for opp in result['optimization_opportunities']:
            print(f"- {opp['parameter']}: {opp['current_performance']} -> {opp['target_improvement']}")