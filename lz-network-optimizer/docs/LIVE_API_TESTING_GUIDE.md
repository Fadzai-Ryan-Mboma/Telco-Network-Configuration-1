# Live Huawei API Testing Guide

## Overview

The live Huawei API test suite (`tests/test_live_huawei_api.py`) validates the LZ Network Optimizer's integration with the Huawei iMaster MAE API using **REAL network hardware**.

**⚠️ WARNING**: These tests modify actual network parameters. Only run on designated test sites with low traffic.

## Prerequisites

### 1. Test Environment Access

- Access to Huawei iMaster MAE test environment
- OAuth2 credentials (username, password, API URL)
- Designated test site with minimal traffic impact

### 2. Environment Configuration

Create `.env` file with:

```bash
# Huawei API Configuration
HUAWEI_API_URL="https://your-huawei-test-api.example.com"
HUAWEI_USERNAME="your-test-username"
HUAWEI_PASSWORD="your-test-password"

# Test Site (can be overridden via command line)
TEST_SITE="MSH-0112-Bindura Hospital"
```

### 3. Python Dependencies

```bash
pip install pytest python-dotenv
```

## Test Suite Structure

### Test Classes

1. **TestLiveAuthentication**
   - OAuth2 token retrieval
   - Token auto-refresh on expiry
   - Credential validation

2. **TestParameterQuery**
   - Query single parameter (reference signal power)
   - Query all 5 tunable parameters
   - MML response parsing

3. **TestParameterModification**
   - Modify power parameter (+1 dB safe change)
   - Modify timer parameter (+1000 ms safe change)
   - Automatic baseline capture and restoration

4. **TestKPICollection**
   - KPI collection via MML (known to be unreliable)
   - Fallback mechanism validation

## Running the Tests

### Basic Usage

```bash
# Run all tests (uses default test site from .env)
pytest tests/test_live_huawei_api.py -v -s

# Specify test site via command line
pytest tests/test_live_huawei_api.py -v -s --test-site="MSH-0112-Bindura Hospital"

# Run specific test class
pytest tests/test_live_huawei_api.py::TestLiveAuthentication -v -s

# Run specific test
pytest tests/test_live_huawei_api.py::TestParameterQuery::test_query_all_parameters -v -s
```

### Advanced Options

```bash
# Skip restoration (DANGEROUS - only for debugging)
pytest tests/test_live_huawei_api.py -v -s --test-site="TEST-SITE" --no-restore

# Verbose output with timing
pytest tests/test_live_huawei_api.py -v -s --tb=short --durations=10

# Stop on first failure
pytest tests/test_live_huawei_api.py -v -s -x
```

## Safety Mechanisms

### 1. Automatic Baseline Capture

Before each test in `TestParameterModification`, the system:
- Queries current values for all 5 parameters
- Stores baseline values
- Uses these for restoration after test

### 2. Conservative Parameter Changes

Maximum changes enforced:
- **Power parameters**: ±1 dB (±10 units in 0.1 dB scale)
- **Timer parameters**: ±1000 ms (±1 second)
- **Offset parameters**: ±2 units

### 3. Automatic Restoration

After each test:
- All parameters restored to baseline values
- Restoration verified via query
- Manual intervention flagged if restoration fails

### 4. Test Site Isolation

- Only specified test site is modified
- Other sites remain untouched
- Single cell ID tested (default: Cell 1)

## Expected Test Results

### Successful Run

```
============================================================
LIVE HUAWEI API TEST SUITE
============================================================
⚠️  WARNING: This test suite modifies REAL network parameters
Test Site: MSH-0112-Bindura Hospital
Test Cell ID: 1
Restore After Test: True
============================================================

TEST 1: AUTHENTICATION
✅ Token obtained: eyJhbGciOiJSUzI1NiIsInR5cCI6...
✅ Token length: 847 characters
PASSED

TEST 2: TOKEN AUTO-REFRESH
⏰ Forced token expiry
✅ Token auto-refresh works
PASSED

TEST 3: QUERY SINGLE PARAMETER
📝 Executing: DSP PDSCHCFG: LOCALCELLID=1;
✅ Query successful
✅ Parsed value: 150
PASSED

TEST 4: QUERY ALL PARAMETERS
📝 Testing: reference_signal_power_pdschcfg
   ✅ Query successful
📝 Testing: p0_nominal_pusch
   ✅ Query successful
...
SUMMARY: 5/5 parameter queries succeeded
PASSED

TEST 5: MODIFY POWER PARAMETER
📸 Capturing baseline configuration...
   ✅ reference_signal_power_pdschcfg: 150
   ✅ p0_nominal_pusch: -85
   ...
📸 Baseline captured: 5 parameters

📊 Baseline value: 150
📊 Test value: 160
📊 Change: +10.0 (+6.7%)
📝 Executing: MOD PDSCHCFG: LOCALCELLID=1, REFERENCESIGNALPWR=160;
✅ Modification command succeeded
⏳ Waiting 3 seconds for parameter propagation...
✅ Verified new value: 160
✅ Parameter modified successfully: 150 → 160

🔄 RESTORING BASELINE CONFIGURATION
📝 Restoring reference_signal_power_pdschcfg to 150...
   ✅ Restored reference_signal_power_pdschcfg
...
✅ BASELINE RESTORATION COMPLETE
PASSED

TEST 6: MODIFY TIMER PARAMETER
...
PASSED

TEST 7: KPI COLLECTION VIA MML
⚠️  KPI collection via MML failed (expected behavior)
→ System will fallback to database as designed
PASSED
```

### Common Failures and Fixes

#### Authentication Failure
```
AssertionError: Token should not be None
```
**Fix**: Verify `HUAWEI_API_URL`, `HUAWEI_USERNAME`, `HUAWEI_PASSWORD` in `.env`

#### Query Failure
```
AssertionError: Query failed: HTTP 404 - Site not found
```
**Fix**: Verify test site name is correct, check site exists in iMaster MAE

#### Modification Failure
```
AssertionError: Modification failed: Parameter out of range
```
**Fix**: Current value + test change exceeds parameter bounds. System should prevent this, but may need adjustment in `_safe_parameter_change()`

#### Parsing Failure
```
⚠️  Could not parse 'REFERENCESIGNALPWR' from MML output
```
**Fix**: Huawei MML response format differs from expected. Update `_parse_parameter_value()` with actual format.

## Troubleshooting

### Issue: Tests hang indefinitely

**Cause**: Huawei API not responding
**Fix**:
1. Check network connectivity
2. Verify API endpoint is accessible: `curl https://your-api-url/health`
3. Check if test site is locked by another operation

### Issue: Restoration fails

**Symptom**: "MANUAL RESTORATION REQUIRED!" message
**Immediate Action**:
1. Note the rollback_id from test output
2. Manually restore via Huawei iMaster MAE UI
3. Or use rollback tool: `python -c "from tools.rollback_manager import execute_rollback; execute_rollback('rollback_id')"`

### Issue: Parameter changes not verified

**Cause**: Huawei system propagation delay or rounding
**Fix**:
1. Increase wait time in test (currently 3s)
2. Check tolerance in assertion (currently 1%)
3. Manually verify via iMaster MAE UI

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Live API Tests

on:
  schedule:
    - cron: '0 2 * * 1'  # Weekly, Monday 2 AM
  workflow_dispatch:  # Manual trigger

jobs:
  live-api-test:
    runs-on: ubuntu-latest
    environment: test  # Requires approval

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest

      - name: Run Live API Tests
        env:
          HUAWEI_API_URL: ${{ secrets.HUAWEI_API_URL }}
          HUAWEI_USERNAME: ${{ secrets.HUAWEI_USERNAME }}
          HUAWEI_PASSWORD: ${{ secrets.HUAWEI_PASSWORD }}
          TEST_SITE: "MSH-0112-Bindura Hospital"
        run: |
          pytest tests/test_live_huawei_api.py -v -s --junitxml=test-results.xml

      - name: Upload Test Results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results.xml
```

## Best Practices

### 1. Test Site Selection

- **DO**: Use low-traffic rural sites
- **DO**: Use sites with backup coverage
- **DON'T**: Use urban sites during business hours
- **DON'T**: Use sites serving critical infrastructure

### 2. Test Timing

- **Best**: Overnight (2-5 AM)
- **OK**: Weekends, off-peak hours
- **AVOID**: Business hours (9 AM - 5 PM)
- **AVOID**: Special events, holidays

### 3. Change Magnitude

- **First test**: Minimal changes (±1 dB, ±500 ms)
- **Validated system**: Moderate changes (±2 dB, ±1000 ms)
- **Never**: Large changes (>±3 dB, >±2000 ms)

### 4. Monitoring

- Monitor KPIs during test
- Have rollback plan ready
- Keep engineer on standby
- Document any anomalies

## Test Results Documentation

After each test run, document:

1. **Date/Time**: When tests were run
2. **Test Site**: Which site was used
3. **Pass/Fail**: Overall results
4. **Response Formats**: Actual MML response formats encountered
5. **Parsing Issues**: Any parameters that couldn't be parsed
6. **Restoration**: Whether automatic restoration succeeded
7. **Anomalies**: Any unexpected behavior

Example test report:

```markdown
## Test Run: 2025-01-13 02:00 AM

**Site**: MSH-0112-Bindura Hospital
**Cell ID**: 1
**Duration**: 3 minutes 47 seconds

### Results
- ✅ Authentication: PASSED
- ✅ Parameter Queries: PASSED (5/5)
- ✅ Power Modification: PASSED
- ✅ Timer Modification: PASSED
- ⚠️  KPI Collection: FAILED (expected)
- ✅ Restoration: PASSED

### Response Format Observations
- Reference signal power: `REFERENCESIGNALPWR=150` (matches expected)
- T310 timer: `T310TIMER=MS2000_T310` (enum format, not numeric)
- Need to update parser for enum handling

### Action Items
- Update `_parse_parameter_value()` to handle enum formats
- Increase propagation wait time to 5 seconds
- Document T310 timer enum mapping
```

## Future Enhancements

### Phase 1 (Current)
- ✅ Basic authentication tests
- ✅ Single parameter modification
- ✅ Automatic restoration

### Phase 2 (Planned)
- Multiple parameter modifications
- Concurrent multi-site testing
- KPI impact verification
- Rollback tool integration

### Phase 3 (Future)
- Load testing (100+ modifications)
- Stress testing (rapid changes)
- Edge case validation (boundary values)
- Performance benchmarking

## Emergency Procedures

### If Tests Cause Network Incident

1. **Immediate**: Stop pytest (`Ctrl+C`)
2. **Emergency Rollback**:
   ```bash
   python tools/rollback_manager.py --site "TEST-SITE" --latest
   ```
3. **Manual Verification**: Check iMaster MAE UI
4. **Document**: Record what happened
5. **Notify**: Alert network operations team
6. **Investigation**: Root cause analysis

### If Restoration Fails

1. **Get Baseline Values**: Check test output for captured values
2. **Manual Restore via UI**: Use iMaster MAE web interface
3. **Verify Restoration**: Query parameters to confirm
4. **Document Incident**: Create post-mortem report

## Support

For issues with live API testing:

1. Check this guide first
2. Review test output logs
3. Consult Huawei iMaster MAE documentation
4. Contact network engineering team
5. Open issue in project repository with:
   - Full test output
   - Environment details
   - MML responses
   - Expected vs actual behavior

## References

- [Huawei iMaster MAE Documentation](https://support.huawei.com)
- [MML Command Reference](../domain/mml_commands.py)
- [Rollback Manager](../tools/rollback_manager.py)
- [Production Readiness Plan](../docs/PRODUCTION_READINESS_PLAN.md)
