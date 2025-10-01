# Liquid Zimbabwe 4G Strip-Down Implementation Plan

## Phase 1: Pre-Implementation Analysis (Days 1-2)

### 1.1 Dependency Mapping
- [ ] Map all BubbleRAN dependencies across codebase
- [ ] Identify shared components (agents.py, tools.py, utils.py)
- [ ] Document Liquid Zimbabwe-only components
- [ ] Create dependency graph visualization

### 1.2 Data Migration Planning
- [ ] Analyze current database schemas
- [ ] Plan migration from BubbleRAN KPIs to LZ KPIs
- [ ] Design new simplified database structure
- [ ] Create data transformation scripts

### 1.3 Configuration Refactoring
- [ ] Strip BubbleRAN parameters from config.yaml
- [ ] Keep only LZ-specific configurations
- [ ] Simplify parameter ranges and weights
- [ ] Remove Docker-related configurations

## Phase 2: Core System Refactoring (Days 3-7)

### 2.1 Agent System Simplification
- [ ] Create pure LZ agents without BubbleRAN fallbacks
- [ ] Remove hybrid monitoring logic
- [ ] Implement direct Huawei API integration
- [ ] Eliminate Docker-based network management

### 2.2 Tool System Overhaul
- [ ] Replace execute_xapp_sql with lz_execute_sql
- [ ] Remove find_value_in_gnb (replace with huawei_get_parameter)
- [ ] Implement MML command tools
- [ ] Create LZ-specific weighted average calculations

### 2.3 Network Integration Layer
- [ ] Streamline huawei_api_client.py
- [ ] Remove simulation fallbacks from live_network_manager.py
- [ ] Implement pure LZ API client
- [ ] Create MML command execution framework

## Phase 3: UI and Experience Redesign (Days 8-10)

### 3.1 Dashboard Simplification
- [ ] Remove BubbleRAN status indicators
- [ ] Focus on 7 core LZ KPIs
- [ ] Simplify parameter controls to 5 core parameters
- [ ] Implement Cassava branding throughout

### 3.2 User Workflow Optimization
- [ ] Streamline network connection process
- [ ] Remove Docker startup procedures
- [ ] Implement direct API connection flow
- [ ] Create LZ-specific optimization workflows

## Phase 4: Testing Infrastructure (Days 11-13)

### 4.1 Comprehensive Test Suite Creation
- [ ] Unit tests for all LZ components
- [ ] Integration tests for Huawei API
- [ ] End-to-end workflow tests
- [ ] Performance benchmarking suite

### 4.2 Validation Framework
- [ ] Parameter validation tests
- [ ] KPI calculation accuracy tests
- [ ] MML command generation tests
- [ ] Agent decision-making validation

## Phase 5: Deployment and Migration (Days 14-15)

### 5.1 Production Deployment
- [ ] Deploy to staging environment
- [ ] Migrate historical data
- [ ] Train users on new interface
- [ ] Go-live with monitoring

### 5.2 Post-Deployment Optimization
- [ ] Monitor system performance
- [ ] Gather user feedback
- [ ] Optimize based on real usage
- [ ] Document lessons learned