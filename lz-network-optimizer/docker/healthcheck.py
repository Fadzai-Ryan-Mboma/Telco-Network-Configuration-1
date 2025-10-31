#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Network Optimizer - Docker Health Check
Purpose: Validate container health for Docker/Kubernetes monitoring
Exit Codes:
    0 = Healthy
    1 = Unhealthy
"""

import sys
import os
from pathlib import Path

# ============================================================================
# Health Check Functions
# ============================================================================

def check_python_imports():
    """Verify critical Python packages can be imported."""
    try:
        import langchain
        import langgraph
        import langchain_nvidia_ai_endpoints
        from dotenv import load_dotenv
        import sqlite3
        return True, "Python imports OK"
    except ImportError as e:
        return False, f"Import error: {str(e)}"


def check_environment_variables():
    """Verify required environment variables are set."""
    required_vars = ["NVIDIA_API_KEY"]
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        return False, f"Missing environment variables: {', '.join(missing_vars)}"
    return True, "Environment variables OK"


def check_database_connectivity():
    """Verify database files exist and are accessible."""
    try:
        import sqlite3

        # Check for database files
        db_paths = [
            Path("/app/data/lz_network.db"),
            Path("/app/data/liquid_zimbabwe.db"),
            Path("/app/data/live_network.db")
        ]

        accessible_dbs = []
        for db_path in db_paths:
            if db_path.exists():
                # Try to connect
                try:
                    conn = sqlite3.connect(str(db_path))
                    conn.close()
                    accessible_dbs.append(db_path.name)
                except sqlite3.Error:
                    pass

        if accessible_dbs:
            return True, f"Database OK: {', '.join(accessible_dbs)}"
        else:
            return False, "No accessible databases found"

    except Exception as e:
        return False, f"Database check error: {str(e)}"


def check_application_structure():
    """Verify critical application directories exist."""
    required_dirs = [
        Path("/app/agents"),
        Path("/app/tools"),
        Path("/app/prompts"),
        Path("/app/domain"),
        Path("/app/network"),
    ]

    missing_dirs = []
    for dir_path in required_dirs:
        if not dir_path.exists():
            missing_dirs.append(str(dir_path))

    if missing_dirs:
        return False, f"Missing directories: {', '.join(missing_dirs)}"
    return True, "Application structure OK"


def check_main_entry_point():
    """Verify main.py exists and is executable."""
    main_py = Path("/app/main.py")
    if not main_py.exists():
        return False, "main.py not found"
    if not os.access(str(main_py), os.R_OK):
        return False, "main.py not readable"
    return True, "Entry point OK"


# ============================================================================
# Main Health Check
# ============================================================================

def main():
    """Run all health checks and report status."""
    checks = [
        ("Python Imports", check_python_imports),
        ("Environment Variables", check_environment_variables),
        ("Database Connectivity", check_database_connectivity),
        ("Application Structure", check_application_structure),
        ("Entry Point", check_main_entry_point),
    ]

    all_passed = True
    results = []

    for check_name, check_func in checks:
        try:
            passed, message = check_func()
            status = "✓" if passed else "✗"
            results.append(f"{status} {check_name}: {message}")
            if not passed:
                all_passed = False
        except Exception as e:
            results.append(f"✗ {check_name}: Exception - {str(e)}")
            all_passed = False

    # Print results (will appear in Docker logs)
    if all_passed:
        print("HEALTHY: All checks passed")
        for result in results:
            print(f"  {result}")
        sys.exit(0)
    else:
        print("UNHEALTHY: Some checks failed")
        for result in results:
            print(f"  {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()
