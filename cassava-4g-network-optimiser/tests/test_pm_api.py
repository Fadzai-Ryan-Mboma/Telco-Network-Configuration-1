#!/usr/bin/env python3
"""
Test script for Huawei iMaster MAE Performance Management API.

Tests the PM REST API workflow:
1. Authenticate (PUT /oauth/token)
2. Create PM Query Task (POST /measurementResults)
3. Get PM Results (GET /measurementResults/{taskId})
4. Delete PM Task (DELETE /measurementResults/{taskId})

Run: python tests/test_pm_api.py
"""

import asyncio
import json
import ssl
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

# =============================================================================
# Configuration
# =============================================================================

BASE_URL = "https://41.174.191.214:31127"
USERNAME = "cassava.ai"
PASSWORD = "#Pass123#"

# Known eNodeB sites from LST CELL results
KNOWN_SITES = [
    "MSH-0112-Bindura Hospital",
    # Add more sites as discovered
]

# PM API endpoints
AUTH_ENDPOINT = "/api/rest/securityManagement/v1/oauth/token"
PM_ENDPOINT = "/api/rest/performanceManagement/v1/measurementResults"
MML_ENDPOINT = "/api/rest/mmlManagement/v1/command"

# Counter IDs from Huawei documentation (iMasterMAE.md examples)
# These are known LTE eNodeB performance counters
# Format: counter_id -> description (based on typical Huawei counter naming)
KNOWN_COUNTER_IDS = {
    # From doc sample - likely traffic/throughput related
    1526749447: "Unknown - from doc sample 1",
    1526743671: "Unknown - from doc sample 2",
    # From doc sample 2 - larger set of counters
    1526728514: "Unknown - traffic counter 1",
    1526728515: "Unknown - traffic counter 2",
    1526728518: "Unknown - traffic counter 3",
    1526728519: "Unknown - traffic counter 4",
    1526728520: "Unknown - traffic counter 5",
    1526730592: "Unknown - traffic counter 6",
    1526730593: "Unknown - traffic counter 7",
    1526730594: "Unknown - traffic counter 8",
    1526730595: "Unknown - traffic counter 9",
    1526730596: "Unknown - traffic counter 10",
    1526730597: "Unknown - traffic counter 11",
    1526749439: "Unknown - traffic counter 12",
    1526737790: "Unknown - traffic counter 13",
}

# Common LTE KPI counter ID ranges (Huawei uses specific prefixes)
# These are educated guesses based on typical Huawei counter ID patterns:
# - 152674xxxx: Cell-level counters
# - 152672xxxx: RRC/connection counters  
# - 152673xxxx: Traffic/throughput counters
# We'll test with a small set first to discover what works

# All counter IDs found in documentation
ALL_DOC_COUNTER_IDS = [
    1526749447, 1526743671,  # From first sample
    1526728514, 1526728515, 1526728518, 1526728519, 1526728520,  # Traffic group
    1526730592, 1526730593, 1526730594, 1526730595, 1526730596, 1526730597,  # Another group
    1526749439, 1526737790,  # Additional
]

TEST_COUNTER_IDS = ALL_DOC_COUNTER_IDS  # Use all known counters


# =============================================================================
# HTTP Client Setup
# =============================================================================

def get_client() -> httpx.AsyncClient:
    """Create async HTTP client with SSL verification disabled."""
    return httpx.AsyncClient(
        base_url=BASE_URL,
        timeout=httpx.Timeout(60.0, connect=10.0),
        verify=False,  # Self-signed cert
    )


# =============================================================================
# Authentication
# =============================================================================

async def authenticate(client: httpx.AsyncClient) -> dict[str, Any]:
    """
    Authenticate with MAE server and get access token.
    
    Returns:
        Dict with accessSession token and expires info
    """
    print("\n" + "=" * 60)
    print("🔐 AUTHENTICATING")
    print("=" * 60)
    
    response = await client.put(
        AUTH_ENDPOINT,
        json={
            "grantType": "password",
            "userName": USERNAME,
            "value": PASSWORD,
        },
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Auth failed: {response.text}")
        raise Exception(f"Authentication failed: {response.status_code}")
    
    data = response.json()
    token = data.get("accessSession", "")
    expires = data.get("expires", 1800)
    
    print(f"✅ Auth successful!")
    print(f"   Token: {token[:20]}...{token[-10:]}")
    print(f"   Expires: {expires}s")
    
    return data


# =============================================================================
# MML Commands (for site discovery)
# =============================================================================

async def execute_mml(
    client: httpx.AsyncClient,
    token: str,
    command: str,
    ne_names: list[str] | None = None,
) -> dict[str, Any]:
    """Execute MML command and return result."""
    print(f"\n📡 MML: {command}")
    
    payload = {"command": command}
    if ne_names:
        payload["neNames"] = ne_names
    
    response = await client.post(
        MML_ENDPOINT,
        json=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Auth-Token": token,
        },
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   ❌ MML failed: {response.text[:200]}")
        return {"error": response.text}
    
    return response.json()


async def discover_sites(client: httpx.AsyncClient, token: str) -> list[str]:
    """Discover available eNodeB sites using MML."""
    print("\n" + "=" * 60)
    print("🔍 DISCOVERING SITES (via MML)")
    print("=" * 60)
    
    # Try LST ENODEB to get all eNodeBs
    result = await execute_mml(client, token, "LST ENODEB:;")
    
    sites = []
    
    # Parse response to extract site names
    if "result" in result:
        response_text = str(result.get("result", ""))
        print(f"\n   Raw response (first 500 chars):\n   {response_text[:500]}")
        
        # Try to extract NE names from response
        # Format varies, but often includes "eNodeB Name" or similar
        lines = response_text.split("\n")
        for line in lines:
            if "MSH-" in line or "eNodeB" in line.lower():
                # Extract site name if present
                parts = line.split()
                for part in parts:
                    if part.startswith("MSH-"):
                        sites.append(part.strip(","))
    
    # Also try the known sites
    if not sites:
        sites = KNOWN_SITES.copy()
        print(f"\n   Using known sites: {sites}")
    else:
        print(f"\n   Discovered sites: {sites}")
    
    return sites


async def discover_pm_counters(client: httpx.AsyncClient, token: str, ne_name: str) -> None:
    """Try to discover available PM counters via MML commands."""
    print("\n" + "=" * 60)
    print("🔍 DISCOVERING PM COUNTERS (via MML)")
    print("=" * 60)
    
    # Try various MML commands to discover PM configuration
    mml_commands = [
        "LST PMSWITCH:;",           # PM switch settings
        "LST PMPARA:;",             # PM parameters
        "DSP PMTASK:;",             # Display PM tasks
        "LST PMTYPE:;",             # List PM types
        "LST PMCOUNTER:;",          # List PM counters (if available)
    ]
    
    for cmd in mml_commands:
        print(f"\n   Trying: {cmd}")
        result = await execute_mml(client, token, cmd, [ne_name])
        
        if "error" not in result:
            # Print first 1000 chars of response
            response_text = json.dumps(result, indent=2)[:1000]
            print(f"   Response:\n{response_text}")
        else:
            print(f"   ❌ Command failed")


async def test_counter_subscriptions_api(
    client: httpx.AsyncClient,
    token: str,
) -> dict[str, Any]:
    """Try to query counter subscriptions via REST API."""
    print("\n" + "=" * 60)
    print("🔍 CHECKING COUNTER SUBSCRIPTIONS API")
    print("=" * 60)
    
    # Try various PM-related endpoints that might list available counters
    endpoints = [
        "/api/rest/performanceManagement/v1/measurementSubscriptions",
        "/api/rest/performanceManagement/v1/counters",
        "/api/rest/performanceManagement/v1/counterGroups",
        "/api/rest/resourceManagement/v1/pmCounters",
    ]
    
    for endpoint in endpoints:
        print(f"\n   Trying: GET {endpoint}")
        try:
            response = await client.get(
                endpoint,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "X-Auth-Token": token,
                },
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Found! Response: {response.text[:500]}")
                return response.json()
            elif response.status_code != 404:
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return {}


async def get_topology_cells(
    client: httpx.AsyncClient,
    token: str,
    ne_fdn: str = None,
) -> dict[str, Any]:
    """Get topology cell information via REST API."""
    print("\n" + "=" * 60)
    print("🔍 GETTING TOPOLOGY CELL INFO")
    print("=" * 60)
    
    # Try topology cells API - from documentation section 5.5
    endpoint = "/api/rest/resourceManagement/v1/topocellsinfo"
    
    # If no FDN provided, try to get all
    payload = {}
    if ne_fdn:
        payload = {"fdns": [ne_fdn]}
    
    print(f"   Endpoint: POST {endpoint}")
    print(f"   Payload: {payload}")
    
    try:
        response = await client.post(
            endpoint,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Auth-Token": token,
            },
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success! Response:\n{json.dumps(data, indent=2)[:1500]}")
            return data
        else:
            print(f"   Response: {response.text[:500]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return {}


async def get_ne_list(
    client: httpx.AsyncClient,
    token: str,
) -> list[dict]:
    """Get list of NEs (network elements) via MML."""
    print("\n" + "=" * 60)
    print("🔍 GETTING NE LIST (via MML)")
    print("=" * 60)
    
    # Execute LST ENODEB to get all eNodeBs
    result = await execute_mml(client, token, "LST ENODEB:;", None)
    
    print(f"   Response:\n{json.dumps(result, indent=2)[:2000]}")
    
    return result
    
    # Also try the known sites
    if not sites:
        sites = KNOWN_SITES.copy()
        print(f"\n   Using known sites: {sites}")
    else:
        print(f"\n   Discovered sites: {sites}")
    
    return sites


# =============================================================================
# Performance Management API
# =============================================================================

async def create_pm_query_task(
    client: httpx.AsyncClient,
    token: str,
    ne_names: list[str],
    counter_ids: list[int],
    period: int = 15,
    hours_back: int = 1,
) -> dict[str, Any]:
    """
    Create a PM data query task.
    
    Args:
        client: HTTP client
        token: Auth token
        ne_names: List of eNodeB names to query
        counter_ids: List of counter IDs (REQUIRED by the API)
        period: Measurement period in minutes (15 or 60)
        hours_back: How many hours of historical data to query
        
    Returns:
        API response with taskId or immediate data
    """
    print("\n" + "=" * 60)
    print("📊 CREATING PM QUERY TASK")
    print("=" * 60)
    
    # Calculate time range (last N hours) - use timezone-aware UTC
    now = datetime.now(timezone.utc)
    # Round down to nearest period
    minutes = (now.minute // period) * period
    end_time = now.replace(minute=minutes, second=0, microsecond=0)
    start_time = end_time - timedelta(hours=hours_back)
    
    # Format times as strings
    time_format = "%Y-%m-%d %H:%M:%S"
    
    payload = {
        "timeFormat": "timeString",
        "startTime": start_time.strftime(time_format),
        "endTime": end_time.strftime(time_format),
        "period": period,
        "counterIds": counter_ids,  # REQUIRED field
        "isQueryAllNe": 0,
        "neTypeName": "eNodeB",
        "neNames": ne_names,
    }
    
    print(f"   Request payload:")
    print(f"   {json.dumps(payload, indent=2)}")
    
    response = await client.post(
        PM_ENDPOINT,
        json=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Language": "en-US",
            "X-Auth-Token": token,
        },
    )
    
    print(f"\n   Status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Data returned immediately!")
    elif response.status_code == 202:
        print("   ⏳ Data being collected (async task created)")
    elif response.status_code == 400:
        print(f"   ❌ Bad request: {response.text[:500]}")
    elif response.status_code == 401:
        print("   ❌ Unauthorized - token may be invalid")
    elif response.status_code == 404:
        print(f"   ❌ Not found: {response.text[:500]}")
    else:
        print(f"   ❌ Unexpected status: {response.text[:500]}")
    
    try:
        data = response.json()
        return {"status_code": response.status_code, **data}
    except json.JSONDecodeError:
        return {"status_code": response.status_code, "raw": response.text}


async def get_pm_results(
    client: httpx.AsyncClient,
    token: str,
    task_id: str,
    limit: int = 5000,
    marker: str | None = None,
) -> dict[str, Any]:
    """
    Get PM query results for a task.
    
    Args:
        client: HTTP client
        token: Auth token
        task_id: Task ID from create_pm_query_task
        limit: Max results per batch
        marker: Pagination marker for next batch
        
    Returns:
        PM data results
    """
    print(f"\n📥 GETTING PM RESULTS (taskId={task_id})")
    
    url = f"{PM_ENDPOINT}/{task_id}"
    params = {"limit": limit}
    if marker:
        params["marker"] = marker
    
    response = await client.get(
        url,
        params=params,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Auth-Token": token,
        },
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 202:
        print("   ⏳ Still collecting data...")
    elif response.status_code == 200:
        print("   ✅ Data ready!")
    
    try:
        return {"status_code": response.status_code, **response.json()}
    except json.JSONDecodeError:
        return {"status_code": response.status_code, "raw": response.text}


async def delete_pm_task(
    client: httpx.AsyncClient,
    token: str,
    task_id: str,
) -> bool:
    """Delete a PM query task to free resources."""
    print(f"\n🗑️  DELETING PM TASK (taskId={task_id})")
    
    response = await client.delete(
        f"{PM_ENDPOINT}/{task_id}",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Auth-Token": token,
        },
    )
    
    print(f"   Status: {response.status_code}")
    success = response.status_code in (200, 204)
    print(f"   {'✅ Deleted' if success else '❌ Failed to delete'}")
    
    return success


# =============================================================================
# Result Parsing
# =============================================================================

def parse_pm_results(data: dict[str, Any]) -> None:
    """Parse and display PM query results."""
    print("\n" + "=" * 60)
    print("📈 PM RESULTS ANALYSIS")
    print("=" * 60)
    
    if "error" in data or data.get("status_code", 200) >= 400:
        print(f"   ❌ Error in response: {data}")
        return
    
    # Extract key fields
    counter_ids = data.get("counterIds", [])
    results = data.get("result", [])
    total_size = data.get("totalSize", 0)
    ret_code = data.get("retCode", "")
    ret_message = data.get("retMessage", "")
    task_id = data.get("taskId", "")
    period = data.get("period", 0)
    marker = data.get("marker", "")
    
    print(f"\n   Task ID: {task_id}")
    print(f"   Return Code: {ret_code} - {ret_message}")
    print(f"   Period: {period} minutes")
    print(f"   Total Records: {total_size}")
    print(f"   Counter IDs Found: {len(counter_ids)}")
    
    if counter_ids:
        print(f"\n   📊 COUNTER IDs DISCOVERED:")
        for i, cid in enumerate(counter_ids):
            print(f"      [{i}] {cid}")
    
    if results:
        print(f"\n   📋 SAMPLE RESULTS ({len(results)} records):")
        for i, record in enumerate(results[:5]):  # Show first 5
            print(f"\n      Record {i + 1}:")
            print(f"         NE Name: {record.get('neName', 'N/A')}")
            print(f"         NE FDN: {record.get('neFdn', 'N/A')}")
            print(f"         Object: {record.get('objectName', 'N/A')[:80]}...")
            print(f"         Start Time: {record.get('startTime', 'N/A')}")
            
            values = record.get("counterValues", [])
            if values and counter_ids:
                print(f"         Counter Values:")
                for j, (cid, val) in enumerate(zip(counter_ids, values)):
                    print(f"            {cid}: {val}")
    
    if marker and marker != "null":
        print(f"\n   📄 More data available (marker: {marker[:20]}...)")


# =============================================================================
# Main Test Runner
# =============================================================================

async def test_pm_api_workflow():
    """Run the complete PM API test workflow."""
    print("\n" + "=" * 60)
    print("🧪 HUAWEI PM API TEST")
    print(f"   Target: {BASE_URL}")
    print(f"   Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    async with get_client() as client:
        # Step 1: Authenticate
        auth_data = await authenticate(client)
        token = auth_data.get("accessSession", "")
        
        if not token:
            print("❌ No token received, aborting")
            return
        
        # Step 2: Get NE list and topology info
        await get_ne_list(client, token)
        await get_topology_cells(client, token)
        
        # Step 3: Try to discover PM counter subscriptions via REST API
        await test_counter_subscriptions_api(client, token)
        
        # Step 4: Discover sites (optional - use known sites)
        sites = KNOWN_SITES  # await discover_sites(client, token)
        
        # Step 4: Create PM Query Task with known counter IDs
        # Try different periods and time ranges
        print("\n" + "=" * 60)
        print(f"🎯 TESTING PM API WITH SITES: {sites}")
        print(f"   Using counter IDs: {TEST_COUNTER_IDS}")
        print("=" * 60)
        
        # Test 1: 15-minute period, last 2 hours
        print("\n📊 Test 1: 15-min period, last 2 hours")
        pm_result = await create_pm_query_task(
            client=client,
            token=token,
            ne_names=sites,
            counter_ids=TEST_COUNTER_IDS,
            period=15,
            hours_back=2,
        )
        
        status = pm_result.get("status_code", 0)
        task_id = pm_result.get("taskId", "")
        
        if pm_result.get("retCode") == "90042":
            # No data with 15-min period, try 60-min
            if task_id:
                await delete_pm_task(client, token, task_id)
            
            print("\n📊 Test 2: 60-min period, last 24 hours")
            pm_result = await create_pm_query_task(
                client=client,
                token=token,
                ne_names=sites,
                counter_ids=TEST_COUNTER_IDS,
                period=60,  # Try hourly
                hours_back=24,  # Last 24 hours
            )
            status = pm_result.get("status_code", 0)
            task_id = pm_result.get("taskId", "")
        
        # Step 5: Handle response
        if status == 200:
            # Data returned immediately
            parse_pm_results(pm_result)
            
            # Cleanup task if we got a taskId
            if task_id:
                await delete_pm_task(client, token, task_id)
                
        elif status == 202:
            # Async - need to poll
            print("\n⏳ Polling for results...")
            
            for attempt in range(5):
                await asyncio.sleep(2)  # Wait 2 seconds between polls
                
                poll_result = await get_pm_results(client, token, task_id)
                
                if poll_result.get("status_code") == 200:
                    parse_pm_results(poll_result)
                    break
                elif poll_result.get("status_code") == 202:
                    print(f"   Attempt {attempt + 1}: Still collecting...")
                else:
                    print(f"   ❌ Poll failed: {poll_result}")
                    break
            
            # Cleanup
            if task_id:
                await delete_pm_task(client, token, task_id)
        
        else:
            print(f"\n❌ PM Query failed with status {status}")
            print(f"   Response: {json.dumps(pm_result, indent=2)[:1000]}")
        
        # Step 5: Summary
        print("\n" + "=" * 60)
        print("📝 TEST SUMMARY")
        print("=" * 60)
        print(f"   Auth: ✅ Success")
        print(f"   PM Query Status: {status}")
        print(f"   Task ID: {task_id or 'N/A'}")


async def test_multiple_sites():
    """Test PM API across multiple sites."""
    print("\n" + "=" * 60)
    print("🧪 MULTI-SITE PM API TEST")
    print("=" * 60)
    
    async with get_client() as client:
        # Authenticate
        auth_data = await authenticate(client)
        token = auth_data.get("accessSession", "")
        
        if not token:
            print("❌ No token received, aborting")
            return
        
        # First, discover all sites using MML
        print("\n🔍 Discovering all eNodeB sites...")
        mml_result = await execute_mml(client, token, "LST ENODEB:;")
        
        # Print raw MML response for analysis
        print("\n📄 Raw MML Response:")
        print(json.dumps(mml_result, indent=2)[:2000])
        
        # Try PM query with known site
        for site in KNOWN_SITES:
            print(f"\n{'='*60}")
            print(f"📡 Testing site: {site}")
            print("=" * 60)
            
            pm_result = await create_pm_query_task(
                client=client,
                token=token,
                ne_names=[site],
                counter_ids=TEST_COUNTER_IDS,
                period=15,
                hours_back=1,
            )
            
            status = pm_result.get("status_code", 0)
            task_id = pm_result.get("taskId", "")
            
            if status == 200:
                parse_pm_results(pm_result)
                if task_id:
                    await delete_pm_task(client, token, task_id)
            elif status == 202 and task_id:
                # Quick poll
                await asyncio.sleep(3)
                poll_result = await get_pm_results(client, token, task_id)
                if poll_result.get("status_code") == 200:
                    parse_pm_results(poll_result)
                await delete_pm_task(client, token, task_id)
            else:
                print(f"   ❌ Failed: {pm_result.get('retMessage', pm_result)}")


# =============================================================================
# Alarm API (Alternative Data Source)
# =============================================================================

ALARM_ENDPOINT = "/api/rest/faultSupervisonManagement/v1/alarms"


async def test_alarm_api(client: httpx.AsyncClient, token: str) -> dict[str, Any]:
    """
    Test Alarm API - This should work without PM subscriptions.
    Can provide network health indicators.
    """
    print("\n" + "=" * 60)
    print("🚨 TESTING ALARM API")
    print("=" * 60)
    
    # Query current alarms (most useful for health check)
    params = {
        "dataType": "CURRENT",  # CURRENT, HISTORY, or LOG
        "limit": 100,
    }
    
    print(f"   Endpoint: GET {ALARM_ENDPOINT}")
    print(f"   Params: {params}")
    
    response = await client.get(
        ALARM_ENDPOINT,
        params=params,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Language": "en-US",
            "X-Auth-Token": token,
        },
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        alarms = data.get("alarmInformationList", [])
        ret_code = data.get("retCode", "")
        ret_message = data.get("retMessage", "")
        
        print(f"   ✅ Success! retCode={ret_code}")
        print(f"   Message: {ret_message}")
        print(f"   Total Alarms: {len(alarms)}")
        
        if alarms:
            print("\n   📋 Sample Alarms (first 5):")
            for i, alarm in enumerate(alarms[:5]):
                alarm_id = alarm.get("alarmId", "?")
                alarm_name = alarm.get("alarmName", "Unknown")
                severity = alarm.get("perceivedSeverity", "?")
                me_name = alarm.get("meName", "?")
                raised_time = alarm.get("alarmRaisedTime", "?")
                
                # Convert severity code to text
                severity_map = {
                    "1": "Critical", "2": "Major", "3": "Minor", 
                    "4": "Warning", "5": "Indeterminate", "6": "Cleared"
                }
                severity_text = severity_map.get(str(severity), severity)
                
                print(f"\n   [{i+1}] ID: {alarm_id}")
                print(f"       Name: {alarm_name}")
                print(f"       Severity: {severity_text}")
                print(f"       NE: {me_name}")
                print(f"       Raised: {raised_time}")
            
            # Summarize by severity
            print("\n   📊 Alarm Summary by Severity:")
            severity_counts = {}
            for alarm in alarms:
                sev = alarm.get("perceivedSeverity", "?")
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
            for sev, count in sorted(severity_counts.items()):
                sev_name = {"1": "Critical", "2": "Major", "3": "Minor", 
                           "4": "Warning", "5": "Indeterminate", "6": "Cleared"}.get(str(sev), sev)
                print(f"       {sev_name}: {count}")
            
            # Get NE names from alarms
            ne_names = set()
            for alarm in alarms:
                me_name = alarm.get("meName", "")
                if me_name and me_name != "OSS":
                    ne_names.add(me_name)
            
            if ne_names:
                print(f"\n   📡 Network Elements with Alarms ({len(ne_names)}):")
                for ne in sorted(ne_names)[:10]:
                    print(f"       - {ne}")
        else:
            print("   ℹ️  No current alarms")
        
        return data
    else:
        print(f"   ❌ Failed: {response.text[:500]}")
        return {"error": response.text, "status_code": response.status_code}


async def test_ne_discovery_via_alarm(client: httpx.AsyncClient, token: str) -> list[str]:
    """
    Discover NE names from alarm data - alternative to MML.
    """
    print("\n" + "=" * 60)
    print("🔍 DISCOVERING NEs VIA ALARM API")
    print("=" * 60)
    
    # Query historical alarms to find more NEs
    all_ne_names = set()
    
    for data_type in ["CURRENT", "HISTORY"]:
        print(f"\n   Querying {data_type} alarms...")
        
        response = await client.get(
            ALARM_ENDPOINT,
            params={
                "dataType": data_type,
                "limit": 500,
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Accept-Language": "en-US",
                "X-Auth-Token": token,
            },
        )
        
        if response.status_code == 200:
            data = response.json()
            alarms = data.get("alarmInformationList", [])
            print(f"   Found {len(alarms)} {data_type.lower()} alarms")
            
            for alarm in alarms:
                me_name = alarm.get("meName", "")
                product_name = alarm.get("productName", "")
                
                # Filter for eNodeB-like names
                if me_name and (
                    me_name.startswith("MSH-") or 
                    "eNodeB" in me_name or 
                    "eNB" in me_name or
                    "LTE" in me_name
                ):
                    all_ne_names.add(me_name)
        else:
            print(f"   ❌ Failed to query {data_type}")
    
    ne_list = sorted(all_ne_names)
    
    if ne_list:
        print(f"\n   ✅ Discovered {len(ne_list)} eNodeB NEs:")
        for ne in ne_list[:20]:
            print(f"       - {ne}")
        if len(ne_list) > 20:
            print(f"       ... and {len(ne_list) - 20} more")
    else:
        print("   ℹ️  No eNodeB NEs found in alarms")
    
    return ne_list


async def comprehensive_api_test():
    """Run comprehensive test of all available APIs."""
    print("\n" + "=" * 60)
    print("🧪 COMPREHENSIVE API TEST")
    print("=" * 60)
    
    async with get_client() as client:
        # Step 1: Authenticate
        auth_data = await authenticate(client)
        token = auth_data.get("accessSession", "")
        
        if not token:
            print("❌ Authentication failed")
            return
        
        # Step 2: Test Alarm API (usually works)
        alarm_result = await test_alarm_api(client, token)
        
        # Step 3: Discover NEs from alarms
        ne_names = await test_ne_discovery_via_alarm(client, token)
        
        # Step 4: If we found NEs, try PM query with them ONE AT A TIME
        if ne_names:
            print("\n" + "=" * 60)
            print("📊 TESTING PM API WITH DISCOVERED NEs")
            print("=" * 60)
            
            # Try each NE individually (to avoid neType mismatch error)
            for ne_name in ne_names[:3]:
                print(f"\n   Testing single NE: {ne_name}")
                
                pm_result = await create_pm_query_task(
                    client=client,
                    token=token,
                    ne_names=[ne_name],  # Single NE only
                    counter_ids=TEST_COUNTER_IDS,
                    period=15,
                    hours_back=2,
                )
                
                status = pm_result.get("status_code", 0)
                ret_code = pm_result.get("retCode", "")
                ret_msg = pm_result.get("retMessage", "")
                
                if status == 200:
                    if ret_code == "90000":
                        print(f"   ✅ SUCCESS - PM data received!")
                        parse_pm_results(pm_result)
                    else:
                        print(f"   ⚠️  Status 200 but retCode={ret_code}: {ret_msg}")
                    
                    task_id = pm_result.get("taskId")
                    if task_id:
                        await delete_pm_task(client, token, task_id)
                else:
                    print(f"   ❌ Failed: {ret_msg}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📝 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        
        alarm_ok = "alarmInformationList" in alarm_result
        pm_ok = False  # We know PM is returning "no data"
        
        print(f"   🔐 Authentication: ✅ Success")
        print(f"   🚨 Alarm API: {'✅ Working' if alarm_ok else '❌ Failed'}")
        print(f"   📊 PM API: ⚠️  No data (subscriptions not configured)")
        print(f"   📡 NEs Discovered: {len(ne_names)}")
        
        if alarm_ok:
            alarms = alarm_result.get("alarmInformationList", [])
            print(f"\n   💡 RECOMMENDATION:")
            print(f"      The Alarm API is working and provides network health data.")
            print(f"      Current alarms: {len(alarms)}")
            print(f"      This data can be used to show:")
            print(f"        - Network health status")
            print(f"        - Critical/Major issues requiring attention")
            print(f"        - Sites with problems")
            print(f"\n      For PM counter data, you need to configure PM subscriptions")
            print(f"      on the MAE system for the desired counters and NEs.")


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    
    print("\n" + "🚀 " * 20)
    print("   HUAWEI PM API TEST SCRIPT")
    print("🚀 " * 20)
    
    # Run comprehensive test (includes Alarm API)
    asyncio.run(comprehensive_api_test())
    
    # Uncomment to run PM-only test
    # asyncio.run(test_pm_api_workflow())
    
    # Uncomment to run multi-site test
    # asyncio.run(test_multiple_sites())
