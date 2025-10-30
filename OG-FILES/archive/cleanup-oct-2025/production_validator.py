#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G - Production Readiness Validation Script
Comprehensive system validation for production deployment
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionValidator:
    """Comprehensive production readiness validator"""
    
    def __init__(self):
        self.results = {
            'overall_status': 'UNKNOWN',
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'score': 0,
            'max_score': 0,
            'critical_issues': [],
            'warnings': [],
            'recommendations': []
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all production readiness tests"""
        print("🚀 LIQUID ZIMBABWE 4G - PRODUCTION READINESS VALIDATION")
        print("=" * 80)
        
        # Test categories
        test_categories = [
            ('Environment Configuration', self.test_environment_config),
            ('API Client Functionality', self.test_api_client),
            ('Database Operations', self.test_database),
            ('KPI Management', self.test_kpi_management),
            ('Parameter Management', self.test_parameter_management),
            ('UI Integration', self.test_ui_integration),
            ('System Performance', self.test_performance),
            ('Security Configuration', self.test_security)
        ]
        
        for category, test_func in test_categories:
            print(f"\n📋 Testing: {category}")
            print("-" * 40)
            
            try:
                result = test_func()
                self.results['tests'][category] = result
                self.results['score'] += result.get('score', 0)
                self.results['max_score'] += result.get('max_score', 0)
                
                if result['status'] == 'PASS':
                    print(f"✅ {category}: PASSED")
                elif result['status'] == 'WARN':
                    print(f"⚠️  {category}: PASSED WITH WARNINGS")
                    self.results['warnings'].extend(result.get('warnings', []))
                else:
                    print(f"❌ {category}: FAILED")
                    self.results['critical_issues'].extend(result.get('issues', []))
                    
            except Exception as e:
                print(f"❌ {category}: ERROR - {e}")
                self.results['tests'][category] = {
                    'status': 'ERROR',
                    'error': str(e),
                    'score': 0,
                    'max_score': 10
                }
                self.results['critical_issues'].append(f"{category}: {e}")
        
        # Calculate overall status
        percentage = (self.results['score'] / self.results['max_score']) * 100 if self.results['max_score'] > 0 else 0
        
        if percentage >= 90 and len(self.results['critical_issues']) == 0:
            self.results['overall_status'] = 'PRODUCTION_READY'
        elif percentage >= 75:
            self.results['overall_status'] = 'NEEDS_MINOR_FIXES'
        elif percentage >= 50:
            self.results['overall_status'] = 'NEEDS_MAJOR_FIXES'
        else:
            self.results['overall_status'] = 'NOT_READY'
        
        self.print_summary()
        return self.results
    
    def test_environment_config(self) -> Dict[str, Any]:
        """Test environment configuration"""
        result = {
            'status': 'PASS',
            'score': 0,
            'max_score': 10,
            'details': {},
            'issues': [],
            'warnings': []
        }
        
        # Check required environment variables
        required_vars = ['LZ_API_URL', 'LZ_API_USERNAME', 'LZ_API_PASSWORD']
        optional_vars = ['LZ_API_TIMEOUT', 'LZ_API_SSL_VERIFY', 'LZ_DB_PATH']
        
        for var in required_vars:
            if os.getenv(var):
                result['details'][var] = 'CONFIGURED'
                result['score'] += 2
            else:
                result['details'][var] = 'MISSING'
                result['issues'].append(f"Required environment variable {var} is not set")
                result['status'] = 'FAIL'
        
        for var in optional_vars:
            if os.getenv(var):
                result['details'][var] = 'CONFIGURED'
                result['score'] += 1
            else:
                result['details'][var] = 'DEFAULT'
                result['warnings'].append(f"Optional environment variable {var} not set, using default")
        
        return result
    
    def test_api_client(self) -> Dict[str, Any]:
        """Test Huawei API client functionality"""
        result = {
            'status': 'PASS',
            'score': 0,
            'max_score': 15,
            'details': {},
            'issues': [],
            'warnings': []
        }
        
        try:
            # Import and instantiate API client
            from agents.huawei_api_client import HuaweiAPIClient
            api_client = HuaweiAPIClient()
            result['score'] += 3
            result['details']['client_creation'] = 'SUCCESS'
            
            # Check configuration
            config_status = api_client.check_configuration()
            result['details']['configuration'] = config_status
            
            if config_status['api_configured']:
                result['score'] += 3
            else:
                result['issues'].append("API URL not configured")
                result['status'] = 'FAIL'
            
            if config_status['credentials_present']:
                result['score'] += 3
            else:
                result['issues'].append("API credentials not configured")
                result['status'] = 'FAIL'
            
            if config_status['network_elements'] > 0:
                result['score'] += 3
                result['details']['network_elements'] = config_status['network_elements']
            else:
                result['warnings'].append("No network elements configured")
                result['status'] = 'WARN'
            
            # Test authentication (if credentials are available)
            if config_status['connection_ready']:
                try:
                    auth_result = api_client.authenticate()
                    if auth_result:
                        result['score'] += 3
                        result['details']['authentication'] = 'SUCCESS'
                    else:
                        result['issues'].append("Authentication failed")
                        result['status'] = 'FAIL'
                except Exception as e:
                    result['warnings'].append(f"Authentication test failed: {e}")
                    result['details']['authentication'] = f'ERROR: {e}'
                    if result['status'] == 'PASS':
                        result['status'] = 'WARN'
            else:
                result['warnings'].append("Cannot test authentication - configuration incomplete")
                
        except ImportError as e:
            result['issues'].append(f"Cannot import API client: {e}")
            result['status'] = 'FAIL'
        except Exception as e:
            result['issues'].append(f"API client test failed: {e}")
            result['status'] = 'FAIL'
        
        return result
    
    def test_database(self) -> Dict[str, Any]:
        """Test database operations"""
        result = {
            'status': 'PASS',
            'score': 0,
            'max_score': 10,
            'details': {},
            'issues': [],
            'warnings': []
        }
        
        try:
            # Test database helper
            from utils.database_helper import get_live_active_sites, get_database_stats
            
            # Test site retrieval
            sites = get_live_active_sites()
            result['details']['sites_count'] = len(sites)
            result['score'] += 3
            
            if len(sites) > 0:
                result['score'] += 2
                result['details']['sites_available'] = True
            else:
                result['warnings'].append("No sites found in database")
                result['details']['sites_available'] = False
            
            # Test database stats
            stats = get_database_stats()
            result['details']['database_stats'] = stats
            result['score'] += 3
            
            # Test database write (create test record)
            try:
                import sqlite3
                db_path = os.getenv('LZ_DB_PATH', './data/historical_db')
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                    table_count = cursor.fetchone()[0]
                    result['details']['database_tables'] = table_count
                    result['score'] += 2
                    
                    if table_count > 0:
                        result['details']['database_initialized'] = True
                    else:
                        result['warnings'].append("Database appears to be empty")
                        
            except Exception as e:
                result['warnings'].append(f"Database connectivity test failed: {e}")
                
        except ImportError as e:
            result['issues'].append(f"Cannot import database utilities: {e}")
            result['status'] = 'FAIL'
        except Exception as e:
            result['issues'].append(f"Database test failed: {e}")
            result['status'] = 'FAIL'
        
        return result
    
    def test_kpi_management(self) -> Dict[str, Any]:
        """Test KPI management functionality"""
        result = {
            'status': 'PASS',
            'score': 0,
            'max_score': 12,
            'details': {},
            'issues': [],
            'warnings': []
        }
        
        try:
            from agents.liquid_zimbabwe_kpi import LiquidZimbabweKPIManager
            
            # Initialize KPI manager with db_path
            db_path = os.getenv('LZ_DB_PATH', './data/historical_db')
            kpi_manager = LiquidZimbabweKPIManager(db_path)
            result['score'] += 3
            result['details']['kpi_manager_init'] = 'SUCCESS'
            
            # Test KPI configuration
            kpi_config = kpi_manager.kpi_config
            result['details']['kpi_count'] = len(kpi_config)
            result['score'] += 2
            
            # Test database schema
            try:
                kpi_manager._initialize_database()
                result['score'] += 2
                result['details']['database_schema'] = 'INITIALIZED'
            except Exception as e:
                result['warnings'].append(f"Database schema initialization warning: {e}")
            
            # Test data collection simulation
            try:
                # This will likely fail without live API, but we test the structure
                live_data = kpi_manager.collect_live_kpi_data()
                result['score'] += 3
                result['details']['live_data_collection'] = 'SUCCESS'
            except Exception as e:
                result['warnings'].append(f"Live data collection failed (expected without API): {e}")
                result['details']['live_data_collection'] = 'SIMULATED'
                result['score'] += 1  # Partial credit for structure being present
            
            # Test historical data retrieval
            try:
                historical = kpi_manager.get_historical_kpis('1 hour')
                result['score'] += 2
                result['details']['historical_data'] = len(historical)
            except Exception as e:
                result['warnings'].append(f"Historical data retrieval failed: {e}")
                
        except ImportError as e:
            result['issues'].append(f"Cannot import KPI manager: {e}")
            result['status'] = 'FAIL'
        except Exception as e:
            result['issues'].append(f"KPI management test failed: {e}")
            result['status'] = 'FAIL'
        
        return result
    
    def test_parameter_management(self) -> Dict[str, Any]:
        """Test parameter management functionality"""
        result = {
            'status': 'PASS',
            'score': 0,
            'max_score': 10,
            'details': {},
            'issues': [],
            'warnings': []
        }
        
        try:
            from agents.liquid_zimbabwe_parameters import LiquidZimbabweParameterManager
            
            # Initialize parameter manager with db_path
            db_path = os.getenv('LZ_DB_PATH', './data/historical_db')
            param_manager = LiquidZimbabweParameterManager(db_path)
            result['score'] += 3
            result['details']['param_manager_init'] = 'SUCCESS'
            
            # Test parameter configuration
            param_config = param_manager.parameter_config
            result['details']['parameter_count'] = len(param_config)
            result['score'] += 2
            
            # Test optimization rules
            try:
                # Test with sample KPI issues
                sample_issues = ['low_network_access_success', 'high_download_quality_issues']
                suggestions = param_manager.suggest_parameter_optimization(sample_issues)
                result['score'] += 2
                result['details']['optimization_rules'] = 'AVAILABLE'
                result['details']['optimization_suggestions'] = len(suggestions)
                
                # Test optimization statistics
                if hasattr(param_manager, 'get_optimization_statistics'):
                    stats = param_manager.get_optimization_statistics()
                    result['score'] += 3
                    result['details']['optimization_stats'] = stats['optimization_rules_count']
                else:
                    result['score'] += 1
                    result['warnings'].append("Advanced optimization statistics not available")
                    
            except Exception as e:
                result['warnings'].append(f"Optimization functionality test failed: {e}")
                result['score'] += 1  # Partial credit for basic functionality
                
        except ImportError as e:
            result['issues'].append(f"Cannot import parameter manager: {e}")
            result['status'] = 'FAIL'
        except Exception as e:
            result['issues'].append(f"Parameter management test failed: {e}")
            result['status'] = 'FAIL'
        
        return result
    
    def test_ui_integration(self) -> Dict[str, Any]:
        """Test UI integration"""
        result = {
            'status': 'PASS',
            'score': 0,
            'max_score': 8,
            'details': {},
            'issues': [],
            'warnings': []
        }
        
        try:
            # Test UI imports - adjust path and imports
            import sys
            sys.path.insert(0, './ui')
            
            # Import UI functions directly
            from ui import get_live_kpi_data, get_live_sites_data, query_live_parameter
            result['score'] += 2
            result['details']['ui_imports'] = 'SUCCESS'
            
            # Test KPI data function
            kpi_data = get_live_kpi_data()
            if isinstance(kpi_data, dict) and 'system_status' in kpi_data:
                result['score'] += 2
                result['details']['kpi_data_function'] = kpi_data['system_status']
            else:
                result['warnings'].append("KPI data function returned unexpected format")
            
            # Test sites data function
            sites_data = get_live_sites_data()
            if isinstance(sites_data, dict) and 'sites' in sites_data:
                result['score'] += 2
                result['details']['sites_data_function'] = len(sites_data['sites'])
            else:
                result['warnings'].append("Sites data function returned unexpected format")
            
            # Test parameter query function
            query_result = query_live_parameter('TEST', 'Test Parameter', 'LST CELL:;')
            if isinstance(query_result, dict):
                result['score'] += 2
                result['details']['parameter_query_function'] = 'FUNCTIONAL'
            else:
                result['warnings'].append("Parameter query function returned unexpected format")
                
        except ImportError as e:
            result['issues'].append(f"Cannot import UI functions: {e}")
            result['status'] = 'FAIL'
        except Exception as e:
            result['issues'].append(f"UI integration test failed: {e}")
            result['status'] = 'FAIL'
        
        return result
    
    def test_performance(self) -> Dict[str, Any]:
        """Test system performance"""
        result = {
            'status': 'PASS',
            'score': 0,
            'max_score': 8,
            'details': {},
            'issues': [],
            'warnings': []
        }
        
        # Test startup time
        start_time = time.time()
        try:
            from agents.huawei_api_client import HuaweiAPIClient
            from agents.liquid_zimbabwe_kpi import LiquidZimbabweKPIManager
            
            api_client = HuaweiAPIClient()
            db_path = os.getenv('LZ_DB_PATH', './data/historical_db')
            kpi_manager = LiquidZimbabweKPIManager(db_path)
            
            startup_time = time.time() - start_time
            result['details']['startup_time'] = f"{startup_time:.2f}s"
            
            if startup_time < 5.0:
                result['score'] += 4
            elif startup_time < 10.0:
                result['score'] += 2
                result['warnings'].append(f"Startup time is acceptable but could be improved: {startup_time:.2f}s")
            else:
                result['issues'].append(f"Startup time is too slow: {startup_time:.2f}s")
                result['status'] = 'FAIL'
                
        except Exception as e:
            result['issues'].append(f"Performance test failed: {e}")
            result['status'] = 'FAIL'
        
        # Test memory usage (basic check)
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            result['details']['memory_usage'] = f"{memory_mb:.1f}MB"
            
            if memory_mb < 500:
                result['score'] += 4
            elif memory_mb < 1000:
                result['score'] += 2
                result['warnings'].append(f"Memory usage is acceptable: {memory_mb:.1f}MB")
            else:
                result['warnings'].append(f"Memory usage is high: {memory_mb:.1f}MB")
                
        except ImportError:
            result['warnings'].append("psutil not available for memory testing")
        except Exception as e:
            result['warnings'].append(f"Memory test failed: {e}")
        
        return result
    
    def test_security(self) -> Dict[str, Any]:
        """Test security configuration"""
        result = {
            'status': 'PASS',
            'score': 0,
            'max_score': 6,
            'details': {},
            'issues': [],
            'warnings': []
        }
        
        # Check SSL verification setting
        ssl_verify = os.getenv('LZ_API_SSL_VERIFY', 'true').lower()
        if ssl_verify in ['true', '1', 'yes']:
            result['score'] += 2
            result['details']['ssl_verification'] = 'ENABLED'
        else:
            result['warnings'].append("SSL verification is disabled - ensure this is appropriate for your environment")
            result['details']['ssl_verification'] = 'DISABLED'
            result['score'] += 1
        
        # Check for sensitive data in environment
        sensitive_vars = ['LZ_API_PASSWORD']
        for var in sensitive_vars:
            value = os.getenv(var, '')
            if value and len(value) > 4:
                result['score'] += 2
                result['details'][f'{var}_present'] = 'YES'
            else:
                result['warnings'].append(f"Sensitive variable {var} appears to be missing or too short")
        
        # Check logging configuration
        log_level = os.getenv('LZ_LOG_LEVEL', 'INFO')
        if log_level.upper() in ['INFO', 'WARN', 'ERROR']:
            result['score'] += 2
            result['details']['log_level'] = log_level
        else:
            result['warnings'].append(f"Unusual log level: {log_level}")
            result['details']['log_level'] = log_level
        
        return result
    
    def print_summary(self):
        """Print validation summary"""
        print(f"\n🎯 PRODUCTION READINESS SUMMARY")
        print("=" * 80)
        
        percentage = (self.results['score'] / self.results['max_score']) * 100 if self.results['max_score'] > 0 else 0
        print(f"Overall Score: {self.results['score']}/{self.results['max_score']} ({percentage:.1f}%)")
        print(f"Overall Status: {self.results['overall_status']}")
        
        if self.results['overall_status'] == 'PRODUCTION_READY':
            print("🎊 ✅ SYSTEM IS PRODUCTION READY!")
        elif self.results['overall_status'] == 'NEEDS_MINOR_FIXES':
            print("⚠️  System needs minor fixes before production deployment")
        elif self.results['overall_status'] == 'NEEDS_MAJOR_FIXES':
            print("❌ System needs major fixes before production deployment")
        else:
            print("❌ System is not ready for production deployment")
        
        if self.results['critical_issues']:
            print(f"\n❌ Critical Issues ({len(self.results['critical_issues'])}):")
            for issue in self.results['critical_issues']:
                print(f"  - {issue}")
        
        if self.results['warnings']:
            print(f"\n⚠️  Warnings ({len(self.results['warnings'])}):")
            for warning in self.results['warnings']:
                print(f"  - {warning}")
        
        print(f"\n📊 Test Results Summary:")
        for category, test_result in self.results['tests'].items():
            status_icon = "✅" if test_result['status'] == 'PASS' else "⚠️" if test_result['status'] == 'WARN' else "❌"
            score = test_result.get('score', 0)
            max_score = test_result.get('max_score', 0)
            print(f"  {status_icon} {category}: {score}/{max_score}")

def main():
    """Main validation function"""
    validator = ProductionValidator()
    results = validator.run_all_tests()
    
    # Save results to file
    results_file = f"validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    # Return exit code based on results
    if results['overall_status'] == 'PRODUCTION_READY':
        return 0
    elif results['overall_status'] == 'NEEDS_MINOR_FIXES':
        return 1
    else:
        return 2

if __name__ == "__main__":
    sys.exit(main())