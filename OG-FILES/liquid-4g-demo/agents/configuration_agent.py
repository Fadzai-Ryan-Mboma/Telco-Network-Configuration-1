#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Demo - Configuration Agent
Stage 4: Generates optimized network configurations based on analytics insights
"""

import asyncio
import sqlite3
import json
import random
import copy
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ConfigurationAgent:
    """
    Configuration Agent - Generates optimized network configurations including:
    - Parameter optimization recommendations
    - Configuration templates
    - Risk assessment for changes
    - Implementation planning
    - Rollback strategies
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
        # Network parameters and their typical ranges
        self.parameter_definitions = {
            # RACH parameters
            "rach_preamble_format": {
                "type": "enum",
                "values": [0, 1, 2, 3],
                "default": 0,
                "impact_kpis": ["rach_setup_success_rate"],
                "description": "RACH preamble format configuration"
            },
            "rach_prach_config_index": {
                "type": "integer",
                "range": [0, 63],
                "default": 6,
                "impact_kpis": ["rach_setup_success_rate", "rrc_connection_success_rate"],
                "description": "PRACH configuration index"
            },
            "rach_root_sequence": {
                "type": "integer",
                "range": [0, 837],
                "default": 0,
                "impact_kpis": ["rach_setup_success_rate"],
                "description": "RACH root sequence index"
            },
            
            # RRC parameters
            "rrc_inactivity_timer": {
                "type": "integer",
                "range": [1, 30],
                "default": 10,
                "impact_kpis": ["rrc_connection_success_rate", "call_drop_rate"],
                "description": "RRC inactivity timer in seconds"
            },
            "rrc_connection_reestablishment_timer": {
                "type": "integer",
                "range": [1, 16],
                "default": 4,
                "impact_kpis": ["rrc_connection_success_rate"],
                "description": "RRC connection reestablishment timer"
            },
            
            # E-RAB parameters
            "erab_qci_priority": {
                "type": "integer",
                "range": [1, 9],
                "default": 1,
                "impact_kpis": ["erab_setup_success_rate", "average_dl_throughput"],
                "description": "E-RAB QCI priority level"
            },
            "erab_allocation_retention_priority": {
                "type": "integer",
                "range": [1, 15],
                "default": 1,
                "impact_kpis": ["erab_setup_success_rate"],
                "description": "E-RAB allocation and retention priority"
            },
            
            # Handover parameters
            "handover_a3_offset": {
                "type": "integer",
                "range": [-30, 30],
                "default": 3,
                "impact_kpis": ["handover_success_rate", "call_drop_rate"],
                "description": "A3 event offset for handover in dB"
            },
            "handover_a3_hysteresis": {
                "type": "integer",
                "range": [0, 30],
                "default": 2,
                "impact_kpis": ["handover_success_rate"],
                "description": "A3 event hysteresis in dB"
            },
            "handover_time_to_trigger": {
                "type": "integer",
                "range": [0, 5120],
                "default": 320,
                "impact_kpis": ["handover_success_rate", "call_drop_rate"],
                "description": "Time to trigger for handover in ms"
            },
            
            # RF parameters
            "dl_rs_power": {
                "type": "integer",
                "range": [-60, 50],
                "default": 18,
                "impact_kpis": ["rsrp_coverage", "average_dl_throughput"],
                "description": "Downlink reference signal power in dBm"
            },
            "ul_power_control_alpha": {
                "type": "float",
                "range": [0.0, 1.0],
                "default": 0.7,
                "impact_kpis": ["average_ul_throughput", "rsrq_quality"],
                "description": "Uplink power control alpha parameter"
            },
            "p0_nominal_pusch": {
                "type": "integer",
                "range": [-126, 24],
                "default": -90,
                "impact_kpis": ["average_ul_throughput"],
                "description": "P0 nominal PUSCH power in dBm"
            },
            
            # Scheduling parameters
            "dl_scheduler_algorithm": {
                "type": "enum",
                "values": ["round_robin", "proportional_fair", "max_ci"],
                "default": "proportional_fair",
                "impact_kpis": ["average_dl_throughput", "erab_setup_success_rate"],
                "description": "Downlink scheduler algorithm"
            },
            "ul_scheduler_algorithm": {
                "type": "enum",
                "values": ["round_robin", "proportional_fair", "max_ci"],
                "default": "proportional_fair",
                "impact_kpis": ["average_ul_throughput"],
                "description": "Uplink scheduler algorithm"
            }
        }
        
        # Configuration templates for different optimization scenarios - Updated for Bindura issues
        self.optimization_templates = {
            "rach_critical_optimization": {  # New template for critical RACH issues
                "description": "Critical RACH optimization for extremely low success rates",
                "parameter_adjustments": {
                    "rach_prach_config_index": "optimize_for_accessibility",
                    "rach_preamble_format": "format_0",  # Most robust format
                    "rach_root_sequence": "optimize_for_interference",
                    "dl_rs_power": "increase_moderate",  # Improve coverage
                    "handover_a3_offset": "increase_small"  # Reduce unnecessary handovers
                },
                "expected_improvements": ["rach_setup_success_rate", "rrc_connection_success_rate"],
                "risk_level": "medium",
                "priority": "critical",
                "bindura_specific": True
            },
            "ibler_optimization": {  # New template for IBLER issues
                "description": "Optimize downlink quality to reduce IBLER from 15.94%",
                "parameter_adjustments": {
                    "dl_rs_power": "increase_moderate",
                    "dl_scheduler_algorithm": "max_ci",  # Prioritize quality
                    "erab_qci_priority": "quality_focused",
                    "ul_power_control_alpha": "optimize_for_quality"
                },
                "expected_improvements": ["dl_ibler", "rsrq_quality", "average_dl_throughput"],
                "risk_level": "low",
                "priority": "critical",
                "bindura_specific": True
            },
            "coverage_optimization": {
                "description": "Optimize for better coverage and signal quality",
                "parameter_adjustments": {
                    "dl_rs_power": "increase_moderate",
                    "handover_a3_offset": "decrease_small",
                    "handover_a3_hysteresis": "increase_small"
                },
                "expected_improvements": ["rsrp_coverage", "rsrq_quality", "handover_success_rate"],
                "risk_level": "low"
            },
            "capacity_optimization": {
                "description": "Optimize for higher throughput and capacity",
                "parameter_adjustments": {
                    "dl_scheduler_algorithm": "proportional_fair",
                    "ul_scheduler_algorithm": "proportional_fair",
                    "erab_qci_priority": "optimize_for_throughput"
                },
                "expected_improvements": ["average_dl_throughput", "average_ul_throughput", "erab_setup_success_rate"],
                "risk_level": "medium"
            },
            "reliability_optimization": {
                "description": "Optimize for connection reliability and stability",
                "parameter_adjustments": {
                    "rrc_inactivity_timer": "increase_moderate",
                    "handover_time_to_trigger": "increase_moderate",
                    "rach_prach_config_index": "optimize_for_reliability"
                },
                "expected_improvements": ["rrc_connection_success_rate", "call_drop_rate", "rach_setup_success_rate"],
                "risk_level": "low"
            },
            "balanced_optimization": {
                "description": "Balanced optimization across all KPIs",
                "parameter_adjustments": {
                    "dl_rs_power": "moderate_adjustment",
                    "handover_a3_offset": "fine_tune",
                    "rrc_inactivity_timer": "moderate_adjustment",
                    "dl_scheduler_algorithm": "proportional_fair"
                },
                "expected_improvements": ["overall_performance"],
                "risk_level": "low"
            }
        }
        
        # Risk assessment criteria
        self.risk_criteria = {
            "parameter_change_magnitude": {
                "low": 0.1,      # <10% change
                "medium": 0.25,  # 10-25% change
                "high": 0.5      # >25% change
            },
            "kpi_impact_scope": {
                "low": 1,        # Affects 1 KPI
                "medium": 3,     # Affects 2-3 KPIs
                "high": 5        # Affects 4+ KPIs
            },
            "rollback_complexity": {
                "low": "single_parameter",
                "medium": "multiple_parameters",
                "high": "configuration_template"
            }
        }
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute configuration generation stage"""
        start_time = datetime.now()
        
        try:
            # Simulate realistic configuration processing time
            await asyncio.sleep(random.uniform(5, 12))
            
            logger.info(f"⚙️ Configuration Agent starting for workflow {context['workflow_id']}")
            
            # Extract analytics results from previous stage
            analytics_results = self._extract_analytics_results(context)
            
            # Analyze optimization requirements
            optimization_requirements = await self._analyze_optimization_requirements(analytics_results)
            
            # Generate configuration recommendations
            configuration_recommendations = await self._generate_configuration_recommendations(
                optimization_requirements, analytics_results
            )
            
            # Perform risk assessment
            risk_assessment = await self._perform_risk_assessment(configuration_recommendations)
            
            # Create implementation plan
            implementation_plan = await self._create_implementation_plan(
                configuration_recommendations, risk_assessment
            )
            
            # Generate rollback strategy
            rollback_strategy = await self._generate_rollback_strategy(configuration_recommendations)
            
            # Create configuration templates
            configuration_templates = await self._create_configuration_templates(
                configuration_recommendations
            )
            
            # Generate MML commands
            mml_commands = await self._generate_mml_commands(configuration_recommendations)
            
            # Perform impact simulation
            impact_simulation = await self._simulate_configuration_impact(
                configuration_recommendations, analytics_results
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                "status": "success",
                "agent_name": "Configuration",
                "configuration_summary": {
                    "generation_duration_seconds": duration,
                    "parameters_optimized": len(configuration_recommendations.get("parameter_changes", {})),
                    "sites_affected": len(self._extract_target_sites(context)),
                    "optimization_templates_used": len(optimization_requirements.get("selected_templates", [])),
                    "risk_level": risk_assessment.get("overall_risk_level", "medium"),
                    "generation_timestamp": datetime.now().isoformat()
                },
                "optimization_requirements": {
                    "primary_objectives": optimization_requirements["primary_objectives"],
                    "secondary_objectives": optimization_requirements["secondary_objectives"],
                    "optimization_strategy": optimization_requirements["optimization_strategy"],
                    "selected_templates": optimization_requirements["selected_templates"],
                    "constraints": optimization_requirements["constraints"]
                },
                "configuration_recommendations": {
                    "parameter_changes": configuration_recommendations["parameter_changes"],
                    "optimization_rationale": configuration_recommendations["rationale"],
                    "expected_improvements": configuration_recommendations["expected_improvements"],
                    "configuration_scope": configuration_recommendations["scope"],
                    "priority_ranking": configuration_recommendations["priority_ranking"]
                },
                "risk_assessment": {
                    "overall_risk_level": risk_assessment["overall_risk_level"],
                    "risk_factors": risk_assessment["risk_factors"],
                    "mitigation_measures": risk_assessment["mitigation_measures"],
                    "risk_matrix": risk_assessment["risk_matrix"],
                    "approval_requirements": risk_assessment["approval_requirements"]
                },
                "implementation_plan": {
                    "implementation_phases": implementation_plan["phases"],
                    "timeline": implementation_plan["timeline"],
                    "resource_requirements": implementation_plan["resource_requirements"],
                    "validation_checkpoints": implementation_plan["validation_checkpoints"],
                    "success_criteria": implementation_plan["success_criteria"]
                },
                "rollback_strategy": {
                    "rollback_triggers": rollback_strategy["triggers"],
                    "rollback_procedures": rollback_strategy["procedures"],
                    "rollback_timeline": rollback_strategy["timeline"],
                    "data_backup_requirements": rollback_strategy["backup_requirements"]
                },
                "configuration_templates": {
                    "huawei_templates": configuration_templates["huawei_templates"],
                    "parameter_files": configuration_templates["parameter_files"],
                    "validation_scripts": configuration_templates["validation_scripts"]
                },
                "mml_commands": {
                    "implementation_commands": mml_commands["implementation"],
                    "verification_commands": mml_commands["verification"],
                    "rollback_commands": mml_commands["rollback"],
                    "command_sequence": mml_commands["sequence"]
                },
                "impact_simulation": {
                    "predicted_kpi_changes": impact_simulation["kpi_predictions"],
                    "performance_forecast": impact_simulation["performance_forecast"],
                    "confidence_intervals": impact_simulation["confidence_intervals"],
                    "scenario_analysis": impact_simulation["scenario_analysis"]
                },
                "recommendations": self._generate_configuration_recommendations_summary(
                    configuration_recommendations, risk_assessment
                ),
                "execution_time": duration
            }
            
            logger.info(f"✅ Configuration Agent completed in {duration:.1f}s - {len(configuration_recommendations.get('parameter_changes', {}))} parameters optimized")
            return result
            
        except Exception as e:
            logger.error(f"❌ Configuration Agent failed: {e}")
            return await self._handle_configuration_failure(str(e), context)
    
    def _extract_analytics_results(self, context: Dict) -> Dict[str, Any]:
        """Extract analytics results from previous stage"""
        previous_results = context.get("previous_results", {})
        analytics_result = previous_results.get("kpi_analytics", {})
        
        if not analytics_result:
            logger.warning("No analytics results found, using fallback data")
            return {"optimization_roadmap": {"opportunities": []}}
        
        return analytics_result
    
    def _extract_target_sites(self, context: Dict) -> List[str]:
        """Extract target sites from context"""
        previous_results = context.get("previous_results", {})
        network_result = previous_results.get("network_connector", {})
        target_sites = network_result.get("target_sites", [])
        
        if not target_sites:
            # Real Bindura sites based on historical data
            target_sites = [
                "MSH0013-Bindura-Zaoga", 
                "MSH-0331-Chiwaridzo 2", 
                "MSH-0112-Bindura Hospital", 
                "MSH-0014-Chipadze"
            ]
        
        return target_sites
    
    async def _analyze_optimization_requirements(self, analytics_results: Dict) -> Dict[str, Any]:
        """Analyze optimization requirements based on analytics insights"""
        await asyncio.sleep(random.uniform(1, 3))
        
        # Extract optimization opportunities from analytics
        roadmap = analytics_results.get("optimization_roadmap", {})
        opportunities = roadmap.get("opportunities", [])
        
        # Extract performance gaps
        benchmark_analysis = analytics_results.get("benchmark_analysis", {})
        performance_gaps = benchmark_analysis.get("performance_gaps", {})
        
        # Extract root causes
        root_cause_analysis = analytics_results.get("root_cause_analysis", {})
        primary_factors = root_cause_analysis.get("primary_factors", [])
        
        # Determine primary objectives
        primary_objectives = []
        secondary_objectives = []
        
        # Analyze critical opportunities
        critical_opportunities = [o for o in opportunities if o.get("priority") == "critical"]
        high_opportunities = [o for o in opportunities if o.get("priority") == "high"]
        
        for opportunity in critical_opportunities:
            if opportunity.get("target_kpi"):
                primary_objectives.append({
                    "kpi": opportunity["target_kpi"],
                    "improvement_target": opportunity.get("estimated_improvement", "10%"),
                    "priority": "critical",
                    "source": "optimization_opportunity"
                })
        
        for opportunity in high_opportunities:
            if opportunity.get("target_kpi"):
                secondary_objectives.append({
                    "kpi": opportunity["target_kpi"],
                    "improvement_target": opportunity.get("estimated_improvement", "5%"),
                    "priority": "high",
                    "source": "optimization_opportunity"
                })
        
        # Analyze performance gaps
        tier1_gaps = performance_gaps.get("tier_1_operator", {})
        for kpi_name, gap_info in tier1_gaps.items():
            if gap_info.get("gap_percentage", 0) > 5:  # Significant gap
                objective = {
                    "kpi": kpi_name,
                    "improvement_target": f"{gap_info['gap_percentage']}%",
                    "priority": "high" if gap_info["gap_percentage"] > 10 else "medium",
                    "source": "benchmark_gap"
                }
                
                if objective["priority"] == "high":
                    primary_objectives.append(objective)
                else:
                    secondary_objectives.append(objective)
        
        # Determine optimization strategy
        if len(critical_opportunities) > 2:
            strategy = "critical_issue_resolution"
        elif len(primary_objectives) > 3:
            strategy = "comprehensive_optimization"
        elif any("coverage" in obj["kpi"] for obj in primary_objectives):
            strategy = "coverage_focused"
        elif any("throughput" in obj["kpi"] for obj in primary_objectives):
            strategy = "capacity_focused"
        else:
            strategy = "balanced_optimization"
        
        # Select optimization templates
        selected_templates = self._select_optimization_templates(
            primary_objectives, secondary_objectives, strategy
        )
        
        # Define constraints
        constraints = {
            "maximum_parameter_changes": 10,
            "risk_tolerance": "medium",
            "implementation_window": "maintenance_hours",
            "rollback_time_limit": "30_minutes",
            "affected_users_limit": 1000
        }
        
        return {
            "primary_objectives": primary_objectives,
            "secondary_objectives": secondary_objectives,
            "optimization_strategy": strategy,
            "selected_templates": selected_templates,
            "constraints": constraints,
            "requirements_timestamp": datetime.now().isoformat()
        }
    
    def _select_optimization_templates(self, primary_objectives: List[Dict], 
                                     secondary_objectives: List[Dict], strategy: str) -> List[str]:
        """Select appropriate optimization templates"""
        selected_templates = []
        
        # Get KPIs that need optimization
        all_objectives = primary_objectives + secondary_objectives
        target_kpis = [obj["kpi"] for obj in all_objectives]
        
        # Coverage optimization
        coverage_kpis = ["rsrp_coverage", "rsrq_quality", "handover_success_rate"]
        if any(kpi in target_kpis for kpi in coverage_kpis):
            selected_templates.append("coverage_optimization")
        
        # Capacity optimization
        capacity_kpis = ["average_dl_throughput", "average_ul_throughput", "erab_setup_success_rate"]
        if any(kpi in target_kpis for kpi in capacity_kpis):
            selected_templates.append("capacity_optimization")
        
        # Reliability optimization
        reliability_kpis = ["rrc_connection_success_rate", "call_drop_rate", "rach_setup_success_rate"]
        if any(kpi in target_kpis for kpi in reliability_kpis):
            selected_templates.append("reliability_optimization")
        
        # If multiple templates or strategy is balanced, include balanced optimization
        if len(selected_templates) > 1 or strategy == "balanced_optimization":
            selected_templates = ["balanced_optimization"]
        
        # Default to balanced if no specific templates identified
        if not selected_templates:
            selected_templates = ["balanced_optimization"]
        
        return selected_templates
    
    async def _generate_configuration_recommendations(self, optimization_requirements: Dict, 
                                                    analytics_results: Dict) -> Dict[str, Any]:
        """Generate specific configuration parameter recommendations"""
        await asyncio.sleep(random.uniform(2, 5))
        
        parameter_changes = {}
        rationale = {}
        expected_improvements = {}
        priority_ranking = []
        
        # Get selected templates
        selected_templates = optimization_requirements.get("selected_templates", [])
        primary_objectives = optimization_requirements.get("primary_objectives", [])
        
        for template_name in selected_templates:
            if template_name in self.optimization_templates:
                template = self.optimization_templates[template_name]
                adjustments = template["parameter_adjustments"]
                
                for param_name, adjustment_type in adjustments.items():
                    if param_name in self.parameter_definitions:
                        param_def = self.parameter_definitions[param_name]
                        
                        # Generate specific parameter value
                        new_value = self._calculate_parameter_value(
                            param_name, param_def, adjustment_type, primary_objectives
                        )
                        
                        # Get current value (simulated)
                        current_value = self._get_current_parameter_value(param_name, param_def)
                        
                        if new_value != current_value:
                            parameter_changes[param_name] = {
                                "current_value": current_value,
                                "recommended_value": new_value,
                                "change_percentage": self._calculate_change_percentage(current_value, new_value),
                                "parameter_type": param_def["type"],
                                "affected_kpis": param_def["impact_kpis"],
                                "optimization_template": template_name,
                                "change_justification": self._get_change_justification(
                                    param_name, adjustment_type, primary_objectives
                                )
                            }
                            
                            rationale[param_name] = {
                                "optimization_goal": template["description"],
                                "technical_rationale": self._get_technical_rationale(param_name, adjustment_type),
                                "expected_impact": param_def["impact_kpis"],
                                "confidence_level": random.uniform(70, 95)
                            }
                            
                            # Track expected improvements
                            for kpi in param_def["impact_kpis"]:
                                if kpi not in expected_improvements:
                                    expected_improvements[kpi] = []
                                expected_improvements[kpi].append({
                                    "parameter": param_name,
                                    "expected_change": self._estimate_kpi_improvement(
                                        param_name, current_value, new_value
                                    ),
                                    "confidence": round(random.uniform(60, 90), 1)
                                })
        
        # Create priority ranking
        priority_ranking = self._create_priority_ranking(parameter_changes, primary_objectives)
        
        # Determine scope
        scope = {
            "affected_sites": len(self._extract_target_sites({"previous_results": {}})),
            "parameter_count": len(parameter_changes),
            "kpi_impact_scope": len(set(
                kpi for changes in parameter_changes.values() 
                for kpi in changes["affected_kpis"]
            )),
            "implementation_complexity": self._assess_implementation_complexity(parameter_changes)
        }
        
        return {
            "parameter_changes": parameter_changes,
            "rationale": rationale,
            "expected_improvements": expected_improvements,
            "scope": scope,
            "priority_ranking": priority_ranking,
            "generation_timestamp": datetime.now().isoformat()
        }
    
    def _calculate_parameter_value(self, param_name: str, param_def: Dict, 
                                 adjustment_type: str, objectives: List[Dict]) -> Any:
        """Calculate specific parameter value based on adjustment type"""
        current_value = self._get_current_parameter_value(param_name, param_def)
        
        if param_def["type"] == "enum":
            # For enum types, select optimal value
            values = param_def["values"]
            if adjustment_type == "optimize_for_throughput":
                return values[-1] if len(values) > 1 else values[0]
            elif adjustment_type == "optimize_for_reliability":
                return values[0] if len(values) > 0 else current_value
            else:
                return random.choice(values)
        
        elif param_def["type"] == "integer":
            param_range = param_def["range"]
            min_val, max_val = param_range[0], param_range[1]
            
            if adjustment_type == "increase_moderate":
                change = (max_val - current_value) * 0.3
            elif adjustment_type == "decrease_small":
                change = -(current_value - min_val) * 0.15
            elif adjustment_type == "increase_small":
                change = (max_val - current_value) * 0.15
            elif adjustment_type == "moderate_adjustment":
                change = random.uniform(-0.2, 0.2) * (max_val - min_val)
            elif adjustment_type == "fine_tune":
                change = random.uniform(-0.1, 0.1) * (max_val - min_val)
            else:
                change = random.uniform(-0.1, 0.1) * current_value
            
            new_value = int(max(min_val, min(max_val, current_value + change)))
            return new_value
        
        elif param_def["type"] == "float":
            param_range = param_def["range"]
            min_val, max_val = param_range[0], param_range[1]
            
            if adjustment_type == "increase_moderate":
                change = (max_val - current_value) * 0.3
            elif adjustment_type == "decrease_small":
                change = -(current_value - min_val) * 0.15
            else:
                change = random.uniform(-0.1, 0.1) * (max_val - min_val)
            
            new_value = max(min_val, min(max_val, current_value + change))
            return round(new_value, 2)
        
        return current_value
    
    def _get_current_parameter_value(self, param_name: str, param_def: Dict) -> Any:
        """Get current parameter value (simulated)"""
        # In a real implementation, this would query the network management system
        default_value = param_def["default"]
        
        if param_def["type"] == "integer":
            # Add some variation around default
            variation = random.uniform(-0.2, 0.2)
            param_range = param_def["range"]
            varied_value = default_value + (variation * (param_range[1] - param_range[0]) * 0.1)
            return int(max(param_range[0], min(param_range[1], varied_value)))
        elif param_def["type"] == "float":
            # Add some variation around default
            variation = random.uniform(-0.1, 0.1)
            param_range = param_def["range"]
            varied_value = default_value + (variation * (param_range[1] - param_range[0]))
            return round(max(param_range[0], min(param_range[1], varied_value)), 2)
        else:
            return default_value
    
    def _calculate_change_percentage(self, current_value: Any, new_value: Any) -> float:
        """Calculate percentage change between current and new value"""
        if isinstance(current_value, (int, float)) and current_value != 0:
            return round(((new_value - current_value) / current_value) * 100, 1)
        else:
            return 0.0
    
    def _get_change_justification(self, param_name: str, adjustment_type: str, 
                                objectives: List[Dict]) -> str:
        """Get justification for parameter change"""
        justifications = {
            "increase_moderate": f"Increasing {param_name} to improve performance based on optimization analysis",
            "decrease_small": f"Fine-tuning {param_name} downward to optimize resource utilization", 
            "increase_small": f"Minor increase in {param_name} to enhance service quality",
            "moderate_adjustment": f"Adjusting {param_name} based on comprehensive performance analysis",
            "fine_tune": f"Fine-tuning {param_name} for optimal balance across KPIs",
            "optimize_for_throughput": f"Optimizing {param_name} to maximize throughput performance",
            "optimize_for_reliability": f"Configuring {param_name} for enhanced connection reliability"
        }
        
        return justifications.get(adjustment_type, f"Optimizing {param_name} based on analytics insights")
    
    def _get_technical_rationale(self, param_name: str, adjustment_type: str) -> str:
        """Get technical rationale for parameter adjustment"""
        rationales = {
            "dl_rs_power": "Reference signal power adjustment impacts coverage and signal quality",
            "handover_a3_offset": "A3 offset controls handover timing and ping-pong effects",
            "rrc_inactivity_timer": "Longer timers reduce connection setup overhead",
            "rach_prach_config_index": "PRACH configuration affects random access success",
            "erab_qci_priority": "QCI priority impacts bearer establishment and throughput"
        }
        
        return rationales.get(param_name, f"Parameter {param_name} adjustment based on network optimization theory")
    
    def _estimate_kpi_improvement(self, param_name: str, current_value: Any, new_value: Any) -> str:
        """Estimate KPI improvement from parameter change"""
        change_magnitude = abs(self._calculate_change_percentage(current_value, new_value))
        
        if change_magnitude < 5:
            return "1-3% improvement"
        elif change_magnitude < 15:
            return "3-8% improvement"
        elif change_magnitude < 30:
            return "5-15% improvement"
        else:
            return "10-25% improvement"
    
    def _create_priority_ranking(self, parameter_changes: Dict, objectives: List[Dict]) -> List[Dict[str, Any]]:
        """Create priority ranking for parameter changes"""
        ranking = []
        
        for param_name, change_info in parameter_changes.items():
            # Calculate priority score
            priority_score = 0
            
            # Impact on primary objectives
            affected_kpis = change_info["affected_kpis"]
            primary_kpis = [obj["kpi"] for obj in objectives]
            
            for kpi in affected_kpis:
                if kpi in primary_kpis:
                    priority_score += 10
                else:
                    priority_score += 3
            
            # Change magnitude factor
            change_pct = abs(change_info["change_percentage"])
            if change_pct > 20:
                priority_score += 5
            elif change_pct > 10:
                priority_score += 3
            else:
                priority_score += 1
            
            # Parameter impact weight
            if param_name in self.parameter_definitions:
                param_def = self.parameter_definitions[param_name]
                kpi_count = len(param_def["impact_kpis"])
                priority_score += kpi_count * 2
            
            ranking.append({
                "parameter": param_name,
                "priority_score": priority_score,
                "implementation_order": 0,  # Will be set after sorting
                "rationale": f"Affects {len(affected_kpis)} KPIs with {change_pct:.1f}% change"
            })
        
        # Sort by priority score
        ranking.sort(key=lambda x: x["priority_score"], reverse=True)
        
        # Set implementation order
        for i, item in enumerate(ranking):
            item["implementation_order"] = i + 1
        
        return ranking
    
    def _assess_implementation_complexity(self, parameter_changes: Dict) -> str:
        """Assess implementation complexity"""
        change_count = len(parameter_changes)
        
        # Count different parameter types
        enum_changes = sum(1 for change in parameter_changes.values() 
                          if change["parameter_type"] == "enum")
        
        # Calculate average change magnitude
        change_percentages = [abs(change["change_percentage"]) 
                            for change in parameter_changes.values()]
        avg_change = statistics.mean(change_percentages) if change_percentages else 0
        
        if change_count <= 3 and avg_change <= 10:
            return "low"
        elif change_count <= 6 and avg_change <= 20:
            return "medium"
        else:
            return "high"
    
    async def _perform_risk_assessment(self, configuration_recommendations: Dict) -> Dict[str, Any]:
        """Perform comprehensive risk assessment for configuration changes"""
        await asyncio.sleep(random.uniform(1, 3))
        
        parameter_changes = configuration_recommendations.get("parameter_changes", {})
        risk_factors = []
        overall_risk_score = 0
        
        for param_name, change_info in parameter_changes.items():
            # Assess individual parameter risk
            param_risk = self._assess_parameter_risk(param_name, change_info)
            risk_factors.append(param_risk)
            overall_risk_score += param_risk["risk_score"]
        
        # Calculate overall risk level
        if parameter_changes:
            avg_risk_score = overall_risk_score / len(parameter_changes)
        else:
            avg_risk_score = 0
        
        if avg_risk_score <= 3:
            overall_risk_level = "low"
        elif avg_risk_score <= 6:
            overall_risk_level = "medium"
        else:
            overall_risk_level = "high"
        
        # Generate mitigation measures
        mitigation_measures = self._generate_mitigation_measures(risk_factors, overall_risk_level)
        
        # Create risk matrix
        risk_matrix = self._create_risk_matrix(risk_factors)
        
        # Determine approval requirements
        approval_requirements = self._determine_approval_requirements(overall_risk_level, parameter_changes)
        
        return {
            "overall_risk_level": overall_risk_level,
            "overall_risk_score": round(avg_risk_score, 1),
            "risk_factors": risk_factors,
            "mitigation_measures": mitigation_measures,
            "risk_matrix": risk_matrix,
            "approval_requirements": approval_requirements,
            "assessment_timestamp": datetime.now().isoformat()
        }
    
    def _assess_parameter_risk(self, param_name: str, change_info: Dict) -> Dict[str, Any]:
        """Assess risk for individual parameter change"""
        risk_score = 0
        risk_factors = []
        
        # Change magnitude risk
        change_pct = abs(change_info["change_percentage"])
        if change_pct > 25:
            risk_score += 3
            risk_factors.append("high_change_magnitude")
        elif change_pct > 10:
            risk_score += 2
            risk_factors.append("moderate_change_magnitude")
        else:
            risk_score += 1
        
        # KPI impact scope risk
        affected_kpis = change_info["affected_kpis"]
        kpi_count = len(affected_kpis)
        if kpi_count >= 4:
            risk_score += 3
            risk_factors.append("wide_kpi_impact")
        elif kpi_count >= 2:
            risk_score += 2
            risk_factors.append("moderate_kpi_impact")
        else:
            risk_score += 1
        
        # Parameter criticality
        critical_params = ["dl_rs_power", "handover_a3_offset", "rrc_inactivity_timer"]
        if param_name in critical_params:
            risk_score += 2
            risk_factors.append("critical_parameter")
        
        # Parameter type risk
        if change_info["parameter_type"] == "enum":
            risk_score += 1  # Enum changes are generally safer
        else:
            risk_score += 2  # Numeric changes have more variability
        
        # Determine risk level
        if risk_score <= 4:
            risk_level = "low"
        elif risk_score <= 7:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        return {
            "parameter": param_name,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "change_magnitude": change_pct,
            "affected_kpis": affected_kpis,
            "mitigation_priority": "high" if risk_level == "high" else "medium"
        }
    
    def _generate_mitigation_measures(self, risk_factors: List[Dict], overall_risk_level: str) -> List[Dict[str, str]]:
        """Generate risk mitigation measures"""
        measures = []
        
        # High-risk parameter changes
        high_risk_params = [rf for rf in risk_factors if rf["risk_level"] == "high"]
        if high_risk_params:
            measures.append({
                "type": "phased_implementation",
                "description": "Implement high-risk changes in phases with validation between each phase",
                "applicability": "high_risk_parameters"
            })
            
            measures.append({
                "type": "enhanced_monitoring",
                "description": "Deploy real-time monitoring with 1-minute granularity during implementation",
                "applicability": "high_risk_parameters"
            })
        
        # Change magnitude mitigation
        high_magnitude_changes = [rf for rf in risk_factors if "high_change_magnitude" in rf["risk_factors"]]
        if high_magnitude_changes:
            measures.append({
                "type": "gradual_adjustment",
                "description": "Implement large changes gradually in 25% increments",
                "applicability": "high_magnitude_changes"
            })
        
        # Wide impact mitigation
        wide_impact_changes = [rf for rf in risk_factors if "wide_kpi_impact" in rf["risk_factors"]]
        if wide_impact_changes:
            measures.append({
                "type": "pilot_site_testing",
                "description": "Test changes on pilot site before full deployment",
                "applicability": "wide_impact_changes"
            })
        
        # Overall risk mitigation
        if overall_risk_level == "high":
            measures.append({
                "type": "emergency_rollback_plan",
                "description": "Prepare automated rollback procedures with 5-minute execution time",
                "applicability": "all_changes"
            })
            
            measures.append({
                "type": "expert_oversight",
                "description": "Assign senior RF engineer for real-time oversight during implementation",
                "applicability": "all_changes"
            })
        
        return measures
    
    def _create_risk_matrix(self, risk_factors: List[Dict]) -> Dict[str, Any]:
        """Create risk matrix categorizing risks"""
        risk_matrix = {
            "low_impact_low_probability": [],
            "low_impact_high_probability": [],
            "high_impact_low_probability": [],
            "high_impact_high_probability": []
        }
        
        for risk_factor in risk_factors:
            # Determine impact level
            kpi_count = len(risk_factor["affected_kpis"])
            impact = "high" if kpi_count >= 3 else "low"
            
            # Determine probability (based on change magnitude)
            change_magnitude = risk_factor["change_magnitude"]
            probability = "high" if change_magnitude > 15 else "low"
            
            # Categorize
            category = f"{impact}_impact_{probability}_probability"
            risk_matrix[category].append({
                "parameter": risk_factor["parameter"],
                "risk_score": risk_factor["risk_score"],
                "description": f"{risk_factor['parameter']} change with {change_magnitude:.1f}% magnitude"
            })
        
        return risk_matrix
    
    def _determine_approval_requirements(self, overall_risk_level: str, parameter_changes: Dict) -> Dict[str, Any]:
        """Determine approval requirements based on risk level"""
        requirements = {
            "approval_level": "none",
            "required_approvers": [],
            "approval_timeframe": "immediate",
            "documentation_requirements": [],
            "testing_requirements": []
        }
        
        if overall_risk_level == "low":
            requirements.update({
                "approval_level": "operational",
                "required_approvers": ["network_operations_engineer"],
                "approval_timeframe": "same_day",
                "documentation_requirements": ["change_summary", "rollback_plan"],
                "testing_requirements": ["basic_validation"]
            })
        elif overall_risk_level == "medium":
            requirements.update({
                "approval_level": "management",
                "required_approvers": ["network_operations_manager", "rf_optimization_lead"],
                "approval_timeframe": "24_hours",
                "documentation_requirements": ["detailed_change_plan", "risk_assessment", "rollback_plan"],
                "testing_requirements": ["pilot_site_validation", "kpi_monitoring_plan"]
            })
        else:  # high risk
            requirements.update({
                "approval_level": "executive",
                "required_approvers": ["network_director", "cto", "rf_optimization_lead"],
                "approval_timeframe": "48_hours",
                "documentation_requirements": [
                    "comprehensive_change_plan", "detailed_risk_assessment", 
                    "rollback_plan", "business_impact_analysis"
                ],
                "testing_requirements": [
                    "extensive_pilot_testing", "simulation_validation", 
                    "emergency_response_plan"
                ]
            })
        
        return requirements
    
    async def _create_implementation_plan(self, configuration_recommendations: Dict, 
                                        risk_assessment: Dict) -> Dict[str, Any]:
        """Create detailed implementation plan"""
        await asyncio.sleep(random.uniform(1, 3))
        
        parameter_changes = configuration_recommendations.get("parameter_changes", {})
        priority_ranking = configuration_recommendations.get("priority_ranking", [])
        overall_risk_level = risk_assessment.get("overall_risk_level", "medium")
        
        # Create implementation phases
        phases = self._create_implementation_phases(priority_ranking, overall_risk_level)
        
        # Generate timeline
        timeline = self._generate_implementation_timeline(phases, overall_risk_level)
        
        # Determine resource requirements
        resource_requirements = self._determine_resource_requirements(parameter_changes, overall_risk_level)
        
        # Create validation checkpoints
        validation_checkpoints = self._create_validation_checkpoints(phases, parameter_changes)
        
        # Define success criteria
        success_criteria = self._define_success_criteria(configuration_recommendations)
        
        return {
            "phases": phases,
            "timeline": timeline,
            "resource_requirements": resource_requirements,
            "validation_checkpoints": validation_checkpoints,
            "success_criteria": success_criteria,
            "plan_timestamp": datetime.now().isoformat()
        }
    
    def _create_implementation_phases(self, priority_ranking: List[Dict], risk_level: str) -> List[Dict[str, Any]]:
        """Create implementation phases based on priority and risk"""
        phases = []
        
        if risk_level == "high":
            # High risk: implement in smaller phases
            phase_size = 2
        elif risk_level == "medium":
            # Medium risk: moderate phase sizes
            phase_size = 3
        else:
            # Low risk: larger phases
            phase_size = 5
        
        # Group parameters into phases
        for i in range(0, len(priority_ranking), phase_size):
            phase_params = priority_ranking[i:i + phase_size]
            
            phase = {
                "phase_id": f"PHASE_{i // phase_size + 1}",
                "phase_name": f"Implementation Phase {i // phase_size + 1}",
                "parameters": [p["parameter"] for p in phase_params],
                "phase_priority": "critical" if i == 0 else "high" if i < phase_size * 2 else "medium",
                "estimated_duration": f"{len(phase_params) * 15}-{len(phase_params) * 30} minutes",
                "validation_required": True,
                "rollback_checkpoint": True
            }
            phases.append(phase)
        
        return phases
    
    def _generate_implementation_timeline(self, phases: List[Dict], risk_level: str) -> Dict[str, Any]:
        """Generate implementation timeline"""
        # Calculate timing based on risk level
        if risk_level == "high":
            prep_time = 4  # hours
            phase_gap = 2  # hours between phases
            validation_time = 1  # hour per phase
        elif risk_level == "medium":
            prep_time = 2  # hours
            phase_gap = 1  # hour between phases
            validation_time = 0.5  # hour per phase
        else:
            prep_time = 1  # hour
            phase_gap = 0.5  # hour between phases
            validation_time = 0.25  # hour per phase
        
        timeline_events = []
        current_time = datetime.now()
        
        # Preparation phase
        timeline_events.append({
            "event": "preparation_start",
            "scheduled_time": current_time.isoformat(),
            "duration_hours": prep_time,
            "description": "Pre-implementation preparation and system checks"
        })
        
        current_time += timedelta(hours=prep_time)
        
        # Implementation phases
        for i, phase in enumerate(phases):
            # Phase implementation
            timeline_events.append({
                "event": f"phase_{i+1}_start",
                "scheduled_time": current_time.isoformat(),
                "duration_hours": 0.5,
                "description": f"Implement {phase['phase_name']}"
            })
            
            current_time += timedelta(hours=0.5)
            
            # Validation
            timeline_events.append({
                "event": f"phase_{i+1}_validation",
                "scheduled_time": current_time.isoformat(),
                "duration_hours": validation_time,
                "description": f"Validate {phase['phase_name']} results"
            })
            
            current_time += timedelta(hours=validation_time)
            
            # Gap before next phase (except for last phase)
            if i < len(phases) - 1:
                current_time += timedelta(hours=phase_gap)
        
        # Final validation
        timeline_events.append({
            "event": "final_validation",
            "scheduled_time": current_time.isoformat(),
            "duration_hours": 1,
            "description": "Comprehensive final validation and monitoring"
        })
        
        total_duration = (current_time - datetime.now()).total_seconds() / 3600 + 1
        
        return {
            "total_duration_hours": round(total_duration, 1),
            "timeline_events": timeline_events,
            "recommended_start_time": "maintenance_window",
            "completion_estimate": (current_time + timedelta(hours=1)).isoformat()
        }
    
    def _determine_resource_requirements(self, parameter_changes: Dict, risk_level: str) -> Dict[str, Any]:
        """Determine resource requirements for implementation"""
        base_engineer_hours = len(parameter_changes) * 0.5
        
        # Adjust based on risk level
        if risk_level == "high":
            engineer_hours = base_engineer_hours * 2
            senior_oversight = True
            monitoring_staff = 2
        elif risk_level == "medium":
            engineer_hours = base_engineer_hours * 1.5
            senior_oversight = True
            monitoring_staff = 1
        else:
            engineer_hours = base_engineer_hours
            senior_oversight = False
            monitoring_staff = 1
        
        return {
            "rf_engineer_hours": round(engineer_hours, 1),
            "network_operations_hours": round(engineer_hours * 0.5, 1),
            "senior_oversight_required": senior_oversight,
            "monitoring_staff_count": monitoring_staff,
            "required_skills": [
                "huawei_eNodeB_configuration",
                "rf_optimization",
                "network_performance_monitoring"
            ],
            "tools_required": [
                "iMaster_MAE",
                "MML_command_interface",
                "network_monitoring_dashboard"
            ]
        }
    
    def _create_validation_checkpoints(self, phases: List[Dict], parameter_changes: Dict) -> List[Dict[str, Any]]:
        """Create validation checkpoints for implementation"""
        checkpoints = []
        
        for i, phase in enumerate(phases):
            checkpoint = {
                "checkpoint_id": f"CHECKPOINT_{i+1}",
                "phase_id": phase["phase_id"],
                "validation_type": "automated_and_manual",
                "validation_criteria": [
                    "parameter_values_applied_correctly",
                    "no_critical_alarms_generated",
                    "kpi_degradation_within_acceptable_limits"
                ],
                "kpi_monitoring": [],
                "success_thresholds": {},
                "rollback_triggers": []
            }
            
            # Add KPI monitoring for affected parameters
            for param_name in phase["parameters"]:
                if param_name in parameter_changes:
                    affected_kpis = parameter_changes[param_name]["affected_kpis"]
                    checkpoint["kpi_monitoring"].extend(affected_kpis)
                    
                    # Set success thresholds
                    for kpi in affected_kpis:
                        checkpoint["success_thresholds"][kpi] = {
                            "max_degradation": "5%",
                            "recovery_time": "15_minutes"
                        }
                        
                        # Set rollback triggers
                        checkpoint["rollback_triggers"].append({
                            "condition": f"{kpi}_degradation_exceeds_10%",
                            "action": "immediate_rollback",
                            "escalation": "automatic"
                        })
            
            # Remove duplicates
            checkpoint["kpi_monitoring"] = list(set(checkpoint["kpi_monitoring"]))
            
            checkpoints.append(checkpoint)
        
        return checkpoints
    
    def _define_success_criteria(self, configuration_recommendations: Dict) -> Dict[str, Any]:
        """Define success criteria for configuration implementation"""
        expected_improvements = configuration_recommendations.get("expected_improvements", {})
        
        success_criteria = {
            "technical_criteria": [],
            "business_criteria": [],
            "operational_criteria": [],
            "overall_success_threshold": "80%"
        }
        
        # Technical criteria based on expected improvements
        for kpi, improvements in expected_improvements.items():
            if improvements:
                avg_improvement = statistics.mean([
                    float(imp["expected_change"].split("-")[0].replace("%", "").replace(" improvement", ""))
                    for imp in improvements
                    if "%" in imp["expected_change"]
                ])
                
                success_criteria["technical_criteria"].append({
                    "metric": kpi,
                    "target_improvement": f"{avg_improvement:.1f}%",
                    "measurement_period": "24_hours_post_implementation",
                    "success_threshold": f"{avg_improvement * 0.7:.1f}%"  # 70% of expected
                })
        
        # Business criteria
        success_criteria["business_criteria"] = [
            {
                "metric": "user_experience_improvement",
                "target": "no_degradation",
                "measurement": "customer_complaints_monitoring"
            },
            {
                "metric": "service_availability",
                "target": ">99.9%",
                "measurement": "service_monitoring_dashboard"
            }
        ]
        
        # Operational criteria
        success_criteria["operational_criteria"] = [
            {
                "metric": "implementation_time",
                "target": "within_maintenance_window",
                "measurement": "actual_vs_planned_duration"
            },
            {
                "metric": "rollback_incidents",
                "target": "zero_rollbacks",
                "measurement": "implementation_log_analysis"
            },
            {
                "metric": "alarm_generation",
                "target": "no_critical_alarms",
                "measurement": "alarm_monitoring_system"
            }
        ]
        
        return success_criteria
    
    async def _generate_rollback_strategy(self, configuration_recommendations: Dict) -> Dict[str, Any]:
        """Generate comprehensive rollback strategy"""
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        parameter_changes = configuration_recommendations.get("parameter_changes", {})
        
        # Define rollback triggers
        triggers = [
            {
                "trigger_type": "kpi_degradation",
                "condition": "any_critical_kpi_degrades_more_than_10%",
                "auto_trigger": True,
                "escalation": "immediate"
            },
            {
                "trigger_type": "alarm_threshold",
                "condition": "critical_alarms_exceed_baseline_by_50%",
                "auto_trigger": True,
                "escalation": "immediate"
            },
            {
                "trigger_type": "user_complaints",
                "condition": "customer_complaints_increase_by_100%",
                "auto_trigger": False,
                "escalation": "manual_review"
            },
            {
                "trigger_type": "service_disruption",
                "condition": "service_availability_drops_below_99%",
                "auto_trigger": True,
                "escalation": "emergency"
            }
        ]
        
        # Generate rollback procedures
        procedures = []
        
        # Create rollback commands for each parameter
        for param_name, change_info in parameter_changes.items():
            procedure = {
                "parameter": param_name,
                "rollback_method": "restore_previous_value",
                "previous_value": change_info["current_value"],
                "rollback_command": self._generate_rollback_command(param_name, change_info["current_value"]),
                "verification_command": self._generate_verification_command(param_name),
                "estimated_time": "2-5 minutes"
            }
            procedures.append(procedure)
        
        # Rollback timeline
        timeline = {
            "detection_to_decision": "1-3 minutes",
            "decision_to_execution": "1-2 minutes", 
            "execution_duration": f"{len(procedures) * 2}-{len(procedures) * 5} minutes",
            "verification_time": "5-10 minutes",
            "total_rollback_time": f"{5 + len(procedures) * 2}-{15 + len(procedures) * 5} minutes"
        }
        
        # Backup requirements
        backup_requirements = {
            "configuration_backup": "automatic_pre_implementation_snapshot",
            "baseline_kpi_data": "24_hour_baseline_capture",
            "alarm_baseline": "current_alarm_state_snapshot",
            "backup_storage": "network_management_system",
            "backup_retention": "30_days"
        }
        
        return {
            "triggers": triggers,
            "procedures": procedures,
            "timeline": timeline,
            "backup_requirements": backup_requirements,
            "rollback_validation": [
                "verify_parameter_values_restored",
                "confirm_kpi_recovery_trend",
                "validate_alarm_state_normalized"
            ]
        }
    
    def _generate_rollback_command(self, param_name: str, previous_value: Any) -> str:
        """Generate MML rollback command for parameter"""
        return f"MOD CELL: CELLID=<CELLID>, {param_name.upper()}={previous_value};"
    
    def _generate_verification_command(self, param_name: str) -> str:
        """Generate MML verification command for parameter"""
        return f"LST CELL: CELLID=<CELLID>, {param_name.upper()};"
    
    async def _create_configuration_templates(self, configuration_recommendations: Dict) -> Dict[str, Any]:
        """Create configuration templates and files"""
        await asyncio.sleep(random.uniform(1, 2))
        
        parameter_changes = configuration_recommendations.get("parameter_changes", {})
        
        # Generate Huawei-specific templates
        huawei_templates = self._generate_huawei_templates(parameter_changes)
        
        # Generate parameter files
        parameter_files = self._generate_parameter_files(parameter_changes)
        
        # Generate validation scripts
        validation_scripts = self._generate_validation_scripts(parameter_changes)
        
        return {
            "huawei_templates": huawei_templates,
            "parameter_files": parameter_files,
            "validation_scripts": validation_scripts
        }
    
    def _generate_huawei_templates(self, parameter_changes: Dict) -> Dict[str, Any]:
        """Generate Huawei-specific configuration templates"""
        templates = {
            "cell_level_config": [],
            "enodeb_level_config": [],
            "batch_config_script": []
        }
        
        for param_name, change_info in parameter_changes.items():
            new_value = change_info["recommended_value"]
            
            # Cell-level parameters
            if param_name in ["dl_rs_power", "handover_a3_offset", "handover_a3_hysteresis"]:
                templates["cell_level_config"].append({
                    "parameter": param_name,
                    "command_template": f"MOD CELL: CELLID=<CELLID>, {param_name.upper()}={new_value};",
                    "applicable_cells": "all_target_cells"
                })
            
            # eNodeB-level parameters  
            elif param_name in ["rach_prach_config_index", "rrc_inactivity_timer"]:
                templates["enodeb_level_config"].append({
                    "parameter": param_name,
                    "command_template": f"MOD ENODEB: ENODEBID=<ENODEBID>, {param_name.upper()}={new_value};",
                    "applicable_sites": "all_target_sites"
                })
            
            # Batch script commands
            templates["batch_config_script"].append(
                f"// Configure {param_name}\n"
                f"MOD CELL: CELLID=<CELLID>, {param_name.upper()}={new_value};\n"
                f"// Verify {param_name}\n"
                f"LST CELL: CELLID=<CELLID>, {param_name.upper()};\n"
            )
        
        return templates
    
    def _generate_parameter_files(self, parameter_changes: Dict) -> Dict[str, Any]:
        """Generate parameter configuration files"""
        files = {
            "csv_import_file": {
                "filename": f"config_changes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "format": "CSV",
                "headers": ["SITE_ID", "CELL_ID", "PARAMETER_NAME", "OLD_VALUE", "NEW_VALUE"],
                "sample_rows": []
            },
            "json_config_file": {
                "filename": f"optimization_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "format": "JSON",
                "content": {}
            }
        }
        
        # Generate sample CSV rows
        for param_name, change_info in parameter_changes.items():
            files["csv_import_file"]["sample_rows"].append({
                "SITE_ID": "<SITE_ID>",
                "CELL_ID": "<CELL_ID>", 
                "PARAMETER_NAME": param_name,
                "OLD_VALUE": change_info["current_value"],
                "NEW_VALUE": change_info["recommended_value"]
            })
        
        # Generate JSON configuration
        files["json_config_file"]["content"] = {
            "configuration_metadata": {
                "optimization_type": "performance_optimization",
                "generated_timestamp": datetime.now().isoformat(),
                "parameter_count": len(parameter_changes)
            },
            "parameter_changes": parameter_changes
        }
        
        return files
    
    def _generate_validation_scripts(self, parameter_changes: Dict) -> Dict[str, Any]:
        """Generate validation scripts"""
        scripts = {
            "pre_implementation_validation": [],
            "post_implementation_validation": [],
            "continuous_monitoring_script": []
        }
        
        # Pre-implementation validation
        scripts["pre_implementation_validation"] = [
            "// Backup current configuration",
            "CFG BACKUP: BACKUPNAME=PRE_OPTIMIZATION_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ";",
            "// Capture baseline KPI values",
            "LST CELLKPI: CELLID=<CELLID>, KPITYPE=ALL;",
            "// Verify system health",
            "DSP ALARM: ALARMTYPE=CRITICAL;"
        ]
        
        # Post-implementation validation
        for param_name in parameter_changes.keys():
            scripts["post_implementation_validation"].extend([
                f"// Verify {param_name} configuration",
                f"LST CELL: CELLID=<CELLID>, {param_name.upper()};",
                f"// Monitor {param_name} impact",
                "LST CELLKPI: CELLID=<CELLID>, KPITYPE=PERFORMANCE;"
            ])
        
        # Continuous monitoring
        scripts["continuous_monitoring_script"] = [
            "// Monitor critical KPIs every 5 minutes for 2 hours",
            "SET MONITOR: INTERVAL=5MIN, DURATION=2HOURS;",
            "MON CELLKPI: CELLID=<CELLID>, KPITYPE=CRITICAL;",
            "// Alert on threshold violations", 
            "SET ALERT: THRESHOLD=10PERCENT, ACTION=NOTIFY;"
        ]
        
        return scripts
    
    async def _generate_mml_commands(self, configuration_recommendations: Dict) -> Dict[str, Any]:
        """Generate MML command sequences"""
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        parameter_changes = configuration_recommendations.get("parameter_changes", {})
        priority_ranking = configuration_recommendations.get("priority_ranking", [])
        
        # Implementation commands
        implementation_commands = []
        verification_commands = []
        rollback_commands = []
        
        for ranking in priority_ranking:
            param_name = ranking["parameter"]
            if param_name in parameter_changes:
                change_info = parameter_changes[param_name]
                
                # Implementation command
                impl_cmd = f"MOD CELL: CELLID=<CELLID>, {param_name.upper()}={change_info['recommended_value']};"
                implementation_commands.append({
                    "sequence": ranking["implementation_order"],
                    "parameter": param_name,
                    "command": impl_cmd,
                    "expected_result": "COMMAND EXECUTED",
                    "estimated_time": "30 seconds"
                })
                
                # Verification command
                verify_cmd = f"LST CELL: CELLID=<CELLID>, {param_name.upper()};"
                verification_commands.append({
                    "sequence": ranking["implementation_order"],
                    "parameter": param_name,
                    "command": verify_cmd,
                    "expected_result": f"{param_name.upper()}={change_info['recommended_value']}",
                    "validation_type": "parameter_value_check"
                })
                
                # Rollback command
                rollback_cmd = f"MOD CELL: CELLID=<CELLID>, {param_name.upper()}={change_info['current_value']};"
                rollback_commands.append({
                    "sequence": ranking["implementation_order"],
                    "parameter": param_name,
                    "command": rollback_cmd,
                    "rollback_reason": "restore_to_baseline",
                    "estimated_time": "30 seconds"
                })
        
        # Command sequence with error handling
        command_sequence = [
            "// Pre-implementation checks",
            "CFG BACKUP: BACKUPNAME=AUTO_BACKUP_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ";",
            "DSP ALARM: ALARMTYPE=CRITICAL;",
            "",
            "// Implementation sequence"
        ]
        
        for cmd in implementation_commands:
            command_sequence.extend([
                f"// Step {cmd['sequence']}: Configure {cmd['parameter']}",
                cmd["command"],
                f"// Verify {cmd['parameter']}",
                verification_commands[cmd["sequence"]-1]["command"],
                ""
            ])
        
        command_sequence.extend([
            "// Post-implementation validation",
            "LST CELLKPI: CELLID=<CELLID>, KPITYPE=ALL;",
            "DSP ALARM: ALARMTYPE=CRITICAL;"
        ])
        
        return {
            "implementation": implementation_commands,
            "verification": verification_commands,
            "rollback": rollback_commands,
            "sequence": command_sequence
        }
    
    async def _simulate_configuration_impact(self, configuration_recommendations: Dict, 
                                           analytics_results: Dict) -> Dict[str, Any]:
        """Simulate impact of configuration changes"""
        await asyncio.sleep(random.uniform(1, 3))
        
        parameter_changes = configuration_recommendations.get("parameter_changes", {})
        expected_improvements = configuration_recommendations.get("expected_improvements", {})
        
        # Predict KPI changes
        kpi_predictions = {}
        performance_forecast = {}
        confidence_intervals = {}
        
        for kpi_name, improvements in expected_improvements.items():
            if improvements:
                # Calculate expected improvement
                improvement_values = []
                for improvement in improvements:
                    if "%" in improvement["expected_change"]:
                        # Parse improvement percentage
                        improvement_str = improvement["expected_change"]
                        if "-" in improvement_str:
                            # Range like "3-8% improvement"
                            min_val = float(improvement_str.split("-")[0])
                            max_val = float(improvement_str.split("-")[1].split("%")[0])
                            avg_improvement = (min_val + max_val) / 2
                        else:
                            # Single value like "5% improvement"
                            avg_improvement = float(improvement_str.split("%")[0])
                        
                        improvement_values.append(avg_improvement)
                
                if improvement_values:
                    predicted_improvement = statistics.mean(improvement_values)
                    
                    kpi_predictions[kpi_name] = {
                        "predicted_improvement_percentage": round(predicted_improvement, 1),
                        "confidence_level": round(statistics.mean([imp["confidence"] for imp in improvements]), 1),
                        "contributing_parameters": [imp["parameter"] for imp in improvements]
                    }
                    
                    # Generate 7-day forecast
                    daily_forecast = []
                    base_improvement = predicted_improvement
                    
                    for day in range(1, 8):
                        # Gradual improvement implementation
                        daily_improvement = base_improvement * (day / 7) * random.uniform(0.8, 1.2)
                        daily_forecast.append({
                            "day": day,
                            "predicted_improvement": round(daily_improvement, 1),
                            "uncertainty": round(daily_improvement * 0.2, 1)
                        })
                    
                    performance_forecast[kpi_name] = daily_forecast
                    
                    # Confidence intervals
                    confidence_intervals[kpi_name] = {
                        "lower_bound": round(predicted_improvement * 0.7, 1),
                        "upper_bound": round(predicted_improvement * 1.3, 1),
                        "confidence_level": "80%"
                    }
        
        # Scenario analysis
        scenario_analysis = {
            "best_case": {
                "description": "All parameters perform at upper confidence interval",
                "overall_improvement": "15-25%",
                "probability": "20%"
            },
            "expected_case": {
                "description": "Parameters perform as predicted",
                "overall_improvement": "8-15%",
                "probability": "60%"
            },
            "worst_case": {
                "description": "Parameters perform at lower confidence interval",
                "overall_improvement": "3-8%",
                "probability": "20%"
            }
        }
        
        return {
            "kpi_predictions": kpi_predictions,
            "performance_forecast": performance_forecast,
            "confidence_intervals": confidence_intervals,
            "scenario_analysis": scenario_analysis,
            "simulation_timestamp": datetime.now().isoformat()
        }
    
    def _generate_configuration_recommendations_summary(self, configuration_recommendations: Dict, 
                                                      risk_assessment: Dict) -> List[Dict[str, str]]:
        """Generate summary recommendations for configuration implementation"""
        recommendations = []
        
        parameter_count = len(configuration_recommendations.get("parameter_changes", {}))
        risk_level = risk_assessment.get("overall_risk_level", "medium")
        
        # Implementation approach recommendation
        if risk_level == "high":
            recommendations.append({
                "type": "implementation_approach",
                "priority": "critical",
                "title": "Implement High-Risk Changes with Enhanced Precautions",
                "description": f"High-risk configuration changes detected ({parameter_count} parameters)",
                "action": "Use phased implementation with pilot testing and real-time monitoring"
            })
        elif parameter_count > 5:
            recommendations.append({
                "type": "implementation_approach", 
                "priority": "high",
                "title": "Use Phased Implementation for Multiple Parameter Changes",
                "description": f"Large number of parameter changes ({parameter_count}) requires careful coordination",
                "action": "Implement in phases with validation checkpoints between each phase"
            })
        
        # Monitoring recommendation
        recommendations.append({
            "type": "monitoring_enhancement",
            "priority": "high",
            "title": "Deploy Enhanced Monitoring During Implementation",
            "description": "Critical KPIs require continuous monitoring during configuration changes",
            "action": "Activate 1-minute granularity monitoring for 24 hours post-implementation"
        })
        
        # Timing recommendation
        recommendations.append({
            "type": "implementation_timing",
            "priority": "medium",
            "title": "Schedule Implementation During Maintenance Window",
            "description": "Minimize user impact by implementing during low-traffic periods",
            "action": "Execute changes during next scheduled maintenance window (typically 2-6 AM)"
        })
        
        # Rollback preparation
        if risk_level in ["medium", "high"]:
            recommendations.append({
                "type": "rollback_preparation",
                "priority": "critical",
                "title": "Prepare Automated Rollback Procedures",
                "description": f"Risk level ({risk_level}) requires comprehensive rollback preparation",
                "action": "Test rollback procedures and ensure automated triggers are configured"
            })
        
        return recommendations
    
    async def _handle_configuration_failure(self, error_msg: str, context: Dict) -> Dict[str, Any]:
        """Handle configuration failure with graceful degradation"""
        return {
            "status": "partial_success",
            "agent_name": "Configuration",
            "error": error_msg,
            "fallback_mode": "manual_configuration_required",
            "configuration_summary": {
                "generation_duration_seconds": 0,
                "parameters_optimized": 0,
                "sites_affected": 0,
                "risk_level": "unknown"
            },
            "recommendations": [
                {
                    "type": "system_recovery",
                    "priority": "critical",
                    "title": "Restore Configuration Generation Capabilities", 
                    "description": f"Configuration generation failed: {error_msg}",
                    "action": "Check configuration database and parameter definition system"
                },
                {
                    "type": "manual_fallback",
                    "priority": "high",
                    "title": "Proceed with Manual Configuration Planning",
                    "description": "Use manual processes for configuration optimization",
                    "action": "Engage RF optimization experts for manual parameter analysis"
                }
            ],
            "execution_time": 0
        }