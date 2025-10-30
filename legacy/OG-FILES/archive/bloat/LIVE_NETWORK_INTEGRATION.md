# Live Network Integration Guide

## Integration Strategy

This document outlines how to integrate the live network API with your existing telco planner system.

## Phase 1: Replace Core Network Functions

### 1.1 Update utils.py Functions

Replace these functions in `agentic_llm_workflow/utils.py`:

```python
# REPLACE THESE FUNCTIONS:
- check_network_status()  → Use live_network_manager.check_network_status()
- start_network()         → Use live_network_manager.start_network()  
- stop_network()          → Use live_network_manager.stop_network()

# MODIFY THESE FUNCTIONS:
- modify_parameter_*()    → Use live_network_manager.modify_parameter()
- get_historical_data()   → Use live_network_manager.get_kpi_data()
```

### 1.2 Update Configuration (config.yaml)

Add live network configuration:

```yaml
# Live Network Configuration
live_network:
  api_base_url: "https://41.174.191.214:31127"
  username: "cassava.ai"
  password: "#Pass123#"
  default_timeout: 60
  
# Update KPI weights for live network metrics
p0_nominal_WA_weights: [0.7, 0.3]  # [throughput_weight, latency_weight]
dl_carrierBandwidth_WA_weights: [0.7, 0.3]
ul_carrierBandwidth_WA_weights: [0.7, 0.3] 
att_tx_WA_weights: [0.7, 0.3]
att_rx_WA_weights: [0.7, 0.3]
```

## Phase 2: Update Agents and Tools

### 2.1 Agent Modifications

Update `agentic_llm_workflow/agents.py`:

```python
# Import live network manager
from .live_network_manager import live_network_manager

# Update agent tools to use live network functions
# Replace Docker-based operations with API calls
```

### 2.2 Tool Updates

Update `agentic_llm_workflow/tools.py`:

```python
def start_network_tool():
    """Start live network connection"""
    return live_network_manager.start_network()

def modify_parameter_tool(param_name, ne_name, cell_id, value):
    """Modify parameter on live network"""
    return live_network_manager.modify_parameter(param_name, ne_name, cell_id, value)
```

## Phase 3: UI Integration

### 3.1 Streamlit UI Updates

Update `telco_planner_ui.py`:

1. **Network Status Display**: Show live network element status
2. **Parameter Management**: Real-time parameter modification
3. **KPI Dashboards**: Live KPI data visualization
4. **Network Element Selection**: Choose specific sites/cells

### 3.2 Database Migration

Migrate from simulation database to live network database:

1. **Preserve Historical Data**: Keep existing data for comparison
2. **New Schema**: Implement live network KPI schema
3. **Data Synchronization**: Regular sync with live network

## Phase 4: Advanced Features

### 4.1 Real-time Monitoring

- **Live KPI Streaming**: Continuous data collection
- **Alerting System**: Automatic alerts for threshold violations
- **Performance Trends**: Historical trend analysis

### 4.2 Intelligent Optimization

- **AI-driven Parameter Tuning**: Use ML for optimization
- **Predictive Analysis**: Forecast network performance
- **Automated Actions**: Self-healing network capabilities

## Implementation Priority

### High Priority (Week 1-2)
1. ✅ Create API client (`huawei_api_client.py`)
2. ✅ Create network manager (`live_network_manager.py`)
3. 🔄 Update utils.py to use live network functions
4. 🔄 Test basic connectivity and parameter queries

### Medium Priority (Week 3-4)
1. 🔄 Update UI to show live network elements
2. 🔄 Implement real-time parameter modification
3. 🔄 Create KPI dashboard for live data
4. 🔄 Add error handling and logging

### Low Priority (Week 5+)
1. ⏳ Advanced KPI collection and analysis
2. ⏳ Machine learning integration for optimization
3. ⏳ Automated monitoring and alerting
4. ⏳ Performance optimization features

## Files to Modify

### Immediate Changes Needed:

1. **`agentic_llm_workflow/utils.py`**:
   - Replace Docker-based network functions
   - Update parameter modification functions
   - Modify database operations

2. **`telco_planner_ui.py`**:
   - Update network status display
   - Add live network element selection
   - Modify parameter input forms

3. **`config.yaml`**:
   - Add live network configuration
   - Update KPI weights for new metrics

4. **`requirements.txt`**:
   - Add requests library if not present
   - Add any additional dependencies

### New Files Created:

1. ✅ **`agentic_llm_workflow/huawei_api_client.py`** - API client
2. ✅ **`agentic_llm_workflow/live_network_manager.py`** - Network manager

## Testing Strategy

### 1. API Testing
```python
# Test authentication
client = HuaweiAPIClient("https://41.174.191.214:31127", "cassava.ai", "#Pass123#")
assert client.authenticate() == True

# Test parameter query  
result = client.query_parameter("reference_signal_power", ["MSH-0112-Bindura Hospital"])
assert result is not None
```

### 2. Integration Testing
```python
# Test network manager
manager = LiveNetworkManager()
assert manager.check_network_status() == True

# Test parameter modification
result = manager.modify_parameter("reference_signal_power", "MSH-0112-Bindura Hospital", 1, 49)
assert result["success"] == True
```

### 3. UI Testing
- Verify network element dropdown populates with live data
- Test parameter modification through UI
- Check KPI dashboard updates with real data

## Migration Checklist

- [ ] Backup existing simulation-based code
- [ ] Implement API client and network manager
- [ ] Update utils.py with live network functions
- [ ] Modify UI to use live network data
- [ ] Test authentication and basic queries
- [ ] Test parameter modifications (start with read-only!)
- [ ] Validate KPI data collection
- [ ] Deploy and monitor for issues

## Risk Mitigation

1. **Read-Only Mode First**: Start with queries only, no modifications
2. **Backup and Rollback**: Always backup before parameter changes
3. **Test Environment**: Use test network elements if available  
4. **Gradual Rollout**: Implement one network element at a time
5. **Monitoring**: Extensive logging and error handling