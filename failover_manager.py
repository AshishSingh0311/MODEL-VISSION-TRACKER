import json
import logging
import os
import threading
import time
from datetime import datetime

from config import (
    FAILOVER_ORDER, 
    ACTIVE_PROVIDER_FILE, 
    DEFAULT_PROVIDER,
    FAILOVER_LOG_FILE,
    HEALTH_STATUS_FILE
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(FAILOVER_LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('failover_manager')

class FailoverManager:
    def __init__(self):
        """Initialize the failover manager"""
        # Make sure directory for active provider file exists
        os.makedirs(os.path.dirname(ACTIVE_PROVIDER_FILE), exist_ok=True)
        
        # Initialize active provider file if it doesn't exist
        if not os.path.exists(ACTIVE_PROVIDER_FILE):
            self._save_active_provider(DEFAULT_PROVIDER)
        
        self.active_provider = self._load_active_provider()
        
    def _load_active_provider(self):
        """Load the active provider from file"""
        try:
            if os.path.exists(ACTIVE_PROVIDER_FILE):
                with open(ACTIVE_PROVIDER_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('active_provider', DEFAULT_PROVIDER)
            return DEFAULT_PROVIDER
        except Exception as e:
            logger.error(f"Failed to load active provider: {str(e)}")
            return DEFAULT_PROVIDER
    
    def _save_active_provider(self, provider):
        """Save the active provider to file"""
        try:
            with open(ACTIVE_PROVIDER_FILE, 'w') as f:
                json.dump({
                    'active_provider': provider,
                    'updated_at': datetime.now().isoformat()
                }, f)
        except Exception as e:
            logger.error(f"Failed to save active provider: {str(e)}")
    
    def check_and_failover(self):
        """Check health status and initiate failover if needed"""
        try:
            if os.path.exists(HEALTH_STATUS_FILE):
                with open(HEALTH_STATUS_FILE, 'r') as f:
                    health_status = json.load(f)
            else:
                logger.error("Health status file not found")
                return False
                
            # Get current active provider
            current_provider = self._load_active_provider()
            
            # Check if current provider is healthy
            if current_provider in health_status:
                current_provider_healthy = health_status[current_provider].get('status', False)
                
                if not current_provider_healthy:
                    # Initiate failover
                    self._perform_failover(current_provider, health_status)
                    return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error in check_and_failover: {str(e)}")
            return False
    
    def _perform_failover(self, failed_provider, health_status):
        """Perform failover to next available provider"""
        # Determine next provider in failover order
        next_provider = FAILOVER_ORDER.get(failed_provider)
        
        # Find a healthy provider
        attempts = 0
        max_attempts = len(FAILOVER_ORDER)
        
        while attempts < max_attempts:
            if next_provider in health_status and health_status[next_provider].get('status', False):
                # Found a healthy provider
                logger.info(f"Initiating failover from {failed_provider} to {next_provider}")
                
                # Update active provider
                self.active_provider = next_provider
                self._save_active_provider(next_provider)
                
                # Log the failover event
                self._log_failover_event(failed_provider, next_provider)
                
                return True
            
            # Try the next provider in the chain
            next_provider = FAILOVER_ORDER.get(next_provider)
            attempts += 1
        
        logger.error(f"Failed to find a healthy provider for failover from {failed_provider}")
        return False
    
    def _log_failover_event(self, from_provider, to_provider):
        """Log a failover event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event': 'failover',
            'from_provider': from_provider,
            'to_provider': to_provider
        }
        
        logger.info(f"Failover event: {from_provider} -> {to_provider}")
        
        # Log event to failover log file
        try:
            with open(FAILOVER_LOG_FILE, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            logger.error(f"Failed to log failover event: {str(e)}")
    
    def run_failover_check_thread(self, interval=10):
        """Run failover checks in a loop at specified intervals"""
        while True:
            self.check_and_failover()
            time.sleep(interval)
    
    def start_monitoring(self, interval=10):
        """Start failover monitoring in a background thread"""
        failover_thread = threading.Thread(
            target=self.run_failover_check_thread,
            args=(interval,),
            daemon=True
        )
        failover_thread.start()
        logger.info(f"Failover monitoring started in background thread (interval: {interval}s)")
        return failover_thread
    
    def manual_failover(self, to_provider):
        """Manually trigger failover to specified provider"""
        current_provider = self._load_active_provider()
        
        if current_provider == to_provider:
            logger.info(f"Provider {to_provider} is already active. No failover needed.")
            return False
        
        logger.info(f"Manual failover initiated from {current_provider} to {to_provider}")
        
        # Update active provider
        self.active_provider = to_provider
        self._save_active_provider(to_provider)
        
        # Log the manual failover event
        self._log_failover_event(current_provider, to_provider)
        
        return True

def get_active_provider():
    """Get the current active provider"""
    try:
        if os.path.exists(ACTIVE_PROVIDER_FILE):
            with open(ACTIVE_PROVIDER_FILE, 'r') as f:
                data = json.load(f)
                return data.get('active_provider', DEFAULT_PROVIDER)
        return DEFAULT_PROVIDER
    except Exception as e:
        logger.error(f"Failed to get active provider: {str(e)}")
        return DEFAULT_PROVIDER

if __name__ == "__main__":
    # When run directly, start failover monitoring
    manager = FailoverManager()
    manager.start_monitoring()
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Failover monitoring stopped")
