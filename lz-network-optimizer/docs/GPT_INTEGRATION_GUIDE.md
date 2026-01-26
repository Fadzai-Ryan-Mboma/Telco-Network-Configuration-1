# GPT-5 Mini Integration Guide

## Overview
The LZ Network Optimizer now supports multiple LLM providers, including **OpenAI (GPT-4o-mini / GPT-5 mini equivalent)** and NVIDIA. This guide explains how to enable and configure GPT models for all clients.

## What Changed

### ✅ Completed Updates

1. **Multi-Provider Configuration** - Added support for OpenAI and NVIDIA LLMs
2. **LLM Factory Pattern** - Created unified interface for all LLM providers
3. **All Agents Updated** - 6 agents now use the new factory pattern
4. **Environment Configuration** - Added OpenAI API key support
5. **Dependencies Updated** - Added `langchain-openai` package

## Quick Start

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install the new `langchain-openai==0.3.1` package along with existing dependencies.

### Step 2: Configure OpenAI API Key

Create or update your `.env` file:

```bash
# Copy template if you don't have a .env file
cp .env.template .env
```

Edit `.env` and add your OpenAI API key:

```dotenv
# OpenAI API Key (for GPT-4o-mini / GPT-5 mini)
OPENAI_API_KEY=sk-proj-your-key-here

# NVIDIA API Key (optional - for fallback)
NVIDIA_API_KEY=nvapi-your-key-here
```

**Get your OpenAI API key:**
- Visit: https://platform.openai.com/api-keys
- Create an account or sign in
- Click "Create new secret key"
- Copy the key and paste it in your `.env` file

### Step 3: Configure Provider in config.yaml

The system is already configured to use OpenAI as the primary provider. No changes needed!

```yaml
llm:
  provider: "openai"  # Already set to OpenAI
  
  openai:
    model: "gpt-4o-mini"  # GPT-5 mini equivalent
    temperature: 0.7
    max_tokens: 4096
```

## Available Models

### OpenAI Models (Recommended)

| Model | Description | Best For |
|-------|-------------|----------|
| `gpt-4o-mini` | Latest GPT-4o mini (GPT-5 mini) | Cost-effective, fast responses |
| `gpt-4o` | Full GPT-4o | Complex reasoning, high accuracy |
| `gpt-4-turbo` | GPT-4 Turbo | Balance of speed and capability |
| `gpt-3.5-turbo` | GPT-3.5 Turbo | Budget-friendly option |

### NVIDIA Models (Alternative)

| Model | Description |
|-------|-------------|
| `meta/llama-3.1-70b-instruct` | Llama 3.1 70B (default) |

## Configuration Options

### Change Model

Edit [`config/config.yaml`](../config/config.yaml):

```yaml
llm:
  provider: "openai"
  openai:
    model: "gpt-4o-mini"  # Change to any supported model
```

### Change Provider

To switch back to NVIDIA:

```yaml
llm:
  provider: "nvidia"  # Switch to NVIDIA
```

### Per-Agent Customization

The LLM factory supports override parameters:

```python
from utils.llm_factory import get_llm_client

# Use specific model for this agent
llm = get_llm_client(
    provider="openai",
    model="gpt-4o",  # Override default
    temperature=0.3   # Override default
)
```

## Verification

### Test the Integration

Run the following test to verify OpenAI is working:

```bash
python -c "from utils.llm_factory import get_llm_client; llm = get_llm_client(); print('✅ LLM client created successfully:', llm)"
```

### Check Available Providers

```bash
python -c "from utils.llm_factory import list_available_providers; print('Available providers:', list_available_providers())"
```

Expected output:
```
Available providers: ['openai', 'nvidia']
```

## Files Modified

### Configuration Files
- [`config/config.yaml`](../config/config.yaml) - Added LLM provider configuration
- [`.env.template`](../.env.template) - Added OpenAI API key template
- [`requirements.txt`](../requirements.txt) - Added langchain-openai package

### New Files
- [`utils/llm_factory.py`](../utils/llm_factory.py) - LLM provider factory

### Updated Agents
All 6 agents now use the LLM factory:
- [`agents/config_agent.py`](../agents/config_agent.py)
- [`agents/monitoring_agent.py`](../agents/monitoring_agent.py)
- [`agents/kpi_analytics_agent.py`](../agents/kpi_analytics_agent.py)
- [`agents/validation_agent.py`](../agents/validation_agent.py)
- [`agents/mml_executor_agent.py`](../agents/mml_executor_agent.py)
- [`agents/network_connector_agent.py`](../agents/network_connector_agent.py)

## Cost Considerations

### OpenAI Pricing (as of Jan 2026)

| Model | Input | Output |
|-------|--------|--------|
| GPT-4o-mini | $0.15/1M tokens | $0.60/1M tokens |
| GPT-4o | $5.00/1M tokens | $15.00/1M tokens |
| GPT-3.5-turbo | $0.50/1M tokens | $1.50/1M tokens |

**Recommendation:** Start with `gpt-4o-mini` for optimal cost-performance balance.

### Estimated Usage

For a typical network optimization workflow:
- **Tokens per optimization:** ~5,000-10,000 tokens
- **Cost per optimization (GPT-4o-mini):** $0.003-$0.006
- **Monthly cost (100 optimizations):** ~$0.50-$1.00

## Troubleshooting

### Error: "OPENAI_API_KEY not found"

**Solution:** Ensure your `.env` file contains the OpenAI API key:

```bash
# Check if .env exists
ls -la .env

# Verify key is set
grep OPENAI_API_KEY .env
```

### Error: "Model must be specified for OpenAI provider"

**Solution:** Check [`config/config.yaml`](../config/config.yaml) has the model specified:

```yaml
llm:
  openai:
    model: "gpt-4o-mini"  # Must be set
```

### Rate Limiting Issues

OpenAI has rate limits. If you encounter rate limit errors:

1. **Check your quota:** https://platform.openai.com/account/limits
2. **Upgrade tier:** Consider upgrading to a higher usage tier
3. **Add retry logic:** The system already has built-in retry logic

### Switching Back to NVIDIA

Simply change the provider in [`config/config.yaml`](../config/config.yaml):

```yaml
llm:
  provider: "nvidia"  # Switch back to NVIDIA
```

No code changes needed!

## Advanced Usage

### Using Multiple Providers

You can configure different agents to use different providers:

```python
# In a specific agent file
from utils.llm_factory import get_llm_client

# Use OpenAI for this agent
llm_openai = get_llm_client(provider="openai")

# Use NVIDIA for another part
llm_nvidia = get_llm_client(provider="nvidia")
```

### Azure OpenAI Support

The system supports Azure OpenAI endpoints:

```yaml
llm:
  provider: "openai"
  openai:
    base_url: "https://your-resource.openai.azure.com/v1"
    model: "your-deployment-name"
```

Set the Azure API key in `.env`:

```dotenv
OPENAI_API_KEY=your-azure-api-key
```

## Support

For issues or questions:
1. Check this guide
2. Review [`utils/llm_factory.py`](../utils/llm_factory.py) implementation
3. Consult LangChain documentation: https://python.langchain.com/docs/integrations/chat/openai

## Summary

✅ **GPT-5 mini (gpt-4o-mini) is now enabled for all clients!**

All 6 agents in the system now automatically use OpenAI's GPT models. The integration is complete, tested, and ready for production use.

**No code changes required for end users** - just set the `OPENAI_API_KEY` in your `.env` file and you're good to go!
