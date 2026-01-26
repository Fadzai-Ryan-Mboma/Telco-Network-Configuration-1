#!/usr/bin/env python3
"""
LLM Connection Test Script
Purpose: Test LLM factory and verify API connectivity
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.llm_factory import get_llm_client, get_llm_config, list_available_providers
from dotenv import load_dotenv

load_dotenv()

def test_llm_config():
    """Test LLM configuration loading"""
    print("\n" + "="*70)
    print("🧪 TEST 1: LLM Configuration")
    print("="*70)
    
    try:
        config = get_llm_config()
        print(f"✅ Config loaded successfully")
        print(f"   Provider: {config.get('provider', 'NOT SET')}")
        print(f"   OpenAI model: {config.get('openai', {}).get('model', 'NOT SET')}")
        print(f"   NVIDIA model: {config.get('nvidia', {}).get('model', 'NOT SET')}")
        return True
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False


def test_environment_variables():
    """Test if API keys are present"""
    print("\n" + "="*70)
    print("🧪 TEST 2: Environment Variables")
    print("="*70)
    
    openai_key = os.getenv('OPENAI_API_KEY')
    nvidia_key = os.getenv('NVIDIA_API_KEY')
    
    print(f"   OPENAI_API_KEY: {'✅ SET' if openai_key else '❌ NOT SET'}")
    if openai_key:
        print(f"   Value: {openai_key[:10]}...{openai_key[-4:]}")
    
    print(f"   NVIDIA_API_KEY: {'✅ SET' if nvidia_key else '❌ NOT SET'}")
    if nvidia_key:
        print(f"   Value: {nvidia_key[:10]}...{nvidia_key[-4:]}")
    
    return openai_key or nvidia_key


def test_available_providers():
    """Test which providers are available"""
    print("\n" + "="*70)
    print("🧪 TEST 3: Available Providers")
    print("="*70)
    
    try:
        providers = list_available_providers()
        if providers:
            print(f"✅ Available providers: {', '.join(providers)}")
        else:
            print(f"❌ No providers available (missing API keys)")
        return len(providers) > 0
    except Exception as e:
        print(f"❌ Error listing providers: {e}")
        return False


def test_llm_initialization(provider=None):
    """Test LLM client initialization"""
    provider_str = provider if provider else "default"
    print("\n" + "="*70)
    print(f"🧪 TEST 4: LLM Initialization ({provider_str})")
    print("="*70)
    
    try:
        llm = get_llm_client(provider=provider)
        print(f"✅ LLM client created successfully")
        print(f"   Type: {type(llm).__name__}")
        print(f"   Model: {getattr(llm, 'model_name', getattr(llm, 'model', 'unknown'))}")
        return True
    except Exception as e:
        print(f"❌ LLM initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_simple_call(provider=None):
    """Test a simple LLM call"""
    provider_str = provider if provider else "default"
    print("\n" + "="*70)
    print(f"🧪 TEST 5: Simple LLM Call ({provider_str})")
    print("="*70)
    
    try:
        llm = get_llm_client(provider=provider)
        
        # Simple test message
        from langchain_core.messages import HumanMessage
        
        messages = [HumanMessage(content="Say 'Hello, I am working!' in exactly 5 words.")]
        
        print("   Sending test message...")
        response = llm.invoke(messages)
        
        print(f"✅ LLM responded successfully")
        print(f"   Response: {response.content}")
        return True
    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("🚀 LLM CONNECTION TEST SUITE")
    print("="*70)
    
    results = {
        "config": test_llm_config(),
        "env_vars": test_environment_variables(),
        "providers": test_available_providers(),
    }
    
    # Test initialization for each available provider
    providers = list_available_providers()
    
    if providers:
        for provider in providers:
            results[f"init_{provider}"] = test_llm_initialization(provider)
            results[f"call_{provider}"] = test_llm_simple_call(provider)
    else:
        print("\n⚠️  No providers available, skipping initialization and call tests")
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:20s}: {status}")
    
    print(f"\n   TOTAL: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n   🎉 All tests passed!")
        return 0
    else:
        print(f"\n   ⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
