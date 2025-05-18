import streamlit as st
import pandas as pd
import os
import time
import json
from datetime import datetime, timedelta
import random

from health_check import get_current_health_status
from failover_manager import get_active_provider, FailoverManager
from backup_sync import BackupSyncManager
from performance_monitor import (
    PerformanceMonitor, 
    get_performance_data, 
    get_availability_history,
    get_cost_history,
    get_network_latency,
    calculate_availability_percentage,
    get_total_cost_by_provider
)
from metrics_table import get_formatted_metrics_table
from graph_renderer import (
    create_performance_bar_chart,
    create_cost_bar_chart,
    create_rto_rpo_scatter,
    create_downtime_comparison_chart,
    create_metrics_radar_chart
)
from advanced_graphs import (
    create_performance_comparison_chart,
    create_availability_timeline,
    create_network_latency_chart,
    create_cost_breakdown_chart,
    create_cost_trend_chart,
    create_availability_sla_gauge,
    create_failover_timeline_chart,
    create_reliability_comparison_chart,
    create_realtime_performance_gauges,
    create_rpo_rto_analysis_chart
)

# Color schemes for consistent visualizations
PROVIDER_COLORS = {
    "aws": "#FF9900",      # AWS Orange
    "azure": "#0078D4",    # Azure Blue
    "gcp": "#4285F4"       # Google Blue
}

def render_dashboard():
    """Render the main dashboard"""
    st.set_page_config(
        page_title="Multi-Cloud Disaster Recovery Framework",
        page_icon="🔄",
        layout="wide"
    )
    
    # Sidebar for navigation and controls
    with st.sidebar:
        st.title("Multi-Cloud DR Framework")
        
        # Navigation
        page = st.radio(
            "Navigation",
            ["Overview", "Health Monitoring", "Failover Management", "Storage & Backup", "Performance Analytics", "Cost Analysis", "Configuration"]
        )
        
        st.markdown("---")
        
        # Status Summary
        st.subheader("System Status")
        health_status = get_current_health_status()
        active_provider = get_active_provider()
        
        # Display active provider
        st.info(f"**Active Provider:** {active_provider.upper()}")
        
        # Quick status indicators
        aws_status = "🟢" if health_status.get("aws", {}).get("status", False) else "🔴"
        azure_status = "🟢" if health_status.get("azure", {}).get("status", False) else "🔴"
        gcp_status = "🟢" if health_status.get("gcp", {}).get("status", False) else "🔴"
        
        st.write(f"AWS: {aws_status} | Azure: {azure_status} | GCP: {gcp_status}")
        
        # Get failover logs count
        failover_count = 0
        if os.path.exists("logs/failover.log"):
            with open("logs/failover.log", "r") as f:
                failover_count = sum(1 for line in f if '{"timestamp":' in line)
        
        st.write(f"Failover Events: {failover_count}")
        
        st.markdown("---")
        
        # Simulation controls (in sidebar)
        st.subheader("Simulation Controls")
        
        # Simulation mode selection
        simulation_mode = st.selectbox(
            "Simulation Mode:",
            ["normal", "degraded", "failure"],
            index=0
        )
        
        # Apply simulation button
        if st.button("Apply Simulation"):
            performance_monitor = PerformanceMonitor()
            success = performance_monitor.set_simulation_mode(simulation_mode)
            if success:
                st.success(f"Simulation mode set to: {simulation_mode}")
            else:
                st.error("Failed to set simulation mode")
        
        # Trigger specific failures
        st.write("Trigger Specific Failures:")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            aws_fail = st.button("AWS ⚠️")
        with col2:
            azure_fail = st.button("Azure ⚠️")
        with col3:
            gcp_fail = st.button("GCP ⚠️")
        
        # Handle failure simulations
        if aws_fail:
            # Simulate AWS failure by altering the health check endpoint
            with open("config.py", "r") as f:
                config_content = f.read()
            
            new_config = config_content.replace(
                '"aws": "https://httpstat.us/200"', 
                '"aws": "https://httpstat.us/500"'
            )
            
            with open("config.py", "w") as f:
                f.write(new_config)
            
            st.warning("AWS failure simulation initiated!")
            st.info("Health check will detect failure in next cycle")
        
        if azure_fail:
            # Simulate Azure failure
            with open("config.py", "r") as f:
                config_content = f.read()
            
            new_config = config_content.replace(
                '"azure": "https://httpstat.us/200"', 
                '"azure": "https://httpstat.us/500"'
            )
            
            with open("config.py", "w") as f:
                f.write(new_config)
            
            st.warning("Azure failure simulation initiated!")
            st.info("Health check will detect failure in next cycle")
        
        if gcp_fail:
            # Simulate GCP failure
            with open("config.py", "r") as f:
                config_content = f.read()
            
            new_config = config_content.replace(
                '"gcp": "https://httpstat.us/200"', 
                '"gcp": "https://httpstat.us/500"'
            )
            
            with open("config.py", "w") as f:
                f.write(new_config)
            
            st.warning("GCP failure simulation initiated!")
            st.info("Health check will detect failure in next cycle")
        
        # Reset all simulations
        if st.button("Reset All"):
            with open("config.py", "r") as f:
                config_content = f.read()
            
            new_config = config_content.replace(
                '"aws": "https://httpstat.us/500"', 
                '"aws": "https://httpstat.us/200"'
            ).replace(
                '"azure": "https://httpstat.us/500"', 
                '"azure": "https://httpstat.us/200"'
            ).replace(
                '"gcp": "https://httpstat.us/500"', 
                '"gcp": "https://httpstat.us/200"'
            )
            
            with open("config.py", "w") as f:
                f.write(new_config)
            
            # Reset simulation mode
            performance_monitor = PerformanceMonitor()
            performance_monitor.set_simulation_mode("normal")
            
            st.success("All simulations reset to normal!")
        
        st.markdown("---")
        
        # Add version information in sidebar footer
        st.caption("Multi-Cloud DR Framework v1.0")
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Main content area based on selected page
    if page == "Overview":
        render_overview_page()
    elif page == "Health Monitoring":
        render_health_monitoring_page()
    elif page == "Failover Management":
        render_failover_management_page()
    elif page == "Storage & Backup":
        render_storage_backup_page()
    elif page == "Performance Analytics":
        render_performance_analytics_page()
    elif page == "Cost Analysis":
        render_cost_analysis_page()
    elif page == "Configuration":
        render_configuration_page()

def render_overview_page():
    """Render the overview dashboard page"""
    # Header
    st.title("Multi-Cloud Disaster Recovery Framework")
    st.markdown("### Real-time monitoring, automated failover, and business continuity")
    
    # Executive Summary in top row
    st.subheader("Executive Summary")
    col1, col2, col3 = st.columns(3)
    
    # Get current data
    health_status = get_current_health_status()
    active_provider = get_active_provider()
    availability_percentages = calculate_availability_percentage()
    total_costs = get_total_cost_by_provider()
    
    # Key metrics
    with col1:
        st.metric(
            label="System Availability",
            value=f"{availability_percentages.get(active_provider, 0):.2f}%",
            delta="0.05%" if random.random() > 0.5 else "-0.03%"
        )
        st.markdown(f"**Active Provider:** {active_provider.upper()}")
    
    with col2:
        # Calculate total number of healthy providers
        healthy_count = sum(1 for provider, status in health_status.items() if status.get('status', False))
        total_count = len(health_status)
        
        st.metric(
            label="Cloud Providers",
            value=f"{healthy_count}/{total_count} Healthy",
            delta=None
        )
        st.markdown(f"**Failover Readiness:** {'High' if healthy_count >= 2 else 'Medium' if healthy_count == 1 else 'Low'}")
    
    with col3:
        # Calculate total cost across all providers
        total_cost = sum(total_costs.values())
        st.metric(
            label="Total Infrastructure Cost",
            value=f"${total_cost:.2f}",
            delta=f"${random.uniform(-10, 10):.2f}" 
        )
        st.markdown(f"**Current Month Projection:** ${total_cost * 30 / 7:.2f}")
    
    # Real-time status dashboard
    st.subheader("Real-Time System Status")
    
    # Real-time performance gauges
    try:
        st.plotly_chart(create_realtime_performance_gauges(), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying performance gauges: {str(e)}")
    
    # Provider availability status
    col1, col2, col3 = st.columns(3)
    
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
    
    # Availability timeline
    st.subheader("Provider Availability Timeline (Last 24 Hours)")
    try:
        st.plotly_chart(create_availability_timeline(), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying availability timeline: {str(e)}")
    
    # Manual Failover Controls
    st.subheader("Manual Failover Control")
    
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
    
    # Key performance metrics
    st.subheader("Key Performance Metrics")
    
    # Display metrics table
    metrics_df = get_formatted_metrics_table()
    st.dataframe(metrics_df, use_container_width=True)
    
    # Recent failover events
    st.subheader("Recent Failover Events")
    try:
        st.plotly_chart(create_failover_timeline_chart(), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying failover timeline: {str(e)}")
    
    # Network latency trends
    st.subheader("Network Latency Trends")
    try:
        st.plotly_chart(create_network_latency_chart(), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying network latency chart: {str(e)}")

def render_health_monitoring_page():
    """Render the health monitoring page"""
    st.title("Health Monitoring Dashboard")
    
    # Get health data
    health_status = get_current_health_status()
    availability_percentages = calculate_availability_percentage()
    performance_data = get_performance_data()
    
    # Provider health metrics
    st.subheader("Cloud Provider Health Status")
    
    # SLA gauges
    try:
        st.plotly_chart(create_availability_sla_gauge(), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying SLA gauges: {str(e)}")
    
    # Provider details in expandable sections
    providers = ["aws", "azure", "gcp"]
    
    for provider in providers:
        with st.expander(f"{provider.upper()} Health Details", expanded=(provider == get_active_provider())):
            col1, col2 = st.columns([1, 2])
            
            # Provider status
            with col1:
                status = health_status.get(provider, {}).get("status", False)
                st.metric(
                    label="Status", 
                    value="Healthy" if status else "Unhealthy"
                )
                if status:
                    st.success(f"{provider.upper()} is operational")
                else:
                    st.error(f"{provider.upper()} is experiencing issues")
                
                # Response time
                response_time = health_status.get(provider, {}).get("response_time", 0)
                if response_time:
                    st.metric("Response Time", f"{response_time:.3f}s")
                
                # Availability percentage
                st.metric(
                    label="24hr Availability", 
                    value=f"{availability_percentages.get(provider, 0):.2f}%"
                )
            
            # Performance metrics
            with col2:
                if provider in performance_data:
                    provider_metrics = performance_data[provider]
                    
                    # Create metrics display
                    st.subheader("Performance Metrics")
                    
                    # Create a dataframe for display
                    metrics_to_display = {
                        "CPU Utilization": f"{provider_metrics.get('cpu_utilization', 0):.1f}%",
                        "Memory Utilization": f"{provider_metrics.get('memory_utilization', 0):.1f}%",
                        "Disk IOPS": f"{provider_metrics.get('disk_iops', 0)}",
                        "Network Throughput": f"{provider_metrics.get('network_throughput', 0):.1f} Mbps",
                        "Success Rate": f"{provider_metrics.get('request_success_rate', 0):.2f}%",
                        "Avg. Response Time": f"{provider_metrics.get('average_response_time', 0) * 1000:.1f} ms"
                    }
                    
                    # Display as a horizontal list
                    metric_cols = st.columns(3)
                    
                    for i, (metric, value) in enumerate(metrics_to_display.items()):
                        with metric_cols[i % 3]:
                            st.metric(metric, value)
                else:
                    st.info(f"No performance data available for {provider.upper()}")
    
    # Health monitoring timeline
    st.subheader("Health Status Timeline (Last 24 Hours)")
    try:
        st.plotly_chart(create_availability_timeline(), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying availability timeline: {str(e)}")
    
    # Advanced performance comparison
    st.subheader("Performance Comparison Across Providers")
    
    try:
        st.plotly_chart(create_performance_comparison_chart(), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying performance comparison chart: {str(e)}")
    
    # Network latency
    st.subheader("Network Latency Monitoring")
    
    try:
        st.plotly_chart(create_network_latency_chart(), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying network latency chart: {str(e)}")
    
    # Health monitoring logs
    st.subheader("Health Check Logs")
    
    if os.path.exists("logs/health_check.log"):
        with open("logs/health_check.log", "r") as f:
            log_content = f.readlines()
            
            # Show only the last 20 log entries
            log_sample = log_content[-20:]
            
            st.text_area("Recent Log Entries", "".join(log_sample), height=200)
            
            if st.button("View Complete Health Check Logs"):
                st.text_area("Complete Health Check Logs", "".join(log_content), height=400)
    else:
        st.info("No health check logs available")

def render_failover_management_page():
    """Render the failover management page"""
    st.title("Failover Management Dashboard")
    
    # Get active provider and health status
    active_provider = get_active_provider()
    health_status = get_current_health_status()
    
    # Active provider status and controls
    st.subheader("Current Active Provider")
    
    # Display active provider with more details
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.metric(
            label="Active Provider", 
            value=active_provider.upper(),
        )
        
        # Show status of active provider
        active_status = health_status.get(active_provider, {}).get("status", False)
        if active_status:
            st.success(f"{active_provider.upper()} is healthy and operational")
        else:
            st.error(f"{active_provider.upper()} is unhealthy! Automatic failover should be triggered soon.")
    
    with col2:
        # Show automatic failover path
        from config import FAILOVER_ORDER
        
        st.markdown("#### Failover Path")
        
        # Create a visual representation of the failover path
        failover_path = []
        current = active_provider
        
        # Generate the path (maximum of 3 hops)
        for _ in range(3):
            next_provider = FAILOVER_ORDER.get(current)
            if next_provider and next_provider not in failover_path:
                failover_path.append(next_provider)
                current = next_provider
            else:
                break
        
        # Show the path with arrows
        path_str = f"{active_provider.upper()}"
        for provider in failover_path:
            path_str += f" → {provider.upper()}"
        
        st.markdown(f"<div style='font-size: 24px; padding: 10px; text-align: center;'>{path_str}</div>", unsafe_allow_html=True)
    
    # Manual Failover Control
    st.subheader("Manual Failover Control")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        failover_provider = st.selectbox(
            "Select provider to failover to:", 
            ["aws", "azure", "gcp"],
            index=["aws", "azure", "gcp"].index(active_provider) if active_provider in ["aws", "azure", "gcp"] else 0
        )
        
        # Add a reason field for documentation
        failover_reason = st.text_input("Failover reason (for documentation):", "Manual failover for testing")
    
    with col2:
        if st.button("Trigger Failover", key="failover_button_1"):
            if failover_provider == active_provider:
                st.warning(f"{failover_provider.upper()} is already the active provider.")
            else:
                # Perform manual failover
                failover_manager = FailoverManager()
                success = failover_manager.manual_failover(failover_provider)
                
                if success:
                    st.success(f"Failover to {failover_provider.upper()} initiated successfully!")
                    
                    # Log the reason (in a real implementation)
                    st.info(f"Reason logged: {failover_reason}")
                    
                    # Add a small delay to allow for failover to complete
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failover failed. Please check logs for details.")
    
    # Failover events timeline
    st.subheader("Failover Events Timeline")
    
    try:
        st.plotly_chart(create_failover_timeline_chart(), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying failover timeline: {str(e)}")
    
    # Provider reliability metrics
    st.subheader("Provider Reliability Analysis")
    try:
        st.plotly_chart(create_reliability_comparison_chart(), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying reliability comparison: {str(e)}")
    
    # Advanced RPO/RTO Analysis
    st.subheader("Recovery Objectives Analysis")
    try:
        st.plotly_chart(create_rpo_rto_analysis_chart(), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying RPO/RTO analysis: {str(e)}")
    
    # Failover logs
    st.subheader("Failover Event Logs")
    
    if os.path.exists("logs/failover.log"):
        with open("logs/failover.log", "r") as f:
            log_content = f.read()
        
        st.text_area("Failover Logs", log_content, height=200)
    else:
        st.info("No failover logs available.")

def render_storage_backup_page():
    """Render the storage and backup page"""
    st.title("Storage & Backup Management Dashboard")
    
    # Get backup status
    backup_manager = BackupSyncManager()
    file_counts = backup_manager.get_file_counts()
    sync_status = backup_manager.get_sync_status()
    
    # Storage summary
    st.subheader("Storage Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("AWS S3 Files", file_counts.get("aws", 0))
        last_sync = sync_status.get("aws", {}).get("last_sync")
        if last_sync:
            sync_time = datetime.fromisoformat(last_sync)
            st.info(f"Last synced: {sync_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Show sync details
            synced_files = sync_status.get("aws", {}).get("files_synced", 0)
            total_files = sync_status.get("aws", {}).get("total_files", 0)
            st.caption(f"Files synced: {synced_files} of {total_files}")
    
    with col2:
        st.metric("Azure Blob Files", file_counts.get("azure", 0))
        last_sync = sync_status.get("azure", {}).get("last_sync")
        if last_sync:
            sync_time = datetime.fromisoformat(last_sync)
            st.info(f"Last synced: {sync_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Show sync details
            synced_files = sync_status.get("azure", {}).get("files_synced", 0)
            total_files = sync_status.get("azure", {}).get("total_files", 0)
            st.caption(f"Files synced: {synced_files} of {total_files}")
    
    with col3:
        st.metric("GCP Bucket Files", file_counts.get("gcp", 0))
        last_sync = sync_status.get("gcp", {}).get("last_sync")
        if last_sync:
            sync_time = datetime.fromisoformat(last_sync)
            st.info(f"Last synced: {sync_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Show sync details
            synced_files = sync_status.get("gcp", {}).get("files_synced", 0)
            total_files = sync_status.get("gcp", {}).get("total_files", 0)
            st.caption(f"Files synced: {synced_files} of {total_files}")
    
    # Backup file distribution
    st.subheader("Backup File Distribution")
    
    # Create a pie chart for file distribution
    import plotly.express as px
    
    providers = list(file_counts.keys())
    counts = list(file_counts.values())
    
    if sum(counts) > 0:
        fig = px.pie(
            values=counts,
            names=[p.upper() for p in providers],
            title="File Distribution Across Cloud Providers",
            color=[p for p in providers],
            color_discrete_map=PROVIDER_COLORS
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No files available for distribution chart")
    
    # Backup Synchronization Status
    st.subheader("Backup Synchronization Status")
    
    # Create a visual representation of sync status
    sync_status_data = []
    
    for provider, status in sync_status.items():
        if "last_sync" in status and status["last_sync"]:
            sync_time = datetime.fromisoformat(status["last_sync"])
            time_since_sync = datetime.now() - sync_time
            
            sync_status_data.append({
                "Provider": provider.upper(),
                "Last Sync": sync_time.strftime("%Y-%m-%d %H:%M:%S"),
                "Time Since Sync": f"{time_since_sync.total_seconds() / 60:.1f} minutes",
                "Files Synced": status.get("files_synced", 0),
                "Total Files": status.get("total_files", 0),
                "Status": "Up to date" if time_since_sync < timedelta(hours=1) else "Needs sync"
            })
    
    if sync_status_data:
        sync_df = pd.DataFrame(sync_status_data)
        st.dataframe(sync_df, use_container_width=True)
    else:
        st.info("No synchronization data available")
    
    # File Uploader for Testing
    st.subheader("Upload Test Files")
    
    upload_provider = st.selectbox(
        "Select provider for file upload:",
        ["aws", "azure", "gcp"]
    )
    
    uploaded_file = st.file_uploader("Choose a file to upload", type=["txt", "json", "csv", "pdf"])
    
    if uploaded_file and st.button("Upload File"):
        # Save the uploaded file to the selected provider's directory
        provider_dir = f"mock_cloud_storage/{upload_provider}_{'s3' if upload_provider == 'aws' else 'blob' if upload_provider == 'azure' else 'bucket'}"
        
        # Create directory if it doesn't exist
        os.makedirs(provider_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(provider_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"File uploaded to {upload_provider.upper()} successfully!")
    
    # Manual Sync Control
    st.subheader("Manual Synchronization Control")
    
    if st.button("Force Synchronization Now"):
        with st.spinner("Syncing files across providers..."):
            # Perform sync
            files_synced, total_files = backup_manager.sync_across_providers()
            
            # Show results
            st.success(f"Sync completed! Synchronized {files_synced} of {total_files} files.")
            st.rerun()
    
    # Backup logs
    st.subheader("Backup Sync Logs")
    
    if os.path.exists("logs/backup_sync.log"):
        with open("logs/backup_sync.log", "r") as f:
            log_content = f.readlines()
            
            # Show only the last 20 log entries
            log_sample = log_content[-20:]
            
            st.text_area("Recent Backup Log Entries", "".join(log_sample), height=200)
            
            if st.button("View Complete Backup Logs"):
                st.text_area("Complete Backup Logs", "".join(log_content), height=400)
    else:
        st.info("No backup sync logs available")

def render_performance_analytics_page():
    """Render the performance analytics page"""
    st.title("Performance Analytics Dashboard")
    
    # Performance metrics visualization
    st.subheader("Performance Metrics by Failure Scenario")
    
    try:
        tab1, tab2 = st.tabs(["Bar Chart", "Radar Chart"])
        
        with tab1:
            st.plotly_chart(create_performance_bar_chart(), use_container_width=True)
        
        with tab2:
            st.plotly_chart(create_metrics_radar_chart(), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying performance charts: {str(e)}")
    
    # Recovery metrics analysis
    st.subheader("Recovery Metrics Analysis")
    
    try:
        tab1, tab2 = st.tabs(["RTO vs. RPO", "Downtime Comparison"])
        
        with tab1:
            st.plotly_chart(create_rto_rpo_scatter(), use_container_width=True)
        
        with tab2:
            st.plotly_chart(create_downtime_comparison_chart(), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying recovery metrics: {str(e)}")
    
    # Advanced performance comparison
    st.subheader("Advanced Provider Performance Comparison")
    
    try:
        st.plotly_chart(create_performance_comparison_chart(), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying provider performance comparison: {str(e)}")
    
    # Real-time performance gauges
    st.subheader("Real-Time Performance Metrics")
    
    try:
        st.plotly_chart(create_realtime_performance_gauges(), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying real-time performance metrics: {str(e)}")
    
    # Detailed provider performance metrics
    st.subheader("Detailed Provider Performance Metrics")
    
    # Get performance data
    performance_data = get_performance_data()
    
    if performance_data:
        # Convert to DataFrame for display
        performance_rows = []
        
        for provider, metrics in performance_data.items():
            row = {
                "Provider": provider.upper(),
                "CPU (%)": f"{metrics.get('cpu_utilization', 0):.1f}%",
                "Memory (%)": f"{metrics.get('memory_utilization', 0):.1f}%",
                "Disk IOPS": metrics.get('disk_iops', 0),
                "Network (Mbps)": f"{metrics.get('network_throughput', 0):.1f}",
                "Success Rate (%)": f"{metrics.get('request_success_rate', 0):.2f}%",
                "Response Time (ms)": f"{metrics.get('average_response_time', 0) * 1000:.1f}",
                "Last Updated": datetime.fromisoformat(metrics.get('timestamp', datetime.now().isoformat())).strftime("%H:%M:%S")
            }
            
            performance_rows.append(row)
        
        perf_df = pd.DataFrame(performance_rows)
        st.dataframe(perf_df, use_container_width=True)
    else:
        st.info("No performance data available")
    
    # Advanced RPO/RTO Analysis
    st.subheader("Advanced Recovery Objectives Analysis")
    
    try:
        st.plotly_chart(create_rpo_rto_analysis_chart(), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying RPO/RTO analysis: {str(e)}")
    
    # Performance metrics table
    st.subheader("Complete Performance Metrics")
    
    metrics_df = get_formatted_metrics_table()
    st.dataframe(metrics_df, use_container_width=True)

def render_cost_analysis_page():
    """Render the cost analysis page"""
    st.title("Cost Analysis Dashboard")
    
    # Cost summary
    st.subheader("Cost Summary")
    
    # Get cost data
    total_costs = get_total_cost_by_provider()
    cost_history = get_cost_history()
    
    # Display total costs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        aws_cost = total_costs.get("aws", 0)
        st.metric(
            label="AWS Total Cost", 
            value=f"${aws_cost:.2f}",
            delta=f"${random.uniform(-5, 5):.2f}"
        )
    
    with col2:
        azure_cost = total_costs.get("azure", 0)
        st.metric(
            label="Azure Total Cost", 
            value=f"${azure_cost:.2f}",
            delta=f"${random.uniform(-5, 5):.2f}"
        )
    
    with col3:
        gcp_cost = total_costs.get("gcp", 0)
        st.metric(
            label="GCP Total Cost", 
            value=f"${gcp_cost:.2f}",
            delta=f"${random.uniform(-5, 5):.2f}"
        )
    
    # Total infrastructure cost
    total_infra_cost = sum(total_costs.values())
    st.metric(
        label="Total Infrastructure Cost",
        value=f"${total_infra_cost:.2f}",
        delta=f"${random.uniform(-10, 10):.2f}" 
    )
    
    # Cost breakdown chart
    st.subheader("Cost Breakdown by Provider and Type")
    
    try:
        st.plotly_chart(create_cost_breakdown_chart(), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying cost breakdown: {str(e)}")
    
    # Cost trend chart
    st.subheader("Daily Cost Trend (Last 30 Days)")
    
    try:
        st.plotly_chart(create_cost_trend_chart(), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying cost trend: {str(e)}")
    
    # Cost by failure scenario
    st.subheader("Cost by Failure Scenario")
    
    try:
        st.plotly_chart(create_cost_bar_chart(), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying cost by scenario: {str(e)}")
    
    # Cost saving recommendations
    st.subheader("Cost Saving Recommendations")
    
    # These would be real recommendations in a production system
    recommendations = [
        {
            "title": "Optimize Cross-Region Data Transfer",
            "description": "Reduce unnecessary data transfers between regions to minimize transfer costs.",
            "savings": "$15-25 per month",
            "impact": "Low"
        },
        {
            "title": "Adjust RPO for Non-Critical Data",
            "description": "Increase RPO for non-critical data to reduce backup frequency and storage costs.",
            "savings": "$30-50 per month",
            "impact": "Medium"
        },
        {
            "title": "Consolidate Multi-Cloud Storage",
            "description": "Optimize storage distribution across providers to leverage economies of scale.",
            "savings": "$40-60 per month",
            "impact": "Medium"
        }
    ]
    
    for i, rec in enumerate(recommendations):
        with st.expander(f"{i+1}. {rec['title']} (Est. Savings: {rec['savings']})"):
            st.markdown(f"**Description:** {rec['description']}")
            st.markdown(f"**Estimated Savings:** {rec['savings']}")
            st.markdown(f"**Operational Impact:** {rec['impact']}")
            
            # Implementation button (just for demo)
            st.button(f"Implement This Recommendation", key=f"rec_{i}")
    
    # Detailed cost data
    st.subheader("Detailed Cost Data")
    
    if cost_history:
        # Show latest cost data
        cost_rows = []
        
        for provider, history in cost_history.items():
            if history:
                latest = history[-1]
                
                row = {
                    "Provider": provider.upper(),
                    "Compute Cost": f"${latest.get('compute_cost', 0):.2f}",
                    "Storage Cost": f"${latest.get('storage_cost', 0):.2f}",
                    "Transfer Cost": f"${latest.get('transfer_cost', 0):.2f}",
                    "Total Cost": f"${latest.get('total_cost', 0):.2f}",
                    "Date": datetime.fromisoformat(latest.get('timestamp')).strftime("%Y-%m-%d")
                }
                
                cost_rows.append(row)
        
        if cost_rows:
            cost_df = pd.DataFrame(cost_rows)
            st.dataframe(cost_df, use_container_width=True)
        else:
            st.info("No detailed cost data available")
    else:
        st.info("No cost history data available")

def render_configuration_page():
    """Render the configuration page"""
    st.title("System Configuration")
    
    # System settings section
    st.subheader("System Settings")
    
    # Health check configuration
    with st.expander("Health Check Configuration", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            health_interval = st.number_input(
                "Health Check Interval (seconds)",
                min_value=5,
                max_value=300,
                value=30,
                step=5
            )
        
        with col2:
            health_timeout = st.number_input(
                "Health Check Timeout (seconds)",
                min_value=1,
                max_value=30,
                value=5,
                step=1
            )
        
        # Endpoint configuration
        st.text_input("AWS Endpoint", value="https://httpstat.us/200")
        st.text_input("Azure Endpoint", value="https://httpstat.us/200")
        st.text_input("GCP Endpoint", value="https://httpstat.us/200")
        
        # Save button
        if st.button("Save Health Check Configuration"):
            st.success("Health check configuration saved!")
            st.info("Note: In production, this would update the actual config file")
    
    # Failover configuration
    with st.expander("Failover Configuration"):
        col1, col2 = st.columns(2)
        
        with col1:
            failover_interval = st.number_input(
                "Failover Check Interval (seconds)",
                min_value=5,
                max_value=60,
                value=10,
                step=5
            )
        
        # Failover provider ordering
        st.subheader("Failover Provider Order")
        
        # Create drag-and-drop-like interface (simplified)
        providers = ["aws", "azure", "gcp"]
        failover_order = {}
        
        for i, provider in enumerate(providers):
            next_provider = st.selectbox(
                f"After {provider.upper()} fails, failover to:",
                [p.upper() for p in providers if p != provider],
                index=0,
                key=f"failover_{provider}"
            )
            failover_order[provider] = next_provider.lower()
        
        # Save button
        if st.button("Save Failover Configuration"):
            st.success("Failover configuration saved!")
            st.info("Note: In production, this would update the actual config file")
    
    # Backup configuration
    with st.expander("Backup Configuration"):
        backup_interval = st.number_input(
            "Backup Sync Interval (minutes)",
            min_value=5,
            max_value=1440,
            value=360,  # 6 hours
            step=5
        )
        
        # Backup scheduling options
        backup_schedule = st.selectbox(
            "Backup Schedule Type",
            ["Interval Based", "Time Based", "Event Based"],
            index=0
        )
        
        if backup_schedule == "Time Based":
            st.time_input("Backup Time", value=datetime.now().replace(hour=1, minute=0))
        elif backup_schedule == "Event Based":
            st.multiselect(
                "Trigger Backup On Events",
                ["Provider Failover", "File Changes", "Manual Trigger", "System Startup"],
                default=["Provider Failover", "Manual Trigger"]
            )
        
        # Save button
        if st.button("Save Backup Configuration"):
            st.success("Backup configuration saved!")
            st.info("Note: In production, this would update the actual config file")
    
    # System information section
    st.subheader("System Information")
    
    # Version and environment info
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Framework Version:** 1.0")
        st.markdown("**Python Version:** 3.11")
        st.markdown("**Operating System:** Linux")
    
    with col2:
        st.markdown("**Uptime:** 3 days, 12 hours")
        st.markdown("**Last Restart:** 2025-05-15 08:30:00")
        st.markdown("**Status:** Active")
    
    # System tools
    st.subheader("System Tools")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Restart Services"):
            st.info("Restarting services... (simulated)")
            # In production would actually restart services
    
    with col2:
        if st.button("Purge Logs"):
            st.info("Purging old logs... (simulated)")
            # In production would actually purge logs
    
    with col3:
        if st.button("Verify Integrity"):
            st.info("Verifying system integrity... (simulated)")
            time.sleep(1)  # Simulate processing
            st.success("System integrity verified!")

if __name__ == "__main__":
    render_dashboard()
