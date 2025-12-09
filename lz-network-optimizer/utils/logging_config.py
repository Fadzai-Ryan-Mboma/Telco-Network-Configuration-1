#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Network Optimizer - Enhanced Logging Configuration
Purpose: Comprehensive logging for terminal visibility of agent workflows
Created: 2025-11-03
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import yaml
from typing import Optional

# Color codes for terminal output
class Colors:
    """ANSI color codes for colorful terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    # Agent-specific colors
    AGENT = '\033[96m'  # Cyan
    TOOL = '\033[93m'   # Yellow
    API = '\033[92m'    # Green
    STATE = '\033[95m'  # Magenta
    LLM = '\033[94m'    # Blue


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""

    COLORS = {
        'DEBUG': Colors.OKCYAN,
        'INFO': Colors.OKGREEN,
        'WARNING': Colors.WARNING,
        'ERROR': Colors.FAIL,
        'CRITICAL': Colors.FAIL + Colors.BOLD,
    }

    def format(self, record):
        # Add color based on level
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Colors.ENDC}"

        # Add color based on logger name
        if 'Agent' in record.name:
            record.name = f"{Colors.AGENT}{record.name}{Colors.ENDC}"
        elif 'Tool' in record.name or 'Huawei' in record.name:
            record.name = f"{Colors.TOOL}{record.name}{Colors.ENDC}"
        elif 'API' in record.name:
            record.name = f"{Colors.API}{record.name}{Colors.ENDC}"
        elif 'LLM' in record.name or 'NVIDIA' in record.name:
            record.name = f"{Colors.LLM}{record.name}{Colors.ENDC}"

        return super().format(record)


class WorkflowLogger:
    """
    Enhanced logger for agent workflow visibility.

    Provides methods to log:
    - Agent state transitions
    - Tool calls and results
    - LLM prompts and responses
    - API requests and responses
    - Workflow decisions
    """

    def __init__(self, name: str = "LZ-Workflow", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Load config
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}

        self.agent_config = self.config.get('logging', {}).get('agent_logs', {})

    def log_workflow_start(self, site_name: str, cell_id: int, query: str):
        """Log workflow initialization"""
        self.logger.info("=" * 80)
        self.logger.info(f"{Colors.BOLD}🚀 OPTIMIZATION WORKFLOW STARTED{Colors.ENDC}")
        self.logger.info(f"  📍 Site: {Colors.BOLD}{site_name}{Colors.ENDC}")
        self.logger.info(f"  📡 Cell ID: {Colors.BOLD}{cell_id}{Colors.ENDC}")
        self.logger.info(f"  💬 Query: {Colors.BOLD}{query}{Colors.ENDC}")
        self.logger.info("=" * 80)

    def log_agent_start(self, agent_name: str, step_number: int):
        """Log agent execution start"""
        self.logger.info("")
        self.logger.info(f"{Colors.AGENT}{'─' * 80}{Colors.ENDC}")
        self.logger.info(f"{Colors.AGENT}🤖 AGENT {step_number}: {agent_name.upper()}{Colors.ENDC}")
        self.logger.info(f"{Colors.AGENT}{'─' * 80}{Colors.ENDC}")

    def log_agent_complete(self, agent_name: str, output_summary: str):
        """Log agent execution completion"""
        self.logger.info(f"{Colors.OKGREEN}✅ {agent_name} completed{Colors.ENDC}")
        self.logger.info(f"   Summary: {output_summary[:100]}...")

    def log_state_transition(self, from_state: str, to_state: str, reason: str = ""):
        """Log workflow state transition"""
        if not self.agent_config.get('log_state_transitions', False):
            return

        self.logger.info(f"{Colors.STATE}📊 STATE TRANSITION: {from_state} → {to_state}{Colors.ENDC}")
        if reason:
            self.logger.info(f"   Reason: {reason}")

    def log_tool_call(self, tool_name: str, parameters: dict):
        """Log tool invocation"""
        if not self.agent_config.get('log_tool_calls', False):
            return

        self.logger.info(f"{Colors.TOOL}🔧 TOOL CALL: {tool_name}{Colors.ENDC}")
        for key, value in parameters.items():
            # Truncate long values
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:100] + "..."
            self.logger.info(f"   {key}: {value_str}")

    def log_tool_result(self, tool_name: str, result: str, success: bool = True):
        """Log tool execution result"""
        if not self.agent_config.get('log_tool_calls', False):
            return

        status = f"{Colors.OKGREEN}✓{Colors.ENDC}" if success else f"{Colors.FAIL}✗{Colors.ENDC}"
        self.logger.info(f"{Colors.TOOL}{status} TOOL RESULT: {tool_name}{Colors.ENDC}")

        # Truncate long results
        result_str = str(result)
        if len(result_str) > 200:
            result_str = result_str[:200] + "... [truncated]"
        self.logger.info(f"   {result_str}")

    def log_llm_prompt(self, agent_name: str, prompt: str):
        """Log LLM prompt"""
        if not self.agent_config.get('log_llm_prompts', False):
            return

        self.logger.info(f"{Colors.LLM}{'┌' + '─' * 78 + '┐'}{Colors.ENDC}")
        self.logger.info(f"{Colors.LLM}│ 📝 LLM PROMPT ({agent_name}){' ' * (78 - len(agent_name) - 17)}│{Colors.ENDC}")
        self.logger.info(f"{Colors.LLM}{'├' + '─' * 78 + '┤'}{Colors.ENDC}")

        # Split prompt into lines and indent
        lines = prompt.split('\n')
        for line in lines[:20]:  # Show first 20 lines
            # Truncate long lines
            if len(line) > 76:
                line = line[:76] + "..."
            self.logger.info(f"{Colors.LLM}│ {line}{' ' * (77 - len(line))}│{Colors.ENDC}")

        if len(lines) > 20:
            self.logger.info(f"{Colors.LLM}│ ... [{len(lines) - 20} more lines]{' ' * 54}│{Colors.ENDC}")

        self.logger.info(f"{Colors.LLM}{'└' + '─' * 78 + '┘'}{Colors.ENDC}")

    def log_llm_response(self, agent_name: str, response: str):
        """Log LLM response"""
        if not self.agent_config.get('log_llm_responses', False):
            return

        self.logger.info(f"{Colors.LLM}{'┌' + '─' * 78 + '┐'}{Colors.ENDC}")
        self.logger.info(f"{Colors.LLM}│ 💬 LLM RESPONSE ({agent_name}){' ' * (78 - len(agent_name) - 19)}│{Colors.ENDC}")
        self.logger.info(f"{Colors.LLM}{'├' + '─' * 78 + '┤'}{Colors.ENDC}")

        # Split response into lines
        lines = response.split('\n')
        for line in lines[:30]:  # Show first 30 lines
            # Truncate long lines
            if len(line) > 76:
                line = line[:76] + "..."
            self.logger.info(f"{Colors.LLM}│ {line}{' ' * (77 - len(line))}│{Colors.ENDC}")

        if len(lines) > 30:
            self.logger.info(f"{Colors.LLM}│ ... [{len(lines) - 30} more lines]{' ' * 54}│{Colors.ENDC}")

        self.logger.info(f"{Colors.LLM}{'└' + '─' * 78 + '┘'}{Colors.ENDC}")

    def log_api_request(self, endpoint: str, method: str, params: dict):
        """Log API request"""
        self.logger.info(f"{Colors.API}🌐 API REQUEST: {method} {endpoint}{Colors.ENDC}")
        if params:
            for key, value in params.items():
                # Don't log sensitive data
                if 'password' in key.lower() or 'token' in key.lower():
                    value = "***REDACTED***"
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                self.logger.info(f"   {key}: {value_str}")

    def log_api_response(self, endpoint: str, status_code: int, response_time: float):
        """Log API response"""
        status = f"{Colors.OKGREEN}✓{Colors.ENDC}" if status_code < 400 else f"{Colors.FAIL}✗{Colors.ENDC}"
        self.logger.info(f"{Colors.API}{status} API RESPONSE: {status_code} ({response_time:.3f}s){Colors.ENDC}")

    def log_decision(self, decision_point: str, decision: str, reason: str):
        """Log workflow decision"""
        self.logger.info(f"{Colors.WARNING}⚖️  DECISION: {decision_point}{Colors.ENDC}")
        self.logger.info(f"   Decision: {Colors.BOLD}{decision}{Colors.ENDC}")
        self.logger.info(f"   Reason: {reason}")

    def log_workflow_end(self, success: bool, summary: str):
        """Log workflow completion"""
        self.logger.info("")
        self.logger.info("=" * 80)
        if success:
            self.logger.info(f"{Colors.OKGREEN}{Colors.BOLD}✅ WORKFLOW COMPLETED SUCCESSFULLY{Colors.ENDC}")
        else:
            self.logger.info(f"{Colors.FAIL}{Colors.BOLD}❌ WORKFLOW FAILED{Colors.ENDC}")
        self.logger.info(f"  Summary: {summary}")
        self.logger.info("=" * 80)


def setup_logging(mode: str = "verbose", log_file: Optional[str] = None):
    """
    Setup comprehensive logging for the application.

    Args:
        mode: Logging mode - "basic", "verbose", or "debug"
        log_file: Optional log file path

    Modes:
        - basic: INFO level, minimal output
        - verbose: INFO level, show all agent/tool activity
        - debug: DEBUG level, show everything including internals
    """

    # Set root logger level based on mode
    if mode == "debug":
        level = logging.DEBUG
    else:
        level = logging.INFO

    # Create formatters
    if mode == "basic":
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
    else:
        formatter = ColoredFormatter(
            '%(asctime)s - %(name)-25s - %(levelname)-8s - %(message)s',
            datefmt='%H:%M:%S'
        )

    # Setup console handler (terminal output)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)

    # Setup file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Configure specific loggers based on mode
    loggers_config = {
        'LZ-Workflow': level,
        'LZ-Agent': level,
        'LZ-Huawei-API': level,
        'LZ-Tool': level,
        'LZ-NVIDIA-LLM': level,
        'LZ-UI': level,
    }

    for logger_name, logger_level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(logger_level)

    # Reduce noise from third-party libraries unless in debug mode
    if mode != "debug":
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)
        logging.getLogger('openai').setLevel(logging.WARNING)
        logging.getLogger('streamlit').setLevel(logging.WARNING)

    return WorkflowLogger()


def create_log_file_path() -> str:
    """Create timestamped log file path"""
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return str(logs_dir / f"lz_optimizer_{timestamp}.log")


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    # Example 1: Basic logging
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Logging Mode")
    print("=" * 80)

    workflow_logger = setup_logging(mode="basic")
    workflow_logger.log_workflow_start("MSH-0112-Bindura Hospital", 1, "Optimize network performance")
    workflow_logger.log_agent_start("Network Connector", 1)
    workflow_logger.log_agent_complete("Network Connector", "Successfully connected to Huawei API")

    # Example 2: Verbose logging
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Verbose Logging Mode")
    print("=" * 80)

    workflow_logger = setup_logging(mode="verbose", log_file=create_log_file_path())
    workflow_logger.log_workflow_start("MSH-0112-Bindura Hospital", 1, "Optimize network performance")
    workflow_logger.log_agent_start("Network Connector", 1)
    workflow_logger.log_tool_call("query_huawei_parameter", {
        "parameter_name": "reference_signal_power_pdschcfg",
        "site_name": "MSH-0112-Bindura Hospital",
        "cell_id": 1
    })
    workflow_logger.log_tool_result("query_huawei_parameter", "Current value: 152 (15.2 dBm)", success=True)
    workflow_logger.log_agent_complete("Network Connector", "Successfully retrieved parameter values")

    workflow_logger.log_agent_start("Monitoring Agent", 2)
    workflow_logger.log_llm_prompt("Monitoring Agent", """
You are a network monitoring expert. Analyze the following KPI data:

Network Access Success: 92.5%
Download Speed: 45.2 Mbps
Upload Speed: 18.3 Mbps

Determine if optimization is needed.
""")
    workflow_logger.log_llm_response("Monitoring Agent", """
Based on the KPI analysis:

1. Network Access Success (92.5%) is below threshold (95%)
2. Download Speed (45.2 Mbps) is below threshold (50 Mbps)

RECOMMENDATION: Optimization needed
PRIMARY ISSUE: Poor network access success rate
""")
    workflow_logger.log_decision("Needs Optimization?", "YES", "Network Access Success below threshold")
    workflow_logger.log_workflow_end(True, "Generated optimization recommendations")

    print("\n" + "=" * 80)
    print(f"Full logs saved to: {create_log_file_path()}")
    print("=" * 80)
