#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Network Optimizer - Pre-Flight Test Script
Purpose: Quick validation before Phase 4 testing
Created: 2025-10-31
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    END = '\033[0m'

def check_streamlit_running():
    """Check if Streamlit UI is running on port 8501"""
    print("\n1. Checking Streamlit UI...")

    try:
        # Check if port 8501 is in use
        result = subprocess.run(
            ["lsof", "-ti:8501"],
            capture_output=True,
            text=True
        )

        if result.stdout.strip():
            pid = result.stdout.strip().split('\n')[0]
            print(f"   {Colors.GREEN}✓{Colors.END} Streamlit running (PID: {pid})")
            print(f"   {Colors.GREEN}✓{Colors.END} UI accessible at: http://localhost:8501")
            return True
        else:
            print(f"   {Colors.YELLOW}⚠{Colors.END} Streamlit not running on port 8501")
            print("   To start: streamlit run ui/app.py")
            return False

    except Exception as e:
        print(f"   {Colors.RED}✗{Colors.END} Cannot check Streamlit status: {e}")
        return False


def check_nvidia_api_key():
    """Check NVIDIA API key configuration"""
    print("\n2. Checking NVIDIA API Key...")

    api_key = os.getenv('NVIDIA_API_KEY')

    if not api_key:
        print(f"   {Colors.RED}✗{Colors.END} NVIDIA_API_KEY not found")
        print("   Set in .env file")
        return False

    print(f"   {Colors.GREEN}✓{Colors.END} API key configured ({len(api_key)} characters)")
    return True


def check_database():
    """Check database exists and has data"""
    print("\n3. Checking Database...")

    db_path = Path(__file__).parent / "data" / "lz_network.db"

    if not db_path.exists():
        print(f"   {Colors.RED}✗{Colors.END} Database not found: {db_path}")
        return False

    print(f"   {Colors.GREEN}✓{Colors.END} Database file exists")

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check records
        cursor.execute("SELECT COUNT(*) FROM kpi_data")
        record_count = cursor.fetchone()[0]

        # Check sites
        cursor.execute("SELECT COUNT(DISTINCT site_name) FROM kpi_data")
        site_count = cursor.fetchone()[0]

        conn.close()

        if record_count < 100:
            print(f"   {Colors.YELLOW}⚠{Colors.END} Low record count: {record_count}")
        else:
            print(f"   {Colors.GREEN}✓{Colors.END} {record_count} records found")

        print(f"   {Colors.GREEN}✓{Colors.END} {site_count} sites available")
        return True

    except Exception as e:
        print(f"   {Colors.RED}✗{Colors.END} Database query failed: {e}")
        return False


def check_imports():
    """Check Python module imports"""
    print("\n4. Checking Python Imports...")

    modules = [
        ("ui.database_helper", "Database Helper"),
        ("ui.workflow_interface", "Workflow Interface"),
        ("streamlit", "Streamlit"),
        ("plotly", "Plotly"),
        ("langchain_nvidia_ai_endpoints", "NVIDIA AI Endpoints")
    ]

    all_ok = True
    for module, name in modules:
        try:
            __import__(module)
            print(f"   {Colors.GREEN}✓{Colors.END} {name}")
        except ImportError as e:
            print(f"   {Colors.RED}✗{Colors.END} {name}: {e}")
            all_ok = False

    return all_ok


def check_docker():
    """Check Docker availability"""
    print("\n5. Checking Docker...")

    docker_path = "/Applications/Docker.app/Contents/Resources/bin/docker"

    if not Path(docker_path).exists():
        print(f"   {Colors.YELLOW}⚠{Colors.END} Docker not found at {docker_path}")
        print("   (Optional - not required for UI testing)")
        return False

    try:
        result = subprocess.run(
            [docker_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"   {Colors.GREEN}✓{Colors.END} {version}")

            # Check if Docker Desktop is running
            result = subprocess.run(
                [docker_path, "info"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                print(f"   {Colors.GREEN}✓{Colors.END} Docker Desktop is running")
            else:
                print(f"   {Colors.YELLOW}⚠{Colors.END} Docker Desktop not running")

            return True
        else:
            print(f"   {Colors.RED}✗{Colors.END} Docker command failed")
            return False

    except Exception as e:
        print(f"   {Colors.YELLOW}⚠{Colors.END} Docker check failed: {e}")
        return False


def main():
    """Run all pre-flight checks"""
    print("=" * 80)
    print(f"{Colors.BOLD}LIQUID ZIMBABWE 4G NETWORK OPTIMIZER{Colors.END}")
    print(f"{Colors.BOLD}Pre-Flight Checks - Phase 4{Colors.END}")
    print("=" * 80)

    results = []

    # Run checks
    results.append(("Streamlit UI", check_streamlit_running()))
    results.append(("NVIDIA API Key", check_nvidia_api_key()))
    results.append(("Database", check_database()))
    results.append(("Python Imports", check_imports()))
    results.append(("Docker", check_docker()))

    # Summary
    print("\n" + "=" * 80)
    print(f"{Colors.BOLD}SUMMARY{Colors.END}")
    print("=" * 80)

    passed = sum(1 for _, status in results if status)
    total = len(results)

    for name, status in results:
        symbol = f"{Colors.GREEN}✓{Colors.END}" if status else f"{Colors.RED}✗{Colors.END}"
        print(f"{symbol} {name}")

    print(f"\n{passed}/{total} checks passed")

    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ SYSTEM READY FOR PHASE 4 TESTING{Colors.END}")
        return 0
    elif passed >= total - 1:  # Docker is optional
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ SYSTEM READY (optional checks failed){Colors.END}")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ SYSTEM NOT READY{Colors.END}")
        print("\nPlease fix failed checks before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
