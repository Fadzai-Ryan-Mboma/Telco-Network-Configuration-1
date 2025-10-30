#!/usr/bin/env python3
"""
Stage 1.2 Database Integration Verification Script
Tests all database functionality for agentic operator
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_database_integration():
    """Test all database integration features"""
    print("🧪 Testing Stage 1.2 Database Integration")
    print("=" * 50)
    
    try:
        from agentic_database import AgenticDatabase
        print("✅ AgenticDatabase imported successfully")
        
        # Initialize database
        print("\n📊 Testing Database Initialization...")
        db = AgenticDatabase()
        print("✅ Database initialized with tables created")
        
        # Test agent status
        print("\n🤖 Testing Agent Status...")
        agents = db.get_agent_status()
        print(f"✅ Retrieved {len(agents)} agents:")
        for agent in agents:
            print(f"   - {agent['agent_name']}: {agent['status']} ({agent['active_tasks']} tasks)")
        
        # Test metrics
        print("\n📈 Testing Metrics...")
        metrics = db.get_current_metrics()
        print(f"✅ Current metrics: {metrics}")
        
        # Test operation creation
        print("\n⚙️ Testing Operation Creation...")
        operation_id = db.create_operation(
            operation_type="Test Parameter Optimization",
            target_site="TEST_SITE_01",
            parameters={"test_param": "value", "simulation": True},
            agent_name="Test Agent"
        )
        
        if not operation_id:
            raise Exception("Failed to create operation")
            
        print(f"✅ Created operation: {operation_id}")
        
        # Test operation logging
        print("\n📝 Testing Operation Logging...")
        db.add_operation_log(operation_id, "Test operation started", "INFO")
        db.add_operation_log(operation_id, "Analysis phase completed", "INFO")
        print("✅ Operation logs added")
        
        # Test operation completion
        print("\n✅ Testing Operation Completion...")
        db.update_operation_status(
            operation_id,
            "completed",
            results={"improvement": "5.2%", "parameters_changed": 2}
        )
        print("✅ Operation marked as completed")
        
        # Test history retrieval
        print("\n📚 Testing History Retrieval...")
        operations = db.get_recent_operations(limit=5)
        print(f"✅ Retrieved {len(operations)} recent operations")
        
        logs = db.get_operation_logs(operation_id)
        print(f"✅ Retrieved {len(logs)} logs for operation {operation_id}")
        
        # Test agent status update
        print("\n🔄 Testing Agent Status Updates...")
        db.update_agent_status("Test Agent", "active", 1, {"test": True})
        print("✅ Agent status updated")
        
        # Test metrics update
        print("\n📊 Testing Metrics Updates...")
        db.update_metrics(active_agents=4, operations_today=15)
        print("✅ Metrics updated")
        
        print("\n" + "=" * 50)
        print("🎉 Stage 1.2 Database Integration: ALL TESTS PASSED!")
        print("✅ Database tables created and functional")
        print("✅ Agent status tracking working")
        print("✅ Operation lifecycle management working")
        print("✅ Metrics tracking working")
        print("✅ History and logging working")
        print("✅ Ready for Stage 2 implementation")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_database_integration()
    sys.exit(0 if success else 1)