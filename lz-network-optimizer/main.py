"""
Liquid Zimbabwe 4G Network Optimizer - Main Entry Point
Purpose: CLI interface for running optimizations
Created: 2025-10-30
"""

import argparse
import logging
import sys
import os
from pathlib import Path

# Add agents directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

from agents.workflow import run_optimization
from network.kpi_collector import KPICollector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Liquid Zimbabwe 4G Network Optimizer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Optimize specific site
  python main.py --site "MSH0013-Bindura-Zaoga" --query "Improve download speed"

  # List available sites
  python main.py --list-sites

  # Run in offline mode (uses historical data only)
  python main.py --site "MSH0013-Bindura-Zaoga" --offline
        """
    )

    parser.add_argument(
        '--site',
        type=str,
        help='Site/eNodeB name to optimize'
    )

    parser.add_argument(
        '--cell-id',
        type=int,
        default=1,
        help='Cell ID (default: 1)'
    )

    parser.add_argument(
        '--query',
        type=str,
        default='Optimize network performance',
        help='Optimization query/goal'
    )

    parser.add_argument(
        '--list-sites',
        action='store_true',
        help='List all available sites'
    )

    parser.add_argument(
        '--offline',
        action='store_true',
        help='Run in offline mode (historical data only)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Set offline mode if requested
    if args.offline:
        os.environ['OFFLINE_MODE'] = 'true'
        logger.info("Running in OFFLINE MODE (historical data only)")

    # Handle list-sites command
    if args.list_sites:
        logger.info("Fetching list of available sites...")
        collector = KPICollector()
        sites = collector.get_all_sites()

        print("\n" + "=" * 80)
        print("AVAILABLE SITES")
        print("=" * 80)
        for i, site in enumerate(sites, 1):
            print(f"{i}. {site}")
        print("=" * 80)
        print(f"Total: {len(sites)} sites\n")
        return 0

    # Validate site argument
    if not args.site:
        parser.error("--site is required (or use --list-sites to see available sites)")

    # Run optimization
    logger.info(f"Starting optimization for site: {args.site}")
    print("\n" + "=" * 80)
    print(f"LIQUID ZIMBABWE 4G NETWORK OPTIMIZER")
    print("=" * 80)
    print(f"Site: {args.site}")
    print(f"Cell ID: {args.cell_id}")
    print(f"Query: {args.query}")
    print("=" * 80 + "\n")

    try:
        # Run workflow
        result = run_optimization(
            site_name=args.site,
            user_query=args.query,
            cell_id=args.cell_id
        )

        # Display results
        print("\n" + "=" * 80)
        print("OPTIMIZATION RESULTS")
        print("=" * 80)
        print(f"Data Source: {result.get('data_source', 'Unknown')}")
        print(f"Optimization Needed: {result.get('needs_optimization', False)}")

        if result.get('needs_optimization'):
            print(f"Primary KPI Issue: {result.get('primary_kpi_issue', 'Unknown')}")
            print(f"Validation Status: {result.get('validation_status', 'N/A')}")
            print(f"Optimization Success: {result.get('optimization_success', False)}")

        print("=" * 80)

        # Display agent outputs summary
        print("\nAGENT WORKFLOW SUMMARY:")
        print("-" * 80)
        for agent_name, output in result.get('agent_outputs', {}).items():
            print(f"\n{agent_name.upper()}:")
            # Show first 300 chars of each output
            print(output[:300] + "..." if len(output) > 300 else output)
            print()

        print("=" * 80)
        logger.info("Optimization completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Optimization failed: {e}", exc_info=True)
        print(f"\nERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
