#!/usr/bin/env python3
"""
Check available NVIDIA models
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('NVIDIA_API_KEY')
if not api_key:
    print("❌ NVIDIA_API_KEY not set")
    exit(1)

url = "https://integrate.api.nvidia.com/v1/models"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers, timeout=10)
models = response.json().get('data', [])

print("\n" + "="*80)
print("AVAILABLE NVIDIA MODELS")
print("="*80)

# Filter for Nemotron and other LLM models
print("\n🔍 NEMOTRON MODELS:")
for model in models:
    if 'nemotron' in model.get('id', '').lower():
        print(f"   ✓ {model.get('id')}")

print("\n🔍 LLAMA MODELS:")
for model in models:
    if 'llama' in model.get('id', '').lower():
        print(f"   ✓ {model.get('id')}")

print("\n🔍 OTHER INSTRUCTION-TUNED MODELS:")
for model in models:
    if 'instruct' in model.get('id', '').lower() and 'nemotron' not in model.get('id', '').lower() and 'llama' not in model.get('id', '').lower():
        print(f"   ✓ {model.get('id')}")

print(f"\n📊 Total models available: {len(models)}")
