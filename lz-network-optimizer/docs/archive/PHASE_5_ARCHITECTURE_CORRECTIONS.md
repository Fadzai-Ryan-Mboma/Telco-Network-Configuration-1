# Phase 5: Architecture Corrections - Cell-by-Cell Modifications

**Document Version:** 1.0
**Date:** 2025-11-03
**Status:** ✅ API Connectivity Fixed, ⚠️ Tools Update Required

---

## Executive Summary

Phase 5.1 (API Connectivity) discovered critical architectural requirements from Huawei API documentation that require updates to tool implementations for Stages 5.2-5.5.

**Key Discovery:**
- **Query operations:** Site-wide (returns all 6 cells)
- **Modify operations:** Cell-by-cell (must execute 6 separate commands)

---

## Critical API Documentation

### Source Files:
1. **docs/API Use.txt** - Authentication and MML endpoint
2. **docs/Configurations.txt** - Cell-by-cell modification examples

### Correct API Patterns:

#### **Authentication (✅ FIXED)**
```python
PUT /api/rest/securityManagement/v1/oauth/token
Body: {
  "grantType": "password",
  "userName": "cassava.ai",
  "value": "#Pass123#"
}
Response: {
  "accessSession": "x-il1c05...",
  "roaRand": "34833e9426...",
  "expires": 1800
}
Header: X-Auth-Token: {accessSession}
```

#### **Query - Site-Wide (✅ WORKING)**
```python
POST /api/rest/mmlManagement/v1/command
{
  "command": "LST UECOOPERATIONPARA:;",
  "neNames": ["MSH-0112-Bindura Hospital"]
}
→ Returns: Data for ALL 6 cells
```

#### **Modify - Cell-by-Cell (⚠️ REQUIRES 6 COMMANDS)**
```python
# Must execute 6 separate commands:
for cell_id in [1, 2, 3, 4, 5, 6]:
    POST /api/rest/mmlManagement/v1/command
    {
      "command": f"MOD PDSCHCFG:LOCALCELLID={cell_id},REFERENCESIGNALPWR=49;",
      "neNames": ["MSH-0112-Bindura Hospital"]
    }
```

---

## Updated Architecture

### MML Command Format

From `Configurations.txt`:

```
Parameter: Reference Signal Power (RS Power)
Query current: LST PDSCHCFG
Change: MOD PDSCHCFG:LOCALCELLID=(local_cell_id),REFERENCESIGNALPWR=(ref_signal_pwr); {(ne_name)}

Example (6 commands required for site-wide change):
MOD PDSCHCFG:LOCALCELLID=1,REFERENCESIGNALPWR=49; {MSH-0112-Bindura Hospital}
MOD PDSCHCFG:LOCALCELLID=2,REFERENCESIGNALPWR=49; {MSH-0112-Bindura Hospital}
MOD PDSCHCFG:LOCALCELLID=3,REFERENCESIGNALPWR=49; {MSH-0112-Bindura Hospital}
MOD PDSCHCFG:LOCALCELLID=4,REFERENCESIGNALPWR=57; {MSH-0112-Bindura Hospital}
MOD PDSCHCFG:LOCALCELLID=5,REFERENCESIGNALPWR=57; {MSH-0112-Bindura Hospital}
MOD PDSCHCFG:LOCALCELLID=6,REFERENCESIGNALPWR=57; {MSH-0112-Bindura Hospital}
```

**Key Points:**
- Each cell requires individual LOCALCELLID specification
- Site name in `{curly braces}` (maps to `neNames` in API)
- Values can differ per cell (e.g., cells 1-3: 49, cells 4-6: 57)

---

## Code Updates Required

### 1. HuaweiAPIClient (✅ COMPLETE)

**File:** `network/huawei_api_client.py`

**Methods Added:**
```python
def execute_mml_command(self, mml_command: str, site_names: List[str]) -> Dict:
    """Execute single MML command for one cell"""
    # Handles both query (site-wide) and modify (cell-specific) commands

def execute_mml_command_batch(self, command_template: str, site_name: str,
                               cell_ids: List[int] = None) -> List[Dict]:
    """Execute same modification across all cells"""
    # For cell_ids in [1,2,3,4,5,6]:
    #     command = template.format(cell_id=cell_id)
    #     execute_mml_command(command, [site_name])
```

**Status:** ✅ Implemented in Stage 5.1

---

### 2. Huawei Tools (⏳ PENDING)

**File:** `tools/huawei_tools.py`

**Required Changes:**

#### **Tool 1: query_huawei_parameter**
Add `site_name` parameter:
```python
@tool
def query_huawei_parameter(
    parameter_name: str,
    site_name: str,  # NEW
    cell_id: int = 1
) -> str:
    # Build query command (already correct - has LOCALCELLID)
    mml_command = build_query_command(parameter_name, cell_id)

    # Execute with site_name (UPDATED)
    response = client.execute_mml_command(mml_command, [site_name])
```

#### **Tool 2: modify_huawei_parameter**
Add `site_name` parameter:
```python
@tool
def modify_huawei_parameter(
    parameter_name: str,
    new_value: Any,
    site_name: str,  # NEW
    cell_id: int = 1,
    reason: str = "Optimization"
) -> str:
    # Build modify command (already correct - has LOCALCELLID)
    mml_command = build_modify_command(parameter_name, new_value, cell_id)

    # Execute with site_name (UPDATED)
    response = client.execute_mml_command(mml_command, [site_name])
```

#### **NEW Tool 3: modify_huawei_parameter_site**
```python
@tool
def modify_huawei_parameter_site(
    parameter_name: str,
    new_value: Any,
    site_name: str,
    cell_ids: List[int] = None,  # Default [1,2,3,4,5,6]
    reason: str = "Optimization"
) -> str:
    """
    Modify parameter across ALL cells at a site.

    Executes 6 separate MML commands (one per cell).
    """
    if cell_ids is None:
        cell_ids = [1, 2, 3, 4, 5, 6]

    # Use batch execution
    command_template = build_modify_command_template(parameter_name, new_value)
    # e.g., "MOD PDSCHCFG:LOCALCELLID={cell_id},REFERENCESIGNALPWR={new_value};"

    results = client.execute_mml_command_batch(
        command_template,
        site_name,
        cell_ids
    )

    # Return summary
    successful = sum(1 for r in results if r['success'])
    return f"Modified {parameter_name} on {successful}/{len(cell_ids)} cells at {site_name}"
```

#### **Tool 4: execute_mml_command**
Add `site_name` parameter:
```python
@tool
def execute_mml_command(
    mml_command: str,
    site_name: str  # NEW
) -> str:
    # Execute with site_name (UPDATED)
    response = client.execute_mml_command(mml_command, [site_name])
```

#### **Tool 5: query_huawei_kpi**
Add `site_name` parameter (already has it ✅):
```python
@tool
def query_huawei_kpi(
    site_name: str,  # Already present
    cell_id: int = 1
) -> str:
    mml_command = f"LST PMDATA: OBJECTTYPE=CELL, LOCALCELLID={cell_id};"
    response = client.execute_mml_command(mml_command, [site_name])  # UPDATED
```

**Status:** ⏳ To be implemented before Stage 5.3

---

### 3. Domain - MML Commands (⏳ PENDING)

**File:** `domain/mml_commands.py`

**Add new function:**
```python
def build_modify_command_template(parameter_name: str, value: Any) -> str:
    """
    Build MML modify command TEMPLATE with {cell_id} placeholder.

    Used for batch execution across multiple cells.

    Args:
        parameter_name: Parameter to modify
        value: New value

    Returns:
        Command template string with {cell_id} placeholder

    Example:
        >>> build_modify_command_template("reference_signal_power_pdschcfg", -180)
        "MOD PDSCHCFG:LOCALCELLID={cell_id},REFERENCESIGNALPWR=-180;"
    """
    if parameter_name not in MML_COMMANDS:
        raise ValueError(f"Unknown parameter: {parameter_name}")

    template = MML_COMMANDS[parameter_name]["modify"]
    return template.format(cell_id="{cell_id}", value=value)
```

**Status:** ⏳ To be implemented before Stage 5.3

---

### 4. MML Executor Agent (⏳ PENDING)

**File:** `agents/mml_executor_agent.py`

**Current Behavior:**
- Generates single MML command per parameter
- Executes once

**Required Behavior:**
- Generate 6 MML commands per parameter (one per cell)
- Execute in sequence with error handling
- Report success/failure per cell

**Implementation Approach:**

```python
# In MML Executor Agent prompt/workflow:

# When receiving parameter change recommendation:
recommendation = {
    'parameter': 'reference_signal_power_pdschcfg',
    'new_value': -180,
    'site_name': 'MSH-0112-Bindura Hospital'
}

# Option A: Use modify_huawei_parameter_site tool
result = modify_huawei_parameter_site(
    parameter_name=recommendation['parameter'],
    new_value=recommendation['new_value'],
    site_name=recommendation['site_name'],
    reason="Agent optimization"
)

# Option B: Generate 6 commands manually
mml_commands = []
for cell_id in [1, 2, 3, 4, 5, 6]:
    mml = build_modify_command(
        recommendation['parameter'],
        recommendation['new_value'],
        cell_id
    )
    mml_commands.append({
        'cell_id': cell_id,
        'command': mml
    })

# Execute each command
results = []
for cmd in mml_commands:
    result = modify_huawei_parameter(
        parameter_name=recommendation['parameter'],
        new_value=recommendation['new_value'],
        site_name=recommendation['site_name'],
        cell_id=cmd['cell_id']
    )
    results.append(result)
```

**Status:** ⏳ To be implemented in Stage 5.3

---

### 5. Rollback Manager (⏳ PENDING)

**File:** `tools/rollback_manager.py` (NEW)

**Purpose:** Manage parameter rollback for all 6 cells

**Class Structure:**
```python
class RollbackManager:
    def __init__(self, site_name: str, cell_ids: List[int] = None):
        self.site_name = site_name
        self.cell_ids = cell_ids or [1, 2, 3, 4, 5, 6]
        self.pre_state = {}  # {cell_id: {param: value}}
        self.changes_made = []

    def capture_pre_state(self, parameter_name: str) -> Dict[int, Any]:
        """
        Query and store current parameter values for all cells.

        Returns:
            {1: -200, 2: -200, 3: -200, 4: -200, 5: -200, 6: -200}
        """
        for cell_id in self.cell_ids:
            # Query current value
            result = query_huawei_parameter(
                parameter_name,
                self.site_name,
                cell_id
            )
            # Parse and store
            self.pre_state[cell_id] = {parameter_name: result}

        return self.pre_state

    def execute_changes(self, parameter_name: str, new_value: Any) -> List[Dict]:
        """
        Execute parameter change for all cells.

        Returns:
            [{cell_id: 1, success: True}, ...]
        """
        results = modify_huawei_parameter_site(
            parameter_name,
            new_value,
            self.site_name,
            self.cell_ids
        )

        self.changes_made.append({
            'parameter': parameter_name,
            'new_value': new_value,
            'results': results
        })

        return results

    def rollback_changes(self, reason: str = "Phase 5 testing") -> List[Dict]:
        """
        Rollback all changes to original values.

        For each change made:
            - Retrieve original value from pre_state
            - Execute reverse MML command for all 6 cells
        """
        rollback_results = []

        for change in self.changes_made:
            param = change['parameter']

            # Rollback each cell to original value
            for cell_id in self.cell_ids:
                original_value = self.pre_state[cell_id][param]

                result = modify_huawei_parameter(
                    param,
                    original_value,
                    self.site_name,
                    cell_id,
                    reason=f"ROLLBACK: {reason}"
                )

                rollback_results.append({
                    'cell_id': cell_id,
                    'parameter': param,
                    'original_value': original_value,
                    'success': 'SUCCESS' in result
                })

        return rollback_results

    def verify_rollback(self) -> bool:
        """
        Verify all cells restored to original state.
        """
        for cell_id in self.cell_ids:
            for param, original_value in self.pre_state[cell_id].items():
                current = query_huawei_parameter(param, self.site_name, cell_id)
                if current != original_value:
                    return False
        return True
```

**Status:** ⏳ To be implemented in Stage 5.4

---

## Stage Implementation Plan

### Stage 5.1: API Connectivity (✅ COMPLETE)
- ✅ Fixed authentication endpoint
- ✅ Fixed MML command endpoint
- ✅ Added `execute_mml_command_batch()` to HuaweiAPIClient
- ✅ Validated with test script (4/4 tests passing)

### Stage 5.2: Docker Deployment Validation (⏳ NEXT)
- Build Docker container
- Test UI accessibility
- Verify database loading
- **Note:** Tool updates can be done in parallel

### Stage 5.3: Generation Mode (⏳ REQUIRES TOOL UPDATES)
**Prerequisites:**
- ✅ Update `tools/huawei_tools.py` with `site_name` parameter
- ✅ Add `modify_huawei_parameter_site` tool
- ✅ Add `build_modify_command_template()` to domain/mml_commands.py
- ✅ Update MML Executor Agent to use batch tool

**Test Flow:**
1. Submit 3 optimization queries
2. Agent generates recommendations
3. **Generate 6 MML commands per parameter** (using new tool)
4. Display for manual review
5. Collect generation logs

### Stage 5.4: Execution Mode (⏳ REQUIRES ROLLBACK MANAGER)
**Prerequisites:**
- ✅ All Stage 5.3 updates complete
- ✅ Create `tools/rollback_manager.py`
- ✅ Integrate rollback manager with workflow

**Test Flow:**
1. Capture pre-state (6 cells)
2. Execute modifications (6 commands per parameter)
3. Wait 5 minutes
4. Measure post-state KPIs
5. **Rollback** (6 commands per parameter)
6. Verify rollback success

### Stage 5.5: UAT Preparation
- Create user documentation
- Generate demo script
- Package all Phase 5 deliverables

---

## Immediate Next Steps

**Option A: Continue with Stage 5.2 (Docker)**
- Proceed with Docker validation
- Update tools in parallel before Stage 5.3

**Option B: Update Tools First**
- Complete tool updates now
- Ensures Stages 5.3-5.4 ready to execute

**Recommendation:** **Option A** (Docker validation) since:
- Stage 5.2 doesn't require tool changes
- Gives time to thoroughly test tool updates
- Parallel workstream approach

---

## Summary

**Architecture Corrections:**
- Query: Site-wide (✅ working)
- Modify: Cell-by-cell (⚠️ requires 6 commands)
- Rollback: Cell-by-cell (⚠️ requires 6 commands)

**Files Updated:**
- ✅ `network/huawei_api_client.py` - Batch execution method added
- ✅ `test_api_postman_replication.py` - Validation complete

**Files Requiring Updates:**
- ⏳ `tools/huawei_tools.py` - Add site_name, batch tool
- ⏳ `domain/mml_commands.py` - Add template builder
- ⏳ `agents/mml_executor_agent.py` - Use batch execution
- ⏳ `tools/rollback_manager.py` - NEW file for Stage 5.4

**Phase 5.1 Status:** ✅ COMPLETE (100% API connectivity)
**Next Stage:** Stage 5.2 (Docker Deployment Validation)

---

**Document End** | Version 1.0 | 2025-11-03
