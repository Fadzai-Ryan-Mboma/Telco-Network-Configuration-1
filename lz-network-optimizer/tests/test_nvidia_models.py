"""
Test different NVIDIA models for tool calling support
"""
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from dotenv import load_dotenv
import os

load_dotenv()

def list_available_models():
    """List all available NVIDIA models."""
    print("="*80)
    print("AVAILABLE NVIDIA MODELS")
    print("="*80)

    api_key = os.getenv('NVIDIA_API_KEY')

    try:
        # Try to get available models
        llm = ChatNVIDIA(api_key=api_key)

        # Get available models
        available_models = ChatNVIDIA.get_available_models(api_key=api_key)

        print(f"\n📋 Found {len(available_models)} models:")

        for model in available_models:
            model_id = model.get('id', 'unknown')
            model_name = model.get('model_name', 'unknown')
            supports_tools = model.get('supports_tools', False)

            status = "✅ Supports Tools" if supports_tools else "❌ No Tool Support"
            print(f"\n  {status}")
            print(f"    ID: {model_id}")
            print(f"    Name: {model_name}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nManual list of NVIDIA models with tool support:")
        print("  - nvidia/nemotron-4-340b-instruct")
        print("  - meta/llama-3.1-405b-instruct")
        print("  - mistralai/mixtral-8x22b-instruct-v0.1")
        print("  - microsoft/phi-3-medium-128k-instruct")

if __name__ == "__main__":
    list_available_models()
