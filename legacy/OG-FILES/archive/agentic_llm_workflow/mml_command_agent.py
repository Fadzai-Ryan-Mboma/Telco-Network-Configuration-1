"""
MML Command Agent for Liquid Zimbabwe
Specialized agent for executing MML commands and parameter management

This agent handles:
- Safe MML command execution on Huawei equipment
- Parameter validation and safety checks
- Command syntax verification
- Rollback capabilities
- Impact assessment before execution
"""

import os
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from liquid_zimbabwe_parameters import LiquidZimbabweParameterManager as LiquidZimbabweParameters
from huawei_api_client import HuaweiAPIClient
from agents import init_agent

class MMLCommandAgent:
    """
    Specialized agent for safe MML command execution and parameter management.
    Provides command validation and execution support to the main 3 agents.
    """
    
    def __init__(self):
        # Initialize with database path
        db_path = os.path.join("data", "liquid_zimbabwe.db")
        os.makedirs("data", exist_ok=True)
        self.parameter_manager = LiquidZimbabweParameters(db_path)
        self.api_client = HuaweiAPIClient(
            base_url="https://41.174.191.214:31127",
            username="cassava.ai",
            password="#Pass123#"
        )
        self.llm_agent = None
        self.command_history = []
        self.safety_checks_enabled = True
        self.max_impact_score = 7  # Maximum allowed impact score (1-10 scale)
        
        # MML Command templates for the 5 priority parameters
        self.mml_templates = {
            "P0_NominalPUSCH": {
                "modify": "MOD CELLALGOSWITCH: CellId={cell_id}, P0NominalPusch={value};",
                "display": "DSP CELLALGOSWITCH: CellId={cell_id};",
                "validation_range": (-126, -30),  # dBm
                "impact_score": 8,  # High impact on uplink power control
                "safety_checks": ["validate_power_range", "check_interference_risk"]
            },
            "ReferenceSignalPower_PDSCH": {
                "modify": "MOD PDSCHCFG: CellId={cell_id}, ReferenceSignalPower={value};",
                "display": "DSP PDSCHCFG: CellId={cell_id};",
                "validation_range": (-60, 50),  # dBm
                "impact_score": 9,  # Very high impact on downlink coverage
                "safety_checks": ["validate_power_range", "check_coverage_impact"]
            },
            "ReferenceSignalPower_PUSCH": {
                "modify": "MOD PUSCHCFG: CellId={cell_id}, ReferenceSignalPower={value};",
                "display": "DSP PUSCHCFG: CellId={cell_id};",
                "validation_range": (-60, 50),  # dBm
                "impact_score": 8,  # High impact on uplink performance
                "safety_checks": ["validate_power_range", "check_uplink_impact"]
            },
            "A3EventOffset": {
                "modify": "MOD MEASCONFIG: CellId={cell_id}, A3EventOffset={value};",
                "display": "DSP MEASCONFIG: CellId={cell_id};",
                "validation_range": (-30, 30),  # dB
                "impact_score": 6,  # Medium-high impact on handover
                "safety_checks": ["validate_offset_range", "check_handover_impact"]
            },
            "T310Timer": {
                "modify": "MOD RADIOBEARERCFG: CellId={cell_id}, T310Timer={value};",
                "display": "DSP RADIOBEARERCFG: CellId={cell_id};",
                "validation_range": (0, 6000),  # ms
                "impact_score": 5,  # Medium impact on connection stability
                "safety_checks": ["validate_timer_range", "check_stability_impact"]
            },
            "PDCCHAggregationLevel": {
                "modify": "MOD PDCCHCFG: CellId={cell_id}, AggregationLevel={value};",
                "display": "DSP PDCCHCFG: CellId={cell_id};",
                "validation_range": (1, 8),  # Aggregation level
                "impact_score": 4,  # Medium impact on resource efficiency
                "safety_checks": ["validate_aggregation_range", "check_resource_impact"]
            }
        }
        
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the LLM agent with MML command tools"""
        llm = init_agent()
        system_prompt = """You are the MML Command Agent for Liquid Zimbabwe's RAN optimization system.
        You specialize in safely executing MML commands on Huawei equipment and managing the 5 priority parameters.
        Your primary responsibility is ensuring command safety and preventing network disruptions.
        Always perform safety checks before executing commands and provide clear explanations of actions taken.
        Focus on parameter optimization while maintaining network stability."""
        
        tools = [
            self._validate_mml_command_tool,
            self._execute_mml_command_tool,
            self._display_current_parameters_tool,
            self._assess_parameter_impact_tool,
            self._generate_safe_mml_commands_tool,
            self._check_command_syntax_tool,
            self._create_parameter_rollback_tool,
            self._batch_parameter_update_tool
        ]
        
        self.llm_agent = create_react_agent(llm, tools=tools, prompt=system_prompt)
    
    @tool
    def _validate_mml_command_tool(self, command: str, cell_id: Optional[str] = None) -> str:
        """Validate MML command syntax and safety"""
        try:
            validation_results = []
            validation_results.append("🔍 MML COMMAND VALIDATION")
            validation_results.append("=" * 30)
            validation_results.append(f"Command: {command}")
            validation_results.append("")
            
            # Basic syntax validation
            if not command.strip().endswith(';'):
                validation_results.append("❌ SYNTAX ERROR: Command must end with semicolon (;)")
                return "\n".join(validation_results)
            
            # Extract command type and parameters
            command_upper = command.upper().strip()
            
            if command_upper.startswith('MOD '):
                command_type = "MODIFY"
                validation_results.append("🔧 Command Type: PARAMETER MODIFICATION")
            elif command_upper.startswith('DSP '):
                command_type = "DISPLAY"
                validation_results.append("👁️ Command Type: PARAMETER DISPLAY")
            elif command_upper.startswith('ADD '):
                command_type = "ADD"
                validation_results.append("➕ Command Type: CONFIGURATION ADD")
            elif command_upper.startswith('RMV '):
                command_type = "REMOVE"
                validation_results.append("➖ Command Type: CONFIGURATION REMOVE")
            else:
                validation_results.append("❓ Command Type: UNRECOGNIZED")
                validation_results.append("⚠️ WARNING: Command type not in standard MML format")
            
            # Check for recognized parameter patterns
            recognized_params = []
            impact_score = 0
            
            for param_name, config in self.mml_templates.items():
                if any(keyword in command_upper for keyword in [param_name.upper(), config["modify"].split(':')[0].split()[-1]]):
                    recognized_params.append(param_name)
                    impact_score = max(impact_score, config["impact_score"])
            
            if recognized_params:
                validation_results.append(f"✅ Recognized Parameters: {', '.join(recognized_params)}")
                validation_results.append(f"📊 Impact Score: {impact_score}/10")
            else:
                validation_results.append("❓ No recognized parameters detected")
                impact_score = 5  # Default medium impact for unknown commands
            
            # Safety assessment
            validation_results.append("")
            validation_results.append("🛡️ SAFETY ASSESSMENT:")
            
            if command_type == "DISPLAY":
                validation_results.append("✅ SAFE: Display commands are read-only")
            elif impact_score <= 3:
                validation_results.append("✅ LOW RISK: Minimal impact expected")
            elif impact_score <= 6:
                validation_results.append("⚠️ MEDIUM RISK: Moderate impact possible")
            elif impact_score <= 8:
                validation_results.append("🔶 HIGH RISK: Significant impact likely")
            else:
                validation_results.append("🚨 CRITICAL RISK: Major impact expected")
                validation_results.append("❌ RECOMMENDATION: Manual review required")
            
            # Cell ID validation
            if cell_id:
                if re.search(r'CellId\s*=\s*\d+', command):
                    validation_results.append(f"✅ Cell ID specified: {cell_id}")
                else:
                    validation_results.append("⚠️ Cell ID not found in command")
            
            # Final recommendation
            validation_results.append("")
            if command_type == "DISPLAY" or impact_score <= self.max_impact_score:
                validation_results.append("✅ VALIDATION PASSED: Command approved for execution")
            else:
                validation_results.append("❌ VALIDATION FAILED: Command requires manual approval")
            
            return "\n".join(validation_results)
            
        except Exception as e:
            return f"❌ Command validation failed: {str(e)}"
    
    @tool
    def _execute_mml_command_tool(self, command: str, cell_id: str, confirm_execution: bool = False) -> str:
        """Safely execute MML command with validation"""
        try:
            execution_results = []
            execution_results.append("⚙️ MML COMMAND EXECUTION")
            execution_results.append("=" * 35)
            execution_results.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            execution_results.append(f"Cell ID: {cell_id}")
            execution_results.append(f"Command: {command}")
            execution_results.append("")
            
            # Pre-execution validation
            validation_result = self._validate_mml_command_tool(command, cell_id)
            
            if "VALIDATION FAILED" in validation_result:
                execution_results.append("❌ PRE-EXECUTION VALIDATION FAILED")
                execution_results.append("Validation Details:")
                execution_results.append(validation_result)
                return "\n".join(execution_results)
            
            # Safety checks for modification commands
            if command.upper().startswith('MOD ') and not confirm_execution:
                execution_results.append("⚠️ SAFETY CONFIRMATION REQUIRED")
                execution_results.append("This is a parameter modification command.")
                execution_results.append("Set confirm_execution=True to proceed after review.")
                return "\n".join(execution_results)
            
            # Attempt to execute via API client
            try:
                # Check API connection
                if not self.api_client.is_connected():
                    connection_result = self.api_client.connect()
                    if not connection_result:
                        execution_results.append("❌ EXECUTION FAILED: API connection unavailable")
                        execution_results.append("📝 Command logged for manual execution")
                        self._log_command_for_manual_execution(command, cell_id)
                        return "\n".join(execution_results)
                
                # Execute command
                execution_results.append("🔄 EXECUTING COMMAND...")
                
                # Use the parameter manager's execute method
                result = self.parameter_manager.execute_mml_command(
                    command=command,
                    cell_id=cell_id,
                    network_element=f"NE_{cell_id}"
                )
                
                if result.get('success', False):
                    execution_results.append("✅ COMMAND EXECUTED SUCCESSFULLY")
                    
                    # Parse and display results
                    if result.get('response'):
                        execution_results.append("📋 EXECUTION RESULTS:")
                        execution_results.append(result['response'])
                    
                    # Log successful execution
                    self.command_history.append({
                        'timestamp': datetime.now(),
                        'command': command,
                        'cell_id': cell_id,
                        'result': 'success',
                        'response': result.get('response', '')
                    })
                    
                else:
                    execution_results.append("❌ COMMAND EXECUTION FAILED")
                    execution_results.append(f"Error: {result.get('error', 'Unknown error')}")
                    
                    # Log failed execution
                    self.command_history.append({
                        'timestamp': datetime.now(),
                        'command': command,
                        'cell_id': cell_id,
                        'result': 'failed',
                        'error': result.get('error', 'Unknown error')
                    })
            
            except Exception as api_error:
                execution_results.append(f"❌ API EXECUTION ERROR: {str(api_error)}")
                execution_results.append("📝 Command logged for manual execution")
                self._log_command_for_manual_execution(command, cell_id)
            
            # Post-execution recommendations
            if command.upper().startswith('MOD '):
                execution_results.append("")
                execution_results.append("📝 POST-EXECUTION RECOMMENDATIONS:")
                execution_results.append("1. Monitor KPIs for impact assessment")
                execution_results.append("2. Verify parameter change took effect")
                execution_results.append("3. Prepare rollback if needed")
            
            return "\n".join(execution_results)
            
        except Exception as e:
            return f"❌ Command execution failed: {str(e)}"
    
    @tool
    def _display_current_parameters_tool(self, cell_id: str, parameter_names: Optional[List[str]] = None) -> str:
        """Display current parameter values for a cell"""
        try:
            if parameter_names is None:
                parameter_names = list(self.mml_templates.keys())
            
            display_results = []
            display_results.append(f"📋 CURRENT PARAMETERS - Cell {cell_id}")
            display_results.append("=" * 45)
            display_results.append(f"Retrieved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            display_results.append("")
            
            for param_name in parameter_names:
                if param_name not in self.mml_templates:
                    display_results.append(f"❓ {param_name}: Unknown parameter")
                    continue
                
                config = self.mml_templates[param_name]
                
                try:
                    # Use display command to get current value
                    display_command = config["display"].format(cell_id=cell_id)
                    
                    # Get current parameter value
                    current_value = self.parameter_manager.get_parameter_value(
                        param_name, cell_id, f"NE_{cell_id}"
                    )
                    
                    if current_value is not None:
                        # Get parameter details
                        param_config = self.parameter_manager.PARAMETER_CONFIG.get(param_name, {})
                        user_name = param_config.get('user_friendly_name', param_name)
                        unit = param_config.get('unit', '')
                        
                        display_results.append(f"✅ {user_name}: {current_value}{unit}")
                        
                        # Add range information
                        valid_range = config["validation_range"]
                        display_results.append(f"   Range: {valid_range[0]} to {valid_range[1]}{unit}")
                        display_results.append(f"   Impact: {config['impact_score']}/10")
                    else:
                        display_results.append(f"❌ {param_name}: Unable to retrieve value")
                
                except Exception as param_error:
                    display_results.append(f"❌ {param_name}: Error - {str(param_error)}")
                
                display_results.append("")
            
            # Add cell status information
            try:
                cell_status = self.api_client.get_cell_status(cell_id)
                if cell_status:
                    display_results.append("📊 CELL STATUS:")
                    display_results.append(f"   State: {cell_status.get('state', 'Unknown')}")
                    display_results.append(f"   Load: {cell_status.get('load', 'Unknown')}%")
                    display_results.append(f"   Active Users: {cell_status.get('active_users', 'Unknown')}")
            except:
                display_results.append("📊 Cell status information unavailable")
            
            return "\n".join(display_results)
            
        except Exception as e:
            return f"❌ Parameter display failed: {str(e)}"
    
    @tool
    def _assess_parameter_impact_tool(self, parameter_name: str, current_value: float, proposed_value: float, cell_id: str) -> str:
        """Assess the impact of changing a parameter value"""
        try:
            impact_results = []
            impact_results.append(f"📊 PARAMETER IMPACT ASSESSMENT")
            impact_results.append("=" * 40)
            impact_results.append(f"Parameter: {parameter_name}")
            impact_results.append(f"Cell ID: {cell_id}")
            impact_results.append(f"Current Value: {current_value}")
            impact_results.append(f"Proposed Value: {proposed_value}")
            impact_results.append("")
            
            if parameter_name not in self.mml_templates:
                impact_results.append("❌ Unknown parameter - cannot assess impact")
                return "\n".join(impact_results)
            
            config = self.mml_templates[parameter_name]
            param_config = self.parameter_manager.PARAMETER_CONFIG.get(parameter_name, {})
            
            # Validate proposed value is within range
            valid_range = config["validation_range"]
            if not (valid_range[0] <= proposed_value <= valid_range[1]):
                impact_results.append(f"❌ RANGE VIOLATION: Proposed value outside valid range")
                impact_results.append(f"   Valid range: {valid_range[0]} to {valid_range[1]}")
                impact_results.append(f"   Risk Level: CRITICAL")
                return "\n".join(impact_results)
            
            # Calculate change magnitude
            change_absolute = abs(proposed_value - current_value)
            change_percentage = (change_absolute / abs(current_value) * 100) if current_value != 0 else 100
            
            impact_results.append(f"📈 CHANGE ANALYSIS:")
            impact_results.append(f"   Absolute Change: {change_absolute}")
            impact_results.append(f"   Percentage Change: {change_percentage:.1f}%")
            impact_results.append(f"   Direction: {'Increase' if proposed_value > current_value else 'Decrease'}")
            impact_results.append("")
            
            # Impact scoring
            base_impact = config["impact_score"]
            
            # Adjust impact based on change magnitude
            if change_percentage > 50:
                adjusted_impact = min(10, base_impact + 2)
                change_severity = "MAJOR"
            elif change_percentage > 25:
                adjusted_impact = min(10, base_impact + 1)
                change_severity = "SIGNIFICANT"
            elif change_percentage > 10:
                adjusted_impact = base_impact
                change_severity = "MODERATE"
            else:
                adjusted_impact = max(1, base_impact - 1)
                change_severity = "MINOR"
            
            impact_results.append(f"🎯 IMPACT ASSESSMENT:")
            impact_results.append(f"   Base Impact Score: {base_impact}/10")
            impact_results.append(f"   Adjusted Impact Score: {adjusted_impact}/10")
            impact_results.append(f"   Change Severity: {change_severity}")
            impact_results.append("")
            
            # Specific parameter impacts
            parameter_impacts = {
                "P0_NominalPUSCH": {
                    "increase": "Higher uplink power → Better coverage but more interference",
                    "decrease": "Lower uplink power → Reduced interference but coverage risk"
                },
                "ReferenceSignalPower_PDSCH": {
                    "increase": "Stronger downlink → Better coverage but more power consumption",
                    "decrease": "Weaker downlink → Power savings but coverage degradation"
                },
                "ReferenceSignalPower_PUSCH": {
                    "increase": "Higher uplink reference → Better uplink quality",
                    "decrease": "Lower uplink reference → Potential quality degradation"
                },
                "A3EventOffset": {
                    "increase": "Later handovers → Less ping-pong but coverage holes risk",
                    "decrease": "Earlier handovers → Better load balancing but more ping-pong"
                },
                "T310Timer": {
                    "increase": "Longer failure detection → More stable but slower recovery",
                    "decrease": "Faster failure detection → Quicker recovery but less stable"
                },
                "PDCCHAggregationLevel": {
                    "increase": "Higher aggregation → More robust but less capacity",
                    "decrease": "Lower aggregation → More capacity but less robust"
                }
            }
            
            param_impact = parameter_impacts.get(parameter_name, {})
            direction = "increase" if proposed_value > current_value else "decrease"
            expected_impact = param_impact.get(direction, "Impact depends on network conditions")
            
            impact_results.append(f"🔍 EXPECTED EFFECTS:")
            impact_results.append(f"   {expected_impact}")
            impact_results.append("")
            
            # Risk assessment
            if adjusted_impact <= 3:
                risk_level = "LOW"
                risk_icon = "✅"
                recommendation = "Safe to proceed"
            elif adjusted_impact <= 6:
                risk_level = "MEDIUM"
                risk_icon = "⚠️"
                recommendation = "Proceed with monitoring"
            elif adjusted_impact <= 8:
                risk_level = "HIGH"
                risk_icon = "🔶"
                recommendation = "Require careful validation"
            else:
                risk_level = "CRITICAL"
                risk_icon = "🚨"
                recommendation = "Manual approval required"
            
            impact_results.append(f"🛡️ RISK ASSESSMENT:")
            impact_results.append(f"   {risk_icon} Risk Level: {risk_level}")
            impact_results.append(f"   Recommendation: {recommendation}")
            
            return "\n".join(impact_results)
            
        except Exception as e:
            return f"❌ Impact assessment failed: {str(e)}"
    
    @tool 
    def _generate_safe_mml_commands_tool(self, parameter_updates: Dict[str, Any], cell_id: str) -> str:
        """Generate safe MML commands for parameter updates"""
        try:
            command_results = []
            command_results.append("🔧 SAFE MML COMMAND GENERATION")
            command_results.append("=" * 40)
            command_results.append(f"Target Cell: {cell_id}")
            command_results.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            command_results.append("")
            
            valid_commands = []
            warnings = []
            errors = []
            
            for param_name, new_value in parameter_updates.items():
                if param_name not in self.mml_templates:
                    errors.append(f"❌ {param_name}: Unknown parameter")
                    continue
                
                config = self.mml_templates[param_name]
                
                # Validate value range
                valid_range = config["validation_range"]
                if not (valid_range[0] <= new_value <= valid_range[1]):
                    errors.append(f"❌ {param_name}: Value {new_value} outside range {valid_range}")
                    continue
                
                # Generate MML command
                mml_command = config["modify"].format(cell_id=cell_id, value=new_value)
                
                # Safety assessment
                impact_score = config["impact_score"]
                if impact_score > self.max_impact_score:
                    warnings.append(f"⚠️ {param_name}: High impact score ({impact_score})")
                
                valid_commands.append({
                    'parameter': param_name,
                    'command': mml_command,
                    'value': new_value,
                    'impact_score': impact_score
                })
            
            # Display generated commands
            if valid_commands:
                command_results.append("✅ GENERATED COMMANDS:")
                command_results.append("")
                
                # Sort by impact score (lowest risk first)
                valid_commands.sort(key=lambda x: x['impact_score'])
                
                for i, cmd_info in enumerate(valid_commands, 1):
                    param_config = self.parameter_manager.PARAMETER_CONFIG.get(cmd_info['parameter'], {})
                    user_name = param_config.get('user_friendly_name', cmd_info['parameter'])
                    
                    command_results.append(f"{i}. {user_name} (Impact: {cmd_info['impact_score']}/10)")
                    command_results.append(f"   Command: {cmd_info['command']}")
                    command_results.append(f"   New Value: {cmd_info['value']}")
                    command_results.append("")
            
            # Display warnings and errors
            if warnings:
                command_results.append("⚠️ WARNINGS:")
                command_results.extend(warnings)
                command_results.append("")
            
            if errors:
                command_results.append("❌ ERRORS:")
                command_results.extend(errors)
                command_results.append("")
            
            # Execution recommendations
            command_results.append("📋 EXECUTION RECOMMENDATIONS:")
            
            if not valid_commands:
                command_results.append("❌ No valid commands generated")
            elif len([cmd for cmd in valid_commands if cmd['impact_score'] > self.max_impact_score]) > 0:
                command_results.append("🚨 Manual approval required for high-impact commands")
                command_results.append("Execute low-impact commands first")
            else:
                command_results.append("✅ All commands within acceptable risk levels")
                command_results.append("Execute in order of impact score (lowest first)")
            
            command_results.append("")
            command_results.append("⚡ Execute commands using: execute_mml_command_tool")
            
            return "\n".join(command_results)
            
        except Exception as e:
            return f"❌ Command generation failed: {str(e)}"
    
    def _log_command_for_manual_execution(self, command: str, cell_id: str):
        """Log command for manual execution when API is unavailable"""
        log_entry = {
            'timestamp': datetime.now(),
            'command': command,
            'cell_id': cell_id,
            'status': 'pending_manual_execution',
            'logged_by': 'MML_Command_Agent'
        }
        self.command_history.append(log_entry)
        
        # Could also write to a file or external logging system
        print(f"📝 Command logged for manual execution: {command}")
    
    def handle_request(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle requests from main agents"""
        user_request = state.get("messages", [])[-1] if state.get("messages") else "Display current parameters"
        
        print("\n⚙️ MML Command Agent - Processing Request")
        
        try:
            # Use LLM agent to process the request
            response = self.llm_agent.invoke({"messages": [HumanMessage(content=user_request)]})
            
            result_message = response["messages"][-1].content if response.get("messages") else "MML command processing complete"
            
            # Update state with command execution information
            enhanced_state = state.copy()
            enhanced_state.update({
                "mml_commands_available": True,
                "parameter_templates": self.mml_templates,
                "safety_checks_enabled": self.safety_checks_enabled,
                "command_history": self.command_history[-5:]  # Last 5 commands
            })
            
            enhanced_state["messages"] = state.get("messages", []) + [("assistant", result_message)]
            
            return enhanced_state
            
        except Exception as e:
            error_msg = f"❌ MML Command Agent error: {str(e)}"
            print(error_msg)
            
            enhanced_state = state.copy()
            enhanced_state["messages"] = state.get("messages", []) + [("assistant", error_msg)]
            return enhanced_state
    
    # ========== MISSING TOOL METHODS ==========
    # Adding placeholder tools that were referenced but not implemented
    
    @tool
    def _check_command_syntax_tool(self, command: str) -> str:
        """Check MML command syntax for validity"""
        try:
            # Basic syntax validation
            if not command.strip():
                return "Command syntax check failed: Empty command"
            
            # Check for basic MML command structure
            if not any(cmd in command.upper() for cmd in ['MOD', 'ADD', 'RMV', 'DSP', 'LST']):
                return "Command syntax check warning: No recognized MML command found"
            
            return f"Command syntax check passed for: {command[:50]}{'...' if len(command) > 50 else ''}"
        except Exception as e:
            return f"Command syntax check failed: {str(e)}"
    
    @tool
    def _create_parameter_rollback_tool(self, parameter_name: str, site_name: str, cell_id: int) -> str:
        """Create rollback plan for parameter change"""
        try:
            current_value = self.parameter_manager.get_parameter_value(parameter_name, site_name, cell_id)
            rollback_command = self.parameter_manager.generate_mml_command(
                parameter_name, current_value, site_name, cell_id
            )
            
            return f"Rollback plan created for {parameter_name}: {rollback_command}"
        except Exception as e:
            return f"Rollback plan creation failed: {str(e)}"
    
    @tool
    def _batch_parameter_update_tool(self, updates: List[Dict[str, Any]]) -> str:
        """Execute multiple parameter updates in a batch"""
        try:
            results = []
            for update in updates[:5]:  # Limit to 5 updates for safety
                param_name = update.get('parameter_name')
                new_value = update.get('new_value')
                site_name = update.get('site_name')
                
                if param_name and new_value and site_name:
                    command = self.parameter_manager.generate_mml_command(param_name, new_value, site_name)
                    results.append(f"Generated command for {param_name}: {command}")
                else:
                    results.append(f"Skipped incomplete update: {update}")
            
            return f"Batch update prepared: {len(results)} commands ready"
        except Exception as e:
            return f"Batch parameter update failed: {str(e)}"

# Lazy initialization function for singleton instance
_mml_command_agent = None

def get_mml_command_agent():
    """Get the singleton MML command agent instance"""
    global _mml_command_agent
    if _mml_command_agent is None:
        _mml_command_agent = MMLCommandAgent()
    return _mml_command_agent

# For backward compatibility
def mml_command_agent():
    """Backward compatibility function"""
    return get_mml_command_agent()