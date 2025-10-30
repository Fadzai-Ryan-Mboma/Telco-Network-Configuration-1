#!/usr/bin/env python3
"""
Enhanced Human Approval Workflow System
Realistic approval interface with safety assessments and decision tracking
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class ApprovalStatus(Enum):
    """Approval status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    CONDITIONAL_APPROVED = "conditional_approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    EXPIRED = "expired"

class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ApprovalRequest:
    """Approval request structure"""
    request_id: str
    workflow_id: str
    requester: str
    request_type: str
    change_description: str
    business_justification: str
    risk_assessment: Dict[str, Any]
    proposed_changes: Dict[str, Any]
    expected_benefits: List[str]
    rollback_plan: Dict[str, Any]
    monitoring_plan: Dict[str, Any]
    urgency_level: str
    estimated_impact: Dict[str, Any]
    compliance_checks: Dict[str, Any]
    created_at: datetime
    expires_at: datetime
    approval_level_required: str
    conditions: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.conditions is None:
            self.conditions = []

@dataclass
class ApprovalDecision:
    """Approval decision structure"""
    decision_id: str
    request_id: str
    approver: str
    decision: ApprovalStatus
    decision_rationale: str
    conditions_added: List[str]
    safety_concerns: List[str]
    monitoring_requirements: List[str]
    escalation_required: bool
    decision_timestamp: datetime
    valid_until: Optional[datetime]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class ApprovalWorkflowEngine:
    """Enhanced approval workflow with realistic decision tracking"""
    
    def __init__(self):
        self.pending_requests = {}
        self.decision_history = {}
        self.approval_policies = self._initialize_approval_policies()
        self.current_approvers = {
            "network_engineer": "John Mwanza (Senior Network Engineer)",
            "operations_manager": "Sarah Chikuni (Operations Manager)", 
            "safety_officer": "David Nyambi (Safety & Compliance Officer)"
        }
    
    def _initialize_approval_policies(self) -> Dict[str, Any]:
        """Initialize approval policies and criteria"""
        return {
            "risk_thresholds": {
                RiskLevel.LOW: {
                    "approval_level": "network_engineer",
                    "max_parameter_change": 0.3,  # 30% change limit
                    "auto_approve_conditions": ["standard_optimization", "routine_maintenance"],
                    "monitoring_duration": 30  # minutes
                },
                RiskLevel.MEDIUM: {
                    "approval_level": "operations_manager",
                    "max_parameter_change": 0.5,  # 50% change limit
                    "required_conditions": ["enhanced_monitoring", "staged_rollout"],
                    "monitoring_duration": 60  # minutes
                },
                RiskLevel.HIGH: {
                    "approval_level": "operations_manager",
                    "max_parameter_change": 0.8,  # 80% change limit
                    "required_conditions": ["crisis_justification", "enhanced_monitoring", "immediate_rollback_ready"],
                    "monitoring_duration": 120,  # minutes
                    "requires_safety_review": True
                },
                RiskLevel.CRITICAL: {
                    "approval_level": "safety_officer",
                    "max_parameter_change": 1.0,  # 100% change limit
                    "required_conditions": ["emergency_authorization", "continuous_monitoring", "dedicated_support"],
                    "monitoring_duration": 240,  # minutes
                    "requires_safety_review": True,
                    "requires_escalation": True
                }
            },
            "change_types": {
                "parameter_optimization": {
                    "base_risk": RiskLevel.LOW,
                    "risk_multipliers": {
                        "rach_parameters": 1.5,  # RACH changes are higher risk
                        "power_parameters": 1.3,
                        "timing_parameters": 1.2,
                        "handover_parameters": 1.1
                    }
                },
                "emergency_optimization": {
                    "base_risk": RiskLevel.HIGH,
                    "urgency_override": True,
                    "requires_business_justification": True
                },
                "configuration_rollback": {
                    "base_risk": RiskLevel.LOW,
                    "fast_track": True
                }
            },
            "network_conditions": {
                "crisis_network": {
                    "risk_tolerance_increase": 1,  # Accept one level higher risk
                    "approval_acceleration": True,
                    "monitoring_enhancement": True
                },
                "normal_operations": {
                    "risk_tolerance_increase": 0,
                    "standard_approval_flow": True
                }
            }
        }
    
    def create_approval_request(self, workflow_context: Dict[str, Any], 
                              configuration_results: Dict[str, Any],
                              validation_results: Dict[str, Any]) -> ApprovalRequest:
        """Create comprehensive approval request"""
        
        request_id = str(uuid.uuid4())[:8]
        
        # Extract key information
        proposed_changes = configuration_results.get('mml_commands', [])
        risk_analysis = validation_results.get('safety_analysis', {})
        business_case = validation_results.get('approval_request', {})
        
        # Assess risk level
        risk_level = self._assess_risk_level(configuration_results, validation_results)
        
        # Determine approval level required
        approval_level = self._determine_approval_level(risk_level, workflow_context)
        
        # Generate monitoring plan
        monitoring_plan = self._generate_monitoring_plan(risk_level, proposed_changes)
        
        # Create rollback plan
        rollback_plan = self._create_rollback_plan(configuration_results)
        
        request = ApprovalRequest(
            request_id=request_id,
            workflow_id=workflow_context.get('workflow_id', 'unknown'),
            requester="LZ AI Optimization System",
            request_type="emergency_network_optimization",
            change_description=business_case.get('change_description', 'Network parameter optimization'),
            business_justification=business_case.get('business_justification', 'Critical network performance issues'),
            risk_assessment={
                "overall_risk": risk_level.value,
                "risk_factors": risk_analysis.get('risk_factors', []),
                "mitigation_measures": self._get_mitigation_measures(risk_level),
                "impact_assessment": risk_analysis.get('impact_assessment', {})
            },
            proposed_changes={
                "mml_commands": proposed_changes,
                "parameter_count": len(proposed_changes),
                "sites_affected": configuration_results.get('change_summary', {}).get('total_sites', 0),
                "cells_affected": configuration_results.get('change_summary', {}).get('total_cells', 0)
            },
            expected_benefits=business_case.get('expected_benefits', []),
            rollback_plan=rollback_plan,
            monitoring_plan=monitoring_plan,
            urgency_level="critical",
            estimated_impact={
                "service_disruption_risk": risk_analysis.get('impact_assessment', {}).get('service_disruption_risk', 'minimal'),
                "customer_impact": risk_analysis.get('impact_assessment', {}).get('customer_impact', 'positive'),
                "rollback_complexity": risk_analysis.get('impact_assessment', {}).get('rollback_complexity', 'simple')
            },
            compliance_checks=validation_results.get('compliance_check', {}),
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=2),  # 2-hour approval window
            approval_level_required=approval_level,
            conditions=self._get_required_conditions(risk_level)
        )
        
        self.pending_requests[request_id] = request
        return request
    
    def _assess_risk_level(self, config_results: Dict[str, Any], validation_results: Dict[str, Any]) -> RiskLevel:
        """Assess overall risk level for the proposed changes"""
        
        # Base risk from validation
        validation_risk = validation_results.get('validation_summary', {}).get('risk_level', 'medium')
        
        # Adjust risk based on network condition
        network_condition = "crisis_network"  # Bindura is in crisis
        
        # Adjust risk based on change magnitude
        change_summary = config_results.get('change_summary', {})
        parameter_count = change_summary.get('parameters_modified', 0)
        
        # Risk calculation logic
        if validation_risk == "low" and parameter_count <= 2 and network_condition == "normal_operations":
            return RiskLevel.LOW
        elif validation_risk == "low" and network_condition == "crisis_network":
            return RiskLevel.MEDIUM  # Crisis network increases risk
        elif validation_risk == "medium" or parameter_count > 3:
            return RiskLevel.HIGH
        elif validation_risk == "high" or network_condition == "crisis_network":
            return RiskLevel.HIGH  # Crisis justifies higher risk tolerance
        else:
            return RiskLevel.MEDIUM
    
    def _determine_approval_level(self, risk_level: RiskLevel, workflow_context: Dict[str, Any]) -> str:
        """Determine required approval level"""
        
        policies = self.approval_policies["risk_thresholds"][risk_level]
        base_level = policies["approval_level"]
        
        # Check for escalation requirements
        if policies.get("requires_escalation", False):
            return "safety_officer"
        elif policies.get("requires_safety_review", False):
            return "operations_manager"
        else:
            return base_level
    
    def _generate_monitoring_plan(self, risk_level: RiskLevel, proposed_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive monitoring plan"""
        
        policies = self.approval_policies["risk_thresholds"][risk_level]
        
        return {
            "monitoring_duration_minutes": policies["monitoring_duration"],
            "monitoring_frequency": "1_minute" if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] else "5_minutes",
            "kpis_to_monitor": [
                "rach_setup_success_rate",
                "dl_ibler",
                "ul_ibler",
                "service_availability",
                "call_setup_success_rate"
            ],
            "alert_thresholds": {
                "rach_degradation": "0.5%",  # Immediate alert if RACH drops below current crisis level
                "ibler_increase": "20%",     # Alert if IBLER increases beyond 20%
                "service_outage": "any"      # Immediate alert for any service disruption
            },
            "rollback_triggers": {
                "automatic": ["service_outage", "rach_below_baseline"],
                "manual": ["performance_degradation", "customer_complaints"]
            },
            "escalation_contacts": [
                "Network Operations Center",
                "Emergency Response Team",
                "Senior Technical Management"
            ],
            "monitoring_tools": ["Real-time KPI dashboard", "Automated alerting", "Customer impact monitoring"]
        }
    
    def _create_rollback_plan(self, config_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive rollback plan"""
        
        rollback_commands = config_results.get('rollback_commands', [])
        
        return {
            "rollback_commands": rollback_commands,
            "rollback_execution_time": "5_minutes",
            "rollback_triggers": [
                "Service outage detection",
                "KPI degradation beyond thresholds",
                "Manual operator intervention",
                "System health alert"
            ],
            "rollback_procedure": [
                "Immediate execution of rollback MML commands",
                "Verification of parameter restoration",
                "KPI monitoring for stability confirmation",
                "Incident documentation and analysis"
            ],
            "rollback_validation": {
                "parameter_verification": True,
                "kpi_stability_check": True,
                "service_restoration_confirmation": True
            },
            "post_rollback_actions": [
                "Root cause analysis",
                "Alternative optimization strategy development",
                "Approval for revised approach"
            ]
        }
    
    def _get_mitigation_measures(self, risk_level: RiskLevel) -> List[str]:
        """Get risk mitigation measures"""
        
        base_measures = [
            "Real-time monitoring during implementation",
            "Immediate rollback capability",
            "Step-by-step execution with validation"
        ]
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            base_measures.extend([
                "Enhanced monitoring with 1-minute intervals",
                "Dedicated technical support during execution",
                "Emergency response team on standby",
                "Customer communication plan activated"
            ])
        
        if risk_level == RiskLevel.CRITICAL:
            base_measures.extend([
                "Senior management notification",
                "Continuous video conference during execution",
                "Multiple rollback scenario preparation"
            ])
        
        return base_measures
    
    def _get_required_conditions(self, risk_level: RiskLevel) -> List[str]:
        """Get required conditions for approval"""
        
        policies = self.approval_policies["risk_thresholds"][risk_level]
        conditions = policies.get("required_conditions", [])
        
        # Add crisis-specific conditions
        conditions.extend([
            "Network crisis justification documented",
            "Alternative low-risk solutions evaluated",
            "Business impact assessment completed"
        ])
        
        return conditions
    
    def process_approval_decision(self, request_id: str, decision: ApprovalStatus,
                                approver: str, rationale: str,
                                additional_conditions: List[str] = None,
                                safety_concerns: List[str] = None) -> ApprovalDecision:
        """Process human approval decision"""
        
        if request_id not in self.pending_requests:
            raise ValueError(f"Approval request {request_id} not found")
        
        request = self.pending_requests[request_id]
        
        if additional_conditions is None:
            additional_conditions = []
        if safety_concerns is None:
            safety_concerns = []
        
        # Determine monitoring requirements based on decision
        monitoring_requirements = []
        if decision in [ApprovalStatus.APPROVED, ApprovalStatus.CONDITIONAL_APPROVED]:
            monitoring_requirements = [
                "Real-time KPI monitoring",
                "Immediate rollback readiness",
                "Progress reporting every 10 minutes"
            ]
            
            if decision == ApprovalStatus.CONDITIONAL_APPROVED:
                monitoring_requirements.extend([
                    "Enhanced safety monitoring",
                    "Additional validation checkpoints",
                    "Escalation on any deviation"
                ])
        
        # Check for escalation requirements
        escalation_required = False
        if decision == ApprovalStatus.REJECTED and request.urgency_level == "critical":
            escalation_required = True
        elif safety_concerns:
            escalation_required = True
        
        # Create decision record
        approval_decision = ApprovalDecision(
            decision_id=str(uuid.uuid4())[:8],
            request_id=request_id,
            approver=approver,
            decision=decision,
            decision_rationale=rationale,
            conditions_added=additional_conditions,
            safety_concerns=safety_concerns,
            monitoring_requirements=monitoring_requirements,
            escalation_required=escalation_required,
            decision_timestamp=datetime.now(),
            valid_until=datetime.now() + timedelta(hours=4) if decision in [ApprovalStatus.APPROVED, ApprovalStatus.CONDITIONAL_APPROVED] else None,
            metadata={
                "approval_level": request.approval_level_required,
                "risk_level": request.risk_assessment["overall_risk"],
                "urgency": request.urgency_level,
                "workflow_id": request.workflow_id
            }
        )
        
        # Store decision
        self.decision_history[request_id] = approval_decision
        
        # Remove from pending if decided
        if decision != ApprovalStatus.PENDING:
            del self.pending_requests[request_id]
        
        return approval_decision
    
    def get_approval_interface_data(self, request_id: str) -> Dict[str, Any]:
        """Get formatted data for approval interface"""
        
        if request_id not in self.pending_requests:
            return {"error": "Request not found"}
        
        request = self.pending_requests[request_id]
        
        return {
            "request_summary": {
                "request_id": request.request_id,
                "workflow_id": request.workflow_id,
                "created_at": request.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "expires_at": request.expires_at.strftime("%Y-%m-%d %H:%M:%S"),
                "time_remaining": str(request.expires_at - datetime.now()),
                "urgency": request.urgency_level,
                "approver_required": self.current_approvers.get(request.approval_level_required, "Unknown")
            },
            "change_details": {
                "description": request.change_description,
                "justification": request.business_justification,
                "sites_affected": request.proposed_changes["sites_affected"],
                "parameters_changed": request.proposed_changes["parameter_count"],
                "expected_benefits": request.expected_benefits
            },
            "risk_assessment": {
                "overall_risk": request.risk_assessment["overall_risk"],
                "risk_factors": request.risk_assessment["risk_factors"],
                "mitigation_measures": request.risk_assessment["mitigation_measures"],
                "service_disruption_risk": request.estimated_impact["service_disruption_risk"],
                "customer_impact": request.estimated_impact["customer_impact"]
            },
            "safety_information": {
                "rollback_plan": request.rollback_plan,
                "monitoring_plan": request.monitoring_plan,
                "compliance_status": request.compliance_checks,
                "required_conditions": request.conditions
            },
            "approval_options": {
                "approve": {
                    "label": "✅ APPROVE",
                    "description": "Approve changes as proposed",
                    "consequences": "Changes will be executed immediately with standard monitoring"
                },
                "conditional_approve": {
                    "label": "⚠️ CONDITIONAL APPROVE", 
                    "description": "Approve with additional conditions",
                    "consequences": "Changes executed with enhanced monitoring and additional safety measures"
                },
                "reject": {
                    "label": "❌ REJECT",
                    "description": "Reject proposed changes",
                    "consequences": "Changes will not be executed. Alternative solutions required."
                }
            },
            "technical_details": {
                "proposed_commands": request.proposed_changes.get("mml_commands", []),
                "rollback_commands": request.rollback_plan.get("rollback_commands", []),
                "monitoring_kpis": request.monitoring_plan.get("kpis_to_monitor", [])
            }
        }
    
    def get_approval_status(self, request_id: str) -> Dict[str, Any]:
        """Get current approval status"""
        
        if request_id in self.pending_requests:
            request = self.pending_requests[request_id]
            return {
                "status": "pending",
                "created_at": request.created_at.isoformat(),
                "expires_at": request.expires_at.isoformat(),
                "approval_level_required": request.approval_level_required,
                "time_remaining_minutes": (request.expires_at - datetime.now()).total_seconds() / 60
            }
        
        elif request_id in self.decision_history:
            decision = self.decision_history[request_id]
            return {
                "status": decision.decision.value,
                "decision_timestamp": decision.decision_timestamp.isoformat(),
                "approver": decision.approver,
                "decision_rationale": decision.decision_rationale,
                "conditions_added": decision.conditions_added,
                "escalation_required": decision.escalation_required,
                "valid_until": decision.valid_until.isoformat() if decision.valid_until else None
            }
        
        else:
            return {"status": "not_found"}
    
    def simulate_human_approval(self, request_id: str, scenario: str = "normal") -> ApprovalDecision:
        """Simulate realistic human approval decision for demo purposes"""
        
        if request_id not in self.pending_requests:
            raise ValueError(f"Request {request_id} not found")
        
        request = self.pending_requests[request_id]
        
        # Simulate different approval scenarios
        if scenario == "immediate_approve":
            decision = ApprovalStatus.APPROVED
            rationale = "Critical network situation requires immediate action. All safety checks passed."
            additional_conditions = []
            safety_concerns = []
            
        elif scenario == "conditional_approve":
            decision = ApprovalStatus.CONDITIONAL_APPROVED
            rationale = "Approved with enhanced monitoring due to network crisis. Proceeding with caution."
            additional_conditions = [
                "Continuous monitoring during execution",
                "Immediate rollback on any service degradation",
                "Progress updates every 5 minutes"
            ]
            safety_concerns = []
            
        elif scenario == "safety_concerns":
            decision = ApprovalStatus.CONDITIONAL_APPROVED
            rationale = "Approved but with safety concerns noted. Enhanced monitoring required."
            additional_conditions = [
                "Dedicated safety officer monitoring",
                "Enhanced rollback procedures ready",
                "Customer impact assessment during execution"
            ]
            safety_concerns = [
                "Aggressive parameter changes in crisis network",
                "Limited testing window for optimization",
                "Potential for cascade effects"
            ]
            
        elif scenario == "reject":
            decision = ApprovalStatus.REJECTED
            rationale = "Proposed changes too risky for current network state. Alternative approach needed."
            additional_conditions = []
            safety_concerns = [
                "Parameter changes too aggressive",
                "Insufficient safety validation",
                "Risk of further network degradation"
            ]
            
        else:  # normal scenario
            decision = ApprovalStatus.APPROVED
            rationale = "Network crisis justifies the proposed optimization. Safety measures adequate."
            additional_conditions = ["Standard enhanced monitoring for crisis optimization"]
            safety_concerns = []
        
        # Process the simulated decision
        approver = self.current_approvers.get(request.approval_level_required, "System Simulator")
        
        return self.process_approval_decision(
            request_id=request_id,
            decision=decision,
            approver=approver,
            rationale=rationale,
            additional_conditions=additional_conditions,
            safety_concerns=safety_concerns
        )