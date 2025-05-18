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
from health_check import get_current_health_status
from db_manager import db_manager

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
            # Get health status using the function that checks both DB and file
            health_status = get_current_health_status()
            
            if not health_status:
                logger.error("Health status not available")
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
        next_provider = FAILOVER_ORDER.get(failed_provider, DEFAULT_PROVIDER)
        
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
                
                # Get failure reason from health status if available
                reason = None
                if failed_provider in health_status:
                    provider_status = health_status[failed_provider]
                    if 'error' in provider_status:
                        reason = provider_status['error']
                    elif 'status_code' in provider_status:
                        reason = f"Status code: {provider_status['status_code']}"
                
                if not reason:
                    reason = "Provider unavailable"
                
                # Log the failover event
                self._log_failover_event(failed_provider, next_provider, reason)
                
                return True
            
            # Try the next provider in the chain
            next_provider = FAILOVER_ORDER.get(next_provider, DEFAULT_PROVIDER)
            attempts += 1
        
        logger.error(f"Failed to find a healthy provider for failover from {failed_provider}")
        return False
    
    def _log_failover_event(self, from_provider, to_provider, reason=None, is_manual=False):
        """Log a failover event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event': 'failover',
            'from_provider': from_provider,
            'to_provider': to_provider,
            'reason': reason if reason else 'Not specified',
            'is_manual': is_manual
        }
        
        logger.info(f"Failover event: {from_provider} -> {to_provider}")
        
        # Log event to database
        db_manager.record_failover_event(
            from_provider=from_provider,
            to_provider=to_provider,
            reason=reason,
            is_manual=is_manual,
            triggered_by='system' if not is_manual else 'user'
        )
        
        # Also log event to failover log file as backup
        try:
            with open(FAILOVER_LOG_FILE, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            logger.error(f"Failed to log failover event to file: {str(e)}")
    
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
    
    def manual_failover(self, to_provider, reason="Manual failover"):
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
        self._log_failover_event(current_provider, to_provider, reason, is_manual=True)
        
        return True
    
    def get_recent_failover_events(self, limit=10):
        """Get recent failover events from database"""
        return db_manager.get_recent_failover_events(limit)

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
