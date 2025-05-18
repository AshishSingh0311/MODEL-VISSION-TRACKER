import json
import logging
import os
import requests
import threading
import time
from datetime import datetime
from pathlib import Path

from config import CLOUD_ENDPOINTS, HEALTH_CHECK_INTERVAL, HEALTH_STATUS_FILE
from db_manager import db_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/health_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('health_check')

class HealthChecker:
    def __init__(self):
        """Initialize the health checker with default values"""
        self.endpoints = CLOUD_ENDPOINTS
        self.status = {provider: {"status": True, "last_checked": datetime.now().isoformat()} 
                      for provider in self.endpoints.keys()}
        self.timeout = 5  # seconds
        
        # Create directory for health status file if it doesn't exist
        os.makedirs(os.path.dirname(HEALTH_STATUS_FILE), exist_ok=True)
        
        # Initialize health status file if it doesn't exist
        if not os.path.exists(HEALTH_STATUS_FILE):
            with open(HEALTH_STATUS_FILE, 'w') as f:
                json.dump(self.status, f)

    def check_health(self):
        """Check the health of all cloud providers"""
        for provider, endpoint in self.endpoints.items():
            try:
                # Perform health check
                response = requests.get(endpoint, timeout=self.timeout)
                
                # Update status based on response
                if response.status_code == 200:
                    status_info = {
                        "status": True, 
                        "last_checked": datetime.now().isoformat(),
                        "response_time": response.elapsed.total_seconds()
                    }
                    self.status[provider] = status_info
                    logger.info(f"{provider.upper()} health check: OK")
                    
                    # Record health check in database
                    db_manager.record_health_check(
                        provider_name=provider,
                        status=True,
                        response_time=response.elapsed.total_seconds()
                    )
                else:
                    status_info = {
                        "status": False,
                        "last_checked": datetime.now().isoformat(),
                        "response_time": response.elapsed.total_seconds(),
                        "status_code": response.status_code
                    }
                    self.status[provider] = status_info
                    logger.warning(f"{provider.upper()} health check failed with status code: {response.status_code}")
                    
                    # Record health check in database
                    db_manager.record_health_check(
                        provider_name=provider,
                        status=False,
                        response_time=response.elapsed.total_seconds(),
                        status_code=response.status_code
                    )
            
            except requests.exceptions.RequestException as e:
                # Handle request exceptions (timeout, connection error, etc.)
                status_info = {
                    "status": False,
                    "last_checked": datetime.now().isoformat(),
                    "error": str(e)
                }
                self.status[provider] = status_info
                logger.error(f"{provider.upper()} health check error: {str(e)}")
                
                # Record health check in database
                db_manager.record_health_check(
                    provider_name=provider,
                    status=False,
                    error_message=str(e)
                )
        
        # Save status to file
        self._save_status()
        
    def _save_status(self):
        """Save the current health status to a JSON file"""
        try:
            with open(HEALTH_STATUS_FILE, 'w') as f:
                json.dump(self.status, f)
        except Exception as e:
            logger.error(f"Failed to save health status: {str(e)}")

    def run_health_check_thread(self):
        """Run health checks in a loop at specified intervals"""
        while True:
            self.check_health()
            time.sleep(HEALTH_CHECK_INTERVAL)
            
    def start_monitoring(self):
        """Start health monitoring in a background thread"""
        health_thread = threading.Thread(target=self.run_health_check_thread, daemon=True)
        health_thread.start()
        logger.info("Health monitoring started in background thread")
        return health_thread

def get_current_health_status():
    """Get the current health status"""
    try:
        # Try to get health status from database first
        db_status = db_manager.get_health_status()
        if db_status:
            return db_status
        
        # Fall back to file if database fails
        if os.path.exists(HEALTH_STATUS_FILE):
            with open(HEALTH_STATUS_FILE, 'r') as f:
                return json.load(f)
        
        return {}
    except Exception as e:
        logger.error(f"Failed to read health status: {str(e)}")
        return {}

if __name__ == "__main__":
    # When run directly, start health monitoring
    checker = HealthChecker()
    checker.start_monitoring()
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Health check monitoring stopped")
