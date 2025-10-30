#!/usr/bin/env python3
"""
Test Huawei iMaster MAE API Connectivity
Validates API access and retrieves basic network information
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from network.huawei_api_client import HuaweiAPIClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api_connectivity():
    """Test complete API connectivity and information retrieval"""

    print("🚀 Huawei iMaster MAE API Connectivity Test")
    print("=" * 70)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    # Configuration
    config = {
        'base_url': os.getenv('LZ_API_URL'),
        'username': os.getenv('LZ_API_USERNAME'),
        'password': os.getenv('LZ_API_PASSWORD'),
        'timeout': 30,
        'retry_attempts': 3,
        'retry_delay': 5,
        'ssl_verify': False  # Set to False for testing with self-signed certs
    }

    print("📋 Configuration:")
    print(f"   Base URL: {config['base_url']}")
    print(f"   Username: {config['username']}")
    print(f"   SSL Verify: {config['ssl_verify']}")
    print(f"   Timeout: {config['timeout']}s")
    print()

    # Test results storage
    results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {}
    }

    try:
        # Initialize API client
        print("🔌 Step 1: Initializing API Client...")
        api_client = HuaweiAPIClient(config)
        print("   ✅ API Client initialized successfully")
        results['tests']['initialization'] = {'status': 'success', 'message': 'Client initialized'}
        print()

    except Exception as e:
        print(f"   ❌ Failed to initialize API client: {str(e)}")
        results['tests']['initialization'] = {'status': 'failed', 'error': str(e)}
        return results

    try:
        # Test 1: Authentication
        print("🔐 Step 2: Testing Authentication...")
        if api_client.connect():
            print("   ✅ Authentication SUCCESSFUL")
            print(f"   📝 Access Token: {api_client.access_token[:20]}..." if api_client.access_token else "   ⚠️ No token received")
            print(f"   ⏰ Token Expires: {api_client.token_expires_at}")
            results['tests']['authentication'] = {
                'status': 'success',
                'token_received': bool(api_client.access_token),
                'token_expires_at': str(api_client.token_expires_at) if api_client.token_expires_at else None
            }
        else:
            print("   ❌ Authentication FAILED")
            results['tests']['authentication'] = {'status': 'failed', 'message': 'Connection failed'}
            return results
        print()

    except Exception as e:
        print(f"   ❌ Authentication error: {str(e)}")
        results['tests']['authentication'] = {'status': 'failed', 'error': str(e)}
        return results

    try:
        # Test 2: Health Check
        print("🏥 Step 3: Testing Health Check...")
        health = api_client.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Details: {json.dumps(health['details'], indent=6)}")
        results['tests']['health_check'] = health
        print()

    except Exception as e:
        print(f"   ⚠️ Health check failed: {str(e)}")
        results['tests']['health_check'] = {'status': 'failed', 'error': str(e)}
        print()

    try:
        # Test 3: Cell List Retrieval
        print("📡 Step 4: Testing Cell Inventory Retrieval...")
        cells = api_client.get_cell_list()
        print(f"   ✅ Retrieved {len(cells)} cells from network")

        if cells and len(cells) > 0:
            print(f"   📊 Sample cell data (first 3):")
            for i, cell in enumerate(cells[:3]):
                print(f"      Cell {i+1}: {json.dumps(cell, indent=9)}")

        results['tests']['cell_list'] = {
            'status': 'success',
            'cell_count': len(cells),
            'sample_cells': cells[:3] if cells else []
        }
        print()

    except Exception as e:
        print(f"   ⚠️ Cell list retrieval failed: {str(e)}")
        results['tests']['cell_list'] = {'status': 'failed', 'error': str(e)}
        print()

    try:
        # Test 4: KPI Data Retrieval (if cells available)
        if 'cell_list' in results['tests'] and results['tests']['cell_list'].get('cell_count', 0) > 0:
            print("📊 Step 5: Testing KPI Data Retrieval...")

            # Try to get KPI data for all cells (or first 5)
            cell_ids = None  # None means all cells
            kpi_data = api_client.get_kpi_data(cell_ids=cell_ids, time_range=15)

            print(f"   ✅ Retrieved KPI data for {len(kpi_data)} cells")

            if kpi_data:
                print(f"   📊 Sample KPI data (first cell):")
                first_cell = list(kpi_data.keys())[0]
                print(f"      Cell ID: {first_cell}")
                print(f"      Data: {json.dumps(kpi_data[first_cell], indent=9)}")

            results['tests']['kpi_data'] = {
                'status': 'success',
                'cells_with_data': len(kpi_data),
                'sample_data': {list(kpi_data.keys())[0]: kpi_data[list(kpi_data.keys())[0]]} if kpi_data else {}
            }
            print()
        else:
            print("⏭️ Step 5: Skipping KPI data test (no cells available)")
            results['tests']['kpi_data'] = {'status': 'skipped', 'reason': 'No cells available'}
            print()

    except Exception as e:
        print(f"   ⚠️ KPI data retrieval failed: {str(e)}")
        results['tests']['kpi_data'] = {'status': 'failed', 'error': str(e)}
        print()

    try:
        # Test 5: Parameter Value Retrieval
        if 'cell_list' in results['tests'] and results['tests']['cell_list'].get('cell_count', 0) > 0:
            print("⚙️ Step 6: Testing Parameter Value Retrieval...")

            # Get first cell ID for testing
            first_cell_id = "CELL_001"  # Use a sample cell ID
            test_parameters = ["REFERENCESIGNALPWR", "P0NOMINALPUSCH"]

            param_data = api_client.get_parameter_values(
                cell_ids=[first_cell_id],
                parameter_names=test_parameters
            )

            print(f"   ✅ Retrieved parameter data")
            print(f"   📊 Parameters: {json.dumps(param_data, indent=6)}")

            results['tests']['parameter_retrieval'] = {
                'status': 'success',
                'parameters_queried': test_parameters,
                'data': param_data
            }
            print()
        else:
            print("⏭️ Step 6: Skipping parameter test (no cells available)")
            results['tests']['parameter_retrieval'] = {'status': 'skipped', 'reason': 'No cells available'}
            print()

    except Exception as e:
        print(f"   ⚠️ Parameter retrieval failed: {str(e)}")
        results['tests']['parameter_retrieval'] = {'status': 'failed', 'error': str(e)}
        print()

    try:
        # Cleanup
        print("🔌 Step 7: Disconnecting...")
        api_client.disconnect()
        print("   ✅ Disconnected successfully")
        results['tests']['disconnect'] = {'status': 'success'}
        print()

    except Exception as e:
        print(f"   ⚠️ Disconnect warning: {str(e)}")
        results['tests']['disconnect'] = {'status': 'warning', 'message': str(e)}
        print()

    # Summary
    print("=" * 70)
    print("📋 TEST SUMMARY")
    print("=" * 70)

    total_tests = len(results['tests'])
    successful_tests = sum(1 for test in results['tests'].values() if test.get('status') == 'success')
    failed_tests = sum(1 for test in results['tests'].values() if test.get('status') == 'failed')
    skipped_tests = sum(1 for test in results['tests'].values() if test.get('status') == 'skipped')

    print(f"Total Tests: {total_tests}")
    print(f"✅ Successful: {successful_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"⏭️ Skipped: {skipped_tests}")
    print()

    results['summary'] = {
        'total': total_tests,
        'successful': successful_tests,
        'failed': failed_tests,
        'skipped': skipped_tests
    }

    # Save results to file
    results_file = f"api_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"📄 Detailed results saved to: {results_file}")
    print()

    return results

if __name__ == "__main__":
    try:
        results = test_api_connectivity()

        # Exit with appropriate code
        if results['summary']['failed'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
