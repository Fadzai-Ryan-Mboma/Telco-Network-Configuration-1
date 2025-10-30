#!/usr/bin/env python3
"""
Test different Huawei API endpoint variations to find the correct MML endpoint
"""

import requests
import os
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Configuration
HUAWEI_API_URL = os.environ.get('HUAWEI_API_URL', 'https://41.174.191.214:31127')
HUAWEI_USERNAME = os.environ.get('HUAWEI_USERNAME', 'cassava.ai')
HUAWEI_PASSWORD = os.environ.get('HUAWEI_PASSWORD', '#Pass123#')

def authenticate():
    """Get authentication token"""
    auth_url = f"{HUAWEI_API_URL}/api/rest/securityManagement/v1/oauth/token"
    
    payload = {
        "grantType": "password",
        "userName": HUAWEI_USERNAME,
        "value": HUAWEI_PASSWORD
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    response = requests.put(auth_url, json=payload, headers=headers, verify=False, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        return data.get("accessSession")
    else:
        print(f"Authentication failed: {response.status_code} - {response.text}")
        return None

def test_endpoint(token, endpoint_url, method="POST", payload=None):
    """Test if an endpoint exists and responds"""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "accessSession": token
    }
    
    try:
        if method == "POST":
            response = requests.post(endpoint_url, json=payload, headers=headers, verify=False, timeout=10)
        elif method == "GET":
            response = requests.get(endpoint_url, headers=headers, verify=False, timeout=10)
        
        print(f"  {method} {endpoint_url}")
        print(f"    Status: {response.status_code}")
        if response.status_code < 500:  # Don't print server error details
            print(f"    Response: {response.text[:200]}...")
        print()
        
        return response.status_code, response.text
        
    except Exception as e:
        print(f"  {method} {endpoint_url}")
        print(f"    Error: {str(e)}")
        print()
        return None, str(e)

def main():
    print("🔍 Testing Huawei API Endpoints")
    print("=" * 50)
    
    # Authenticate first
    token = authenticate()
    if not token:
        print("❌ Authentication failed!")
        return
    
    print(f"✅ Authentication successful! Token: {token[:20]}...")
    print()
    
    # Test payload for MML commands
    mml_payload = {"command": "DSP VERSION;"}
    
    # List of endpoint variations to test
    endpoints_to_test = [
        # Original endpoints from liquid-4g-core
        ("/rest-oss/rest/mml/v1/execute", "POST", mml_payload),
        
        # Alternative MML endpoints
        ("/api/rest/mmlManagement/v1/execute", "POST", mml_payload),
        ("/api/rest/mmlManagement/v1/command", "POST", mml_payload),
        ("/api/rest/mml/v1/execute", "POST", mml_payload),
        ("/api/rest/mml/v1/command", "POST", mml_payload),
        
        # REST endpoints
        ("/rest/mml/v1/execute", "POST", mml_payload),
        ("/rest/mml/v1/command", "POST", mml_payload),
        
        # Alternative patterns
        ("/rest-oss/mml/v1/execute", "POST", mml_payload),
        ("/rest-oss/api/mml/v1/execute", "POST", mml_payload),
        
        # Different versions
        ("/rest-oss/rest/mml/v2/execute", "POST", mml_payload),
        ("/api/rest/mmlManagement/v2/execute", "POST", mml_payload),
        
        # Discovery endpoints
        ("/api", "GET", None),
        ("/rest", "GET", None),
        ("/rest-oss", "GET", None),
        ("/api/rest", "GET", None),
    ]
    
    print("🧪 Testing endpoint variations:")
    print()
    
    for endpoint_path, method, payload in endpoints_to_test:
        full_url = f"{HUAWEI_API_URL}{endpoint_path}"
        test_endpoint(token, full_url, method, payload)

if __name__ == "__main__":
    main()