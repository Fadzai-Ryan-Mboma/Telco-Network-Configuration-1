#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Network Optimizer
Phase 5 - Stage 5.1: API Connectivity Test (Postman Replication)

This script replicates Postman API tests in Python to troubleshoot
Huawei iMaster MAE API connectivity issues.

Test Suite:
1. TCP Connection Test
2. SSL Handshake Test
3. Authentication Endpoint Test
4. KPI Query Test
5. Parameter Query Test
6. MML Command Test

Usage:
    python3 test_api_postman_replication.py

Expected Environment Variables:
    HUAWEI_API_URL - Base URL (e.g., https://41.174.191.214:31127)
    HUAWEI_USERNAME - API username
    HUAWEI_PASSWORD - API password
"""

import os
import sys
import time
import json
import socket
import ssl
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
import urllib3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Suppress SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ANSI color codes for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.CYAN}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'=' * 80}{Colors.ENDC}\n")

def print_test(number: int, name: str):
    """Print test name"""
    print(f"\n{Colors.BLUE}Test {number}: {name}{Colors.ENDC}")
    print(f"{Colors.BLUE}{'-' * 80}{Colors.ENDC}")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ PASSED:{Colors.ENDC} {message}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  WARNING:{Colors.ENDC} {message}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}❌ FAILED:{Colors.ENDC} {message}")

def print_info(message: str):
    """Print info message"""
    print(f"   {message}")

class PostmanReplicationTest:
    """API connectivity test suite replicating Postman tests"""

    def __init__(self):
        """Initialize test suite"""
        self.base_url = os.getenv('HUAWEI_API_URL', '').rstrip('/')
        self.username = os.getenv('HUAWEI_USERNAME', '')
        self.password = os.getenv('HUAWEI_PASSWORD', '')

        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }

        self.access_token = None

    def validate_configuration(self) -> bool:
        """Validate environment variables are set"""
        print_test(0, "Configuration Validation")

        missing = []
        if not self.base_url:
            missing.append('HUAWEI_API_URL')
        if not self.username:
            missing.append('HUAWEI_USERNAME')
        if not self.password:
            missing.append('HUAWEI_PASSWORD')

        if missing:
            print_error(f"Missing environment variables: {', '.join(missing)}")
            print_info("Please set these variables before running tests:")
            print_info("  export HUAWEI_API_URL='https://41.174.191.214:31127'")
            print_info("  export HUAWEI_USERNAME='cassava.ai'")
            print_info("  export HUAWEI_PASSWORD='your_password'")
            return False

        print_success(f"API URL: {self.base_url}")
        print_success(f"Username: {self.username}")
        print_success(f"Password: {'*' * len(self.password)} (configured)")

        return True

    def test_tcp_connection(self) -> Dict[str, Any]:
        """Test 1: TCP Connection to API server"""
        print_test(1, "TCP Connection Test")

        test_result = {
            'test_name': 'TCP Connection',
            'status': 'unknown',
            'details': {}
        }

        try:
            # Parse URL to get hostname and port
            from urllib.parse import urlparse
            parsed_url = urlparse(self.base_url)
            hostname = parsed_url.hostname
            port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)

            print_info(f"Testing connection to {hostname}:{port}")

            # Test TCP connection
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)

            result = sock.connect_ex((hostname, port))
            connection_time = time.time() - start_time

            sock.close()

            if result == 0:
                test_result['status'] = 'pass'
                test_result['details'] = {
                    'hostname': hostname,
                    'port': port,
                    'connection_time': f"{connection_time:.3f}s"
                }
                print_success(f"TCP connection successful to {hostname}:{port}")
                print_success(f"Connection time: {connection_time:.3f}s")
            else:
                test_result['status'] = 'fail'
                test_result['details'] = {
                    'hostname': hostname,
                    'port': port,
                    'error_code': result
                }
                print_error(f"TCP connection failed (error code: {result})")
                print_info("Possible causes:")
                print_info("  - Server is down")
                print_info("  - Firewall blocking connection")
                print_info("  - Incorrect IP address or port")
                print_info("  - VPN required")

        except Exception as e:
            test_result['status'] = 'error'
            test_result['details'] = {'error': str(e)}
            print_error(f"TCP connection test error: {str(e)}")

        self.results['tests'].append(test_result)
        return test_result

    def test_ssl_handshake(self) -> Dict[str, Any]:
        """Test 2: SSL/TLS Handshake"""
        print_test(2, "SSL/TLS Handshake Test")

        test_result = {
            'test_name': 'SSL Handshake',
            'status': 'unknown',
            'details': {}
        }

        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(self.base_url)
            hostname = parsed_url.hostname
            port = parsed_url.port or 443

            print_info(f"Testing SSL handshake with {hostname}:{port}")

            # Create SSL context that accepts self-signed certificates
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            # Perform SSL handshake
            start_time = time.time()
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    handshake_time = time.time() - start_time

                    # Get certificate info
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()

                    test_result['status'] = 'pass'
                    test_result['details'] = {
                        'handshake_time': f"{handshake_time:.3f}s",
                        'ssl_version': ssock.version(),
                        'cipher': cipher[0] if cipher else 'unknown',
                        'self_signed': cert is None  # None when verify_mode is CERT_NONE
                    }

                    print_success(f"SSL handshake successful")
                    print_success(f"Handshake time: {handshake_time:.3f}s")
                    print_success(f"SSL version: {ssock.version()}")
                    print_success(f"Cipher: {cipher[0] if cipher else 'unknown'}")

                    if cert is None:
                        print_warning("Self-signed certificate detected (expected for Huawei iMaster MAE)")
                        print_info("SSL verification disabled (ssl_verify=False)")

        except Exception as e:
            test_result['status'] = 'error'
            test_result['details'] = {'error': str(e)}
            print_error(f"SSL handshake failed: {str(e)}")

        self.results['tests'].append(test_result)
        return test_result

    def test_authentication_endpoint(self) -> Dict[str, Any]:
        """Test 3: Authentication Endpoint"""
        print_test(3, "Authentication Endpoint Test")

        test_result = {
            'test_name': 'Authentication',
            'status': 'unknown',
            'details': {}
        }

        try:
            # CORRECT endpoint from Postman testing
            auth_url = f"{self.base_url}/api/rest/securityManagement/v1/oauth/token"
            print_info(f"Testing endpoint: {auth_url}")

            # Prepare authentication payload (matching Postman request EXACTLY)
            auth_payload = {
                "grantType": "password",
                "userName": self.username,
                "value": self.password
            }

            print_info(f"Payload: {json.dumps({**auth_payload, 'value': '***'}, indent=2)}")

            # Make authentication request (PUT method as per Postman)
            start_time = time.time()
            response = requests.put(
                auth_url,
                json=auth_payload,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                verify=False,  # Accept self-signed certificates
                timeout=10
            )
            response_time = time.time() - start_time

            test_result['details'] = {
                'url': auth_url,
                'status_code': response.status_code,
                'response_time': f"{response_time:.3f}s",
                'headers': dict(response.headers)
            }

            print_info(f"HTTP Status: {response.status_code}")
            print_info(f"Response time: {response_time:.3f}s")
            print_info(f"Response headers:")
            for key, value in response.headers.items():
                print_info(f"  {key}: {value}")

            # Check response
            if response.status_code == 200:
                try:
                    auth_data = response.json()

                    # Huawei uses 'accessSession' instead of 'access_token'
                    if 'accessSession' in auth_data:
                        self.access_token = auth_data['accessSession']

                        test_result['status'] = 'pass'
                        test_result['details']['access_token_length'] = len(self.access_token)
                        test_result['details']['expires'] = auth_data.get('expires', 'not_specified')
                        test_result['details']['roaRand'] = auth_data.get('roaRand', 'not_provided')

                        print_success("✅ Authentication successful!")
                        print_success(f"Access session token received (length: {len(self.access_token)} chars)")
                        print_success(f"Token expires in: {auth_data.get('expires', 'not specified')}s")

                        if 'roaRand' in auth_data:
                            print_success(f"ROA Random: {auth_data['roaRand']}")

                        print_info("")
                        print_info("Token details:")
                        print_info(f"  accessSession: {self.access_token[:50]}...")
                        print_info(f"  expires: {auth_data.get('expires')}s ({auth_data.get('expires', 0)/60:.1f} minutes)")
                    else:
                        test_result['status'] = 'fail'
                        test_result['details']['response_body'] = auth_data
                        print_error("No accessSession token in response")
                        print_info(f"Response body: {json.dumps(auth_data, indent=2)}")

                except json.JSONDecodeError:
                    test_result['status'] = 'fail'
                    test_result['details']['response_text'] = response.text[:500]
                    print_error("Response is not valid JSON")
                    print_info(f"Response text: {response.text[:500]}")

            elif response.status_code == 404:
                test_result['status'] = 'fail'
                test_result['details']['issue'] = 'endpoint_not_found'
                print_error("Authentication endpoint returns 404 (NOT FOUND)")
                print_warning("This is a KNOWN ISSUE from Phase 4 testing")
                print_info("Possible causes:")
                print_info("  - Incorrect auth endpoint path")
                print_info("  - API version mismatch (v1 vs v2)")
                print_info("  - Internal/development API with different structure")
                print_info("  - VPN required for access")
                print_info("")
                print_info("Recommended actions:")
                print_info("  1. Verify endpoint path with Huawei documentation")
                print_info("  2. Try alternative endpoints:")
                print_info("     - /api/v1/login")
                print_info("     - /rest/login")
                print_info("     - /auth/login")
                print_info("  3. Contact Huawei support for correct endpoint")
                print_info("  4. Check if VPN connection required")

            elif response.status_code == 401:
                test_result['status'] = 'fail'
                test_result['details']['issue'] = 'unauthorized'
                print_error("Authentication failed: Invalid credentials (401)")
                print_info("Please verify username and password are correct")

            else:
                test_result['status'] = 'fail'
                test_result['details']['response_text'] = response.text[:500]
                print_error(f"Unexpected HTTP status: {response.status_code}")
                print_info(f"Response: {response.text[:500]}")

        except requests.exceptions.Timeout:
            test_result['status'] = 'error'
            test_result['details'] = {'error': 'Request timeout (10s)'}
            print_error("Request timed out after 10 seconds")

        except requests.exceptions.ConnectionError as e:
            test_result['status'] = 'error'
            test_result['details'] = {'error': str(e)}
            print_error(f"Connection error: {str(e)}")
            print_info("Check if server is reachable and VPN is connected")

        except Exception as e:
            test_result['status'] = 'error'
            test_result['details'] = {'error': str(e)}
            print_error(f"Authentication test error: {str(e)}")

        self.results['tests'].append(test_result)
        return test_result

    def test_mml_query(self) -> Dict[str, Any]:
        """Test 4: MML Command Query (Read-Only)"""
        print_test(4, "MML Command Query Test")

        test_result = {
            'test_name': 'MML Query',
            'status': 'unknown',
            'details': {}
        }

        if not self.access_token:
            print_warning("Skipping MML query test (no access token)")
            print_info("Authentication must succeed before MML queries can be tested")
            test_result['status'] = 'skipped'
            test_result['details'] = {'reason': 'no_access_token'}
            self.results['tests'].append(test_result)
            return test_result

        try:
            # Use correct MML endpoint from API documentation
            mml_url = f"{self.base_url}/api/rest/mmlManagement/v1/command"
            print_info(f"Testing endpoint: {mml_url}")

            # Test with read-only LIST command for Bindura Hospital
            mml_payload = {
                "command": "LST UECOOPERATIONPARA:;",
                "neNames": ["MSH-0112-Bindura Hospital"]
            }

            print_info(f"Command: {mml_payload['command']}")
            print_info(f"Target site: {mml_payload['neNames'][0]}")

            # Make MML query request
            start_time = time.time()
            response = requests.post(
                mml_url,
                json=mml_payload,
                headers={
                    'X-Auth-Token': self.access_token,  # Correct Huawei header
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                verify=False,
                timeout=10
            )
            response_time = time.time() - start_time

            test_result['details'] = {
                'url': mml_url,
                'status_code': response.status_code,
                'response_time': f"{response_time:.3f}s",
                'command': mml_payload['command']
            }

            print_info(f"HTTP Status: {response.status_code}")
            print_info(f"Response time: {response_time:.3f}s")

            if response.status_code == 200:
                mml_result = response.json()

                test_result['status'] = 'pass'
                test_result['details']['result'] = mml_result

                print_success(f"✅ MML command executed successfully!")
                print_info("")
                print_info(f"Response structure:")
                for key in mml_result.keys():
                    print_info(f"  {key}: {type(mml_result[key]).__name__}")

                print_info("")
                print_info(f"Full response:")
                print_info(f"{json.dumps(mml_result, indent=2)[:500]}...")

            else:
                test_result['status'] = 'fail'
                print_error(f"MML query failed: HTTP {response.status_code}")
                print_info(f"Response: {response.text[:500]}")

        except Exception as e:
            test_result['status'] = 'error'
            test_result['details'] = {'error': str(e)}
            print_error(f"MML query test error: {str(e)}")

        self.results['tests'].append(test_result)
        return test_result

    def test_comparison_with_postman(self):
        """Compare Python test results with Postman results"""
        print_test(5, "Comparison with Postman Results")

        print_info("Comparing Python implementation with Postman:")
        print("")

        print_info("Expected Postman Results:")
        print_info("  ✅ TCP Connection: SUCCESS")
        print_info("  ✅ SSL Handshake: SUCCESS (self-signed cert)")
        print_info("  ⚠️  Authentication: 404 or SUCCESS (depending on endpoint)")
        print_info("  ⚠️  KPI Query: SUCCESS if authenticated")
        print("")

        print_info("Python Test Results:")
        for test in self.results['tests']:
            status_icon = {
                'pass': '✅',
                'fail': '❌',
                'error': '⚠️',
                'skipped': '⏭️',
                'unknown': '❓'
            }.get(test['status'], '❓')

            print_info(f"  {status_icon} {test['test_name']}: {test['status'].upper()}")

        print("")
        print_info("Recommendations:")

        # Generate recommendations based on test results
        auth_test = next((t for t in self.results['tests'] if t['test_name'] == 'Authentication'), None)

        if auth_test and auth_test['status'] == 'fail':
            if auth_test['details'].get('status_code') == 404:
                print_warning("Auth endpoint returns 404 - Contact Huawei support for correct endpoint")
                print_info("  System will fall back to database (as designed in Phase 4)")
            elif auth_test['details'].get('status_code') == 401:
                print_warning("Invalid credentials - Verify username and password")

        tcp_test = next((t for t in self.results['tests'] if t['test_name'] == 'TCP Connection'), None)
        if tcp_test and tcp_test['status'] == 'fail':
            print_warning("TCP connection failed - Check network connectivity and VPN")

    def generate_report(self) -> str:
        """Generate test report"""
        print_header("TEST REPORT SUMMARY")

        total_tests = len([t for t in self.results['tests'] if t['status'] != 'skipped'])
        passed_tests = len([t for t in self.results['tests'] if t['status'] == 'pass'])
        failed_tests = len([t for t in self.results['tests'] if t['status'] in ['fail', 'error']])

        print_info(f"Timestamp: {self.results['timestamp']}")
        print_info(f"Total Tests: {total_tests}")
        print_info(f"Passed: {passed_tests}")
        print_info(f"Failed: {failed_tests}")
        print_info(f"Pass Rate: {(passed_tests/total_tests*100) if total_tests > 0 else 0:.1f}%")
        print("")

        # Save report to file
        report_filename = f"reports/api_connectivity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            os.makedirs('reports', exist_ok=True)
            with open(report_filename, 'w') as f:
                json.dump(self.results, f, indent=2)

            print_success(f"Report saved to: {report_filename}")
        except Exception as e:
            print_warning(f"Could not save report: {str(e)}")

        return report_filename

    def run_all_tests(self):
        """Run all tests in sequence"""
        print_header("LIQUID ZIMBABWE 4G NETWORK OPTIMIZER - API CONNECTIVITY TEST SUITE")
        print_info("Phase 5 - Stage 5.1: Postman Replication Test")
        print_info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Validate configuration
        if not self.validate_configuration():
            print_error("Configuration validation failed. Exiting.")
            return False

        # Run test sequence
        self.test_tcp_connection()
        self.test_ssl_handshake()
        self.test_authentication_endpoint()
        self.test_mml_query()  # Changed from test_kpi_query
        self.test_comparison_with_postman()

        # Generate report
        self.generate_report()

        # Determine overall result
        failed_count = len([t for t in self.results['tests'] if t['status'] in ['fail', 'error']])

        if failed_count == 0:
            print_header("✅ ALL TESTS PASSED")
            return True
        else:
            print_header(f"⚠️ {failed_count} TEST(S) FAILED")
            return False

def main():
    """Main entry point"""
    tester = PostmanReplicationTest()
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
