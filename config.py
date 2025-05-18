import os
import random
from pathlib import Path
from datetime import datetime, timedelta

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent

# Health check configuration
HEALTH_CHECK_INTERVAL = 30  # seconds

# Mock cloud endpoints to check health
CLOUD_ENDPOINTS = {
    "aws": "https://httpstat.us/200",
    "azure": "https://httpstat.us/200",
    "gcp": "https://httpstat.us/200"
}

# Paths for data storage
HEALTH_STATUS_FILE = os.path.join(BASE_DIR, "data", "health_status.json")
ACTIVE_PROVIDER_FILE = os.path.join(BASE_DIR, "data", "active_provider.json")
METRICS_FILE = os.path.join(BASE_DIR, "data", "metrics.json")
PERFORMANCE_DATA_FILE = os.path.join(BASE_DIR, "data", "performance_data.json")
AVAILABILITY_HISTORY_FILE = os.path.join(BASE_DIR, "data", "availability_history.json")
COST_HISTORY_FILE = os.path.join(BASE_DIR, "data", "cost_history.json")
NETWORK_LATENCY_FILE = os.path.join(BASE_DIR, "data", "network_latency.json")
FAILOVER_LOG_FILE = os.path.join(BASE_DIR, "logs", "failover.log")

# Mock cloud storage directories
CLOUD_STORAGE = {
    "aws": os.path.join(BASE_DIR, "mock_cloud_storage", "aws_s3"),
    "azure": os.path.join(BASE_DIR, "mock_cloud_storage", "azure_blob"),
    "gcp": os.path.join(BASE_DIR, "mock_cloud_storage", "gcp_bucket")
}

# Create necessary directories if they don't exist
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
for cloud_dir in CLOUD_STORAGE.values():
    os.makedirs(cloud_dir, exist_ok=True)

# Default active provider
DEFAULT_PROVIDER = "aws"

# Failover order (where to go next if current provider fails)
FAILOVER_ORDER = {
    "aws": "azure",
    "azure": "gcp",
    "gcp": "aws"
}

# Cloud provider details with failover priorities
CLOUD_PROVIDERS = {
    "aws": {
        "name": "Amazon Web Services",
        "region": "us-east-1",
        "priority": 1,
        "base_latency": 25,  # milliseconds
        "base_reliability": 0.998,
        "cost_per_hour": 0.75,
        "storage_cost_gb": 0.023,
        "data_transfer_cost_gb": 0.09
    },
    "azure": {
        "name": "Microsoft Azure",
        "region": "eastus",
        "priority": 2,
        "base_latency": 30,  # milliseconds
        "base_reliability": 0.996,
        "cost_per_hour": 0.80,
        "storage_cost_gb": 0.018,
        "data_transfer_cost_gb": 0.08
    },
    "gcp": {
        "name": "Google Cloud Platform",
        "region": "us-central1",
        "priority": 3,
        "base_latency": 28,  # milliseconds
        "base_reliability": 0.997,
        "cost_per_hour": 0.72,
        "storage_cost_gb": 0.020,
        "data_transfer_cost_gb": 0.11
    }
}

# Backup sync interval in seconds (for demo, reduced to 5 minutes)
BACKUP_SYNC_INTERVAL = 5 * 60  # seconds in real production this would be 6 * 60 * 60

# Simulated network conditions
NETWORK_SIMULATION = {
    "normal": {
        "latency_range": (20, 50),  # milliseconds
        "packet_loss_range": (0, 0.1),  # percentage
        "jitter_range": (1, 5)  # milliseconds
    },
    "degraded": {
        "latency_range": (80, 150),
        "packet_loss_range": (0.5, 2),
        "jitter_range": (10, 30)
    },
    "failure": {
        "latency_range": (200, 500),
        "packet_loss_range": (5, 20),
        "jitter_range": (30, 100)
    }
}

# Performance metrics data from research paper
INITIAL_METRICS = {
    "AWS Instance Failure": {
        "Downtime": 120,
        "RTO": 45,
        "RPO": 5,
        "Failover Time": 30,
        "Cost": 20,
        "Data Loss Probability": 0.01,
        "Reliability Score": 0.95
    },
    "Azure Storage Failure": {
        "Downtime": 150,
        "RTO": 60,
        "RPO": 6,
        "Failover Time": 35,
        "Cost": 25,
        "Data Loss Probability": 0.02,
        "Reliability Score": 0.93
    },
    "GCP Network Disruption": {
        "Downtime": 180,
        "RTO": 90,
        "RPO": 7,
        "Failover Time": 50,
        "Cost": 30,
        "Data Loss Probability": 0.03,
        "Reliability Score": 0.90
    },
    "Cross-Cloud Failover": {
        "Downtime": 90,
        "RTO": 40,
        "RPO": 4,
        "Failover Time": 25,
        "Cost": 22,
        "Data Loss Probability": 0.005,
        "Reliability Score": 0.97
    },
    "Multi-Cloud Outage": {
        "Downtime": 110,
        "RTO": 50,
        "RPO": 5,
        "Failover Time": 40,
        "Cost": 28,
        "Data Loss Probability": 0.015,
        "Reliability Score": 0.96
    }
}

# Initial simulated availability history (past 24 hours with 1-hour intervals)
def generate_initial_availability_history():
    providers = ["aws", "azure", "gcp"]
    history = {provider: [] for provider in providers}
    
    # Generate 24 hourly data points
    now = datetime.now()
    for hour_offset in range(24):
        # Calculate hour safely, ensuring it stays in 0-23 range
        hour_value = (now.hour - hour_offset) % 24
        timestamp = now.replace(hour=hour_value, minute=0, second=0, microsecond=0)
        
        for provider in providers:
            # Generate mostly up status with occasional downs
            status = True
            if random.random() < 0.05:  # 5% chance of being down
                status = False
                
            history[provider].append({
                "timestamp": timestamp.isoformat(),
                "status": status,
                "response_time": random.uniform(0.05, 0.5) if status else None
            })
    
    return history

INITIAL_AVAILABILITY_HISTORY = generate_initial_availability_history()

# Initial simulated cost history (past 30 days)
def generate_initial_cost_history():
    providers = ["aws", "azure", "gcp"]
    history = {provider: [] for provider in providers}
    
    # Generate 30 daily data points
    now = datetime.now()
    current_month_day = now.day
    
    for day_offset in range(30):
        # Calculate date safely by subtracting timedelta days
        historical_date = now - timedelta(days=day_offset)
        
        for provider in providers:
            # Base cost per provider with some random variation
            provider_info = CLOUD_PROVIDERS[provider]
            compute_cost = provider_info["cost_per_hour"] * 24 * (0.9 + 0.2 * random.random())
            storage_cost = provider_info["storage_cost_gb"] * random.randint(50, 200)
            transfer_cost = provider_info["data_transfer_cost_gb"] * random.randint(10, 100)
            
            history[provider].append({
                "timestamp": historical_date.isoformat(),
                "compute_cost": round(compute_cost, 2),
                "storage_cost": round(storage_cost, 2),
                "transfer_cost": round(transfer_cost, 2),
                "total_cost": round(compute_cost + storage_cost + transfer_cost, 2)
            })
    
    return history

INITIAL_COST_HISTORY = generate_initial_cost_history()

# Initial network latency data
def generate_initial_network_latency():
    providers = ["aws", "azure", "gcp"]
    latency_data = {provider: [] for provider in providers}
    
    # Current timestamp
    now_timestamp = datetime.now().timestamp()
    
    # Generate 50 data points (could represent last 50 minutes)
    for i in range(50):
        for provider in providers:
            base_latency = CLOUD_PROVIDERS[provider]["base_latency"]
            variation = random.uniform(-5, 15)
            
            # Occasionally add a latency spike
            if random.random() < 0.05:
                variation += random.uniform(20, 100)
                
            # Calculate timestamp for each point (going back in time)
            point_timestamp = now_timestamp - (50 - i) * 60  # 1 minute intervals
            
            latency_data[provider].append({
                "timestamp": point_timestamp,
                "latency": round(base_latency + variation, 1)
            })
    
    return latency_data

INITIAL_NETWORK_LATENCY = generate_initial_network_latency()
