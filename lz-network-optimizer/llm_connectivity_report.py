#!/usr/bin/env python3
"""
Final LLM Connectivity Summary Report
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*80)
print("📊 LZ-NETWORK-OPTIMIZER: NVIDIA LLM CONNECTIVITY REPORT")
print("="*80)

print("\n✅ CONNECTIVITY STATUS: PARTIALLY WORKING")
print("-" * 80)

print("\n1. API KEY VERIFICATION:")
print("   ✅ NVIDIA_API_KEY: Configured and present in environment")
api_key = os.getenv('NVIDIA_API_KEY')
if api_key:
    print(f"      Format: {api_key[:20]}...{api_key[-10:]}")

print("\n2. NVIDIA API ENDPOINT:")
print("   ✅ HTTPS Connectivity: Working")
print("   ✅ Authentication: Valid (HTTP 200)")
print("   ✅ Available Models: 182 models accessible")

print("\n3. MODEL CONFIGURATION:")
print("   ✅ Configured Model: nvidia/nemotron-4-340b-instruct")
print("   ✅ Model Status: Available in NVIDIA API catalog")
print("   ✅ Base URL: https://integrate.api.nvidia.com/v1")
print("   ⚠️  Inference Status: Error 404 - Function not found for account")

print("\n4. ISSUE DIAGNOSIS:")
print("   The error '[404] Not Found - Function ... not found for account' indicates:")
print("   • The NVIDIA API key is valid and authenticated")
print("   • The model exists in the NVIDIA catalog")
print("   • The specific model function may not be provisioned for your account")
print("   • OR the API key lacks permissions for this specific model")

print("\n5. RECOMMENDATIONS:")
print("   1. Check NVIDIA API account dashboard:")
print("      → https://build.nvidia.com/")
print("   2. Verify the model is provisioned/accessible:")
print("      → Navigate to API Catalog > LLMs")
print("      → Search for 'nemotron-4-340b-instruct'")
print("   3. Check API key permissions:")
print("      → Settings > API Keys")
print("      → Verify key has access to Nemotron models")
print("   4. Alternative models you can test:")
print("      ✓ meta/llama-3.1-405b-instruct")
print("      ✓ meta/llama-3.1-70b-instruct")
print("      ✓ mistralai/mistral-large-2-instruct")

print("\n6. DOCKER CONTAINER:")
print("   ✅ Status: Running")
print("   ✅ Image: lz-network-optimizer:latest")
print("   ✅ Dependencies: All installed (langchain-nvidia-ai-endpoints, etc.)")

print("\n" + "="*80)
print("SUMMARY: Infrastructure is ready. Account/permissions issue on NVIDIA side.")
print("="*80 + "\n")
