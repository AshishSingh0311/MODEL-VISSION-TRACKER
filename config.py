import os
from pathlib import Path

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

# Backup sync interval in seconds (6 hours)
BACKUP_SYNC_INTERVAL = 6 * 60 * 60  # seconds

# Performance metrics data from research paper
INITIAL_METRICS = {
    "AWS Instance Failure": {
        "Downtime": 120,
        "RTO": 45,
        "RPO": 5,
        "Failover Time": 30,
        "Cost": 20
    },
    "Azure Storage Failure": {
        "Downtime": 150,
        "RTO": 60,
        "RPO": 6,
        "Failover Time": 35,
        "Cost": 25
    },
    "GCP Network Disruption": {
        "Downtime": 180,
        "RTO": 90,
        "RPO": 7,
        "Failover Time": 50,
        "Cost": 30
    },
    "Cross-Cloud Failover": {
        "Downtime": 90,
        "RTO": 40,
        "RPO": 4,
        "Failover Time": 25,
        "Cost": 22
    },
    "Multi-Cloud Outage": {
        "Downtime": 110,
        "RTO": 50,
        "RPO": 5,
        "Failover Time": 40,
        "Cost": 28
    }
}
