#!/usr/bin/env python3
"""
Application Runner Script.

Main entry point for the Cassava 4G Network Optimizer.
Supports multiple run modes: UI, CLI optimization, and monitoring.

Usage:
    python -m cassava_optimizer.scripts.run ui           # Start Streamlit UI
    python -m cassava_optimizer.scripts.run optimize     # Run optimization workflow
    python -m cassava_optimizer.scripts.run monitor      # Start monitoring mode
"""

import argparse
import asyncio
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from cassava_optimizer.config import get_settings, Settings

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure application logging."""
    from cassava_optimizer.utils.logger import configure_logging, get_logger
    
    settings = get_settings()
    
    configure_logging(
        log_level=settings.log_level if not verbose else "DEBUG",
        log_file=settings.log_file,
        json_format=settings.log_json_format,
    )


async def run_optimization(
    site_name: Optional[str] = None,
    dry_run: bool = False,
    auto_approve: bool = False,
) -> None:
    """
    Run the optimization workflow for a site or all sites.
    
    Args:
        site_name: Specific site to optimize, or None for all sites
        dry_run: If True, generate recommendations without executing
        auto_approve: If True, automatically approve recommendations
    """
    from cassava_optimizer.config import get_settings
    from cassava_optimizer.infrastructure.database import DatabaseManager
    from cassava_optimizer.workflow.orchestrator import WorkflowOrchestrator
    from cassava_optimizer.workflow.state import create_initial_state
    
    settings = get_settings()
    db_manager = DatabaseManager(settings.database_url)
    
    try:
        await db_manager.connect()
        logger.info("Connected to database")
        
        # Get sites to optimize
        if site_name:
            result = await db_manager.execute(
                "SELECT id, name FROM sites WHERE name = ?",
                (site_name,)
            )
            sites = await result.fetchall()
            if not sites:
                raise ValueError(f"Site not found: {site_name}")
        else:
            result = await db_manager.execute(
                "SELECT id, name FROM sites WHERE status = 'online'"
            )
            sites = await result.fetchall()
        
        if not sites:
            logger.warning("No sites found to optimize")
            print("❌ No sites found to optimize")
            return
        
        print(f"\n📊 Found {len(sites)} site(s) to optimize")
        
        # Initialize orchestrator
        orchestrator = WorkflowOrchestrator(settings)
        
        for site_id, site_name in sites:
            print(f"\n{'='*60}")
            print(f"🔧 Optimizing site: {site_name}")
            print(f"{'='*60}")
            
            # Create initial state
            initial_state = create_initial_state(
                site_id=site_id,
                site_name=site_name,
                dry_run=dry_run,
                auto_approve=auto_approve,
            )
            
            # Run workflow
            try:
                final_state = await orchestrator.run(initial_state)
                
                # Print results
                print(f"\n✅ Optimization complete for {site_name}")
                print(f"   Total recommendations: {final_state.get('total_recommendations', 0)}")
                print(f"   Approved: {final_state.get('approved_count', 0)}")
                print(f"   Executed: {final_state.get('executed_count', 0)}")
                
                if final_state.get("errors"):
                    print(f"\n⚠️  Warnings/Errors:")
                    for error in final_state["errors"][-5:]:  # Last 5 errors
                        print(f"   - {error}")
                        
            except Exception as e:
                logger.error(f"Optimization failed for {site_name}: {e}")
                print(f"❌ Optimization failed for {site_name}: {e}")
                continue
        
        print(f"\n{'='*60}")
        print("🎉 All optimizations complete!")
        print(f"{'='*60}")
        
    except Exception as e:
        logger.error(f"Optimization workflow failed: {e}")
        raise
    finally:
        await db_manager.disconnect()


async def run_monitor() -> None:
    """Run continuous monitoring mode."""
    from cassava_optimizer.config import get_settings
    from cassava_optimizer.infrastructure.database import DatabaseManager
    from cassava_optimizer.tools.mae_tools import fetch_site_kpis, check_site_health
    
    settings = get_settings()
    db_manager = DatabaseManager(settings.database_url)
    
    try:
        await db_manager.connect()
        logger.info("Starting monitoring mode")
        print("\n🔍 Starting continuous monitoring (Ctrl+C to stop)\n")
        
        # Get all active sites
        result = await db_manager.execute(
            "SELECT id, name FROM sites WHERE status = 'online'"
        )
        sites = await result.fetchall()
        
        if not sites:
            print("❌ No active sites found for monitoring")
            return
        
        print(f"📡 Monitoring {len(sites)} site(s)")
        
        iteration = 0
        while True:
            iteration += 1
            print(f"\n--- Monitor iteration {iteration} ---")
            
            for site_id, site_name in sites:
                try:
                    # Fetch and store KPIs
                    kpi_result = await fetch_site_kpis.ainvoke({
                        "site_name": site_name,
                    })
                    
                    # Check health
                    health_result = await check_site_health.ainvoke({
                        "site_name": site_name,
                    })
                    
                    health_status = "🟢" if health_result.get("status") == "healthy" else "🟡"
                    print(f"   {health_status} {site_name}: {health_result.get('status', 'unknown')}")
                    
                except Exception as e:
                    logger.warning(f"Monitor error for {site_name}: {e}")
                    print(f"   🔴 {site_name}: Error - {e}")
            
            # Wait before next iteration
            await asyncio.sleep(settings.monitor_interval or 300)
            
    except asyncio.CancelledError:
        print("\n\n🛑 Monitoring stopped")
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        raise
    finally:
        await db_manager.disconnect()


def run_ui() -> None:
    """Start the Streamlit UI."""
    settings = get_settings()
    
    # Find the app.py file
    app_path = Path(__file__).parent.parent / "ui" / "app.py"
    
    if not app_path.exists():
        raise FileNotFoundError(f"UI app not found at: {app_path}")
    
    print("\n🚀 Starting Cassava Network Optimizer UI\n")
    print(f"   App: {app_path}")
    print(f"   URL: http://localhost:8501")
    print("\nPress Ctrl+C to stop\n")
    
    # Build streamlit command
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.port", str(settings.ui_port or 8501),
        "--server.address", "0.0.0.0",
        "--theme.base", "dark",
        "--theme.primaryColor", "#00F19C",
        "--theme.backgroundColor", "#0E1117",
        "--theme.secondaryBackgroundColor", "#1B1F2D",
        "--browser.gatherUsageStats", "false",
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n\n🛑 UI stopped")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start UI: {e}")
        raise


async def run_health_check() -> bool:
    """Run a health check on all system components."""
    from cassava_optimizer.config import get_settings
    from cassava_optimizer.infrastructure.database import DatabaseManager
    from cassava_optimizer.network.mae_client import HuaweiMAEClient
    from cassava_optimizer.utils.logger import get_logger
    
    settings = get_settings()
    all_healthy = True
    
    print("\n🏥 Running system health check\n")
    
    # Check database
    print("📦 Database:", end=" ")
    try:
        db_manager = DatabaseManager(settings.database_url)
        await db_manager.connect()
        result = await db_manager.execute("SELECT COUNT(*) FROM sites")
        count = (await result.fetchone())[0]
        await db_manager.disconnect()
        print(f"✅ OK ({count} sites)")
    except Exception as e:
        print(f"❌ FAILED - {e}")
        all_healthy = False
    
    # Check MAE API
    print("🌐 Huawei MAE API:", end=" ")
    try:
        async with HuaweiMAEClient(settings) as client:
            sites = await client.get_managed_elements()
            print(f"✅ OK ({len(sites)} elements)")
    except Exception as e:
        print(f"❌ FAILED - {e}")
        all_healthy = False
    
    # Check NVIDIA NIM
    print("🤖 NVIDIA NIM:", end=" ")
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{settings.nvidia_nim_url}/v1/models",
                headers={"Authorization": f"Bearer {settings.nvidia_api_key}"},
            )
            if response.status_code == 200:
                print("✅ OK")
            else:
                print(f"⚠️  Status {response.status_code}")
    except Exception as e:
        print(f"❌ FAILED - {e}")
        all_healthy = False
    
    # Check log directory
    print("📝 Logs:", end=" ")
    try:
        log_dir = Path(settings.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ OK ({log_dir})")
    except Exception as e:
        print(f"❌ FAILED - {e}")
        all_healthy = False
    
    print()
    if all_healthy:
        print("✅ All systems healthy!")
    else:
        print("⚠️  Some systems are unhealthy")
    
    return all_healthy


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Cassava 4G Network Optimizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m cassava_optimizer.scripts.run ui              # Start web UI
    python -m cassava_optimizer.scripts.run optimize        # Optimize all sites
    python -m cassava_optimizer.scripts.run optimize -s HQ  # Optimize specific site
    python -m cassava_optimizer.scripts.run monitor         # Continuous monitoring
    python -m cassava_optimizer.scripts.run health          # System health check
        """
    )
    
    parser.add_argument(
        "command",
        choices=["ui", "optimize", "monitor", "health"],
        help="Command to run",
    )
    
    parser.add_argument(
        "--site", "-s",
        help="Site name for optimization (default: all sites)",
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate recommendations without executing",
    )
    
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Automatically approve recommendations",
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.verbose)
    
    # Banner
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     🌿 Cassava 4G Network Optimizer                       ║
    ║     Powered by AI-Driven Network Intelligence             ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    try:
        if args.command == "ui":
            run_ui()
            
        elif args.command == "optimize":
            asyncio.run(run_optimization(
                site_name=args.site,
                dry_run=args.dry_run,
                auto_approve=args.auto_approve,
            ))
            
        elif args.command == "monitor":
            asyncio.run(run_monitor())
            
        elif args.command == "health":
            healthy = asyncio.run(run_health_check())
            sys.exit(0 if healthy else 1)
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Command failed: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
