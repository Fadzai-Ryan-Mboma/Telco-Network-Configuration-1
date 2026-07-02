Claude Assessment

---

# NetGenix — Comprehensive Audit Report
**Auditor:** AI Testing Agent | **Date:** 30 April 2026 | **System:** NetGenix Network Optimizer v1.0 | **URL:** http://localhost:8511/

---

## Executive Summary

NetGenix is a single-page AI-powered network optimization dashboard built for Cassava Technologies, designed to give telecom operations teams natural-language-driven insight and control over LTE/5G network performance at multiple sites. The system shows a promising foundational architecture — an AI chat assistant, live KPI cards, chart visualizations, and multi-site switching — but is currently running in a persistently **DISCONNECTED** state from all backend services, which severely limits functional verification and exposes several critical bugs, UX design weaknesses, and structural form issues.

---

## 1. FUNCTIONALITY & OPERATION

### 1.1 System Connectivity — CRITICAL FAILURE

**Status: DISCONNECTED (all 5 services)**

Every single backend service indicator shows "DISCONNECTED" at all times during testing, regardless of site or metric selected:

- API Connection → DISCONNECTED
- Network Elements → DISCONNECTED
- Database → DISCONNECTED
- Access NBI → DISCONNECTED
- Evaluation NBI → DISCONNECTED

This is the most severe issue in the system. The application is presenting KPI values (e.g. 92.76% Network Access Success) and chart data while simultaneously declaring itself completely disconnected from all data sources. The data being rendered is clearly synthetic/static/mock data that does not reflect live network state — yet it is presented with the same visual authority as real data, with no disclaimer. This is a **trust and integrity failure**: an operator relying on this dashboard in production could make decisions based on fabricated numbers.

**Specific sub-issues:**
- No fallback state clearly communicates "this is demo/mock data"
- No retry mechanism visible in the UI — there is no "Reconnect" button
- The "Updated:" timestamp continues showing a recent time even when disconnected, which compounds the deception
- The status indicators ("API Connection", "Network Elements", etc.) have no tooltip, no detail, no error message — just the word "DISCONNECTED" with no context about what failed or why

---

### 1.2 Page Load & Initialization

**Bug: ~8–10 second cold-start delay before sites populate**

On every fresh page load, the site selector combobox shows "Loading sites..." for approximately 8–10 seconds. During this period:
- All KPI values show "N/A"
- The chart shows "No data available for selected period"
- The BELOW status fires prematurely (Current Value: N/A, Status: BELOW)
- The page is in a degraded but not clearly communicated loading state

There is no loading spinner, skeleton screen, progress indicator, or user-facing acknowledgment that initialization is in progress. Users will see N/A values and broken charts with no feedback, likely interpret this as an error, and potentially refresh — resetting the cycle.

---

### 1.3 Site Selector

**Works correctly once loaded. Minor inconsistency detected.**

All four sites load and switch correctly, with KPI values and charts updating on selection:

| Site ID | Location Code Displayed | Note |
|---------|------------------------|------|
| MSH-0014-Chipadze | 0014 | ✓ Correct — 4-digit numeric ID |
| MSH-0112-Bindura Hospital | 0112 | ✓ Correct |
| MSH-0331-Chiwaridzo 2 | 0331 | ✓ Correct |
| MSH0013-Bindura-Zaoga | Bindura | ✗ **Bug** — shows city name, not numeric code |

**Bug:** MSH0013-Bindura-Zaoga displays "Bindura" as its location code, while all other sites display their 4-digit code (0014, 0112, 0331). This is an inconsistent data mapping. Additionally, the site ID itself uses a different naming format — "MSH0013" without a hyphen, vs. "MSH-0014", "MSH-0112", "MSH-0331" — suggesting inconsistent data entry or schema.

---

### 1.4 KPI Metrics & Charting

**All 7 metric types tested. Key findings:**

| Metric | Target Baseline | Observations |
|--------|----------------|-------------|
| Network Access Success | 90.00% | ✓ Logical — higher is better, ABOVE = good |
| Download Speed | 5.00 Mbps | ✓ Logical |
| Download Quality | 80.00% | ✓ Logical |
| Upload Speed | 3.00 Mbps | ✓ Logical |
| Upload Quality | 92.00% | ✓ Logical |
| Control Channel Load | 70.00% | ⚠ **Semantic bug** — 26.29% shows as "BELOW" target with no polarity context |
| Feedback Channel Load | 20.00% | ⚠ **Semantic bug** — 3.21% shows as "BELOW" with no polarity context |

**Critical Semantic Bug — Channel Load Metrics:**
For Control Channel Load (target: 70%) and Feedback Channel Load (target: 20%), the system shows values well below the target as "BELOW" — using the same visual treatment as an underperforming metric. However, in network engineering, low channel load is generally *desirable* (it means the channel is not congested). The system applies a uniform "higher is better" polarity to all metrics, which is incorrect for load metrics where "lower is better." This will actively mislead operators into thinking their channels are underperforming when they are actually healthy.

**Chart observations:**
- The chart renders an `application` role element (canvas/SVG), confirming it uses a visualization library
- The 7D default view shows Apr 22–Apr 29 data (8 data points)
- Y-axis ticks shown: 91.35, 91.8, 92.25, 92.7, 93.15 (for NAS on MSH-0014)
- Chart data appears consistent across metric switching
- The chart does not have an accessible label or ARIA description beyond the role="application"

**Time Range Buttons (7D / 14D / 30D / 60D / 90D):**
These buttons are rendered and present in the DOM. Since the application appears to use mock/static data rather than a live backend, it is not possible to verify whether these buttons actually fetch different data ranges or simply redraw with the same dataset. This is a significant gap — if time range switching is non-functional, it represents a major incomplete feature.

---

### 1.5 AI Assistant

**Status: Not fully testable — appears decorative or non-functional in disconnected state**

The AI Assistant panel includes:
- A welcome message ("Hi! I'm your AI Network Optimizer…")
- A timestamp (static — does not update in real time)
- 4 suggestion buttons: "Optimize download speed", "Improve network access success", "Fix upload quality issues", "Reduce connection drops"
- A free-text input form with a "Send" button
- A "Ready to Optimize" panel below the chat

**Issues found:**
1. The suggestion buttons (ref_3–ref_6) are anonymous buttons with no ARIA labels — they render as `button []` in the accessibility tree, only identified by child text content
2. The chat form submits but no AI response was generated during testing — the "Ready to Optimize" placeholder remains unchanged after submission, suggesting the AI is also gated behind the disconnected backend
3. The timestamp ("11:17:37 AM") shows the time the page first loaded, not the current time — it does not appear to update, making it misleading as a "last activity" indicator
4. There is no loading/thinking state shown when the AI is processing
5. There is no error message if the AI call fails
6. The welcome message is truncated in the accessibility tree ("Hi! I'm your AI Network Optimizer. Describe any network issue or optimization goal, and I'll analyze") — the DOM text appears to be cut off in the generic element, suggesting overflow issues

---

### 1.6 Navigation Tabs (Performance / Activity / Reports / Topology)

**Status: Present but behavior unverified**

The four tab buttons (Performance, Activity, Reports, Topology) exist in the DOM but click interaction could not be verified through the accessibility-only interface. Critically, the tabs have no `aria-selected`, `role="tab"`, or active state visible in the accessibility tree, making it impossible to determine which tab is currently active. The "Performance" tab appears to be the default, but there is no visual or accessible indicator confirming selection.

**Issue:** No `role="tablist"` / `role="tab"` ARIA semantics — the tabs are plain `<button>` elements with no accessible tab panel association. Screen reader users cannot navigate the tab interface correctly.

---

### 1.7 Network Parameters Panel

The header area shows 4 network parameter values in a status strip:

| Parameter | Value | Unit |
|-----------|-------|------|
| Signal Power | -180 | dBm |
| A3 Offset | 1000 | — |
| T310 Timer | (shown) | — |
| P0 PUSCH | -96 | dBm |
| PDCCH AGG | (shown) | — |

**Bugs:**
- **Signal Power: -180 dBm** is physically impossible for a real LTE signal. The lowest theoretical sensitivity for LTE is around -140 dBm; -180 dBm is below the thermal noise floor. This strongly confirms mock/placeholder data.
- **A3 Offset: 1000** — typical A3 offsets in LTE are in the range of 0–30 dB. A value of 1000 is nonsensical in any realistic network context.
- The "Updated:" timestamp in the parameter strip is static and never refreshes.
- Parameter names lack tooltip/help text — "PDCCH AGG", "A3 Offset", "T310 Timer", and "P0 PUSCH" are engineering acronyms with no contextual explanation for less experienced users.

---

## 2. FORM ANALYSIS

### 2.1 Site Selector Form Control

- **Type:** `<select>` (native combobox) — ✓ accessible
- **Label:** "Active Site" (label text in banner, but not programmatically associated via `<label for>` or `aria-labelledby`) — ⚠ accessible association unclear
- **Placeholder text during load:** "Loading sites..." used as an option value — this means a user could theoretically "select" the loading state — should be `disabled` and non-selectable
- **No search/filter capability** — with only 4 sites this is acceptable, but will not scale

### 2.2 Metric Dropdown

- **Type:** `<select>` — ✓ accessible
- **Label:** No visible label — the dropdown label is purely positional context
- **No grouping** — metrics are listed flat with no logical grouping (e.g., "Throughput", "Quality", "Load") — difficult to scan
- **Values vs labels:** Internal values use underscore format (`control_channel_load`) — this is appropriate, but the display names could be more descriptive (e.g., "PDCCH Control Channel Load (%)")

### 2.3 Chat Input Form

- **Type:** `<input type="text">` — ⚠ Should be `<textarea>` for multi-line network queries
- **Placeholder:** "Describe your network optimization goal..." — good, descriptive
- **Submit button:** Has no visible label in the accessibility tree (shows as `button []` in some states) — should have `aria-label="Send message"` or visible text consistently rendered
- **Max length:** No `maxlength` attribute — users could submit arbitrarily long queries
- **Form submission behavior:** Unclear if pressing Enter submits or inserts newline — no keyboard shortcut hint shown
- **Empty submission:** No validation preventing empty form submission — user can click Send with no input
- **Form reset after send:** Not verified — unclear if the input clears after successful submission
- **No character counter**

### 2.4 Time Range Buttons

- **Type:** `<button type="button">` — ✓ correct (non-submit)
- **No aria-pressed or active state** — when 7D is selected, nothing in the accessibility tree distinguishes it from 14D/30D/60D/90D
- **No default active state visible** — 7D appears to be default but is not marked as selected/active in the accessible tree
- **No keyboard focus ring description** — unclear if tab navigation works correctly

---

## 3. UI/UX ANALYSIS

### 3.1 Information Architecture

The layout presents a **split-panel design**: AI Chat assistant on the left, Performance dashboard on the right. While conceptually sound, the execution has significant problems:

- **The AI assistant and the performance panel are peers competing for attention** — neither is clearly "primary". In a real operations workflow, the chart/KPI panel is the anchor; the AI is a tool. The current layout inverts this relationship by giving the AI equal or dominant visual weight.
- **The "DISCONNECTED" badge is shown in a very small area** above the network parameter strip, without color emphasis appropriate to its severity. A fully-disconnected operations dashboard should be showing a prominent warning state, not a subtle label.
- **No hierarchy between critical alerts and routine metrics** — everything is presented at the same visual weight.

### 3.2 Header Design

The header contains: Brand name | "AI Powered" badge | "Active Site" label | Site dropdown | "Live" badge | Location | Location Code | "Cells" | "Updated:" | Light Mode toggle.

This is too much information for a single header strip. Issues:

- The "Live" badge appears even though the system is fully disconnected — this is a **false status indicator**
- "Location" and location code ("0014") duplicate information already in the dropdown
- "Cells" has no number next to it — unclear what this is communicating
- The "AI Powered" badge is marketing copy, not operational information — it belongs in an about/splash screen, not the operational header
- The light mode toggle is a small icon-only button with very low discoverability; no visible label in the header unless hovered

### 3.3 Status Indicators

The five status indicators (API Connection, Network Elements, Database, Access NBI, Evaluation NBI) are displayed as small text labels. This design fails on multiple counts:

- **Monochrome in the accessibility tree** — it's unclear if they render with color-coding (red/green), but if they do, this is color-as-the-sole-differentiator, which fails WCAG 1.4.1
- **No icons** — a single color-dot icon next to each would make status scannable at a glance
- **No drill-down** — clicking a DISCONNECTED indicator does nothing; there's no error detail, log, or recommended action
- **No priority/grouping** — "Database" being disconnected is more critical than "Evaluation NBI" in most operational contexts, but all five appear equally weighted
- **Terminology** — "NBI" (Northbound Interface) is a very technical term that may confuse non-specialist users; no tooltip or explanation provided

### 3.4 KPI Display Panel

The KPI summary card shows: Current Value | % change | Operating Average | Target Baseline | Status (ABOVE/BELOW)

Issues:
- The **"0.0%" change indicator** on initial load implies no change rather than "data unavailable" — misleading
- The **percentage change** (e.g., "-0.4%", "-1.6%") is shown without a time reference — change vs. what period? Yesterday? The selected time range? The previous data point?
- **"Operating Average"** vs **"Target Baseline"** — these concepts are not explained. Is the operating average the average over the selected time period? A rolling 30-day average? The difference matters operationally.
- **Status: BELOW** appears in red/warning state during loading (when data is N/A) — this is a false alarm that would trigger unnecessary operator concern
- **No units on the chart y-axis** — it's unclear if values are in %, Mbps, or other units without reading the metric dropdown label
- **No trend arrow** (↑↓) on the current value — a visual trend indicator would be much faster to parse than the percentage text

### 3.5 Chart Component

- The chart uses an ARIA `role="application"` element — this means screen readers hand off interaction to the application; without a proper accessible description or data table alternative, the chart is **completely inaccessible** to screen reader users
- The 7D chart for MSH-0014 NAS shows only 8 data points (Apr 22–29) — a 7-day window should ideally show hourly granularity (~168 points) or at minimum daily averages with clear labels indicating these are daily values
- No tooltip interaction verified (due to canvas/SVG nature and click unavailability)
- No export/download option for chart data
- No ability to compare sites side by side in the chart

### 3.6 AI Assistant UX

- The "TRY ASKING" section with suggestion chips is good UX practice — reducing the blank-canvas problem
- However, the 4 suggestions are all positive-framing ("Optimize...", "Improve...", "Fix...", "Reduce...") — users also need to be able to ask "What is wrong with..." or "Show me..." style queries; the suggestions don't represent the full range of use cases
- The chat panel has no history — when navigating between sites, does the conversation persist or reset? This is unclear
- No indication of which AI model/version is being used
- No way to copy or export the AI recommendations
- No "thumbs up/down" feedback mechanism on AI responses
- The static greeting timestamp ("11:17:37 AM") creates a false sense that the AI is actively monitoring the network in real time when it is not

### 3.7 Accessibility Audit

| Issue | Severity | WCAG Reference |
|-------|----------|---------------|
| Chat submit button has no accessible label in all states | High | 4.1.2 Name, Role, Value |
| Tab buttons lack role="tab"/aria-selected | High | 4.1.2 |
| Chart has no data table alternative | High | 1.1.1, 4.1.2 |
| Status indicators rely on text only (no icon/color described) | Medium | 1.4.1 |
| Form controls lack programmatic label association | Medium | 1.3.1, 4.1.2 |
| No skip navigation / landmark labeling | Medium | 2.4.1 |
| Time range buttons have no active/selected state | Medium | 4.1.2 |
| No focus management on tab switching | Medium | 2.4.3 |
| Loading state has no ARIA live region announcement | Medium | 4.1.3 |
| Suggestion buttons (ref_3-6) have no aria-label | Low | 4.1.2 |

### 3.8 Dark/Light Mode

A "Switch to light mode" button is present but hidden in the initial accessibility view (only visible after the banner element is inspected). This button:
- Has a child element labeled "Light mode" — this is the button's effective accessible name, which is good
- Its discoverability is low — it appears as a small icon in the header corner
- No system/OS color scheme preference (`prefers-color-scheme`) detection observed — the app defaults to dark mode regardless of system setting
- The light mode state is not remembered between sessions (no `localStorage` or cookie observed)

### 3.9 Visual Design Observations (from DOM structure)

While screenshots were not available in this test environment, the DOM structure reveals:
- The app uses a dark mode design by default (confirmed by the "Switch to light mode" button)
- The layout appears to be a two-column design (AI left, dashboard right)
- There is a footer with "NetGenix Network Optimizer | Powered by AI" and "Cassava Technologies 2026"
- The footer is thin and decorative only — no useful links, version number, support contact, or documentation

---

## 4. PRIORITIZED RECOMMENDATIONS

### P0 — Critical (Must Fix Before Production)

1. **Fix backend connectivity or clearly flag mock data.** Never show a "Last updated" timestamp alongside synthetic data. Add a persistent "DEMO MODE" or "SIMULATION" banner when running on mock data, or resolve the API connection failures.
2. **Fix the channel load metric polarity.** Control Channel Load and Feedback Channel Load are "lower is better" metrics. The ABOVE/BELOW logic must be inverted for these, or a per-metric polarity configuration introduced. As-is, operators will be alarmed by healthy networks.
3. **Remove the "Live" badge when disconnected.** Showing "Live" while all services are DISCONNECTED is actively dangerous — operators may trust data they shouldn't.

### P1 — High (Fix Before Release)

4. **Add a loading state with skeleton screens or a spinner** — users must never see N/A values without understanding why.
5. **Implement ARIA semantics for tabs** — add `role="tablist"`, `role="tab"`, `aria-selected`, and `aria-controls` to the tab system.
6. **Add accessible chart alternatives** — at minimum, render an HTML `<table>` visually hidden but accessible, containing the chart data.
7. **Label all form controls** — associate labels programmatically, add `aria-label` to unlabeled buttons.
8. **Fix the impossible sensor values** — Signal Power (-180 dBm) and A3 Offset (1000) must be replaced with realistic mock values or real data.
9. **Fix site naming inconsistency** — MSH0013 should be MSH-0013; "Bindura" location code should be "0013".

### P2 — Medium (Improve Quality)

10. **Add a reconnect mechanism** — give the DISCONNECTED indicator an actionable button to retry connection.
11. **Add tooltips to all technical parameters** — PDCCH AGG, A3 Offset, T310 Timer, P0 PUSCH, NBI — explain what each means.
12. **Add units to the KPI card and chart** — all values should have explicit units (%, Mbps, dBm, etc.).
13. **Add time reference to the % change indicator** — e.g., "−0.4% vs. previous 24h".
14. **Replace chat `<input type="text">` with `<textarea>`** for multi-line optimization queries.
15. **Add empty-input validation** to the chat form.
16. **Persist light/dark mode preference** in localStorage.
17. **Add OS color scheme detection** (`prefers-color-scheme`).
18. **Show active state on time range buttons** (pressed/selected styling + aria-pressed).

### P3 — Enhancement (Future Iteration)

19. **Add ARIA live regions** for the loading state and for new AI responses.
20. **Add site comparison view** — allow two sites to be charted side by side.
21. **Add chart export** (CSV/PNG download).
22. **Add AI response feedback mechanism** (thumbs up/down).
23. **Add hourly granularity to 7D charts** — daily granularity misses intraday spikes.
24. **Add operational guidance tooltips** to ABOVE/BELOW status — explain what to do, not just what the state is.
25. **Add a version number** to the footer for support and traceability.
26. **Add a site health summary view** — show all 4 sites at a glance rather than requiring dropdown switching.

---

## 5. SUMMARY SCORECARD

| Domain | Score | Rating |
|--------|-------|--------|
| Functionality — Core Operations | 2/10 | ❌ Critical (disconnected backend, mock data presented as real) |
| Functionality — Data Accuracy | 3/10 | ❌ Critical (impossible values, wrong polarity on load metrics) |
| Functionality — Completeness | 5/10 | ⚠ Partial (site switching works; AI, tab switching, time ranges unverifiable) |
| Form Design | 5/10 | ⚠ Partial (dropdowns work; chat form has multiple issues) |
| Accessibility | 3/10 | ❌ Poor (missing ARIA roles, unlabeled buttons, inaccessible chart) |
| UI Layout & Information Architecture | 5/10 | ⚠ Partial (coherent structure undermined by false status indicators) |
| UX & Operator Workflow | 4/10 | ⚠ Poor (misleading statuses, no guidance, low discoverability of features) |
| Visual Consistency | 6/10 | ✓ Acceptable (dark mode consistent; site naming inconsistency breaks it) |
| **Overall** | **4/10** | **Requires significant work before production readiness** |

---

*This report was generated through systematic DOM inspection, form interaction testing, state observation, and cross-metric/cross-site comparative analysis. Direct click interaction with tab and time range buttons was constrained by the browser environment during this test — a follow-up session with full mouse interaction is recommended to verify tab panel content and time range data fetching behavior.*

------------------

ChatGPT assessment 

Below is a **critical audit report based on the visible NetGenix dashboard state**. This is not a full end-to-end QA result because I only have the current page context, not backend logs, test credentials, or live interaction traces.

# NetGenix System Audit Report

## Scope Reviewed

System visible as:

**NetGenix — AI Powered Network Optimizer**

Active site:

**MSH-0014-Chipadze**

Visible modules:

**Performance, Activity, Reports, Topology, AI Assistant, NBI status, KPI trend dashboard, network parameters**

---

# Executive Review

NetGenix has a strong concept: it combines live site monitoring, KPI tracking, network parameter visibility, and AI-assisted optimisation in one operational interface.

However, the current system feels like a promising prototype rather than a hardened NOC-grade platform. The biggest concern is **operational trust**. A network operator must immediately understand:

1. Is the platform connected?
2. Is the data live?
3. Are the recommendations safe?
4. What action should I take next?
5. What changed after action was taken?

Right now, the dashboard shows useful information, but some signals conflict with each other. For example, the platform shows **DISCONNECTED**, while KPI data and updated timestamps are still displayed. That creates doubt about data validity.

---

# 1. Functionality & Operations Audit

## 1.1 Connection and NBI Status

### Current observation

The dashboard shows:

* **DISCONNECTED**
* Updated timestamp: **4/30/2026, 11:43:28 AM**
* Separate indicators for:

  * API Connection
  * Network Elements
  * Database
  * Access NBI
  * Evaluation NBI

### Critical issue

The system does not clearly explain what is disconnected.

Is it:

* API disconnected?
* Access NBI disconnected?
* Evaluation NBI disconnected?
* Database disconnected?
* Selected site unavailable?
* AI assistant disconnected?

This is a major operational risk.

### Recommendation

Replace the single vague **DISCONNECTED** state with a structured health panel:

| Component      |         Status | Last Successful Check | Error  |
| -------------- | -------------: | --------------------: | ------ |
| API            | Online/Offline |             timestamp | reason |
| Database       | Online/Offline |             timestamp | reason |
| Access NBI     | Online/Offline |             timestamp | reason |
| Evaluation NBI | Online/Offline |             timestamp | reason |
| AI Assistant   | Online/Offline |             timestamp | reason |

Each failure should include a diagnostic reason such as:

* Authentication failed
* Timeout
* Endpoint unreachable
* No data returned
* Invalid credentials
* NBI session expired

---

## 1.2 KPI Dashboard

### Current observation

Visible KPI:

**Network Access Success**

* Current value: **92.76%**
* Operating average: **90.00%**
* Status: **ABOVE**
* Change: **-0.4%**

### Strength

The KPI view is useful. It gives current value, operating average, trend, and baseline comparison.

### Critical issue

The KPI meaning is incomplete.

A NOC user needs to know:

* Is 92.76% good enough?
* What is the SLA threshold?
* Is the decline of -0.4% significant?
* Is this site improving or degrading?
* Is this based on all cells or selected cells?
* What is the sample size?
* Is the data live or stale?

### Recommendation

Add KPI interpretation directly beside the metric:

Example:

**Network Access Success: 92.76%**
Status: Above baseline, but declining slightly over the last 7 days.
Risk: Medium if decline continues for 2 more periods.
Affected scope: 6 cells.
Last valid KPI pull: timestamp.

---

## 1.3 Site and Cell Visibility

### Current observation

The selected site shows:

* Location: **0014**
* Cells: **6**

### Issue

The dashboard does not show the actual cell list or which cell is responsible for KPI degradation.

For network optimisation, site-level averages are not enough. A bad cell can be hidden inside a good site average.

### Recommendation

Add a cell breakdown table:

| Cell   | Access Success | DL Speed | UL Quality | Alarm | Risk |
| ------ | -------------: | -------: | ---------: | ----- | ---- |
| Cell 1 |          94.1% |     Good |       Good | No    | Low  |
| Cell 2 |          87.2% |     Poor |     Medium | Yes   | High |

The system should identify the worst-performing cell automatically.

---

## 1.4 Parameter Visibility

### Current observation

Displayed parameters:

* Signal Power: **-180 dBm**
* A3 Offset: **3 dB**
* T310 Timer: **1000 ms**
* P0 PUSCH: **-96 dBm**
* PDCCH AGG: **4**

### Critical issue

The parameter values are shown, but there is no context.

For each parameter, the operator needs:

* Current value
* Recommended range
* Vendor default
* Last changed date
* Who changed it
* Whether it is abnormal
* Impact on KPIs

### Major red flag

**Signal Power: -180 dBm** appears suspiciously low. If this represents actual measured signal power, it may indicate invalid data, placeholder data, poor parsing, or an unavailable measurement. The system should flag abnormal values automatically.

### Recommendation

Add parameter validation:

| Parameter    |  Current |   Expected Range | Status   | Impact                     |
| ------------ | -------: | ---------------: | -------- | -------------------------- |
| Signal Power | -180 dBm | e.g. -120 to -60 | Critical | Possible invalid/no signal |
| A3 Offset    |     3 dB |   vendor-defined | Normal   | Handover behaviour         |
| T310         |  1000 ms |   vendor-defined | Normal   | Drop recovery              |

---

## 1.5 AI Assistant

### Current observation

The assistant offers:

* Optimize download speed
* Improve network access success
* Fix upload quality issues
* Reduce connection drops

### Strength

The assistant is well-positioned for operational workflows.

### Critical issue

The assistant currently looks generic. For it to be useful in a NOC environment, it must be grounded in the selected site, current KPI, current parameters, and NBI status.

### Required behaviour

If the operator asks:

**“Improve network access success”**

The assistant should return:

1. Current diagnosis
2. Suspected root cause
3. Affected cells
4. Evidence
5. Recommended parameter changes
6. Risk level
7. Dry-run MML command
8. Approval requirement before execution
9. Rollback command
10. Post-change monitoring window

### Recommendation

Every AI recommendation should follow this format:

**Diagnosis → Evidence → Recommendation → Risk → Dry-run Command → Approval → Rollback → Monitoring Plan**

---

## 1.6 Reports Module

### Current observation

Reports tab exists but is not visible in detail.

### Required audit expectations

Reports should include:

* Weekly KPI summary
* Worst sites
* Best sites
* Exception list
* Parameter change audit
* AI recommendation history
* NBI availability report
* Before/after optimisation impact
* Export to Excel/PDF

### Recommendation

Reports must not only show KPI numbers. They should tell the operational story:

**What degraded, why it matters, what was recommended, what was changed, and whether performance improved.**

---

## 1.7 Topology Module

### Current observation

Topology tab exists but is not visible in detail.

### Required improvement

Topology should show:

* Site status
* Cell health
* Neighbor relationships
* Alarm overlays
* KPI heatmap
* Degradation clusters
* NBI availability
* Drilldown from region → site → cell

---

# 2. Form / Visual Design Audit

## 2.1 Layout

### Strength

The layout is clean and modern. It has a clear left-side operational area and right-side performance dashboard.

### Issue

The dashboard has too many isolated cards without enough hierarchy.

The operator’s eye should immediately go to:

1. Site status
2. Connection status
3. KPI health
4. Recommended next action

Currently, the dashboard shows many values, but not enough prioritisation.

### Recommendation

Create a clear command-center hierarchy:

**Top row:** Site + connection health + last update
**Second row:** KPI health cards
**Third row:** cell/parameter diagnostics
**Fourth row:** AI recommendations and action queue

---

## 2.2 Colour and Status Language

### Issue

The system uses status labels, but the severity language is not strong enough.

For NOC operations, statuses should be unmistakable:

* Healthy
* Warning
* Critical
* Disconnected
* Stale Data
* Action Required

### Recommendation

Use consistent status colours:

* Green: healthy
* Amber: warning
* Red: critical
* Grey: offline/stale
* Blue: informational

Also add labels, not just colours, because operators may work in poor lighting or with accessibility constraints.

---

## 2.3 Data Density

### Issue

The dashboard is visually clean but operationally light. It shows summary values but not enough decision-support context.

### Recommendation

Add expandable drilldowns rather than crowding the main view.

Example:

* KPI card shows headline value
* Clicking expands:

  * cell breakdown
  * trend
  * anomaly reason
  * related parameters
  * suggested action

---

# 3. UI/UX Audit

## 3.1 Operator Workflow

### Current likely workflow

1. Select site
2. Check status
3. Review KPI
4. Ask AI assistant
5. Apply recommendations manually or through MML

### Problem

The workflow is not explicit enough.

The system should guide the operator from observation to action.

### Recommended workflow design

**Detect → Diagnose → Recommend → Approve → Execute → Verify → Report**

Each stage should be visible in the UI.

---

## 3.2 AI Assistant UX

### Issue

The AI assistant is currently presented like a chatbot, but this is an operational tool. A pure chat interface is not enough.

### Recommendation

Turn AI output into structured operational cards:

**Recommendation Card**

* Issue detected
* Confidence score
* Impacted KPI
* Root cause hypothesis
* Suggested change
* Risk level
* Dry-run command
* Required approval
* Rollback command

This is much better than long text responses.

---

## 3.3 Error Handling

### Critical issue

The dashboard says **DISCONNECTED**, but the user is not told what to do.

### Recommendation

Every error state should answer:

* What failed?
* Why did it fail?
* When did it fail?
* What is affected?
* What should the operator do next?

Example:

**Access NBI Offline**
Last successful connection: 11:35:12
Likely cause: Authentication timeout
Impact: Live command execution unavailable
Action: Re-authenticate or switch to read-only mode

---

## 3.4 Trust and Auditability

### Major gap

For a network optimisation system, auditability is essential.

The UI should show:

* Who requested an optimisation
* What AI recommended
* What command was generated
* Whether it was dry-run or live
* Who approved it
* What changed
* Before/after KPI impact
* Rollback status

Without this, the platform is risky for production operations.

---

# Highest-Priority Issues

## Critical

1. **DISCONNECTED status is vague**
2. **KPI data appears despite disconnected state**
3. **No explanation of data freshness or validity**
4. **No visible cell-level root cause breakdown**
5. **No visible AI safety workflow for MML execution**
6. **No audit trail visible for recommendations/actions**

## High

1. Parameter values lack validation and recommended ranges
2. AI assistant needs structured operational output
3. Reports need audit and before/after optimisation evidence
4. Topology needs operational drilldown
5. KPI trends need risk interpretation

## Medium

1. Improve visual hierarchy
2. Add severity colours and labels
3. Add operator workflow stages
4. Add tooltips for telecom parameters
5. Add export/report preview states

---

# Recommended Improvement Roadmap

## Phase 1 — Operational Trust

* Fix connection status clarity
* Add component-level health checks
* Add data freshness indicators
* Add stale data warnings
* Add parameter validation

## Phase 2 — Optimisation Workflow

* Add cell-level diagnostics
* Add AI recommendation cards
* Add dry-run MML preview
* Add approval gate
* Add rollback logic
* Add post-change monitoring

## Phase 3 — Reporting and Audit

* Add action history
* Add before/after KPI reports
* Add Excel/PDF export
* Add recommendation audit log
* Add weekly executive summary

## Phase 4 — NOC-Grade UX

* Add topology health map
* Add alarm overlay
* Add role-based access
* Add operator notes
* Add incident/change-ticket integration

---

# Overall Assessment

NetGenix is a strong platform concept with real operational value, especially because it combines KPI monitoring, parameter visibility, AI recommendations, and reporting.

But to be production-ready, it needs stronger **trust, traceability, diagnostics, and action safety**.

Current maturity estimate:

**Prototype / early operational MVP**

Target maturity:

**NOC-grade AI-assisted optimisation platform**

Biggest improvement needed:

**Move from “dashboard that shows values” to “operational system that explains, recommends, safely acts, and proves impact.”**
