# Liquid Zimbabwe 4G Network Optimizer (Production)

**Version**: 2.0.0
**Status**: Production-Ready Hybrid Agentic System
**License**: Proprietary - Liquid Intelligent Technologies

## Overview

Enterprise-grade 4G network optimization platform with intelligent hybrid agents that combine:
- **LLM Primary**: LangChain + OpenAI/Claude/Local LLMs for intelligent decision-making
- **Rule-Based Fallback**: YAML-based deterministic logic when LLM unavailable
- **Result**: Best of both worlds - AI flexibility + guaranteed uptime

## Key Features

### 🤖 Hybrid Agentic System
- 6-stage intelligent workflow (Monitor → Analyze → Optimize → Configure → Validate → Execute)
- LLM-powered optimization with automatic rule-based fallback
- Circuit breaker pattern prevents cascading failures
- Comprehensive metrics tracking (Prometheus)

### 🗄️ Single Unified Database
- No fragmentation - all data in one normalized SQLite database
- Foreign keys and proper indexes
- Built-in migration system

### 🔐 Security First
- Zero hardcoded credentials
- Docker secrets integration
- Secrets manager ready (HashiCorp Vault, AWS Secrets Manager)

### 📊 Production Monitoring
- Prometheus metrics
- Grafana dashboards
- LLM vs rule usage tracking
- Cost monitoring

### 🐳 Container Ready
- Docker and Docker Compose
- Kubernetes manifests
- Health checks built-in

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (for deployment)
- OpenAI API key (or Anthropic/Local LLM)

### Installation

```bash
# Clone repository
cd liquid-4g-prod

# Install dependencies
pip install -e .

# Setup environment
cp .env.example .env
# Edit .env with your credentials

# Initialize database
python -m liquid4g.infrastructure.database.migrate

# Run tests
pytest

# Start application
python -m liquid4g
```

### Docker Deployment

```bash
# Setup secrets
mkdir -p docker/secrets
echo "your_huawei_password" > docker/secrets/huawei_password.txt
echo "your_openai_key" > docker/secrets/openai_api_key.txt

# Build and deploy
cd docker
docker-compose up -d

# Access UI
open http://localhost:8501
```

## Architecture

### Clean Architecture Layers
```
┌─────────────────────────────────────┐
│      Interfaces (UI/API/CLI)        │
├─────────────────────────────────────┤
│      Application (Use Cases)        │
├─────────────────────────────────────┤
│      Domain (Business Logic)        │
├─────────────────────────────────────┤
│   Infrastructure (DB/External)      │
└─────────────────────────────────────┘
```

### 6-Stage Agentic Workflow
1. **Network Connector**: Connect to Huawei iMaster MAE API
2. **Monitoring Analysis**: Collect and analyze KPI data
3. **KPI Analytics**: Identify optimization opportunities
4. **Configuration**: Generate MML commands for optimization
5. **Validation**: Human approval workflow with safety checks
6. **Execution**: Execute changes with real-time monitoring

## Configuration

### LLM Configuration
Edit `config/agents/llm_config.yaml`:
```yaml
llm:
  provider: "openai"  # openai | anthropic | local
  model: "gpt-4o-mini"
  temperature: 0.0
  fallback_enabled: true
```

### Agent Configuration
Each agent can be configured independently:
- Enable/disable LLM per agent
- Circuit breaker thresholds
- Timeout settings
- Confidence thresholds

## Documentation

- [Architecture Overview](docs/architecture/overview.md)
- [Deployment Guide](docs/deployment/docker.md)
- [Development Setup](docs/development/setup.md)
- [API Documentation](docs/api/endpoints.md)
- [Agent Prompts](docs/agents/llm_prompts.md)

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=liquid4g --cov-report=html

# Run specific test
pytest tests/unit/agents/test_optimizer_agent.py
```

## Monitoring

Access monitoring dashboards:
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090

Key metrics:
- `liquid4g_agent_executions_total{mode="llm|rule"}`
- `liquid4g_agent_duration_seconds`
- `liquid4g_llm_costs_total`
- `liquid4g_circuit_breaker_state`

## Migration from liquid-4g-core

```bash
# Run migration script
python scripts/import_legacy_data.py

# Verify data
python scripts/verify_migration.py
```

## Contributing

See [CONTRIBUTING.md](docs/development/contributing.md)

## Support

For issues, questions, or feature requests:
- Internal: Cassava AI Team
- Email: ai-team@liquid.tech

## License

Proprietary - Liquid Intelligent Technologies Zimbabwe
All Rights Reserved © 2025
