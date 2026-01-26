#!/usr/bin/env python3
"""
Test NVIDIA LLM Connectivity
Purpose: Verify that NVIDIA Nemotron-4-340B is reachable and working
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_nvidia_api_key():
    """Check if API key is set"""
    print("\n" + "="*70)
    print("✓ TEST 1: NVIDIA API Key")
    print("="*70)
    
    api_key = os.getenv('NVIDIA_API_KEY')
    if api_key:
        print(f"✅ NVIDIA_API_KEY is set")
        print(f"   Value: {api_key[:20]}...{api_key[-10:]}")
        return True
    else:
        print(f"❌ NVIDIA_API_KEY is NOT set")
        return False

def test_nvidia_endpoint():
    """Test connectivity to NVIDIA API endpoint"""
    print("\n" + "="*70)
    print("✓ TEST 2: NVIDIA API Endpoint Connectivity")
    print("="*70)
    
    api_key = os.getenv('NVIDIA_API_KEY')
    if not api_key:
        print("❌ Cannot test - NVIDIA_API_KEY not set")
        return False
    
    url = "https://integrate.api.nvidia.com/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"   Testing: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Successfully connected to NVIDIA API")
            print(f"   Status Code: {response.status_code}")
            models = response.json()
            print(f"   Available models: {len(models.get('data', []))} found")
            return True
        else:
            print(f"❌ NVIDIA API returned error")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Request timeout (10s) - API may be slow or unreachable")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_llm_factory():
    """Test LLM factory initialization"""
    print("\n" + "="*70)
    print("✓ TEST 3: LLM Factory Initialization")
    print("="*70)
    
    try:
        from utils.llm_factory import get_llm_client
        
        llm = get_llm_client()
        print(f"✅ LLM client created successfully")
        print(f"   Type: {type(llm).__name__}")
        print(f"   Model: {llm.model_name if hasattr(llm, 'model_name') else llm.model}")
        return True
    except Exception as e:
        print(f"❌ LLM factory initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_llm_call():
    """Test a simple LLM API call"""
    print("\n" + "="*70)
    print("✓ TEST 4: Simple LLM API Call")
    print("="*70)
    
    try:
        from utils.llm_factory import get_llm_client
        
        llm = get_llm_client()
        
        print("   Sending test prompt: 'Say hello in one word'")
        response = llm.invoke("Say hello in one word")
        
        print(f"✅ LLM API call successful!")
        print(f"   Response: {response.content}")
        return True
    except Exception as e:
        print(f"❌ LLM API call failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🧪 NVIDIA LLM CONNECTIVITY TEST SUITE")
    print("="*70)
    
    results = []
    
    # Run tests
    results.append(("API Key Check", test_nvidia_api_key()))
    results.append(("Endpoint Connectivity", test_nvidia_endpoint()))
    results.append(("LLM Factory Init", test_llm_factory()))
    results.append(("Simple LLM Call", test_simple_llm_call()))
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - NVIDIA LLM IS REACHABLE AND WORKING!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed - Check configuration and API key")
        return 1

if __name__ == "__main__":
    sys.exit(main())
