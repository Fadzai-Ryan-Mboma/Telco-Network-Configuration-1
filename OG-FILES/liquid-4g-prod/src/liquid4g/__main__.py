"""
CLI Entry Point for Liquid4G
"""

import click
from rich.console import Console
from liquid4g.core.logging import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
@click.version_option(version="2.0.0")
def cli():
    """Liquid Zimbabwe 4G Network Optimizer CLI"""
    pass


@cli.command()
@click.option("--host", default="0.0.0.0", help="API host")
@click.option("--port", default=8000, type=int, help="API port")
def api(host: str, port: int):
    """Start the REST API server"""
    console.print("[bold green]🚀 Starting Liquid4G API Server...[/bold green]")
    logger.info(f"Starting API server on {host}:{port}")

    try:
        import uvicorn
        from liquid4g.interfaces.api.main import app

        uvicorn.run(app, host=host, port=port)
    except ImportError:
        console.print("[bold red]❌ FastAPI not installed. Run: pip install liquid4g[api][/bold red]")


@cli.command()
def ui():
    """Start the Streamlit UI"""
    console.print("[bold green]🚀 Starting Liquid4G UI...[/bold green]")
    logger.info("Starting Streamlit UI")

    try:
        import streamlit.web.cli as stcli
        import sys
        import os
        from pathlib import Path

        # Use enhanced UI with liquid-4g-core design
        ui_path = Path(__file__).parent / "interfaces" / "ui" / "ui.py"
        ui_dir = Path(__file__).parent / "interfaces" / "ui"
        
        # Change to UI directory for proper asset loading
        original_cwd = os.getcwd()
        os.chdir(ui_dir)
        
        sys.argv = ["streamlit", "run", "ui.py", "--server.port", "8502"]
        sys.exit(stcli.main())
    except ImportError:
        console.print("[bold red]❌ Streamlit not installed. Run: pip install liquid4g[ui][/bold red]")
    finally:
        # Restore original directory
        try:
            os.chdir(original_cwd)
        except:
            pass


@cli.command()
@click.option("--site-id", required=True, help="Site ID to optimize")
@click.option("--trigger", default="manual", help="Trigger reason")
def optimize(site_id: str, trigger: str):
    """Run optimization workflow for a site"""
    console.print(f"[bold blue]🤖 Starting optimization for site: {site_id}[/bold blue]")
    logger.info(f"Starting optimization: site={site_id}, trigger={trigger}")

    # TODO: Import and run orchestrator
    console.print("[yellow]⚠️ Orchestrator not yet implemented[/yellow]")


@cli.command()
def migrate():
    """Run database migrations"""
    console.print("[bold blue]🗄️ Running database migrations...[/bold blue]")

    try:
        from liquid4g.infrastructure.database.migrations import run_migrations

        run_migrations()
        console.print("[bold green]✅ Migrations completed successfully[/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Migration failed: {e}[/bold red]")
        logger.error(f"Migration failed: {e}")


@cli.command()
def test():
    """Run test suite"""
    console.print("[bold blue]🧪 Running tests...[/bold blue]")

    import pytest
    import sys

    sys.exit(pytest.main(["-v", "--cov=liquid4g"]))


def main():
    """Main entry point"""
    cli()


if __name__ == "__main__":
    main()
