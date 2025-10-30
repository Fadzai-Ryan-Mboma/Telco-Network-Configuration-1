#!/usr/bin/env python3
"""
Test exact API format from API Use.txt
"""

import requests
import json
import os
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Configuration  
HUAWEI_API_URL = "https://41.174.191.214:31127"
HUAWEI_USERNAME = "cassava.ai" 
HUAWEI_PASSWORD = "#Pass123#"

def authenticate():
    """Authenticate using exact format from API Use.txt"""
    url = f"{HUAWEI_API_URL}/api/rest/securityManagement/v1/oauth/token"

    payload = json.dumps({
        "grantType": "password",
        "userName": HUAWEI_USERNAME,
        "value": HUAWEI_PASSWORD
    })
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    response = requests.request("PUT", url, headers=headers, data=payload, verify=False)
    
    if response.status_code == 200:
        result = response.json()
        return result.get("accessSession")
    else:
        print(f"Authentication failed: {response.status_code} - {response.text}")
        return None

def test_mml_command(token):
    """Test MML command using exact format from API Use.txt"""
    url = f"{HUAWEI_API_URL}/api/rest/mmlManagement/v1/command"

    # Use exact payload format from API Use.txt
    payload = json.dumps({
        "command": "LST UECOOPERATIONPARA:;",
        "neNames": [
            "MSH-0112-Bindura Hospital"
        ]
    })
    
    headers = {
        'X-Auth-Token': token,
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    return response.status_code == 200

def main():
    print("🧪 Testing exact API Use.txt format")
    print("=" * 50)
    
    # Step 1: Authenticate
    print("🔐 Authenticating...")
    token = authenticate()
    
    if not token:
        print("❌ Authentication failed!")
        return
        
    print(f"✅ Authentication successful!")
    print(f"   Token: {token[:20]}...{token[-10:]}")
    print()
    
    # Step 2: Test MML command  
    print("📡 Testing MML command with exact API Use.txt format...")
    success = test_mml_command(token)
    
    if success:
        print("✅ MML command successful!")
    else:
        print("❌ MML command failed!")

if __name__ == "__main__":
    main()