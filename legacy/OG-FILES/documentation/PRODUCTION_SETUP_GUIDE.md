# 🚀 **Liquid Zimbabwe 4G - Production Environment Setup**

## Environment Variables Configuration

Create a `.env` file in your project root with the following variables:

```bash
# Huawei iMaster MAE API Configuration
LZ_API_URL=https://your-huawei-imaster-server.com
LZ_API_USERNAME=your_api_username
LZ_API_PASSWORD=your_api_password

# Optional: API Configuration
LZ_API_TIMEOUT=30
LZ_API_RETRY_ATTEMPTS=3
LZ_API_SSL_VERIFY=true

# Database Configuration
LZ_DB_PATH=./data/historical_db

# Logging Configuration
LZ_LOG_LEVEL=INFO
LZ_LOG_PATH=./logs/lz_system.log
```

## Production Deployment Checklist

### ✅ **API Credentials Setup**

1. **Obtain Huawei iMaster MAE Credentials**
   - Request API access from network operations team
   - Get server URL, username, and password
   - Verify API endpoints are accessible

2. **Set Environment Variables**
   ```bash
   export LZ_API_URL="https://your-imaster-server.com"
   export LZ_API_USERNAME="your_username"
   export LZ_API_PASSWORD="your_password"
   ```

3. **Test API Connection**
   ```bash
   cd liquid-4g-core
   python -c "
   from agents.huawei_api_client import HuaweiAPIClient
   client = HuaweiAPIClient()
   status = client.check_configuration()
   print('Configuration Status:', status)
   if status['connection_ready']:
       print('✅ Ready for API testing')
   else:
       print('❌ Configuration needs attention')
       for issue in status['issues']:
           print(f'  - {issue}')
   "
   ```

### ✅ **Production Testing Validation**

#### **Phase 1: API Connectivity Test (15 minutes)**
```bash
# Test 1: API Authentication
python -c "
from agents.huawei_api_client import HuaweiAPIClient
client = HuaweiAPIClient()
try:
    auth_result = client.authenticate()
    print('✅ Authentication successful')
except Exception as e:
    print(f'❌ Authentication failed: {e}')
"

# Test 2: Network Element Discovery
python -c "
from agents.huawei_api_client import HuaweiAPIClient
client = HuaweiAPIClient()
elements = client.get_network_elements()
print(f'Found {len(elements)} network elements')
for element in elements:
    print(f'  - {element.name}: {len(element.cell_ids)} cells')
"

# Test 3: Basic MML Command
python -c "
from agents.huawei_api_client import HuaweiAPIClient
client = HuaweiAPIClient()
if client.network_elements:
    site = client.network_elements[0].name
    result = client.execute_mml_command(site, 'LST CELL:;')
    print(f'MML Command Test: {result[\"status\"]}')
else:
    print('No network elements available for testing')
"
```

#### **Phase 2: KPI Data Validation (30 minutes)**
```bash
# Test KPI data collection
python -c "
from agents.liquid_zimbabwe_kpi import LiquidZimbabweKPIManager
kpi_manager = LiquidZimbabweKPIManager()
try:
    # Test data collection from live network
    kpi_data = kpi_manager.collect_live_kpi_data()
    print(f'✅ KPI data collected: {len(kpi_data)} metrics')
    
    # Test database operations
    kpi_manager.store_kpi_data(kpi_data)
    print('✅ KPI data stored to database')
    
    # Test historical retrieval
    historical = kpi_manager.get_historical_kpis('1 hour')
    print(f'✅ Historical data retrieved: {len(historical)} records')
    
except Exception as e:
    print(f'❌ KPI testing failed: {e}')
"
```

#### **Phase 3: Parameter Management Test (20 minutes)**
```bash
# Test parameter operations
python -c "
from agents.liquid_zimbabwe_parameters import LiquidZimbabweParameterManager
param_manager = LiquidZimbabweParameterManager()
try:
    # Test parameter retrieval
    if param_manager.api_client.network_elements:
        site = param_manager.api_client.network_elements[0].name
        params = param_manager.get_current_parameters(site)
        print(f'✅ Parameters retrieved for {site}: {len(params)} parameters')
        
        # Test optimization suggestions
        suggestions = param_manager.suggest_parameter_optimization({})
        print(f'✅ Optimization suggestions generated: {len(suggestions)} suggestions')
    else:
        print('❌ No network elements available for parameter testing')
        
except Exception as e:
    print(f'❌ Parameter testing failed: {e}')
"
```

#### **Phase 4: UI Integration Test (15 minutes)**
```bash
# Test UI with live data
python -c "
import sys
sys.path.append('./ui')
from ui import get_live_kpi_data, get_live_sites_data

# Test live KPI data
kpi_data = get_live_kpi_data()
print(f'✅ UI KPI integration: {kpi_data[\"system_status\"]}')

# Test live sites data
sites_data = get_live_sites_data()
if 'error' not in sites_data:
    print(f'✅ UI sites integration: {len(sites_data[\"sites\"])} sites loaded')
else:
    print(f'❌ UI sites integration: {sites_data[\"error\"]}')
"

# Start UI for manual testing
echo "Starting UI for manual validation..."
streamlit run ui/ui.py --server.port 8501
```

## Security Considerations

### **Production Security Setup**

1. **Environment Variable Security**
   ```bash
   # Secure environment file
   chmod 600 .env
   
   # Add to .gitignore
   echo ".env" >> .gitignore
   echo "*.log" >> .gitignore
   ```

2. **SSL/TLS Configuration**
   ```bash
   # Verify SSL certificates
   export LZ_API_SSL_VERIFY=true
   
   # For internal networks with self-signed certificates
   # export LZ_API_SSL_VERIFY=false
   ```

3. **Logging Security**
   ```bash
   # Create secure log directory
   mkdir -p logs
   chmod 750 logs
   
   # Rotate logs to prevent disk space issues
   # Configure logrotate for production
   ```

## Performance Monitoring

### **Production Monitoring Setup**

1. **System Resource Monitoring**
   ```bash
   # Monitor memory usage
   ps aux | grep "streamlit\|python.*ui.py"
   
   # Monitor CPU usage
   top -p $(pgrep -f "streamlit")
   ```

2. **API Performance Monitoring**
   ```bash
   # Test API response times
   python -c "
   import time
   from agents.huawei_api_client import HuaweiAPIClient
   
   client = HuaweiAPIClient()
   start_time = time.time()
   client.authenticate()
   auth_time = time.time() - start_time
   print(f'Authentication time: {auth_time:.2f}s')
   
   if client.network_elements:
       start_time = time.time()
       result = client.execute_mml_command(client.network_elements[0].name, 'LST CELL:;')
       mml_time = time.time() - start_time
       print(f'MML command time: {mml_time:.2f}s')
   "
   ```

## Troubleshooting

### **Common Issues and Solutions**

1. **Authentication Failures**
   ```bash
   # Check credentials
   echo "URL: $LZ_API_URL"
   echo "Username: $LZ_API_USERNAME"
   echo "Password: [HIDDEN]"
   
   # Test network connectivity
   curl -k "$LZ_API_URL/api/rest/securityManagement/v1/oauth/token"
   ```

2. **SSL Certificate Issues**
   ```bash
   # For development/testing only
   export LZ_API_SSL_VERIFY=false
   
   # For production, install proper certificates
   ```

3. **Database Issues**
   ```bash
   # Check database permissions
   ls -la data/historical_db
   
   # Reinitialize if corrupted
   rm data/historical_db
   python -c "from agents.liquid_zimbabwe_kpi import LiquidZimbabweKPIManager; LiquidZimbabweKPIManager()"
   ```

## Production Deployment

### **Final Deployment Steps**

1. **Environment Setup**
   ```bash
   # Set production environment variables
   source .env
   
   # Verify configuration
   python validate_system.py
   ```

2. **Service Startup**
   ```bash
   # Start the service
   cd liquid-4g-core
   streamlit run ui/ui.py --server.port 8501 --server.address 0.0.0.0
   ```

3. **Health Checks**
   ```bash
   # Check service status
   curl http://localhost:8501/_stcore/health
   
   # Check API connectivity
   python -c "
   from agents.huawei_api_client import HuaweiAPIClient
   client = HuaweiAPIClient()
   status = client.check_configuration()
   print('System Ready:', status['connection_ready'])
   "
   ```

---

## 🎯 **Production Readiness Checklist**

- [ ] **API Credentials Configured** (LZ_API_URL, LZ_API_USERNAME, LZ_API_PASSWORD)
- [ ] **Authentication Testing** (Successful API login)
- [ ] **Network Element Discovery** (Sites visible in system)
- [ ] **MML Command Execution** (Basic parameter queries working)
- [ ] **KPI Data Collection** (Live metrics flowing)
- [ ] **Database Operations** (Data storage and retrieval)
- [ ] **UI Integration** (Dashboard shows live data)
- [ ] **Parameter Management** (Optimization suggestions working)
- [ ] **Security Configuration** (SSL, logging, permissions)
- [ ] **Performance Validation** (Response times acceptable)
- [ ] **Monitoring Setup** (Resource usage tracked)
- [ ] **Documentation Complete** (Operational procedures documented)

---

*🚀 **Once all items are checked, your Liquid Zimbabwe 4G system is 100% production ready!***