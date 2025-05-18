import streamlit as st
import pandas as pd
import os
import time
import json
from datetime import datetime

from health_check import get_current_health_status
from failover_manager import get_active_provider, FailoverManager
from backup_sync import BackupSyncManager
from metrics_table import get_formatted_metrics_table
from graph_renderer import (
    create_performance_bar_chart,
    create_cost_bar_chart,
    create_rto_rpo_scatter,
    create_downtime_comparison_chart,
    create_metrics_radar_chart
)

def render_dashboard():
    """Render the main dashboard"""
    st.set_page_config(
        page_title="Multi-Cloud Disaster Recovery Framework",
        page_icon="🔄",
        layout="wide"
    )
    
    # Header with logos
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("Multi-Cloud Disaster Recovery Framework")
        st.markdown("### Real-time monitoring, automated failover, and performance metrics")
    
    # Add cloud infrastructure image
    st.image("https://pixabay.com/get/g9405ffd845ce9ee5f5d4452d4e44d7f38a0df8a68dbe9dd4a83afece8e25ac6265e52c0122074ec97a5b43658aafb3ac76932e446e3dbd04a8f09d83f307cf7a_1280.jpg", 
             caption="Cloud Computing Infrastructure")
    
    # Health Status Section
    st.header("Cloud Providers Health Status")
    col1, col2, col3 = st.columns(3)
    
    # Get current health status and active provider
    health_status = get_current_health_status()
    active_provider = get_active_provider()
    
    # Display health status for each provider
    with col1:
        status = health_status.get("aws", {}).get("status", False)
        st.metric(
            label="AWS Status", 
            value="Healthy" if status else "Unhealthy",
            delta="Active" if active_provider == "aws" else None
        )
        if status:
            st.success("AWS is operational")
        else:
            st.error("AWS is experiencing issues")
        
        response_time = health_status.get("aws", {}).get("response_time", 0)
        if response_time:
            st.info(f"Response time: {response_time:.3f}s")
    
    with col2:
        status = health_status.get("azure", {}).get("status", False)
        st.metric(
            label="Azure Status", 
            value="Healthy" if status else "Unhealthy",
            delta="Active" if active_provider == "azure" else None
        )
        if status:
            st.success("Azure is operational")
        else:
            st.error("Azure is experiencing issues")
            
        response_time = health_status.get("azure", {}).get("response_time", 0)
        if response_time:
            st.info(f"Response time: {response_time:.3f}s")
    
    with col3:
        status = health_status.get("gcp", {}).get("status", False)
        st.metric(
            label="GCP Status", 
            value="Healthy" if status else "Unhealthy",
            delta="Active" if active_provider == "gcp" else None
        )
        if status:
            st.success("GCP is operational")
        else:
            st.error("GCP is experiencing issues")
            
        response_time = health_status.get("gcp", {}).get("response_time", 0)
        if response_time:
            st.info(f"Response time: {response_time:.3f}s")
    
    # Active Provider Section
    st.header("Active Cloud Provider")
    
    # Display active provider info
    st.info(f"Current active provider: {active_provider.upper()}")
    
    # Manual Failover Section
    st.subheader("Manual Failover")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        failover_provider = st.selectbox(
            "Select provider to failover to:", 
            ["aws", "azure", "gcp"],
            index=["aws", "azure", "gcp"].index(active_provider) if active_provider in ["aws", "azure", "gcp"] else 0
        )
    
    with col2:
        if st.button("Trigger Failover"):
            if failover_provider == active_provider:
                st.warning(f"{failover_provider.upper()} is already the active provider.")
            else:
                # Perform manual failover
                failover_manager = FailoverManager()
                success = failover_manager.manual_failover(failover_provider)
                
                if success:
                    st.success(f"Failover to {failover_provider.upper()} initiated successfully!")
                    # Add a small delay to allow for failover to complete
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failover failed. Please check logs for details.")
    
    # Add disaster recovery concept image
    st.image("https://pixabay.com/get/g8c656ade93fa622c15742ec363833e47608cb3945ec65b2ff747fe2309495721477633c6cd6d0130f6fe02b3d735ef39d9bcfceadbd746ee2bdd89d96ceb47fa_1280.jpg", 
             caption="Disaster Recovery Concept")
    
    # Backup Status Section
    st.header("Backup Status")
    
    # Get backup status
    backup_manager = BackupSyncManager()
    file_counts = backup_manager.get_file_counts()
    sync_status = backup_manager.get_sync_status()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("AWS S3 Files", file_counts.get("aws", 0))
        last_sync = sync_status.get("aws", {}).get("last_sync")
        if last_sync:
            sync_time = datetime.fromisoformat(last_sync)
            st.info(f"Last synced: {sync_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    with col2:
        st.metric("Azure Blob Files", file_counts.get("azure", 0))
        last_sync = sync_status.get("azure", {}).get("last_sync")
        if last_sync:
            sync_time = datetime.fromisoformat(last_sync)
            st.info(f"Last synced: {sync_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    with col3:
        st.metric("GCP Bucket Files", file_counts.get("gcp", 0))
        last_sync = sync_status.get("gcp", {}).get("last_sync")
        if last_sync:
            sync_time = datetime.fromisoformat(last_sync)
            st.info(f"Last synced: {sync_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Performance Metrics Section
    st.header("Performance Metrics")
    
    # Display metrics table
    st.subheader("Disaster Recovery Metrics")
    metrics_df = get_formatted_metrics_table()
    st.dataframe(metrics_df, use_container_width=True)
    
    # Add network monitoring dashboard image
    st.image("https://pixabay.com/get/g92c8f5adbdd0c2c518e652cc89f0d860a92118555bc55431b0d5776792d7b7b5e19e9b25c873303bb5cfbccede2d4b8b9490d8c0677e4e058899348ec332b421_1280.jpg", 
             caption="Network Monitoring Dashboard")
    
    # Performance Visualization Section
    st.header("Performance Visualization")
    
    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs([
        "Performance Metrics", 
        "Cost Analysis", 
        "RTO vs. RPO", 
        "Comparative Analysis"
    ])
    
    with tab1:
        st.plotly_chart(create_performance_bar_chart(), use_container_width=True)
        st.plotly_chart(create_downtime_comparison_chart(), use_container_width=True)
    
    with tab2:
        st.plotly_chart(create_cost_bar_chart(), use_container_width=True)
    
    with tab3:
        st.plotly_chart(create_rto_rpo_scatter(), use_container_width=True)
    
    with tab4:
        st.plotly_chart(create_metrics_radar_chart(), use_container_width=True)
    
    # System Logs Section
    st.header("System Logs")
    
    # Display failover logs
    if os.path.exists("logs/failover.log"):
        with open("logs/failover.log", "r") as f:
            log_content = f.read()
        
        st.text_area("Failover Logs", log_content, height=200)
    else:
        st.info("No failover logs available.")
    
    # Footer
    st.markdown("---")
    st.caption("Multi-Cloud Disaster Recovery Framework - Monitoring Dashboard")
    st.caption("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    render_dashboard()
