# MML Commands Reference - Liquid Zimbabwe 4G Network Optimizer

## Overview

This document provides a comprehensive reference of all Man-Machine Language (MML) commands currently implemented and recognized by the Liquid Zimbabwe 4G Network Optimizer system.

## Command Origins and References

### Primary Source
- **Configuration File**: `liquid-4g-core/config/Configurations.txt`
- **API Documentation**: `liquid-4g-core/config/API Use.txt`
- **Implementation**: `liquid-4g-core/agents/huawei_api_client.py`
- **Standards**: Huawei iMaster MAE API documentation and LTE/4G parameter optimization guidelines

### Implementation Location
All MML commands are implemented in the `HuaweiAPIClient` class within the `_load_parameter_configs()` method at lines 208-244 of `huawei_api_client.py`.

## Currently Implemented MML Commands

### 1. Reference Signal Power Configuration

**Purpose**: Downlink reference signal power control for cell coverage optimization

```mml
Query:  LST PDSCHCFG
Modify: MOD PDSCHCFG:LOCALCELLID={cell_id},REFERENCESIGNALPWR={value}; {{{ne_name}}}
```

**Details**:
- **Parameter**: `reference_signal_power`
- **Range**: -600 to 500 (0.1 dBm units)
- **Description**: Reference signal power configuration for downlink
- **Use Case**: Optimizing cell coverage and reducing interference

**Example**:
```mml
MOD PDSCHCFG:LOCALCELLID=1,REFERENCESIGNALPWR=49; {MAT-0007-Hwange Baobab}
```

**Reference**: 3GPP TS 36.213 - Physical layer procedures

---

### 2. A3 Event Offset (Handover Threshold)

**Purpose**: Intra-frequency handover threshold configuration

```mml
Query:  LST UECOOPERATIONPARA
Modify: MOD UECOOPERATIONPARA:LOCALCELLID={cell_id},A3OFFSET=dB{value}; {{{ne_name}}}
```

**Details**:
- **Parameter**: `a3_event_offset`
- **Range**: dB0 to dB15
- **Description**: Intra-frequency handover threshold
- **Use Case**: Optimizing handover performance and reducing call drops

**Example**:
```mml
MOD UECOOPERATIONPARA:LOCALCELLID=1,A3OFFSET=dB3; {MAT-0007-Hwange Baobab}
```

**Reference**: 3GPP TS 36.331 - RRC Protocol specification (A3 event definition)

---

### 3. T310 Timer (Radio Link Failure Detection)

**Purpose**: Radio Link Failure detection timer configuration

```mml
Query:  LST UETIMERCONST
Modify: MOD UETIMERCONST:LOCALCELLID={cell_id},T310={value}; {{{ne_name}}}
```

**Details**:
- **Parameter**: `t310_timer`
- **Range**: Timer constants (e.g., MS1000_T310)
- **Description**: Radio Link Failure detection timer
- **Use Case**: Balancing RLF detection speed vs false alarms

**Example**:
```mml
MOD UETIMERCONST:LOCALCELLID=1,T310=MS1000_T310; {MAT-0007-Hwange Baobab}
```

**Reference**: 3GPP TS 36.331 - RRC Protocol specification (Timer T310)

---

### 4. P0 Nominal PUSCH (Uplink Power Control)

**Purpose**: Uplink nominal power control configuration

```mml
Query:  LST CELLULPCCOMM
Modify: MOD CELLULPCCOMM:LOCALCELLID={cell_id},P0NOMINALPUSCH={value}; {{{ne_name}}}
```

**Details**:
- **Parameter**: `p0_nominal_pusch`
- **Range**: -126 to 24
- **Description**: Uplink nominal power control configuration
- **Use Case**: Optimizing uplink coverage and interference management

**Example**:
```mml
MOD CELLULPCCOMM:LOCALCELLID=1,P0NOMINALPUSCH=-67; {MAT-0007-Hwange Baobab}
```

**Reference**: 3GPP TS 36.213 - Physical layer procedures (Power control)

---

### 5. PDCCH Aggregation Level

**Purpose**: Control channel robustness configuration

```mml
Query:  LST CELLUSPARACFG
Modify: MOD CELLUSPARACFG:LOCALCELLID={cell_id},USDATAPDCCHSINROFFSET={value}; {{{ne_name}}}
```

**Details**:
- **Parameter**: `pdcch_aggregation_level`
- **Range**: 0 to 30
- **Description**: PDCCH aggregation level for control channel robustness
- **Use Case**: Improving control channel reliability in challenging RF conditions

**Example**:
```mml
MOD CELLUSPARACFG:LOCALCELLID=1,USDATAPDCCHSINROFFSET=0; {MAT-0007-Hwange Baobab}
```

**Reference**: 3GPP TS 36.212 - Multiplexing and channel coding (PDCCH)

## Command Structure and Syntax

### General MML Command Format

```
[ACTION] [OBJECT]:[PARAMETERS]; {[NETWORK_ELEMENT]}
```

**Components**:
- **ACTION**: `LST` (List/Query), `MOD` (Modify), `ADD` (Add), `RMV` (Remove)
- **OBJECT**: Network object type (e.g., PDSCHCFG, UECOOPERATIONPARA)
- **PARAMETERS**: Comma-separated parameter=value pairs
- **NETWORK_ELEMENT**: Target network element name in curly braces

### Parameter Formatting Rules

1. **Cell ID**: Always use `LOCALCELLID={cell_id}`
2. **Numeric Values**: Direct assignment (e.g., `REFERENCESIGNALPWR=49`)
3. **dB Values**: Prefix with "dB" (e.g., `A3OFFSET=dB3`)
4. **Timer Values**: Use predefined constants (e.g., `T310=MS1000_T310`)
5. **Network Element**: Always wrap in curly braces `{network_element_name}`

## API Implementation Details

### Authentication
```python
url = "https://41.174.191.214:31127/api/rest/securityManagement/v1/oauth/token"
```

### MML Command Execution
```python
url = "https://41.174.191.214:31127/api/rest/mmlManagement/v1/command"
```

### Headers Required
```python
headers = {
    'X-Auth-Token': '[auth_token]',
    'Content-Type': 'application/json'
}
```

### Payload Structure
```python
payload = {
    "command": "[mml_command]",
    "neNames": ["[network_element_name]"]
}
```

## Command Categories by Function

### 1. Power Control Commands
- `LST PDSCHCFG` / `MOD PDSCHCFG` - Downlink power
- `LST CELLULPCCOMM` / `MOD CELLULPCCOMM` - Uplink power

### 2. Mobility Management Commands
- `LST UECOOPERATIONPARA` / `MOD UECOOPERATIONPARA` - Handover parameters

### 3. RRC Management Commands
- `LST UETIMERCONST` / `MOD UETIMERCONST` - Timer configurations

### 4. Channel Configuration Commands
- `LST CELLUSPARACFG` / `MOD CELLUSPARACFG` - Channel parameters

## Network Elements Currently Configured

### Active Sites
Based on database configuration and testing:

1. **MAT-0007-Hwange Baobab** (Primary test site)
2. **MSH-0112-Bindura Hospital** (Secondary test site)
3. **MSH-0014-Chipadze** (Configured in code)

Each site supports cells 1-6 (LOCALCELLID=1 through LOCALCELLID=6)

## Command Validation and Safety

### Pre-execution Checks
1. **Authentication**: Valid X-Auth-Token required
2. **Network Element**: Must exist in network
3. **Cell ID**: Must be valid for target network element
4. **Parameter Range**: Values must be within specified ranges

### Error Handling
- API timeout: 30 seconds
- Retry logic: 3 attempts with exponential backoff
- Validation: Parameter range checking before execution

## Usage in Optimization Workflows

### Automated Parameter Optimization
The system uses these MML commands in automated optimization workflows:

1. **Query current values** using `LST` commands
2. **Analyze KPI data** to determine optimal values
3. **Execute modifications** using `MOD` commands
4. **Validate changes** by re-querying parameters

### Agent Integration
MML commands are integrated into specialized agents:

- **`liquid_zimbabwe_parameters.py`**: Parameter optimization logic
- **`huawei_api_client.py`**: Low-level MML execution
- **`liquid_zimbabwe_monitoring.py`**: Performance monitoring

## Command Extensions and Future Additions

### Potential Additional Commands

Based on Huawei LTE documentation, additional commands that could be implemented:

```mml
# Cell Management
LST CELL / MOD CELL / ADD CELL / RMV CELL

# Neighbor Relations
LST EUCELLNREL / MOD EUCELLNREL / ADD EUCELLNREL / RMV EUCELLNREL

# Load Balancing
LST LOADBALANCINGPARA / MOD LOADBALANCINGPARA

# QoS Configuration
LST QCI / MOD QCI / ADD QCI / RMV QCI

# Carrier Aggregation
LST CACOMPCELL / MOD CACOMPCELL / ADD CACOMPCELL / RMV CACOMPCELL
```

### Implementation Requirements
To add new MML commands:

1. **Update** `Configurations.txt` with new parameter details
2. **Extend** `ParameterConfig` in `huawei_api_client.py`
3. **Add** validation logic in parameter range checking
4. **Test** with live network elements
5. **Document** in this reference guide

## Troubleshooting Common Issues

### Authentication Failures
```
Error: Invalid or expired auth token
Solution: Re-authenticate using /oauth/token endpoint
```

### Network Element Not Found
```
Error: Network element not accessible
Solution: Verify network element name and connectivity
```

### Parameter Out of Range
```
Error: Parameter value exceeds allowed range
Solution: Check parameter ranges in this document
```

### MML Syntax Errors
```
Error: Invalid MML command syntax
Solution: Verify command format against examples
```

## Compliance and Standards

### 3GPP Standards Compliance
All implemented MML commands comply with relevant 3GPP specifications:
- **TS 36.211**: Physical channels and modulation
- **TS 36.212**: Multiplexing and channel coding
- **TS 36.213**: Physical layer procedures
- **TS 36.331**: Radio Resource Control (RRC) protocol

### Huawei Implementation
Commands are specific to Huawei iMaster MAE platform and may require adaptation for other vendors.

---

## Version History

- **v1.0** (Initial): Basic 5 parameter implementation
- **v1.1** (Current): Enhanced documentation and validation
- **v2.0** (Planned): Extended command set and multi-vendor support

---

**Last Updated**: October 7, 2025  
**Maintainer**: Liquid Zimbabwe 4G Network Optimizer Team  
**Contact**: Technical documentation updates via system configuration files