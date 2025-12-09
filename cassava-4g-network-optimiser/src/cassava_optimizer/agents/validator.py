"""
Validator Agent - Pre-execution validation stage.

Responsible for validating recommendations before they are applied,
including safety checks, conflict detection, and approval workflows.
"""

from typing import Any

import structlog

from cassava_optimizer.agents.base import AgentContext, AgentExecutionError, BaseAgent
from cassava_optimizer.domain.enums import AgentType, RiskLevel
from cassava_optimizer.domain.mml_commands import ALL_TEMPLATES, validate_command_safety, validate_command_syntax

logger = structlog.get_logger(__name__)


class ValidatorAgent(BaseAgent):
    """
    Agent responsible for validating recommendations before execution.
    
    Validation includes:
    - Parameter value range checking
    - MML command syntax validation
    - Conflict detection between recommendations
    - Risk threshold enforcement
    - Human approval workflow (if required)
    
    Fail-fast: Rejects unsafe recommendations.
    """
    
    # Maximum allowed risk for auto-approval
    MAX_AUTO_APPROVE_RISK = RiskLevel.MEDIUM
    
    # Parameter safety bounds
    PARAMETER_BOUNDS = {
        "tx_power": {"min": 10, "max": 60, "unit": "dBm"},
        "electrical_tilt": {"min": 0, "max": 15, "unit": "degrees"},
        "handover_threshold": {"min": -120, "max": -70, "unit": "dBm"},
        "ho_margin": {"min": 0, "max": 10, "unit": "dB"},
        "qrxlevmin": {"min": -140, "max": -44, "unit": "dBm"},
        "a3_offset": {"min": -6, "max": 6, "unit": "dB"},
        "a3_time_to_trigger": {"min": 40, "max": 5120, "unit": "ms"},
        "a2_threshold": {"min": -140, "max": -44, "unit": "dBm"},
        "cio": {"min": -24, "max": 24, "unit": "dB"},
        "target_bler": {"min": 0.01, "max": 0.3, "unit": "ratio"},
    }
    
    def __init__(self) -> None:
        """Initialize the validator agent."""
        super().__init__()
    
    @property
    def agent_type(self) -> AgentType:
        return AgentType.VALIDATOR
    
    async def _validate_preconditions(self, context: AgentContext) -> None:
        """Validate that recommendations exist to validate."""
        await super()._validate_preconditions(context)
        
        if not context.recommendations:
            self._log.info("No recommendations to validate")
    
    async def _execute(self, context: AgentContext) -> dict[str, Any]:
        """
        Validate all recommendations before execution.
        
        Returns:
            Dictionary containing:
            - validated_recommendations: Recommendations that passed validation
            - rejected_recommendations: Recommendations that failed validation
            - requires_approval: Whether human approval is needed
            - validation_summary: Summary of validation results
        """
        recommendations = context.recommendations
        
        self._log.info(
            "Starting validation",
            site_id=context.site_id,
            recommendation_count=len(recommendations),
        )
        
        if not recommendations:
            return {
                "validated_recommendations": [],
                "rejected_recommendations": [],
                "requires_approval": False,
                "validation_summary": "No recommendations to validate",
            }
        
        validated = []
        rejected = []
        requires_approval = False
        
        for rec in recommendations:
            validation_result = self._validate_recommendation(rec)
            
            if validation_result["valid"]:
                # Check if it needs approval
                risk = RiskLevel(rec.get("risk_level", "medium"))
                if risk.value == "high" and not context.auto_approve:
                    requires_approval = True
                    rec["requires_approval"] = True
                else:
                    rec["requires_approval"] = False
                
                rec["validation_notes"] = validation_result.get("notes", [])
                validated.append(rec)
            else:
                rec["rejection_reasons"] = validation_result["reasons"]
                rejected.append(rec)
        
        # Check for conflicts between validated recommendations
        conflict_check = self._check_conflicts(validated)
        if conflict_check["has_conflicts"]:
            # Remove conflicting lower-priority recommendations
            validated = self._resolve_conflicts(validated, conflict_check["conflicts"])
        
        # Update context with validated recommendations
        context.recommendations = validated
        
        summary = self._generate_validation_summary(validated, rejected, requires_approval)
        
        output = {
            "validated_recommendations": validated,
            "rejected_recommendations": rejected,
            "requires_approval": requires_approval,
            "validation_summary": summary,
            "conflict_resolution": conflict_check,
        }
        
        self._log.info(
            "Validation complete",
            validated=len(validated),
            rejected=len(rejected),
            requires_approval=requires_approval,
        )
        
        return output
    
    def _validate_recommendation(
        self,
        rec: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Validate a single recommendation.
        
        Returns:
            Validation result with valid flag and reasons/notes
        """
        reasons = []
        notes = []
        
        # 1. Validate parameter values
        for param in rec.get("parameters", []):
            param_result = self._validate_parameter(param)
            if not param_result["valid"]:
                reasons.append(param_result["reason"])
            elif param_result.get("note"):
                notes.append(param_result["note"])
        
        # 2. Validate MML commands
        for cmd in rec.get("mml_commands", []):
            cmd_result = self._validate_mml_command(cmd)
            if not cmd_result["valid"]:
                reasons.append(cmd_result["reason"])
        
        # 3. Validate risk level is acceptable
        risk = rec.get("risk_level", "medium")
        if risk == "high":
            notes.append("High-risk change - manual review recommended")
        
        return {
            "valid": len(reasons) == 0,
            "reasons": reasons,
            "notes": notes,
        }
    
    def _validate_parameter(
        self,
        param: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate a parameter change is within safe bounds."""
        name = param.get("name", "")
        recommended = param.get("recommended")
        
        if recommended is None:
            return {
                "valid": False,
                "reason": f"Parameter {name} has no recommended value",
            }
        
        bounds = self.PARAMETER_BOUNDS.get(name)
        if not bounds:
            # Unknown parameter - allow but note it
            return {
                "valid": True,
                "note": f"Parameter {name} has no defined bounds - verify manually",
            }
        
        try:
            value = float(recommended)
        except (ValueError, TypeError):
            return {
                "valid": False,
                "reason": f"Parameter {name} value '{recommended}' is not numeric",
            }
        
        min_val = bounds.get("min")
        max_val = bounds.get("max")
        unit = bounds.get("unit", "")
        
        if min_val is not None and value < min_val:
            return {
                "valid": False,
                "reason": f"Parameter {name}={value}{unit} is below minimum {min_val}{unit}",
            }
        
        if max_val is not None and value > max_val:
            return {
                "valid": False,
                "reason": f"Parameter {name}={value}{unit} exceeds maximum {max_val}{unit}",
            }
        
        return {"valid": True}
    
    def _validate_mml_command(
        self,
        command: str,
    ) -> dict[str, Any]:
        """Validate MML command syntax."""
        if not command:
            return {"valid": False, "reason": "Empty MML command"}
        
        # Basic syntax checks
        command = command.strip()
        
        # Must end with semicolon
        if not command.endswith(";"):
            return {
                "valid": False,
                "reason": f"MML command must end with semicolon: {command[:50]}...",
            }
        
        # Must start with valid command type
        valid_prefixes = ["MOD", "SET", "ADD", "DEL", "DSP", "LST", "ACT", "DEA", "BLK", "UBL"]
        if not any(command.upper().startswith(p) for p in valid_prefixes):
            return {
                "valid": False,
                "reason": f"Unknown MML command type: {command[:20]}...",
            }
        
        # Check for dangerous commands
        dangerous_patterns = ["DELETE", "REMOVE", "RESET", "FORMAT"]
        if any(p in command.upper() for p in dangerous_patterns):
            return {
                "valid": False,
                "reason": f"Potentially dangerous command blocked: {command[:30]}...",
            }
        
        return {"valid": True}
    
    def _check_conflicts(
        self,
        recommendations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Check for conflicts between recommendations."""
        conflicts = []
        
        # Track parameters being modified
        param_changes: dict[str, list[dict[str, Any]]] = {}
        
        for i, rec in enumerate(recommendations):
            for param in rec.get("parameters", []):
                param_name = param.get("name", "")
                
                if param_name in param_changes:
                    # Conflict detected - same parameter modified by multiple recs
                    existing = param_changes[param_name]
                    conflicts.append({
                        "parameter": param_name,
                        "recommendations": [existing[0]["rec_index"], i],
                        "values": [
                            existing[0]["value"],
                            param.get("recommended"),
                        ],
                    })
                else:
                    param_changes[param_name] = [{
                        "rec_index": i,
                        "value": param.get("recommended"),
                        "priority": rec.get("priority", 5),
                    }]
        
        return {
            "has_conflicts": len(conflicts) > 0,
            "conflicts": conflicts,
        }
    
    def _resolve_conflicts(
        self,
        recommendations: list[dict[str, Any]],
        conflicts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Resolve conflicts by keeping higher priority recommendations."""
        # Find indices of recommendations to remove
        to_remove = set()
        
        for conflict in conflicts:
            indices = conflict.get("recommendations", [])
            if len(indices) >= 2:
                # Compare priorities - lower number = higher priority
                priorities = [
                    recommendations[i].get("priority", 5) for i in indices
                ]
                
                # Remove lower priority (higher number)
                if priorities[0] > priorities[1]:
                    to_remove.add(indices[0])
                else:
                    to_remove.add(indices[1])
        
        # Filter out removed recommendations
        resolved = [
            rec for i, rec in enumerate(recommendations)
            if i not in to_remove
        ]
        
        self._log.info(
            "Conflicts resolved",
            removed_count=len(to_remove),
            remaining=len(resolved),
        )
        
        return resolved
    
    def _generate_validation_summary(
        self,
        validated: list[dict[str, Any]],
        rejected: list[dict[str, Any]],
        requires_approval: bool,
    ) -> str:
        """Generate human-readable validation summary."""
        parts = []
        
        total = len(validated) + len(rejected)
        parts.append(f"Validated {len(validated)} of {total} recommendations.")
        
        if rejected:
            parts.append(f"Rejected {len(rejected)} due to safety constraints.")
        
        if requires_approval:
            parts.append("Human approval required for high-risk changes.")
        elif validated:
            parts.append("All changes within auto-approval thresholds.")
        
        return " ".join(parts)
