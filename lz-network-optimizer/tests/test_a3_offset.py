"""
Test A3OFFSET write command using correct UECOOPERATIONPARA MML command.
This verifies that MML write commands reach the network nodes and are accepted.
"""

import os
import sys
sys.path.append('/app')

from network.huawei_api_client import HuaweiAPIClient

def test_a3_offset():
    print("=" * 55)
    print("A3 OFFSET WRITE TEST".center(55))
    print("=" * 55)
    
    # Initialize client with config from environment
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
    
    # Test parameters
    cell_id = 1
    site_name = 'MSH-0014-Chipadze'
    
    # STEP 1: Query current A3OFFSET value
    print(f"STEP 1: Querying current A3OFFSET for {site_name} cell {cell_id}")
    print("-" * 55)
    query_cmd = f"LST UECOOPERATIONPARA: LOCALCELLID={cell_id};"
    print(f"Query Command: {query_cmd}")
    print()
    
    query_response = client.execute_mml_command(query_cmd, [site_name])
    query_result = query_response.get('results', [{}])[0]
    print(f"Query Result: {query_result.get('result')}")
    print(f"Query RetCode: {query_result.get('retCode')}")
    print()
    print("Query Report:")
    print(query_result.get('report', 'No report'))
    print()
    print("=" * 55)
    print()
    
    # STEP 2: Test MOD command with A3OFFSET=3 (standard value, likely current)
    test_offset = 3  # dB - standard A3 offset value
    
    print(f"STEP 2: Testing MOD command for {site_name} cell {cell_id}")
    print(f"Parameter: A3OFFSET (A3 Event Offset for Handover)")
    print(f"Action: Set to {test_offset} dB (likely current value)")
    print("-" * 55)
    
    # Execute MOD command
    mml_command = f"MOD UECOOPERATIONPARA: LOCALCELLID={cell_id}, A3OFFSET={test_offset};"
    print(f"MML Command:")
    print(mml_command)
    print()
    
    mod_response = client.execute_mml_command(mml_command, [site_name])
    result = mod_response.get('results', [{}])[0]
    
    # Display result
    print("Response:")
    print(f"  Site: {result.get('name', 'N/A')}")
    print(f"  Result: {result.get('result', 'N/A')}")
    print(f"  RetCode: {result.get('retCode', 'N/A')}")
    print(f"  Serial ID: {result.get('serialId', 'N/A')}")
    print()
    print(f"  Report:")
    print(result.get('report', 'No report available'))
    print()
    print("=" * 55)
    print()
    
    # Interpret result
    ret_code = result.get('retCode')
    if ret_code == 0 or result.get('result') == 'Success':
        print("✅✅✅ SUCCESS! MML WRITE COMMAND ACCEPTED BY NODE!")
        print("✅ Parameter modification capability confirmed working!")
        print()
        print("This confirms:")
        print("  • MML write commands reach the network nodes")
        print("  • Commands are processed and accepted")
        print("  • System can modify network parameters")
        print("=" * 55)
        return True
    elif ret_code == -1:
        print("❌ FAILED: Command execution error")
        print(f"Error: {result.get('report', 'Unknown error')}")
        print("=" * 55)
        return False
    else:
        print(f"❓ Unexpected result: {result.get('result', 'Unknown')}")
        print("=" * 55)
        return False

if __name__ == "__main__":
    try:
        success = test_a3_offset()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
