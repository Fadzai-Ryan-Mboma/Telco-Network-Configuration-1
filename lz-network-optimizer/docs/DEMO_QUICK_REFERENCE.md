# Quick Demo Reference Card

## 🎯 Bindura Zaoga Current Parameters (Baseline)
```
Signal Power:  152 (15.2 dBm)
A3 Offset:     3 dB
T310 Timer:    1000 ms
P0 PUSCH:      -67 dBm
PDCCH Agg:     CONGREG_LV4
```

## 🎯 4 Demo Scenarios - Quick Reference

### 1️⃣ LOW DOWNLOAD SPEED (Most Common)
**Prompt:** `improve download speed for Bindura Zaoga`
```
Issue:     Download below target
Current:   RS Power 152 (15.2 dBm)
Fix:       RS Power 152 → 172 (+2 dBm)
Result:    +15-25% download speed
Risk:      LOW (2.8/10)
Key Fact:  Coverage +65m, better cell-edge SINR
```

### 2️⃣ CRITICAL ACCESS FAILURE (Emergency)
**Prompt:** `fix network access issues at Bindura Zaoga`
```
Issue:     Access below 95% threshold
Current:   RS Power 152, T310 1000ms, A3 3dB
Fix:       RS Power +3 dBm + T310 → 2000ms + A3 → 2dB
Result:    Access +5-7%
Risk:      MEDIUM (5.5/10) - 72hr monitoring
Key Fact:  Improved coverage, reduced RLF
```

### 3️⃣ LOW UPLOAD SPEED
**Prompt:** `optimize upload speed for Bindura Zaoga`
```
Issue:     Upload below target
Current:   P0 PUSCH -67 dBm
Fix:       P0 PUSCH -67 → -61 dBm (+6 dB)
Result:    Upload +20-30%
Risk:      LOW (3.2/10)
Key Fact:  UE power boost, better uplink SINR
```

### 4️⃣ PDCCH OPTIMIZATION
**Prompt:** `improve quality for Bindura Zaoga`
```
Issue:     Control channel load high
Current:   PDCCH Level 4 (CONGREG_LV4)
Fix:       Optimize PDCCH SINR offset
Result:    Better CCE efficiency
Risk:      LOW (3.5/10)
Key Fact:  Scheduler optimization
```

---

## 📊 What Engineers Will See

### KPI Analysis (Agent 1-2)
✅ Weighted 3-tier scoring (Foundation/Revenue/Efficiency)  
✅ RSRP, SINR, MCS distribution, Power headroom  
✅ Root cause with RF engineering justification  

### Configuration (Agent 3)
✅ Link budget calculations (MAPL, coverage radius)  
✅ Realistic parameters (-5 to +1 dBm RS power)  
✅ Layer analysis (PHY/MAC/RRC)  

### Validation (Agent 4)
✅ Risk scoring (1-10 scale)  
✅ Neighbor cell interference quantified  
✅ Equipment limits checked  

### Execution (Agent 5-6)
✅ Real Huawei MML commands  
✅ Before/after KPIs with deltas  
✅ Rollback plan ready  

---

## 🔧 Technical Highlights to Mention

**"Unlike basic optimizers, this shows..."**

1. **Real RF Engineering:**
   - Okumura-Hata path loss for LTE 1800 MHz
   - SINR-to-MCS mapping (QPSK/16-QAM/64-QAM)
   - Link budget: Tx power + gain - path loss

2. **Production Parameters:**
   - Reference Signal Power: 0.1 dBm units (-5 to +1 dBm realistic)
   - P0 Nominal PUSCH: -126 to +24 dBm range
   - PDCCH SINR Offset: NOT aggregation level (common mistake)

3. **Neighbor Impact:**
   - MSH-0112-Bindura Hospital: 1.2 km, +0.7 to +1.8 dB IoT
   - Handover ping-pong risk quantified (+8-12%)
   - Pilot pollution zones identified

4. **Risk Management:**
   - Multi-level validation (range, magnitude, history, conflicts)
   - Automatic rollback triggers (access -5%, throughput -10%)
   - Enhanced monitoring plans (15-min intervals, 72 hours)

---

## ❓ Expected Questions & Answers

**Q: "Why kbit/s not Mbps?"**  
A: KPI definition from Huawei counters: "DL Cell PDCP Layer Average Throughput(kbit/s)". 15,800 kbit/s = 15.8 Mbps cell average (realistic for shared LTE).

**Q: "88% access rate seems high for 'critical'?"**  
A: 88% means 12% connection failures. In telecom, <95% is critical (target: 98-99%). 5.5% would mean site shutdown.

**Q: "Can you just max out power?"**  
A: Trade-offs: Neighbor interference (+1.8 dB shown), equipment stress (PA %), pilot pollution, regulations, power cost. We optimize within constraints.

**Q: "How do you know these improvements are real?"**  
A: Based on historical optimization data (success rates shown: 84-91%), 3GPP specs, and validated RF propagation models. Real deployment validates further.

**Q: "PDCCH Aggregation Level isn't configurable?"**  
A: Correct! It's dynamic (scheduler-selected). We configure **PDCCH SINR Offset** which influences scheduler's AL selection. Old systems got this wrong.

---

## 🎬 Demo Flow (15 min)

**Minutes 1-3:** Overview
- Explain 6-agent workflow (Monitoring → KPI → Config → Validation → MML → Execution)
- Show MSH-0014-Chipadze site selection

**Minutes 4-7:** Scenario 1 (Low Download)
- Run query, pause at each agent output
- Highlight: Link budget, coverage calculation, MCS distribution
- Show MML commands, explain Huawei syntax

**Minutes 8-11:** Scenario 2 (Critical Access)
- Emphasize emergency nature (88.2% → 95.8%)
- Show multi-parameter approach (power + timer + handover)
- Explain medium risk justification

**Minutes 12-14:** Scenario 3 or 4 (Quick)
- Pick based on audience interest
- Upload: Good for power/battery discussion
- Quality: Good for scheduler/resource discussion

**Minutes 14-15:** Q&A + Next Steps
- Production deployment requirements
- Live API integration status
- Custom optimization scenarios

---

## 💡 Key Selling Points

1. **RF Engineering Accurate** - Not just AI hype, real telecom knowledge
2. **Production Ready** - Actual Huawei MML commands, not pseudo-code
3. **Risk Aware** - Multi-level safety checks, rollback capability
4. **Transparent** - Full visibility into decision-making process
5. **Realistic** - Based on actual Liquid Zimbabwe network data

---

**Print this card before demos!** 📄
