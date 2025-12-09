# LZ Network Optimizer - RF Engineering Demo Guide

**Target Audience:** RF Engineers, Network Operations Teams  
**Demo Duration:** 15-20 minutes  
**Last Updated:** November 26, 2025

---

## Quick Start

1. **Launch Application:**
   ```bash
   cd lz-network-optimizer
   streamlit run ui/app.py
   ```

2. **Select Site:** `MSH-0014-Chipadze` (default demo site with realistic data)

3. **Run Scenarios Below** (in order for best flow)

---

## Scenario 1: Low Download Throughput (Most Common)

### **Demo Prompt:**
```
improve download speed for MSH-0014-Chipadze
```

### **Expected Results:**

**KPI Analysis:**
- Weighted Score: **71.2/100 (FAIR)**
- Primary Issue: **Low DL Throughput** (15.8 Mbps, target: 25 Mbps)
- Root Cause: Insufficient coverage at cell edge → Poor SINR → Low MCS
- Cell Edge RSRP: **-104 dBm** (weak signal)
- DL IBLER: **17.2%** (elevated error rate)

**Configuration Recommendations:**
- **Reference Signal Power:** -1.0 dBm → +1.0 dBm (+2 dBm increase)
- **PDCCH SINR Offset:** 12 dB → 8 dB (-4 dB, more aggressive scheduling)
- Risk Level: **LOW (2.8/10)**

**Validation:**
- ✅ **APPROVED** - All parameters within safe ranges
- Neighbor interference: +0.7 dB (acceptable)
- Equipment utilization: +12% PA usage (within specs)

**Expected Improvements:**
```
DL Throughput:    15,800 → 19,200 kbit/s  (+21%, +3,400 kbit/s)
Cell Edge RSRP:   -104 dBm → -102 dBm     (+2 dB improvement)
DL Quality:       82.8% → 85.7%            (+2.9pp)
PDCCH CCE Load:   52% → 44%                (-8pp efficiency gain)
Coverage Radius:  820m → 885m              (+65m, +7.9%)
KPI Score:        71.2 → 79.8/100          (+8.6 points)
```

**Key Technical Points:**
- Link budget: +2 dB MAPL improvement
- MCS distribution: 20% users upgrade QPSK → 16-QAM
- HARQ retransmissions: -28% reduction
- LTE Band 3 (1800 MHz), Urban-Hilly terrain

---

## Scenario 2: Critical Network Access Failure

### **Demo Prompt:**
```
fix network access issues at MSH-0014-Chipadze
```

### **Expected Results:**

**KPI Analysis:**
- Weighted Score: **52.3/100 (CRITICAL)**
- Primary Issue: **Network Access** (88.2%, target: 95%)
- Root Cause: Severe coverage gap + weak signal + late handovers
- Cell Edge RSRP: **-109 dBm** (below receiver sensitivity)
- Cell Edge SINR: **-2 dB** (cannot maintain connection)
- RLF Rate: **3.2%** (high radio link failures)

**Configuration Recommendations:**
- **Reference Signal Power:** -5.0 dBm → -2.0 dBm (+3 dBm EMERGENCY increase)
- **T310 Timer:** 1000 ms → 2000 ms (+1000 ms, reduce premature RLF)
- **A3 Handover Offset:** 3 dB → 2 dB (-1 dB, earlier handover triggering)
- Risk Level: **MEDIUM (5.5/10)** - Justified for critical situation

**Validation:**
- ✅ **APPROVED WITH MONITORING** - Large change but critical need
- Enhanced monitoring: 15-min KPI checks for 72 hours
- Network engineer on standby first 48 hours
- Neighbor interference: +1.8 dB to MSH-0112 (moderate, monitored)

**Expected Improvements:**
```
Network Access:   88.2% → 95.8%            (+7.6pp RECOVERED)
DL Throughput:    12,300 → 17,800 kbit/s  (+45%, +5,500 kbit/s)
Cell Edge RSRP:   -109 dBm → -106 dBm     (+3 dB recovery)
Cell Edge SINR:   -2 dB → +1 dB            (+3 dB, now usable!)
RLF Rate:         3.2% → 1.1%              (-66% reduction)
Coverage Area:    1.33 km² → 2.01 km²     (+51% expansion)
KPI Score:        52.3 → 76.1/100          (+23.8 points)
```

**Key Technical Points:**
- Emergency optimization - aggressive but justified
- Coverage hole: 15% area → 3% area (-80% reduction)
- Handover success to MSH-0112: 89.2% → 96.1%
- T310 extension prevents premature disconnections

---

## Scenario 3: Low Upload Performance

### **Demo Prompt:**
```
optimize upload speed for MSH-0014-Chipadze
```

### **Expected Results:**

**KPI Analysis:**
- Weighted Score: **74.5/100 (FAIR)**
- Primary Issue: **Low UL Throughput** (4.8 Mbps, target: 8.0 Mbps)
- Root Cause: Conservative uplink power control (P0 too low)
- UE Power Headroom: **12 dB average** (excessive margin, underutilized)
- Current UE Tx Power: **14 dBm** (well below 23 dBm max capability)

**Configuration Recommendations:**
- **P0 Nominal PUSCH:** -96 dBm → -90 dBm (+6 dBm increase)
- Risk Level: **LOW (3.2/10)**

**Validation:**
- ✅ **APPROVED** - Safe parameter change
- UE power headroom post-change: 6 dB (healthy margin)
- All UEs within 23 dBm regulatory limit
- Uplink IoT to neighbors: +0.9 dB (acceptable)

**Expected Improvements:**
```
UL Throughput:    4,800 → 6,800 kbit/s    (+42%, +2,000 kbit/s)
UL Quality:       90.8% → 93.9%            (+3.1pp)
UE Tx Power:      14 dBm → 18 dBm          (+4 dBm, better utilization)
PUSCH SINR:       11.2 dB → 13.8 dB        (+2.6 dB improvement)
Cell Edge UL:     1,400 → 1,900 kbit/s    (+36% edge improvement)
KPI Score:        74.5 → 82.3/100          (+7.8 points)
```

**Key Technical Points:**
- MCS upgrade: 55% QPSK → 35% QPSK (20% users shift to 16-QAM)
- UE battery: +6-8% consumption (acceptable trade-off)
- HARQ retransmissions (UL): -36% reduction
- Spectral efficiency: 2.1 → 2.9 bps/Hz (+38%)

---

## Scenario 4: Poor Download Quality

### **Demo Prompt:**
```
improve quality for MSH-0014-Chipadze
```

### **Expected Results:**

**KPI Analysis:**
- Weighted Score: **73.8/100 (FAIR)**
- Primary Issue: **Poor DL Quality** (IBLER 20.5%, target: <5%)
- Root Cause: PDCCH congestion → Excessive aggregation levels
- PDCCH CCE Load: **58%** (elevated, near saturation)
- Average Aggregation Level: **5.1** (high CCE waste)
- PDCCH Blocking: **4.2%** (target: <2%)

**Configuration Recommendations:**
- **PDCCH SINR Offset:** 12 dB → 6 dB (-6 dB, -50% reduction)
- Risk Level: **LOW (3.5/10)**

**Validation:**
- ✅ **APPROVED** - Efficiency optimization
- Cell-edge PDCCH BLER: +0.9pp (minor, acceptable)
- Overall throughput improvement outweighs edge impact
- Monitor for 48 hours, can adjust to 8 dB if needed

**Expected Improvements:**
```
DL Quality:       79.5% → 89.3%            (+9.8pp via reduced retx)
DL IBLER:         20.5% → 10.7%            (-9.8pp major improvement)
DL Throughput:    18,200 → 19,600 kbit/s  (+7.7%, +1,400 kbit/s)
PDCCH CCE Load:   58% → 41%                (-17pp resource efficiency)
PDCCH Blocking:   4.2% → 1.9%              (-55% reduction)
Avg AL:           5.1 → 3.2                 (-37% CCE consumption)
KPI Score:        73.8 → 83.6/100          (+9.8 points)
```

**Key Technical Points:**
- AL distribution shift: 29% AL8 → 8% AL8 (reserve for weak UEs only)
- DCI grants per TTI: 8.2 → 11.8 (+44% more users scheduled)
- Scheduler efficiency: Dramatically improved
- Average latency: 42 ms → 35 ms (-17%)

---

## Demo Talking Points

### **For RF Engineers:**

1. **Realistic Data:**
   - Based on actual Bindura network KPIs (historical_data.csv)
   - Throughput in kbit/s (not inflated Mbps)
   - RACH values realistic (88-99%, not impossible low values)
   - Reference signal power realistic (-5 to +1 dBm range)

2. **RF Engineering Fundamentals:**
   - Link budget calculations shown (MAPL, path loss models)
   - Coverage analysis: Okumura-Hata for LTE 1800 MHz
   - SINR-to-MCS relationships explained
   - Neighbor cell interference quantified (+0.7 to +1.8 dB IoT)

3. **Layer-by-Layer Analysis:**
   - PHY: Modulation distribution, spectral efficiency
   - MAC: HARQ, PRB utilization, scheduler efficiency
   - RRC: Connection stability, RLF rates, handover success

4. **Risk Assessment:**
   - Quantified risk scores (1-10 scale)
   - Equipment limits checked (PA utilization, thermal)
   - Neighbor impact analyzed (specific sites, distances)
   - Rollback plans ready (5-minute reversion)

### **Key Differentiators:**

✅ **Technically Accurate:** Real RF engineering calculations  
✅ **Production-Ready:** Actual MML commands for Huawei eNodeB  
✅ **Risk-Aware:** Multi-level validation before execution  
✅ **Observable:** Complete KPI tracking pre/post optimization  
✅ **Traceable:** Full audit trail, rollback capability  

---

## Common Questions

**Q: Why kbit/s instead of Mbps?**  
A: Your KPI definition uses kbit/s (DL Cell PDCP Layer Average Throughput). 15,800 kbit/s = 15.8 Mbps cell average, which is realistic for shared LTE.

**Q: Are the improvement percentages realistic?**  
A: Yes. Single-parameter changes: 5-15%. Multi-parameter: 15-30%. Our scenarios show 12-45% based on severity and number of parameters changed.

**Q: Why not just increase power to maximum?**  
A: Trade-offs:
- Neighbor interference increases
- Equipment stress (PA utilization)
- Pilot pollution in overlap areas
- Regulatory compliance
- Power consumption

**Q: Can this run on live network?**  
A: Yes, but requires:
- OAuth2 credentials to Huawei U2000 NMS
- Production database connection
- Change approval workflow
- Enhanced monitoring active
- Network engineer on standby

---

## Notes

- All scenarios use **DRY RUN mode** (simulation only)
- No actual network changes applied in demo
- Real deployment requires approval workflow
- Historical data: September 2025 Bindura network
- Site: MSH-0014-Chipadze (6-cell LTE site)

---

**End of Demo Guide**
