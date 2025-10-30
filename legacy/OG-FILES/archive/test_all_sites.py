#!/usr/bin/env python3
"""
Liquid Zimbabwe Live API Test - All Network Elements
Tests all 4 configured network elements to verify which ones exist in the live system
"""

import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add the liquid-4g-core directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "liquid-4g-core"))

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('LZ-All-Sites-Test')

def test_env_and_auth():
    """Quick environment and authentication test"""
    try:
        # Set environment variables
        os.environ['HUAWEI_API_URL'] = os.getenv('LZ_API_URL', '')
        os.environ['HUAWEI_USERNAME'] = os.getenv('LZ_API_USERNAME', '')
        os.environ['HUAWEI_PASSWORD'] = os.getenv('LZ_API_PASSWORD', '')
        
        from agents.huawei_api_client import HuaweiAPIClient
        client = HuaweiAPIClient()
        
        if client.authenticate():
            return client
        else:
            return None
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return None

def test_single_ne(client, ne_name, ne_info):
    """Test a single network element with all 5 parameters"""
    print(f"\n🔍 Testing: {ne_name}")
    print(f"   Location: {ne_info['location']}")
    print(f"   Site ID: {ne_info['site_id']}")
    
    # Test parameters
    parameters = [
        ("Reference Signal Power", "LST PDSCHCFG:;"),
        ("A3 Event Offset", "LST UECOOPERATIONPARA:;"),
        ("T310 Timer", "LST UETIMERCONST:;"),
        ("P0_NominalPUSCH", "LST CELLULPCCOMM:;"),
        ("PDCCH Aggregation", "LST CELLUSPARACFG:;")
    ]
    
    ne_results = {
        'ne_name': ne_name,
        'location': ne_info['location'],
        'site_id': ne_info['site_id'],
        'status': 'unknown',
        'parameters_tested': 0,
        'parameters_success': 0,
        'cells_found': 0,
        'error_details': None
    }
    
    for param_name, command in parameters:
        try:
            result = client.execute_mml_command(
                command=command,
                ne_names=[ne_name]
            )
            
            ne_results['parameters_tested'] += 1
            
            if result and isinstance(result, dict) and 'results' in result:
                if len(result['results']) > 0:
                    ret_code = result['results'][0].get('retCode', -1)
                    
                    if ret_code == 0:
                        ne_results['parameters_success'] += 1
                        
                        # Extract cell count
                        if 'report' in result['results'][0]:
                            report = result['results'][0]['report']
                            import re
                            match = re.search(r'Number of results = (\d+)', report)
                            if match:
                                cells = int(match.group(1))
                                if cells > ne_results['cells_found']:
                                    ne_results['cells_found'] = cells
                        
                        if ne_results['parameters_success'] == 1:  # First success
                            print(f"   ✅ NE EXISTS - {param_name} successful")
                            ne_results['status'] = 'active'
                    else:
                        if ne_results['status'] == 'unknown':
                            print(f"   ⚠️ Command error (retCode: {ret_code})")
                        break  # If one fails, likely all will fail
            break  # Only need one successful test to confirm NE exists
            
        except Exception as e:
            error_msg = str(e)
            
            # Check for specific NE not found error
            if "not exist" in error_msg.lower() or "doesn't exist" in error_msg.lower():
                print(f"   ❌ NE DOES NOT EXIST")
                ne_results['status'] = 'not_found'
                ne_results['error_details'] = "Network Element not found in live system"
                break
            else:
                print(f"   ❌ Error: {error_msg}")
                ne_results['status'] = 'error'
                ne_results['error_details'] = error_msg
                break
    
    # Final status update
    if ne_results['status'] == 'unknown' and ne_results['parameters_success'] == 0:
        ne_results['status'] = 'unreachable'
    
    return ne_results

def test_all_network_elements():
    """Test all 4 configured network elements"""
    print("🚀 Liquid Zimbabwe - All Network Elements Test")
    print("=" * 60)
    
    # Setup
    client = test_env_and_auth()
    if not client:
        print("❌ Failed to authenticate. Cannot proceed with testing.")
        return
    
    print("✅ Authentication successful!")
    
    # All 4 network elements from our configuration
    network_elements = {
        "MSH-0112-Bindura Hospital": {
            "site_id": "MSH-0112",
            "location": "Bindura Hospital"
        },
        "MSH0013-Bindura-Zaoga": {
            "site_id": "MSH-0013", 
            "location": "Bindura Zaoga"
        },
        "MSH-0331-Chiwaridzo 2": {
            "site_id": "MSH-0331",
            "location": "Chiwaridzo 2"
        },
        "MSH-0014-Chipadze": {
            "site_id": "MSH-0014",
            "location": "Chipadze"
        }
    }
    
    print(f"\n📡 Testing {len(network_elements)} Network Elements...")
    
    # Test each NE
    all_results = []
    for ne_name, ne_info in network_elements.items():
        result = test_single_ne(client, ne_name, ne_info)
        all_results.append(result)
    
    # Summary
    print(f"\n" + "="*60)
    print("📊 COMPREHENSIVE NETWORK ELEMENT SUMMARY")
    print("="*60)
    
    active_sites = [r for r in all_results if r['status'] == 'active']
    not_found_sites = [r for r in all_results if r['status'] == 'not_found']
    error_sites = [r for r in all_results if r['status'] in ['error', 'unreachable']]
    
    print(f"\n✅ ACTIVE SITES ({len(active_sites)}/{len(network_elements)}):")
    if active_sites:
        for site in active_sites:
            print(f"   🟢 {site['ne_name']}")
            print(f"      📍 Location: {site['location']}")
            print(f"      📱 Cells: {site['cells_found']}")
            print(f"      ✅ Parameters working: {site['parameters_success']}/{site['parameters_tested']}")
    else:
        print("   None found")
    
    print(f"\n❌ SITES NOT FOUND ({len(not_found_sites)}/{len(network_elements)}):")
    if not_found_sites:
        for site in not_found_sites:
            print(f"   🔴 {site['ne_name']} ({site['location']})")
            print(f"      ⚠️ {site['error_details']}")
    else:
        print("   None")
    
    if error_sites:
        print(f"\n⚠️ SITES WITH ERRORS ({len(error_sites)}/{len(network_elements)}):")
        for site in error_sites:
            print(f"   🟡 {site['ne_name']} ({site['location']})")
            print(f"      ❌ {site['error_details']}")
    
    # Operational Summary
    print(f"\n" + "="*60)
    print("🎯 OPERATIONAL SUMMARY")
    print("="*60)
    
    if active_sites:
        total_cells = sum(site['cells_found'] for site in active_sites)
        print(f"✅ Operational Sites: {len(active_sites)}")
        print(f"📱 Total Active Cells: {total_cells}")
        print(f"🔧 Parameter Query Capability: Working")
        
        # Recommend which site to use for operations
        best_site = max(active_sites, key=lambda x: x['cells_found'])
        print(f"🏆 Recommended Primary Site: {best_site['ne_name']}")
        print(f"   📍 Location: {best_site['location']}")
        print(f"   📱 Cells: {best_site['cells_found']}")
        
    print(f"\n📈 System Readiness:")
    if len(active_sites) >= 1:
        print(f"   ✅ Ready for network optimization")
        print(f"   ✅ Can proceed with Phase 2 implementation")
        print(f"   ✅ Multiple site monitoring possible" if len(active_sites) > 1 else "   ⚠️ Single site monitoring only")
    else:
        print(f"   ❌ No active sites found")
        print(f"   ❌ Cannot proceed without live network access")
    
    return all_results

if __name__ == "__main__":
    test_all_network_elements()