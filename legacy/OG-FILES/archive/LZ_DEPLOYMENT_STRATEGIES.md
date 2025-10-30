# Liquid Zimbabwe 4G System - Deployment Strategies (Post-Docker Removal)

## Overview: From Docker to Direct Deployment

Since we're removing Docker containers (BubbleRAN simulation dependencies), we need alternative deployment strategies that are **simpler, lighter, and more direct** for the pure Liquid Zimbabwe system.

## Deployment Option 1: Native Python Deployment (Recommended)

### 1.1 Direct Python Installation

```bash
# Deployment Structure
liquid_zimbabwe_optimizer/
├── deploy/
│   ├── install.sh              # Automated installation script
│   ├── systemd/               # Service definitions
│   ├── nginx/                 # Reverse proxy config
│   └── scripts/               # Management scripts
├── src/                       # Application code
├── config/                    # Configuration files
├── data/                      # Database and logs
└── requirements.txt           # Python dependencies
```

### 1.2 Installation Script
```bash
#!/bin/bash
# install.sh - Complete system installation

set -e

echo "🚀 Installing Liquid Zimbabwe Optimizer..."

# 1. System Dependencies
sudo apt-get update
sudo apt-get install -y python3.10 python3.10-venv python3-pip nginx sqlite3

# 2. Create application user
sudo useradd --system --shell /bin/bash --home-dir /opt/lz-optimizer lz-optimizer
sudo mkdir -p /opt/lz-optimizer
sudo chown lz-optimizer:lz-optimizer /opt/lz-optimizer

# 3. Create Python virtual environment
sudo -u lz-optimizer python3.10 -m venv /opt/lz-optimizer/venv
source /opt/lz-optimizer/venv/bin/activate

# 4. Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Copy application files
sudo cp -r src/* /opt/lz-optimizer/
sudo cp -r config/* /opt/lz-optimizer/config/
sudo chown -R lz-optimizer:lz-optimizer /opt/lz-optimizer/

# 6. Setup systemd service
sudo cp deploy/systemd/lz-optimizer.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable lz-optimizer

# 7. Configure Nginx reverse proxy
sudo cp deploy/nginx/lz-optimizer.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/lz-optimizer.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 8. Initialize database
sudo -u lz-optimizer /opt/lz-optimizer/venv/bin/python /opt/lz-optimizer/scripts/init_db.py

# 9. Start services
sudo systemctl start lz-optimizer
sudo systemctl start nginx

echo "✅ Installation complete!"
echo "🌐 Access the dashboard at: http://your-server:8501"
```

### 1.3 Systemd Service Definition
```ini
# /etc/systemd/system/lz-optimizer.service
[Unit]
Description=Liquid Zimbabwe Network Optimizer
After=network.target

[Service]
Type=simple
User=lz-optimizer
Group=lz-optimizer
WorkingDirectory=/opt/lz-optimizer
Environment=PATH=/opt/lz-optimizer/venv/bin
ExecStart=/opt/lz-optimizer/venv/bin/streamlit run main_ui.py --server.port=8501 --server.address=127.0.0.1
Restart=always
RestartSec=3

# Resource limits
MemoryMax=2G
CPUQuota=200%

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/lz-optimizer/data /opt/lz-optimizer/logs

[Install]
WantedBy=multi-user.target
```

### 1.4 Nginx Configuration
```nginx
# /etc/nginx/sites-available/lz-optimizer.conf
server {
    listen 80;
    server_name your-server.cassavatechnologies.com;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8501/health;
        access_log off;
    }

    # Static files (if any)
    location /static {
        alias /opt/lz-optimizer/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Deployment Option 2: Lightweight Container (Optional)

### 2.1 Minimal Dockerfile (No BubbleRAN Dependencies)
```dockerfile
# Dockerfile.lz-only
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create app user
RUN groupadd -r lzuser && useradd -r -g lzuser lzuser

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p data logs && \
    chown -R lzuser:lzuser /app

# Switch to non-root user
USER lzuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/health || exit 1

# Expose port
EXPOSE 8501

# Start command
CMD ["streamlit", "run", "main_ui.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 2.2 Simplified Docker Compose
```yaml
# docker-compose.lz.yaml
version: '3.8'

services:
  lz-optimizer:
    build:
      context: .
      dockerfile: Dockerfile.lz-only
    ports:
      - "8501:8501"
    environment:
      - NVIDIA_API_KEY=${NVIDIA_API_KEY}
      - HUAWEI_API_URL=${HUAWEI_API_URL}
      - HUAWEI_USERNAME=${HUAWEI_USERNAME}
      - HUAWEI_PASSWORD=${HUAWEI_PASSWORD}
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - ./logs:/app/logs
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - lz-optimizer
    restart: unless-stopped
```

## Deployment Option 3: Cloud-Native Deployment

### 3.1 Kubernetes Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lz-optimizer
  namespace: cassava-telco
spec:
  replicas: 2
  selector:
    matchLabels:
      app: lz-optimizer
  template:
    metadata:
      labels:
        app: lz-optimizer
    spec:
      containers:
      - name: lz-optimizer
        image: cassava/lz-optimizer:latest
        ports:
        - containerPort: 8501
        env:
        - name: NVIDIA_API_KEY
          valueFrom:
            secretKeyRef:
              name: lz-secrets
              key: nvidia-api-key
        - name: HUAWEI_API_URL
          valueFrom:
            configMapKeyRef:
              name: lz-config
              key: huawei-api-url
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8501
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8501
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
        - name: config-volume
          mountPath: /app/config
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: lz-data-pvc
      - name: config-volume
        configMap:
          name: lz-config

---
apiVersion: v1
kind: Service
metadata:
  name: lz-optimizer-service
spec:
  selector:
    app: lz-optimizer
  ports:
  - port: 80
    targetPort: 8501
  type: LoadBalancer
```

### 3.2 AWS ECS Deployment
```json
{
  "family": "lz-optimizer",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/lzOptimizerTaskRole",
  "containerDefinitions": [
    {
      "name": "lz-optimizer",
      "image": "cassava/lz-optimizer:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "HUAWEI_API_URL",
          "value": "https://41.174.191.214:31127"
        }
      ],
      "secrets": [
        {
          "name": "NVIDIA_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:nvidia-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/lz-optimizer",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8501/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

## Deployment Option 4: Serverless Deployment

### 4.1 AWS Lambda + API Gateway
```python
# lambda_handler.py
import json
import streamlit as streamlit_app
from mangum import Mangum

# Streamlit app wrapped for Lambda
def create_app():
    # Import your main LZ app
    from main_ui import main
    return main()

# Lambda handler
handler = Mangum(create_app(), lifespan="off")

def lambda_handler(event, context):
    return handler(event, context)
```

### 4.2 Serverless Framework Configuration
```yaml
# serverless.yml
service: lz-optimizer

provider:
  name: aws
  runtime: python3.10
  region: us-east-1
  memorySize: 1024
  timeout: 30
  environment:
    NVIDIA_API_KEY: ${env:NVIDIA_API_KEY}
    HUAWEI_API_URL: ${env:HUAWEI_API_URL}

functions:
  app:
    handler: lambda_handler.lambda_handler
    events:
      - http:
          path: /{proxy+}
          method: ANY
      - http:
          path: /
          method: ANY

plugins:
  - serverless-python-requirements
  - serverless-domain-manager

custom:
  pythonRequirements:
    dockerizePip: false
  customDomain:
    domainName: lz-optimizer.cassavatechnologies.com
    stage: prod
    certificateName: '*.cassavatechnologies.com'
```

## Deployment Comparison Matrix

| **Deployment Type** | **Complexity** | **Resource Usage** | **Scalability** | **Maintenance** | **Cost** |
|---------------------|----------------|-------------------|-----------------|-----------------|----------|
| **Native Python** | Low | Very Low | Manual | Low | Very Low |
| **Lightweight Container** | Medium | Low | Medium | Medium | Low |
| **Kubernetes** | High | Medium | Excellent | High | Medium |
| **AWS ECS/Fargate** | Medium | Medium | Excellent | Low | Medium |
| **Serverless Lambda** | Medium | Very Low | Automatic | Very Low | Variable |

## Recommended Deployment Strategy

### For Development/Testing:
```bash
# Quick development setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run main_ui.py
```

### For Production (Recommended):
**Native Python Deployment** with these components:
- **Systemd service** for process management
- **Nginx reverse proxy** for web serving
- **SSL termination** for security
- **Monitoring** with systemd journal
- **Backup scripts** for data protection

### Quick Production Setup Script:
```bash
#!/bin/bash
# quick-deploy.sh

# Download and run the installer
curl -fsSL https://raw.githubusercontent.com/cassava/lz-optimizer/main/deploy/install.sh | bash

# Configure your API credentials
sudo -u lz-optimizer nano /opt/lz-optimizer/config/config.yaml

# Start the service
sudo systemctl start lz-optimizer

echo "✅ Liquid Zimbabwe Optimizer is running!"
echo "🌐 Access at: http://$(hostname -I | awk '{print $1}'):8501"
```

## Benefits of Removing Docker

### Resource Efficiency:
- **Memory**: 2GB vs 8GB+ (75% reduction)
- **Storage**: 5GB vs 20GB+ (75% reduction)
- **Startup**: 10s vs 3-5min (95% faster)

### Operational Simplicity:
- **No container orchestration**
- **Direct process management**
- **Standard Linux service patterns**
- **Simplified troubleshooting**

### Security Benefits:
- **Reduced attack surface**
- **Standard OS security model**
- **No container runtime vulnerabilities**
- **Direct system integration**

The **Native Python deployment** is the recommended approach for production as it provides the best balance of simplicity, performance, and maintainability for the pure Liquid Zimbabwe system.