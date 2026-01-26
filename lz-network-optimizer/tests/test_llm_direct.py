#!/usr/bin/env python3
"""
Quick LLM Test - Run directly to verify NVIDIA LLM is working
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.llm_factory import get_llm_client, get_llm_config
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

def main():
    print("\n" + "="*70)
    print("🧪 QUICK LLM TEST - NVIDIA Provider")
    print("="*70)
    
    # Test 1: Check config
    print("\n1️⃣  Checking configuration...")
    try:
        config = get_llm_config()
        provider = config.get('provider', 'NOT SET')
        print(f"   ✅ Provider configured: {provider}")
        
        if provider != 'nvidia':
            print(f"   ⚠️  WARNING: Provider is set to '{provider}' but should be 'nvidia'")
    except Exception as e:
        print(f"   ❌ Config error: {e}")
        return 1
    
    # Test 2: Check API key
    print("\n2️⃣  Checking API key...")
    nvidia_key = os.getenv('NVIDIA_API_KEY')
    if nvidia_key:
        print(f"   ✅ NVIDIA_API_KEY is set")
        print(f"   Value: {nvidia_key[:10]}...{nvidia_key[-4:]}")
    else:
        print(f"   ❌ NVIDIA_API_KEY is NOT set")
        return 1
    
    # Test 3: Initialize LLM
    print("\n3️⃣  Initializing NVIDIA LLM...")
    try:
        llm = get_llm_client()
        print(f"   ✅ LLM initialized successfully")
        print(f"   Type: {type(llm).__name__}")
        print(f"   Model: {getattr(llm, 'model', 'unknown')}")
    except Exception as e:
        print(f"   ❌ LLM initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Test 4: Simple LLM call
    print("\n4️⃣  Testing LLM call...")
    try:
        messages = [HumanMessage(content="Respond with exactly: 'LLM is working correctly!'")]
        print("   Sending test message...")
        response = llm.invoke(messages)
        print(f"   ✅ LLM responded!")
        print(f"   Response: {response.content}")
    except Exception as e:
        print(f"   ❌ LLM call failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Test 5: Test with a more complex prompt
    print("\n5️⃣  Testing with technical prompt...")
    try:
        messages = [HumanMessage(content="""You are a network optimization expert.
        
Analyze this scenario:
- Site: MSH-0014-Chipadze
- Average Download Speed: 45 Mbps (threshold: 50 Mbps)
- Network Access Success: 96.5%

What is the PRIMARY issue? Respond with ONE of these:
- low_download_speed
- low_network_access_success
- no_issue
""")]
        print("   Sending technical prompt...")
        response = llm.invoke(messages)
        print(f"   ✅ LLM responded!")
        print(f"   Response: {response.content[:200]}...")
    except Exception as e:
        print(f"   ❌ LLM call failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "="*70)
    print("🎉 ALL TESTS PASSED! NVIDIA LLM is working correctly!")
    print("="*70)
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
