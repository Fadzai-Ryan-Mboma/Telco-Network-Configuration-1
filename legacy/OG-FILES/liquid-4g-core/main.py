#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Network Optimizer - Production Startup
Multi-process startup for backend agents and UI interface
"""

import subprocess
import sys
import time
import signal
import logging
import os
from multiprocessing import Process

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('LZ-Startup')

def run_backend_agents():
    """Run the backend agent system"""
    logger.info("🤖 Starting LZ 4G backend agents...")
    try:
        subprocess.run([sys.executable, "agents.py"])
    except Exception as e:
        logger.error(f"❌ Error running backend agents: {e}")

def run_ui():
    """Run the Streamlit UI"""
    logger.info("🌐 Starting Streamlit UI on port 8501...")
    try:
        # Give backend a moment to start
        time.sleep(3)
        
        # Start Streamlit with config file
        os.system("streamlit run ui/ui.py --config ui/.streamlit/config.toml")
    except Exception as e:
        logger.error(f"❌ Error running Streamlit UI: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("🛑 Shutdown signal received, stopping all processes...")
    sys.exit(0)

def main():
    """Main container startup"""
    logger.info("🚀 Liquid Zimbabwe 4G Network Optimizer - Production Startup")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check environment
    api_url = os.getenv('LZ_API_URL', 'Not configured')
    env = os.getenv('LZ_ENV', 'development')
    
    logger.info(f"Environment: {env}")
    logger.info(f"API URL: {api_url}")
    
    try:
        # Start backend agents in separate process
        backend_process = Process(target=run_backend_agents)
        backend_process.start()
        
        # Start Streamlit UI in separate process  
        ui_process = Process(target=run_ui)
        ui_process.start()
        
        logger.info("✅ Production system started successfully!")
        logger.info("📊 Streamlit UI available at: http://localhost:8501")
        logger.info("🔧 Backend agents running in background")
        logger.info("🌍 Ready for Phase 2: Live Network Integration")
        
        # Keep main process alive
        try:
            backend_process.join()
            ui_process.join()
        except KeyboardInterrupt:
            logger.info("🛑 Keyboard interrupt received")
        finally:
            # Clean shutdown
            if backend_process.is_alive():
                backend_process.terminate()
                backend_process.join()
            
            if ui_process.is_alive():
                ui_process.terminate()
                ui_process.join()
                
            logger.info("👋 LZ 4G Optimizer stopped gracefully")
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()