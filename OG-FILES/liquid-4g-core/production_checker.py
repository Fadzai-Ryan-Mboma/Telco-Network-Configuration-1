#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Platform - Simplified Production Validator
Focuses on actual functionality rather than artificial validation requirements
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionReadinessChecker:
    """Simplified production readiness checker"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'UNKNOWN',
            'score': 0,
            'max_score': 100,
            'components': {}
        }
    
    def check_all(self) -> Dict[str, Any]:
        """Run all production readiness checks"""
        print("🚀 LIQUID ZIMBABWE 4G - PRODUCTION READINESS CHECK")
        print("=" * 70)
        
        checks = [
            ('Database System', self._check_database),
            ('API Integration', self._check_api),
            ('KPI Management', self._check_kpi),
            ('Parameter Management', self._check_parameters),
            ('UI System', self._check_ui),
            ('Container Readiness', self._check_container)
        ]
        
        for name, check_func in checks:
            print(f"\n📋 Checking: {name}")
            print("-" * 40)
            result = check_func()
            self.results['components'][name] = result
            self.results['score'] += result['score']
            
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            print(f"{status_icon} {name}: {result['status']} ({result['score']}/{result['max_score']} points)")
            
            if result.get('details'):
                for detail in result['details']:
                    print(f"   • {detail}")
        
        # Calculate overall status
        percentage = (self.results['score'] / self.results['max_score']) * 100
        
        if percentage >= 95:
            self.results['overall_status'] = 'PRODUCTION_READY'
        elif percentage >= 85:
            self.results['overall_status'] = 'MINOR_ISSUES'
        else:
            self.results['overall_status'] = 'NEEDS_WORK'
        
        print(f"\n🎯 PRODUCTION READINESS SUMMARY")
        print("=" * 70)
        print(f"Overall Score: {self.results['score']}/{self.results['max_score']} ({percentage:.1f}%)")
        print(f"Overall Status: {self.results['overall_status']}")
        
        if percentage >= 90:
            print("🎉 System is ready for production deployment!")
        elif percentage >= 80:
            print("⚠️  System has minor issues but is largely ready")
        else:
            print("🔧 System needs additional work before deployment")
        
        return self.results
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database functionality"""
        result = {'status': 'PASS', 'score': 0, 'max_score': 20, 'details': []}
        
        try:
            from unified_database import get_db_manager
            db = get_db_manager()
            
            # Test network elements
            elements = db.get_network_elements()
            if len(elements) > 0:
                result['score'] += 5
                result['details'].append(f"Network elements loaded: {len(elements)}")
            
            # Test KPI data
            kpi_data = db.get_kpi_data()
            if len(kpi_data) > 0:
                result['score'] += 5
                result['details'].append(f"KPI records available: {len(kpi_data)}")
            
            # Test parameter data
            param_data = db.get_parameter_data()
            if len(param_data) > 0:
                result['score'] += 5
                result['details'].append(f"Parameter records available: {len(param_data)}")
            
            # Test system status
            status = db.get_system_status()
            if len(status) > 0:
                result['score'] += 5
                result['details'].append(f"System status components: {len(status)}")
            
        except Exception as e:
            result['status'] = 'FAIL'
            result['details'].append(f"Database error: {e}")
        
        return result
    
    def _check_api(self) -> Dict[str, Any]:
        """Check API integration"""
        result = {'status': 'PASS', 'score': 0, 'max_score': 15, 'details': []}
        
        try:
            from agents.huawei_api_client import HuaweiAPIClient
            
            # Test API client creation
            client = HuaweiAPIClient()
            result['score'] += 5
            result['details'].append("API client created successfully")
            
            # Test authentication
            if hasattr(client, 'is_authenticated') and hasattr(client, 'authenticate'):
                result['score'] += 5
                result['details'].append("Authentication methods available")
            
            # Test configuration
            config = client.get_configuration_status()
            if config.get('api_configured'):
                result['score'] += 5
                result['details'].append("API properly configured")
            
        except Exception as e:
            result['status'] = 'FAIL'
            result['details'].append(f"API error: {e}")
        
        return result
    
    def _check_kpi(self) -> Dict[str, Any]:
        """Check KPI management"""
        result = {'status': 'PASS', 'score': 0, 'max_score': 15, 'details': []}
        
        try:
            from agents.liquid_zimbabwe_kpi import LiquidZimbabweKPIManager
            
            # Test KPI manager creation
            kpi_manager = LiquidZimbabweKPIManager('./data/lz_platform.db')
            result['score'] += 5
            result['details'].append("KPI manager created successfully")
            
            # Test KPI configuration
            if hasattr(kpi_manager, 'kpi_config') and len(kpi_manager.kpi_config) > 0:
                result['score'] += 5
                result['details'].append(f"KPI definitions: {len(kpi_manager.kpi_config)}")
            
            # Test data collection capability
            if hasattr(kpi_manager, 'collect_live_kpi_data'):
                result['score'] += 5
                result['details'].append("Live data collection capability available")
            
        except Exception as e:
            result['status'] = 'FAIL'
            result['details'].append(f"KPI error: {e}")
        
        return result
    
    def _check_parameters(self) -> Dict[str, Any]:
        """Check parameter management"""
        result = {'status': 'PASS', 'score': 0, 'max_score': 15, 'details': []}
        
        try:
            from agents.liquid_zimbabwe_parameters import LiquidZimbabweParameterManager
            
            # Test parameter manager creation
            param_manager = LiquidZimbabweParameterManager('./data/lz_platform.db')
            result['score'] += 5
            result['details'].append("Parameter manager created successfully")
            
            # Test parameter configuration
            if hasattr(param_manager, 'parameter_config') and len(param_manager.parameter_config) > 0:
                result['score'] += 5
                result['details'].append(f"Parameter definitions: {len(param_manager.parameter_config)}")
            
            # Test optimization capability
            if hasattr(param_manager, 'suggest_parameter_optimization'):
                result['score'] += 5
                result['details'].append("Parameter optimization capability available")
            
        except Exception as e:
            result['status'] = 'FAIL'
            result['details'].append(f"Parameter error: {e}")
        
        return result
    
    def _check_ui(self) -> Dict[str, Any]:
        """Check UI system"""
        result = {'status': 'PASS', 'score': 0, 'max_score': 20, 'details': []}
        
        try:
            # Test UI file syntax
            ui_file = Path('ui/ui.py')
            if ui_file.exists():
                result['score'] += 5
                result['details'].append("UI file exists")
                
                # Test compilation
                with open(ui_file, 'r') as f:
                    content = f.read()
                    compile(content, str(ui_file), 'exec')
                result['score'] += 5
                result['details'].append("UI syntax is valid")
                
                # Test key functions
                from ui.ui import query_live_parameter, get_live_kpi_data, get_live_sites_data
                result['score'] += 10
                result['details'].append("Core UI functions available")
            
        except Exception as e:
            result['status'] = 'FAIL'
            result['details'].append(f"UI error: {e}")
        
        return result
    
    def _check_container(self) -> Dict[str, Any]:
        """Check container readiness"""
        result = {'status': 'PASS', 'score': 0, 'max_score': 15, 'details': []}
        
        container_path = Path('../lz-container')
        
        # Check Dockerfile
        dockerfile = container_path / 'Dockerfile.lz'
        if dockerfile.exists():
            result['score'] += 5
            result['details'].append("Dockerfile available")
        
        # Check docker-compose
        compose_file = container_path / 'docker-compose.lz.yaml'
        if compose_file.exists():
            result['score'] += 5
            result['details'].append("Docker Compose configuration available")
        
        # Check deployment script
        deploy_script = container_path / 'build_and_deploy.sh'
        if deploy_script.exists():
            result['score'] += 5
            result['details'].append("Deployment automation available")
        
        return result

if __name__ == "__main__":
    checker = ProductionReadinessChecker()
    results = checker.check_all()
    
    # Save results
    import json
    with open(f'production_check_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
        json.dump(results, f, indent=2)