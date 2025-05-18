import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import os

from health_check import get_current_health_status
from failover_manager import get_active_provider
from advanced_failover import advanced_failover_manager
from db_manager import db_manager

# Color schemes for providers
PROVIDER_COLORS = {
    "aws": "#FF9900",      # AWS Orange
    "azure": "#0078D4",    # Azure Blue
    "gcp": "#4285F4"       # Google Blue
}

# Define LogiXpress application services
LOGIXPRESS_SERVICES = {
    "tracking_api": {
        "name": "Package Tracking API",
        "description": "Real-time package location tracking API for mobile and web clients",
        "priority": "critical",
        "recovery_target": 30,  # seconds
        "dependencies": ["database", "authentication"]
    },
    "route_engine": {
        "name": "Route Optimization Engine",
        "description": "AI-powered delivery route planning and optimization",
        "priority": "high",
        "recovery_target": 120,  # seconds
        "dependencies": ["mapping_service", "traffic_data"]
    },
    "customer_alerts": {
        "name": "Customer Notification System",
        "description": "SMS and email alerts for delivery updates",
        "priority": "medium",
        "recovery_target": 300,  # seconds
        "dependencies": ["messaging_queue", "customer_db"]
    },
    "warehouse_management": {
        "name": "Warehouse Coordination System",
        "description": "Inventory tracking and warehouse operations management",
        "priority": "high",
        "recovery_target": 180,  # seconds
        "dependencies": ["inventory_db", "scanner_api"]
    },
    "logistics_dashboard": {
        "name": "Operations Dashboard",
        "description": "Real-time monitoring dashboard for logistics coordinators",
        "priority": "medium",
        "recovery_target": 300,  # seconds
        "dependencies": ["analytics", "reporting_service"]
    }
}

# LogiXpress business metrics
BUSINESS_METRICS = {
    "packages_tracked": 10000,  # per minute
    "active_deliveries": 25000,
    "warehouses_connected": 45,
    "delivery_partners": 2800,
    "daily_notifications": 150000
}

# LogiXpress recommended provider strengths
PROVIDER_STRENGTHS = {
    "aws": ["Network Latency / Congestion", "Global Reach", "Edge Computing"],
    "azure": ["Compute Instance Failure", "Multi-cloud Coordination", "Disaster Recovery"],
    "gcp": ["Storage Outage", "Cost-Optimized Backup", "Analytics & ML"]
}

def render_logixpress_dashboard():
    """Render the LogiXpress Case Study Dashboard"""
    st.title("LogiXpress Multi-Cloud Business Continuity")
    st.markdown("### Real-time Logistics Operations with Automated Disaster Recovery")
    
    # Company profile
    with st.expander("About LogiXpress", expanded=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            **LogiXpress** is a modern logistics technology company that provides real-time package 
            tracking, route optimization, warehouse coordination, and customer notification systems 
            for courier and supply chain businesses. 
            
            Headquartered in Mumbai with operations across India, Southeast Asia, and Europe, 
            LogiXpress powers time-sensitive logistics for e-commerce platforms, pharmaceuticals, 
            and retail chains.
            """)
        
        with col2:
            # Business metrics
            st.metric("Packages Tracked", f"{BUSINESS_METRICS['packages_tracked']:,}/min")
            st.metric("Active Deliveries", f"{BUSINESS_METRICS['active_deliveries']:,}")
            st.metric("Warehouses", f"{BUSINESS_METRICS['warehouses_connected']}")
    
    # Current system status
    st.header("Logistics System Status")
    
    # Get current status
    health_status = get_current_health_status()
    active_provider = get_active_provider()
    
    # Provider status summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        aws_status = health_status.get("aws", {}).get("status", False)
        st.metric(
            "AWS Status",
            "Operational" if aws_status else "Degraded",
            "Active" if active_provider == "aws" else None,
            delta_color="normal"
        )
        
        color = "green" if aws_status else "red"
        st.markdown(f"<div style='height:5px;background-color:{color};margin-bottom:15px;'></div>", 
                   unsafe_allow_html=True)
    
    with col2:
        azure_status = health_status.get("azure", {}).get("status", False)
        st.metric(
            "Azure Status",
            "Operational" if azure_status else "Degraded",
            "Active" if active_provider == "azure" else None,
            delta_color="normal"
        )
        
        color = "green" if azure_status else "red"
        st.markdown(f"<div style='height:5px;background-color:{color};margin-bottom:15px;'></div>", 
                   unsafe_allow_html=True)
    
    with col3:
        gcp_status = health_status.get("gcp", {}).get("status", False)
        st.metric(
            "GCP Status",
            "Operational" if gcp_status else "Degraded",
            "Active" if active_provider == "gcp" else None,
            delta_color="normal"
        )
        
        color = "green" if gcp_status else "red"
        st.markdown(f"<div style='height:5px;background-color:{color};margin-bottom:15px;'></div>", 
                   unsafe_allow_html=True)
    
    # LogiXpress services status
    st.subheader("LogiXpress Mission-Critical Services")
    
    services_data = []
    for service_id, service in LOGIXPRESS_SERVICES.items():
        # Determine service status based on active provider
        # For simulation, we'll consider a service healthy if its dependencies
        # can be satisfied by the active provider
        is_healthy = True
        
        # If the active provider is unhealthy, services will be affected
        if active_provider in health_status and not health_status[active_provider].get("status", False):
            # High priority services could be affected
            if service["priority"] == "critical":
                is_healthy = False
        
        # Add service with status to data list
        services_data.append({
            "Service": service["name"],
            "Description": service["description"],
            "Priority": service["priority"].capitalize(),
            "Status": "Operational" if is_healthy else "Degraded",
            "Recovery Target": f"{service['recovery_target']} sec"
        })
    
    # Create a DataFrame and display as a table
    services_df = pd.DataFrame(services_data)
    
    # Format the table
    def highlight_status(val):
        color = 'green' if val == 'Operational' else 'red'
        return f'background-color: {color}; color: white'
    
    # Apply the styling to the Status column only
    styled_df = services_df.style.applymap(highlight_status, subset=['Status'])
    
    st.dataframe(styled_df, use_container_width=True)
    
    # Recent failover events specific to LogiXpress
    st.header("Resilience Events Timeline")
    
    # Get recent failover events
    failover_events = advanced_failover_manager.get_recent_failover_events(limit=5)
    
    if failover_events:
        # Create timeline of failover events
        events_data = []
        
        for i, event in enumerate(failover_events):
            # Analyze the impact on LogiXpress services
            impacted_services = []
            for service_id, service in LOGIXPRESS_SERVICES.items():
                if service["priority"] == "critical" or (service["priority"] == "high" and random.random() > 0.7):
                    impacted_services.append(service["name"])
            
            # Calculate business impact metrics
            packages_affected = int(BUSINESS_METRICS["packages_tracked"] * random.uniform(0.1, 0.3) * (3 if event.get("is_manual", False) else 1))
            recovery_time = random.randint(15, 45) if event.get("from_provider") != "aws" else random.randint(30, 90)
            
            from_provider = event.get("from_provider", "unknown").upper()
            to_provider = event.get("to_provider", "unknown").upper()
            
            events_data.append({
                "Event Time": datetime.fromisoformat(event.get("occurred_at", datetime.now().isoformat())).strftime("%Y-%m-%d %H:%M:%S"),
                "Event Type": "Automated Failover" if not event.get("is_manual", False) else "Manual Failover",
                "Transition": f"{from_provider} → {to_provider}",
                "Trigger": event.get("reason", "Unknown"),
                "Recovery Time": f"{recovery_time}s",
                "Packages Affected": f"{packages_affected:,}",
                "Services Impacted": ", ".join(impacted_services[:2]) + (f" +{len(impacted_services)-2} more" if len(impacted_services) > 2 else "")
            })
        
        # Create DataFrame and display
        events_df = pd.DataFrame(events_data)
        st.dataframe(events_df, use_container_width=True)
    else:
        st.info("No failover events have occurred yet.")
    
    # Cloud provider recommendations
    st.header("Cloud Provider Recommendations")
    st.markdown("### Optimizing LogiXpress Logistics with Strategic Multi-Cloud Deployment")
    
    # Create table of recommendations
    recommendations = []
    
    for scenario, providers in {
        "Compute Instance Failure": "azure",
        "Storage Outage": "gcp",
        "Network Latency / Congestion": "aws",
        "Cost-Optimized Backup Strategy": "gcp",
        "Multi-cloud Coordination": "azure"
    }.items():
        # Get the corresponding reason from provider strengths
        reason = ""
        if scenario in PROVIDER_STRENGTHS.get(providers, []):
            if providers == "aws":
                reason = "Global network infrastructure with fast edge routing"
            elif providers == "azure":
                reason = "Strong API management and seamless cross-region orchestration"
            elif providers == "gcp":
                reason = "High durability and smart replication in Cloud Storage"
        
        recommendations.append({
            "Scenario": scenario,
            "Recommended Cloud": providers.upper(),
            "Reason": reason if reason else "Best performance for this scenario"
        })
    
    recommendations_df = pd.DataFrame(recommendations)
    st.dataframe(recommendations_df, use_container_width=True)
    
    # Delivery impact visualization - what happens during failover
    st.header("Business Impact Analysis")
    
    # Create a simulation of delivery impact during failover
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Package Tracking Availability")
        
        # Create a time series of simulated availability
        time_points = 20
        base_time = datetime.now() - timedelta(hours=4)
        times = [base_time + timedelta(minutes=i*12) for i in range(time_points)]
        
        # Simulated availability with a dip during failover
        availability = [99.9] * (time_points // 3) + [85.5, 78.2, 69.8, 82.1, 94.3] + [99.9] * (time_points - time_points // 3 - 5)
        
        # Create dataframe
        availability_df = pd.DataFrame({
            "Time": times,
            "Availability (%)": availability
        })
        
        fig = px.line(
            availability_df, 
            x="Time", 
            y="Availability (%)",
            title="Package Tracking API Availability During Failover",
            markers=True
        )
        
        # Add a threshold line for SLA
        fig.add_shape(
            type="line",
            x0=times[0],
            x1=times[-1],
            y0=99.5,
            y1=99.5,
            line=dict(
                color="green",
                width=2,
                dash="dash",
            )
        )
        
        # Add annotation for SLA
        fig.add_annotation(
            x=times[1],
            y=99.7,
            text="SLA Target (99.5%)",
            showarrow=False,
            font_size=10
        )
        
        # Add recovery annotation
        recovery_point = times[time_points // 3 + 4]
        fig.add_annotation(
            x=recovery_point,
            y=94.3,
            text="Recovery Complete",
            showarrow=True,
            arrowhead=1
        )
        
        # Add failover annotation
        failover_point = times[time_points // 3 + 1]
        fig.add_annotation(
            x=failover_point,
            y=78.2,
            text="Failover Initiated",
            showarrow=True,
            arrowhead=1
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Financial Impact Analysis")
        
        # Create a pie chart of potential loss avoided by automatic failover
        impact_data = {
            "Avoided Loss (Auto-Failover)": 92,
            "Actual Impact": 8
        }
        
        impact_df = pd.DataFrame({
            "Category": list(impact_data.keys()),
            "Percentage": list(impact_data.values())
        })
        
        fig = px.pie(
            impact_df,
            values="Percentage",
            names="Category",
            title="Financial Impact Reduction with Auto-Failover",
            color_discrete_sequence=["#00cc96", "#ef553b"]
        )
        
        fig.update_traces(textinfo="percent+label")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add financial metrics
        estimated_loss = random.randint(15000, 25000)
        avoided_loss = int(estimated_loss * 0.92)
        
        financial_metrics = {
            "Estimated Potential Loss": f"${estimated_loss:,}",
            "Loss Avoided by Auto-Failover": f"${avoided_loss:,}",
            "Actual Business Impact": f"${estimated_loss - avoided_loss:,}"
        }
        
        st.markdown("#### Financial Impact Metrics")
        
        for key, value in financial_metrics.items():
            st.markdown(f"**{key}:** {value}")

# Function to add LogiXpress tab to the dashboard
def add_logixpress_tab_to_dashboard():
    """Add LogiXpress case study tab to the main dashboard"""
    import dashboard
    
    # Patch the render_dashboard function by extending the navigation options
    original_render_dashboard = dashboard.render_dashboard
    
    def patched_render_dashboard():
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
                ["Overview", "Health Monitoring", "Failover Management", "Disaster Recovery", 
                 "Storage & Backup", "Performance Analytics", "Cost Analysis", "LogiXpress Case Study", "Configuration"]
            )
            
            # Original sidebar contents...
            
        # Main content area based on selected page
        if page == "LogiXpress Case Study":
            render_logixpress_dashboard()
        else:
            # Call original page rendering based on selection
            if page == "Overview":
                dashboard.render_overview_page()
            elif page == "Health Monitoring":
                dashboard.render_health_monitoring_page()
            elif page == "Failover Management":
                dashboard.render_failover_management_page()
            elif page == "Disaster Recovery":
                dashboard.render_disaster_recovery_dashboard()
            elif page == "Storage & Backup":
                dashboard.render_storage_backup_page()
            elif page == "Performance Analytics":
                dashboard.render_performance_analytics_page()
            elif page == "Cost Analysis":
                dashboard.render_cost_analysis_page()
            elif page == "Configuration":
                dashboard.render_configuration_page()
    
    # Patch the original function
    dashboard.render_dashboard = patched_render_dashboard

if __name__ == "__main__":
    # This is a test to see if the dashboard renders correctly
    st.set_page_config(layout="wide")
    render_logixpress_dashboard()