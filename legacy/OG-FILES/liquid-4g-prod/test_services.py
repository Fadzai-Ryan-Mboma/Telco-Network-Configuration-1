#!/usr/bin/env python3
"""
Test Services Script

Verify that both UI and API are working correctly.
"""

import requests
import time

def test_services():
    """Test both API and UI services"""
    
    print("🧪 Testing Liquid 4G Services...")
    print("=" * 50)
    
    # Test API
    print("\n[1/2] Testing REST API...")
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        if response.status_code == 200:
            print("✅ API is running on http://localhost:8000")
        else:
            print(f"⚠️ API returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ API not running on http://localhost:8000")
        print("   Start with: python -m liquid4g api")
    except Exception as e:
        print(f"❌ API test failed: {e}")
    
    # Test API docs
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API docs available at http://localhost:8000/docs")
    except:
        print("⚠️ API docs not accessible")
    
    # Test UI
    print("\n[2/2] Testing Streamlit UI...")
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("✅ UI is running on http://localhost:8501")
        else:
            print(f"⚠️ UI returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ UI not running on http://localhost:8501")
        print("   Start with: streamlit run src/liquid4g/interfaces/ui/app.py")
    except Exception as e:
        print(f"❌ UI test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Service Test Complete!")
    print("\n📋 Quick Links:")
    print("   • Web UI:    http://localhost:8501")
    print("   • API Docs:  http://localhost:8000/docs")
    print("   • API Root:  http://localhost:8000")

if __name__ == "__main__":
    test_services()