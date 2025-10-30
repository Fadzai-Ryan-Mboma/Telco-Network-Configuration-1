#!/usr/bin/env python3
"""
Test Liquid Zimbabwe 4G System in Fallback Mode
Tests all functionality using historical/simulated data (no live API required)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agents.liquid_zimbabwe_kpi import LiquidZimbabweKPIManager
from agents.liquid_zimbabwe_parameters import LiquidZimbabweParameterManager
from datetime import datetime
import json

def test_kpi_system():
    """Test KPI management system with fallback data"""
    print("=" * 70)
    print("📊 KPI MANAGEMENT SYSTEM TEST")
    print("=" * 70)

    try:
        kpi_manager = LiquidZimbabweKPIManager()
        print("✅ KPI Manager initialized")

        # Test 1: Get KPI Summary
        print("\n1️⃣ Testing KPI Summary...")
        summary = kpi_manager.get_kpi_summary()
        print(f"   Sites: {summary['meta']['site_count']}")
        print(f"   Cells: {summary['meta']['cell_count']}")
        print(f"   Last Updated: {summary['meta']['last_updated']}")

        print("\n   KPI Status:")
        for kpi_key, kpi_data in summary.items():
            if kpi_key != 'meta':
                print(f"   • {kpi_data['user_friendly_name']}: {kpi_data['value']:.2f} {kpi_data['unit']} ({kpi_data['status']})")

        # Test 2: Simulated Data Collection
        print("\n2️⃣ Testing Simulated Data Collection...")
        simulated_data = kpi_manager.collect_live_kpi_data()
        print(f"   Status: {simulated_data['status']}")
        print(f"   Sites Processed: {simulated_data['sites_processed']}")
        print(f"   Collection Time: {simulated_data['collection_time']}")

        if simulated_data['data']:
            first_site = list(simulated_data['data'].keys())[0]
            print(f"\n   Sample Data from {first_site}:")
            for kpi_key, kpi_info in list(simulated_data['data'][first_site].items())[:3]:
                print(f"      {kpi_key}: {kpi_info['value']} ({kpi_info['status']})")

        # Test 3: Alert Checking
        print("\n3️⃣ Testing Alert System...")
        alerts = kpi_manager.check_kpi_alerts()
        if alerts:
            print(f"   Found {len(alerts)} alerts:")
            for alert in alerts[:3]:
                print(f"      {alert['status'].upper()}: {alert['kpi_name']} at {alert['site_name']}")
        else:
            print(f"   No alerts - all KPIs within normal ranges")

        print("\n✅ KPI System Test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ KPI System Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_parameter_system():
    """Test parameter management system"""
    print("\n" + "=" * 70)
    print("⚙️ PARAMETER MANAGEMENT SYSTEM TEST")
    print("=" * 70)

    try:
        param_manager = LiquidZimbabweParameterManager()
        print("✅ Parameter Manager initialized")

        # Test 1: Get All Parameters
        print("\n1️⃣ Testing Parameter Configuration...")
        all_params = param_manager.get_all_parameters()
        print(f"   Total Parameters: {len(all_params)}")

        for param_name, config in list(all_params.items())[:3]:
            print(f"\n   • {config['user_friendly_name']}")
            print(f"     Range: {config['range']}")
            print(f"     Default: {config['default_value']}")

        # Test 2: Parameter Values
        print("\n2️⃣ Testing Parameter Value Retrieval...")
        for param_name in list(all_params.keys())[:3]:
            current_value = param_manager.get_current_parameter_value(param_name)
            print(f"   {param_name}: {current_value}")

        # Test 3: Parameter Validation
        print("\n3️⃣ Testing Parameter Validation...")
        test_param = 'reference_signal_power_rs'
        test_value = -200

        is_valid, message = param_manager.validate_parameter_value(test_param, test_value)
        print(f"   Parameter: {test_param}")
        print(f"   Test Value: {test_value}")
        print(f"   Valid: {is_valid}")
        print(f"   Message: {message}")

        # Test 4: MML Command Generation
        print("\n4️⃣ Testing MML Command Generation...")
        mml_command = param_manager.generate_mml_command(
            param_name='reference_signal_power_rs',
            value=-180,
            site_id='SITE_001',
            cell_id='1'
        )
        print(f"   Generated Command:")
        print(f"   {mml_command}")

        # Test 5: Optimization Suggestions
        print("\n5️⃣ Testing Optimization Engine...")
        test_issues = ['low_download_speed', 'high_upload_quality_issues']
        suggestions = param_manager.suggest_parameter_optimization(test_issues)

        print(f"   Issues: {test_issues}")
        print(f"   Suggestions Generated: {len(suggestions)}")

        if suggestions:
            print(f"\n   Top Suggestion:")
            top = suggestions[0]
            print(f"   Parameter: {top['user_friendly_name']}")
            print(f"   Current: {top['current_value']}")
            print(f"   Suggested: {top['suggested_value']}")
            print(f"   Reason: {top['reason']}")
            print(f"   Impact: {top['impact_level']}")

        print("\n✅ Parameter System Test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Parameter System Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_integration():
    """Test database operations"""
    print("\n" + "=" * 70)
    print("💾 DATABASE INTEGRATION TEST")
    print("=" * 70)

    try:
        import sqlite3

        # Test KPI Database
        print("\n1️⃣ Testing KPI Database...")
        kpi_db = 'data/liquid_zimbabwe.db'
        conn = sqlite3.connect(kpi_db)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM kpi_data")
        kpi_count = cursor.fetchone()[0]
        print(f"   KPI Records: {kpi_count}")

        cursor.execute("SELECT COUNT(DISTINCT site_name) FROM kpi_data")
        site_count = cursor.fetchone()[0]
        print(f"   Unique Sites: {site_count}")

        conn.close()

        # Test Parameter Database
        print("\n2️⃣ Testing Parameter Database...")
        param_db = 'data/live_network.db'
        conn = sqlite3.connect(param_db)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM parameter_data")
        param_count = cursor.fetchone()[0]
        print(f"   Parameter Records: {param_count}")

        cursor.execute("SELECT COUNT(DISTINCT site_id) FROM parameter_data")
        param_sites = cursor.fetchone()[0]
        print(f"   Sites with Parameters: {param_sites}")

        conn.close()

        # Test Platform Database
        print("\n3️⃣ Testing Platform Database...")
        platform_db = 'data/lz_platform.db'
        conn = sqlite3.connect(platform_db)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"   Platform Tables: {len(tables)}")
        for table in tables:
            print(f"      • {table[0]}")

        conn.close()

        print("\n✅ Database Integration Test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Database Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n")
    print("🚀 LIQUID ZIMBABWE 4G - FALLBACK MODE TESTING")
    print("=" * 70)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Mode: OFFLINE (No API Required)")
    print("=" * 70)

    results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {}
    }

    # Run tests
    tests = [
        ('Database Integration', test_database_integration),
        ('KPI Management System', test_kpi_system),
        ('Parameter Management System', test_parameter_system),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            result = test_func()
            results['tests'][test_name] = 'PASSED' if result else 'FAILED'
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results['tests'][test_name] = f'CRASHED: {e}'
            failed += 1

    # Summary
    print("\n" + "=" * 70)
    print("📋 TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/len(tests)*100):.1f}%")

    # Save results
    results['summary'] = {
        'total': len(tests),
        'passed': passed,
        'failed': failed,
        'success_rate': f"{(passed/len(tests)*100):.1f}%"
    }

    results_file = f"fallback_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 Results saved to: {results_file}")
    print("=" * 70)

    # Conclusion
    if passed == len(tests):
        print("\n✅ ALL TESTS PASSED - System Operational in Fallback Mode")
        print("💡 System ready for offline development and testing")
        print("⚠️ Live API required for production deployment")
        return 0
    else:
        print("\n⚠️ SOME TESTS FAILED - Review errors above")
        return 1

if __name__ == '__main__':
    sys.exit(main())
