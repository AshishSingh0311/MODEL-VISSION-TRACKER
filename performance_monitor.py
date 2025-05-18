import json
import logging
import os
import random
import threading
import time
from datetime import datetime, timedelta

from config import (
    CLOUD_PROVIDERS,
    NETWORK_SIMULATION,
    PERFORMANCE_DATA_FILE,
    AVAILABILITY_HISTORY_FILE,
    COST_HISTORY_FILE,
    NETWORK_LATENCY_FILE,
    INITIAL_AVAILABILITY_HISTORY,
    INITIAL_COST_HISTORY,
    INITIAL_NETWORK_LATENCY
)

from health_check import get_current_health_status
from failover_manager import get_active_provider

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/performance_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('performance_monitor')

class PerformanceMonitor:
    def __init__(self):
        """Initialize the performance monitor"""
        self.providers = list(CLOUD_PROVIDERS.keys())
        self.init_performance_data()
        self.init_availability_history()
        self.init_cost_history()
        self.init_network_latency()
        self.simulation_mode = "normal"  # normal, degraded, failure
        
    def init_performance_data(self):
        """Initialize performance data file if it doesn't exist"""
        try:
            if not os.path.exists(PERFORMANCE_DATA_FILE):
                # Create initial performance data
                performance_data = {
                    provider: {
                        "cpu_utilization": random.uniform(10, 30),
                        "memory_utilization": random.uniform(20, 40),
                        "disk_iops": random.randint(100, 500),
                        "network_throughput": random.uniform(50, 200),
                        "request_success_rate": random.uniform(98, 100),
                        "average_response_time": random.uniform(0.1, 0.3),
                        "timestamp": datetime.now().isoformat()
                    } for provider in self.providers
                }
                
                os.makedirs(os.path.dirname(PERFORMANCE_DATA_FILE), exist_ok=True)
                with open(PERFORMANCE_DATA_FILE, 'w') as f:
                    json.dump(performance_data, f)
                    
                logger.info("Initialized performance data file")
        except Exception as e:
            logger.error(f"Error initializing performance data: {str(e)}")
    
    def init_availability_history(self):
        """Initialize availability history file if it doesn't exist"""
        try:
            if not os.path.exists(AVAILABILITY_HISTORY_FILE):
                # Use initial availability history from config
                os.makedirs(os.path.dirname(AVAILABILITY_HISTORY_FILE), exist_ok=True)
                with open(AVAILABILITY_HISTORY_FILE, 'w') as f:
                    json.dump(INITIAL_AVAILABILITY_HISTORY, f)
                    
                logger.info("Initialized availability history file")
        except Exception as e:
            logger.error(f"Error initializing availability history: {str(e)}")
    
    def init_cost_history(self):
        """Initialize cost history file if it doesn't exist"""
        try:
            if not os.path.exists(COST_HISTORY_FILE):
                # Use initial cost history from config
                os.makedirs(os.path.dirname(COST_HISTORY_FILE), exist_ok=True)
                with open(COST_HISTORY_FILE, 'w') as f:
                    json.dump(INITIAL_COST_HISTORY, f)
                    
                logger.info("Initialized cost history file")
        except Exception as e:
            logger.error(f"Error initializing cost history: {str(e)}")
    
    def init_network_latency(self):
        """Initialize network latency file if it doesn't exist"""
        try:
            if not os.path.exists(NETWORK_LATENCY_FILE):
                # Use initial network latency from config
                os.makedirs(os.path.dirname(NETWORK_LATENCY_FILE), exist_ok=True)
                with open(NETWORK_LATENCY_FILE, 'w') as f:
                    json.dump(INITIAL_NETWORK_LATENCY, f)
                    
                logger.info("Initialized network latency file")
        except Exception as e:
            logger.error(f"Error initializing network latency: {str(e)}")
    
    def update_performance_data(self):
        """Update performance metrics based on current health status and simulation mode"""
        try:
            # Get current health status and active provider
            health_status = get_current_health_status()
            active_provider = get_active_provider()
            
            # Load current performance data
            if os.path.exists(PERFORMANCE_DATA_FILE):
                with open(PERFORMANCE_DATA_FILE, 'r') as f:
                    performance_data = json.load(f)
            else:
                performance_data = {}
            
            # Update performance data for each provider
            for provider in self.providers:
                is_healthy = provider in health_status and health_status[provider].get('status', False)
                is_active = provider == active_provider
                
                # Base performance influenced by health status
                if not is_healthy:
                    # Provider is unhealthy - use failure simulation mode
                    sim_mode = "failure"
                elif provider in performance_data and random.random() < 0.05:
                    # Occasionally introduce degraded performance 
                    sim_mode = "degraded"
                else:
                    # Normal operation
                    sim_mode = self.simulation_mode
                
                # Generate performance metrics based on simulation mode
                metrics = self._generate_performance_metrics(provider, sim_mode, is_active)
                
                # Update performance data
                performance_data[provider] = metrics
                
                # Store in database
                from db_manager import db_manager
                db_manager.record_performance_metrics(provider, metrics)
            
            # Save updated performance data to file as backup
            with open(PERFORMANCE_DATA_FILE, 'w') as f:
                json.dump(performance_data, f)
                
            logger.debug("Updated performance data")
            
            # Update availability history
            self._update_availability_history(health_status)
            
            # Update network latency
            self._update_network_latency()
            
            # Occasionally update cost history (hourly)
            if random.random() < 0.01:  # ~1% chance each update
                self._update_cost_history()
            
            return performance_data
            
        except Exception as e:
            logger.error(f"Error updating performance data: {str(e)}")
            return {}
    
    def _generate_performance_metrics(self, provider, sim_mode, is_active):
        """Generate realistic performance metrics based on simulation mode"""
        # Get simulation parameters
        sim_params = NETWORK_SIMULATION[sim_mode]
        
        # Base provider parameters
        provider_info = CLOUD_PROVIDERS[provider]
        base_latency = provider_info["base_latency"]
        
        # CPU utilization
        if sim_mode == "normal":
            cpu_util = random.uniform(10, 40)
        elif sim_mode == "degraded":
            cpu_util = random.uniform(60, 85)
        else:  # failure
            cpu_util = random.uniform(85, 100)
            
        # Add more load if provider is active
        if is_active:
            cpu_util = min(100, cpu_util + random.uniform(10, 20))
        
        # Memory utilization (correlated with CPU but with some independence)
        memory_util = cpu_util * random.uniform(0.8, 1.2)
        memory_util = max(10, min(100, memory_util))
        
        # Disk IOPS
        if sim_mode == "normal":
            disk_iops = random.randint(500, 2000)
        elif sim_mode == "degraded":
            disk_iops = random.randint(200, 500)
        else:  # failure
            disk_iops = random.randint(10, 200)
        
        # Network throughput (Mbps)
        if sim_mode == "normal":
            network_throughput = random.uniform(200, 1000)
        elif sim_mode == "degraded":
            network_throughput = random.uniform(50, 200)
        else:  # failure
            network_throughput = random.uniform(1, 50)
        
        # Request success rate
        if sim_mode == "normal":
            success_rate = random.uniform(99.5, 100)
        elif sim_mode == "degraded":
            success_rate = random.uniform(95, 99.5)
        else:  # failure
            success_rate = random.uniform(0, 95)
        
        # Average response time (ms)
        latency_min, latency_max = sim_params["latency_range"]
        response_time = random.uniform(latency_min, latency_max) / 1000  # convert to seconds
        
        # Response time affected by base latency of provider
        response_time = response_time * (base_latency / 25)  # normalize against AWS latency
        
        return {
            "cpu_utilization": round(cpu_util, 2),
            "memory_utilization": round(memory_util, 2),
            "disk_iops": int(disk_iops),
            "network_throughput": round(network_throughput, 2),
            "request_success_rate": round(success_rate, 2),
            "average_response_time": round(response_time, 3),
            "timestamp": datetime.now().isoformat()
        }
    
    def _update_availability_history(self, health_status):
        """Update availability history with latest health status"""
        try:
            # Load current availability history
            if os.path.exists(AVAILABILITY_HISTORY_FILE):
                with open(AVAILABILITY_HISTORY_FILE, 'r') as f:
                    availability_history = json.load(f)
            else:
                availability_history = {provider: [] for provider in self.providers}
            
            # Get current time rounded to the hour
            now = datetime.now()
            current_hour = now.replace(minute=0, second=0, microsecond=0)
            
            # Update for each provider
            for provider in self.providers:
                # Check if we already have an entry for the current hour
                provider_history = availability_history.get(provider, [])
                
                if not provider_history or datetime.fromisoformat(provider_history[-1]["timestamp"]).hour != current_hour.hour:
                    # Add new hourly entry
                    is_available = provider in health_status and health_status[provider].get('status', False)
                    response_time = health_status.get(provider, {}).get('response_time', None) if is_available else None
                    
                    provider_history.append({
                        "timestamp": current_hour.isoformat(),
                        "status": is_available,
                        "response_time": response_time
                    })
                    
                    # Keep only the last 24 hours of data
                    if len(provider_history) > 24:
                        provider_history = provider_history[-24:]
                    
                    availability_history[provider] = provider_history
            
            # Save updated availability history
            with open(AVAILABILITY_HISTORY_FILE, 'w') as f:
                json.dump(availability_history, f)
                
            logger.debug("Updated availability history")
            
        except Exception as e:
            logger.error(f"Error updating availability history: {str(e)}")
    
    def _update_network_latency(self):
        """Update network latency data with a new data point"""
        try:
            # Load current network latency data
            if os.path.exists(NETWORK_LATENCY_FILE):
                with open(NETWORK_LATENCY_FILE, 'r') as f:
                    latency_data = json.load(f)
            else:
                latency_data = {provider: [] for provider in self.providers}
            
            # Current timestamp
            current_time = datetime.now().timestamp()
            
            # Update for each provider
            for provider in self.providers:
                provider_latency = latency_data.get(provider, [])
                
                # Get base latency for provider
                base_latency = CLOUD_PROVIDERS[provider]["base_latency"]
                
                # Add random variation based on simulation mode
                if self.simulation_mode == "normal":
                    variation = random.uniform(-5, 10)
                elif self.simulation_mode == "degraded":
                    variation = random.uniform(10, 50)
                else:  # failure
                    variation = random.uniform(50, 200)
                
                # Occasionally add a latency spike
                if random.random() < 0.05:
                    variation += random.uniform(20, 100)
                    
                # Add new data point
                provider_latency.append({
                    "timestamp": current_time,
                    "latency": round(base_latency + variation, 1)
                })
                
                # Keep only the last 50 data points
                if len(provider_latency) > 50:
                    provider_latency = provider_latency[-50:]
                
                latency_data[provider] = provider_latency
            
            # Save updated network latency data
            with open(NETWORK_LATENCY_FILE, 'w') as f:
                json.dump(latency_data, f)
                
            logger.debug("Updated network latency data")
            
        except Exception as e:
            logger.error(f"Error updating network latency: {str(e)}")
    
    def _update_cost_history(self):
        """Update cost history with a new data point"""
        try:
            # Load current cost history
            if os.path.exists(COST_HISTORY_FILE):
                with open(COST_HISTORY_FILE, 'r') as f:
                    cost_history = json.load(f)
            else:
                cost_history = {provider: [] for provider in self.providers}
            
            # Get active provider
            active_provider = get_active_provider()
            
            # Get current date
            now = datetime.now()
            current_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Update for each provider
            for provider in self.providers:
                provider_history = cost_history.get(provider, [])
                
                # Check if we already have an entry for the current day
                if not provider_history or datetime.fromisoformat(provider_history[-1]["timestamp"]).day != current_day.day:
                    # Get provider cost info
                    provider_info = CLOUD_PROVIDERS[provider]
                    
                    # Calculate costs with realistic variations
                    # More cost for active provider
                    activity_multiplier = 1.5 if provider == active_provider else 1.0
                    
                    compute_cost = provider_info["cost_per_hour"] * 24 * activity_multiplier * (0.9 + 0.2 * random.random())
                    storage_cost = provider_info["storage_cost_gb"] * random.randint(50, 200)
                    transfer_cost = provider_info["data_transfer_cost_gb"] * random.randint(10, 100) * activity_multiplier
                    
                    # Add new daily cost entry
                    provider_history.append({
                        "timestamp": current_day.isoformat(),
                        "compute_cost": round(compute_cost, 2),
                        "storage_cost": round(storage_cost, 2),
                        "transfer_cost": round(transfer_cost, 2),
                        "total_cost": round(compute_cost + storage_cost + transfer_cost, 2)
                    })
                    
                    # Keep only the last 30 days of data
                    if len(provider_history) > 30:
                        provider_history = provider_history[-30:]
                    
                    cost_history[provider] = provider_history
            
            # Save updated cost history
            with open(COST_HISTORY_FILE, 'w') as f:
                json.dump(cost_history, f)
                
            logger.debug("Updated cost history")
            
        except Exception as e:
            logger.error(f"Error updating cost history: {str(e)}")
    
    def set_simulation_mode(self, mode):
        """Set the simulation mode for performance metrics"""
        if mode in NETWORK_SIMULATION:
            self.simulation_mode = mode
            logger.info(f"Simulation mode set to: {mode}")
            return True
        else:
            logger.error(f"Invalid simulation mode: {mode}")
            return False
    
    def run_performance_monitor_thread(self, interval=60):
        """Run performance monitoring in a loop at specified intervals"""
        while True:
            try:
                self.update_performance_data()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in performance monitor thread: {str(e)}")
                time.sleep(10)  # Short delay before trying again
    
    def start_monitoring(self, interval=60):
        """Start performance monitoring in a background thread"""
        performance_thread = threading.Thread(
            target=self.run_performance_monitor_thread,
            args=(interval,),
            daemon=True
        )
        performance_thread.start()
        logger.info(f"Performance monitoring started in background thread (interval: {interval}s)")
        return performance_thread

def get_performance_data():
    """Get the current performance data"""
    try:
        if os.path.exists(PERFORMANCE_DATA_FILE):
            with open(PERFORMANCE_DATA_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error getting performance data: {str(e)}")
        return {}

def get_availability_history():
    """Get the availability history"""
    try:
        if os.path.exists(AVAILABILITY_HISTORY_FILE):
            with open(AVAILABILITY_HISTORY_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error getting availability history: {str(e)}")
        return {}

def get_cost_history():
    """Get the cost history"""
    try:
        if os.path.exists(COST_HISTORY_FILE):
            with open(COST_HISTORY_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error getting cost history: {str(e)}")
        return {}

def get_network_latency():
    """Get the network latency data"""
    try:
        if os.path.exists(NETWORK_LATENCY_FILE):
            with open(NETWORK_LATENCY_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error getting network latency: {str(e)}")
        return {}

def calculate_availability_percentage(provider=None):
    """Calculate availability percentage for the specified provider or all providers"""
    try:
        availability_history = get_availability_history()
        
        if not availability_history:
            return {}
        
        if provider:
            providers = [provider]
        else:
            providers = list(availability_history.keys())
        
        result = {}
        for prov in providers:
            if prov in availability_history:
                history = availability_history[prov]
                if history:
                    uptime_count = sum(1 for entry in history if entry.get("status", False))
                    availability = (uptime_count / len(history)) * 100
                    result[prov] = round(availability, 2)
                else:
                    result[prov] = 0.0
        
        return result
    except Exception as e:
        logger.error(f"Error calculating availability percentage: {str(e)}")
        return {}

def get_total_cost_by_provider():
    """Get the total cost for each provider over the entire history"""
    try:
        cost_history = get_cost_history()
        
        if not cost_history:
            return {}
        
        result = {}
        for provider, history in cost_history.items():
            total_cost = sum(entry.get("total_cost", 0) for entry in history)
            result[provider] = round(total_cost, 2)
        
        return result
    except Exception as e:
        logger.error(f"Error calculating total cost: {str(e)}")
        return {}

if __name__ == "__main__":
    # When run directly, start performance monitoring
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Performance monitoring stopped")