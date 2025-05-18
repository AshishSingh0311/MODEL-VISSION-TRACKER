import os
import time
import threading
import streamlit as st
import logging
from pathlib import Path

from health_check import HealthChecker
from failover_manager import FailoverManager
from backup_sync import BackupSyncManager
from dashboard import render_dashboard

# Ensure necessary directories exist
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("mock_cloud_storage/aws_s3", exist_ok=True)
os.makedirs("mock_cloud_storage/azure_blob", exist_ok=True)
os.makedirs("mock_cloud_storage/gcp_bucket", exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/main.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('main')

def start_services():
    """Start all background services"""
    logger.info("Starting Multi-Cloud Disaster Recovery Framework services...")
    
    # Start health checking service
    health_checker = HealthChecker()
    health_thread = health_checker.start_monitoring()
    logger.info("Health checker started")
    
    # Start failover manager
    failover_manager = FailoverManager()
    failover_thread = failover_manager.start_monitoring()
    logger.info("Failover manager started")
    
    # Start backup sync manager
    backup_manager = BackupSyncManager()
    backup_thread = backup_manager.start_backup_sync()
    logger.info("Backup sync manager started")
    
    # Add test files to AWS S3 mock directory if empty
    aws_dir = "mock_cloud_storage/aws_s3"
    if not os.listdir(aws_dir):
        logger.info("Adding test files to AWS S3 mock directory")
        for i in range(5):
            test_file = os.path.join(aws_dir, f"test_file_{i}.txt")
            with open(test_file, "w") as f:
                f.write(f"This is test file {i} content")
    
    logger.info("All services started successfully")
    return health_thread, failover_thread, backup_thread

def main():
    """Main entry point for the application"""
    # Start background services
    threads = start_services()
    
    # Launch Streamlit dashboard
    render_dashboard()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
