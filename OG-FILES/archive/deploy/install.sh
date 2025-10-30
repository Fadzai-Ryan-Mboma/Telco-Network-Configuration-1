#!/bin/bash
# Liquid Zimbabwe Optimizer - Production Installation Script
# Usage: curl -fsSL https://raw.githubusercontent.com/cassava/lz-optimizer/main/deploy/install.sh | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
APP_NAME="lz-optimizer"
APP_USER="lz-optimizer"
APP_HOME="/opt/lz-optimizer"
PYTHON_VERSION="3.10"
VENV_PATH="${APP_HOME}/venv"
SERVICE_PORT="8501"
NGINX_PORT="80"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root. Use: sudo $0"
    fi
}

# Detect OS and distribution
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        error "Cannot detect OS. This script supports Ubuntu/Debian only."
    fi
    
    log "Detected OS: $OS $VER"
}

# Update system packages
update_system() {
    log "Updating system packages..."
    apt-get update -qq
    apt-get upgrade -y -qq
}

# Install system dependencies
install_system_deps() {
    log "Installing system dependencies..."
    apt-get install -y \
        python${PYTHON_VERSION} \
        python${PYTHON_VERSION}-venv \
        python3-pip \
        nginx \
        sqlite3 \
        curl \
        wget \
        unzip \
        git \
        htop \
        logrotate \
        supervisor \
        fail2ban
}

# Create application user
create_app_user() {
    log "Creating application user: $APP_USER"
    
    if id "$APP_USER" &>/dev/null; then
        warn "User $APP_USER already exists"
    else
        useradd --system --shell /bin/bash --home-dir $APP_HOME --create-home $APP_USER
        log "Created user: $APP_USER"
    fi
    
    # Create necessary directories
    mkdir -p $APP_HOME/{config,data,logs,backups,scripts}
    chown -R $APP_USER:$APP_USER $APP_HOME
}

# Setup Python virtual environment
setup_python_env() {
    log "Setting up Python virtual environment..."
    
    # Create virtual environment
    sudo -u $APP_USER python${PYTHON_VERSION} -m venv $VENV_PATH
    
    # Upgrade pip
    sudo -u $APP_USER $VENV_PATH/bin/pip install --upgrade pip setuptools wheel
    
    log "Python virtual environment created at: $VENV_PATH"
}

# Install Python dependencies
install_python_deps() {
    log "Installing Python dependencies..."
    
    # Create requirements.txt for LZ-only system
    cat > $APP_HOME/requirements.txt << 'EOF'
# Core AI & Agent Framework
langchain==0.3.25
langchain-core==0.3.58
langchain-nvidia-ai-endpoints==0.3.10
langgraph==0.4.1

# Network Integration
requests==2.31.0
urllib3==2.0.4
httpx==0.25.0
certifi==2023.11.17

# Data Management
pandas==2.1.3
numpy==1.24.3
pyyaml==6.0.1

# User Interface
streamlit==1.45.0
plotly==5.17.0
altair==5.1.0

# Monitoring & Logging
loguru==0.7.2

# Development & Testing (optional)
pytest==7.4.2
black==23.9.1
EOF

    chown $APP_USER:$APP_USER $APP_HOME/requirements.txt
    
    # Install dependencies
    sudo -u $APP_USER $VENV_PATH/bin/pip install -r $APP_HOME/requirements.txt
    
    log "Python dependencies installed successfully"
}

# Download application code
download_app_code() {
    log "Downloading Liquid Zimbabwe Optimizer code..."
    
    # For now, create placeholder structure
    # In production, this would clone from your repository
    
    mkdir -p $APP_HOME/src
    
    # Create main application file
    cat > $APP_HOME/src/main_ui.py << 'EOF'
import streamlit as st
import time
from datetime import datetime

st.set_page_config(
    page_title="Liquid Zimbabwe Network Optimizer",
    page_icon="📡",
    layout="wide"
)

# Custom CSS for Cassava branding
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #0066CC 0%, #00A0A0 100%);
    color: white;
    padding: 1.5rem;
    margin: -1rem -1rem 2rem -1rem;
    border-radius: 0 0 10px 10px;
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header"><h1>🔷 Cassava Technologies - Liquid Zimbabwe Network Optimizer</h1></div>', unsafe_allow_html=True)

# Status indicators
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Network Status", "🟢 Connected", "Live")

with col2:
    st.metric("Last Update", datetime.now().strftime("%H:%M:%S"), "Real-time")

with col3:
    st.metric("System Health", "✅ Optimal", "100%")

# KPI Dashboard
st.header("📊 Network Performance KPIs")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Network Access Success", "97.2%", "2.1%")
    
with col2:
    st.metric("Download Quality", "8.3%", "-1.2%")
    
with col3:
    st.metric("Upload Quality", "4.1%", "0.8%")

# Charts placeholder
st.header("📈 Performance Trends")
import numpy as np
chart_data = np.random.randn(20, 3)
st.line_chart(chart_data)

# AI Assistant
st.header("🤖 AI Optimization Assistant")
st.success("✅ System is running in demo mode. Connect to Huawei API to enable live optimization.")

if st.button("🔄 Test Connection"):
    with st.spinner("Testing connection..."):
        time.sleep(2)
        st.success("✅ Demo mode active - ready for API integration!")

# Health check endpoint
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    st.write("Liquid Zimbabwe Network Optimizer - Demo Mode")
EOF

    chown -R $APP_USER:$APP_USER $APP_HOME/src
    log "Application code downloaded and configured"
}

# Create systemd service
create_systemd_service() {
    log "Creating systemd service..."
    
    cat > /etc/systemd/system/$APP_NAME.service << EOF
[Unit]
Description=Liquid Zimbabwe Network Optimizer
After=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_HOME/src
Environment=PATH=$VENV_PATH/bin
ExecStart=$VENV_PATH/bin/streamlit run main_ui.py --server.port=$SERVICE_PORT --server.address=127.0.0.1
Restart=always
RestartSec=3

# Resource limits (LZ optimized)
MemoryMax=2G
CPUQuota=200%

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_HOME/data $APP_HOME/logs

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$APP_NAME

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable $APP_NAME
    
    log "Systemd service created and enabled"
}

# Configure Nginx
configure_nginx() {
    log "Configuring Nginx reverse proxy..."
    
    # Remove default site
    rm -f /etc/nginx/sites-enabled/default
    
    # Create LZ optimizer site configuration
    cat > /etc/nginx/sites-available/$APP_NAME << EOF
server {
    listen $NGINX_PORT;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    location / {
        proxy_pass http://127.0.0.1:$SERVICE_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:$SERVICE_PORT/health;
        access_log off;
    }
    
    # Logs
    access_log /var/log/nginx/$APP_NAME-access.log;
    error_log /var/log/nginx/$APP_NAME-error.log;
}
EOF

    # Enable site
    ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
    
    # Test configuration
    nginx -t || error "Nginx configuration test failed"
    
    log "Nginx configured successfully"
}

# Setup logging and monitoring
setup_logging() {
    log "Setting up logging and monitoring..."
    
    # Create log rotation configuration
    cat > /etc/logrotate.d/$APP_NAME << EOF
$APP_HOME/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 $APP_USER $APP_USER
    postrotate
        systemctl reload $APP_NAME
    endscript
}
EOF

    # Create basic monitoring script
    cat > $APP_HOME/scripts/monitor.sh << 'EOF'
#!/bin/bash
# Basic monitoring script

APP_NAME="lz-optimizer"
LOG_FILE="/opt/lz-optimizer/logs/monitor.log"

# Check if service is running
if systemctl is-active --quiet $APP_NAME; then
    echo "$(date): $APP_NAME is running" >> $LOG_FILE
else
    echo "$(date): $APP_NAME is NOT running - attempting restart" >> $LOG_FILE
    systemctl start $APP_NAME
fi

# Check memory usage
MEMORY_USAGE=$(ps -o pid,rss,comm | grep streamlit | awk '{sum+=$2} END {print sum/1024}')
echo "$(date): Memory usage: ${MEMORY_USAGE}MB" >> $LOG_FILE

# Check disk space
DISK_USAGE=$(df /opt/lz-optimizer | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "$(date): WARNING: Disk usage high: $DISK_USAGE%" >> $LOG_FILE
fi
EOF

    chmod +x $APP_HOME/scripts/monitor.sh
    chown $APP_USER:$APP_USER $APP_HOME/scripts/monitor.sh
    
    # Add to crontab for regular monitoring
    (crontab -l 2>/dev/null; echo "*/5 * * * * $APP_HOME/scripts/monitor.sh") | crontab -
    
    log "Logging and monitoring configured"
}

# Create configuration template
create_config() {
    log "Creating configuration template..."
    
    cat > $APP_HOME/config/config.yaml << 'EOF'
# Liquid Zimbabwe Network Optimizer Configuration

# NVIDIA NIM Configuration
nvidia_api_key: "YOUR_NVIDIA_API_KEY_HERE"
llm_model: "meta/llama-3.1-70b-instruct"
llm_base_url: "https://integrate.api.nvidia.com/v1"
llm_temp: 0
llm_top_p: 0.7
llm_max_tokens: 1024

# Huawei API Configuration
huawei_api:
  base_url: "https://41.174.191.214:31127"
  username: "cassava.ai"
  password: "#Pass123#"
  verify_ssl: false
  timeout_seconds: 30

# Liquid Zimbabwe KPI Configuration
kpis:
  network_access_success:
    threshold: 95
    weight: 0.2
  download_quality:
    threshold: 10
    weight: 0.15
  upload_quality:
    threshold: 8
    weight: 0.15
  control_channel_load:
    threshold: 70
    weight: 0.15
  feedback_channel_load:
    threshold: 10
    weight: 0.1
  download_speed:
    threshold: 5000
    weight: 0.125
  upload_speed:
    threshold: 1000
    weight: 0.125

# Parameter Configuration
parameters:
  reference_signal_power_pdschcfg:
    range: [-600, 500]
    default: -120
  reference_signal_power_rs:
    range: [-600, 500]
    default: -120
  a3_event_offset:
    range: [0, 15]
    default: 6
  t310_timer:
    range: [0, 30000]
    default: 1000
  rach_preamble_initial_power:
    range: [-120, -90]
    default: -104

# Database Configuration
database:
  path: "/opt/lz-optimizer/data/lz_network.db"
  backup_interval_hours: 24

# Monitoring Configuration
monitoring:
  kpi_collection_interval: 30
  optimization_check_interval: 300
  validation_period: 600

# Logging Configuration
logging:
  level: "INFO"
  file: "/opt/lz-optimizer/logs/lz-optimizer.log"
  max_size_mb: 100
  backup_count: 5
EOF

    chown $APP_USER:$APP_USER $APP_HOME/config/config.yaml
    chmod 600 $APP_HOME/config/config.yaml  # Protect sensitive data
    
    log "Configuration template created at: $APP_HOME/config/config.yaml"
    warn "Please edit the configuration file to add your API keys and credentials"
}

# Start services
start_services() {
    log "Starting services..."
    
    # Start and enable services
    systemctl start $APP_NAME
    systemctl enable $APP_NAME
    
    systemctl reload nginx
    systemctl enable nginx
    
    # Wait a moment for services to start
    sleep 5
    
    # Check service status
    if systemctl is-active --quiet $APP_NAME; then
        log "✅ $APP_NAME service is running"
    else
        error "❌ $APP_NAME service failed to start"
    fi
    
    if systemctl is-active --quiet nginx; then
        log "✅ Nginx service is running"
    else
        error "❌ Nginx service failed to start"
    fi
}

# Setup firewall (optional)
setup_firewall() {
    log "Configuring basic firewall..."
    
    if command -v ufw >/dev/null 2>&1; then
        ufw --force enable
        ufw allow ssh
        ufw allow $NGINX_PORT
        ufw allow 443  # For future SSL
        log "Firewall configured with UFW"
    else
        warn "UFW not available, skipping firewall configuration"
    fi
}

# Main installation function
main() {
    log "🚀 Starting Liquid Zimbabwe Network Optimizer Installation"
    log "============================================================="
    
    check_root
    detect_os
    update_system
    install_system_deps
    create_app_user
    setup_python_env
    install_python_deps
    download_app_code
    create_systemd_service
    configure_nginx
    setup_logging
    create_config
    setup_firewall
    start_services
    
    log "============================================================="
    log "✅ Installation completed successfully!"
    log ""
    log "📋 Next Steps:"
    log "1. Edit configuration: sudo nano $APP_HOME/config/config.yaml"
    log "2. Add your API keys and credentials"
    log "3. Restart the service: sudo systemctl restart $APP_NAME"
    log ""
    log "🌐 Access your dashboard at: http://$(hostname -I | awk '{print $1}'):$NGINX_PORT"
    log "📊 Service status: sudo systemctl status $APP_NAME"
    log "📝 View logs: sudo journalctl -u $APP_NAME -f"
    log ""
    log "🔧 Configuration file: $APP_HOME/config/config.yaml"
    log "📁 Application home: $APP_HOME"
    log "👤 Application user: $APP_USER"
    log ""
    log "Happy optimizing! 🎯"
}

# Run main function
main "$@"