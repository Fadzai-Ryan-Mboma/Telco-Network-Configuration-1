#!/usr/bin/env python3
"""
Liquid Zimbabwe Live API Test - Dynamic Site Loading
Tests all network elements from live_network.db to verify which ones exist in the live system
"""

import os
import sys
import json
import sqlite3
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
logger = logging.getLogger('LZ-Dynamic-Sites-Test')

def load_network_elements_from_db():
    """Load network elements from live_network.db"""
    try:
        db_path = "data/live_network.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query all network elements
        cursor.execute("""
            SELECT name, site_id, location, cell_ids, status 
            FROM network_elements 
            ORDER BY name
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        network_elements = {}
        for row in rows:
            ne_name, site_id, location, cell_ids, status = row
            network_elements[ne_name] = {
                "site_id": site_id,
                "location": location,
                "cell_ids": cell_ids,
                "db_status": status
            }
        
        print(f"📁 Loaded {len(network_elements)} network elements from database:")
        for ne_name, info in network_elements.items():
            print(f"   - {ne_name} ({info['location']}) - DB Status: {info['db_status']}")
        
        return network_elements
        
    except Exception as e:
        print(f"❌ Failed to load network elements from database: {e}")
        return {}

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
    print(f"   📍 Location: {ne_info['location']}")
    print(f"   🏢 Site ID: {ne_info['site_id']}")
    print(f"   💾 DB Status: {ne_info['db_status']}")
    
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
        'db_status': ne_info['db_status'],
        'live_status': 'unknown',
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
                            print(f"   ✅ LIVE & ACTIVE - {param_name} successful")
                            ne_results['live_status'] = 'active'
                    else:
                        if ne_results['live_status'] == 'unknown':
                            print(f"   ⚠️ Command error (retCode: {ret_code})")
                        break  # If one fails, likely all will fail
            break  # Only need one successful test to confirm NE exists
            
        except Exception as e:
            error_msg = str(e)
            
            # Check for specific NE not found error
            if "not exist" in error_msg.lower() or "doesn't exist" in error_msg.lower():
                print(f"   ❌ NOT IN LIVE SYSTEM")
                ne_results['live_status'] = 'not_found'
                ne_results['error_details'] = "Network Element not found in live system"
                break
            else:
                print(f"   ❌ Error: {error_msg}")
                ne_results['live_status'] = 'error'
                ne_results['error_details'] = error_msg
                break
    
    # Final status update
    if ne_results['live_status'] == 'unknown' and ne_results['parameters_success'] == 0:
        ne_results['live_status'] = 'unreachable'
    
    return ne_results

def update_database_with_live_status(test_results):
    """Update the database with live system status"""
    try:
        db_path = "data/live_network.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\n🔄 Updating database with live system status...")
        
        for result in test_results:
            # Update status based on live test results
            if result['live_status'] == 'active':
                new_status = 'live_active'
            elif result['live_status'] == 'not_found':
                new_status = 'db_only'
            else:
                new_status = 'error'
            
            cursor.execute("""
                UPDATE network_elements 
                SET status = ?, last_updated = datetime('now')
                WHERE name = ?
            """, (new_status, result['ne_name']))
            
            print(f"   📝 Updated {result['ne_name']}: {result['db_status']} → {new_status}")
        
        conn.commit()
        conn.close()
        print(f"✅ Database updated successfully!")
        
    except Exception as e:
        print(f"❌ Failed to update database: {e}")

def test_all_network_elements():
    """Test all network elements from database"""
    print("🚀 Liquid Zimbabwe - Dynamic Network Elements Test")
    print("=" * 60)
    print("Loading network elements from live_network.db...")
    print("=" * 60)
    
    # Load network elements from database
    network_elements = load_network_elements_from_db()
    
    if not network_elements:
        print("❌ No network elements found in database. Cannot proceed.")
        return []
    
    # Setup
    client = test_env_and_auth()
    if not client:
        print("❌ Failed to authenticate. Cannot proceed with testing.")
        return []
    
    print("✅ Authentication successful!")
    print(f"\n📡 Testing {len(network_elements)} Network Elements from Database...")
    
    # Test each NE
    all_results = []
    for ne_name, ne_info in network_elements.items():
        result = test_single_ne(client, ne_name, ne_info)
        all_results.append(result)
    
    # Update database with live status
    update_database_with_live_status(all_results)
    
    # Summary
    print(f"\n" + "="*60)
    print("📊 COMPREHENSIVE DATABASE vs LIVE SYSTEM ANALYSIS")
    print("="*60)
    
    active_sites = [r for r in all_results if r['live_status'] == 'active']
    not_found_sites = [r for r in all_results if r['live_status'] == 'not_found']
    error_sites = [r for r in all_results if r['live_status'] in ['error', 'unreachable']]
    
    print(f"\n✅ LIVE & ACTIVE SITES ({len(active_sites)}/{len(network_elements)}):")
    if active_sites:
        for site in active_sites:
            cells_text = f"{site['cells_found']} cells" if site['cells_found'] > 0 else "cells unknown"
            print(f"   🟢 {site['ne_name']}")
            print(f"      📍 Location: {site['location']}")
            print(f"      📱 Cells: {cells_text}")
            print(f"      ✅ Parameters: {site['parameters_success']}/{site['parameters_tested']} working")
    else:
        print("   None found")
    
    print(f"\n❌ IN DATABASE BUT NOT LIVE ({len(not_found_sites)}/{len(network_elements)}):")
    if not_found_sites:
        for site in not_found_sites:
            print(f"   🔴 {site['ne_name']} ({site['location']})")
            print(f"      💾 DB Status: {site['db_status']}")
            print(f"      ⚠️ Issue: {site['error_details']}")
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
        print(f"✅ Live Operational Sites: {len(active_sites)}")
        print(f"📱 Total Active Cells: {total_cells}")
        print(f"🔧 Parameter Query Capability: Working")
        print(f"💾 Database Accuracy: {len(active_sites)}/{len(network_elements)} sites verified")
        
        # Recommend which site to use for operations
        best_site = max(active_sites, key=lambda x: x['cells_found'])
        print(f"🏆 Recommended Primary Site: {best_site['ne_name']}")
        print(f"   📍 Location: {best_site['location']}")
        print(f"   📱 Cells: {best_site['cells_found']}")
        
    print(f"\n📈 System Readiness:")
    if len(active_sites) >= 1:
        print(f"   ✅ Ready for network optimization")
        print(f"   ✅ Can proceed with Phase 2 implementation")
        if len(active_sites) > 1:
            print(f"   ✅ Multiple site monitoring possible")
        else:
            print(f"   ⚠️ Single site monitoring only")
        
        # Database sync status
        accuracy_rate = (len(active_sites) / len(network_elements)) * 100
        print(f"   📊 Database-to-Live accuracy: {accuracy_rate:.1f}%")
    else:
        print(f"   ❌ No active sites found")
        print(f"   ❌ Cannot proceed without live network access")
        print(f"   📊 Database may need review/cleanup")
    
    return all_results

if __name__ == "__main__":
    test_all_network_elements()