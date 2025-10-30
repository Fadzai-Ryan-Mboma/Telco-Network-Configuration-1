# Deployment Guide

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL or SQLite (default)
- Docker & Docker Compose (optional)
- OpenAI or Anthropic API key

### Installation

1. **Install dependencies:**
```bash
cd liquid-4g-prod
pip install -e ".[dev]"
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Initialize database:**
```bash
python -c "from liquid4g.infrastructure.database.migrations import get_migration_manager; get_migration_manager().initialize_schema()"
```

4. **Load sample data (optional):**
```bash
python tests/test_system.py
```

### Running Locally

**Option 1: CLI**
```bash
# Start API
python -m liquid4g api

# Start UI (in another terminal)
python -m liquid4g ui
```

**Option 2: Direct**
```bash
# API
uvicorn liquid4g.interfaces.api.main:app --reload

# UI
streamlit run src/liquid4g/interfaces/ui/app.py
```

### Running with Docker

1. **Create secrets:**
```bash
mkdir -p docker/secrets
echo "your_username" > docker/secrets/huawei_username.txt
echo "your_password" > docker/secrets/huawei_password.txt
echo "sk-your-key" > docker/secrets/openai_api_key.txt
```

2. **Create .env file:**
```bash
cat > docker/.env << EOF
HUAWEI_API_URL=https://your-api:31127
LLM_PROVIDER=openai
DATABASE_PATH=/app/data/liquid4g.db
REDIS_ENABLED=true
REDIS_HOST=redis
EOF
```

3. **Start services:**
```bash
cd docker
docker-compose up -d
```

4. **Access:**
- API: http://localhost:8000
- UI: http://localhost:8501
- API Docs: http://localhost:8000/docs

### Configuration

**Environment Variables:**
```bash
# Core
ENV=production
DATABASE_PATH=data/liquid4g.db

# Huawei API
HUAWEI_API_URL=https://api:31127
HUAWEI_USERNAME=  # Use secrets
HUAWEI_PASSWORD=  # Use secrets
HUAWEI_SSL_VERIFY=false

# LLM
LLM_PROVIDER=openai  # openai|anthropic|local
OPENAI_API_KEY=  # Use secrets
OPENAI_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7

# Circuit Breaker
CIRCUIT_BREAKER_ENABLED=true
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60

# Redis (optional)
REDIS_ENABLED=false
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Testing

### Run Tests
```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=liquid4g --cov-report=html

# Specific test
pytest tests/test_system.py::test_monitor_agent -v
```

### Manual Testing

1. **Check database:**
```python
from liquid4g.infrastructure.database.migrations import get_migration_manager
mgr = get_migration_manager()
print(mgr.is_initialized())
print(mgr.get_current_version())
```

2. **Test API:**
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/sites
```

3. **Test optimization:**
```bash
curl -X POST http://localhost:8000/api/v1/optimize/cell \
  -H "Content-Type: application/json" \
  -d '{"cell_id": "TEST_CELL_001", "auto_execute": false}'
```

## Production Deployment

### Security Checklist
- [ ] Use Docker secrets for all credentials
- [ ] Enable SSL/TLS for API
- [ ] Set `HUAWEI_SSL_VERIFY=true`
- [ ] Use strong database encryption
- [ ] Enable firewall rules
- [ ] Implement rate limiting
- [ ] Set up monitoring/alerting

### Monitoring

**Health Checks:**
- API: `GET /health`
- Database: `GET /api/v1/statistics/operations`
- Agents: `GET /api/v1/agents`

**Logs:**
```bash
# Docker
docker-compose logs -f api

# Local
tail -f data/logs/liquid4g.log
```

**Metrics:**
- Circuit breaker state
- Agent success rates
- LLM usage rates
- Operation durations

### Backup

```bash
# Database backup
cp data/liquid4g.db backups/liquid4g_$(date +%Y%m%d).db

# Full backup
tar -czf backup_$(date +%Y%m%d).tar.gz data/ config/
```

### Scaling

**Horizontal Scaling:**
- Deploy multiple API instances behind load balancer
- Share Redis for cache coordination
- Use PostgreSQL instead of SQLite

**Vertical Scaling:**
- Increase container resources
- Tune database connection pool
- Enable Redis caching

## Troubleshooting

### Common Issues

**1. Database not initialized**
```bash
python -c "from liquid4g.infrastructure.database.migrations import get_migration_manager; get_migration_manager().initialize_schema()"
```

**2. Circuit breaker stuck open**
```python
from liquid4g.llm import get_llm_executor
executor = get_llm_executor()
executor.reset_circuit_breaker()
```

**3. LLM not available**
```bash
# Check API key
echo $OPENAI_API_KEY

# Test provider
python -c "from liquid4g.llm import get_llm_provider; print(get_llm_provider().get_available_providers())"
```

**4. Docker network issues**
```bash
docker-compose down
docker network prune
docker-compose up -d
```

### Support

- GitHub Issues: https://github.com/your-org/liquid-4g-prod
- Documentation: See README.md and stage completion files
- Logs: Check `data/logs/` directory
