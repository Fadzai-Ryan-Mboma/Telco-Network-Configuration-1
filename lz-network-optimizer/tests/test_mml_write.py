#!/usr/bin/env python3
"""Test MML command write capability"""
import os, sys
sys.path.append('/app')
from network.huawei_api_client import HuaweiAPIClient

api_config = {
    'base_url': os.getenv('HUAWEI_API_URL'),
    'username': os.getenv('HUAWEI_USERNAME'),
    'password': os.getenv('HUAWEI_PASSWORD'),
    'timeout': 15,
    'retry_attempts': 1,
    'retry_delay': 2,
    'ssl_verify': False
}

print("="*70)
print("MML WRITE COMMAND TEST")
print("="*70)

try:
    client = HuaweiAPIClient(api_config)
    if not client.connect():
        print("❌ Connection failed")
        sys.exit(1)
    
    print("✅ Connected to Huawei iMaster MAE\n")
    
    site_name = 'MSH-0014-Chipadze'
    cell_id = 1
    
    # Test MOD command - write current value back to itself
    print(f"Testing: MOD CELLHOPARACFG for {site_name} cell {cell_id}")
    print("Parameter: HIGHSPEEDTHD (High Speed Handover Threshold)")
    print("Action: Set to 60 km/h (likely current value)")
    print("-"*70)
    
    modify_cmd = f'MOD CELLHOPARACFG: LOCALCELLID={cell_id}, HIGHSPEEDTHD=60;'
    print(f"\nMML Command:\n{modify_cmd}\n")
    
    response = client.execute_mml_command(modify_cmd, [site_name])
    result = response.get('results', [{}])[0]
    
    print("Response:")
    print(f"  Site: {result.get('name')}")
    print(f"  Result: {result.get('result')}")
    print(f"  RetCode: {result.get('retCode')}")
    print(f"  Serial ID: {result.get('serialId')}")
    print(f"\n  Report:\n  {result.get('report', 'No report')}")
    
    print("\n" + "="*70)
    if result.get('result') == 'Success' or result.get('retCode') == 0:
        print("✅✅✅ SUCCESS! MML WRITE COMMAND ACCEPTED BY NODE!")
        print("✅ Parameter modification capability confirmed working!")
    elif result.get('retCode') == -1:
        print("⚠️  Command rejected - likely incorrect format or parameter name")
        print(f"Error message: {result.get('report', '')}")
    else:
        print(f"❓ Unexpected result: {result.get('result')}")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
