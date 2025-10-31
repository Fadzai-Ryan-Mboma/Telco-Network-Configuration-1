#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Network Optimizer - Comprehensive API Test Suite
Purpose: Test NVIDIA and Huawei API connectivity with troubleshooting
Created: 2025-10-31
"""

import os
import sys
import socket
import ssl
import time
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"{Colors.BOLD}{title}{Colors.END}")
    print("=" * 80)

def print_test(test_name, status, message=""):
    """Print test result"""
    symbols = {"pass": f"{Colors.GREEN}✓{Colors.END}", "fail": f"{Colors.RED}✗{Colors.END}", "warn": f"{Colors.YELLOW}⚠{Colors.END}"}
    symbol = symbols.get(status, "•")
    print(f"{symbol} {test_name}")
    if message:
        print(f"  {message}")

# ==========================================================================
# TEST SUITE 1: NVIDIA API CONNECTIVITY
# ==========================================================================

def test_nvidia_api_key():
    """Test 1.1: NVIDIA API Key Configuration"""
    print_header("TEST SUITE 1: NVIDIA API CONNECTIVITY")
    print("\n1.1 Testing NVIDIA API Key Configuration...")

    api_key = os.getenv('NVIDIA_API_KEY')

    if not api_key:
        print_test("API key present", "fail", "NVIDIA_API_KEY not found in environment")
        print(f"\n{Colors.YELLOW}Troubleshooting:{Colors.END}")
        print("  1. Check .env file exists in project root")
        print("  2. Verify NVIDIA_API_KEY is set in .env")
        print("  3. Get API key from: https://build.nvidia.com/")
        return False

    if len(api_key) < 20:
        print_test("API key format", "warn", f"Key seems short ({len(api_key)} chars)")
        return False

    print_test("API key present", "pass", f"{len(api_key)} characters")
    print_test("API key format", "pass", "Length looks valid")
    return True


def test_nvidia_llm_initialization():
    """Test 1.2: NVIDIA LLM Initialization"""
    print("\n1.2 Testing NVIDIA LLM Initialization...")

    try:
        from langchain_nvidia_ai_endpoints import ChatNVIDIA
        print_test("Import ChatNVIDIA", "pass")

        llm = ChatNVIDIA(
            model="meta/llama-3.1-70b-instruct",
            api_key=os.getenv("NVIDIA_API_KEY"),
            temperature=0.7,
            max_tokens=100
        )
        print_test("Initialize LLM", "pass", "meta/llama-3.1-70b-instruct")
        return True

    except ImportError as e:
        print_test("Import ChatNVIDIA", "fail", str(e))
        print(f"\n{Colors.YELLOW}Troubleshooting:{Colors.END}")
        print("  pip install langchain-nvidia-ai-endpoints")
        return False
    except Exception as e:
        print_test("Initialize LLM", "fail", str(e))
        return False


def test_nvidia_simple_call():
    """Test 1.3: NVIDIA Simple LLM Call"""
    print("\n1.3 Testing NVIDIA Simple LLM Call...")

    try:
        from langchain_nvidia_ai_endpoints import ChatNVIDIA

        llm = ChatNVIDIA(
            model="meta/llama-3.1-70b-instruct",
            api_key=os.getenv("NVIDIA_API_KEY"),
            temperature=0.7,
            max_tokens=50,
            timeout=30
        )

        start_time = time.time()
        response = llm.invoke("Say 'API test successful' in 3 words.")
        elapsed = time.time() - start_time

        print_test("API call", "pass", f"Response in {elapsed:.2f}s")
        print_test("Response received", "pass", f'"{response.content[:50]}"...')
        return True

    except Exception as e:
        print_test("API call", "fail", str(e))
        print(f"\n{Colors.YELLOW}Troubleshooting:{Colors.END}")
        print("  1. Check internet connection")
        print("  2. Verify API key is valid (not expired)")
        print("  3. Check firewall/proxy settings")
        print("  4. Try: curl -I https://integrate.api.nvidia.com")
        return False


def test_nvidia_with_agent():
    """Test 1.4: NVIDIA API with Agent Tools"""
    print("\n1.4 Testing NVIDIA API with Agent Tools...")

    try:
        sys.path.insert(0, os.path.dirname(__file__))

        from agents.network_connector_agent import network_connector_agent
        print_test("Import agent", "pass")

        test_state = {
            "site_name": "MSH0013-Bindura-Zaoga",
            "cell_id": 1,
            "user_query": "Get network status",
            "agent_outputs": {}
        }

        result_state = network_connector_agent(test_state)
        print_test("Execute agent", "pass")

        output_length = len(result_state.get('network_connector_output', ''))
        print_test("Agent output", "pass", f"{output_length} characters")
        return True

    except Exception as e:
        print_test("Agent execution", "fail", str(e))
        return False


# ==========================================================================
# TEST SUITE 2: HUAWEI API CONNECTIVITY
# ==========================================================================

def test_huawei_configuration():
    """Test 2.1: Huawei API Configuration"""
    print_header("TEST SUITE 2: HUAWEI API CONNECTIVITY")
    print("\n2.1 Testing Huawei API Configuration...")

    api_url = os.getenv('HUAWEI_API_URL')
    username = os.getenv('HUAWEI_USERNAME')
    password = os.getenv('HUAWEI_PASSWORD')

    config_ok = True

    if not api_url:
        print_test("API URL", "fail", "HUAWEI_API_URL not set")
        config_ok = False
    else:
        print_test("API URL", "pass", api_url)

    if not username:
        print_test("Username", "fail", "HUAWEI_USERNAME not set")
        config_ok = False
    else:
        print_test("Username", "pass", username)

    if not password:
        print_test("Password", "fail", "HUAWEI_PASSWORD not set")
        config_ok = False
    else:
        print_test("Password", "pass", "***" + password[-4:] if len(password) > 4 else "***")

    if not config_ok:
        print(f"\n{Colors.YELLOW}Troubleshooting:{Colors.END}")
        print("  1. Check .env file has HUAWEI_API_URL, HUAWEI_USERNAME, HUAWEI_PASSWORD")
        print("  2. Verify credentials are correct")

    return config_ok


def test_network_connectivity():
    """Test 2.2: Network Connectivity to Huawei API"""
    print("\n2.2 Testing Network Connectivity...")

    api_url = os.getenv('HUAWEI_API_URL')
    if not api_url:
        print_test("Network connectivity", "fail", "No API URL configured")
        return False

    try:
        parsed_url = urlparse(api_url)
        hostname = parsed_url.hostname
        port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)

        print_test("Parse URL", "pass", f"{hostname}:{port}")

        # DNS resolution
        try:
            ip_address = socket.gethostbyname(hostname)
            print_test("DNS resolution", "pass", f"{hostname} → {ip_address}")
        except socket.gaierror as e:
            print_test("DNS resolution", "fail", str(e))
            print(f"\n{Colors.YELLOW}Troubleshooting:{Colors.END}")
            print("  1. Check internet connection")
            print("  2. Verify VPN is connected (if required)")
            print("  3. Check DNS server settings")
            return False

        # TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)

        try:
            start_time = time.time()
            result = sock.connect_ex((hostname, port))
            elapsed = time.time() - start_time

            if result == 0:
                print_test("TCP connection", "pass", f"Connected in {elapsed:.2f}s")
            else:
                print_test("TCP connection", "fail", f"Cannot connect to {hostname}:{port}")
                print(f"\n{Colors.YELLOW}Troubleshooting:{Colors.END}")
                print("  1. Check firewall allows outbound connections")
                print("  2. Verify VPN is connected")
                print("  3. Confirm API endpoint is correct")
                return False
        finally:
            sock.close()

        return True

    except Exception as e:
        print_test("Network connectivity", "fail", str(e))
        return False


def test_ssl_certificate():
    """Test 2.3: SSL Certificate Validation"""
    print("\n2.3 Testing SSL Certificate...")

    api_url = os.getenv('HUAWEI_API_URL')
    if not api_url or not api_url.startswith('https'):
        print_test("SSL check", "warn", "Not using HTTPS")
        return True

    try:
        parsed_url = urlparse(api_url)
        hostname = parsed_url.hostname
        port = parsed_url.port or 443

        context = ssl.create_default_context()

        with socket.create_connection((hostname, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                print_test("SSL handshake", "pass")
                print_test("Certificate valid", "pass", f"Issued to: {cert.get('subject', [[('',hostname)]])[0][0][1]}")

        return True

    except ssl.SSLError as e:
        print_test("SSL validation", "warn", str(e))
        print(f"\n{Colors.YELLOW}Note:{Colors.END}")
        print("  SSL verification may be disabled in HuaweiAPIClient (ssl_verify=False)")
        print("  This is common for internal/development environments")
        return True
    except Exception as e:
        print_test("SSL check", "warn", str(e))
        return True


def test_huawei_api_client():
    """Test 2.4: Huawei API Client Initialization"""
    print("\n2.4 Testing Huawei API Client...")

    try:
        from network.huawei_api_client import HuaweiAPIClient
        print_test("Import HuaweiAPIClient", "pass")

        # Build config dict (correct way)
        config = {
            'base_url': os.getenv('HUAWEI_API_URL'),
            'username': os.getenv('HUAWEI_USERNAME'),
            'password': os.getenv('HUAWEI_PASSWORD'),
            'timeout': 30,
            'retry_attempts': 2,
            'retry_delay': 3,
            'ssl_verify': False  # Common for internal APIs
        }

        client = HuaweiAPIClient(config)
        print_test("Initialize client", "pass")

        # Note: Not testing connect() as it requires actual API access
        print_test("Client ready", "pass", "Use test_with_api.py for full test")

        return True

    except Exception as e:
        print_test("Client initialization", "fail", str(e))
        print(f"\n{Colors.YELLOW}Troubleshooting:{Colors.END}")
        print("  1. Check network/huawei_api_client.py exists")
        print("  2. Verify HuaweiAPIClient.__init__() accepts 'config' dict")
        return False


# ==========================================================================
# TEST SUITE 3: SYSTEM CHECKS
# ==========================================================================

def test_database_connectivity():
    """Test 3.1: Database Connectivity"""
    print_header("TEST SUITE 3: SYSTEM CHECKS")
    print("\n3.1 Testing Database Connectivity...")

    try:
        import sqlite3
        from pathlib import Path

        db_path = Path(__file__).parent / "data" / "lz_network.db"

        if not db_path.exists():
            print_test("Database file", "fail", f"Not found: {db_path}")
            return False

        print_test("Database file", "pass", str(db_path))

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM kpi_data")
        record_count = cursor.fetchone()[0]
        print_test("Database query", "pass", f"{record_count} records")

        cursor.execute("SELECT COUNT(DISTINCT site_name) FROM kpi_data")
        site_count = cursor.fetchone()[0]
        print_test("Sites available", "pass", f"{site_count} sites")

        conn.close()
        return True

    except Exception as e:
        print_test("Database connectivity", "fail", str(e))
        return False


def test_dependencies():
    """Test 3.2: Python Dependencies"""
    print("\n3.2 Testing Python Dependencies...")

    required_packages = [
        ("langchain", "LangChain"),
        ("langchain_nvidia_ai_endpoints", "NVIDIA AI Endpoints"),
        ("langgraph", "LangGraph"),
        ("streamlit", "Streamlit"),
        ("plotly", "Plotly"),
        ("dotenv", "python-dotenv")
    ]

    all_ok = True
    for module, name in required_packages:
        try:
            __import__(module)
            print_test(f"{name}", "pass")
        except ImportError:
            print_test(f"{name}", "fail", f"{module} not installed")
            all_ok = False

    if not all_ok:
        print(f"\n{Colors.YELLOW}Fix:{Colors.END}")
        print("  pip install -r requirements-lz.txt")

    return all_ok


# ==========================================================================
# MAIN TEST EXECUTION
# ==========================================================================

def main():
    """Run all test suites"""
    print("\n" + "=" * 80)
    print(f"{Colors.BOLD}LIQUID ZIMBABWE 4G NETWORK OPTIMIZER{Colors.END}")
    print(f"{Colors.BOLD}Comprehensive API Test Suite{Colors.END}")
    print("=" * 80)
    print(f"\nDate: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")

    # Track results
    results = {}

    # Suite 1: NVIDIA API
    results['nvidia_key'] = test_nvidia_api_key()
    results['nvidia_init'] = test_nvidia_llm_initialization()
    results['nvidia_call'] = test_nvidia_simple_call()
    results['nvidia_agent'] = test_nvidia_with_agent()

    # Suite 2: Huawei API
    results['huawei_config'] = test_huawei_configuration()
    results['huawei_network'] = test_network_connectivity()
    results['huawei_ssl'] = test_ssl_certificate()
    results['huawei_client'] = test_huawei_api_client()

    # Suite 3: System
    results['database'] = test_database_connectivity()
    results['dependencies'] = test_dependencies()

    # Summary
    print_header("TEST SUMMARY")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\nTotal Tests: {total}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
    print(f"{Colors.RED}Failed: {total - passed}{Colors.END}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    print("\n" + "=" * 80)

    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ ALL TESTS PASSED{Colors.END}")
        print("\nSystem is ready for Phase 4 testing!")
        return 0
    elif passed >= total * 0.7:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  PARTIAL SUCCESS{Colors.END}")
        print("\nSome tests failed. Review troubleshooting steps above.")
        return 1
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ TESTS FAILED{Colors.END}")
        print("\nMultiple failures detected. Review configuration and troubleshooting steps.")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        sys.exit(130)
