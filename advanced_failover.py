import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta
import random

from config import (
    FAILOVER_ORDER, 
    ACTIVE_PROVIDER_FILE, 
    DEFAULT_PROVIDER,
    FAILOVER_LOG_FILE,
    HEALTH_STATUS_FILE,
    CLOUD_PROVIDERS
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
logger = logging.getLogger('advanced_failover')

class AdvancedFailoverManager:
    """Advanced failover manager with more sophisticated decision logic"""
    
    def __init__(self):
        """Initialize the advanced failover manager"""
        # Make sure directory for active provider file exists
        os.makedirs(os.path.dirname(ACTIVE_PROVIDER_FILE), exist_ok=True)
        
        # Initialize active provider file if it doesn't exist
        if not os.path.exists(ACTIVE_PROVIDER_FILE):
            self._save_active_provider(DEFAULT_PROVIDER)
        
        self.active_provider = self._load_active_provider()
        
        # Track health status history for better decision making
        self.health_history = {provider: [] for provider in CLOUD_PROVIDERS.keys()}
        
        # Configure provider weights for decision making
        self.provider_weights = {
            "aws": {
                "reliability": 0.6,
                "performance": 0.7,
                "cost": 0.5
            },
            "azure": {
                "reliability": 0.5,
                "performance": 0.6,
                "cost": 0.6
            },
            "gcp": {
                "reliability": 0.55,
                "performance": 0.5,
                "cost": 0.7
            }
        }
        
        # Failover thresholds
        self.consecutive_failures_threshold = 3  # Number of consecutive failures before failover
        self.recovery_time_threshold = 60  # Seconds to wait before failing back
        self.performance_degradation_threshold = 0.5  # Performance drop ratio triggering failover
        
        # Metrics for advanced decisions
        self.last_failover_time = {provider: None for provider in CLOUD_PROVIDERS.keys()}
        
        # Load performance metrics for decision making
        from performance_monitor import get_performance_data
        self.current_performance = get_performance_data()
        
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
    
    def update_health_history(self, health_status):
        """Update the health history with current status"""
        current_time = datetime.now()
        
        for provider, status in health_status.items():
            # Add to history with timestamp
            is_healthy = status.get('status', False)
            response_time = status.get('response_time', None)
            
            self.health_history[provider].append({
                'timestamp': current_time,
                'healthy': is_healthy,
                'response_time': response_time
            })
            
            # Keep only the last 10 status checks
            if len(self.health_history[provider]) > 10:
                self.health_history[provider] = self.health_history[provider][-10:]
    
    def count_consecutive_failures(self, provider):
        """Count the number of consecutive failures for a provider"""
        if not self.health_history.get(provider):
            return 0
            
        consecutive_failures = 0
        
        # Count failures starting from the latest entry
        for status in reversed(self.health_history[provider]):
            if not status['healthy']:
                consecutive_failures += 1
            else:
                break  # Stop counting when we find a healthy status
        
        return consecutive_failures
    
    def calculate_provider_score(self, provider, health_status):
        """Calculate a score for each provider based on multiple factors"""
        # Base score starts at 0
        score = 0
        
        # 1. Current health status (most important)
        is_healthy = provider in health_status and health_status[provider].get('status', False)
        if is_healthy:
            score += 50  # Big boost for being currently healthy
        else:
            return 0  # Immediately disqualify unhealthy providers
        
        # 2. Recent health history (reliability)
        if provider in self.health_history and self.health_history[provider]:
            history = self.health_history[provider]
            recent_health_ratio = sum(1 for status in history if status['healthy']) / len(history)
            score += 20 * recent_health_ratio * self.provider_weights[provider]['reliability']
        
        # 3. Performance metrics
        if provider in self.current_performance:
            perf = self.current_performance[provider]
            
            # Response time (lower is better)
            response_time = perf.get('average_response_time', 0.5)
            response_score = max(0, 10 - (response_time * 10))  # 0-10 points
            
            # Success rate (higher is better)
            success_rate = perf.get('request_success_rate', 95) / 100  # As ratio
            success_score = success_rate * 10  # 0-10 points
            
            performance_score = (response_score + success_score) * self.provider_weights[provider]['performance']
            score += performance_score
        
        # 4. Failover timing - avoid too frequent failovers to the same provider
        if provider in self.last_failover_time and self.last_failover_time[provider] is not None:
            time_since_last_failover = (datetime.now() - self.last_failover_time[provider]).total_seconds()
            if time_since_last_failover < self.recovery_time_threshold:
                # Reduce score if we recently failed over from this provider
                score -= 15
        
        # 5. Cost factors
        if provider in CLOUD_PROVIDERS:
            # Lower cost gets higher score
            # Normalized to 0-10 range across providers
            provider_info = CLOUD_PROVIDERS[provider]
            # Find max and min costs across all providers
            all_costs = [p['cost_per_hour'] for p in CLOUD_PROVIDERS.values()]
            max_cost = max(all_costs)
            min_cost = min(all_costs)
            
            # Calculate normalized cost score (lower cost = higher score)
            if max_cost > min_cost:  # Avoid division by zero
                cost_score = 10 * (1 - (provider_info['cost_per_hour'] - min_cost) / (max_cost - min_cost))
            else:
                cost_score = 5  # Equal costs
                
            score += cost_score * self.provider_weights[provider]['cost']
        
        logger.debug(f"Provider {provider} score: {score}")
        return score
    
    def select_best_provider(self, health_status, exclude_providers=None):
        """Select the best provider based on multiple factors"""
        if exclude_providers is None:
            exclude_providers = []
        
        # Calculate scores for each provider
        scores = {}
        for provider in CLOUD_PROVIDERS.keys():
            if provider not in exclude_providers:
                scores[provider] = self.calculate_provider_score(provider, health_status)
        
        # Find provider with highest score
        best_provider = None
        best_score = -1
        
        for provider, score in scores.items():
            if score > best_score:
                best_score = score
                best_provider = provider
        
        if best_provider:
            logger.info(f"Selected best provider: {best_provider} (score: {best_score})")
        else:
            logger.warning("No suitable provider found, using default")
            best_provider = DEFAULT_PROVIDER
            
        return best_provider
        
    def check_and_failover(self):
        """Check health status and initiate failover if needed using advanced logic"""
        try:
            # Get health status
            health_status = get_current_health_status()
            
            if not health_status:
                logger.error("Health status not available")
                return False
            
            # Update health history
            self.update_health_history(health_status)
            
            # Get current active provider
            current_provider = self._load_active_provider()
            
            # Check if current provider needs failover
            needs_failover = False
            failover_reason = None
            
            # Case 1: Current provider is unhealthy
            if current_provider in health_status:
                current_provider_healthy = health_status[current_provider].get('status', False)
                
                if not current_provider_healthy:
                    # Check for multiple consecutive failures for increased reliability
                    consecutive_failures = self.count_consecutive_failures(current_provider)
                    
                    if consecutive_failures >= self.consecutive_failures_threshold:
                        needs_failover = True
                        failover_reason = f"Provider unhealthy for {consecutive_failures} consecutive checks"
            
            # Case 2: Significant performance degradation
            if not needs_failover and current_provider in self.current_performance:
                # Check performance degradation
                if self.detect_performance_degradation(current_provider):
                    needs_failover = True
                    failover_reason = "Significant performance degradation detected"
            
            # Case 3: Better provider available for a long time
            if not needs_failover:
                better_provider = self.check_for_better_provider(current_provider, health_status)
                if better_provider:
                    needs_failover = True
                    failover_reason = f"Better performing provider ({better_provider}) available"
                    
            if needs_failover:
                # Initiate failover to best available provider
                self._perform_advanced_failover(current_provider, health_status, failover_reason)
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error in check_and_failover: {str(e)}")
            return False
    
    def detect_performance_degradation(self, provider):
        """Detect significant performance degradation for a provider"""
        # Get performance data
        if provider not in self.current_performance:
            return False
            
        current_perf = self.current_performance[provider]
        
        # Check for high response time
        response_time = current_perf.get('average_response_time', 0)
        if response_time > 0.5:  # More than 500ms response time
            return True
            
        # Check for low success rate
        success_rate = current_perf.get('request_success_rate', 100)
        if success_rate < 95:  # Less than 95% success rate
            return True
            
        # Check for high resource utilization
        cpu_util = current_perf.get('cpu_utilization', 0)
        memory_util = current_perf.get('memory_utilization', 0)
        
        if cpu_util > 85 and memory_util > 80:  # High resource usage
            return True
            
        return False
    
    def check_for_better_provider(self, current_provider, health_status):
        """Check if there's a significantly better provider available"""
        # Calculate score for current provider
        current_score = self.calculate_provider_score(current_provider, health_status)
        
        # Calculate scores for all other healthy providers
        for provider in CLOUD_PROVIDERS.keys():
            if provider != current_provider:
                provider_score = self.calculate_provider_score(provider, health_status)
                
                # Check if this provider is significantly better (25% improvement)
                if provider_score > current_score * 1.25 and provider_score > 60:
                    return provider
        
        return None
    
    def _perform_advanced_failover(self, failed_provider, health_status, reason):
        """Perform failover using advanced provider selection"""
        # Mark the failed provider to avoid immediate failback
        exclude_providers = [failed_provider]
        
        # Select the best provider based on multi-factor scoring
        best_provider = self.select_best_provider(health_status, exclude_providers)
        
        if not best_provider or best_provider == failed_provider:
            logger.error(f"Failed to find a suitable failover target from {failed_provider}")
            return False
            
        logger.info(f"Advanced failover initiated from {failed_provider} to {best_provider}")
        
        # Update active provider
        self.active_provider = best_provider
        self._save_active_provider(best_provider)
        
        # Record failover time for this provider
        if failed_provider in self.last_failover_time:
            self.last_failover_time[failed_provider] = datetime.now()
        
        # Log the failover event
        self._log_failover_event(failed_provider, best_provider, reason)
        
        return True
    
    def _log_failover_event(self, from_provider, to_provider, reason=None, is_manual=False):
        """Log a failover event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event': 'failover',
            'from_provider': from_provider,
            'to_provider': to_provider,
            'reason': reason if reason else 'Not specified',
            'is_manual': is_manual,
            'scores': {
                provider: self.calculate_provider_score(provider, get_current_health_status())
                for provider in CLOUD_PROVIDERS.keys()
            }
        }
        
        logger.info(f"Failover event: {from_provider} -> {to_provider}, Reason: {reason}")
        
        # Log event to database
        details = {
            "scores": event['scores'],
            "advanced_logic": True
        }
        
        db_manager.record_failover_event(
            from_provider=from_provider,
            to_provider=to_provider,
            reason=reason,
            is_manual=is_manual,
            triggered_by='advanced_system' if not is_manual else 'user',
            details=json.dumps(details)
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
            # Update performance data
            from performance_monitor import get_performance_data
            self.current_performance = get_performance_data()
            
            # Check and perform failover if needed
            self.check_and_failover()
            
            # Wait for next check
            time.sleep(interval)
    
    def start_monitoring(self, interval=10):
        """Start failover monitoring in a background thread"""
        # Initialize with current health data
        health_status = get_current_health_status()
        if health_status:
            self.update_health_history(health_status)
        
        failover_thread = threading.Thread(
            target=self.run_failover_check_thread,
            args=(interval,),
            daemon=True
        )
        failover_thread.start()
        logger.info(f"Advanced failover monitoring started in background thread (interval: {interval}s)")
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
        
        # Record failover time
        if current_provider in self.last_failover_time:
            self.last_failover_time[current_provider] = datetime.now()
        
        # Log the manual failover event
        self._log_failover_event(current_provider, to_provider, reason, is_manual=True)
        
        return True
    
    def simulate_disaster_scenario(self, scenario="random"):
        """Simulate a disaster scenario for testing"""
        # Get current health status
        health_status = get_current_health_status()
        current_provider = self._load_active_provider()
        
        if scenario == "random":
            # Randomly select a scenario
            scenarios = ["provider_failure", "performance_degradation", "network_outage"]
            scenario = random.choice(scenarios)
        
        logger.info(f"Simulating disaster scenario: {scenario}")
        
        if scenario == "provider_failure":
            # Simulate complete provider failure
            logger.info(f"Simulating complete failure of provider: {current_provider}")
            
            # Create failure history
            for _ in range(self.consecutive_failures_threshold + 1):
                self.health_history[current_provider].append({
                    'timestamp': datetime.now(),
                    'healthy': False,
                    'response_time': None
                })
            
            # Trigger failover check
            return self.check_and_failover()
            
        elif scenario == "performance_degradation":
            # Simulate performance degradation
            logger.info(f"Simulating performance degradation on provider: {current_provider}")
            
            # Temporarily modify performance data
            if current_provider in self.current_performance:
                # Make a copy of the original performance data
                original_perf = self.current_performance[current_provider].copy()
                
                # Degrade performance metrics
                self.current_performance[current_provider].update({
                    'average_response_time': 0.8,  # High response time
                    'request_success_rate': 92,   # Lower success rate
                    'cpu_utilization': 90,        # High CPU
                    'memory_utilization': 85      # High memory
                })
                
                # Trigger failover check
                result = self.check_and_failover()
                
                # Restore original performance data
                self.current_performance[current_provider] = original_perf
                
                return result
        
        elif scenario == "network_outage":
            # Simulate network connectivity issues
            logger.info(f"Simulating network outage between providers")
            
            # Select a random provider to fail (not the current one)
            other_providers = [p for p in CLOUD_PROVIDERS.keys() if p != current_provider]
            if other_providers:
                failed_provider = random.choice(other_providers)
                
                # Create network failure for that provider
                for _ in range(self.consecutive_failures_threshold + 1):
                    self.health_history[failed_provider].append({
                        'timestamp': datetime.now(),
                        'healthy': False,
                        'response_time': None
                    })
                
                logger.info(f"Simulated network outage for provider: {failed_provider}")
                
                # In this case, we don't expect a failover since current provider is still healthy
                self.check_and_failover()
                return False
        
        return False
        
    def get_recent_failover_events(self, limit=10):
        """Get recent failover events from database"""
        try:
            # Use the database manager to get recent events
            from db_manager import db_manager
            recent_events = db_manager.get_recent_failover_events(limit=limit)
            return recent_events
        except Exception as e:
            logger.error(f"Error getting recent failover events: {str(e)}")
            return []

# Get active provider function (kept for compatibility)
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

# Create a single instance for the application to use
advanced_failover_manager = AdvancedFailoverManager()

if __name__ == "__main__":
    # When run directly, start advanced failover monitoring
    manager = AdvancedFailoverManager()
    manager.start_monitoring()
    
    # Test by simulating disaster scenarios
    time.sleep(5)  # Wait for initial data collection
    manager.simulate_disaster_scenario("provider_failure")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Advanced failover monitoring stopped")