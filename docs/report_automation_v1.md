Below is a **strict, explicit, step‑by‑step reconstruction of the TWO separate report generations exactly as Brighton demonstrated them in the meetings**.  
I am **not designing an improved process** here — this is the **AS‑IS, do‑exactly‑this workflow**, mapped 1:1 to what was shown and said in the videos and transcripts.

I’ll break it into:

1.  **Report 1 – Site Performance (Top / Bottom Sites)**
2.  **Report 2 – Executive Network KPI Report (GCO / GCUO / General)**

For each report you’ll get:

*   Purpose
*   Inputs
*   Step‑by‑step actions Brighton performed
*   Exact outputs he produced

***

# REPORT 1 — SITE PERFORMANCE REPORT

**(Top / Bottom Sites by Traffic, PRB Utilisation, Code Drop)**

## Purpose (as stated in meeting)

To show **top‑performing and bottom‑performing sites** for the week, used in operational and executive visibility.

***

## Inputs Used

*   **System:** Evaluation (OSS)
*   **Report type:** LTE Main KPI / PRB / Code Drop reports
*   **Time window:** Weekly (Thursday → Wednesday)
*   **Output format:** Excel

***

## STEP‑BY‑STEP — EXACTLY HOW BRIGHTON DID IT

### STEP 1: Log into Evaluation

*   Open the Evaluation OSS portal
*   Navigate to **Report Management**

***

### STEP 2: Select the KPI Report

Brighton repeats this whole process **per KPI**.

Example shown:

*   LTE Main KPI Report  
    (other runs were PRB utilisation and code drop)

***

### STEP 3: Set the Date Range

*   Select **weekly range**
*   Explicitly stated example:
    *   From **Thursday** to **Wednesday**
    *   Example used in meeting: **2nd → 8th**

This is done **manually each time**.

***

### STEP 4: Choose Scope

*   Run report:
    *   For **entire network**
    *   Then again at **cell level**

Both are extracted as needed.

***

### STEP 5: Run Query & Export

*   Execute the query
*   Download the output as an **Excel file**

This Excel is the *raw extract*.

***

### STEP 6: Excel “Cooking” – Traffic KPI

In Excel:

1.  Identify traffic values (originally in **gigabits**)
2.  Convert units:
    *   Brighton divides by **8** (Gb → GB)
3.  Build a **Pivot Table**:
    *   Rows: Site / Cell
    *   Values: Traffic
4.  Aggregate:
    *   **Daily sums**
    *   Then compute **weekly average**
5.  Sort:
    *   Largest → smallest

***

### STEP 7: Extract Top & Bottom Sites

*   Select:
    *   **Top 20 sites**
    *   **Bottom 20 sites**
*   Manually **exclude new / non‑commercialised sites**
    *   This exclusion is **human judgement**, not system‑driven

***

### STEP 8: Repeat for PRB Utilisation

Brighton repeats the full flow with a KPI change:

1.  In Evaluation:
    *   Select **Busy Hour Downlink PRB Utilisation**
2.  System extracts:
    *   Busiest hour per cell
3.  In Excel:
    *   Use **AVERAGE** (not sum)
4.  Sort
5.  Extract:
    *   Top 20
    *   Bottom 20

***

### STEP 9: Repeat for Code Drop Rate

Same pattern again:

*   Extract
*   Average over the week
*   Rank
*   Select Top / Bottom 20

***

## FINAL OUTPUTS OF REPORT 1

Brighton ends with:

*   ✅ Top 20 sites by:
    *   Traffic
    *   PRB utilisation
    *   Code drop
*   ✅ Bottom 20 sites by same KPIs
*   ✅ Weekly averages per KPI
*   ✅ Excel tables copied into report templates

No dashboards. No automation. **Excel‑based outputs only.**

***

# REPORT 2 — EXECUTIVE NETWORK KPI REPORT

**(GCO / GCUO / General Executive View)**

## Purpose

To give **executive‑level weekly network health metrics**, reused across multiple report tabs.

***

## Inputs Used

*   **Evaluation**
*   **Tariro**
*   **Subscriber system**
*   **EPC Monthly Report**
*   **Excel master template**

***

## STEP‑BY‑STEP — EXACTLY HOW BRIGHTON DID IT

### STEP 1: Start with Evaluation (Traffic & Utilisation)

*   Run Evaluation reports for the same **weekly date range**
*   Extract traffic KPIs as Excel

***

### STEP 2: Traffic Calculation (Executive Metric)

In Excel:

1.  Take **daily traffic values**
2.  SUM all days for the week
3.  Convert to TB:
    *   Divide by **8000**
4.  Final output:
    *   **Total weekly traffic (TB)**

Example mentioned in session:

*   “951 TB over 7 days” (illustrative of the method, not hard‑coded)

***

### STEP 3: Radio Network Availability (Tariro)

*   Log into **Tariro**
*   Extract:
    *   Radio Network Availability KPI
*   Tariro provides **pre‑calculated averages**
*   Brighton:
    *   Pastes values into Excel
    *   Recalculates **weekly average manually**

***

### STEP 4: Subscriber Metrics

Two values are manually sourced:

1.  **Total subscribers**
    *   Extracted from subscriber system
2.  **Active subscribers**
    *   Downloaded via a separate link
    *   Can be exported as PDF / Excel

These values are **manually pasted** into Excel.

***

### STEP 5: Peak Throughput

*   Open **EPC Monthly Report**
*   Select same weekly date range
*   Identify **peak throughput value**
*   Manually copy this number into Excel

***

### STEP 6: Excel Formula Calculations

Using pre‑inserted formulas in the template:

*   **Penetration rate**
        active_subscribers / subscriber_capacity
*   **Average GB per user**
        total_traffic_gb / active_subscribers
*   **Average throughput per user**
        peak_throughput / active_subscribers

Brighton explicitly says:

> “The formulas are already there — I just drag them.”

***

### STEP 7: Copy Values Across Report Tabs

Once the main section is complete:

*   Copy the **same computed values** into:
    *   GCO tab
    *   GCUO tab
    *   General reporting tab

This is repetitive but intentional.

***

## FINAL OUTPUTS OF REPORT 2

Brighton produces:

*   ✅ Total weekly traffic (TB)
*   ✅ Radio Network Availability (weekly avg)
*   ✅ PRB utilisation
*   ✅ Code drop rate
*   ✅ Peak throughput
*   ✅ Total subscribers
*   ✅ Active subscribers
*   ✅ Penetration rate
*   ✅ Avg GB per user
*   ✅ Avg throughput per user
*   ✅ Same numbers reused across multiple executive tabs

Again: **Excel‑only outputs**, fully manual.

***

# WHAT I NEED FROM YOU (ONLY IF YOU WANT TO IMPLEMENT THIS)

To help you **generate these two reports exactly**, tell me:

1.  Do you want:
    *   **Exact replica (Excel‑only, same structure)**
    *   or **Exact logic, but automated**?
2.  Should site exclusions (new / non‑commercialised) remain:
    *   Manual, or
    *   Config‑driven?
3.  Are you targeting:
    *   Scripted automation (Python),
    *   RPA,
    *   Or an agent‑based workflow?

Once you answer, I can:

*   Translate this into **pseudo‑code**
*   Produce a **logic flow diagram**
*   Or generate a **drop‑in automation spec** that mirrors Brighton’s work 1:1.


--------------

Great — targeting **scripted automation (Python)** is the *right* choice for your case, and it fits perfectly with **“exact logic, but automated”**.

Below is a **clear, concrete Python‑first blueprint** that mirrors **exactly what Brighton did**, without changing behaviour, outputs, or KPIs.

***

# ✅ SCRIPTED AUTOMATION (PYTHON) — BRIGHTON‑PARITY DESIGN

This is **not RPA** and **not AI**.  
It is **deterministic Python automation** that reproduces Brighton’s steps.

***

## 1. WHAT “SCRIPTED AUTOMATION (PYTHON)” MEANS HERE

In your context:

> **Python scripts replace Brighton’s hands — not his judgement.**

Python will:

*   Run queries
*   Load Excel extracts
*   Apply the *same formulas*
*   Generate the *same tables*
*   Pause where Brighton paused

Python will **not**:

*   Decide which sites to exclude
*   Change KPI definitions
*   Optimise logic

***

## 2. OVERALL PYTHON FLOW (HIGH LEVEL)

```text
Weekly Trigger
   ↓
Data Extraction (files / exports)
   ↓
KPI Processing (pure Python)
   ↓
Manual Exclusion Hook
   ↓
Report 1 Output (Site Performance)
   ↓
Report 2 Output (Executive KPIs)
```

This aligns 1:1 with your logic flow diagram.

***

## 3. MODULE‑BY‑MODULE BREAKDOWN (EXACT LOGIC)

### MODULE 1 — DATE WINDOW (Thu → Wed)

```python
def get_reporting_window(reference_date):
    # returns last Thursday to Wednesday
```

✅ Same logic Brighton uses  
✅ Deterministic  
✅ No config ambiguity

***

### MODULE 2 — DATA INGESTION (NO APIs ASSUMED)

Because Evaluation / Tariro may be UI‑only, Python assumes **file‑based ingestion**:

```text
/inputs
  ├── evaluation_traffic.xlsx
  ├── evaluation_prb.xlsx
  ├── evaluation_codedrop.xlsx
  ├── tariro_availability.xlsx
  ├── subscribers.xlsx
  ├── epc_throughput.xlsx
```

Python responsibility:

*   Validate files exist
*   Validate date ranges match
*   Fail loudly if something is missing

✅ This mirrors Brighton downloading files manually

***

### MODULE 3 — REPORT 1: SITE PERFORMANCE (Top / Bottom)

#### Traffic Processing (Exact)

```python
traffic_gb = traffic_gbit / 8
weekly_sum = traffic_gb.groupby(site).sum()
weekly_avg = weekly_sum / 7
```

#### PRB Utilisation

```python
weekly_avg_prb = prb_busy_hour.groupby(site).mean()
```

#### Code Drop

```python
weekly_avg_codedrop = codedrop.groupby(site).mean()
```

#### Ranking

```python
top_20 = df.sort_values(metric, ascending=False).head(20)
bottom_20 = df.sort_values(metric, ascending=True).head(20)
```

✅ Same maths  
✅ Same ranking  
✅ Same outputs

***

### MODULE 4 — MANUAL EXCLUSION (INTENTIONAL PAUSE)

This is **deliberate**, because Brighton explicitly does this manually.

Two safe patterns:

#### Option A — CSV Override

```text
excluded_sites.csv
```

Python loads it and filters.

#### Option B — Script Pause

```python
input("Update excluded_sites.csv and press Enter to continue")
```

✅ Preserves human judgement  
✅ Matches Brighton’s behaviour

***

### MODULE 5 — REPORT 1 OUTPUTS

Python produces:

*   `report1_top_bottom_sites.xlsx`
    *   Top 20 / Bottom 20
    *   Traffic
    *   PRB
    *   Code Drop
    *   Weekly averages

✅ Excel‑ready  
✅ Copy‑paste compatible

***

## 4. REPORT 2 — EXECUTIVE KPI AUTOMATION

### MODULE 6 — TRAFFIC (TB)

```python
weekly_tb = total_gb / 8000
```

✅ Exact conversion Brighton stated

***

### MODULE 7 — TARIRO AVAILABILITY

```python
weekly_availability = tariro_daily.mean()
```

✅ Ignores Tariro’s auto‑averages  
✅ Recalculates weekly avg (as Brighton did)

***

### MODULE 8 — SUBSCRIBER & THROUGHPUT INGESTION

Python **does not compute these**, it just loads them:

```python
active_subs
total_subs
peak_throughput
```

✅ Same manual sourcing  
✅ No assumptions introduced

***

### MODULE 9 — EXECUTIVE FORMULAS (UNCHANGED)

```python
penetration = active_subs / capacity
avg_gb_per_user = total_gb / active_subs
avg_throughput_per_user = peak_throughput / active_subs
```

✅ Same Excel formulas  
✅ Same semantics

***

### MODULE 10 — COPY ACROSS SECTIONS

Python writes **identical values** into:

*   GCO sheet
*   GCUO sheet
*   General sheet

Just like Brighton’s copy‑paste step.

***

## 5. FINAL PYTHON OUTPUTS

| Output                          | Purpose              |
| ------------------------------- | -------------------- |
| `report1_site_performance.xlsx` | Top / Bottom Sites   |
| `report2_exec_kpis.xlsx`        | GCO / GCUO / General |
| `audit_log.json`                | Traceability         |
| `excluded_sites.csv`            | Manual control       |

***

## 6. WHY PYTHON IS THE RIGHT TARGET (FOR YOU)

✅ Deterministic  
✅ Testable  
✅ Version‑controlled  
✅ Easier than RPA  
✅ Matches your engineering skillset  
✅ Safe for telecom data

Most importantly:

> **Python lets you prove parity with Brighton’s outputs line‑by‑line.**

***

## 7. WHAT I CAN DO NEXT (NO GUESSING)

If you want, I can **immediately**:

1.  Generate **pseudo‑code for all modules**
2.  Produce a **repo folder structure**
3.  Create a **validation checklist** (Brighton vs Python outputs)
4.  Convert this into an **Airflow DAG**
5.  Write **Excel template‑aware Python code**

Tell me **which one you want next**, and I’ll do it in the next message.
