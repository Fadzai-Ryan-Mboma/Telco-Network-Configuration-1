# Liquid Zimbabwe 4G System - Dependencies & Technology Stack

## Streamlined Dependencies (Post Strip-Down)

### Core AI & Orchestration
```
# LLM and Agent Framework
langchain==0.3.25
langchain-core==0.3.58
langchain-nvidia-ai-endpoints==0.3.10
langgraph==0.4.1

# NVIDIA NIM Integration
nvidia-nim-client==1.2.0
```

### Network Integration
```
# API Communication
requests==2.31.0
urllib3==2.0.4
httpx==0.25.0

# SSL/Security
certifi==2023.11.17
cryptography==41.0.7
```

### Data Management
```
# Database
sqlite3 (built-in)
pandas==2.1.3
numpy==1.24.3

# Configuration
pyyaml==6.0.1
toml==0.10.2
```

### User Interface
```
# Streamlit Dashboard
streamlit==1.45.0
plotly==5.17.0
altair==5.1.0

# Visualization
matplotlib==3.7.2
seaborn==0.12.2
```

### Monitoring & Logging
```
# Logging and Monitoring
loguru==0.7.2
prometheus-client==0.17.1
```

### Development & Testing
```
# Testing Framework
pytest==7.4.2
pytest-asyncio==0.21.1
pytest-mock==3.11.1
pytest-cov==4.1.0

# Code Quality
black==23.9.1
flake8==6.1.0
mypy==1.5.1
```

## Removed Dependencies (From BubbleRAN)
```
❌ NO LONGER NEEDED:
- docker==6.1.3           # Docker container management
- docker-compose==1.29.2  # Container orchestration
- kubernetes==27.2.0      # K8s integration
- helm==3.12.3            # Helm charts
- rf-simulation-tools     # RF simulation libraries
- 5g-core-network-sim     # 5G core simulation
- usrp-drivers            # USRP hardware drivers
- gnu-radio==3.10.4       # Software-defined radio
```

## Technology Stack Comparison

### Before (Hybrid BubbleRAN + LZ)
```
Application Layer:
├── Streamlit UI (complex dual interface)
├── LangGraph (handling both sim + live)
├── NVIDIA NIM (analyzing mixed data)

Orchestration Layer:
├── Docker Compose (multiple containers)
├── Kubernetes (optional scaling)
├── Complex agent routing

Network Layer:
├── BubbleRAN (simulation containers)
├── 5G Core Network (simulated)
├── Huawei API (live network)
├── Dual database systems

Infrastructure:
├── High memory usage (8GB+)
├── Complex startup (3-5 minutes)
├── Multiple network interfaces
```

### After (Pure LZ)
```
Application Layer:
├── Streamlit UI (focused LZ interface)
├── LangGraph (LZ-optimized agents)
├── NVIDIA NIM (LZ-specific prompts)

Direct Integration:
├── Huawei iMaster MAE API
├── Single database system
├── Simplified configuration

Infrastructure:
├── Low memory usage (<2GB)
├── Fast startup (10-30 seconds)
├── Single network interface
```

## System Requirements

### Minimum Requirements
- **CPU**: 4 cores, 2.5GHz
- **RAM**: 4GB
- **Storage**: 10GB SSD
- **Network**: Stable internet connection
- **OS**: Linux/macOS/Windows with Python 3.9+

### Recommended Requirements
- **CPU**: 8 cores, 3.0GHz+
- **RAM**: 8GB
- **Storage**: 20GB NVMe SSD
- **Network**: Low-latency connection to Huawei API
- **OS**: Linux (Ubuntu 22.04 LTS recommended)

### Production Requirements
- **CPU**: 16 cores, 3.5GHz+
- **RAM**: 16GB
- **Storage**: 50GB NVMe SSD
- **Network**: Redundant connections
- **OS**: Linux with monitoring tools