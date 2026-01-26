"""
Test the two failed parameters using their actual current values.
"""

import os
import sys
import re
sys.path.append('/app')

from network.huawei_api_client import HuaweiAPIClient

def extract_value_from_report(report, pattern):
    """Extract a value from MML report using regex"""
    match = re.search(pattern, report, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def test_failed_params():
    """Test Reference Signal Power and PDCCH with actual current values"""
    
    print("=" * 70)
    print("TESTING FAILED PARAMETERS WITH ACTUAL CURRENT VALUES".center(70))
    print("=" * 70)
    print()
    
    # Initialize client
    api_config = {
        'base_url': os.getenv('HUAWEI_API_URL'),
        'username': os.getenv('HUAWEI_USERNAME'),
        'password': os.getenv('HUAWEI_PASSWORD'),
        'timeout': 15,
        'retry_attempts': 1,
        'retry_delay': 2,
        'ssl_verify': False
    }
    
    client = HuaweiAPIClient(api_config)
    if not client.connect():
        print("❌ Connection failed")
        return False
    
    print("✅ Connected to Huawei iMaster MAE")
    print()
    
    site_name = 'MSH-0014-Chipadze'
    cell_id = 1
    
    # TEST 1: Reference Signal Power
    print("=" * 70)
    print("TEST 1: Reference Signal Power".center(70))
    print("=" * 70)
    print()
    
    print("📊 Step 1: Query current REFERENCESIGNALPWR value...")
    query_cmd = f'LST PDSCHCFG: LOCALCELLID={cell_id};'
    print(f"   Command: {query_cmd}")
    
    query_response = client.execute_mml_command(query_cmd, [site_name])
    query_result = query_response.get('results', [{}])[0]
    
    if query_result.get('retCode') == 0:
        report = query_result.get('report', '')
        print(f"   ✅ Query successful")
        print()
        print("   Full report:")
        print("-" * 70)
        print(report)
        print("-" * 70)
        print()
        
        # Try to extract current value
        current_value = extract_value_from_report(report, r'Reference signal power\s*=\s*(-?\d+)')
        if current_value:
            print(f"   📍 Current value: {current_value}")
            print()
            print(f"✍️  Step 2: Testing MOD with actual current value...")
            mod_cmd = f'MOD PDSCHCFG: LOCALCELLID={cell_id}, REFERENCESIGNALPWR={current_value};'
            print(f"   Command: {mod_cmd}")
            
            mod_response = client.execute_mml_command(mod_cmd, [site_name])
            mod_result = mod_response.get('results', [{}])[0]
            
            if mod_result.get('retCode') == 0:
                print(f"   ✅ WRITE SUCCESSFUL with current value {current_value}!")
            else:
                print(f"   ❌ Still failed with RetCode: {mod_result.get('retCode')}")
                print(f"   Result: {mod_result.get('result')}")
        else:
            print("   ⚠️  Could not extract current value from report")
    else:
        print(f"   ❌ Query failed")
    
    print()
    print()
    
    # TEST 2: PDCCH Aggregation Level
    print("=" * 70)
    print("TEST 2: PDCCH Aggregation Level".center(70))
    print("=" * 70)
    print()
    
    print("📊 Step 1: Query current PDCCH configuration...")
    query_cmd = f'LST CELLPDCCHALGO: LOCALCELLID={cell_id};'
    print(f"   Command: {query_cmd}")
    
    query_response = client.execute_mml_command(query_cmd, [site_name])
    query_result = query_response.get('results', [{}])[0]
    
    if query_result.get('retCode') == 0:
        report = query_result.get('report', '')
        print(f"   ✅ Query successful")
        print()
        print("   Full report:")
        print("-" * 70)
        print(report)
        print("-" * 70)
        print()
        
        # Look for aggregation level parameter name in report
        print("   🔍 Searching for aggregation level parameter...")
        aggr_lines = [line for line in report.split('\n') if 'aggr' in line.lower() or 'level' in line.lower()]
        if aggr_lines:
            print("   Found lines mentioning aggregation/level:")
            for line in aggr_lines[:5]:
                print(f"      {line}")
            print()
            
        # Try alternative parameter names
        print("✍️  Step 2: Testing alternative MOD commands...")
        
        alt_commands = [
            f'MOD CELLPDCCHALGO: LOCALCELLID={cell_id}, PDCCHAGGLVL=4;',
            f'MOD CELLPDCCHALGO: LOCALCELLID={cell_id}, AGGRLEVEL=4;',
            f'MOD CELLPDCCH: LOCALCELLID={cell_id}, AGGLEVEL=4;',
        ]
        
        for cmd in alt_commands:
            print(f"   Testing: {cmd}")
            mod_response = client.execute_mml_command(cmd, [site_name])
            mod_result = mod_response.get('results', [{}])[0]
            
            if mod_result.get('retCode') == 0:
                print(f"   ✅ SUCCESS with command: {cmd}")
                break
            else:
                print(f"   ❌ Failed: {mod_result.get('result')} (RetCode: {mod_result.get('retCode')})")
        
    else:
        print(f"   ❌ Query failed")
    
    print()
    print("=" * 70)
    print("TEST COMPLETE".center(70))
    print("=" * 70)

if __name__ == "__main__":
    try:
        test_failed_params()
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
