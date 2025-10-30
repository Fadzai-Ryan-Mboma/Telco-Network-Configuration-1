#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Network Optimizer - Container Startup with UI
Runs both backend agents and Streamlit UI for testing
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
logger = logging.getLogger('LZ-Container-Startup')

def run_backend_agents():
    """Run the backend agent system"""
    logger.info("🤖 Starting LZ 4G backend agents...")
    try:
        # Simple subprocess approach
        subprocess.run([sys.executable, "agents_lz_test.py"])
    except Exception as e:
        logger.error(f"❌ Error running backend agents: {e}")

def run_streamlit_ui():
    """Run the Streamlit UI"""
    logger.info("🌐 Starting Streamlit UI on port 8501...")
    try:
        # Give backend a moment to start
        time.sleep(5)
        
        # Start Streamlit
        os.system("streamlit run lz_ui_test.py --server.port 8501 --server.address 0.0.0.0 --server.headless true")
    except Exception as e:
        logger.error(f"❌ Error running Streamlit UI: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("🛑 Shutdown signal received, stopping all processes...")
    sys.exit(0)

def main():
    """Main container startup"""
    logger.info("🚀 Liquid Zimbabwe 4G Network Optimizer - Container Starting...")
    
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
        ui_process = Process(target=run_streamlit_ui)
        ui_process.start()
        
        logger.info("✅ Both backend and UI processes started!")
        logger.info("📊 Streamlit UI available at: http://localhost:8501")
        logger.info("🔧 Backend agents running in background")
        
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
                
            logger.info("👋 LZ 4G Optimizer stopped")
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()