# Engineer Testing Guide: LZ Network Optimizer with TA Integration

**Version**: 1.0
**Date**: 2026-01-12
**Status**: Core Functional Components Complete

---

## Executive Summary

This guide outlines testing procedures for the newly integrated Timing Advance (TA) functionality in the LZ Network Optimizer. The system now tracks UE distance distribution across 12 distance bins, enabling coverage-aware optimization decisions.

### What Was Implemented (Core Functional Components)

✅ **Phase 1-2**: TA Data Infrastructure
- Created `timing_advance_data` table with 27 columns
- Imported 2,178 TA records covering 4 sites, 24 cells (Sept-Nov 2025)
- Added `query_ta_metrics()` LangChain tool for LLM agents

✅ **Phase 3**: KPI System Enhancement
- Added 2 TA-based KPIs: `ta_overshoot_percentage`, `avg_timing_advance`
- Updated KPI weighting: Now 9 KPIs total (7 original + 2 TA)
- Adjusted tier 3 weights: 8% + 8% + 4% + 3% + 2% = 25%

✅ **Phase 5**: Optimization Rules Enhancement
- Added 3 TA-based rules (Rule 11-13)
- Rule 11: High overshoot → Reduce power
- Rule 12: High cell edge → Increase power
- Rule 13: Low avg TA → Alert for manual antenna adjustment
- Integrated TA issue detection into `detect_kpi_issues()` function

### What Was NOT Implemented (Future Enhancements)

❌ **Phase 4**: Enhanced LLM Prompting (433+ lines of prompt enhancements)
❌ **Phase 6**: NVIDIA Telco RAN Research Document
❌ **Phase 7**: Live Mode Configuration Updates
❌ **Phase 9**: Future Enhancements Roadmap

**Rationale**: Core functional components provide immediate value for testing. Prompt enhancements and documentation can be added iteratively based on real-world testing feedback.

---

## Test Objectives

### Test Objective 1: TA Data Validation

**Goal**: Verify TA data was imported correctly and is queryable

**Test Steps**:

1. **Verify Import Count**:
   ```bash
   cd lz-network-optimizer
   python -c "
   import sqlite3
   conn = sqlite3.connect('data/lz_network.db')
   cursor = conn.cursor()
   cursor.execute('SELECT COUNT(*) FROM timing_advance_data')
   print(f'Total TA records: {cursor.fetchone()[0]}')
   cursor.execute('SELECT COUNT(DISTINCT site_name) FROM timing_advance_data')
   print(f'Unique sites: {cursor.fetchone()[0]}')
   conn.close()
   "
   ```
   **Expected Output**: Total TA records: 2178, Unique sites: 4

2. **Verify Site List**:
   ```bash
   python -c "
   import sqlite3
   conn = sqlite3.connect('data/lz_network.db')
   cursor = conn.cursor()
   cursor.execute('SELECT DISTINCT site_name FROM timing_advance_data ORDER BY site_name')
   for row in cursor.fetchall():
       print(f'  - {row[0]}')
   conn.close()
   "
   ```
   **Expected Sites**:
   - MSH-0112-Bindura Hospital
   - MSH-0014-Chipadze
   - MSH0013-Bindura-Zaoga
   - MSH-0331-Chiwaridzo 2

3. **Spot-Check Calculation**:
   ```bash
   python -c "
   import sqlite3
   conn = sqlite3.connect('data/lz_network.db')
   cursor = conn.cursor()
   cursor.execute('''
       SELECT site_name, timestamp, total_ues, overshoot_percentage,
              cell_edge_percentage, avg_ta_index
       FROM timing_advance_data
       LIMIT 3
   ''')
   for row in cursor.fetchall():
       print(f'Site: {row[0]}')
       print(f'  Timestamp: {row[1]}')
       print(f'  Total UEs: {row[2]:,}')
       print(f'  Overshoot %: {row[3]:.2f}')
       print(f'  Cell Edge %: {row[4]:.2f}')
       print(f'  Avg TA Index: {row[5]:.2f}')
       print()
   conn.close()
   "
   ```
   **Expected**: Valid numbers, percentages in reasonable ranges (0-100%), avg TA index typically 4-7

4. **Test Query Tool**:
   ```bash
   python -c "
   from tools.sql_tools import query_ta_metrics
   result = query_ta_metrics.invoke({
       'site_name': 'MSH0013-Bindura-Zaoga',
       'days': 7
   })
   print(result)
   "
   ```
   **Expected**: Formatted table with TA distribution, summary statistics, warnings/alerts if applicable

**Success Criteria**:
- [ ] 2,178 records imported
- [ ] All 4 sites present
- [ ] Calculations are accurate (overshoot_percentage = (Index0 + Index10 + Index11) / total × 100)
- [ ] Query tool returns formatted, actionable data

---

### Test Objective 2: KPI Configuration Validation

**Goal**: Verify 9 KPIs are configured correctly with proper weights

**Test Steps**:

1. **Verify KPI Count**:
   ```bash
   python -c "
   from domain.liquid_zimbabwe_kpi import LiquidZimbabweKPIManager
   kpi_mgr = LiquidZimbabweKPIManager()
   print(f'Total KPIs: {len(kpi_mgr.kpi_config)}')
   print('\\nKPI List:')
   for kpi_name, config in kpi_mgr.kpi_config.items():
       print(f'  - {kpi_name}: {config[\"user_friendly_name\"]}')
   "
   ```
   **Expected**: Total KPIs: 9 (7 original + 2 TA-based)

2. **Verify Weight Sum**:
   ```bash
   python -c "
   import yaml
   with open('config/kpi_weights.yaml', 'r') as f:
       weights = yaml.safe_load(f)

   total_weight = sum(kpi['weight'] for kpi in weights['kpi_weights'].values())
   print(f'Total weight: {total_weight:.2f}')
   print(f'Expected: 1.00')
   print(f'Match: {abs(total_weight - 1.0) < 0.001}')
   "
   ```
   **Expected**: Total weight: 1.00, Match: True

3. **Test TA KPI Query Methods**:
   ```bash
   python -c "
   from domain.liquid_zimbabwe_kpi import LiquidZimbabweKPIManager
   kpi_mgr = LiquidZimbabweKPIManager()

   # Test get_ta_distribution
   ta_data = kpi_mgr.get_ta_distribution('MSH0013-Bindura-Zaoga', days=1)
   if ta_data:
       print(f'TA Distribution Retrieved:')
       print(f'  Total UEs: {ta_data[\"total_ues\"]:,}')
       print(f'  Overshoot %: {ta_data[\"overshoot_percentage\"]:.2f}')
       print(f'  Cell Edge %: {ta_data[\"cell_edge_percentage\"]:.2f}')
       print(f'  Avg TA Index: {ta_data[\"avg_ta_index\"]:.2f}')

   # Test check_ta_alerts
   alerts = kpi_mgr.check_ta_alerts('MSH0013-Bindura-Zaoga')
   print(f'\\nTA Alerts: {len(alerts)} detected')
   for alert in alerts:
       print(f'  - {alert[\"alert_level\"]}: {alert[\"message\"]}')
   "
   ```
   **Expected**: TA data retrieved, alerts generated if thresholds exceeded

**Success Criteria**:
- [ ] 9 KPIs configured
- [ ] Weights sum to exactly 1.0
- [ ] TA KPI methods return valid data
- [ ] Alert thresholds trigger correctly

---

### Test Objective 3: Optimization Rules Validation

**Goal**: Verify 13 rules are defined and TA rules trigger correctly

**Test Steps**:

1. **Verify Rule Count**:
   ```bash
   python -c "
   from domain.optimization_rules import OPTIMIZATION_RULES
   print(f'Total Rules: {len(OPTIMIZATION_RULES)}')
   print('\\nTA-Based Rules:')
   for rule_id in ['rule_11', 'rule_12', 'rule_13']:
       rule = OPTIMIZATION_RULES[rule_id]
       print(f'  {rule_id}: {rule.kpi_issue} → {rule.parameter_name} ({rule.adjustment_direction})')
   "
   ```
   **Expected**: Total Rules: 13, TA rules (11-13) listed with correct parameters

2. **Test TA Issue Detection**:
   ```bash
   python -c "
   from domain.optimization_rules import detect_kpi_issues

   # Test high overshoot scenario
   kpis_high_overshoot = {
       'ta_overshoot_percentage': 18.0,  # Above 10% threshold
       'cell_edge_percentage': 15.0,
       'avg_timing_advance': 5.5
   }
   thresholds = {'ta_overshoot_max': 10.0, 'cell_edge_max': 20.0, 'avg_ta_min': 3.0}
   issues = detect_kpi_issues(kpis_high_overshoot, thresholds)
   print(f'High Overshoot Test: {\"high_ta_overshoot\" in issues} (Expected: True)')

   # Test high cell edge scenario
   kpis_high_cell_edge = {
       'ta_overshoot_percentage': 8.0,
       'cell_edge_percentage': 25.0,  # Above 20% threshold
       'avg_timing_advance': 7.2
   }
   issues = detect_kpi_issues(kpis_high_cell_edge, thresholds)
   print(f'High Cell Edge Test: {\"high_cell_edge\" in issues} (Expected: True)')

   # Test low avg TA scenario
   kpis_low_avg_ta = {
       'ta_overshoot_percentage': 8.0,
       'cell_edge_percentage': 15.0,
       'avg_timing_advance': 2.5  # Below 3.0 threshold
   }
   issues = detect_kpi_issues(kpis_low_avg_ta, thresholds)
   print(f'Low Avg TA Test: {\"low_avg_ta\" in issues} (Expected: True)')
   "
   ```
   **Expected**: All three tests return True

3. **Test Rule Matching**:
   ```bash
   python -c "
   from domain.optimization_rules import find_applicable_rules

   # Test high overshoot rule matching
   kpi_issues = ['high_ta_overshoot']
   rules = find_applicable_rules(kpi_issues)
   if rules:
       rule = rules[0]
       print(f'Rule Matched: {rule.rule_id}')
       print(f'  KPI Issue: {rule.kpi_issue}')
       print(f'  Parameter: {rule.parameter_name}')
       print(f'  Direction: {rule.adjustment_direction}')
       print(f'  Confidence: {rule.confidence}')
   "
   ```
   **Expected**: Rule 11 matched, decrease reference_signal_power, confidence 0.85

**Success Criteria**:
- [ ] 13 optimization rules defined
- [ ] TA issue detection triggers correctly for all 3 scenarios
- [ ] Rule matching returns correct rules for TA issues
- [ ] Rule 13 (low_avg_ta) has adjustment_direction="alert_only"

---

### Test Objective 4: End-to-End Integration Test

**Goal**: Verify TA data flows through full optimization workflow

**Test Steps**:

1. **Manual Workflow Test** (using Python REPL):
   ```bash
   python
   ```
   ```python
   from domain.liquid_zimbabwe_kpi import LiquidZimbabweKPIManager
   from domain.optimization_rules import detect_kpi_issues, find_applicable_rules
   from tools.sql_tools import get_ta_metrics_direct

   # Step 1: Get TA data for a site
   site = "MSH0013-Bindura-Zaoga"
   ta_data = get_ta_metrics_direct(site, days=1)
   if ta_data:
       latest = ta_data[0]
       print(f"Site: {site}")
       print(f"Overshoot: {latest['overshoot_percentage']:.2f}%")
       print(f"Cell Edge: {latest['cell_edge_percentage']:.2f}%")
       print(f"Avg TA: {latest['avg_ta_index']:.2f}")

   # Step 2: Detect issues
   kpis = {
       'ta_overshoot_percentage': latest['overshoot_percentage'],
       'cell_edge_percentage': latest['cell_edge_percentage'],
       'avg_timing_advance': latest['avg_ta_index']
   }
   thresholds = {
       'ta_overshoot_max': 10.0,
       'cell_edge_max': 20.0,
       'avg_ta_min': 3.0
   }
   issues = detect_kpi_issues(kpis, thresholds)
   print(f"\nDetected Issues: {issues}")

   # Step 3: Find applicable rules
   rules = find_applicable_rules(issues)
   print(f"\nApplicable Rules: {len(rules)}")
   for rule in rules:
       print(f"  - {rule.rule_id}: {rule.description[:80]}...")
   ```

2. **Verify Alert Generation**:
   ```python
   # Test KPI alert system
   kpi_mgr = LiquidZimbabweKPIManager()
   alerts = kpi_mgr.check_ta_alerts(site)
   print(f"\nTA Alerts Generated: {len(alerts)}")
   for alert in alerts:
       print(f"  [{alert['alert_level']}] {alert['kpi_name']}: {alert['message']}")
   ```

3. **Test Real Data Across All Sites**:
   ```bash
   python -c "
   from domain.liquid_zimbabwe_kpi import LiquidZimbabweKPIManager

   kpi_mgr = LiquidZimbabweKPIManager()
   sites = ['MSH0013-Bindura-Zaoga', 'MSH-0331-Chiwaridzo 2',
            'MSH-0112-Bindura Hospital', 'MSH-0014-Chipadze']

   for site in sites:
       ta_data = kpi_mgr.get_ta_distribution(site, days=1)
       if ta_data:
           print(f'{site}:')
           print(f'  Overshoot: {ta_data[\"overshoot_percentage\"]:.1f}%', end='')
           print(' ⚠️ HIGH' if ta_data['overshoot_percentage'] > 10 else ' ✓')
           print(f'  Cell Edge: {ta_data[\"cell_edge_percentage\"]:.1f}%', end='')
           print(' ⚠️ HIGH' if ta_data['cell_edge_percentage'] > 20 else ' ✓')
           print(f'  Avg TA: {ta_data[\"avg_ta_index\"]:.2f}')
       print()
   "
   ```

**Success Criteria**:
- [ ] TA data flows from database → KPI manager → issue detection → rule matching
- [ ] Alerts are generated and stored in kpi_alerts table
- [ ] All 4 sites can be queried and analyzed
- [ ] System identifies coverage issues correctly

---

## System Status After Core Implementation

### ✅ Functional Components

| Component | Status | Description |
|-----------|--------|-------------|
| TA Data Table | ✅ Complete | 27-column schema with indexes |
| TA Data Import | ✅ Complete | 2,178 records, 4 sites, 24 cells |
| TA Query Tool | ✅ Complete | LangChain tool for LLM agents |
| TA KPIs | ✅ Complete | 2 new KPIs added to system |
| KPI Weights | ✅ Complete | 9 KPIs, weights sum to 1.0 |
| TA Optimization Rules | ✅ Complete | 3 new rules (11-13) |
| Issue Detection | ✅ Complete | TA issues integrated |
| Alert System | ✅ Complete | TA alerts generated and stored |

### 🚧 Pending Enhancements (Optional)

| Component | Status | Priority |
|-----------|--------|----------|
| Enhanced Agent Prompts | ⏸️ Deferred | Medium |
| TA Context Builder | ⏸️ Deferred | Medium |
| Few-Shot Examples | ⏸️ Deferred | Low |
| NVIDIA Research Doc | ⏸️ Deferred | Low |
| Live Mode Config | ⏸️ Deferred | High (if deploying) |
| Rollback Enhancement | ⏸️ Deferred | High (if deploying) |

---

## Next Steps

### Immediate (Testing Phase)

1. **Run All 4 Test Objectives** above to validate core functionality
2. **Review TA Data** for each site to understand baseline coverage patterns
3. **Simulate TA-Based Optimizations** using Python REPL to verify rule logic
4. **Document Findings** in testing report

### Short-Term (If Testing Successful)

1. **Phase 4**: Add enhanced LLM prompts with TA awareness (433 lines)
2. **Phase 7**: Configure live mode (disable demo, enable auto-rollback)
3. **Test Live Optimization**: Run 3-5 low-risk optimizations with engineer approval

### Long-Term (Post-Testing)

1. **Phase 6**: NVIDIA Telco RAN best practices research and integration
2. **Phase 9**: Future enhancements roadmap (additional parameters, KPIs, ML integration)
3. **Iterative Improvement**: Refine rules based on real-world outcomes

---

## Troubleshooting

### Issue: "No TA data found for site"

**Cause**: Site name mismatch or no data for date range
**Solution**:
```bash
# Check available sites
python -c "
import sqlite3
conn = sqlite3.connect('data/lz_network.db')
cursor = conn.cursor()
cursor.execute('SELECT DISTINCT site_name FROM timing_advance_data')
print([row[0] for row in cursor.fetchall()])
"
```

### Issue: "Module not found" errors

**Cause**: Not running from lz-network-optimizer directory
**Solution**: `cd lz-network-optimizer` before running tests

### Issue: KPI weights don't sum to 1.0

**Cause**: YAML file not updated correctly
**Solution**: Verify in `config/kpi_weights.yaml`:
- Tier 1: 0.25
- Tier 2: 0.50
- Tier 3: 0.25 (0.08 + 0.08 + 0.04 + 0.03 + 0.02)

---

## Contact & Support

For questions or issues during testing:
- **Review**: Implementation plan at `/Users/fadzai/.claude/plans/breezy-shimmying-crescent.md`
- **Check Logs**: System logs include TA import and query details
- **Database**: Direct SQL queries to `data/lz_network.db` for debugging

---

**Document Version**: 1.0
**Last Updated**: 2026-01-12
**Next Review**: After completing Test Objectives 1-4
