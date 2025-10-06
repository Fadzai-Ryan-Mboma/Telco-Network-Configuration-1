# Liquid Zimbabwe 4G UI Components

## Overview
This folder contains all UI-related files and configurations for the Liquid Zimbabwe 4G Network Optimizer.

## Structure
```
ui/
├── ui.py                 # Main Streamlit dashboard application
├── .streamlit/          # Streamlit configuration
│   └── config.toml      # Streamlit server and theme settings
└── README.md           # This documentation
```

## Files

### ui.py
Main Streamlit dashboard providing:
- Real-time KPI monitoring (RSRP, RSRQ, Throughput, etc.)
- Network parameter visualization
- Agent status monitoring
- System health indicators
- Interactive trend analysis

### .streamlit/config.toml
Streamlit configuration file containing:
- Server settings (port 8501, headless mode)
- Security settings (CORS, XSRF protection)
- Theme configuration (colors, styling)
- Logging configuration

## Usage

The UI is automatically started by the main application. Access it via:
- **Container:** http://localhost:8501
- **Direct:** `streamlit run ui/ui.py`

## Features

### Dashboard Sections
1. **KPI Monitoring:** Live network performance metrics
2. **Parameter Control:** Network optimization parameters
3. **Agent Status:** Backend agent health and activity
4. **System Info:** Container and process monitoring
5. **Trend Analysis:** Historical data visualization

### Real-time Updates
- Data refreshes every 30 seconds
- Status indicators update automatically
- Charts and metrics display live data

## Configuration

UI behavior can be customized via:
- `.streamlit/config.toml` for Streamlit settings
- Environment variables for data sources
- Agent configuration for metric availability